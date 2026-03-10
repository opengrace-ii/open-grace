"""
Tests for Plugin System.
"""

import pytest
from open_grace.plugins.sdk import Plugin, PluginMetadata, PluginType, tool, agent
from open_grace.plugins.manager import PluginManager
from open_grace.plugins.loader import PluginLoader, PluginValidator


class TestPluginSDK:
    """Test suite for Plugin SDK."""
    
    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
    
    def test_plugin_initialization(self):
        """Test plugin initialization."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        class TestPlugin(Plugin):
            def initialize(self, config):
                return True
        
        plugin = TestPlugin(metadata)
        assert plugin.metadata == metadata
        assert plugin._initialized is False
    
    def test_tool_registration(self):
        """Test registering tools in a plugin."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        class TestPlugin(Plugin):
            def initialize(self, config):
                self.register_tool("echo", self.echo)
                return True
            
            def echo(self, message: str) -> str:
                """Echo a message."""
                return message
        
        plugin = TestPlugin(metadata)
        plugin.initialize({})
        
        tools = plugin.get_tools()
        assert "echo" in tools
        assert tools["echo"].name == "echo"
    
    def test_tool_decorator(self):
        """Test the @tool decorator."""
        @tool(name="greet", description="Greet someone")
        def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        assert hasattr(greet, '_is_tool')
        assert greet._tool_name == "greet"
        assert greet._tool_description == "Greet someone"


class TestPluginValidator:
    """Test suite for PluginValidator."""
    
    def test_validate_valid_metadata(self):
        """Test validating valid metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        errors = PluginValidator.validate_metadata(metadata)
        assert len(errors) == 0
    
    def test_validate_missing_name(self):
        """Test validating metadata with missing name."""
        metadata = PluginMetadata(
            name="",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        errors = PluginValidator.validate_metadata(metadata)
        assert any("name is required" in e for e in errors)
    
    def test_validate_invalid_version(self):
        """Test validating metadata with invalid version."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="invalid",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        errors = PluginValidator.validate_metadata(metadata)
        assert any("semantic versioning" in e for e in errors)


class TestPluginManager:
    """Test suite for PluginManager."""
    
    @pytest.fixture
    def manager(self):
        """Create plugin manager for testing."""
        return PluginManager()
    
    @pytest.mark.asyncio
    async def test_load_plugin_from_instance(self, manager):
        """Test loading a plugin from instance."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.TOOL
        )
        
        class TestPlugin(Plugin):
            def initialize(self, config):
                self.register_tool("test_tool", lambda: "test")
                return True
        
        plugin = TestPlugin(metadata)
        loaded = await manager.load_plugin_from_instance(plugin)
        
        assert loaded is not None
        assert loaded.metadata.name == "test_plugin"
    
    def test_get_plugin(self, manager):
        """Test getting a loaded plugin."""
        # This would need a loaded plugin first
        plugin = manager.get_plugin("nonexistent")
        assert plugin is None
    
    def test_list_plugins(self, manager):
        """Test listing plugins."""
        plugins = manager.list_plugins()
        assert isinstance(plugins, list)