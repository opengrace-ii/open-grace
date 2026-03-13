from fastapi import APIRouter, Request
from typing import Optional
from backend.api.deps import get_backend_logger
from backend.observability.logger import get_logger

router = APIRouter(prefix="/observability", tags=["observability"])
backend_logger = get_backend_logger()
logger = get_logger()

@router.post("/activity")
async def log_frontend_activity(request: Request):
    """Log an activity from the frontend."""
    data = await request.json()
    event = data.get("event", "Unknown Event")
    category = data.get("category", "UI")
    details = data.get("details", "")
    
    logger.log_activity(
        f"CLIENT | {category} | {event} | {details}"
    )
    return {"success": True}

@router.get("/activity/stream")
async def stream_activity_log():
    """Return the last 200 lines of activity log as JSON (backward compat)."""
    # This logic should be shared with get_activity_history
    log_path = logger.log_dir / "activity.log"
    if not log_path.exists():
        return {"lines": [], "total": 0}
    
    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()
            recent = [l.strip() for l in all_lines[-200:] if l.strip()]
            return {"lines": recent, "total": len(all_lines)}
    except Exception as e:
        return {"lines": [f"Error reading log: {str(e)}"], "total": 0}

@router.get("/activity/history")
async def get_activity_history(lines: int = 200):
    """Return the last N lines of the activity log."""
    log_path = logger.log_dir / "activity.log"
    if not log_path.exists():
        return {"lines": [], "total": 0}
    
    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()
            recent = [l.strip() for l in all_lines[-lines:] if l.strip()]
            return {"lines": recent, "total": len(all_lines)}
    except Exception as e:
        return {"lines": [f"Error reading log: {str(e)}"], "total": 0}
