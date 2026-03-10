"""
Sandbox Executor - High-level interface for secure execution.

Integrates sandbox with the rest of the system.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from open_grace.sandbox.docker_sandbox import DockerSandbox, SandboxConfig, ExecutionResult
from open_grace.security.permissions import PermissionManager, get_permission_manager, ActionCategory
from open_grace.observability.logger import get_logger


class ExecutionType(Enum):
    """Types of execution."""
    SHELL = "shell"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


class SandboxExecutor:
    """
    High-level executor for running code securely.
    
    Provides:
    - Permission-based execution
    - Language-specific configurations
    - Resource management
    - Result caching
    
    Usage:
        executor = SandboxExecutor()
        
        # Execute with automatic permissions
        result = await executor.execute(
            code="print('Hello')",
            execution_type=ExecutionType.PYTHON
        )
        
        # Execute shell with permissions
        result = await executor.execute_shell(
            command="ls -la",
            require_permission=True
        )
    """
    
    # Language-specific Docker images
    LANGUAGE_IMAGES = {
        ExecutionType.PYTHON: "python:3.11-slim",
        ExecutionType.JAVASCRIPT: "node:20-slim",
        ExecutionType.TYPESCRIPT: "node:20-slim",
    }
    
    def __init__(self, permission_manager: Optional[PermissionManager] = None):
        """
        Initialize the executor.
        
        Args:
            permission_manager: Permission manager for access control
        """
        self.sandbox = DockerSandbox()
        self.permission_manager = permission_manager or get_permission_manager()
        self.logger = get_logger()
    
    async def execute(self, code: str,
                     execution_type: ExecutionType = ExecutionType.PYTHON,
                     config: Optional[SandboxConfig] = None,
                     require_permission: bool = True) -> ExecutionResult:
        """
        Execute code in sandbox.
        
        Args:
            code: Code to execute
            execution_type: Type of code
            config: Sandbox configuration
            require_permission: Whether to check permissions
            
        Returns:
            ExecutionResult
        """
        # Check permissions
        if require_permission:
            action = f"execute:{execution_type.value}"
            if not self.permission_manager.check_permission(action, ActionCategory.SYSTEM):
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="Permission denied: Sandbox execution not allowed",
                    exit_code=-1,
                    duration_ms=0
                )
        
        # Get language-specific config
        if config is None:
            config = self._get_default_config(execution_type)
        
        # Execute based on type
        if execution_type == ExecutionType.SHELL:
            return await self.sandbox.execute_shell(code, config)
        elif execution_type == ExecutionType.PYTHON:
            return await self.sandbox.execute_python(code, config)
        elif execution_type in (ExecutionType.JAVASCRIPT, ExecutionType.TYPESCRIPT):
            return await self._execute_node(code, config, execution_type)
        else:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Unsupported execution type: {execution_type}",
                exit_code=-1,
                duration_ms=0
            )
    
    async def execute_shell(self, command: str,
                           config: Optional[SandboxConfig] = None,
                           require_permission: bool = True) -> ExecutionResult:
        """
        Execute shell command.
        
        Args:
            command: Shell command
            config: Sandbox configuration
            require_permission: Whether to check permissions
            
        Returns:
            ExecutionResult
        """
        # Check permissions
        if require_permission:
            if not self.permission_manager.check_permission("execute:shell", ActionCategory.SYSTEM):
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="Permission denied: Shell execution not allowed",
                    exit_code=-1,
                    duration_ms=0
                )
        
        config = config or self._get_default_config(ExecutionType.SHELL)
        return await self.sandbox.execute_shell(command, config)
    
    async def execute_with_files(self, code: str,
                                files: Dict[str, str],
                                execution_type: ExecutionType = ExecutionType.PYTHON,
                                config: Optional[SandboxConfig] = None,
                                require_permission: bool = True) -> ExecutionResult:
        """
        Execute code with additional files.
        
        Args:
            code: Main code to execute
            files: Additional files to include
            execution_type: Type of code
            config: Sandbox configuration
            require_permission: Whether to check permissions
            
        Returns:
            ExecutionResult
        """
        # Check permissions
        if require_permission:
            action = f"execute:{execution_type.value}"
            if not self.permission_manager.check_permission(action, ActionCategory.SYSTEM):
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="Permission denied",
                    exit_code=-1,
                    duration_ms=0
                )
        
        # Add main code to files
        if execution_type == ExecutionType.PYTHON:
            files["main.py"] = code
            command = "python /workspace/main.py"
        elif execution_type == ExecutionType.JAVASCRIPT:
            files["main.js"] = code
            command = "node /workspace/main.js"
        elif execution_type == ExecutionType.TYPESCRIPT:
            files["main.ts"] = code
            command = "npx ts-node /workspace/main.ts"
        else:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Unsupported execution type: {execution_type}",
                exit_code=-1,
                duration_ms=0
            )
        
        config = config or self._get_default_config(execution_type)
        return await self.sandbox.execute_with_files(command, files, config)
    
    def _get_default_config(self, execution_type: ExecutionType) -> SandboxConfig:
        """Get default configuration for execution type."""
        image = self.LANGUAGE_IMAGES.get(execution_type, "python:3.11-slim")
        
        return SandboxConfig(
            image=image,
            memory_limit="512m",
            cpu_limit=1.0,
            timeout=300,
            network_enabled=False,
            working_dir="/workspace"
        )
    
    async def _execute_node(self, code: str, config: SandboxConfig, 
                           execution_type: ExecutionType) -> ExecutionResult:
        """Execute Node.js/TypeScript code."""
        files = {}
        
        if execution_type == ExecutionType.JAVASCRIPT:
            files["script.js"] = code
            command = "node /workspace/script.js"
        else:  # TypeScript
            files["script.ts"] = code
            command = "npx ts-node /workspace/script.ts"
        
        return await self.sandbox.execute_with_files(command, files, config)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [t.value for t in ExecutionType]
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        return {
            "sandbox": self.sandbox.get_status(),
            "supported_languages": self.get_supported_languages()
        }