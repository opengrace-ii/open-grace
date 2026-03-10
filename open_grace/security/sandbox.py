"""
Sandbox System for TaskForge.
Provides isolated execution environments for potentially dangerous operations.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager
import subprocess
import json


@dataclass
class SandboxConfig:
    """Configuration for a sandbox environment."""
    allow_network: bool = False
    allow_file_write: bool = True
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_memory_mb: int = 512
    timeout_seconds: int = 60
    allowed_paths: List[str] = None
    blocked_paths: List[str] = None
    
    def __post_init__(self):
        if self.allowed_paths is None:
            self.allowed_paths = []
        if self.blocked_paths is None:
            self.blocked_paths = [
                "/etc/passwd",
                "/etc/shadow",
                "/root",
                os.path.expanduser("~/.ssh"),
                os.path.expanduser("~/.gnupg"),
            ]


class Sandbox:
    """
    A sandboxed execution environment.
    
    Features:
    - Temporary working directory
    - Path restrictions
    - Resource limits
    - Execution isolation
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None, 
                 working_dir: Optional[str] = None):
        self.config = config or SandboxConfig()
        self.working_dir = working_dir
        self._temp_dir: Optional[str] = None
        self._created = False
    
    def create(self) -> str:
        """Create the sandbox environment."""
        if self.working_dir:
            self._temp_dir = self.working_dir
            Path(self._temp_dir).mkdir(parents=True, exist_ok=True)
        else:
            self._temp_dir = tempfile.mkdtemp(prefix="taskforge_sandbox_")
        
        self._created = True
        return self._temp_dir
    
    def cleanup(self):
        """Clean up the sandbox environment."""
        if self._temp_dir and not self.working_dir:
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup sandbox: {e}")
        self._created = False
    
    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed in the sandbox."""
        path = os.path.abspath(path)
        
        # Check blocked paths
        for blocked in self.config.blocked_paths:
            if path.startswith(os.path.abspath(blocked)):
                return False
        
        # Check allowed paths
        if self.config.allowed_paths:
            for allowed in self.config.allowed_paths:
                if path.startswith(os.path.abspath(allowed)):
                    return True
            # If allowed_paths is set, path must be in one of them
            return False
        
        return True
    
    def resolve_path(self, path: str) -> str:
        """Resolve a path relative to the sandbox."""
        if os.path.isabs(path):
            return path
        return os.path.join(self._temp_dir, path)
    
    def execute(self, command: List[str], **kwargs) -> Dict[str, Any]:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Command and arguments as list
            **kwargs: Additional subprocess arguments
            
        Returns:
            Dict with stdout, stderr, returncode
        """
        if not self._created:
            self.create()
        
        # Set up environment
        env = os.environ.copy()
        if not self.config.allow_network:
            # Disable network by setting proxy to invalid
            env["http_proxy"] = "http://127.0.0.1:1"
            env["https_proxy"] = "http://127.0.0.1:1"
        
        # Run command
        try:
            result = subprocess.run(
                command,
                cwd=self._temp_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                env=env,
                **kwargs
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {self.config.timeout_seconds} seconds",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def write_file(self, path: str, content: str) -> bool:
        """Write a file in the sandbox."""
        if not self.config.allow_file_write:
            return False
        
        full_path = self.resolve_path(path)
        
        if not self.is_path_allowed(full_path):
            return False
        
        try:
            Path(full_path).parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def read_file(self, path: str) -> Optional[str]:
        """Read a file from the sandbox."""
        full_path = self.resolve_path(path)
        
        if not self.is_path_allowed(full_path):
            return None
        
        try:
            with open(full_path, "r") as f:
                return f.read()
        except Exception:
            return None
    
    def __enter__(self):
        self.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class DockerSandbox:
    """
    Docker-based sandbox for maximum isolation.
    
    Requires Docker to be installed and running.
    """
    
    def __init__(self, image: str = "python:3.11-slim", 
                 config: Optional[SandboxConfig] = None):
        self.image = image
        self.config = config or SandboxConfig()
        self.container_id: Optional[str] = None
    
    def create(self) -> bool:
        """Create a Docker container for sandboxing."""
        try:
            # Create container
            result = subprocess.run(
                ["docker", "run", "-d", "--rm", "-i", 
                 "--network", "none" if not self.config.allow_network else "bridge",
                 "--memory", f"{self.config.max_memory_mb}m",
                 "--name", f"taskforge_sandbox_{os.getpid()}",
                 self.image, "sleep", "3600"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.container_id = result.stdout.strip()
                return True
            else:
                print(f"Docker error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("Docker not found. Please install Docker.")
            return False
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute a command in the Docker container."""
        if not self.container_id:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Sandbox not created",
                "returncode": -1
            }
        
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_id, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {self.config.timeout_seconds} seconds",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def copy_to(self, src: str, dst: str) -> bool:
        """Copy a file into the container."""
        if not self.container_id:
            return False
        
        result = subprocess.run(
            ["docker", "cp", src, f"{self.container_id}:{dst}"],
            capture_output=True
        )
        return result.returncode == 0
    
    def copy_from(self, src: str, dst: str) -> bool:
        """Copy a file from the container."""
        if not self.container_id:
            return False
        
        result = subprocess.run(
            ["docker", "cp", f"{self.container_id}:{src}", dst],
            capture_output=True
        )
        return result.returncode == 0
    
    def cleanup(self):
        """Stop and remove the container."""
        if self.container_id:
            subprocess.run(
                ["docker", "stop", self.container_id],
                capture_output=True
            )
            self.container_id = None
    
    def __enter__(self):
        self.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


@contextmanager
def sandbox_context(config: Optional[SandboxConfig] = None):
    """Context manager for sandbox execution."""
    sandbox = Sandbox(config)
    try:
        sandbox.create()
        yield sandbox
    finally:
        sandbox.cleanup()
