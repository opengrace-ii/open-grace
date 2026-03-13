"""
SysAdmin Agent - Manages systems and infrastructure.

Specialized agent for:
- System administration tasks
- File and process management
- Service configuration
- Log analysis
- Security operations
"""

import os
import subprocess
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from open_grace.agents.base_agent import BaseAgent, AgentTask


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    stdout: str
    stderr: str
    returncode: int
    success: bool
    execution_time_ms: float


@dataclass
class SystemInfo:
    """System information snapshot."""
    hostname: str
    platform: str
    cpu_count: int
    memory_total_gb: float
    memory_available_gb: float
    disk_usage: Dict[str, Any]
    uptime_seconds: float


class SysAdminAgent(BaseAgent):
    """
    Agent specialized in system administration.
    
    Capabilities:
    - Execute shell commands
    - Manage files and directories
    - Monitor system resources
    - Configure services
    - Analyze logs
    - Manage processes
    
    Usage:
        sysadmin = SysAdminAgent()
        result = await sysadmin.process_task(AgentTask(
            description="Check disk usage and clean up temp files",
            context={}
        ))
    """
    
    # Dangerous commands that require confirmation
    DANGEROUS_PATTERNS = [
        "rm -rf /", "rm -rf /*", "> /dev/sda", "mkfs.",
        "dd if=", ":(){ :|:& };:", "chmod -R 777 /",
        "shutdown", "reboot", "halt", "poweroff"
    ]
    
    def __init__(self, allow_dangerous: bool = False, **kwargs):
        """
        Initialize the sysadmin agent.
        
        Args:
            allow_dangerous: Whether to allow dangerous commands
        """
        super().__init__(name="SysAdmin", **kwargs)
        self.allow_dangerous = allow_dangerous
        
        # Register tools
        self.register_tool("execute", self._execute_command)
        self.register_tool("get_system_info", self._get_system_info)
        self.register_tool("list_processes", self._list_processes)
        self.register_tool("read_logs", self._read_logs)
    
    async def process_task(self, task: AgentTask) -> Any:
        """
        Process a system administration task.
        
        Args:
            task: The task to process
            
        Returns:
            Task result
        """
        description = task.description.lower()
        
        # Route to appropriate handler
        if any(word in description for word in ["disk", "space", "storage", "cleanup"]):
            return await self.check_disk_space()
        
        elif any(word in description for word in ["process", "cpu", "memory", "performance"]):
            return await self.analyze_performance()
        
        elif any(word in description for word in ["log", "error", "debug"]):
            return await self.analyze_logs(task.context.get("log_path"), task.context.get("pattern"))
        
        elif any(word in description for word in ["service", "daemon", "systemctl"]):
            return await self.manage_service(task.context.get("service_name"), task.context.get("action"))
        
        elif any(word in description for word in ["file", "directory", "folder", "path"]):
            return await self.file_operations(task.description, task.context)
        
        else:
            # Default: execute command
            return await self.execute_command(task.description, context=task.context)
    
    async def execute_command(self, command: str, 
                             timeout: int = 30,
                             cwd: Optional[str] = None,
                             context: Optional[Dict[str, Any]] = None) -> CommandResult:
        """
        Execute a shell command safely.
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds
            cwd: Working directory (relative to workspace_root if not absolute)
            context: Additional context
            
        Returns:
            CommandResult
        """
        import time
        context = context or {}
        
        # Check for dangerous commands
        if not self.allow_dangerous:
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in command.lower():
                    return CommandResult(
                        command=command,
                        stdout="",
                        stderr=f"Dangerous command blocked: {pattern}",
                        returncode=-1,
                        success=False,
                        execution_time_ms=0
                    )
        
        start_time = time.time()
        
        # Determine effective working directory
        effective_cwd = self.workspace_root
        if cwd:
            if os.path.isabs(cwd):
                effective_cwd = Path(cwd)
            else:
                effective_cwd = self.workspace_root / cwd
        
        # Ensure it exists
        effective_cwd.mkdir(parents=True, exist_ok=True)
        
        # Security: Enforce workspace boundary
        try:
            effective_cwd.relative_to(self.workspace_root)
        except ValueError:
            return CommandResult(
                command=command,
                stdout="",
                stderr=f"Security violation: Execution attempted outside workspace boundary ({effective_cwd})",
                returncode=-1,
                success=False,
                execution_time_ms=0
            )

        # Try to use sandbox if requested or for dangerous commands
        use_sandbox = context.get("use_sandbox", False)
        if use_sandbox:
            from open_grace.sandbox.docker_sandbox import DockerSandbox, SandboxConfig
            sandbox = DockerSandbox()
            if sandbox.get_status()["docker_available"]:
                self.logger.info(f"Executing command in sandbox: {command}")
                sb_result = await sandbox.execute_shell(command, config=SandboxConfig(working_dir=str(effective_cwd)))
                return CommandResult(
                    command=command,
                    stdout=sb_result.stdout,
                    stderr=sb_result.stderr,
                    returncode=sb_result.exit_code,
                    success=sb_result.success,
                    execution_time_ms=sb_result.duration_ms
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(effective_cwd)
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return CommandResult(
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                success=result.returncode == 0,
                execution_time_ms=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                returncode=-1,
                success=False,
                execution_time_ms=timeout * 1000
            )
        except Exception as e:
            return CommandResult(
                command=command,
                stdout="",
                stderr=str(e),
                returncode=-1,
                success=False,
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        result = await self.execute_command("df -h")
        
        # Parse output
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        mounts = []
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                mounts.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percent": parts[4],
                    "mount": parts[5]
                })
        
        return {
            "success": result.success,
            "mounts": mounts,
            "raw_output": result.stdout
        }
    
    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze system performance."""
        # Get CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Get memory info
        memory = psutil.virtual_memory()
        
        # Get disk info
        disk = psutil.disk_usage('/')
        
        # Get top processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": (disk.used / disk.total) * 100
            },
            "top_processes": processes[:10]
        }
    
    async def analyze_logs(self, log_path: Optional[str] = None,
                          pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze system logs.
        
        Args:
            log_path: Path to log file (default: /var/log/syslog)
            pattern: Pattern to search for
            
        Returns:
            Analysis results
        """
        if log_path is None:
            # Try common log locations
            for path in ["/var/log/syslog", "/var/log/messages", "/var/log/system.log"]:
                if Path(path).exists():
                    log_path = path
                    break
        
        if not log_path or not Path(log_path).exists():
            return {"error": "No log file found"}
        
        # Read last 100 lines
        cmd = f"tail -n 100 '{log_path}'"
        if pattern:
            cmd += f" | grep -i '{pattern}'"
        
        result = await self.execute_command(cmd)
        
        # Analyze with LLM
        system_prompt = """You are a log analysis expert. Analyze the log entries and provide:
1. Summary of what's happening
2. Any errors or warnings
3. Recommendations if issues found

Be concise but informative."""
        
        analysis = await self.think(
            f"Analyze these log entries:\n\n{result.stdout[:2000]}",
            system=system_prompt
        )
        
        return {
            "log_path": log_path,
            "pattern": pattern,
            "recent_entries": result.stdout,
            "analysis": analysis
        }
    
    async def manage_service(self, service_name: Optional[str],
                            action: Optional[str]) -> CommandResult:
        """
        Manage a system service.
        
        Args:
            service_name: Name of the service
            action: Action to perform (start, stop, restart, status)
            
        Returns:
            CommandResult
        """
        if not service_name or not action:
            return CommandResult(
                command="",
                stdout="",
                stderr="Service name and action required",
                returncode=-1,
                success=False,
                execution_time_ms=0
            )
        
        # Determine the command based on init system
        if Path("/bin/systemctl").exists():
            cmd = f"systemctl {action} {service_name}"
        elif Path("/usr/sbin/service").exists():
            cmd = f"service {service_name} {action}"
        else:
            return CommandResult(
                command="",
                stdout="",
                stderr="Unknown init system",
                returncode=-1,
                success=False,
                execution_time_ms=0
            )
        
        return await self.execute_command(cmd)
    
    async def file_operations(self, description: str,
                             context: Dict[str, Any]) -> Any:
        """Handle file operations."""
        # This would use the file_tool from TaskForge
        # For now, return a placeholder
        return {"message": "File operations handled by file tool", "description": description}
    
    async def _execute_command(self, command: str, **kwargs) -> CommandResult:
        """Tool: Execute a command."""
        return await self.execute_command(command, **kwargs)
    
    async def _get_system_info(self) -> SystemInfo:
        """Tool: Get system information."""
        import platform
        
        boot_time = psutil.boot_time()
        uptime = __import__('time').time() - boot_time
        
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemInfo(
            hostname=platform.node(),
            platform=platform.platform(),
            cpu_count=psutil.cpu_count(),
            memory_total_gb=memory.total / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            disk_usage={
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": (disk.used / disk.total) * 100
            },
            uptime_seconds=uptime
        )
    
    async def _list_processes(self) -> List[Dict[str, Any]]:
        """Tool: List running processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        return processes
    
    async def _read_logs(self, path: str, lines: int = 50) -> str:
        """Tool: Read log file."""
        try:
            result = await self.execute_command(f"tail -n {lines} '{path}'")
            return result.stdout
        except:
            return ""