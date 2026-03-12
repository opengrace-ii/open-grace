import logging
import os
from pathlib import Path

# Ensure logs directory exists at the root of the project
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Required format: 2026-03-12 15:02:21 | backend | ERROR | login token generation failed
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, log_file: str) -> logging.Logger:
    """Setup a standard logger that writes to a specific file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False # Prevent double logging if root logger is also configured
    
    # Avoid duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_DIR / log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Pre-configure required loggers
system_logger = setup_logger("system", "system.log")
backend_logger = setup_logger("backend", "backend.log")
frontend_logger = setup_logger("frontend", "frontend.log")
diagnostics_logger = setup_logger("diagnostics", "diagnostics.log")

def get_diagnostics_logger() -> logging.Logger:
    return diagnostics_logger

def get_backend_logger() -> logging.Logger:
    return backend_logger

def get_system_logger() -> logging.Logger:
    return system_logger

def get_frontend_logger() -> logging.Logger:
    return frontend_logger

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class CrashReport:
    id: str
    timestamp: str
    url: str
    method: str
    error: str
    traceback: str
    request_body: Optional[str] = None
    system_state: Dict[str, Any] = field(default_factory=dict)

class CrashStore:
    def __init__(self):
        self.reports: List[CrashReport] = []
        self.max_size = 20
    
    def add_report(self, report: CrashReport):
        self.reports.insert(0, report)
        if len(self.reports) > self.max_size:
            self.reports.pop()
    
    def get_reports(self) -> List[CrashReport]:
        return self.reports

crash_store = CrashStore()
