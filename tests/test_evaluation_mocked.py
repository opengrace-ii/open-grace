"""
Component test for the Self-Improvement Loop with mocked LLM.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from open_grace.agents.agent_swarm import AgentSwarm
from open_grace.agents.evaluator_agent import EvaluationReport, EvaluatorAgent
from open_grace.memory.long_term_memory import LongTermMemory
from open_grace.memory.knowledge_store import KnowledgeStore

class TestSelfImprovementLoop(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        # Mocking KnowledgeStore and ModelRouter
        self.mock_kb = MagicMock(spec=KnowledgeStore)
        self.mock_router = AsyncMock()
        
        # Patching get_knowledge_store and get_router
        self.kb_patcher = patch('open_grace.memory.long_term_memory.get_knowledge_store', return_value=self.mock_kb)
        self.router_patcher = patch('open_grace.memory.long_term_memory.get_router', return_value=self.mock_router)
        self.kb_patcher.start()
        self.router_patcher.start()

    async def asyncTearDown(self):
        self.kb_patcher.stop()
        self.router_patcher.stop()

    async def test_distillation_with_evaluation(self):
        """Test that distillation incorporates evaluation metrics."""
        ltm = LongTermMemory()
        ltm.short_term = MagicMock()
        ltm.short_term._history = [
            {"type": "action", "content": "Wrote quicksort implementation"}
        ]
        
        eval_report = EvaluationReport(
            quality_score=9.0,
            alignment_score=10.0,
            critique="Excellent implementation with pivot optimization.",
            efficiency_analysis="O(n log n) achieved.",
            lessons_learned=["Pivot selection is key"],
            improvement_strategies=["Consider hybrid sort for small arrays"]
        )
        
        # Mock LLM distillation response
        mock_response = MagicMock()
        mock_response.content = '[{"key": "Quicksort Pattern", "content": "Use median-of-three for pivot", "category": "coding"}]'
        self.mock_router.generate.return_value = mock_response
        
        await ltm.distill_and_store("session_1", "Implement Quicksort", evaluation=eval_report)
        
        # Verify that store_insight was called with the evaluation data
        self.mock_kb.store_insight.assert_called_once()
        args, kwargs = self.mock_kb.store_insight.call_args
        self.assertEqual(kwargs["quality_score"], 9.0)
        self.assertEqual(kwargs["critique"], "Excellent implementation with pivot optimization.")
        self.assertIn("Implement Quicksort", kwargs["metadata"]["original_task"])
        
        print("✅ Distillation with evaluation verified!")

if __name__ == "__main__":
    unittest.main()
