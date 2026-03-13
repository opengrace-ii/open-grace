import logging
import os
from pathlib import Path
from backend.tracing.health import get_system_health

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
from typing import List, Optional, Dict, Any
import json

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

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "url": self.url,
            "method": self.method,
            "error": self.error,
            "traceback": self.traceback,
            "request_body": self.request_body,
            "system_state": self.system_state
        }

class CrashStore:
    def __init__(self, persistence_file: Path = LOG_DIR / "crashes.json"):
        self.persistence_file = persistence_file
        self.reports: List[CrashReport] = []
        self.max_size = 20
        self._load_reports()
    
    def _load_reports(self):
        if self.persistence_file.exists():
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    self.reports = []
                    for r in data:
                        report = CrashReport(
                            id=r["id"],
                            timestamp=r["timestamp"],
                            url=r["url"],
                            method=r["method"],
                            error=r["error"],
                            traceback=r["traceback"],
                            request_body=r.get("request_body"),
                            system_state=r.get("system_state", {})
                        )
                        self.reports.append(report)
            except Exception as e:
                print(f"Failed to load crash reports: {e}")
    
    def _save_reports(self):
        try:
            with open(self.persistence_file, "w") as f:
                json.dump([r.to_dict() for r in self.reports], f, indent=2)
        except Exception as e:
            print(f"Failed to save crash reports: {e}")

    def add_report(self, report: CrashReport):
        self.reports.insert(0, report)
        if len(self.reports) > self.max_size:
            self.reports.pop()
        self._save_reports()
    
    def get_reports(self) -> List[CrashReport]:
        return self.reports

crash_store = CrashStore()
