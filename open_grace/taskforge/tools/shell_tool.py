"""
Shell Tool for TaskForge.
Executes shell commands securely with permission gating.
"""

import subprocess
import shlex
from typing import List, Optional
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolOutput


class ShellToolInput(BaseModel):
    """Input schema for ShellTool."""
    command: str = Field(..., description="The shell command to execute")
    cwd: Optional[str] = Field(default=None, description="Working directory for the command")
    timeout: int = Field(default=30, description="Timeout in seconds")
    capture_output: bool = Field(default=True, description="Whether to capture stdout/stderr")


class ShellTool(BaseTool):
    """
    Tool for executing shell commands.
    
    Security features:
    - Command validation
    - Timeout protection
    - Working directory restriction
    """
    
    name = "shell"
    description = "Execute shell commands safely with output capture"
    input_schema = ShellToolInput
    
    # Dangerous commands that require extra scrutiny
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "> /dev/sda",
        "dd if=/dev/zero",
        "mkfs.",
        "format ",
        "del /f /s /q",
        "rd /s /q",
    ]
    
    def __init__(self, allowed_commands: Optional[List[str]] = None):
        super().__init__()
        self.allowed_commands = allowed_commands or []
    
    def is_dangerous(self, command: str) -> bool:
        """Check if a command contains dangerous patterns."""
        cmd_lower = command.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                return True
        return False
    
    def run(self, command: str, cwd: Optional[str] = None, timeout: int = 30, 
            capture_output: bool = True, **kwargs) -> ToolOutput:
        """
        Execute a shell command.
        
        Args:
            command: The shell command to execute
            cwd: Working directory for the command
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            ToolOutput with stdout, stderr, and return code
        """
        try:
            # Validate input
            self.validate_input(
                command=command,
                cwd=cwd,
                timeout=timeout,
                capture_output=capture_output
            )
            
            # Check for dangerous commands
            if self.is_dangerous(command):
                return ToolOutput(
                    success=False,
                    error=f"Command blocked: potentially dangerous operation detected"
                )
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            output = {
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "returncode": result.returncode,
                "command": command
            }
            
            success = result.returncode == 0
            error = result.stderr if result.returncode != 0 and capture_output else None
            
            return ToolOutput(
                success=success,
                result=output,
                error=error
            )
            
        except subprocess.TimeoutExpired:
            return ToolOutput(
                success=False,
                error=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Shell execution error: {str(e)}"
            )
    
    def run_safe(self, command_args: List[str], cwd: Optional[str] = None, 
                 timeout: int = 30) -> ToolOutput:
        """
        Execute a command without shell=True (safer).
        
        Args:
            command_args: List of command arguments
            cwd: Working directory
            timeout: Timeout in seconds
            
        Returns:
            ToolOutput with execution results
        """
        try:
            result = subprocess.run(
                command_args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": " ".join(command_args)
            }
            
            return ToolOutput(
                success=result.returncode == 0,
                result=output,
                error=result.stderr if result.returncode != 0 else None
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Safe shell execution error: {str(e)}"
            )
