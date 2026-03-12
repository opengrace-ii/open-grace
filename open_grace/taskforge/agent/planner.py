"""
Planner for TaskForge.
Uses LLM (Ollama) to plan tasks and decide which tools to use.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import httpx


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    step_number: int
    tool: str
    action: str
    args: Dict[str, Any]
    description: str
    depends_on: List[int] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class TaskPlan:
    """A complete plan for executing a task."""
    task: str
    steps: List[PlanStep]
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "reasoning": self.reasoning,
            "steps": [asdict(step) for step in self.steps]
        }


class OllamaClient:
    """Client for Ollama LLM API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "llama3",
                 temperature: float = 0.7):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "")
        except httpx.ConnectError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running."
            )
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with the LLM."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
        except httpx.ConnectError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running."
            )
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def list_models(self) -> List[str]:
        """List available models."""
        url = f"{self.base_url}/api/tags"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                models = response.json().get("models", [])
                return [m["name"] for m in models]
        except Exception:
            return []


class Planner:
    """
    Task planner using LLM to generate execution plans.
    
    The planner:
    1. Analyzes the user's task
    2. Decides which tools to use
    3. Creates a step-by-step plan
    4. Returns structured plan data
    """
    
    SYSTEM_PROMPT = """You are TaskForge, an AI automation agent. Your job is to analyze user tasks and create execution plans.

Available tools and their parameters:

1. shell: Execute shell commands
   - Required: command (the shell command string)
   - Optional: cwd (working directory), timeout (seconds)
   - Example args: {"command": "ls -la", "cwd": "/home/user"}

2. file: File operations
   - Required: action (read, write, list, move, copy, delete, mkdir, info, exists), path
   - Optional: content (for write), destination (for move/copy), recursive (bool)
   - Example args: {"action": "list", "path": "/home/user/Downloads"}

3. git: Git operations
   - Required: action (status, log, commit, push, pull, branch, add, clone), path
   - Optional: message (for commit), branch (for branch operations), remote, url, files
   - Example args: {"action": "status", "path": "."}

4. sql: SQLite database operations
   - Required: action (query, execute, tables, schema), database (file path)
   - Optional: query (SQL string), params (list of parameters)
   - Example args: {"action": "tables", "database": "data.db"}

When given a task, create a step-by-step plan using these tools.
Respond in this exact JSON format:

{
  "reasoning": "Brief explanation of your approach",
  "steps": [
    {
      "step_number": 1,
      "tool": "tool_name",
      "action": "action_name",
      "args": {"arg1": "value1", "arg2": "value2"},
      "description": "What this step does",
      "depends_on": []
    }
  ]
}

Important:
- For shell tool: put the command in args.command, NOT in action
- For file/git/sql tools: put the action name in action field AND in args.action
- Use absolute paths when possible
- The user's home directory is /home/opengrace (NOT /home/user)
- Downloads folder is at /home/opengrace/Downloads
- Chain steps using depends_on when order matters
- Be specific with file paths and arguments
- Only use available tools
"""
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.client = OllamaClient(base_url=base_url, model=model)
        self.model = model
    
    async def plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        Create an execution plan for a task.
        
        Args:
            task: The user's task description
            context: Optional context information
            
        Returns:
            TaskPlan with steps to execute
        """
        # Build the prompt
        prompt = f"Task: {task}\n\n"
        
        # Add default context
        prompt += "Context:\n"
        prompt += f"  home_directory: /home/opengrace\n"
        prompt += f"  current_directory: {os.getcwd()}\n"
        prompt += f"  user: opengrace\n"
        
        if context:
            for key, value in context.items():
                prompt += f"  {key}: {value}\n"
        prompt += "\n"
        
        prompt += "Create an execution plan in JSON format:"
        
        # Generate plan
        try:
            response = await self.client.generate(prompt, system=self.SYSTEM_PROMPT)
            return self._parse_plan(task, response)
        except ConnectionError:
            # Fallback to simple plan if Ollama not available
            return self._fallback_plan(task)
        except Exception as e:
            print(f"Planning error: {e}")
            return self._fallback_plan(task)
    
    def _parse_plan(self, task: str, response: str) -> TaskPlan:
        """Parse the LLM response into a TaskPlan."""
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                
                steps = []
                for step_data in data.get("steps", []):
                    steps.append(PlanStep(
                        step_number=step_data.get("step_number", len(steps) + 1),
                        tool=step_data.get("tool", "shell"),
                        action=step_data.get("action", ""),
                        args=step_data.get("args", {}),
                        description=step_data.get("description", ""),
                        depends_on=step_data.get("depends_on", [])
                    ))
                
                return TaskPlan(
                    task=task,
                    steps=steps,
                    reasoning=data.get("reasoning", "")
                )
            except json.JSONDecodeError:
                pass
        
        # If parsing fails, return fallback plan
        return self._fallback_plan(task)
    
    def _fallback_plan(self, task: str) -> TaskPlan:
        """Create a simple fallback plan when LLM is unavailable."""
        # Simple keyword-based planning
        task_lower = task.lower()
        steps = []
        
        if "list" in task_lower or "show" in task_lower:
            if "file" in task_lower or "directory" in task_lower or "folder" in task_lower:
                steps.append(PlanStep(
                    step_number=1,
                    tool="file",
                    action="list",
                    args={"path": "."},
                    description="List files in current directory"
                ))
        
        elif "read" in task_lower or "view" in task_lower or "cat" in task_lower:
            steps.append(PlanStep(
                step_number=1,
                tool="shell",
                action="run",
                args={"command": f"echo 'Please specify a file to read'"},
                description="Prompt for file specification"
            ))
        
        elif "git" in task_lower:
            if "status" in task_lower:
                steps.append(PlanStep(
                    step_number=1,
                    tool="git",
                    action="status",
                    args={"path": "."},
                    description="Check git status"
                ))
            elif "log" in task_lower:
                steps.append(PlanStep(
                    step_number=1,
                    tool="git",
                    action="log",
                    args={"path": "."},
                    description="Show git log"
                ))
        
        if not steps:
            steps.append(PlanStep(
                step_number=1,
                tool="shell",
                action="run",
                args={"command": f"echo 'Task: {task}'"},
                description="Echo task (fallback)"
            ))
        
        return TaskPlan(
            task=task,
            steps=steps,
            reasoning="Fallback plan (LLM unavailable)"
        )
    
    async def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Have a conversation with the LLM.
        
        Args:
            message: User message
            history: Previous conversation history
            
        Returns:
            LLM response
        """
        messages = history or []
        messages.append({"role": "user", "content": message})
        
        try:
            return await self.client.chat(messages)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def set_model(self, model: str):
        """Change the LLM model."""
        self.model = model
        self.client.model = model
    
    async def is_available(self) -> bool:
        """Check if the LLM is available."""
        try:
            models = await self.client.list_models()
            return len(models) > 0
        except Exception:
            return False
