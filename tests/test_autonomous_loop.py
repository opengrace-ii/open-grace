import asyncio
import os
import sys
from pathlib import Path

# Add project root to path with priority
sys.path.insert(0, str(Path(__file__).parent.parent))

from open_grace.agents.agent_swarm import AgentSwarm
from open_grace.kernel.orchestrator import GraceOrchestrator

async def test_autonomous_loop():
    print("🚀 Starting Autonomous Loop Test...")
    
    swarm = AgentSwarm()
    
    task = "Create a simple Python script named 'hello.py' that prints 'Hello from TaskForge!' and then run it."
    
    print(f"📝 Task: {task}")
    
    results = await swarm.execute(task)
    
    print("\n✅ Test Results:")
    print(f"Status: {'Success' if results.get('success') else 'Failed'}")
    
    if results.get("error"):
        print(f"Error: {results.get('error')}")
    
    print("\nStep breakdown:")
    for step_id, result in results.get("results", {}).items():
        print(f"- Step {step_id}: {'✔️' if result.get('success') else '❌'} {result.get('error', '')}")
        if result.get("result"):
            print(f"  Result: {result.get('result')[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_autonomous_loop())
