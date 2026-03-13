"""
Plugin Manager - Manages plugin lifecycle and integration.

Coordinates plugins with the rest of the Open Grace system.
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from open_grace.plugins.sdk import Plugin, PluginMetadata, PluginType
from open_grace.plugins.loader import PluginLoader, PluginValidator
from open_grace.kernel.orchestrator import GraceOrchestrator, get_orchestrator
from open_grace.tools.registry import ToolRegistry, get_tool_registry
from open_grace.observability.logger import get_logger


@dataclass
class PluginState:
    """State of a loaded plugin."""
    plugin: Plugin
    loaded_at: str
    initialized: bool = False
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class PluginManager:
    """
    Manages the lifecycle of plugins.
    
    Responsibilities:
    - Load and initialize plugins
    - Register plugin tools with the system
    - Register plugin agents with the orchestrator
    - Handle plugin configuration
    - Manage plugin dependencies
    
    Usage:
        manager = PluginManager()
        await manager.initialize()
        
        # Load all plugins
        await manager.load_all_plugins()
        
        # Get a tool from a plugin
        tool = manager.get_tool("my_plugin", "my_tool")
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 plugin_dirs: Optional[List[str]] = None):
        """
        Initialize the plugin manager.
        
        Args:
            config_path: Path to plugin configuration
            plugin_dirs: Directories to search for plugins
        """
        self.config_path = config_path or os.path.expanduser("~/.open_grace/plugins.yaml")
        self.loader = PluginLoader(plugin_dirs)
        self.logger = get_logger()
        
        # State
        self._plugins: Dict[str, PluginState] = {}
        self._config: Dict[str, Any] = {}
        
        # System integrations
        self._orchestrator: Optional[GraceOrchestrator] = None
        self._tool_registry: Optional[Any] = None
    
    async def initialize(self):
        """Initialize the plugin manager."""
        self.logger.info("Initializing Plugin Manager")
        
        # Load configuration
        self._load_config()
        
        # Get system references
        self._orchestrator = await get_orchestrator()
        self._tool_registry = get_tool_registry()
    
    def _load_config(self):
        """Load plugin configuration."""
        import yaml
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                self.logger.error(f"Failed to load plugin config: {e}")
                self._config = {}
        else:
            self._config = {"plugins": {}}
    
    def _save_config(self):
        """Save plugin configuration."""
        import yaml
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Failed to save plugin config: {e}")
    
    async def load_plugin(self, plugin_source: str) -> Optional[Plugin]:
        """
        Load a single plugin.
        
        Args:
            plugin_source: Path to plugin file or module name
            
        Returns:
            Loaded plugin or None
        """
        # Determine source type
        if os.path.isfile(plugin_source):
            plugin = self.loader.load_from_file(plugin_source)
        elif os.path.isdir(plugin_source):
            plugins = self.loader.load_from_directory(plugin_source)
            plugin = plugins[0] if plugins else None
        else:
            plugin = self.loader.load_from_module(plugin_source)
        
        if plugin is None:
            return None
        
        # Validate plugin
        errors = PluginValidator.validate_plugin(plugin)
        if errors:
            self.logger.error(f"Plugin validation failed: {errors}")
            return None
        
        # Check for conflicts
        if plugin.metadata.name in self._plugins:
            self.logger.warning(f"Plugin {plugin.metadata.name} already loaded")
            return None
        
        # Get plugin configuration
        plugin_config = self._config.get("plugins", {}).get(
            plugin.metadata.name, {}
        )
        
        # Initialize plugin
        try:
            success = plugin.initialize(plugin_config)
            if not success:
                self.logger.error(f"Plugin {plugin.metadata.name} initialization failed")
                return None
        except Exception as e:
            self.logger.error(f"Plugin {plugin.metadata.name} initialization error: {e}")
            return None
        
        # Store plugin state
        self._plugins[plugin.metadata.name] = PluginState(
            plugin=plugin,
            loaded_at=datetime.now().isoformat(),
            initialized=True,
            config=plugin_config
        )
        
        # Register with systems
        await self._register_plugin(plugin)
        
        self.logger.info(f"Plugin loaded and initialized: {plugin.metadata.name}")
        return plugin
    
    async def load_all_plugins(self) -> List[Plugin]:
        """
        Load all available plugins.
        
        Returns:
            List of loaded plugins
        """
        loaded = []
        
        # Load from loader
        plugins = self.loader.load_all()
        
        for plugin in plugins:
            # Check if enabled in config
            plugin_config = self._config.get("plugins", {}).get(
                plugin.metadata.name, {}
            )
            
            if plugin_config.get("enabled", True):
                loaded_plugin = await self.load_plugin_from_instance(plugin)
                if loaded_plugin:
                    loaded.append(loaded_plugin)
        
        return loaded
    
    async def load_plugin_from_instance(self, plugin: Plugin) -> Optional[Plugin]:
        """Load a plugin from an existing instance."""
        # Validate
        errors = PluginValidator.validate_plugin(plugin)
        if errors:
            self.logger.error(f"Plugin validation failed: {errors}")
            return None
        
        # Check for conflicts
        if plugin.metadata.name in self._plugins:
            self.logger.warning(f"Plugin {plugin.metadata.name} already loaded")
            return None
        
        # Get configuration
        plugin_config = self._config.get("plugins", {}).get(
            plugin.metadata.name, {}
        )
        
        # Initialize
        try:
            success = plugin.initialize(plugin_config)
            if not success:
                return None
        except Exception as e:
            self.logger.error(f"Plugin initialization error: {e}")
            return None
        
        # Store and register
        self._plugins[plugin.metadata.name] = PluginState(
            plugin=plugin,
            loaded_at=datetime.now().isoformat(),
            initialized=True,
            config=plugin_config
        )
        
        await self._register_plugin(plugin)
        
        return plugin
    
    async def _register_plugin(self, plugin: Plugin):
        """Register plugin components with the system."""
        # Register tools
        for tool_name, tool_def in plugin.get_tools().items():
            full_name = f"{plugin.metadata.name}.{tool_name}"
            if self._tool_registry:
                self._tool_registry.register(
                    name=full_name,
                    function=tool_def.function,
                    description=tool_def.description,
                    permission_level=tool_def.permission_level
                )
        
        # Register agents
        for agent_name, agent_def in plugin.get_agents().items():
            if self._orchestrator:
                await self._orchestrator.register_agent(
                    agent_type=agent_def.name,
                    name=f"{plugin.metadata.name}.{agent_name}",
                    capabilities=agent_def.capabilities,
                    agent_instance=agent_def.agent_class
                )
        
        # Register event handlers
        for event_type, handlers in plugin.get_event_handlers().items():
            if self._orchestrator:
                for handler in handlers:
                    self._orchestrator.on_event(event_type, handler)
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if unloaded successfully
        """
        if plugin_name not in self._plugins:
            return False
        
        state = self._plugins.pop(plugin_name)
        
        try:
            state.plugin.shutdown()
            self.logger.info(f"Plugin unloaded: {plugin_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name."""
        state = self._plugins.get(name)
        return state.plugin if state else None
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins."""
        return {name: state.plugin for name, state in self._plugins.items()}
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin."""
        state = self._plugins.get(name)
        if not state:
            return None
        
        return {
            "name": state.plugin.metadata.name,
            "version": state.plugin.metadata.version,
            "description": state.plugin.metadata.description,
            "author": state.plugin.metadata.author,
            "type": state.plugin.metadata.plugin_type.value,
            "loaded_at": state.loaded_at,
            "initialized": state.initialized,
            "tools": list(state.plugin.get_tools().keys()),
            "agents": list(state.plugin.get_agents().keys()),
        }
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with info."""
        return [
            self.get_plugin_info(name)
            for name in self._plugins.keys()
        ]
    
    def get_tool(self, plugin_name: str, tool_name: str) -> Optional[Any]:
        """Get a tool from a plugin."""
        state = self._plugins.get(plugin_name)
        if not state:
            return None
        
        tools = state.plugin.get_tools()
        tool_def = tools.get(tool_name)
        return tool_def.function if tool_def else None
    
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin in configuration."""
        if "plugins" not in self._config:
            self._config["plugins"] = {}
        
        if plugin_name not in self._config["plugins"]:
            self._config["plugins"][plugin_name] = {}
        
        self._config["plugins"][plugin_name]["enabled"] = True
        self._save_config()
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin in configuration."""
        if "plugins" not in self._config:
            self._config["plugins"] = {}
        
        if plugin_name not in self._config["plugins"]:
            self._config["plugins"][plugin_name] = {}
        
        self._config["plugins"][plugin_name]["enabled"] = False
        self._save_config()


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


async def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
        await _plugin_manager.initialize()
    return _plugin_manager


def set_plugin_manager(manager: PluginManager):
    """Set the global plugin manager instance."""
    global _plugin_manager
    _plugin_manager = manager