import asyncio
import logging
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import heapq
from datetime import datetime, timedelta
import json
from pathlib import Path
import signal
import threading
from queue import PriorityQueue
import numpy as np
import psutil

class ActivityState(Enum):
    ACTIVE = "active"
    RESTING = "resting"
    DORMANT = "dormant"
    PROCESSING = "processing"
    WAITING = "waiting"

class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4

@dataclass(order=True)
class ScheduledTask:
    priority: TaskPriority
    scheduled_time: float
    task_id: str = field(compare=False)
    callback: Callable = field(compare=False)
    interval: Optional[float] = field(default=None, compare=False)
    condition: Optional[Callable[[], bool]] = field(default=None, compare=False)
    last_run: Optional[float] = field(default=None, compare=False)
    cpu_threshold: float = field(default=0.8, compare=False)
    memory_threshold: float = field(default=0.8, compare=False)

class ActivityRegulator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = ActivityState.ACTIVE
        self.task_queue = PriorityQueue()
        self.periodic_tasks: Dict[str, ScheduledTask] = {}
        self.event_tasks: Dict[str, ScheduledTask] = {}
        self.running = True
        
        # Activity cycle parameters
        self.cycle_duration = 60  # seconds
        self.last_cycle = time.time()
        
        # Setup activity logging
        self.activity_dir = Path('activity_logs')
        self.activity_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize component activity logs
        self.components = ['cognitive', 'sensory', 'ml', 'browser', 'terminal', 'personality', 'emergency']
        for component in self.components:
            component_dir = self.activity_dir / component
            component_dir.mkdir(parents=True, exist_ok=True)
            activity_file = component_dir / 'activity.json'
            if not activity_file.exists():
                with open(activity_file, 'w') as f:
                    json.dump([], f)
        
        # Start background monitoring
        self.monitor_thread = threading.Thread(target=self._monitor_activities, daemon=True)
        self.monitor_thread.start()
        
    def _monitor_activities(self):
        """Background thread to monitor and log system activities"""
        while self.running:
            try:
                current_time = time.time()
                
                # Log system state
                self._log_activity('cognitive', f"System state: {self.state.value}")
                
                # Log task queue status
                queue_size = self.task_queue.qsize()
                if queue_size > 0:
                    self._log_activity('cognitive', f"Task queue size: {queue_size}")
                
                # Log periodic task status
                for task_id, task in self.periodic_tasks.items():
                    if task.last_run:
                        time_since_last = current_time - task.last_run
                        if time_since_last > task.interval * 2:  # Task is delayed
                            self._log_activity('emergency', 
                                f"Task {task_id} delayed by {time_since_last:.1f}s")
                
                # Check system health
                cpu_usage = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                if cpu_usage > 80:
                    self._log_activity('emergency', f"High CPU usage: {cpu_usage}%")
                if memory.percent > 80:
                    self._log_activity('emergency', f"High memory usage: {memory.percent}%")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self._log_activity('emergency', f"Monitor error: {str(e)}")
                time.sleep(5)  # Back off on error
                
    def _log_activity(self, component: str, description: str, context: Dict = None):
        """Log an activity for a component"""
        try:
            activity_file = self.activity_dir / component / 'activity.json'
            
            # Read existing activities
            current = []
            if activity_file.exists():
                with open(activity_file) as f:
                    current = json.load(f)
            
            # Add new activity
            activity = {
                'time': time.time(),
                'description': description,
                'context': context or {}
            }
            current.append(activity)
            
            # Keep last 1000 activities
            if len(current) > 1000:
                current = current[-1000:]
            
            # Write back
            with open(activity_file, 'w') as f:
                json.dump(current, f)
                
        except Exception as e:
            self.logger.error(f"Error logging activity: {e}")
            
    def add_task(self, task_id: str, callback: Callable,
                priority: TaskPriority = TaskPriority.MEDIUM,
                interval: Optional[float] = None):
        """Add a new task to the system"""
        task = ScheduledTask(
            priority=priority,
            scheduled_time=time.time(),
            task_id=task_id,
            callback=callback,
            interval=interval
        )
        
        if interval:
            self.periodic_tasks[task_id] = task
            self._log_activity('cognitive', f"Added periodic task: {task_id}")
        else:
            self.event_tasks[task_id] = task
            self._log_activity('cognitive', f"Added event task: {task_id}")
            
        self.task_queue.put(task)
        
    def remove_task(self, task_id: str):
        """Remove a task from the system"""
        if task_id in self.periodic_tasks:
            del self.periodic_tasks[task_id]
            self._log_activity('cognitive', f"Removed periodic task: {task_id}")
        if task_id in self.event_tasks:
            del self.event_tasks[task_id]
            self._log_activity('cognitive', f"Removed event task: {task_id}")
            
    async def run(self):
        """Main activity regulation loop"""
        self._log_activity('cognitive', "Activity regulation started")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Process scheduled tasks
                while not self.task_queue.empty():
                    task = self.task_queue.get()
                    
                    if current_time >= task.scheduled_time:
                        try:
                            self._log_activity('cognitive', f"Executing task: {task.task_id}")
                            await task.callback()
                            task.last_run = current_time
                            
                            # Reschedule periodic task
                            if task.interval:
                                task.scheduled_time = current_time + task.interval
                                self.task_queue.put(task)
                                
                        except Exception as e:
                            self._log_activity('emergency', 
                                f"Task {task.task_id} failed: {str(e)}")
                    else:
                        # Put it back if it's not time yet
                        self.task_queue.put(task)
                        break
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self._log_activity('emergency', f"Activity regulation error: {str(e)}")
                await asyncio.sleep(1)
                
    def shutdown(self):
        """Shutdown the activity regulator"""
        self.running = False
        self._log_activity('cognitive', "Activity regulation shutting down")
