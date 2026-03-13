"""
Agents - Multi-agent system for Open Grace.

Specialized agents that collaborate to solve complex tasks:
- PlannerAgent: Breaks down complex tasks
- CoderAgent: Writes and debugs code
- SysAdminAgent: Manages systems and infrastructure
- ResearchAgent: Searches and analyzes information
"""

from backend.agents.base_agent import BaseAgent, AgentMessage
from backend.agents.planner_agent import PlannerAgent
from backend.agents.coder_agent import CoderAgent
from backend.agents.sysadmin_agent import SysAdminAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.agent_swarm import AgentSwarm

__all__ = [
    "BaseAgent",
    "AgentMessage",
    "PlannerAgent",
    "CoderAgent",
    "SysAdminAgent",
    "ResearchAgent",
    "AgentSwarm",
]