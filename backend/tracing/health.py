import os
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

    # Use a slightly longer interval for more stable readings (0.5s)
    # This matches htop's default refresh rate more closely
    cpu = psutil.cpu_percent(interval=0.5)

    # Calculate "Used" memory in a way that matches htop's green bar (Total - Available)
    # Note: memory.percent from psutil matches (Total - Available) / Total
    # but we want to be explicit about what is being shown.
    # htop 'Used' = Total - Free - Buffers - Cached
    # psutil 'Available' is roughly Free + Buffers + Cached (with some nuances)
    # So (Total - Available) is the most accurate 'Used' representation.
    mem_used_percent = memory.percent

    # Also capture load average for better context
    load_1, load_5, load_15 = os.getloadavg()
    cpu_count = psutil.cpu_count()
    
    # We will report instantaneous CPU as the primary metric to match 'htop' bars
    # and keep load average as supplemental data.
    effective_cpu = cpu

    disk = psutil.disk_usage('/')

    api_status = "ok"
    db_status = "ok"
    
    score = calculate_health_score(api_status, db_status, effective_cpu, mem_used_percent, disk.percent)

    # Anomaly Detection Logic
    warnings = []
    if effective_cpu > 90:
        warnings.append(f"High CPU usage detected ({effective_cpu:.1f}%)")
    if mem_used_percent > 85:
        warnings.append(f"Memory pressure detected ({mem_used_percent}%)")
    if disk.percent > 90:
        warnings.append(f"Disk space low ({disk.percent}% used)")
    if load_1 > cpu_count * 2:
        warnings.append("System load is critically high")

    return {
        "api": api_status,
        "database": db_status,
        "models": "available",
        "memory": f"{mem_used_percent}%",
        "cpu": f"{effective_cpu:.1f}%",
        "disk": f"{disk.percent}%",
        "load_avg": [round(float(l), 2) for l in [load_1, load_5, load_15]],
        "health_score": score,
        "warnings": warnings,
        "anomaly_flag": len(warnings) > 0
    }
