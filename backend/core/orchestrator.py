import asyncio
import logging
from typing import Any, Optional
from pathlib import Path

from open_grace.agents.planner_agent import PlannerAgent
from open_grace.agents.coder_agent import CoderAgent
from open_grace.agents.research_agent import ResearchAgent
from open_grace.agents.sysadmin_agent import SysAdminAgent
from open_grace.agents.base_agent import AgentTask
from open_grace.core.resource_manager import ResourceManager
from open_grace.core.workspace_manager import get_workspace_manager

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Main orchestrator that coordinates agents to fulfill a goal.
    Follows a sequential pipeline: Planner -> Researcher -> Coder -> Sysadmin.
    """
    
    MAX_AGENT_STEPS = 5

    def __init__(self, workspace_root: str = "/home/opengrace/open_grace/workspace"):
        # Initialize managers
        self.rm = ResourceManager()
        self.wm = get_workspace_manager()

        # Initialize agents
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.researcher = ResearchAgent()
        self.sysadmin = SysAdminAgent()
        
    async def run(self, goal: str) -> str:
        """
        Executes the agent pipeline to achieve the given goal.
        """
        logger.info(f"Starting orchestration for goal: {goal}")
        
        # Determine working directory for this project via WorkspaceManager
        project_name = goal.lower().replace(" ", "_").strip()[:20]
        project_dir = self.wm.create_project_workspace(project_name)
        
        context = {"working_dir": str(project_dir), "goal": goal}
        
        # We loop with a max limit to prevent runaway execution
        for step in range(self.MAX_AGENT_STEPS):
            logger.info(f"Orchestration Step {step + 1}/{self.MAX_AGENT_STEPS}")

            # 1. Planner Phase
            logger.info("Phase 1: Planning")
            plan = await self.rm.run_agent(self.planner.create_plan, goal, context)
            logger.info(f"Plan created: {plan}")
            
            # 2. Researcher Phase
            logger.info("Phase 2: Researching")
            research_task = AgentTask(
                id="research_task",
                description=f"Research requirements and patterns for: {goal}",
                context=context
            )
            research_result = await self.rm.run_agent(self.researcher.process_task, research_task)
            context["research"] = research_result
            
            # 3. Coder Phase
            logger.info("Phase 3: Coding")
            coder_task = AgentTask(
                id="coder_task",
                description=f"Implement the project based on research: {research_result}",
                context=context
            )
            code_result = await self.rm.run_agent(self.coder.process_task, coder_task)
            context["code"] = code_result
            
            # 4. Sysadmin Phase
            logger.info("Phase 4: Sysadmin Execution")
            sysadmin_task = AgentTask(
                id="sysadmin_task",
                description=f"Deploy/Run the code generated. Context: {code_result}",
                context=context
            )
            sysadmin_result = await self.rm.run_agent(self.sysadmin.process_task, sysadmin_task)
            
            logger.info(f"Orchestration cycle complete for loop {step + 1}")
            
            # For this pipeline, we currently break after one full pass
            # but we have the loop structure for future iterative refinements.
            break

        logger.info(f"Orchestration complete for goal: {goal}")
        return "project created and executed"

# Example usage pattern when integrated with CLI/API
async def execute_goal(goal: str):
    orchestrator = AgentOrchestrator()
    return await orchestrator.run(goal)
