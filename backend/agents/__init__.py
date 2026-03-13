"""
Agents - Multi-agent system for Open Grace.

Specialized agents that collaborate to solve complex tasks:
- PlannerAgent: Breaks down complex tasks
- CoderAgent: Writes and debugs code
- SysAdminAgent: Manages systems and infrastructure
- ResearchAgent: Searches and analyzes information
"""

from open_grace.agents.base_agent import BaseAgent, AgentMessage
from open_grace.agents.planner_agent import PlannerAgent
from open_grace.agents.coder_agent import CoderAgent
from open_grace.agents.sysadmin_agent import SysAdminAgent
from open_grace.agents.research_agent import ResearchAgent
from open_grace.agents.agent_swarm import AgentSwarm

__all__ = [
    "BaseAgent",
    "AgentMessage",
    "PlannerAgent",
    "CoderAgent",
    "SysAdminAgent",
    "ResearchAgent",
    "AgentSwarm",
]