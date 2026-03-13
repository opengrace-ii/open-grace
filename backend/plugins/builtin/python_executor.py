"""
Python Executor Tool - Safe code execution for Open Grace agents.
"""

from typing import Dict, List, Optional, Any
from backend.plugins.sdk import Plugin, PluginMetadata, PluginType, tool
from backend.sandbox.bwrap_runner import get_sandbox

class PythonExecutorPlugin(Plugin):
    """Plugin providing safe Python execution."""
    
    def __init__(self):
        super().__init__(
            metadata=PluginMetadata(
                name="python_executor",
                version="1.0.0",
                description="Safe Python code execution",
                author="Open Grace",
                plugin_type=PluginType.TOOL
            )
        )
        self.sandbox = get_sandbox()
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config
        self.register_tool("execute_python", self.execute_python, permission_level="normal")
        return True

    def execute_python(self, code: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute Python code safely within the bubblewrap sandbox.
        """
        # Wrap the code to handle possible single/double quote issues in bash -c
        # For simplicity, we write it to a temporary file inside the sandbox first
        # but since we already have write_file, the agent could do that.
        # Alternatively, we just pass it via aHEREDOC or similar.
        
        # Escaping code for bash -c "python3 -c '...'" is tricky.
        # Let's use a simpler approach: use temporary script file.
        
        script_path = "/home/opengrace/open_grace/workspace/tmp_script.py"
        try:
            with open(script_path, 'w') as f:
                f.write(code)
            
            # Execute the script file inside the sandbox
            result = self.sandbox.run_command(f"python3 {script_path}", working_dir=working_dir)
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

import os # Needed in execute_python
