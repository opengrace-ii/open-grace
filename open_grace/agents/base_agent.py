"""
Base Agent - Foundation for all agents in Open Grace.

Provides common functionality for:
- Message passing
- State management
- Tool execution
- Memory access
"""

import uuid
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from open_grace.model_router.router import ModelRouter, get_router
from open_grace.memory.vector_store import VectorStore, get_vector_store
from open_grace.security.vault import get_vault
from open_grace.observability.logger import get_logger


class AgentState(Enum):
    """Agent lifecycle states."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Message passed between agents."""
    id: str
    from_agent: str
    to_agent: str
    message_type: str  # "task", "response", "query", "broadcast"
    content: Any
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AgentTask:
    """Task assigned to an agent."""
    id: str
    description: str
    context: Dict[str, Any]
    priority: int = 5
    created_at: str = ""
    deadline: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class BaseAgent(ABC):
    """
    Base class for all Open Grace agents.
    
    Agents are specialized AI workers that:
    - Receive tasks through messages
    - Use tools to accomplish objectives
    - Maintain their own state and memory
    - Communicate with other agents
    
    Usage:
        class MyAgent(BaseAgent):
            async def process_task(self, task: AgentTask) -> Any:
                # Implementation
                return result
    """
    
    def __init__(self,
                 agent_id: Optional[str] = None,
                 name: Optional[str] = None,
                 model_router: Optional[ModelRouter] = None,
                 vector_store: Optional[VectorStore] = None):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique agent ID (generated if not provided)
            name: Human-readable name
            model_router: Model router for LLM access
            vector_store: Vector store for memory
        """
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.name = name or self.__class__.__name__
        self.state = AgentState.IDLE
        
        # Core components
        self.model_router = model_router or get_router()
        self.vector_store = vector_store or get_vector_store()
        self.vault = get_vault()
        self.logger = get_logger()
        
        # Message handling
        self._inbox: asyncio.Queue = asyncio.Queue()
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._subscribed_agents: List[str] = []
        
        # State
        self._memory: Dict[str, Any] = {}
        self._task_history: List[Dict[str, Any]] = []
        self._current_task: Optional[AgentTask] = None
        
        # Tools
        self._tools: Dict[str, Callable] = {}
        
        # Background task
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    @property
    def agent_type(self) -> str:
        """Return the agent type identifier."""
        return self.__class__.__name__.lower().replace("agent", "")
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Any:
        """
        Process a task. Must be implemented by subclasses.
        
        Args:
            task: The task to process
            
        Returns:
            Task result
        """
        pass
    
    async def start(self):
        """Start the agent's message processing loop."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._message_loop())
        self.logger.info(f"Agent {self.name} ({self.agent_id}) started")
    
    async def stop(self):
        """Stop the agent."""
        self._running = False
        worker_task = getattr(self, "_worker_task", None)
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except (asyncio.CancelledError, Exception):
                pass
        
        self.logger.info(f"Agent {self.name} ({self.agent_id}) stopped")
    
    async def send_message(self, to_agent: str, content: Any, 
                          message_type: str = "task",
                          metadata: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """
        Send a message to another agent.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            message_type: Type of message
            metadata: Additional metadata
            
        Returns:
            The sent message
        """
        message = AgentMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
        
        # In a real system, this would route to the target agent
        # For now, we just log it
        self.logger.info(f"Agent {self.name} sent {message_type} to {to_agent}")
        
        return message
    
    async def broadcast(self, content: Any, 
                       message_type: str = "broadcast",
                       metadata: Optional[Dict[str, Any]] = None):
        """
        Broadcast a message to all subscribed agents.
        
        Args:
            content: Message content
            message_type: Type of message
            metadata: Additional metadata
        """
        for agent_id in self._subscribed_agents:
            await self.send_message(agent_id, content, message_type, metadata)
    
    async def receive_message(self, message: AgentMessage):
        """Receive a message into the inbox."""
        await self._inbox.put(message)
    
    def subscribe_to(self, agent_id: str):
        """Subscribe to another agent's broadcasts."""
        if agent_id not in self._subscribed_agents:
            self._subscribed_agents.append(agent_id)
    
    def unsubscribe_from(self, agent_id: str):
        """Unsubscribe from another agent's broadcasts."""
        if agent_id in self._subscribed_agents:
            self._subscribed_agents.remove(agent_id)
    
    def register_tool(self, name: str, tool_func: Callable):
        """Register a tool for the agent to use."""
        self._tools[name] = tool_func
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Use a registered tool."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self._tools[tool_name]
        
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        else:
            return tool(**kwargs)
    
    def remember(self, key: str, value: Any):
        """Store something in agent memory."""
        self._memory[key] = {
            "value": value,
            "stored_at": datetime.now().isoformat()
        }
    
    def recall(self, key: str) -> Optional[Any]:
        """Recall something from agent memory."""
        entry = self._memory.get(key)
        return entry["value"] if entry else None
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type,
            "state": self.state.value,
            "memory_keys": list(self._memory.keys()),
            "task_count": len(self._task_history),
            "current_task": self._current_task.id if self._current_task else None
        }
    
    async def execute(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Convenience method to execute a task from a description.
        
        Args:
            task_description: The task description
            context: Additional context
            
        Returns:
            Execution result
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            id=task_id,
            description=task_description,
            context=context or {},
            priority=5
        )
        return await self.process_task(task)

    async def think(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Use the LLM to think about something.
        
        Args:
            prompt: The prompt to think about
            system: Optional system message
            
        Returns:
            LLM response
        """
        self.state = AgentState.THINKING
        
        try:
            response = await self.model_router.generate(prompt, system=system)
            if response and hasattr(response, "content"):
                return str(response.content)
            return ""
        finally:
            self.state = AgentState.IDLE
    
    async def search_memory(self, query: str, top_k: int = 5) -> List[Any]:
        """Search the vector store for relevant information."""
        results = self.vector_store.search(query, top_k=top_k)
        return results
    
    async def _message_loop(self):
        """Main message processing loop."""
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self._inbox.get(),
                    timeout=1.0
                )
                
                # Process message
                await self._handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Agent {self.name} message error: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        """Handle an incoming message."""
        self.logger.info(f"Agent {self.name} received {message.message_type} from {message.from_agent}")
        
        if message.message_type == "task":
            # Create task from message
            task = AgentTask(
                id=f"task_{uuid.uuid4().hex[:8]}",
                description=str(message.content),
                context=message.metadata.get("context", {}),
                priority=message.metadata.get("priority", 5)
            )
            
            # Execute task
            self._current_task = task
            self.state = AgentState.EXECUTING
            
            try:
                result = await self.process_task(task)
                
                # Send response
                await self.send_message(
                    message.from_agent,
                    result,
                    message_type="response",
                    metadata={"task_id": task.id, "success": True}
                )
                
                # Record in history
                self._task_history.append({
                    "task_id": task.id,
                    "description": task.description,
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Agent {self.name} task error: {e}")
                
                # Send error response
                await self.send_message(
                    message.from_agent,
                    str(e),
                    message_type="response",
                    metadata={"task_id": task.id, "success": False, "error": str(e)}
                )
            
            finally:
                self._current_task = None
                self.state = AgentState.IDLE
        
        # Call registered handlers
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self.logger.error(f"Message handler error: {e}")
    
    def on_message(self, message_type: str, handler: Callable):
        """Register a handler for a message type."""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)