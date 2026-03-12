import asyncio
from open_grace.kernel.orchestrator import GraceOrchestrator, TaskStatus
from open_grace.memory.sqlite_store import SQLiteMemoryStore

class MockFailingAgent:
    async def execute(self, description):
        raise ValueError("Simulated critical failure for Graph of Thoughts testing!")

async def main():
    print("Testing Graph-of-Thoughts Execution Engine...")
    
    # Initialize orchestrator locally
    orchestrator = GraceOrchestrator()
    orchestrator.memory = SQLiteMemoryStore()
    
    # We won't start the full worker loop to avoid it consuming tasks before we can inspect
    # Instead, we'll manually execute the task.
    # Wait, _task_worker is started on initialize. Let's do a manual execution without initialize.
    
    agent_id = await orchestrator.register_agent(
        "research", "TestAgent", ["test"], MockFailingAgent()
    )
    
    task_id = await orchestrator.submit_task("Analyze code", "research")
    task = orchestrator._tasks[task_id]
    
    print(f"Executing task {task_id} with simulated failure...")
    await orchestrator._execute_task(task)
    
    print(f"Task status is now: {task.status}")
    
    assert task.status == TaskStatus.BRANCHING, f"Expected BRANCHING, got {task.status}"
    
    branches = task.metadata.get("branches")
    assert branches is not None and len(branches) == 2, "Expected 2 branches to be created"
    
    print(f"Successfully entered Graph-of-Thoughts branching state.")
    print(f"Rollback Branch Task ID: {branches[0]}")
    print(f"Investigate Branch Task ID: {branches[1]}")
    print("Graph-of-Thoughts tests SUCCESS!")

if __name__ == "__main__":
    asyncio.run(main())
