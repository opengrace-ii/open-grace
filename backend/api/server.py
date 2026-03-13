"""
API Server - FastAPI-based REST API for Open Grace.

Provides endpoints for controlling the system via HTTP.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from open_grace.kernel.orchestrator import GraceOrchestrator, get_orchestrator, TaskStatus
from open_grace.agents.base_agent import AgentState
from open_grace.security.auth import AuthManager, get_auth_manager, User
from open_grace.api.mobile import MobileAPIManager, get_mobile_manager, PushSubscription, MobileNotification
from open_grace.observability.logger import get_logger
from open_grace.diagnostics.diagnostics_router import diagnostics_router
from open_grace.diagnostics.logs import get_backend_logger

backend_logger = get_backend_logger()

# Security
security = HTTPBearer(auto_error=False)


# Pydantic models for API
class TaskRequest(BaseModel):
    """Request to create a task."""
    description: str
    agent_type: Optional[str] = None
    priority: int = 5
    model: Optional[str] = None


class TaskResponse(BaseModel):
    """Response with task info."""
    id: str
    id_numeric: int = 0
    description: str
    status: str
    agent_type: Optional[str]
    created_at: str
    result: Optional[Any] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    provider: Optional[str] = None
    error: Optional[str] = None
    user: Optional[str] = None
    client_ip: Optional[str] = None


class AgentInfo(BaseModel):
    """Agent information."""
    id: str
    name: str
    agent_type: str
    status: str
    capabilities: List[str]
    task_count: int


class SystemStatus(BaseModel):
    """System status information."""
    instance_id: str
    initialized: bool
    agents: Dict[str, Any]
    tasks: Dict[str, Any]
    queue_size: int


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    # Password would be added in production


class LoginResponse(BaseModel):
    """Login response with token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CreateAPIKeyRequest(BaseModel):
    """Request to create API key."""
    name: str
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API key response."""
    key_id: str
    api_key: str
    name: str
    created_at: str
    expires_at: Optional[str] = None


class APIServer:
    """
    FastAPI server for Open Grace.
    
    Provides REST endpoints and WebSocket for real-time updates.
    
    Usage:
        server = APIServer()
        await server.start(host="0.0.0.0", port=8000)
    """
    
    def __init__(self):
        """Initialize the API server."""
        self.app = FastAPI(
            title="Open Grace API",
            description="REST API for Open Grace TaskForge AI",
            version="0.3.0"
        )
        
        # Add tracing middleware
        @self.app.middleware("http")
        async def trace_activity(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Don't log health/metrics calls to avoid clutter
            if request.url.path not in ["/health", "/system/status", "/observability/activity/stream"]:
                client_host = request.client.host if request.client else "unknown"
                self.logger.log_activity(
                    f"API | {request.method} {request.url.path} | {response.status_code} | {client_host} | {duration:.3f}s"
                )
                backend_logger.info(f"REQ | {request.method} {request.url.path} | {response.status_code}")
            return response

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add diagnostics exception handler
        @self.app.exception_handler(Exception)
        async def backend_exception_handler(request: Request, exc: Exception):
            import traceback
            import uuid
            from open_grace.diagnostics.logs import crash_store, CrashReport
            from open_grace.diagnostics.health import get_system_health
            
            tb = traceback.format_exc()
            backend_logger.error(f"Unhandled exception at {request.url.path}: {exc}\n{tb}")
            
            # Capture request body if possible
            body = None
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = body_bytes.decode('utf-8')
            except:
                pass

            # Create crash report
            report = CrashReport(
                id=str(uuid.uuid4())[:8],
                timestamp=datetime.now().isoformat(),
                url=str(request.url),
                method=request.method,
                error=str(exc),
                traceback=tb,
                request_body=body,
                system_state=get_system_health()
            )
            crash_store.add_report(report)
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Internal Server Error",
                    "crash_id": report.id
                }
            )
            
        self.app.include_router(diagnostics_router)
        
        self.orchestrator: Optional[GraceOrchestrator] = None
        self.auth_manager: Optional[AuthManager] = None
        self.mobile_manager: Optional[MobileAPIManager] = None
        self.logger = get_logger()
        self._websockets: List[WebSocket] = []
        
        # Register routes
        self._register_routes()
    
    async def _get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
        """Get current user from token."""
        if not credentials:
            return None
        
        if not self.auth_manager:
            self.auth_manager = get_auth_manager()
        
        token = credentials.credentials
        
        # Try JWT first
        user = self.auth_manager.get_user_from_token(token)
        if user:
            return user
        
        # Try API key
        user = self.auth_manager.validate_api_key(token)
        return user
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize the orchestrator on startup."""
            await get_orchestrator()
            
        self.app.include_router(diagnostics_router)
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "name": "Open Grace API",
                "version": "0.3.0",
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # Add logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            client_ip = request.client.host if request.client else "unknown"
            backend_logger.info(f"{request.method} {request.url.path} | Status: {response.status_code} | Duration: {duration:.3f}s | IP: {client_ip}")
            return response

        # Auth endpoints
        @self.app.post("/auth/login", response_model=LoginResponse)
        async def login(request: LoginRequest, request_obj: Request):
            """Login and get access token."""
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            # Find user by username
            user = self.auth_manager.get_user_by_username(request.username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Get device info from headers
            user_agent = request_obj.headers.get('user-agent', 'Unknown')
            client_ip = request_obj.client.host if request_obj.client else 'Unknown'
            
            # Create JWT token with device info
            token = self.auth_manager.create_jwt_token(
                user_id=user.id,
                additional_claims={
                    'device_name': user_agent[:50] if user_agent else 'Unknown',
                    'ip_address': client_ip
                }
            )
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create token"
                )
            
            return LoginResponse(
                access_token=token,
                expires_in=86400  # 24 hours
            )
        
        @self.app.post("/auth/api-keys", response_model=APIKeyResponse)
        async def create_api_key(
            request: CreateAPIKeyRequest,
            current_user: User = Depends(self._get_current_user)
        ):
            """Create a new API key."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            api_key, key_id = self.auth_manager.create_api_key(
                user_id=current_user.id,
                name=request.name,
                expires_days=request.expires_days
            )
            
            key_info = self.auth_manager._api_keys.get(key_id)
            
            return APIKeyResponse(
                key_id=key_id,
                api_key=api_key,
                name=request.name,
                created_at=key_info.created_at,
                expires_at=key_info.expires_at
            )
        
        @self.app.get("/auth/api-keys")
        async def list_api_keys(current_user: User = Depends(self._get_current_user)):
            """List API keys for current user."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            keys = self.auth_manager.list_api_keys(user_id=current_user.id)
            return [
                {
                    "key_id": k.key_id,
                    "name": k.name,
                    "created_at": k.created_at,
                    "expires_at": k.expires_at,
                    "last_used_at": k.last_used_at,
                    "is_active": k.is_active
                }
                for k in keys
            ]
        
        @self.app.delete("/auth/api-keys/{key_id}")
        async def revoke_api_key(
            key_id: str,
            current_user: User = Depends(self._get_current_user)
        ):
            """Revoke an API key."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            # Verify key belongs to user
            key_info = self.auth_manager._api_keys.get(key_id)
            if not key_info or key_info.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            self.auth_manager.revoke_api_key(key_id)
            return {"success": True, "message": "API key revoked"}
        
        @self.app.get("/auth/me")
        async def get_current_user_info(current_user: User = Depends(self._get_current_user)):
            """Get current user information."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            return {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "is_admin": current_user.is_admin,
                "created_at": current_user.created_at
            }
        
        @self.app.get("/auth/sessions")
        async def get_active_sessions(current_user: User = Depends(self._get_current_user)):
            """Get all active sessions (admin only)."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            # Get user's own sessions
            user_sessions = self.auth_manager.list_sessions(current_user.id)
            
            # Admin can see all sessions
            all_sessions = []
            if current_user.is_admin:
                all_sessions = self.auth_manager.get_all_active_sessions()
            else:
                all_sessions = [s.to_dict() for s in user_sessions]
            
            return {
                "sessions": all_sessions,
                "total": len(all_sessions)
            }
        
        @self.app.post("/auth/sessions/terminate-all")
        async def terminate_all_sessions(
            current_user: User = Depends(self._get_current_user)
        ):
            """Terminate all sessions for current user."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            count = self.auth_manager.terminate_all_user_sessions(current_user.id)
            
            return {
                "success": True,
                "message": f"Terminated {count} sessions",
                "terminated_count": count
            }
        
        @self.app.delete("/auth/sessions/{session_id}")
        async def terminate_session(
            session_id: str,
            current_user: User = Depends(self._get_current_user)
        ):
            """Terminate a specific session."""
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not self.auth_manager:
                self.auth_manager = get_auth_manager()
            
            # Get session to check ownership
            sessions = self.auth_manager.list_sessions()
            session = None
            for s in sessions:
                if s.session_id == session_id:
                    session = s
                    break
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Only admin or session owner can terminate
            if not current_user.is_admin and session.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot terminate this session"
                )
            
            success = self.auth_manager.revoke_session(session_id)
            
            return {
                "success": success,
                "message": "Session terminated" if success else "Failed to terminate session"
            }
        
        # Task endpoints
        @self.app.post("/tasks", response_model=TaskResponse)
        async def create_task(
            request: TaskRequest,
            request_obj: Request,
            current_user: User = Depends(self._get_current_user)
        ):
            """Create a new task."""
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
                
            orchestrator = await get_orchestrator()
            
            client_ip = request_obj.client.host if request_obj.client else 'Unknown'
            
            metadata = {
                "user": current_user.username,
                "client_ip": client_ip,
                "is_admin": current_user.is_admin
            }
            if request.model:
                metadata["model"] = request.model
                
            task_id = await orchestrator.submit_task(
                description=request.description,
                agent_type=request.agent_type,
                priority=request.priority,
                metadata=metadata
            )
            
            # Get task info
            tasks = await orchestrator.list_tasks()
            task = next((t for t in tasks if t.id == task_id), None)
            
            if not task:
                raise HTTPException(status_code=500, detail="Task creation failed")
            
            return TaskResponse(
                id=task.id,
                id_numeric=task.id_numeric,
                description=task.description,
                status=task.status.value,
                agent_type=task.agent_type,
                created_at=task.created_at.isoformat() if isinstance(task.created_at, datetime) else task.created_at,
                result=task.result,
                model=(task.result.get("model") if isinstance(task.result, dict) else None) or task.metadata.get("model"),
                tokens_used=(task.result.get("total_tokens") if isinstance(task.result, dict) else None) or task.metadata.get("total_tokens"),
                latency_ms=(task.result.get("latency_ms") if isinstance(task.result, dict) else None) or task.metadata.get("latency_ms"),
                provider=(task.result.get("provider") if isinstance(task.result, dict) else None) or task.metadata.get("provider"),
                error=task.error,
                user=task.metadata.get("user") or "Auto",
                client_ip=task.metadata.get("client_ip") or "Unknown"
            )
        
        @self.app.get("/tasks", response_model=List[TaskResponse])
        async def list_tasks(status: Optional[str] = None):
            """List all tasks."""
            orchestrator = await get_orchestrator()
            
            task_status = None
            if status:
                try:
                    task_status = TaskStatus(status)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
            tasks = await orchestrator.list_tasks(status=task_status)
            
            return [
                TaskResponse(
                    id=t.id,
                    id_numeric=t.id_numeric,
                    description=t.description,
                    status=t.status.value,
                    agent_type=t.agent_type,
                    created_at=t.created_at.isoformat() if isinstance(t.created_at, datetime) else t.created_at,
                    result=t.result,
                    model=(t.result.get("model") if isinstance(t.result, dict) else None) or t.metadata.get("model"),
                    tokens_used=(t.result.get("total_tokens") if isinstance(t.result, dict) else None) or t.metadata.get("total_tokens"),
                    latency_ms=(t.result.get("latency_ms") if isinstance(t.result, dict) else None) or t.metadata.get("latency_ms"),
                    provider=(t.result.get("provider") if isinstance(t.result, dict) else None) or t.metadata.get("provider"),
                    error=t.error,
                    user=t.metadata.get("user") or "Auto",
                    client_ip=t.metadata.get("client_ip") or "Unknown"
                )
                for t in tasks
            ]
        
        @self.app.get("/tasks/{task_id}", response_model=TaskResponse)
        async def get_task(task_id: str):
            """Get task by ID."""
            orchestrator = await get_orchestrator()
            
            tasks = await orchestrator.list_tasks()
            task = next((t for t in tasks if t.id == task_id), None)
            
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return TaskResponse(
                id=task.id,
                id_numeric=task.id_numeric,
                description=task.description,
                status=task.status.value,
                agent_type=task.agent_type,
                created_at=task.created_at.isoformat() if isinstance(task.created_at, datetime) else task.created_at,
                result=task.result,
                model=(task.result.get("model") if isinstance(task.result, dict) else None) or task.metadata.get("model"),
                tokens_used=(task.result.get("total_tokens") if isinstance(task.result, dict) else None) or task.metadata.get("total_tokens"),
                latency_ms=(task.result.get("latency_ms") if isinstance(task.result, dict) else None) or task.metadata.get("latency_ms"),
                provider=(task.result.get("provider") if isinstance(task.result, dict) else None) or task.metadata.get("provider"),
                error=task.error,
                user=task.metadata.get("user") or "Auto",
                client_ip=task.metadata.get("client_ip") or "Unknown"
            )
        
        @self.app.post("/tasks/{task_id}/cancel")
        async def cancel_task(task_id: str):
            """Cancel a task."""
            orchestrator = await get_orchestrator()
            
            success = await orchestrator.cancel_task(task_id)
            
            if not success:
                raise HTTPException(status_code=400, detail="Could not cancel task")
            
            return {"success": True, "message": "Task cancelled"}
        
        # Agent endpoints
        @self.app.get("/agents", response_model=List[AgentInfo])
        async def list_agents(agent_type: Optional[str] = None):
            """List all agents."""
            orchestrator = await get_orchestrator()
            
            agents = await orchestrator.list_agents(agent_type=agent_type)
            
            return [
                AgentInfo(
                    id=a.id,
                    name=a.name,
                    agent_type=a.agent_type,
                    status=a.status.value,
                    capabilities=a.capabilities,
                    task_count=a.task_count
                )
                for a in agents
            ]
        
        @self.app.get("/agents/{agent_id}")
        async def get_agent(agent_id: str):
            """Get agent by ID."""
            orchestrator = await get_orchestrator()
            
            agents = await orchestrator.list_agents()
            agent = next((a for a in agents if a.id == agent_id), None)
            
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            return {
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status.value,
                "capabilities": agent.capabilities,
                "task_count": agent.task_count,
                "created_at": agent.created_at.isoformat() if isinstance(agent.created_at, datetime) else agent.created_at
            }
        
        # System endpoints
        @self.app.get("/system/status", response_model=SystemStatus)
        async def get_system_status():
            """Get system status."""
            orchestrator = await get_orchestrator()
            status = await orchestrator.get_system_status()
            
            return SystemStatus(
                instance_id=status["instance_id"],
                initialized=status["initialized"],
                agents=status["agents"],
                tasks=status["tasks"],
                queue_size=status["queue_size"]
            )
        
        @self.app.get("/system/providers")
        async def get_providers():
            """Get AI model provider status."""
            orchestrator = await get_orchestrator()
            status = await orchestrator.get_system_status()
            
            return status.get("providers", {})
        
        # Mobile endpoints
        @self.app.post("/mobile/register")
        async def register_mobile_device(
            subscription: PushSubscription,
            current_user: User = Depends(self._get_current_user)
        ):
            """Register device for push notifications."""
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not self.mobile_manager:
                self.mobile_manager = get_mobile_manager()
            
            success = self.mobile_manager.register_device(
                current_user.id,
                subscription
            )
            
            return {"success": success}
        
        @self.app.post("/mobile/notify")
        async def send_test_notification(
            current_user: User = Depends(self._get_current_user)
        ):
            """Send test notification (for debugging)."""
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not self.mobile_manager:
                self.mobile_manager = get_mobile_manager()
            
            success = self.mobile_manager.send_notification(
                current_user.id,
                MobileNotification(
                    title="Test Notification",
                    body="Open Grace mobile notifications are working!"
                )
            )
            
            return {"success": success}
        
        @self.app.get("/mobile/devices")
        async def get_mobile_devices(
            current_user: User = Depends(self._get_current_user)
        ):
            """Get registered mobile devices."""
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not self.mobile_manager:
                self.mobile_manager = get_mobile_manager()
            
            devices = self.mobile_manager.get_user_devices(current_user.id)
            return {"devices": devices}

        # Observability endpoints
        @self.app.post("/observability/activity")
        async def log_frontend_activity(request: Request):
            """Log an activity from the frontend."""
            data = await request.json()
            event = data.get("event", "Unknown Event")
            category = data.get("category", "UI")
            details = data.get("details", "")
            
            self.logger.log_activity(
                f"CLIENT | {category} | {event} | {details}"
            )
            return {"success": True}

        @self.app.get("/observability/activity/stream")
        async def stream_activity_log():
            """Return the last 200 lines of activity log as JSON (backward compat)."""
            return await get_activity_history()

        @self.app.get("/observability/activity/history")
        async def get_activity_history(lines: int = 200):
            """Return the last N lines of the activity log."""
            log_path = self.logger.log_dir / "activity.log"
            if not log_path.exists():
                return {"lines": [], "total": 0}
            
            try:
                with open(log_path, "r") as f:
                    all_lines = f.readlines()
                    recent = [l.strip() for l in all_lines[-lines:] if l.strip()]
                    return {"lines": recent, "total": len(all_lines)}
            except Exception as e:
                return {"lines": [f"Error reading log: {str(e)}"], "total": 0}
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await websocket.accept()
            self._websockets.append(websocket)
            
            try:
                # Send initial status
                orchestrator = await get_orchestrator()
                status = await orchestrator.get_system_status()
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })
                
                # Listen for messages
                while True:
                    message = await websocket.receive_text()
                    # Handle client messages if needed
                    
            except WebSocketDisconnect:
                self._websockets.remove(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                if websocket in self._websockets:
                    self._websockets.remove(websocket)
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected WebSocket clients."""
        if not self._websockets:
            return

        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients in parallel
        tasks = []
        for ws in self._websockets:
            tasks.append(ws.send_json(message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Identify disconnected clients
            disconnected = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    disconnected.append(self._websockets[i])
            
            # Remove disconnected clients
            for ws in disconnected:
                if ws in self._websockets:
                    self._websockets.remove(ws)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Start the API server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
        """
        import uvicorn
        
        self.logger.info(f"Starting API server on {host}:{port}")
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app


# Create app instance for uvicorn
app = APIServer().app

# Main entry point
if __name__ == "__main__":
    async def main():
        server = APIServer()
        await server.start(host="0.0.0.0", port=8000)
    
    asyncio.run(main())