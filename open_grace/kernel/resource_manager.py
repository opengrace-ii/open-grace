"""
Resource Manager - Manages system resources for Open Grace.

Tracks and manages:
- CPU usage
- Memory usage
- Disk space
- Network resources
- GPU resources (if available)
"""

import os
import psutil
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_percent: float
    disk_free_gb: float
    network_io_mb: tuple  # (sent, received)
    gpu_available: bool
    gpu_memory_percent: Optional[float] = None


class ResourceManager:
    """
    Manages and monitors system resources.
    
    Usage:
        rm = ResourceManager()
        snapshot = rm.get_snapshot()
        
        if rm.has_available_resources(cpu_percent=50, memory_gb=2):
            # Proceed with resource-intensive task
    """
    
    def __init__(self):
        self._history: List[ResourceSnapshot] = []
        self._max_history = 1000
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def get_snapshot(self) -> ResourceSnapshot:
        """Get current resource snapshot."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024 ** 3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024 ** 3)
        
        # Network
        net_io = psutil.net_io_counters()
        network_io_mb = (net_io.bytes_sent / (1024 ** 2), net_io.bytes_recv / (1024 ** 2))
        
        # GPU (if available)
        gpu_available = False
        gpu_memory_percent = None
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_available = True
            gpu_memory_percent = (info.used / info.total) * 100
        except:
            pass
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_percent=disk_percent,
            disk_free_gb=disk_free_gb,
            network_io_mb=network_io_mb,
            gpu_available=gpu_available,
            gpu_memory_percent=gpu_memory_percent
        )
        
        # Store in history
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        return snapshot
    
    def has_available_resources(self, 
                                cpu_percent: Optional[float] = None,
                                memory_gb: Optional[float] = None,
                                disk_gb: Optional[float] = None) -> bool:
        """
        Check if required resources are available.
        
        Args:
            cpu_percent: Required CPU percentage available
            memory_gb: Required memory in GB
            disk_gb: Required disk space in GB
            
        Returns:
            True if resources are available
        """
        snapshot = self.get_snapshot()
        
        if cpu_percent is not None:
            available_cpu = 100 - snapshot.cpu_percent
            if available_cpu < cpu_percent:
                return False
        
        if memory_gb is not None:
            if snapshot.memory_available_gb < memory_gb:
                return False
        
        if disk_gb is not None:
            if snapshot.disk_free_gb < disk_gb:
                return False
        
        return True
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get a summary of current resources."""
        snapshot = self.get_snapshot()
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "cpu": {
                "percent_used": snapshot.cpu_percent,
                "percent_available": 100 - snapshot.cpu_percent
            },
            "memory": {
                "percent_used": snapshot.memory_percent,
                "available_gb": round(snapshot.memory_available_gb, 2)
            },
            "disk": {
                "percent_used": snapshot.disk_percent,
                "free_gb": round(snapshot.disk_free_gb, 2)
            },
            "network": {
                "sent_mb": round(snapshot.network_io_mb[0], 2),
                "received_mb": round(snapshot.network_io_mb[1], 2)
            },
            "gpu": {
                "available": snapshot.gpu_available,
                "memory_percent": snapshot.gpu_memory_percent
            }
        }
    
    def get_average_usage(self, minutes: int = 5) -> Dict[str, float]:
        """Get average resource usage over the last N minutes."""
        cutoff = datetime.now() - __import__('datetime').timedelta(minutes=minutes)
        recent = [s for s in self._history if s.timestamp > cutoff]
        
        if not recent:
            return {}
        
        return {
            "avg_cpu": sum(s.cpu_percent for s in recent) / len(recent),
            "avg_memory": sum(s.memory_percent for s in recent) / len(recent),
            "avg_disk": sum(s.disk_percent for s in recent) / len(recent)
        }
    
    async def start_monitoring(self, interval_seconds: float = 5.0):
        """Start continuous resource monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self, interval_seconds: float):
        """Monitoring loop."""
        while self._monitoring:
            self.get_snapshot()
            await asyncio.sleep(interval_seconds)