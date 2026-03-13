"""
Task Scheduler - Advanced task scheduling for Open Grace.

Supports:
- Priority-based scheduling
- Cron-based recurring tasks
- Resource-aware scheduling
- Task dependencies
"""

import asyncio
import croniter
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class ScheduleType(Enum):
    """Types of task schedules."""
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"


@dataclass
class ScheduledTask:
    """A scheduled task definition."""
    id: str
    name: str
    description: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    task_func: Callable
    priority: int = 5
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskScheduler:
    """
    Advanced task scheduler for Open Grace.
    
    Supports one-time, interval, and cron-based scheduling.
    
    Usage:
        scheduler = TaskScheduler()
        
        # Schedule a one-time task
        scheduler.schedule_once("cleanup", cleanup_func, delay_seconds=3600)
        
        # Schedule recurring task
        scheduler.schedule_interval("backup", backup_func, interval_seconds=86400)
        
        # Schedule with cron
        scheduler.schedule_cron("report", report_func, cron="0 9 * * 1")
        
        await scheduler.start()
    """
    
    def __init__(self):
        self._schedules: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._check_interval = 1.0  # seconds
    
    async def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
    
    def schedule_once(self, name: str, task_func: Callable,
                     delay_seconds: float = 0,
                     priority: int = 5,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule a one-time task.
        
        Args:
            name: Task name
            task_func: Function to execute
            delay_seconds: Delay before execution
            priority: Task priority
            metadata: Additional metadata
            
        Returns:
            Schedule ID
        """
        schedule_id = f"sched_{str(uuid.uuid4())[:8]}"
        
        next_run = datetime.now() + timedelta(seconds=delay_seconds)
        
        schedule = ScheduledTask(
            id=schedule_id,
            name=name,
            description=f"One-time task: {name}",
            schedule_type=ScheduleType.ONCE,
            schedule_config={"delay_seconds": delay_seconds},
            task_func=task_func,
            priority=priority,
            next_run=next_run,
            max_runs=1,
            metadata=metadata or {}
        )
        
        self._schedules[schedule_id] = schedule
        return schedule_id
    
    def schedule_interval(self, name: str, task_func: Callable,
                         interval_seconds: float,
                         priority: int = 5,
                         max_runs: Optional[int] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule a recurring interval task.
        
        Args:
            name: Task name
            task_func: Function to execute
            interval_seconds: Interval between runs
            priority: Task priority
            max_runs: Maximum number of runs (None = unlimited)
            metadata: Additional metadata
            
        Returns:
            Schedule ID
        """
        schedule_id = f"sched_{str(uuid.uuid4())[:8]}"
        
        schedule = ScheduledTask(
            id=schedule_id,
            name=name,
            description=f"Interval task: {name} (every {interval_seconds}s)",
            schedule_type=ScheduleType.INTERVAL,
            schedule_config={"interval_seconds": interval_seconds},
            task_func=task_func,
            priority=priority,
            next_run=datetime.now(),
            max_runs=max_runs,
            metadata=metadata or {}
        )
        
        self._schedules[schedule_id] = schedule
        return schedule_id
    
    def schedule_cron(self, name: str, task_func: Callable,
                     cron: str,
                     priority: int = 5,
                     max_runs: Optional[int] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule a cron-based task.
        
        Args:
            name: Task name
            task_func: Function to execute
            cron: Cron expression (e.g., "0 9 * * 1" for Mondays at 9am)
            priority: Task priority
            max_runs: Maximum number of runs (None = unlimited)
            metadata: Additional metadata
            
        Returns:
            Schedule ID
        """
        schedule_id = f"sched_{str(uuid.uuid4())[:8]}"
        
        # Calculate next run
        itr = croniter.croniter(cron, datetime.now())
        next_run = itr.get_next(datetime)
        
        schedule = ScheduledTask(
            id=schedule_id,
            name=name,
            description=f"Cron task: {name} ({cron})",
            schedule_type=ScheduleType.CRON,
            schedule_config={"cron": cron},
            task_func=task_func,
            priority=priority,
            next_run=next_run,
            max_runs=max_runs,
            metadata=metadata or {}
        )
        
        self._schedules[schedule_id] = schedule
        return schedule_id
    
    def unschedule(self, schedule_id: str) -> bool:
        """Remove a scheduled task."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False
    
    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a scheduled task."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = True
            return True
        return False
    
    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a scheduled task."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = False
            return True
        return False
    
    def list_schedules(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """List all scheduled tasks."""
        schedules = list(self._schedules.values())
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        return schedules
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()
            
            # Check for tasks to run
            for schedule in list(self._schedules.values()):
                if not schedule.enabled:
                    continue
                
                if schedule.max_runs and schedule.run_count >= schedule.max_runs:
                    continue
                
                if schedule.next_run and schedule.next_run <= now:
                    # Execute task
                    asyncio.create_task(self._execute_scheduled(schedule))
                    
                    # Update schedule
                    schedule.last_run = now
                    schedule.run_count += 1
                    
                    # Calculate next run
                    if schedule.schedule_type == ScheduleType.ONCE:
                        schedule.enabled = False
                    elif schedule.schedule_type == ScheduleType.INTERVAL:
                        interval = schedule.schedule_config["interval_seconds"]
                        schedule.next_run = now + timedelta(seconds=interval)
                    elif schedule.schedule_type == ScheduleType.CRON:
                        cron = schedule.schedule_config["cron"]
                        itr = croniter.croniter(cron, now)
                        schedule.next_run = itr.get_next(datetime)
            
            await asyncio.sleep(self._check_interval)
    
    async def _execute_scheduled(self, schedule: ScheduledTask):
        """Execute a scheduled task."""
        try:
            if asyncio.iscoroutinefunction(schedule.task_func):
                await schedule.task_func()
            else:
                schedule.task_func()
        except Exception as e:
            # Log error but don't stop scheduler
            print(f"Scheduled task {schedule.name} failed: {e}")