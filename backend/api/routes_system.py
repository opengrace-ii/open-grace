from fastapi import APIRouter, Request
from typing import Optional
from backend.api.deps import get_orchestrator

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/status")
async def get_system_status():
    """Get system health and agent status."""
    orchestrator = await get_orchestrator()
    status = await orchestrator.get_system_status()
    return status

@router.get("/health")
async def health_check():
    """Simple health check for load balancers."""
    return {"status": "healthy", "timestamp": "2026-03-13T17:10:18Z"}
