"""
Grace Orchestrator - Central coordinator for Open Grace platform.

The orchestrator manages:
- Agent lifecycle
- Task routing and execution
- Resource allocation
- System state
- Inter-agent communication
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from open_grace.model_router.router import ModelRouter, get_router, RoutingStrategy
from open_grace.security.vault import SecretVault, get_vault
from open_grace.memory.sqlite_store import SQLiteMemoryStore
from open_grace.observability.logger import GraceLogger


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Agent lifecycle status."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class Task:
    """A task to be executed."""
    id: str
    description: str
    status: TaskStatus
    agent_type: Optional[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    id: str
    name: str
    agent_type: str
    status: AgentStatus
    capabilities: List[str]
    created_at: datetime
    last_active: Optional[datetime] = None
    task_count: int = 0


class GraceOrchestrator:
    """
    Central orchestrator for the Open Grace platform.
    
    Manages agents, tasks, and coordinates execution across the system.
    
    Usage:
        orchestrator = GraceOrchestrator()
        await orchestrator.initialize()
        
        # Execute a task
        task_id = await orchestrator.submit_task("Organize my downloads")
        result = await orchestrator.get_task_result(task_id)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to orchestrator configuration
        """
        self.config_path = config_path or Path.home() / ".open_grace" / "config.yaml"
        self.instance_id = str(uuid.uuid4())[:8]
        
        # Core components
        self.router: Optional[ModelRouter] = None
        self.vault: Optional[SecretVault] = None
        self.memory: Optional[SQLiteMemoryStore] = None
        self.logger: Optional[GraceLogger] = None
        
        # Agent registry
        self._agents: Dict[str, AgentInfo] = {}
        self._agent_instances: Dict[str, Any] = {}
        
        # Task management
        self._tasks: Dict[str, Task] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        
        # State
        self._initialized = False
        self._shutdown = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    async def initialize(self):
        """Initialize all orchestrator components."""
        if self._initialized:
            return
        
        # Initialize logger first
        self.logger = GraceLogger()
        self.logger.info(f"Initializing Grace Orchestrator (instance: {self.instance_id})")
        
        # Initialize vault
        self.vault = get_vault()
        self.logger.info("Vault initialized")
        
        # Initialize model router
        self.router = get_router()
        self.logger.info("Model router initialized")
        
        # Initialize memory
        self.memory = SQLiteMemoryStore()
        self.logger.info("Memory store initialized")
        
        # Start task worker
        self._worker_task = asyncio.create_task(self._task_worker())
        
        self._initialized = True
        self.logger.info("Grace Orchestrator initialized successfully")
        
        # Emit event
        await self._emit_event("orchestrator.initialized", {"instance_id": self.instance_id})
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator."""
        self.logger.info("Shutting down Grace Orchestrator")
        self._shutdown = True
        
        # Cancel worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all agents
        for agent_id in list(self._agents.keys()):
            await self.unregister_agent(agent_id)
        
        self._initialized = False
        self.logger.info("Grace Orchestrator shutdown complete")
    
    async def register_agent(self, agent_type: str, name: str, 
                            capabilities: List[str],
                            agent_instance: Any) -> str:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_type: Type of agent (coder, sysadmin, research, etc.)
            name: Human-readable name
            capabilities: List of capabilities
            agent_instance: The agent instance
            
        Returns:
            Agent ID
        """
        agent_id = f"{agent_type}_{str(uuid.uuid4())[:8]}"
        
        agent_info = AgentInfo(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            status=AgentStatus.IDLE,
            capabilities=capabilities,
            created_at=datetime.now()
        )
        
        self._agents[agent_id] = agent_info
        self._agent_instances[agent_id] = agent_instance
        
        self.logger.info(f"Agent registered: {name} ({agent_id})")
        await self._emit_event("agent.registered", {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "name": name
        })
        
        return agent_id
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            True if unregistered, False if not found
        """
        if agent_id not in self._agents:
            return False
        
        agent_info = self._agents[agent_id]
        agent_info.status = AgentStatus.SHUTDOWN
        
        # Cleanup
        del self._agents[agent_id]
        if agent_id in self._agent_instances:
            del self._agent_instances[agent_id]
        
        self.logger.info(f"Agent unregistered: {agent_info.name} ({agent_id})")
        await self._emit_event("agent.unregistered", {"agent_id": agent_id})
        
        return True
    
    async def submit_task(self, description: str, 
                         agent_type: Optional[str] = None,
                         priority: int = 5,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a task for execution.
        
        Args:
            description: Task description
            agent_type: Preferred agent type (None for auto-selection)
            priority: Task priority (1-10, higher = more important)
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        task_id = f"task_{str(uuid.uuid4())[:8]}"
        
        task = Task(
            id=task_id,
            description=description,
            status=TaskStatus.PENDING,
            agent_type=agent_type,
            created_at=datetime.now(),
            metadata={
                "priority": priority,
                **(metadata or {})
            }
        )
        
        self._tasks[task_id] = task
        await self._task_queue.put((priority, task_id))
        
        self.logger.info(f"Task submitted: {description[:50]}... (ID: {task_id})")
        await self._emit_event("task.submitted", {
            "task_id": task_id,
            "description": description,
            "agent_type": agent_type
        })
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        task = self._tasks.get(task_id)
        return task.status if task else None
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Wait for and get the result of a task.
        
        Args:
            task_id: The task ID
            timeout: Maximum time to wait (None = forever)
            
        Returns:
            Task result or None if timeout
        """
        start_time = datetime.now()
        
        while True:
            task = self._tasks.get(task_id)
            if not task:
                return None
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            
            if task.status == TaskStatus.FAILED:
                raise Exception(task.error or "Task failed")
            
            if timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    return None
            
            await asyncio.sleep(0.1)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            
            self.logger.info(f"Task cancelled: {task_id}")
            await self._emit_event("task.cancelled", {"task_id": task_id})
            return True
        
        return False
    
    async def list_agents(self, agent_type: Optional[str] = None) -> List[AgentInfo]:
        """List registered agents."""
        agents = list(self._agents.values())
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        return agents
    
    async def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """List tasks."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "instance_id": self.instance_id,
            "initialized": self._initialized,
            "agents": {
                "total": len(self._agents),
                "by_status": {
                    status.value: sum(1 for a in self._agents.values() if a.status == status)
                    for status in AgentStatus
                }
            },
            "tasks": {
                "total": len(self._tasks),
                "by_status": {
                    status.value: sum(1 for t in self._tasks.values() if t.status == status)
                    for status in TaskStatus
                }
            },
            "queue_size": self._task_queue.qsize(),
            "providers": self.router.get_provider_status() if self.router else {}
        }
    
    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    async def _task_worker(self):
        """Background worker to process tasks."""
        while not self._shutdown:
            try:
                # Get next task
                priority, task_id = await asyncio.wait_for(
                    self._task_queue.get(), 
                    timeout=1.0
                )
                
                task = self._tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # Execute task
                await self._execute_task(task)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Task worker error: {e}")
    
    async def _execute_task(self, task: Task):
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        self.logger.info(f"Executing task: {task.id}")
        await self._emit_event("task.started", {"task_id": task.id})
        
        try:
            # Select agent
            agent_id = await self._select_agent(task.agent_type)
            
            if not agent_id:
                # Use model router directly if no agent available
                response = self.router.generate(
                    task.description,
                    strategy=RoutingStrategy.HYBRID
                )
                task.result = {
                    "content": response.content,
                    "provider": response.provider.value,
                    "model": response.model
                }
            else:
                # Execute via agent
                agent_instance = self._agent_instances.get(agent_id)
                if agent_instance:
                    result = await agent_instance.execute(task.description)
                    task.result = result
                    
                    # Update agent stats
                    agent_info = self._agents[agent_id]
                    agent_info.task_count += 1
                    agent_info.last_active = datetime.now()
            
            task.status = TaskStatus.COMPLETED
            self.logger.info(f"Task completed: {task.id}")
            await self._emit_event("task.completed", {
                "task_id": task.id,
                "result": task.result
            })
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.logger.error(f"Task failed: {task.id} - {e}")
            await self._emit_event("task.failed", {
                "task_id": task.id,
                "error": str(e)
            })
        
        finally:
            task.completed_at = datetime.now()
    
    async def _select_agent(self, agent_type: Optional[str]) -> Optional[str]:
        """Select the best agent for a task."""
        available_agents = [
            (aid, info) for aid, info in self._agents.items()
            if info.status == AgentStatus.IDLE
            and (not agent_type or info.agent_type == agent_type)
        ]
        
        if not available_agents:
            return None
        
        # Simple selection: pick the one with fewest tasks
        return min(available_agents, key=lambda x: x[1].task_count)[0]


# Global orchestrator instance
_orchestrator: Optional[GraceOrchestrator] = None


async def get_orchestrator() -> GraceOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = GraceOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


def set_orchestrator(orchestrator: GraceOrchestrator):
    """Set the global orchestrator instance."""
    global _orchestrator
    _orchestrator = orchestrator