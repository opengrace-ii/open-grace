import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class TaskQueue:
    """
    Asynchronous task queue for managing multiple agent jobs.
    Ensures that user requests are queued safely and can be processed sequentially.
    """
    def __init__(self):
        self._queue = asyncio.Queue()
        self._pending_tasks = {} # Track task status if needed

    async def add_task(self, goal: str, context: Optional[dict] = None) -> str:
        """
        Adds a new goal/task to the queue.
        Returns a task ID.
        """
        task_id = f"task_{id(goal)}_{asyncio.get_event_loop().time()}"
        task_data = {
            "id": task_id,
            "goal": goal,
            "context": context or {},
            "status": "queued"
        }
        await self._queue.put(task_data)
        self._pending_tasks[task_id] = task_data
        logger.info(f"TaskQueue: Added task {task_id} - Goal: {goal}")
        return task_id

    async def get_task(self) -> dict:
        """
        Retrieves the next task from the queue.
        """
        task_data = await self._queue.get()
        task_data["status"] = "processing"
        logger.info(f"TaskQueue: Retrieving task {task_data['id']}")
        return task_data

    def mark_done(self, task_id: str):
        """
        Signals that a task is complete.
        """
        if task_id in self._pending_tasks:
            self._pending_tasks[task_id]["status"] = "completed"
            self._queue.task_done()
            logger.info(f"TaskQueue: Task {task_id} marked as done")

    def get_queue_size(self) -> int:
        return self._queue.qsize()

# Global instance
_task_queue: Optional[TaskQueue] = None

def get_task_queue() -> TaskQueue:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
