import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

class EventLogger:
    """
    Standardized event logging for agent actions and system events.
    Stored in structured format for analysis and UI display.
    """
    def __init__(self, log_path: str = "/home/opengrace/open_grace/logs/events.jsonl"):
        self.log_path = log_path
        self._ensure_log_dir()
        
    def _ensure_log_dir(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(self, source: str, event_type: str, data: Any, level: str = "INFO"):
        event = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "type": event_type,
            "data": data,
            "level": level
        }
        
        # Write to file (append)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
            
        # Log to standard logging as well
        logger = logging.getLogger(source)
        msg = f"[{event_type}] {data}"
        if level == "INFO":
            logger.info(msg)
        elif level == "WARNING":
            logger.warning(msg)
        elif level == "ERROR":
            logger.error(msg)

import os
# Global instance
_instance: Optional[EventLogger] = None

def get_event_logger() -> EventLogger:
    global _instance
    if _instance is None:
        _instance = EventLogger()
    return _instance
