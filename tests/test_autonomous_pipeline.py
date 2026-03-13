import asyncio
import logging
from open_grace.core.orchestrator import AgentOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_pipeline():
    print("🚀 Starting End-to-End Orchestrator Pipeline Test")
    
    orchestrator = AgentOrchestrator()
    
    goal = "Create a simple Python script named 'hello_world.py' in the current project directory and run it."
    
    print(f"📝 Goal: {goal}")
    
    try:
        result = await orchestrator.run(goal)
        print(f"\n✅ Result: {result}")
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
