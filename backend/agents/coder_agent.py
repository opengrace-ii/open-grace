"""
Coder Agent - Writes, debugs, and reviews code.

Specialized agent for software development tasks including:
- Writing new code
- Debugging existing code
- Code review and refactoring
- Test generation
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from backend.agents.base_agent import BaseAgent, AgentTask
from backend.memory.sqlite_store import SQLiteMemoryStore


@dataclass
class CodeSnippet:
    """A code snippet with metadata."""
    language: str
    code: str
    filename: Optional[str] = None
    description: str = ""


@dataclass
class CodeReview:
    """Code review results."""
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    overall_quality: str  # "excellent", "good", "needs_improvement"
    summary: str


class CoderAgent(BaseAgent):
    """
    Agent specialized in software development.
    
    Capabilities:
    - Write code in multiple languages
    - Debug and fix errors
    - Review and refactor code
    - Generate tests
    - Explain code
    
    Usage:
        coder = CoderAgent()
        result = await coder.process_task(AgentTask(
            description="Write a Python function to calculate fibonacci",
            context={"language": "python"}
        ))
    """
    
    def __init__(self, **kwargs):
        """Initialize the coder agent."""
        super().__init__(name="Coder", **kwargs)
        self.sqlite = SQLiteMemoryStore()
        
        # Register tools
        self.register_tool("write_file", self._write_file)
        self.register_tool("read_file", self._read_file)
        self.register_tool("run_tests", self._run_tests)
    
    async def process_task(self, task: AgentTask) -> Any:
        """
        Process a coding task.
        
        Args:
            task: The coding task
            
        Returns:
            Task result
        """
        description = task.description.lower()
        
        # Route to appropriate method
        if any(word in description for word in ["debug", "fix", "error", "bug"]):
            return await self.debug_code(task.description, task.context)
        
        elif any(word in description for word in ["review", "refactor", "improve"]):
            return await self.review_code(task.description, task.context)
        
        elif any(word in description for word in ["test", "testing"]):
            return await self.generate_tests(task.description, task.context)
        
        elif any(word in description for word in ["explain", "understand", "document"]):
            return await self.explain_code(task.description, task.context)
        
        else:
            # Default: write code
            return await self.write_code(task.description, task.context)
    
    async def write_code(self, description: str, 
                        context: Optional[Dict[str, Any]] = None) -> CodeSnippet:
        """
        Write code based on a description.
        
        Args:
            description: What code to write
            context: Additional context (language, constraints, etc.)
            
        Returns:
            CodeSnippet with the generated code
        """
        context = context or {}
        language = context.get("language", "python")
        
        system_prompt = f"""You are an expert {language} programmer. Write clean, well-documented, production-ready code.

Guidelines:
- Include docstrings/comments
- Handle edge cases
- Follow best practices for {language}
- Include type hints if applicable
- Write modular, reusable code

