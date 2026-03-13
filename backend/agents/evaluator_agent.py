"""
Evaluator Agent - Analyzes task results and provides quality feedback.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from backend.agents.base_agent import BaseAgent, AgentTask

class EvaluationReport(BaseModel):
    """Structured report for task evaluation."""
    quality_score: float = Field(description="Score from 0.0 to 10.0 representing the quality of the result.")
    alignment_score: float = Field(description="How well the result aligns with the original goal (0-10).")
    critique: str = Field(description="Detailed qualitative feedback on the result.")
    efficiency_analysis: str = Field(description="Analysis of how efficient the solution was.")
    lessons_learned: List[str] = Field(description="Key takeaways or patterns to reuse/avoid.")
    improvement_strategies: List[str] = Field(description="Specific strategies for future similar tasks.")

class EvaluatorAgent(BaseAgent):
    """
    Agent responsible for evaluating the performance of the swarm.
    
    It compares goals with outcomes to derive quality metrics and 
    actionable improvement strategies.
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="Evaluator", **kwargs)

    async def process_task(self, task: AgentTask) -> EvaluationReport:
        """
        Evaluate a completed task.
        
        Args:
            task.description: Usually the original goal.
            task.context['result']: The actual result to evaluate.
            task.context['plan']: The plan that was followed.
        """
        goal = task.description
        result = task.context.get('result', '')
        plan = task.context.get('plan', '')
        
        system_prompt = """You are a Senior System Auditor and AI Strategist.
Your goal is to evaluate task outcomes with extreme precision.
You must be critical but constructive.
Look for:
1. Completeness: Did the result meet all requirements?
2. Correctness: Are there bugs or logical errors?
3. Efficiency: Could it have been done better?
4. Pattern recognition: What generalizable strategy can we learn from this?
"""

        user_prompt = f"""### Original Goal:
{goal}

### Execution Plan:
{plan}

### Actual Result:
{result}

Please evaluate this task outcome and provide a structured report.
"""

        try:
            report: EvaluationReport = await self.think(
                user_prompt, 
                system=system_prompt, 
                response_model=EvaluationReport
            )
            return report
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            # Fallback report
            return EvaluationReport(
                quality_score=5.0,
                alignment_score=5.0,
                critique=f"Evaluation could not be performed automatically due to error: {e}",
                efficiency_analysis="N/A",
                lessons_learned=["Monitor system health during evaluation"],
                improvement_strategies=["Check model router connectivity"]
            )
