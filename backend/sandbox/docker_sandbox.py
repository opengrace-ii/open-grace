"""
Docker Sandbox - Secure containerized execution environment.

Isolates potentially dangerous operations in Docker containers
with resource limits and security constraints.
"""

import os
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

try:
    import docker
    from docker.models.containers import Container
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from backend.observability.logger import get_logger


@dataclass
class SandboxConfig:
    """Configuration for Docker sandbox."""
    image: str = "python:3.11-slim"
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    timeout: int = 300  # seconds
    network_enabled: bool = False
    volumes: Optional[Dict[str, Dict[str, str]]] = None
    environment: Optional[Dict[str, str]] = None
    working_dir: str = "/workspace"


@dataclass
class ExecutionResult:
    """Result of sandboxed execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    container_id: Optional[str] = None


class DockerSandbox:
    """
    Secure execution environment using Docker containers.
    
    Features:
    - Resource limits (CPU, memory)
    - Network isolation
    - Volume mounting with restrictions
    - Automatic cleanup
    - Execution timeout
    
    Usage:
        sandbox = DockerSandbox()
        
        # Execute shell command
        result = await sandbox.execute_shell("ls -la", config=SandboxConfig())
        
        # Execute Python code
        result = await sandbox.execute_python("print('Hello')", config=SandboxConfig())
        
        # Execute with file input
        result = await sandbox.execute_with_files(
            command="python process.py",
            files={"process.py": "print('Processing')"},
            config=SandboxConfig()
        )
    """
    
    def __init__(self):
        """Initialize the Docker sandbox."""
        self.logger = get_logger()
        self._client = None
        self._active_containers: Dict[str, Container] = {}
        
        if not DOCKER_AVAILABLE:
            self.logger.warning("Docker SDK not available. Sandbox disabled.")
    
    def _get_client(self):
        """Get or create Docker client."""
        if self._client is None and DOCKER_AVAILABLE:
            try:
                self._client = docker.from_env()
            except Exception as e:
                self.logger.error(f"Failed to connect to Docker: {e}")
        return self._client
    
    async def execute_shell(self, command: str, 
                          config: Optional[SandboxConfig] = None) -> ExecutionResult:
        """
        Execute a shell command in a sandboxed container.
        
        Args:
            command: Shell command to execute
            config: Sandbox configuration
            
        Returns:
            ExecutionResult
        """
        config = config or SandboxConfig()
        
        return await self._execute_in_container(
            command=command,
            config=config
        )
    
    async def execute_python(self, code: str,
                           config: Optional[SandboxConfig] = None) -> ExecutionResult:
        """
        Execute Python code in a sandboxed container.
        
        Args:
            code: Python code to execute
            config: Sandbox configuration
            
        Returns:
            ExecutionResult
        """
        config = config or SandboxConfig()
        
        # Create a temporary directory for the code
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "script.py")
        
        try:
            # Write code to file
            with open(script_path, 'w') as f:
                f.write(code)
            
            # Execute with the file mounted
            result = await self._execute_in_container(
                command=f"python {config.working_dir}/script.py",
                config=config,
                host_files={temp_dir: {"bind": config.working_dir, "mode": "ro"}}
            )
            
            return result
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def execute_with_files(self, command: str,
                                files: Dict[str, str],
                                config: Optional[SandboxConfig] = None) -> ExecutionResult:
        """
        Execute a command with input files.
        
        Args:
            command: Command to execute
            files: Dictionary of filename -> content
            config: Sandbox configuration
            
        Returns:
            ExecutionResult
        """
        config = config or SandboxConfig()
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Write all files
            for filename, content in files.items():
                file_path = os.path.join(temp_dir, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Execute with files mounted
            result = await self._execute_in_container(
                command=command,
                config=config,
                host_files={temp_dir: {"bind": config.working_dir, "mode": "rw"}}
            )
            
            return result
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _execute_in_container(self, command: str,
                                   config: SandboxConfig,
                                   host_files: Optional[Dict[str, Dict[str, str]]] = None
                                   ) -> ExecutionResult:
        """
        Execute command in a Docker container.
        
        Args:
            command: Command to run
            config: Sandbox configuration
            host_files: Additional files to mount
            
        Returns:
            ExecutionResult
        """
        client = self._get_client()
        
        if client is None:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="Docker not available",
                exit_code=-1,
                duration_ms=0
            )
        
        container = None
        start_time = datetime.now()
        
        try:
            # Prepare volumes
            volumes = config.volumes or {}
            if host_files:
                volumes.update(host_files)
            
            # Create container
            container = client.containers.run(
                image=config.image,
                command=["sh", "-c", command],
                detach=True,
                mem_limit=config.memory_limit,
                cpu_quota=int(config.cpu_limit * 100000),
                network_disabled=not config.network_enabled,
                volumes=volumes,
                environment=config.environment,
                working_dir=config.working_dir,
                auto_remove=False  # We'll remove manually for better control
            )
            
            container_id = container.id[:12]
            self._active_containers[container_id] = container
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=config.timeout)
                exit_code = result.get('StatusCode', -1)
            except Exception:
                # Timeout or error
                exit_code = -1
            
            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
            
            # Calculate duration
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                success=exit_code == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=duration_ms,
                container_id=container_id
            )
            
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"Sandbox execution error: {e}")
            
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration_ms
            )
            
        finally:
            # Cleanup container
            if container:
                try:
                    container.stop(timeout=5)
                    container.remove(force=True)
                except:
                    pass
                
                # Remove from active containers
                if container_id in self._active_containers:
                    del self._active_containers[container_id]
    
    async def cleanup(self):
        """Clean up all active containers."""
        for container_id, container in list(self._active_containers.items()):
            try:
                container.stop(timeout=5)
                container.remove(force=True)
            except:
                pass
        
        self._active_containers.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get sandbox status."""
        return {
            "docker_available": DOCKER_AVAILABLE,
            "client_connected": self._client is not None,
            "active_containers": len(self._active_containers)
        }