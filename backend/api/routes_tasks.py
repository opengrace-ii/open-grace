from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime
from backend.api.models import TaskRequest, TaskResponse
from backend.api.deps import get_orchestrator, security
from backend.core.orchestrator import TaskStatus
from backend.api.routes_auth import _get_current_user
from backend.security.auth import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse)
async def create_task(
    request: TaskRequest,
    request_obj: Request,
    current_user: User = Depends(_get_current_user)
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

@router.get("", response_model=List[TaskResponse])
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

@router.get("/{task_id}", response_model=TaskResponse)
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

@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task."""
    orchestrator = await get_orchestrator()
    success = await orchestrator.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not cancel task")
    return {"success": True, "message": "Task cancelled"}
