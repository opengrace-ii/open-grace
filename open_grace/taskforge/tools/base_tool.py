"""
Base Tool class for TaskForge.
All tools must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base input schema for tools."""
    pass


class ToolOutput(BaseModel):
    """Base output schema for tools."""
    success: bool = Field(default=True, description="Whether the tool execution was successful")
    result: Any = Field(default=None, description="The result of the tool execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class BaseTool(ABC):
    """
    Abstract base class for all TaskForge tools.
    
    Each tool must define:
    - name: Unique identifier for the tool
    - description: Human-readable description
    - input_schema: Pydantic model for input validation
    """
    
    name: str = "base_tool"
    description: str = "Base tool class"
    input_schema: type[ToolInput] = ToolInput
    
    def __init__(self):
        self._validate_tool()
    
    def _validate_tool(self):
        """Validate that the tool is properly configured."""
        if not self.name or self.name == "base_tool":
            raise ValueError(f"Tool {self.__class__.__name__} must define a unique name")
        if not self.description:
            raise ValueError(f"Tool {self.__class__.__name__} must define a description")
    
    @abstractmethod
    def run(self, **kwargs) -> ToolOutput:
        """
        Execute the tool with the given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            ToolOutput: The result of the tool execution
        """
        pass
    
    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """
        Validate input against the tool's schema.
        
        Args:
            **kwargs: Input arguments to validate
            
        Returns:
            Dict of validated arguments
        """
        try:
            validated = self.input_schema(**kwargs)
            return validated.model_dump()
        except Exception as e:
            raise ValueError(f"Invalid input for tool '{self.name}': {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for this tool.
        
        Returns:
            Dict containing tool metadata and input schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.model_json_schema()
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
