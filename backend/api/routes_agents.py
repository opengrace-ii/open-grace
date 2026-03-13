from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from backend.api.models import AgentInfo
from backend.api.deps import get_orchestrator

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("", response_model=List[AgentInfo])
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

@router.get("/{agent_id}")
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
