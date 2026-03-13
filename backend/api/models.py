from typing import Dict, List, Any, Optional, Optional
from datetime import datetime
from pydantic import BaseModel

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
