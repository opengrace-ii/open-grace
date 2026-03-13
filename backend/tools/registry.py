"""
Tool Registry - Central registry for all tools in Open Grace.

Manages tool registration, discovery, and execution.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from backend.security.permissions import PermissionManager, get_permission_manager, ActionCategory
from backend.observability.logger import get_logger


@dataclass
class ToolInfo:
    """Information about a registered tool."""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, Any]
    permission_level: str
    registered_at: str
    source: str  # "builtin", "plugin:<name>", "user"
    call_count: int = 0


class ToolRegistry:
    """
    Central registry for all tools in Open Grace.
    
    Manages:
    - Tool registration
    - Permission checking
    - Execution logging
    - Tool discovery
    
    Usage:
        registry = ToolRegistry()
        
        # Register a tool
        registry.register("echo", echo_function, "Echo a message")
        
        # Execute a tool
        result = await registry.execute("echo", message="Hello")
    """
    
    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """
        Initialize the tool registry.
        
        Args:
            permission_manager: Permission manager for access control
        """
        self._tools: Dict[str, ToolInfo] = {}
        self.permission_manager = permission_manager or get_permission_manager()
        self.logger = get_logger()
    
    def register(self, name: str, function: Callable,
                description: str = "",
                parameters: Optional[Dict[str, Any]] = None,
                permission_level: str = "normal",
                source: str = "user") -> ToolInfo:
        """
        Register a tool.
        
        Args:
            name: Tool name (unique identifier)
            function: Tool function
            description: Tool description
            parameters: Parameter schema
            permission_level: "low", "normal", or "high"
            source: Source of the tool
            
        Returns:
            ToolInfo
        """
        if name in self._tools:
            self.logger.warning(f"Tool {name} already registered, overwriting")
        
        tool_info = ToolInfo(
            name=name,
            function=function,
            description=description,
            parameters=parameters or {},
            permission_level=permission_level,
            registered_at=datetime.now().isoformat(),
            source=source
        )
        
        self._tools[name] = tool_info
        self.logger.info(f"Tool registered: {name} (source: {source})")
        
        return tool_info
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.info(f"Tool unregistered: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[ToolInfo]:
        """Get tool information."""
        return self._tools.get(name)
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get tool function."""
        tool = self._tools.get(name)
        return tool.function if tool else None
    
    def list_tools(self, source: Optional[str] = None) -> List[ToolInfo]:
        """
        List registered tools.
        
        Args:
            source: Filter by source
            
        Returns:
            List of ToolInfo
        """
        tools = list(self._tools.values())
        if source:
            tools = [t for t in tools if t.source == source]
        return tools
    
    def list_tool_names(self) -> List[str]:
        """List all tool names."""
        return list(self._tools.keys())
    
    async def execute(self, name: str, **kwargs) -> Any:
        """
        Execute a tool with permission checking.
        
        Args:
            name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Tool result
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        # Check permissions for high-level tools
        if tool.permission_level == "high":
            action = f"execute_tool:{name}"
            if not self.permission_manager.check_permission(action, ActionCategory.SYSTEM):
                raise PermissionError(f"Permission denied for tool: {name}")
        
        # Log execution
        self.logger.log_tool_execution(
            tool_name=name,
            success=True,
            duration_ms=0,  # Will be updated
            details={"args": kwargs}
        )
        
        # Execute tool
        try:
            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**kwargs)
            else:
                result = tool.function(**kwargs)
            
            # Update stats
            tool.call_count += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tool execution failed: {name} - {e}")
            raise
    
    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON schema for a tool.
        
        Args:
            name: Tool name
            
        Returns:
            JSON schema dict
        """
        tool = self._tools.get(name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "permission_level": tool.permission_level
        }
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all tools."""
        return {
            name: self.get_tool_schema(name)
            for name in self._tools.keys()
        }
    
    def search_tools(self, query: str) -> List[ToolInfo]:
        """
        Search tools by name or description.
        
        Args:
            query: Search query
            
        Returns:
            Matching tools
        """
        query_lower = query.lower()
        return [
            tool for tool in self._tools.values()
            if query_lower in tool.name.lower()
            or query_lower in tool.description.lower()
        ]


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def set_tool_registry(registry: ToolRegistry):
    """Set the global tool registry instance."""
    global _registry
    _registry = registry