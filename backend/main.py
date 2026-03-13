"""
API Server - FastAPI-based REST API for Open Grace.
Main Entry Point that orchestrates specialized route modules.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.api.deps import get_orchestrator, get_backend_logger
from backend.observability.logger import get_logger

# Import specialized route modules
from backend.api.routes_system import router as system_router
from backend.api.routes_auth import router as auth_router
from backend.api.routes_tasks import router as tasks_router
from backend.api.routes_agents import router as agents_router
from backend.api.routes_logs import router as logs_router
try:
    from backend.api.routes_mobile import router as mobile_router
except ImportError:
    mobile_router = None

backend_logger = get_backend_logger()

class APIServer:
    """
    FastAPI server for Open Grace.
    Provides a unified entry point for all specialized API modules.
    """
    
    def __init__(self):
        """Initialize the API server and include all sub-routers."""
        self.app = FastAPI(
            title="Open Grace API",
            description="Professional AI OS Engine - REST & Real-time Gateway",
            version="0.3.0"
        )
        
        self.logger = get_logger()
        self._websockets: List[WebSocket] = []
        
        # 1. Setup Middlewares
        self._setup_middlewares()
        
        # 2. Setup Exception Handlers
        self._setup_exception_handlers()
        
        # 3. Include Specialized Routers
        self._include_routers()
        
        # 4. Setup Startup Events
        @self.app.on_event("startup")
        async def startup_event():
            backend_logger.info("Initializing Grace Orchestrator...")
            try:
                await get_orchestrator()
            except Exception as e:
                backend_logger.error(f"Startup error: {e}")

    def _setup_middlewares(self):
        """Configure CORS and Tracing middlewares."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.middleware("http")
        async def trace_activity(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            if request.url.path not in ["/health", "/system/status", "/observability/activity/stream"]:
                client_host = request.client.host if request.client else "unknown"
                backend_logger.info(f"REQ | {request.method} {request.url.path} | {response.status_code} | {duration:.3f}s | {client_host}")
            return response

    def _setup_exception_handlers(self):
        """Global exception handler for the API."""
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            import traceback
            import uuid
            from backend.tracing.logs import crash_store, CrashReport
            from backend.tracing import get_backend_logger, get_system_health
            
            tb = traceback.format_exc()
            backend_logger.error(f"CRASH | {request.url.path} | {exc}\n{tb}")
            
            report = CrashReport(
                id=str(uuid.uuid4())[:8],
                timestamp=datetime.now().isoformat(),
                url=str(request.url),
                method=request.method,
                error=str(exc),
                traceback=tb,
                system_state=get_system_health()
            )
            crash_store.add_report(report)
            
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"message": "Internal Server Error", "crash_id": report.id})

    def _include_routers(self):
        """Aggregate all specialized routers."""
        self.app.include_router(system_router)
        self.app.include_router(auth_router)
        self.app.include_router(tasks_router)
        self.app.include_router(agents_router)
        self.app.include_router(logs_router)
        if mobile_router:
            self.app.include_router(mobile_router)

    # WebSocket Gateway
    @property
    def websocket_handler(self):
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self._websockets.append(websocket)
            try:
                orchestrator = await get_orchestrator()
                status = await orchestrator.get_system_status()
                await websocket.send_json({"type": "status", "data": status})
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self._websockets.remove(websocket)
            except Exception as e:
                backend_logger.error(f"WS_ERROR | {e}")
                if websocket in self._websockets:
                    self._websockets.remove(websocket)
        return websocket_endpoint

# Instantiate the server
server = APIServer()
app = server.app
# Ensure websocket is registered (FastAPI routes are registered on the app instance)
server.websocket_handler