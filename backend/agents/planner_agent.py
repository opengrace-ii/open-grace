"""
Planner Agent - Breaks down complex tasks into executable steps.

The planner analyzes tasks and creates structured execution plans
that can be executed by other agents or the orchestrator.
"""

import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from backend.agents.base_agent import BaseAgent, AgentTask


class PlanStep(BaseModel):
    """A single step in an execution plan."""
    step_number: int = Field(description="Step sequence number")
    description: str = Field(description="Clear description of what to do")
    agent_type: str = Field(description="Which agent should execute this (e.g. coder, sysadmin, research)")
    estimated_minutes: int = Field(default=10, description="Estimated time in minutes")
    dependencies: List[int] = Field(default_factory=list, description="Step numbers this depends on")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the step")

    @property
    def estimated_time(self) -> int:
        return self.estimated_minutes * 60


class ExecutionPlan(BaseModel):
    """A complete execution plan."""
    reasoning: str = Field(description="Brief explanation of your approach")
    estimated_total_minutes: int = Field(default=30)
    steps: List[PlanStep] = Field(description="Sequence of execution steps")
    task_id: str = Field(default="")
    original_task: str = Field(default="")
    
    @property
    def estimated_total_time(self) -> int:
        return self.estimated_total_minutes * 60


class PlannerAgent(BaseAgent):
    """
    Agent that breaks down complex tasks into executable steps.
    
    The planner:
    1. Analyzes the task complexity
    2. Identifies required capabilities
    3. Creates a step-by-step plan
    4. Assigns steps to appropriate agents
    
    Usage:
        planner = PlannerAgent()
        plan = await planner.create_plan("Build a REST API with authentication")
        for step in plan.steps:
            print(f"{step.step_number}. {step.description} -> {step.agent_type}")
    """
    
    def __init__(self, **kwargs):
        """Initialize the planner agent."""
        super().__init__(name="Planner", **kwargs)
        
        # Agent capabilities mapping
        self._agent_capabilities = {
            "coder": [
                "write code", "debug", "refactor", "create files",
                "implement functions", "write tests", "review code"
            ],
            "sysadmin": [
                "system commands", "file operations", "install packages",
                "configure services", "monitor logs", "manage processes"
            ],
            "research": [
                "search", "analyze", "summarize", "find information",
                "research", "investigate", "explore"
            ]
        }
    
    async def process_task(self, task: AgentTask) -> ExecutionPlan:
        """
        Process a planning task.
        
        Args:
            task: The task to plan
            
        Returns:
            ExecutionPlan with steps
        """
        return await self.create_plan(task.description, task.context)
    
    async def create_plan(self, task_description: str, 
                         context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Create an execution plan for a task.
        
        Args:
            task_description: Description of the task
            context: Additional context
            
        Returns:
            ExecutionPlan
        """
        # Build planning prompt
        system_prompt = """You are a task planner AI. Your job is to break down complex tasks into clear, executable steps.

For each step, provide:
1. Step number
2. Clear description
3. Required agent type (coder, sysadmin, or research)
4. Estimated time in minutes
5. Dependencies on previous steps
6. Any parameters needed"""
        
        user_prompt = f"Task: {task_description}\n\n"
        if context:
            user_prompt += f"Context: {json.dumps(context, indent=2)}\n\n"
        user_prompt += "Create an execution plan."
        
        try:
            # Request parsed ExecutionPlan directly from the model router
            plan: ExecutionPlan = await self.think(user_prompt, system=system_prompt, response_model=ExecutionPlan)
            plan.task_id = f"plan_{id(task_description) % 10000}"
            plan.original_task = task_description
            return plan
            
        except Exception as e:
            self.logger.warning(f"Failed to generate structured plan: {e}. Falling back to default plan.")
            return await self._create_fallback_plan(task_description, error=str(e))
    
    async def _create_fallback_plan(self, task_description: str, error: Optional[str] = None) -> ExecutionPlan:
        """Create a simple fallback plan when LLM fails."""
        task_lower = task_description.lower()
        
        steps = []
        
        # Simple keyword-based planning
        if any(word in task_lower for word in ["code", "program", "function", "class", "script"]):
            steps.append(PlanStep(
                step_number=1,
                description="Analyze requirements and design solution",
                agent_type="research",
                estimated_minutes=5,
                dependencies=[],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Write the code implementation",
                agent_type="coder",
                estimated_minutes=10,
                dependencies=[1],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=3,
                description="Test and verify the implementation",
                agent_type="coder",
                estimated_minutes=5,
                dependencies=[2],
                parameters={}
            ))
        
        elif any(word in task_lower for word in ["system", "server", "config", "install"]):
            steps.append(PlanStep(
                step_number=1,
                description="Analyze system requirements",
                agent_type="research",
                estimated_minutes=5,
                dependencies=[],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Execute system configuration",
                agent_type="sysadmin",
                estimated_minutes=10,
                dependencies=[1],
                parameters={}
            ))
        
        else:
            steps.append(PlanStep(
                step_number=1,
                description="Research and analyze the task",
                agent_type="research",
                estimated_minutes=5,
                dependencies=[],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Execute the main task",
                agent_type="coder",
                estimated_minutes=10,
                dependencies=[1],
                parameters={}
            ))
        
        total_time = sum(s.estimated_minutes for s in steps)
        
        if error:
            self.logger.info(f"Fallback planning due to error: {error}")
        self.logger.warning("Using fallback plan based on system keywords")

        return ExecutionPlan(
            task_id=f"plan_fallback",
            original_task=task_description,
            steps=steps,
            estimated_total_minutes=total_time,
            reasoning="Fallback plan based on task keywords"
        )
    
    def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Optimize an execution plan by:
        - Parallelizing independent steps
        - Reordering for efficiency
        - Merging similar steps
        
        Args:
            plan: The plan to optimize
            
        Returns:
            Optimized ExecutionPlan
        """
        # Group steps by agent type for potential parallelization
        agent_steps: Dict[str, List[PlanStep]] = {}
        for step in plan.steps:
            if step.agent_type not in agent_steps:
                agent_steps[step.agent_type] = []
            agent_steps[step.agent_type].append(step)
        
        # TODO: Implement optimization logic
        # For now, return original plan
        return plan
    
    async def estimate_complexity(self, task_description: str) -> Dict[str, Any]:
        """
        Estimate task complexity.
        
        Returns:
            Dict with complexity metrics
        """
        system_prompt = """Analyze the complexity of this task. Respond with JSON:
{
  "complexity": "low|medium|high",
  "reasoning": "Why this complexity level",
  "required_agents": ["list", "of", "agents"],
  "risk_factors": ["potential", "issues"]
}"""
        
        response = await self.think(
            f"Task: {task_description}\n\nAnalyze complexity:",
            system=system_prompt
        )
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            return json.loads(response[json_start:json_end])
        except:
            return {
                "complexity": "medium",
                "reasoning": "Default estimation",
                "required_agents": ["coder"],
                "risk_factors": []
            }