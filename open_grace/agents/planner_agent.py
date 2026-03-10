"""
Planner Agent - Breaks down complex tasks into executable steps.

The planner analyzes tasks and creates structured execution plans
that can be executed by other agents or the orchestrator.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from open_grace.agents.base_agent import BaseAgent, AgentTask


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    step_number: int
    description: str
    agent_type: str  # Which agent should execute this
    estimated_time: int  # Estimated time in seconds
    dependencies: List[int]  # Step numbers this depends on
    parameters: Dict[str, Any]  # Parameters for the step


@dataclass
class ExecutionPlan:
    """A complete execution plan."""
    task_id: str
    original_task: str
    steps: List[PlanStep]
    estimated_total_time: int
    reasoning: str


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
6. Any parameters needed

Respond in JSON format:
{
  "reasoning": "Brief explanation of your approach",
  "estimated_total_minutes": 30,
  "steps": [
    {
      "step_number": 1,
      "description": "What to do",
      "agent_type": "coder",
      "estimated_minutes": 10,
      "dependencies": [],
      "parameters": {}
    }
  ]
}"""
        
        user_prompt = f"Task: {task_description}\n\n"
        if context:
            user_prompt += f"Context: {json.dumps(context, indent=2)}\n\n"
        user_prompt += "Create an execution plan:"
        
        # Get plan from LLM
        response = await self.think(user_prompt, system=system_prompt)
        
        # Parse the plan
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                plan_data = json.loads(response[json_start:json_end])
            else:
                plan_data = json.loads(response)
            
            # Build ExecutionPlan
            steps = []
            for step_data in plan_data.get("steps", []):
                steps.append(PlanStep(
                    step_number=step_data["step_number"],
                    description=step_data["description"],
                    agent_type=step_data["agent_type"],
                    estimated_time=step_data["estimated_minutes"] * 60,
                    dependencies=step_data.get("dependencies", []),
                    parameters=step_data.get("parameters", {})
                ))
            
            return ExecutionPlan(
                task_id=f"plan_{id(task_description) % 10000}",
                original_task=task_description,
                steps=steps,
                estimated_total_time=plan_data.get("estimated_total_minutes", 0) * 60,
                reasoning=plan_data.get("reasoning", "")
            )
            
        except json.JSONDecodeError:
            # Fallback: create simple plan
            return self._create_fallback_plan(task_description)
    
    def _create_fallback_plan(self, task_description: str) -> ExecutionPlan:
        """Create a simple fallback plan when LLM fails."""
        task_lower = task_description.lower()
        
        steps = []
        
        # Simple keyword-based planning
        if any(word in task_lower for word in ["code", "program", "function", "class", "script"]):
            steps.append(PlanStep(
                step_number=1,
                description="Analyze requirements and design solution",
                agent_type="research",
                estimated_time=300,
                dependencies=[],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Write the code implementation",
                agent_type="coder",
                estimated_time=600,
                dependencies=[1],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=3,
                description="Test and verify the implementation",
                agent_type="coder",
                estimated_time=300,
                dependencies=[2],
                parameters={}
            ))
        
        elif any(word in task_lower for word in ["system", "server", "config", "install"]):
            steps.append(PlanStep(
                step_number=1,
                description="Analyze system requirements",
                agent_type="research",
                estimated_time=300,
                dependencies=[],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Execute system configuration",
                agent_type="sysadmin",
                estimated_time=600,
                dependencies=[1],
                parameters={}
            ))
        
        else:
            steps.append(PlanStep(
                step_number=1,
                description="Research and analyze the task",
                agent_type="research",
                estimated_time=300,
                dependencies=[],
                parameters={}
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Execute the main task",
                agent_type="coder",
                estimated_time=600,
                dependencies=[1],
                parameters={}
            ))
        
        total_time = sum(s.estimated_time for s in steps)
        
        return ExecutionPlan(
            task_id=f"plan_fallback",
            original_task=task_description,
            steps=steps,
            estimated_total_time=total_time,
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