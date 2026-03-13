from typing import List, Dict, Any, Optional
import time

class ShortTermMemory:
    """
    Episodic memory to track recent actions and findings within a single task session.
    """
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def add_event(self, event_type: str, content: Any, metadata: Optional[Dict] = None):
        """
        Adds an item to memory.
        """
        self._history.append({
            "timestamp": time.time(),
            "type": event_type,
            "content": content,
            "metadata": metadata or {}
        })

    def get_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def clear(self):
        self._history = []

    def search_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self._history if e["type"] == event_type]

# Each agent/orchestrator might have its own short-term memory instance
