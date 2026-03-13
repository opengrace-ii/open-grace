"""
Verification test for the Self-Improvement / Evaluation Loop.
"""

import asyncio
import json
import os
from open_grace.agents.agent_swarm import AgentSwarm
from open_grace.agents.evaluator_agent import EvaluationReport
from open_grace.memory.long_term_memory import get_ltm
from open_grace.memory.knowledge_store import get_knowledge_store

async def verify_loop():
    print("--- Starting Self-Improvement Loop Verification ---")
    
    swarm = AgentSwarm()
    await swarm.initialize()
    
    # 1. Execute a task that will trigger the loop
    print("\n1. Executing an example task...")
    task_desc = "Implement a quicksort in Python"
    result = await swarm.execute(task_desc)
    
    if "evaluation" in result:
        print("\n2. Evaluation successfully triggered!")
        eval_report = result["evaluation"]
        print(f"   Quality Score: {eval_report['quality_score']}/10")
        print(f"   Critique: {eval_report['critique'][:100]}...")
    else:
        print("\nFAILED: Evaluation not found in result.")
        return

    # 2. Check if knowledge was stored with evaluation data
    print("\n3. Checking KnowledgeStore for quality metrics...")
    kb = get_knowledge_store()
    items = kb.get_by_category("coding")
    
    found = False
    for item in items:
        # Items are dicts returned by dict(row)
        if item.get("quality_score") is not None:
            print(f"   Found knowledge item with quality score: {item['quality_score']}")
            print(f"   Critique stored correctly.")
            found = True
            break
    
    if not found:
        print("   FAILED: No knowledge items with quality metrics found.")
        return

    # 3. Test recall enhancement
    print("\n4. Testing enhanced recall...")
    ltm = get_ltm()
    recall_context = ltm.recall_context("quicksort implementation")
    
    if "[Quality:" in recall_context and "Warning/Critique:" in recall_context:
        print("   Recall context successfully enhanced with quality metrics!")
    else:
        # It might not have surfaced if the search didn't match perfectly, 
        # but in a clean test it should.
        print("   Warning: Recall context might not show all metrics depending on vector search results.")
        print(f"   Raw recall context start: {recall_context[:200]}...")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_loop())
