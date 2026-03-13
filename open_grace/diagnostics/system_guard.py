import psutil
import logging

logger = logging.getLogger(__name__)

class SystemGuard:
    """
    Monitors system health and provides safety signals to prevent system freezes.
    """
    def __init__(self, mem_threshold: float = 90.0, cpu_threshold: float = 95.0):
        self.mem_threshold = mem_threshold
        self.cpu_threshold = cpu_threshold

    def healthy(self) -> bool:
        """
        Checks if the system is currently within safe resource limits.
        """
        mem = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=None)

        if mem > self.mem_threshold:
            logger.warning(f"SystemGuard: High memory usage detected: {mem}%")
            return False

        if cpu > self.cpu_threshold:
            logger.warning(f"SystemGuard: High CPU usage detected: {cpu}%")
            return False

        return True

    def get_stats(self):
        return {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "healthy": self.healthy()
        }
