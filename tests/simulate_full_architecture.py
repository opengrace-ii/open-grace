import asyncio
import logging
import os
from open_grace.core.orchestrator import AgentOrchestrator
from open_grace.core.task_queue import get_task_queue
from open_grace.core.workspace_manager import get_workspace_manager
from open_grace.diagnostics.event_logger import get_event_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_autonomous_system():
    print("\n--- Simulating Full Autonomous Architecture ---\n")
    
    # 1. Initialize Components
    queue = get_task_queue()
    wm = get_workspace_manager()
    logger = get_event_logger()
    orchestrator = AgentOrchestrator()
    
    # 2. Add Task to Queue
    print("1. Adding task to queue...")
    task_id = await queue.add_task("Create a simple landing page artifact")
    
    # 3. Scheduler Simulation
    print("2. Scheduler retrieving task...")
    task = await queue.get_task()
    
    # 4. Orchestrator Processing
    print(f"3. Orchestrator starting task: {task['goal']}")
    logger.log_event("Simulation", "TaskStarted", {"id": task_id, "goal": task["goal"]})
    
    try:
        # We run the orchestrator which now uses WorkspaceManager and Sandbox
        # We'll mock the actual agent calls if they take too long, 
        # but the infrastructure is what we are testing.
        result = await orchestrator.run(task["goal"])
        print(f"Orchestration Result: {result}")
        
        # 5. Verify Workspace
        project_name = task["goal"].lower().replace(" ", "_").strip()[:20]
        files = wm.list_project_files(project_name)
        print(f"4. Workspace files generated: {files}")
        
        logger.log_event("Simulation", "TaskCompleted", {"id": task_id, "success": True})
        queue.mark_done(task_id)
        
    except Exception as e:
        print(f"Simulation failed: {e}")
        logger.log_event("Simulation", "TaskFailed", {"id": task_id, "error": str(e)}, level="ERROR")

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    asyncio.run(simulate_autonomous_system())
