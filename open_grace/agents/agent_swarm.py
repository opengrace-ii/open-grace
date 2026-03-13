"""
Agent Swarm - Coordinates multiple agents working together.

Manages agent collaboration, task distribution, and result aggregation.
"""

import asyncio
import re
import uuid
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from open_grace.agents.base_agent import BaseAgent, AgentTask, AgentMessage
from open_grace.agents.planner_agent import PlannerAgent, ExecutionPlan


@dataclass
class SwarmTask:
    """A task for the swarm."""
    id: str
    description: str
    plan: Optional[ExecutionPlan]
    results: Dict[str, Any]
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    completed_at: Optional[str] = None


class AgentSwarm:
    """
    Coordinates multiple agents working together on complex tasks.
    
    The swarm:
    1. Uses PlannerAgent to break down tasks
    2. Distributes steps to appropriate agents
    3. Manages dependencies between steps
    4. Aggregates results
    
    Usage:
        swarm = AgentSwarm()
        await swarm.initialize()
        
        # Add agents
        swarm.add_agent(CoderAgent())
        swarm.add_agent(SysAdminAgent())
        
        # Execute complex task
        result = await swarm.execute("Build a web API with auth")
    """
    
    def __init__(self):
        """Initialize the agent swarm."""
        self.agents: Dict[str, BaseAgent] = {}
        self.planner = PlannerAgent()
        self._tasks: Dict[str, SwarmTask] = {}
        self._running = False
    
    async def initialize(self):
        """Initialize the swarm and start all agents."""
        self._running = True
        
        # Start planner
        await self.planner.start()
        
        # Start all agents
        for agent in self.agents.values():
            await agent.start()
    
    async def shutdown(self):
        """Shutdown the swarm and all agents."""
        self._running = False
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
        
        # Stop planner
        await self.planner.stop()
    
    def add_agent(self, agent: BaseAgent) -> str:
        """
        Add an agent to the swarm.
        
        Args:
            agent: The agent to add
            
        Returns:
            Agent ID
        """
        self.agents[agent.agent_id] = agent
        return agent.agent_id
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the swarm."""
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            asyncio.create_task(agent.stop())
            return True
        return False
    
    def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Get all agents of a specific type."""
        return [
            agent for agent in self.agents.values()
            if agent.agent_type == agent_type
        ]
    
    async def execute(self, task_description: str,
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a complex task using the swarm.
        
        Args:
            task_description: Description of the task
            context: Additional context
            
        Returns:
            Execution results
        """
        context = context or {}
        
        # Create project workspace if not provided
        if "working_dir" not in context:
            # Create a safe project name from the task description
            project_name = re.sub(r'[^a-zA-Z0-9]', '_', task_description[:30]).strip('_').lower()
            if not project_name:
                project_name = f"project_{uuid.uuid4().hex[:8]}"
            
            project_dir = Path("/home/opengrace/open_grace/workspace/projects") / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            context["working_dir"] = str(project_dir)

        # Create swarm task
        task_id = f"swarm_{uuid.uuid4().hex[:8]}"
        swarm_task = SwarmTask(
            id=task_id,
            description=task_description,
            plan=None,
            results={},
            status="running",
            created_at=datetime.now().isoformat()
        )
        self._tasks[task_id] = swarm_task
        
        try:
            # Step 1: Plan the task
            plan = await self.planner.create_plan(task_description, context)
            swarm_task.plan = plan
            
            # Step 2: Execute steps
            step_results = await self._execute_plan(plan, context)
            swarm_task.results = {str(k): v for k, v in step_results.items()}
            
            # Step 3: Aggregate results
            final_result = await self._aggregate_results(plan, step_results)
            
            swarm_task.status = "completed"
            swarm_task.completed_at = datetime.now().isoformat()
            
            return {
                "task_id": task_id,
                "success": True,
                "plan": {
                    "steps": len(plan.steps),
                    "estimated_time": plan.estimated_total_time,
                    "reasoning": plan.reasoning
                },
                "results": final_result,
                "step_results": step_results
            }
            
        except Exception as e:
            swarm_task.status = "failed"
            swarm_task.completed_at = datetime.now().isoformat()
            
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    async def _execute_plan(self, plan: ExecutionPlan, context: Optional[Dict[str, Any]] = None) -> Dict[int, Any]:
        """Execute all steps in a plan."""
        results = {}
        completed_steps = set()
        context = context or {}
        
        # Sort steps by dependencies
        sorted_steps = self._topological_sort(plan.steps)
        
        for step in sorted_steps:
            # Check dependencies
            if not all(dep in completed_steps for dep in step.dependencies):
                # Wait for dependencies
                while not all(dep in completed_steps for dep in step.dependencies):
                    await asyncio.sleep(0.1)
            
            # Find appropriate agent
            agent = self._find_agent_for_step(step)
            
            if not agent:
                results[step.step_number] = {
                    "success": False,
                    "error": f"No agent available for type: {step.agent_type}"
                }
                continue
            
            # Execute step
            step_context = context.copy()
            step_context.update(step.parameters)
            
            task = AgentTask(
                id=f"step_{step.step_number}",
                description=step.description,
                context=step_context,
                priority=5
            )
            
            try:
                result = await agent.process_task(task)
                results[step.step_number] = {
                    "success": True,
                    "result": result,
                    "agent": agent.agent_id
                }
                completed_steps.add(step.step_number)
                
            except Exception as e:
                results[step.step_number] = {
                    "success": False,
                    "error": str(e),
                    "agent": agent.agent_id
                }
        
        return results
    
    def _topological_sort(self, steps: List[Any]) -> List[Any]:
        """Sort steps by dependencies."""
        # Simple topological sort
        step_map = {s.step_number: s for s in steps}
        sorted_steps = []
        visited = set()
        
        def visit(step):
            if step.step_number in visited:
                return
            visited.add(step.step_number)
            for dep in step.dependencies:
                if dep in step_map:
                    visit(step_map[dep])
            sorted_steps.append(step)
        
        for step in steps:
            visit(step)
        
        return sorted_steps
    
    def _find_agent_for_step(self, step: Any) -> Optional[BaseAgent]:
        """Find the best agent for a step."""
        # Get agents of the required type
        agents = self.get_agents_by_type(step.agent_type)
        
        if not agents:
            return None
        
        # Pick the first available (idle) agent
        for agent in agents:
            if agent.state.value == "idle":
                return agent
        
        # If none idle, return first agent
        return agents[0]
    
    async def _aggregate_results(self, plan: ExecutionPlan,
                                step_results: Dict[int, Any]) -> Any:
        """Aggregate step results into final output."""
        # Collect successful results
        successful = [
            result["result"] for result in step_results.values()
            if result.get("success")
        ]
        
        # If only one result, return it directly
        if len(successful) == 1:
            return successful[0]
        
        # Otherwise, create a summary
        summary_prompt = f"""Summarize the following task execution results:

Original Task: {plan.original_task}

Steps Completed: {len(successful)} / {len(plan.steps)}

Results:
{chr(10).join(f"- {str(r)[:200]}" for r in successful)}

Provide a concise summary of what was accomplished."""
        
        summary = await self.planner.think(summary_prompt)
        return {
            "summary": summary,
            "steps_completed": len(successful),
            "total_steps": len(plan.steps),
            "details": successful
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status."""
        return {
            "agents": {
                "total": len(self.agents),
                "by_type": {}
            },
            "tasks": {
                "total": len(self._tasks),
                "completed": sum(1 for t in self._tasks.values() if t.status == "completed"),
                "failed": sum(1 for t in self._tasks.values() if t.status == "failed"),
                "running": sum(1 for t in self._tasks.values() if t.status == "running")
            }
        }
    
    async def broadcast(self, message: str, message_type: str = "broadcast"):
        """Broadcast a message to all agents."""
        for agent in self.agents.values():
            await agent.receive_message(AgentMessage(
                id=f"broadcast_{id(message)}",
                from_agent="swarm",
                to_agent=agent.agent_id,
                message_type=message_type,
                content=message
            ))