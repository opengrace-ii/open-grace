"""
API - REST API for Open Grace.

Provides HTTP endpoints for:
- Task management
- Agent control
- System monitoring
- Real-time updates via WebSockets
"""

from backend.api.server import APIServer

__all__ = ["APIServer"]