Respond with only the code, no explanations."""
        
        user_prompt = f"Task: {description}\n\nWrite the code:"
        
        response = await self.think(user_prompt, system=system_prompt)
        
        # Extract code from response
        code = self._extract_code(response, language)
        
        filename = context.get("filename")
        working_dir = context.get("working_dir")
        
        if filename and working_dir:
            file_path = Path(working_dir) / filename
            await self._write_file(str(file_path), code)
            self.logger.info(f"CoderAgent wrote code to {file_path}")
        
        return CodeSnippet(
            language=language,
            code=code,
            filename=filename,
            description=description
        )
    
    async def debug_code(self, description: str,
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Debug code with errors.
        
        Args:
            description: Description of the problem
            context: Context including the code and error messages
            
        Returns:
            Debug results with fixed code
        """
        context = context or {}
        code = context.get("code", "")
        error = context.get("error", "")
        language = context.get("language", "python")
        session_id = context.get("session_id", "default")
        
        short_error = error.strip().split('\n')[-1] if error else ""
        
        # Recall from episodic memory
        episodes = self.sqlite.get_episodes(agent_id=self.agent_id, limit=20)
        past_fixes = []
        for ep in episodes:
            # Simple substring matching for now based on error signature
            if short_error and len(short_error) > 5 and short_error in ep.get("context", ""):
                past_fixes.append(ep)
        
        episodic_block = ""
        if past_fixes:
            episodic_block = "\nPast similar fixes you performed:\n"
            for ep in past_fixes[:3]:
                episodic_block += f"- Context (Error): {ep.get('context')}\n- Fix:\n{ep.get('result')}\n"
        
        system_prompt = """You are a debugging expert. Analyze the code and error, then provide:
1. Root cause analysis
2. The fixed code
3. Explanation of the fix

Respond in this format:
ANALYSIS: <root cause>
FIXED_CODE:
```<language>
<fixed code>
```
EXPLANATION: <why the fix works>"""
        
        user_prompt = f"""Error: {error}

Code:
```{language}
{code}
```{episodic_block}

Debug this code."""
        
        response = await self.think(user_prompt, system=system_prompt)
        
        # Parse response
        analysis = self._extract_section(response, "ANALYSIS")
        fixed_code = self._extract_code(response, language)
        explanation = self._extract_section(response, "EXPLANATION")
        
        if analysis and fixed_code:
            self.sqlite.save_episode(
                session_id=session_id,
                agent_id=self.agent_id,
                context=short_error,
                action="debug_code",
                result=fixed_code
            )
        
        return {
            "analysis": analysis,
            "fixed_code": fixed_code,
            "explanation": explanation,
            "language": language
        }
    
    async def review_code(self, description: str,
                         context: Optional[Dict[str, Any]] = None) -> CodeReview:
        """
        Review code for quality and issues.
        
        Args:
            description: Description of what to review
            context: Context including the code
            
        Returns:
            CodeReview with findings
        """
        context = context or {}
        code = context.get("code", "")
        language = context.get("language", "python")
        
        system_prompt = """You are a code reviewer. Analyze the code for:
- Bugs and logic errors
- Security issues
- Performance problems
- Code style violations
- Maintainability issues

Respond in JSON format:
{
  "issues": [
    {"severity": "high|medium|low", "line": 5, "message": "description"}
  ],
  "suggestions": ["improvement ideas"],
  "overall_quality": "excellent|good|needs_improvement",
  "summary": "brief overall assessment"
}"""
        
        user_prompt = f"""Review this {language} code:

```{language}
{code}
```

Provide a detailed review."""
        
        response = await self.think(user_prompt, system=system_prompt)
        
        try:
            # Extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            review_data = json.loads(response[json_start:json_end])
            
            return CodeReview(
                issues=review_data.get("issues", []),
                suggestions=review_data.get("suggestions", []),
                overall_quality=review_data.get("overall_quality", "good"),
                summary=review_data.get("summary", "")
            )
        except:
            return CodeReview(
                issues=[],
                suggestions=["Could not parse review"],
                overall_quality="unknown",
                summary="Review parsing failed"
            )
    
    async def generate_tests(self, description: str,
                            context: Optional[Dict[str, Any]] = None) -> CodeSnippet:
        """
        Generate unit tests for code.
        
        Args:
            description: Description of what to test
            context: Context including the code to test
            
        Returns:
            CodeSnippet with test code
        """
        context = context or {}
        code = context.get("code", "")
        language = context.get("language", "python")
        test_framework = context.get("framework", "pytest" if language == "python" else "jest")
        
        system_prompt = f"""You are a testing expert. Generate comprehensive unit tests using {test_framework}.

Include tests for:
- Normal cases
- Edge cases
- Error cases
- Boundary conditions

Respond with only the test code."""
        
        user_prompt = f"""Generate tests for this {language} code:

```{language}
{code}
```

Write comprehensive tests."""
        
        response = await self.think(user_prompt, system=system_prompt)
        
        test_code = self._extract_code(response, language)
        
        return CodeSnippet(
            language=language,
            code=test_code,
            filename=f"test_{context.get('filename', 'module')}",
            description=f"Tests for {description}"
        )
    
    async def explain_code(self, description: str,
                          context: Optional[Dict[str, Any]] = None) -> str:
        """
        Explain what code does.
        
        Args:
            description: What to explain
            context: Context including the code
            
        Returns:
            Explanation text
        """
        context = context or {}
        code = context.get("code", "")
        language = context.get("language", "python")
        
        system_prompt = """You are a programming teacher. Explain the code clearly and concisely.

Structure your explanation:
1. High-level overview
2. Key components/functions
3. How it works (step by step)
4. Any important details

Use simple language but be technically accurate."""
        
        user_prompt = f"""Explain this {language} code:

```{language}
{code}
```

{description}"""
        
        return await self.think(user_prompt, system=system_prompt)
    
    def _extract_code(self, text: str, language: str) -> str:
        """Extract code from markdown code blocks."""
        # Look for code blocks
        pattern = rf'```{language}\s*\n(.*?)\n```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try any code block
        pattern = r'```\s*\n(.*?)\n```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Return full text if no code blocks
        return text.strip()
    
    def _extract_section(self, text: str, section: str) -> str:
        """Extract a section from text."""
        pattern = rf'{section}:\s*(.*?)(?=\n\w+:|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    async def _write_file(self, path: str, content: str) -> bool:
        """Tool: Write content to a file."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write file {path}: {e}")
            return False
    
    async def _read_file(self, path: str) -> str:
        """Tool: Read content from a file."""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {path}: {e}")
            return ""
    
    async def _run_tests(self, command: str) -> Dict[str, Any]:
        """Tool: Run tests using a command."""
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }