"""
Long-Term Memory Coordinator - Manages the transition of episodic findings 
to permanent knowledge.
"""

import asyncio
from typing import Dict, List, Optional, Any
from open_grace.memory.knowledge_store import get_knowledge_store
from open_grace.memory.short_term_memory import ShortTermMemory
from open_grace.model_router.router import get_router

class LongTermMemory:
    """
    Coordinator for System 1: Long-Term Knowledge Memory.
    
    This system:
    1. Collects events from short-term memory
    2. Uses an LLM to distill key insights and patterns
    3. Stores them in the KnowledgeStore
    """
    
    def __init__(self, short_term: Optional[ShortTermMemory] = None):
        self.kb = get_knowledge_store()
        self.router = get_router()
        self.short_term = short_term

    async def distill_and_store(self, session_id: str, task_description: str, 
                               evaluation: Optional[Any] = None):
        """
        Process short-term memory after a task to extract long-term value.
        Incorporates evaluation feedback if available.
        """
        if evaluation:
            from open_grace.agents.evaluator_agent import EvaluationReport
            # Ensure it's the right type for later usage
            evaluation: EvaluationReport = evaluation
            
        if not self.short_term:
            return

        events = self.short_term._history
        if not events:
            return

        # Prepare distillation prompt
        events_str = "\n".join([f"- {e['type']}: {e['content']}" for e in events])
        
        eval_data = ""
        if evaluation:
            eval_data = f"""
            ### Quality Score: {evaluation.quality_score}/10
            ### Critique: {evaluation.critique}
            ### Lessons Learned: {", ".join(evaluation.lessons_learned)}
            ### Improvement Strategies: {", ".join(evaluation.improvement_strategies)}
            """

        prompt = f"""
        Task: {task_description}
        Recent Actions and Findings:
        {events_str}
        
        {eval_data}
        
        Analyze the actions and findings from this task, including the evaluation feedback.
        Distill them into 1-3 critical pieces of long-term knowledge.
        
        If the quality was low, focus on 'Mistakes to Avoid' and 'Correction Strategies'.
        If the quality was high, focus on 'Successful Patterns' and 'Best Practices'.
        
        For each piece of knowledge, provide:
        - Key: A short unique name
        - Content: The detailed finding, pattern, or lesson learned
        - Category: One of [coding, research, system, general]
        
        Format as JSON list:
        [{{"key": "...", "content": "...", "category": "..."}}]
        """

        try:
            response = await self.router.generate(prompt, system="You are a knowledge architect. Your goal is to improve the long-term intelligence of an AI OS.")
            # Expecting JSON response here. Since router can handle response_model, 
            # we should ideally use that, but for now we'll do simple parsing.
            
            import json
            import re
            
            # Simple cleanup in case of markdown blocks
            content = response.content
            if "```json" in content:
                content = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL).group(1)
            elif "```" in content:
                content = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL).group(1)
            
            insights = json.loads(content)
            
            for insight in insights:
                self.kb.store_insight(
                    key=insight["key"],
                    content=insight["content"],
                    category=insight["category"],
                    quality_score=evaluation.quality_score if evaluation else None,
                    critique=evaluation.critique if evaluation else None,
                    metadata={"source_session": session_id, "original_task": task_description}
                )
                
            return len(insights)
        except Exception as e:
            print(f"Distillation failed: {e}")
            return 0

    def recall_context(self, query: str) -> str:
        """
        Retrieve relevant past knowledge for the current task context.
        """
        results = self.kb.query_knowledge(query)
        if not results:
            return ""
            
        context = "\n### Relevant Past Knowledge & Lessons Learned:\n"
        for res in results:
            score = res.get("metadata", {}).get("quality_score")
            critique = res.get("metadata", {}).get("critique")
            
            score_str = f" [Quality: {score}/10]" if score is not None else ""
            context += f"- [{res['category']}] {res['key']}{score_str}: {res['content']}\n"
            
            if critique:
                context += f"  > Warning/Critique: {critique}\n"
            
        return context

_ltm: Optional[LongTermMemory] = None

def get_ltm(st_memory: Optional[ShortTermMemory] = None) -> LongTermMemory:
    global _ltm
    if _ltm is None:
        _ltm = LongTermMemory(short_term=st_memory)
    return _ltm
