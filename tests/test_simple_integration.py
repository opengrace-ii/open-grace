"""
Simple integration test for Self-Improvement Loop.
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from open_grace.memory.long_term_memory import LongTermMemory
from open_grace.agents.evaluator_agent import EvaluationReport

async def run_test():
    print("--- Simplified Integration Test ---")
    
    # Mock dependencies
    mock_kb = MagicMock()
    mock_router = AsyncMock()
    
    with patch('open_grace.memory.long_term_memory.get_knowledge_store', return_value=mock_kb), \
         patch('open_grace.memory.long_term_memory.get_router', return_value=mock_router):
        
        ltm = LongTermMemory()
        ltm.short_term = MagicMock()
        ltm.short_term._history = [{"type": "action", "content": "Test action"}]
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = '[{"key": "test_key", "content": "test_content", "category": "general"}]'
        mock_router.generate.return_value = mock_response
        
        eval_report = EvaluationReport(
            quality_score=8.5,
            alignment_score=9.0,
            critique="Good job.",
            efficiency_analysis="Efficient.",
            lessons_learned=["Keep testing"],
            improvement_strategies=["Add more mocks"]
        )
        
        print("Running distillation...")
        await ltm.distill_and_store("session_test", "Test task", evaluation=eval_report)
        
        # Verify store_insight call
        if mock_kb.store_insight.called:
            args, kwargs = mock_kb.store_insight.call_args
            print(f"✅ store_insight called successfully!")
            print(f"   Quality score in call: {kwargs.get('quality_score')}")
            print(f"   Critique in call: {kwargs.get('critique')}")
        else:
            print("❌ FAILED: store_insight was not called.")

if __name__ == "__main__":
    asyncio.run(run_test())
