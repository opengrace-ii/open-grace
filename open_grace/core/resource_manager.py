import asyncio
import psutil
import logging

logger = logging.getLogger(__name__)

class ResourceManager:
    """
    Manages system resources and execution concurrency for agents and models.
    """
    def __init__(self, max_agents: int = 2, max_models: int = 1):
        self.agent_semaphore = asyncio.Semaphore(max_agents)
        self.model_semaphore = asyncio.Semaphore(max_models)
        self.max_mem_percent = 85
        self.max_cpu_percent = 90

    async def run_agent(self, agent_func, *args, **kwargs):
        """
        Runs an agent task within the agent concurrency limit.
        """
        async with self.agent_semaphore:
            if self.system_overloaded():
                logger.warning("System overloaded! Throttling agent execution.")
                # Optional: wait or raise exception
                raise Exception("System overloaded: Memory or CPU limits exceeded")
            
            return await agent_func(*args, **kwargs)

    async def run_model(self, model_call_func, *args, **kwargs):
        """
        Runs a model call within the model concurrency limit.
        """
        async with self.model_semaphore:
            return await model_call_func(*args, **kwargs)

    def system_overloaded(self) -> bool:
        """
        Checks if system resources are near limits.
        """
        mem = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=None) # Non-blocking check

        if mem > self.max_mem_percent:
            logger.error(f"High Memory Usage: {mem}%")
            return True
        if cpu > self.max_cpu_percent:
            logger.error(f"High CPU Usage: {cpu}%")
            return True
        return False

    def get_status(self):
        return {
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(interval=None),
            "agents_running": self.agent_semaphore._value, # Note: internal but useful for debug
            "models_running": self.model_semaphore._value
        }
