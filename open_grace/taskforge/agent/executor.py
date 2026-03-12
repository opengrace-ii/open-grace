import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from tools.base_tool import BaseTool, ToolOutput
from agent.planner import PlanStep, TaskPlan
from security.permissions import PermissionManager, ActionCategory, get_permission_manager


@dataclass
class ExecutionResult:
    """Result of executing a plan step."""
    step_number: int
    tool: str
    action: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Executor:
    """
    Executes task plans using registered tools.
    
    Features:
    - Tool registry management
    - Permission checking
    - Step-by-step execution
    - Error handling and recovery
    - Execution logging
    """
    
    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None,
                 permission_manager: Optional[PermissionManager] = None):
        self.tools: Dict[str, BaseTool] = tools or {}
        self.permission_manager = permission_manager or get_permission_manager()
        self.execution_history: List[ExecutionResult] = []
    
    def register_tool(self, tool: BaseTool):
        """Register a tool for execution."""
        self.tools[tool.name] = tool
    
    def register_tools(self, tools: List[BaseTool]):
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute_step(self, step: PlanStep, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a single plan step.
        
        Args:
            step: The plan step to execute
            context: Execution context from previous steps
            
        Returns:
            ExecutionResult with outcome
        """
        start_time = time.time()
        
        # Check if tool exists
        if step.tool not in self.tools:
            return ExecutionResult(
                step_number=step.step_number,
                tool=step.tool,
                action=step.action,
                success=False,
                error=f"Tool '{step.tool}' not found. Available: {', '.join(self.tools.keys())}"
            )
        
        tool = self.tools[step.tool]
        
        # Check permissions
        action_str = f"{step.tool}.{step.action}({step.args})"
        category = self._get_action_category(step.tool)
        
        if not self.permission_manager.check_permission(action_str, category):
            return ExecutionResult(
                step_number=step.step_number,
                tool=step.tool,
                action=step.action,
                success=False,
                error="Permission denied by user"
            )
        
        # Execute the tool
        try:
            # Merge context into args if needed
            args = step.args.copy()
            if context:
                # Replace placeholders like {{step1.result.path}}
                args = self._resolve_placeholders(args, context)
            
            # Add action to args for tools that need it
            if step.action:
                if step.tool in ['file', 'git', 'sql']:
                    args['action'] = step.action
            
            # Run the tool - use to_thread to avoid blocking event loop
            if asyncio.iscoroutinefunction(tool.run):
                output: ToolOutput = await tool.run(**args)
            else:
                output: ToolOutput = await asyncio.to_thread(tool.run, **args)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            result = ExecutionResult(
                step_number=step.step_number,
                tool=step.tool,
                action=step.action,
                success=output.success,
                result=output.result,
                error=output.error,
                execution_time_ms=execution_time
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            result = ExecutionResult(
                step_number=step.step_number,
                tool=step.tool,
                action=step.action,
                success=False,
                error=f"{str(e)}\n{traceback.format_exc()}",
                execution_time_ms=execution_time
            )
            
            self.execution_history.append(result)
            return result
    
    async def execute_plan(self, plan: TaskPlan, 
                             stop_on_error: bool = True) -> List[ExecutionResult]:
        """
        Execute a complete plan.
        
        Args:
            plan: The task plan to execute
            stop_on_error: Whether to stop on first error
            
        Returns:
            List of execution results
        """
        results = []
        context: Dict[str, Any] = {}
        
        # Sort steps by step number
        sorted_steps = sorted(plan.steps, key=lambda s: s.step_number)
        
        for step in sorted_steps:
            # Check dependencies
            if step.depends_on:
                deps_satisfied = all(
                    any(r.step_number == dep and r.success for r in results)
                    for dep in step.depends_on
                )
                if not deps_satisfied:
                    results.append(ExecutionResult(
                        step_number=step.step_number,
                        tool=step.tool,
                        action=step.action,
                        success=False,
                        error=f"Dependencies not satisfied: {step.depends_on}"
                    ))
                    if stop_on_error:
                        break
                    continue
            
            # Execute step
            result = await self.execute_step(step, context)
            results.append(result)
            
            # Store result in context for future steps
            context[f"step{step.step_number}"] = {
                "success": result.success,
                "result": result.result,
                "error": result.error
            }
            
            # Stop on error if configured
            if not result.success and stop_on_error:
                break
        
        return results
    
    def _get_action_category(self, tool_name: str) -> ActionCategory:
        """Map tool name to action category."""
        category_map = {
            "shell": ActionCategory.SHELL,
            "file": ActionCategory.FILE_WRITE,
            "git": ActionCategory.GIT_PUSH,
            "sql": ActionCategory.SQL_WRITE,
        }
        return category_map.get(tool_name, ActionCategory.SYSTEM)
    
    def _resolve_placeholders(self, args: Dict[str, Any], 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve placeholder values in arguments."""
        resolved = {}
        
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # Parse placeholder like {{step1.result.path}}
                placeholder = value[2:-2]  # Remove {{ and }}
                parts = placeholder.split(".")
                
                try:
                    current = context
                    for part in parts:
                        if isinstance(current, dict):
                            current = current.get(part)
                        else:
                            current = None
                            break
                    
                    resolved[key] = current if current is not None else value
                except Exception:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution history."""
        if not self.execution_history:
            return {"total": 0, "successful": 0, "failed": 0}
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        failed = total - successful
        
        total_time = sum(r.execution_time_ms for r in self.execution_history)
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "total_time_ms": total_time,
            "average_time_ms": total_time // total if total > 0 else 0
        }
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history.clear()
