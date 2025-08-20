"""
Scheduling Module for Deep Tree Echo (Echo Level)

This module represents the temporal dimension at the echo/subconscious level of the DTE architecture.
It manages schedules, tasks, events, and time-related organization for workspaces.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class WorkspaceScheduling:
    """Manages temporal organization of schedules, tasks, and events."""
    
    def __init__(self):
        """Initialize the scheduling system."""
        self.schedules = {}  # schedule_id -> schedule_dict
        self.tasks = {}  # task_id -> task_dict
        self.events = {}  # event_id -> event_dict
        
        # Relationship mappings
        self.schedule_tasks = defaultdict(list)  # schedule_id -> list of task_ids
        self.task_dependencies = defaultdict(list)  # task_id -> list of prerequisite_task_ids
        self.task_dependents = defaultdict(list)  # task_id -> list of dependent_task_ids
        
        # Classification mappings
        self.schedule_types = defaultdict(list)  # type -> list of schedule_ids
        self.task_types = defaultdict(list)  # type -> list of task_ids
        self.event_types = defaultdict(list)  # type -> list of event_ids
        
        # Temporal tracking
        self.timeline = []  # ordered list of (timestamp, entity_type, entity_id, action)
        self.active_tasks = []  # list of currently active task_ids
        self.completed_tasks = []  # list of completed task_ids
        
        # Progress tracking
        self.task_progress = {}  # task_id -> progress (0.0 to 1.0)
        self.schedule_progress = {}  # schedule_id -> progress (0.0 to 1.0)
        
    def create_schedule(self, name: str, schedule_type: str = "generic",
                       start_time: datetime = None,
                       end_time: datetime = None, 
                       attributes: Dict[str, Any] = None) -> str:
        """Create a new schedule.
        
        Args:
            name: Name of the schedule
            schedule_type: Type of schedule (recurring, one-time, project, etc.)
            start_time: Optional start time for the schedule
            end_time: Optional end time for the schedule
            attributes: Additional attributes for the schedule
            
        Returns:
            ID of the created schedule
        """
        schedule_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        # Set default times if not provided
        if not start_time:
            start_time = created_at
        if not end_time and schedule_type != "recurring":
            # Default to 30 days for non-recurring schedules
            end_time = created_at + timedelta(days=30)
            
        self.schedules[schedule_id] = {
            "id": schedule_id,
            "name": name,
            "type": schedule_type,
            "start_time": start_time,
            "end_time": end_time,
            "created_at": created_at,
            "updated_at": created_at,
            "status": "active"
        }
        
        # Add to type classification
        self.schedule_types[schedule_type].append(schedule_id)
        
        # Store attributes
        if attributes:
            self.schedules[schedule_id]["attributes"] = attributes
            
        # Add to timeline
        self.timeline.append((created_at, "schedule", schedule_id, "created"))
        
        logger.info(f"Created schedule '{name}' of type '{schedule_type}' with ID {schedule_id}")
        return schedule_id
        
    def create_task(self, name: str, schedule_id: str, 
                  task_type: str = "generic",
                  start_time: datetime = None,
                  duration: int = None,  # in minutes
                  due_time: datetime = None,
                  recurrence: str = None,
                  dependencies: List[str] = None,
                  attributes: Dict[str, Any] = None) -> str:
        """Create a new task within a schedule.
        
        Args:
            name: Name of the task
            schedule_id: ID of the parent schedule
            task_type: Type of task (action, milestone, etc.)
            start_time: Optional start time for the task
            duration: Optional duration in minutes
            due_time: Optional due time for the task
            recurrence: Optional recurrence pattern (daily, weekly, etc.)
            dependencies: Optional list of prerequisite task names
            attributes: Additional attributes for the task
            
        Returns:
            ID of the created task
        """
        if schedule_id not in self.schedules:
            logger.error(f"Cannot create task: schedule {schedule_id} not found")
            return None
            
        task_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        # Set default times if not provided
        if not start_time:
            start_time = created_at
        
        if not due_time and duration:
            due_time = start_time + timedelta(minutes=duration)
            
        self.tasks[task_id] = {
            "id": task_id,
            "name": name,
            "schedule_id": schedule_id,
            "type": task_type,
            "start_time": start_time,
            "duration": duration,
            "due_time": due_time,
            "recurrence": recurrence,
            "created_at": created_at,
            "updated_at": created_at,
            "status": "pending"
        }
        
        # Add to parent schedule
        self.schedule_tasks[schedule_id].append(task_id)
        
        # Add to type classification
        self.task_types[task_type].append(task_id)
        
        # Store attributes
        if attributes:
            self.tasks[task_id]["attributes"] = attributes
            
        # Set up dependencies if provided
        if dependencies:
            # Convert task names to IDs
            for dep_name in dependencies:
                for other_task_id, task in self.tasks.items():
                    if task["name"] == dep_name and task["schedule_id"] == schedule_id:
                        self.task_dependencies[task_id].append(other_task_id)
                        self.task_dependents[other_task_id].append(task_id)
                        break
                        
        # Initialize progress
        self.task_progress[task_id] = 0.0
        
        # Add to timeline
        self.timeline.append((created_at, "task", task_id, "created"))
        
        # Update schedule's progress
        self._update_schedule_progress(schedule_id)
        
        logger.info(f"Created task '{name}' in schedule '{self.schedules[schedule_id]['name']}'")
        return task_id
        
    def create_event(self, name: str, event_time: datetime,
                   event_type: str = "generic",
                   duration: int = None,  # in minutes
                   related_task_id: str = None,
                   attributes: Dict[str, Any] = None) -> str:
        """Create a new event.
        
        Args:
            name: Name of the event
            event_time: When the event occurs
            event_type: Type of event (milestone, deadline, etc.)
            duration: Optional duration in minutes
            related_task_id: Optional related task ID
            attributes: Additional attributes for the event
            
        Returns:
            ID of the created event
        """
        event_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        self.events[event_id] = {
            "id": event_id,
            "name": name,
            "type": event_type,
            "event_time": event_time,
            "duration": duration,
            "related_task_id": related_task_id,
            "created_at": created_at,
            "status": "pending"
        }
        
        # Add to type classification
        self.event_types[event_type].append(event_id)
        
        # Store attributes
        if attributes:
            self.events[event_id]["attributes"] = attributes
            
        # Add to timeline
        self.timeline.append((event_time, "event", event_id, "scheduled"))
        
        logger.info(f"Created event '{name}' of type '{event_type}' at {event_time}")
        return event_id
        
    def update_task(self, task_id: str, name: str = None,
                  start_time: datetime = None,
                  duration: int = None,
                  due_time: datetime = None,
                  status: str = None,
                  attributes: Dict[str, Any] = None) -> bool:
        """Update an existing task."""
        if task_id not in self.tasks:
            logger.error(f"Cannot update task: {task_id} not found")
            return False
            
        task = self.tasks[task_id]
        
        if name is not None:
            task["name"] = name
            
        if start_time is not None:
            task["start_time"] = start_time
            
        if duration is not None:
            task["duration"] = duration
            # Update due time if duration changes
            if task.get("start_time"):
                task["due_time"] = task["start_time"] + timedelta(minutes=duration)
                
        if due_time is not None:
            task["due_time"] = due_time
            
        if status is not None:
            old_status = task["status"]
            task["status"] = status
            
            # Handle status transitions
            if status == "active" and old_status != "active":
                if task_id not in self.active_tasks:
                    self.active_tasks.append(task_id)
                self.timeline.append((datetime.now(), "task", task_id, "started"))
                
            elif status == "completed" and old_status != "completed":
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)
                if task_id not in self.completed_tasks:
                    self.completed_tasks.append(task_id)
                self.task_progress[task_id] = 1.0
                self.timeline.append((datetime.now(), "task", task_id, "completed"))
                
                # Update dependent tasks
                for dependent_id in self.task_dependents.get(task_id, []):
                    self._check_task_dependencies(dependent_id)
                    
                # Update schedule progress
                self._update_schedule_progress(task["schedule_id"])
                
        if attributes is not None:
            task.setdefault("attributes", {}).update(attributes)
            
        task["updated_at"] = datetime.now()
        
        logger.info(f"Updated task '{task['name']}' ({task_id})")
        return True
        
    def update_schedule(self, schedule_id: str, name: str = None,
                       start_time: datetime = None,
                       end_time: datetime = None,
                       status: str = None,
                       attributes: Dict[str, Any] = None) -> bool:
        """Update an existing schedule."""
        if schedule_id not in self.schedules:
            logger.error(f"Cannot update schedule: {schedule_id} not found")
            return False
            
        schedule = self.schedules[schedule_id]
        
        if name is not None:
            schedule["name"] = name
            
        if start_time is not None:
            schedule["start_time"] = start_time
            
        if end_time is not None:
            schedule["end_time"] = end_time
            
        if status is not None:
            old_status = schedule["status"]
            schedule["status"] = status
            
            # Handle status transitions
            if status == "completed" and old_status != "completed":
                self.timeline.append((datetime.now(), "schedule", schedule_id, "completed"))
                
                # Mark all remaining tasks as completed
                for task_id in self.schedule_tasks.get(schedule_id, []):
                    if self.tasks[task_id]["status"] != "completed":
                        self.update_task(task_id, status="completed")
                        
        if attributes is not None:
            schedule.setdefault("attributes", {}).update(attributes)
            
        schedule["updated_at"] = datetime.now()
        
        logger.info(f"Updated schedule '{schedule['name']}' ({schedule_id})")
        return True
        
    def set_task_progress(self, task_id: str, progress: float) -> bool:
        """Set the progress level of a task (0.0 to 1.0)."""
        if task_id not in self.tasks:
            return False
            
        # Clamp progress between 0 and 1
        progress = max(0.0, min(1.0, progress))
        
        # Record previous progress for logging
        previous = self.task_progress.get(task_id, 0.0)
        
        # Update progress
        self.task_progress[task_id] = progress
        
        # Update task status if completed
        if progress >= 1.0 and self.tasks[task_id]["status"] != "completed":
            self.update_task(task_id, status="completed")
        elif progress > 0.0 and self.tasks[task_id]["status"] == "pending":
            self.update_task(task_id, status="active")
            
        logger.info(f"Updated task '{self.tasks[task_id]['name']}' progress: {previous:.2f} -> {progress:.2f}")
        
        # Update the schedule's progress
        schedule_id = self.tasks[task_id]["schedule_id"]
        self._update_schedule_progress(schedule_id)
        
        return True
        
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get a task by ID."""
        if task_id not in self.tasks:
            return None
            
        task = dict(self.tasks[task_id])
        task["progress"] = self.task_progress.get(task_id, 0.0)
        
        # Add dependency information
        task["dependencies"] = list(self.task_dependencies.get(task_id, []))
        task["dependents"] = list(self.task_dependents.get(task_id, []))
        
        return task
        
    def get_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Get a schedule by ID."""
        if schedule_id not in self.schedules:
            return None
            
        schedule = dict(self.schedules[schedule_id])
        schedule["progress"] = self.schedule_progress.get(schedule_id, 0.0)
        schedule["tasks"] = list(self.schedule_tasks.get(schedule_id, []))
        
        # Calculate task statistics
        total_tasks = len(schedule["tasks"])
        completed_tasks = sum(1 for t_id in schedule["tasks"] 
                             if self.tasks[t_id]["status"] == "completed")
        active_tasks = sum(1 for t_id in schedule["tasks"] 
                          if self.tasks[t_id]["status"] == "active")
        
        schedule["task_stats"] = {
            "total": total_tasks,
            "completed": completed_tasks,
            "active": active_tasks,
            "pending": total_tasks - completed_tasks - active_tasks
        }
        
        return schedule
        
    def get_upcoming_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events sorted by time."""
        now = datetime.now()
        upcoming = [
            event for event in self.events.values()
            if event["event_time"] >= now and event["status"] != "cancelled"
        ]
        
        # Sort by time (nearest first)
        upcoming.sort(key=lambda x: x["event_time"])
        
        if limit:
            upcoming = upcoming[:limit]
            
        return upcoming
        
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all currently active tasks."""
        return [self.get_task(task_id) for task_id in self.active_tasks]
        
    def get_timeline_events(self, start_time: datetime = None, 
                          end_time: datetime = None,
                          limit: int = None) -> List[Dict[str, Any]]:
        """Get timeline events within a time range."""
        if not start_time:
            start_time = datetime.now() - timedelta(days=7)  # Default to last week
        if not end_time:
            end_time = datetime.now() + timedelta(days=30)  # Default to next month
            
        # Filter timeline events by time range
        filtered_events = [
            entry for entry in self.timeline
            if start_time <= entry[0] <= end_time
        ]
        
        # Sort by time (oldest first)
        filtered_events.sort(key=lambda x: x[0])
        
        if limit:
            filtered_events = filtered_events[:limit]
            
        # Convert to readable format
        result = []
        for timestamp, entity_type, entity_id, action in filtered_events:
            entity_name = ""
            if entity_type == "task" and entity_id in self.tasks:
                entity_name = self.tasks[entity_id]["name"]
            elif entity_type == "schedule" and entity_id in self.schedules:
                entity_name = self.schedules[entity_id]["name"]
            elif entity_type == "event" and entity_id in self.events:
                entity_name = self.events[entity_id]["name"]
                
            result.append({
                "timestamp": timestamp,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "action": action
            })
            
        return result
        
    def get_scheduling_state(self) -> Dict[str, Any]:
        """Get the current state of the scheduling system."""
        now = datetime.now()
        
        # Calculate statistics
        active_schedules = sum(1 for s in self.schedules.values() if s["status"] == "active")
        completed_schedules = sum(1 for s in self.schedules.values() if s["status"] == "completed")
        
        active_task_count = len(self.active_tasks)
        completed_task_count = len(self.completed_tasks)
        total_task_count = len(self.tasks)
        
        upcoming_events = len([
            e for e in self.events.values()
            if e["event_time"] > now and e["status"] != "cancelled"
        ])
        
        # Find overdue tasks
        overdue_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task.get("due_time") and task["due_time"] < now 
            and task["status"] != "completed"
        ]
        
        state = {
            "schedule_count": len(self.schedules),
            "active_schedules": active_schedules,
            "completed_schedules": completed_schedules,
            "task_count": total_task_count,
            "active_tasks": active_task_count,
            "completed_tasks": completed_task_count,
            "event_count": len(self.events),
            "upcoming_events": upcoming_events,
            "overdue_tasks": len(overdue_tasks),
            "timeline_entries": len(self.timeline),
            "schedule_types": {
                type_name: len(schedules) 
                for type_name, schedules in self.schedule_types.items()
            },
            "task_types": {
                type_name: len(tasks) 
                for type_name, tasks in self.task_types.items()
            }
        }
        return state
        
    def _check_task_dependencies(self, task_id: str):
        """Check if all dependencies for a task are completed."""
        if task_id not in self.tasks:
            return
            
        # Skip if task is already active or completed
        if self.tasks[task_id]["status"] in ["active", "completed"]:
            return
            
        # Get all dependencies
        dependencies = self.task_dependencies.get(task_id, [])
        if not dependencies:
            # No dependencies, can be started
            self.update_task(task_id, status="active")
            return
            
        # Check if all dependencies are completed
        all_completed = all(
            self.tasks.get(dep_id, {}).get("status") == "completed"
            for dep_id in dependencies
        )
        
        if all_completed:
            # All dependencies completed, update task to active
            self.update_task(task_id, status="active")
            
    def _update_schedule_progress(self, schedule_id: str):
        """Update a schedule's progress based on its tasks."""
        if schedule_id not in self.schedules:
            return
            
        tasks = self.schedule_tasks.get(schedule_id, [])
        if not tasks:
            self.schedule_progress[schedule_id] = 0.0
            return
            
        # Calculate progress as the average of all task progresses
        total_progress = sum(self.task_progress.get(task_id, 0.0) for task_id in tasks)
        average_progress = total_progress / len(tasks)
        
        self.schedule_progress[schedule_id] = average_progress
        
        # Update schedule status if all tasks are completed
        if average_progress >= 1.0 and self.schedules[schedule_id]["status"] != "completed":
            self.update_schedule(schedule_id, status="completed")


# Create a singleton instance
workspace_scheduling = WorkspaceScheduling()

def get_scheduling() -> WorkspaceScheduling:
    """Get the workspace scheduling singleton."""
    return workspace_scheduling