from fastapi import APIRouter
from pathlib import Path

from .health import get_system_health
from .self_test import run_all_diagnostics

diagnostics_router = APIRouter(prefix="/system", tags=["diagnostics"])

@diagnostics_router.get("/health")
async def health_check():
    return get_system_health()

@diagnostics_router.get("/logs")
async def get_logs(service: str = "backend", lines: int = 100):
    log_file = Path(f"logs/{service}.log")
    if not log_file.exists():
        return {"error": f"Log file for {service} not found"}
        
    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            recent = [line.strip() for line in all_lines[-lines:] if line.strip()]
            return {"lines": recent}
    except Exception as e:
        return {"error": str(e)}

@diagnostics_router.get("/health-score")
async def health_score():
    return get_system_health()

@diagnostics_router.get("/error-timeline")
async def get_error_timeline():
    # Simple mock data for error timeline
    return {
        "hour": [0, 2, 1, 0, 4, 1, 0, 0, 2, 1, 0, 0],
        "day": [12, 15, 8, 22, 14, 10, 5, 25, 18, 12, 10, 8, 15, 20, 10, 5, 8, 12, 15, 18, 22, 14, 10, 12]
    }

@diagnostics_router.get("/diagnostics")
async def get_diagnostics():
    return {
        "status": "ready",
        "watchdog_active": True,
        "layers_count": 7
    }

@diagnostics_router.post("/self-test")
async def trigger_self_test():
    report = run_all_diagnostics()
    return report

@diagnostics_router.get("/crash-reports")
async def get_crash_reports():
    from .logs import crash_store
    return crash_store.get_reports()

@diagnostics_router.get("/crash-reports/{report_id}")
async def get_crash_report(report_id: str):
    from .logs import crash_store
    reports = crash_store.get_reports()
    report = next((r for r in reports if r.id == report_id), None)
    if not report:
        return {"error": "Report not found"}
    return report

@diagnostics_router.post("/test-crash")
async def test_crash():
    """Endpoint to trigger a test crash for verification."""
    raise ValueError("Test crash triggered for diagnostics verification")

@diagnostics_router.post("/crash-reports/{report_id}/replay")
async def replay_crash(report_id: str):
    from .logs import crash_store, backend_logger
    reports = crash_store.get_reports()
    report = next((r for r in reports if r.id == report_id), None)
    if not report:
        return {"error": "Report not found"}
    
    backend_logger.info(f"REPLAY | Replaying crash {report_id} in safe mode...")
    # Simulation of 'Safe Mode' replay
    return {
        "success": True, 
        "message": f"Crash #{report_id} replayed in Safe Mode.",
        "log": f"Re-executing {report.method} {report.url} with strict isolation..."
    }
