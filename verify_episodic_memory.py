import asyncio
import os
from open_grace.agents.coder_agent import CoderAgent
from open_grace.agents.base_agent import AgentTask
from open_grace.memory.sqlite_store import SQLiteMemoryStore

# Mock ModelRouter to avoid actual LLM calls
class MockRouter:
    def __init__(self):
        self.call_count = 0
        self.last_prompt = ""
    
    async def think(self, prompt, **kwargs):
        self.call_count += 1
        self.last_prompt = prompt
        
        return """
ANALYSIS: Found the off-by-one bug.
FIXED_CODE:
```python
def my_func(arr):
    for i in range(len(arr)):
        print(arr[i])
```
EXPLANATION: Changed range limit.
"""
    
    # We will patch the CoderAgent.think to use our mock
    
async def main():
    print("Testing Contextual RAG with Episodic Memory...")
    
    # Ensure memory db is clear or use a test one
    store = SQLiteMemoryStore("./data/test_memory.db")
    
    coder = CoderAgent(agent_id="test_coder")
    coder.sqlite = store
    
    # Patch think to use our mock
    mock_router = MockRouter()
    async def mock_think(prompt, **kwargs):
        return await mock_router.think(prompt, **kwargs)
    coder.think = mock_think
    
    # First Error!
    print("\\n[1] Submitting task with error...")
    task1 = AgentTask(
        id="task_1",
        description="Fix the IndexError in this array loop.",
        context={
            "language": "python",
            "code": "def my_func(arr):\\n    for i in range(len(arr) + 1):\\n        print(arr[i])",
            "error": "IndexError: list index out of range",
            "session_id": "test_session"
        }
    )
    
    result1 = await coder.process_task(task1)
    
    # Check if memory was saved
    episodes = store.get_episodes(agent_id="test_coder")
    assert len(episodes) > 0, "No episodic memory saved!"
    print(f"[✓] Saved {len(episodes)} episodes.")
    
    # Second Error! Same type of bug
    print("\\n[2] Submitting similar task to check recall...")
    task2 = AgentTask(
        id="task_2",
        description="Fix another array loop.",
        context={
            "language": "python",
            "code": "def other_func(arr):\\n    for j in range(len(arr) + 1):\\n        do_something(arr[j])",
            "error": "IndexError: list index out of range",
            "session_id": "test_session_2"
        }
    )
    
    result2 = await coder.process_task(task2)
    
    # Verify the prompt contained the episodic block
    assert "Past similar fixes you performed:" in mock_router.last_prompt, "RAG Context was not injected!"
    print("[✓] RAG Context injected successfully!")
    print("\\nVerifying episodic memory injection block:")
    
    # Print a snippet of the injected context
    snippet_start = mock_router.last_prompt.find("Past similar fixes you performed:")
    snippet = mock_router.last_prompt[snippet_start:snippet_start + 250]
    print("------------------------------------------")
    print(snippet + "...")
    print("------------------------------------------")
    
    print("\\nContextual RAG Extrinsic Memory tests SUCCESS!")
    
    # cleanup
    if os.path.exists("./data/test_memory.db"):
        os.remove("./data/test_memory.db")

if __name__ == "__main__":
    asyncio.run(main())
