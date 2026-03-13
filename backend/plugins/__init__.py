"""
Plugins - Plugin system for Open Grace.

Enables third-party extensions for:
- Custom tools
- Custom agents
- Custom memory backends
- Event handlers
"""

from backend.plugins.sdk import Plugin, PluginMetadata, tool, agent
from backend.plugins.manager import PluginManager, get_plugin_manager
from backend.plugins.loader import PluginLoader

__all__ = [
    "Plugin",
    "PluginMetadata",
    "tool",
    "agent",
    "PluginManager",
    "get_plugin_manager",
    "PluginLoader",
]