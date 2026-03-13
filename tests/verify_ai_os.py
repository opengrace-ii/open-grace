"""
Unified verification script for System 1 (Long-Term Memory) and System 2 (Tool System).
"""

import asyncio
import os
from open_grace.memory.knowledge_store import get_knowledge_store
from open_grace.memory.long_term_memory import get_ltm
from open_grace.memory.short_term_memory import ShortTermMemory
from open_grace.plugins.builtin.file_editor import FileEditorPlugin
from open_grace.plugins.builtin.python_executor import PythonExecutorPlugin

async def verify_ai_os():
    print("\n--- Verifying AI OS Evolution Components ---\n")
    
    # 1. Verify Tools (System 2)
    print("1. Testing Builtin Tools...")
    editor = FileEditorPlugin()
    editor.initialize({})
    
    executor = PythonExecutorPlugin()
    executor.initialize({})
    
    test_file = "evolution_test.txt"
    write_res = editor.write_file(test_file, "Builtin tools are functional.")
    print(f"   [FileEditor] Write: {write_res}")
    
    read_res = editor.read_file(test_file)
    print(f"   [FileEditor] Read: {read_res}")
    
    exec_res = executor.execute_python("print('Python executor is alive!')")
    print(f"   [PythonExecutor] Result: {exec_res.get('stdout', '').strip()}")
    
    # 2. Verify Memory (System 1)
    print("\n2. Testing Long-Term Memory Distillation...")
    st_memory = ShortTermMemory()
    st_memory.add_event("action", "Fixed a bug in React component", {"file": "App.js"})
    st_memory.add_event("finding", "Using UseMemo here improved FPS by 20%", {"metric": "fps"})
    
    ltm = get_ltm(st_memory=st_memory)
    print("   Distilling short-term memory...")
    insights_count = await ltm.distill_and_store("test_session", "Optimize React performance")
    print(f"   Insights stored: {insights_count}")
    
    print("\n3. Testing Knowledge Recall...")
    recall = ltm.recall_context("How do I improve React performance?")
    print(f"   Recalled Context:\n{recall}")
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_ai_os())
