import asyncio
import logging
from typing import Optional, Any
from open_grace.model_router.router import get_router, RoutingStrategy

logger = logging.getLogger(__name__)

class ModelPool:
    """
    Controls and throttles access to AI models to prevent system overload.
    Essentially a singleton wrapper around the ModelRouter with concurrency limits.
    """
    def __init__(self, max_parallel: int = 1):
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.router = get_router()

    async def generate(self, prompt: str, system: Optional[str] = None, strategy: Optional[RoutingStrategy] = None):
        """
        Throttled generate call.
        """
        async with self.semaphore:
            logger.info(f"ModelPool: Executing generate call (Parallel slots: {self.semaphore._value})")
            return await self.router.generate(prompt, system=system, strategy=strategy)

    async def chat(self, messages: list, strategy: Optional[RoutingStrategy] = None):
        """
        Throttled chat call.
        """
        async with self.semaphore:
            logger.info(f"ModelPool: Executing chat call (Parallel slots: {self.semaphore._value})")
            return await self.router.chat(messages, strategy=strategy)

# Global instances
_model_pool: Optional[ModelPool] = None

def get_model_pool() -> ModelPool:
    global _model_pool
    if _model_pool is None:
        _model_pool = ModelPool(max_parallel=1)
    return _model_pool
