"""
Grace Logger - Structured logging for Open Grace.

Provides:
- Structured JSON logging
- Log rotation
- Multiple log levels
- Context tracking
"""

import json
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


class StructuredLogFormatter(logging.Formatter):
    """Formatter for structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields safely
        context = getattr(record, "context", None)
        if context is not None:
            log_data["context"] = context
            
        agent_id = getattr(record, "agent_id", None)
        if agent_id is not None:
            log_data["agent_id"] = agent_id
            
        task_id = getattr(record, "task_id", None)
        if task_id is not None:
            log_data["task_id"] = task_id
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)  # type: ignore
        
        return json.dumps(log_data)


class GraceLogger:
    """
    Structured logger for Open Grace.
    
    Usage:
        logger = GraceLogger()
        logger.info("System started")
        logger.error("An error occurred", extra={"context": {"user_id": "123"}})
    """
    
    def __init__(self, name: str = "open_grace", 
                 log_dir: Optional[str] = None,
                 console_output: bool = True):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            console_output: Whether to output to console
        """
        self.name = name
        self.log_dir = Path(log_dir or Path.home() / ".open_grace" / "logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers = []  # Clear existing handlers
        
        # Structured formatter
        formatter = StructuredLogFormatter()
        
        # File handler with rotation
        log_file = self.log_dir / "open_grace.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            # Use simpler format for console
            simple_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(simple_formatter)
            self._logger.addHandler(console_handler)
        
        # Separate error log
        error_file = self.log_dir / "errors.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self._logger.addHandler(error_handler)

        # Activity log (human readable audit trail)
        self._activity_logger = logging.getLogger(f"{name}_activity")
        self._activity_logger.setLevel(logging.INFO)
        self._activity_logger.handlers = []
        activity_file = self.log_dir / "activity.log"
        activity_handler = RotatingFileHandler(
            activity_file,
            maxBytes=20 * 1024 * 1024,
            backupCount=10
        )
        activity_formatter = logging.Formatter(
            "%(asctime)s | [%(levelname)s] | %(message)s"
        )
        activity_handler.setFormatter(activity_formatter)
        self._activity_logger.addHandler(activity_handler)
        
        # Callbacks for real-time bridging (dashboard/websockets)
        self._callbacks = []
    
    def register_callback(self, callback):
        """Register a callback for all log events."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            
    def _trigger_callbacks(self, log_data: Dict[str, Any]):
        """Trigger all registered callbacks with log data."""
        for callback in self._callbacks:
            try:
                callback(log_data)
            except Exception as e:
                # Don't let callback errors crash the logger
                print(f"Error in log callback: {e}", file=sys.stderr)

    def log_activity(self, message: str, level: str = "INFO"):
        """Log a high-level activity for the audit trail."""
        lvl = getattr(logging, level.upper(), logging.INFO)
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "type": "activity",
            "message": message
        }
        self._activity_logger.log(lvl, message)
        self._trigger_callbacks(log_data)
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._logger.debug(message, extra=extra or {})
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._logger.info(message, extra=extra or {})
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._logger.warning(message, extra=extra or {})
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._logger.error(message, extra=extra or {})
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._logger.critical(message, extra=extra or {})
    
    def log_agent_action(self, agent_id: str, action: str, 
                        details: Optional[Dict[str, Any]] = None):
        """Log an agent action."""
        self.info(
            f"Agent {agent_id}: {action}",
            extra={
                "agent_id": agent_id,
                "context": details or {}
            }
        )
        self._trigger_callbacks({
            "type": "agent_action",
            "agent_id": agent_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def log_task_event(self, task_id: str, event: str,
                      details: Optional[Dict[str, Any]] = None):
        """Log a task event."""
        self.info(
            f"Task {task_id}: {event}",
            extra={
                "task_id": task_id,
                "context": details or {}
            }
        )
        self._trigger_callbacks({
            "type": "task_event",
            "task_id": task_id,
            "event": event,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def log_tool_execution(self, tool_name: str, success: bool,
                          duration_ms: float, details: Optional[Dict[str, Any]] = None):
        """Log a tool execution."""
        status = "succeeded" if success else "failed"
        self.info(
            f"Tool {tool_name} {status} in {duration_ms}ms",
            extra={
                "context": {
                    "tool": tool_name,
                    "success": success,
                    "duration_ms": duration_ms,
                    **(details or {})
                }
            }
        )


# Global logger instance
_logger: Optional[GraceLogger] = None


def get_logger() -> GraceLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = GraceLogger()
    return _logger