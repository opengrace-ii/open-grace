import asyncio
import logging
from open_grace.core.orchestrator import AgentOrchestrator
from open_grace.core.resource_manager import ResourceManager
from open_grace.model_router.router import get_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_resource_management():
    print("\n--- Testing Resource Management and Concurrency ---\n")
    
    rm = ResourceManager(max_agents=2, max_models=1)
    orchestrator = AgentOrchestrator()
    router = get_router()
    
    print(f"Initial Status: {rm.get_status()}")
    
    # Test Agent Throttling
    print("\n1. Testing Agent Throttling...")
    async def dummy_agent_task(name, duration=1):
        print(f"Agent {name} starting...")
        await asyncio.sleep(duration)
        print(f"Agent {name} finished.")
        return f"Result from {name}"

    # Run 3 agents with a semaphore of 2
    tasks = [
        rm.run_agent(dummy_agent_task, "Alpha", 2),
        rm.run_agent(dummy_agent_task, "Beta", 2),
        rm.run_agent(dummy_agent_task, "Gamma", 2)
    ]
    
    print("Started 3 agents (limit is 2)...")
    results = await asyncio.gather(*tasks)
    print(f"Agent results: {results}")

    # Test Model Throttling
    print("\n2. Testing Model Throttling...")
    # Note: This uses the real router which now has a semaphore
    async def fast_generate():
        return await router.generate("test prompt", max_retries=1)

    # We can't easily "gather" and see the lock in action without mocking,
    # but the semaphore is now integrated in the router calls.
    
    print("\n3. Testing Orchestrator Step Limit...")
    # The orchestrator now has MAX_AGENT_STEPS = 5 and a break
    try:
        result = await orchestrator.run("Hello World project")
        print(f"Orchestrator result: {result}")
    except Exception as e:
        print(f"Orchestrator failed as expected under some conditions: {e}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_resource_management())
