"""
Main Agent for TaskForge.
Orchestrates planning, execution, and memory.
"""

import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from tools.base_tool import BaseTool
from tools.shell_tool import ShellTool
from tools.file_tool import FileTool
from tools.git_tool import GitTool
from tools.sql_tool import SQLTool
from agent.planner import Planner, TaskPlan
from agent.executor import Executor, ExecutionResult
from memory.memory import MemoryStore, TaskMemory, MemoryEntry, get_memory_store
from security.permissions import PermissionManager, get_permission_manager


@dataclass
class AgentResponse:
    """Response from the agent."""
    task: str
    success: bool
    plan: TaskPlan
    results: List[ExecutionResult]
    message: str
    execution_time_ms: int = 0


class TaskForgeAgent:
    """
    Main TaskForge AI Agent.
    
    The agent:
    1. Receives user tasks
    2. Plans execution using LLM
    3. Executes with security checks
    4. Stores results in memory
    5. Returns formatted response
    """
    
    def __init__(self, 
                 model: str = "llama3",
                 ollama_url: str = "http://localhost:11434",
                 memory_store: Optional[MemoryStore] = None,
                 permission_manager: Optional[PermissionManager] = None):
        """
        Initialize the TaskForge agent.
        
        Args:
            model: Ollama model to use
            ollama_url: Ollama API URL
            memory_store: Memory store instance
            permission_manager: Permission manager instance
        """
        self.session_id = str(uuid.uuid4())[:8]
        self.planner = Planner(model=model, base_url=ollama_url)
        self.executor = Executor(permission_manager=permission_manager)
        self.memory = memory_store or get_memory_store()
        self.permissions = permission_manager or get_permission_manager()
        
        # Register default tools
        self._register_default_tools()
        
        # Initialize session
        self.memory.create_session(self.session_id, {
            "model": model,
            "started_at": datetime.now().isoformat()
        })
    
    def _register_default_tools(self):
        """Register the default set of tools."""
        from tools.email_tool import EmailTool
        
        self.executor.register_tools([
            ShellTool(),
            FileTool(),
            GitTool(),
            SQLTool(),
            EmailTool(),
        ])
    
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute a task.
        
        Args:
            task: The task description
            context: Optional context information
            
        Returns:
            AgentResponse with results
        """
        import time
        start_time = time.time()
        
        # Log the task
        self.memory.save_entry(MemoryEntry(
            session_id=self.session_id,
            entry_type="task",
            content=task
        ))
        
        # Plan the task
        try:
            plan = self.planner.plan(task, context)
        except Exception as e:
            return AgentResponse(
                task=task,
                success=False,
                plan=TaskPlan(task=task, steps=[], reasoning=f"Planning failed: {e}"),
                results=[],
                message=f"Failed to plan task: {e}",
                execution_time_ms=0
            )
        
        # Execute the plan
        results = self.executor.execute_plan(plan)
        
        # Determine success
        success = all(r.success for r in results) and len(results) > 0
        
        # Build response message
        if success:
            message = self._build_success_message(results)
        else:
            message = self._build_failure_message(results)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Save to memory
        task_memory = TaskMemory(
            task=task,
            plan=[step.description for step in plan.steps],
            results=[
                {
                    "step": r.step_number,
                    "tool": r.tool,
                    "success": r.success,
                    "result": r.result
                }
                for r in results
            ],
            success=success
        )
        self.memory.save_task(task_memory, self.session_id)
        
        # Update session
        self.memory.update_session(self.session_id)
        
        return AgentResponse(
            task=task,
            success=success,
            plan=plan,
            results=results,
            message=message,
            execution_time_ms=execution_time
        )
    
    def chat(self, message: str) -> str:
        """
        Have a conversation with the agent.
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        # Log conversation
        self.memory.save_entry(MemoryEntry(
            session_id=self.session_id,
            entry_type="conversation",
            content=f"User: {message}"
        ))
        
        # Get response from LLM
        response = self.planner.chat(message)
        
        # Log response
        self.memory.save_entry(MemoryEntry(
            session_id=self.session_id,
            entry_type="conversation",
            content=f"Agent: {response}"
        ))
        
        return response
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history."""
        return self.memory.get_tasks(self.session_id, limit)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "session_id": self.session_id,
            "memory_stats": self.memory.get_stats(),
            "execution_summary": self.executor.get_execution_summary(),
            "available_tools": self.executor.get_available_tools()
        }
    
    def set_model(self, model: str):
        """Change the LLM model."""
        self.planner.set_model(model)
    
    def is_ready(self) -> bool:
        """Check if the agent is ready to accept tasks."""
        return self.planner.is_available()
    
    def _build_success_message(self, results: List[ExecutionResult]) -> str:
        """Build a success message from results."""
        messages = []
        
        for result in results:
            if result.success:
                if result.result:
                    if isinstance(result.result, dict):
                        if "stdout" in result.result:
                            messages.append(result.result["stdout"].strip())
                        elif "content" in result.result:
                            messages.append(result.result["content"][:500])
                        else:
                            messages.append(str(result.result)[:200])
                    else:
                        messages.append(str(result.result)[:200])
        
        return "\n".join(messages) if messages else "Task completed successfully."
    
    def _build_failure_message(self, results: List[ExecutionResult]) -> str:
        """Build a failure message from results."""
        errors = []
        
        for result in results:
            if not result.success:
                if result.error:
                    errors.append(f"Step {result.step_number}: {result.error[:200]}")
        
        if errors:
            return "Task failed with errors:\n" + "\n".join(errors)
        return "Task failed."


# Global agent instance
_agent: Optional[TaskForgeAgent] = None


def get_agent(model: str = "llama3", 
              ollama_url: str = "http://localhost:11434") -> TaskForgeAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        _agent = TaskForgeAgent(model=model, ollama_url=ollama_url)
    return _agent


def set_agent(agent: TaskForgeAgent):
    """Set the global agent instance."""
    global _agent
    _agent = agent
