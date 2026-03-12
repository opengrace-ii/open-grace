import psutil
from typing import Dict, Any

def calculate_health_score(api_status: str, db_status: str, cpu: float, mem: float, disk: float) -> int:
    """Calculate an aggregate health score from 0-100."""
    score = 100
    
    # Critical services
    if api_status != "ok": score -= 30
    if db_status != "ok": score -= 20
    
    # Resource stress
    if cpu > 90: score -= 15
    elif cpu > 70: score -= 5
    
    if mem > 90: score -= 15
    elif mem > 70: score -= 5
    
    if disk > 95: score -= 20
    elif disk > 85: score -= 10
    
    return max(0, score)

def get_system_health() -> Dict[str, Any]:
    """Retrieve system health metrics and calculate score."""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    disk = psutil.disk_usage('/')

    api_status = "ok"
    db_status = "ok"
    
    score = calculate_health_score(api_status, db_status, cpu, memory.percent, disk.percent)

    # Anomaly Detection Logic
    warnings = []
    if cpu > 90:
        warnings.append("High CPU usage detected (>90%)")
    if memory.percent > 80:
        warnings.append("Memory pressure detected (>80%)")
    if disk.percent > 90:
        warnings.append("Disk space low (<10% free)")

    return {
        "api": api_status,
        "database": db_status,
        "models": "available",
        "memory": f"{memory.percent}%",
        "cpu": f"{cpu}%",
        "disk": f"{disk.percent}%",
        "health_score": score,
        "warnings": warnings,
        "anomaly_flag": len(warnings) > 0
    }
