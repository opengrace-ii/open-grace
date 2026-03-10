"""
Plugin SDK - Software Development Kit for Open Grace plugins.

Provides decorators and base classes for creating plugins.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass
from enum import Enum


class PluginType(Enum):
    """Types of plugins."""
    TOOL = "tool"
    AGENT = "agent"
    MEMORY = "memory"
    EVENT_HANDLER = "event_handler"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}


@dataclass
class ToolDefinition:
    """Definition of a tool provided by a plugin."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    permission_level: str = "normal"  # "low", "normal", "high"


@dataclass
class AgentDefinition:
    """Definition of an agent provided by a plugin."""
    name: str
    description: str
    agent_class: Type
    capabilities: List[str]


class Plugin(ABC):
    """
    Base class for Open Grace plugins.
    
    Plugins extend Open Grace functionality by providing:
    - Custom tools
    - Custom agents
    - Event handlers
    - Custom memory backends
    
    Usage:
        class MyPlugin(Plugin):
            def __init__(self):
                super().__init__(
                    metadata=PluginMetadata(
                        name="my_plugin",
                        version="1.0.0",
                        description="My custom plugin",
                        author="Developer",
                        plugin_type=PluginType.TOOL
                    )
                )
            
            def initialize(self, config):
                # Register tools
                self.register_tool("my_tool", self.my_function)
    """
    
    def __init__(self, metadata: PluginMetadata):
        """
        Initialize the plugin.
        
        Args:
            metadata: Plugin metadata
        """
        self.metadata = metadata
        self._tools: Dict[str, ToolDefinition] = {}
        self._agents: Dict[str, AgentDefinition] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._config: Dict[str, Any] = {}
        self._initialized = False
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration
            
        Returns:
            True if initialization successful
        """
        pass
    
    def shutdown(self):
        """Shutdown the plugin. Override to clean up resources."""
        pass
    
    def register_tool(self, name: str, function: Callable,
                     description: Optional[str] = None,
                     permission_level: str = "normal") -> ToolDefinition:
        """
        Register a tool provided by this plugin.
        
        Args:
            name: Tool name
            function: Tool function
            description: Tool description (auto-generated if not provided)
            permission_level: Required permission level
            
        Returns:
            ToolDefinition
        """
        # Auto-generate description from docstring
        if description is None and function.__doc__:
            description = function.__doc__.strip().split('\n')[0]
        elif description is None:
            description = f"Tool: {name}"
        
        # Extract parameters from function signature
        sig = inspect.signature(function)
        parameters = {}
        for param_name, param in sig.parameters.items():
            param_info = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any",
                "required": param.default == inspect.Parameter.empty
            }
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            parameters[param_name] = param_info
        
        # Extract return type
        return_annotation = sig.return_annotation
        returns = {"type": str(return_annotation) if return_annotation != inspect.Signature.empty else "any"}
        
        tool_def = ToolDefinition(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            returns=returns,
            permission_level=permission_level
        )
        
        self._tools[name] = tool_def
        return tool_def
    
    def register_agent(self, name: str, agent_class: Type,
                      description: str,
                      capabilities: List[str]) -> AgentDefinition:
        """
        Register an agent provided by this plugin.
        
        Args:
            name: Agent name
            agent_class: Agent class
            description: Agent description
            capabilities: List of capabilities
            
        Returns:
            AgentDefinition
        """
        agent_def = AgentDefinition(
            name=name,
            description=description,
            agent_class=agent_class,
            capabilities=capabilities
        )
        
        self._agents[name] = agent_def
        return agent_def
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def get_tools(self) -> Dict[str, ToolDefinition]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_agents(self) -> Dict[str, AgentDefinition]:
        """Get all registered agents."""
        return self._agents.copy()
    
    def get_event_handlers(self) -> Dict[str, List[Callable]]:
        """Get all registered event handlers."""
        return self._event_handlers.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self._config.copy()


# Decorators for easy plugin creation

def tool(name: Optional[str] = None, 
         description: Optional[str] = None,
         permission_level: str = "normal"):
    """
    Decorator to mark a function as a tool.
    
    Usage:
        @tool(name="greet", description="Greet a user")
        def greet(name: str) -> str:
            return f"Hello, {name}!"
    """
    def decorator(func: Callable) -> Callable:
        func._is_tool = True
        func._tool_name = name or func.__name__
        func._tool_description = description or func.__doc__ or ""
        func._tool_permission_level = permission_level
        return func
    return decorator


def agent(name: Optional[str] = None,
          description: Optional[str] = None,
          capabilities: Optional[List[str]] = None):
    """
    Decorator to mark a class as an agent.
    
    Usage:
        @agent(name="custom_agent", capabilities=["coding"])
        class CustomAgent(BaseAgent):
            pass
    """
    def decorator(cls: Type) -> Type:
        cls._is_agent = True
        cls._agent_name = name or cls.__name__
        cls._agent_description = description or cls.__doc__ or ""
        cls._agent_capabilities = capabilities or []
        return cls
    return decorator


def event_handler(event_type: str):
    """
    Decorator to mark a function as an event handler.
    
    Usage:
        @event_handler("task.completed")
        def on_task_completed(event_data):
            print(f"Task completed: {event_data}")
    """
    def decorator(func: Callable) -> Callable:
        func._is_event_handler = True
        func._event_type = event_type
        return func
    return decorator


# Example plugin implementations for reference

class ExampleToolPlugin(Plugin):
    """Example plugin demonstrating tool registration."""
    
    def __init__(self):
        super().__init__(
            metadata=PluginMetadata(
                name="example_tools",
                version="1.0.0",
                description="Example tool plugin",
                author="Open Grace",
                plugin_type=PluginType.TOOL
            )
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        self._config = config
        
        # Register tools
        self.register_tool("echo", self.echo)
        self.register_tool("reverse", self.reverse)
        
        return True
    
    def echo(self, message: str) -> str:
        """Echo a message back."""
        return message
    
    def reverse(self, text: str) -> str:
        """Reverse a string."""
        return text[::-1]