"""
Open Grace TaskForge AI - A Local AI Operating System

Open Grace is a secure, modular, local-first AI platform for automation,
research, coding assistance, and autonomous task orchestration.

The platform consists of:
- Open Grace: The overarching platform and ecosystem
- TaskForge: The AI agent engine that powers automation

Usage:
    from open_grace import GraceKernel
    
    grace = GraceKernel()
    grace.initialize()
    result = grace.execute("Organize my downloads folder")
"""

__version__ = "0.3.0"
__author__ = "opengrace-ii"
__license__ = "MIT"

from open_grace.kernel.orchestrator import GraceOrchestrator
from open_grace.config.settings import GraceSettings

__all__ = [
    "GraceOrchestrator",
    "GraceSettings",
    "__version__",
]