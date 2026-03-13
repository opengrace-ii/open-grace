"""
Plugin Loader - Dynamic plugin loading for Open Grace.

Supports loading plugins from:
- Python modules (local files)
- Python packages (installed via pip)
- Git repositories (future)
"""

import os
import sys
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Type
from pathlib import Path

from open_grace.plugins.sdk import Plugin, PluginMetadata
from open_grace.observability.logger import get_logger


class PluginLoader:
    """
    Loads plugins dynamically from various sources.
    
    Usage:
        loader = PluginLoader()
        
        # Load from file
        plugin = loader.load_from_file("/path/to/plugin.py")
        
        # Load from directory
        plugins = loader.load_from_directory("/path/to/plugins/")
        
        # Load from module
        plugin = loader.load_from_module("my_plugin_module")
    """
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        Initialize the plugin loader.
        
        Args:
            plugin_dirs: Directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or [
            os.path.expanduser("~/.open_grace/plugins"),
            "/usr/share/open_grace/plugins"
        ]
        self.logger = get_logger()
        self._loaded_plugins: Dict[str, Plugin] = {}
        
        # Ensure plugin directories exist
        for dir_path in self.plugin_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def load_from_file(self, file_path: str) -> Optional[Plugin]:
        """
        Load a plugin from a Python file.
        
        Args:
            file_path: Path to the plugin file
            
        Returns:
            Loaded Plugin instance or None
        """
        try:
            # Create module spec
            module_name = Path(file_path).stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if spec is None or spec.loader is None:
                self.logger.error(f"Could not load plugin from {file_path}")
                return None
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find Plugin class
            plugin_class = self._find_plugin_class(module)
            
            if plugin_class is None:
                self.logger.error(f"No Plugin class found in {file_path}")
                return None
            
            # Instantiate plugin
            plugin = plugin_class()
            
            self.logger.info(f"Loaded plugin from {file_path}: {plugin.metadata.name}")
            return plugin
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {file_path}: {e}")
            return None
    
    def load_from_module(self, module_name: str) -> Optional[Plugin]:
        """
        Load a plugin from an installed Python module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Loaded Plugin instance or None
        """
        try:
            # Import module
            module = importlib.import_module(module_name)
            
            # Find Plugin class
            plugin_class = self._find_plugin_class(module)
            
            if plugin_class is None:
                self.logger.error(f"No Plugin class found in module {module_name}")
                return None
            
            # Instantiate plugin
            plugin = plugin_class()
            
            self.logger.info(f"Loaded plugin from module {module_name}: {plugin.metadata.name}")
            return plugin
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin from module {module_name}: {e}")
            return None
    
    def load_from_directory(self, directory: str) -> List[Plugin]:
        """
        Load all plugins from a directory.
        
        Args:
            directory: Directory containing plugin files
            
        Returns:
            List of loaded plugins
        """
        plugins = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return plugins
        
        # Find all Python files
        for file_path in dir_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            plugin = self.load_from_file(str(file_path))
            if plugin:
                plugins.append(plugin)
        
        # Find all package directories
        for subdir in dir_path.iterdir():
            if subdir.is_dir() and (subdir / "__init__.py").exists():
                # Try to load as a package
                plugin = self._load_from_package(str(subdir))
                if plugin:
                    plugins.append(plugin)
        
        return plugins
    
    def _load_from_package(self, package_path: str) -> Optional[Plugin]:
        """Load a plugin from a package directory."""
        try:
            package_name = Path(package_path).name
            
            # Add to path if needed
            parent_dir = str(Path(package_path).parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            # Import package
            module = importlib.import_module(package_name)
            
            # Find Plugin class
            plugin_class = self._find_plugin_class(module)
            
            if plugin_class:
                plugin = plugin_class()
                self.logger.info(f"Loaded plugin from package {package_path}: {plugin.metadata.name}")
                return plugin
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin from package {package_path}: {e}")
            return None
    
    def load_all(self) -> List[Plugin]:
        """
        Load all plugins from configured directories.
        
        Returns:
            List of loaded plugins
        """
        all_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if Path(plugin_dir).exists():
                plugins = self.load_from_directory(plugin_dir)
                all_plugins.extend(plugins)
        
        return all_plugins
    
    def _find_plugin_class(self, module) -> Optional[Type[Plugin]]:
        """
        Find a Plugin subclass in a module.
        
        Args:
            module: Module to search
            
        Returns:
            Plugin class or None
        """
        for name in dir(module):
            obj = getattr(module, name)
            
            if (isinstance(obj, type) and 
                issubclass(obj, Plugin) and 
                obj is not Plugin):
                return obj
        
        return None
    
    def get_loaded_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins."""
        return self._loaded_plugins.copy()
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if unloaded successfully
        """
        if plugin_name in self._loaded_plugins:
            plugin = self._loaded_plugins.pop(plugin_name)
            plugin.shutdown()
            return True
        return False


class PluginValidator:
    """Validates plugin structure and requirements."""
    
    @staticmethod
    def validate_metadata(metadata: PluginMetadata) -> List[str]:
        """
        Validate plugin metadata.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not metadata.name:
            errors.append("Plugin name is required")
        
        if not metadata.version:
            errors.append("Plugin version is required")
        
        if not metadata.description:
            errors.append("Plugin description is required")
        
        # Validate version format (simplified semver)
        if metadata.version:
            parts = metadata.version.split(".")
            if len(parts) < 2:
                errors.append("Version must follow semantic versioning (e.g., 1.0.0)")
        
        return errors
    
    @staticmethod
    def validate_plugin(plugin: Plugin) -> List[str]:
        """
        Validate a plugin instance.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate metadata
        metadata_errors = PluginValidator.validate_metadata(plugin.metadata)
        errors.extend(metadata_errors)
        
        # Check for required methods
        if not hasattr(plugin, 'initialize'):
            errors.append("Plugin must have an initialize method")
        
        return errors