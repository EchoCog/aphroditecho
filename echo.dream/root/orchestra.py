"""
Orchestra Module for Deep Tree Echo (Root Level)

This module represents the temporal dimension at the root/unconscious level of the DTE architecture.
It coordinates timing, process synchronization, and event handling.
"""

import logging
import threading
import time
import queue
import uuid
from typing import Dict, List, Callable, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class SystemOrchestra:
    """Manages system-wide timing and process coordination."""
    
    def __init__(self):
        """Initialize the orchestra system."""
        self.running = False
        self.heartbeat_interval = 1.0  # seconds
        self.heartbeat_thread = None
        self.last_heartbeat = None
        
        # Event queues for different priority levels
        self.high_priority_queue = queue.PriorityQueue()
        self.normal_priority_queue = queue.PriorityQueue()
        self.low_priority_queue = queue.PriorityQueue()
        
        # Scheduled events with timestamps
        self.scheduled_events = {}  # event_id -> (timestamp, callback, args, kwargs)
        
        # Registered callbacks
        self.callbacks = {}  # callback_name -> callback_function
        
        # Event history
        self.event_history = []
        self.max_history_size = 1000
        
        # Process registry
        self.processes = {}  # process_id -> process_info
        
        # Synchronization points
        self.sync_points = {}  # sync_id -> (expected_count, current_count, callback)
        self.sync_locks = {}  # sync_id -> threading.Event
        
    def start(self):
        """Start the orchestra system."""
        if self.running:
            return
        
        self.running = True
        self.last_heartbeat = datetime.now()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        logger.info("Orchestra system started")
        
    def stop(self):
        """Stop the orchestra system."""
        if not self.running:
            return
        
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5.0)
            self.heartbeat_thread = None
            
        logger.info("Orchestra system stopped")
        
    def register_callback(self, callback_name: str, callback: Callable) -> bool:
        """Register a named callback function."""
        if callback_name in self.callbacks:
            logger.warning(f"Callback '{callback_name}' already registered, replacing")
            
        self.callbacks[callback_name] = callback
        logger.info(f"Registered callback '{callback_name}'")
        return True
        
    def unregister_callback(self, callback_name: str) -> bool:
        """Unregister a named callback function."""
        if callback_name not in self.callbacks:
            return False
            
        del self.callbacks[callback_name]
        logger.info(f"Unregistered callback '{callback_name}'")
        return True
        
    def schedule_event(self, timestamp: datetime, callback_name: str, 
                      priority: int = 1, *args, **kwargs) -> str:
        """Schedule an event to occur at a specific time."""
        if callback_name not in self.callbacks:
            logger.error(f"Cannot schedule event: callback '{callback_name}' not registered")
            return None
            
        event_id = str(uuid.uuid4())
        self.scheduled_events[event_id] = (timestamp, callback_name, args, kwargs)
        
        # Calculate the delay in seconds
        delay = (timestamp - datetime.now()).total_seconds()
        if delay < 0:
            delay = 0
            
        # Add to appropriate queue based on priority
        queue_item = (timestamp, event_id)
        if priority == 0:  # High priority
            self.high_priority_queue.put(queue_item)
        elif priority == 1:  # Normal priority
            self.normal_priority_queue.put(queue_item)
        else:  # Low priority
            self.low_priority_queue.put(queue_item)
            
        logger.info(f"Scheduled event {event_id} with callback '{callback_name}' at {timestamp}")
        return event_id
        
    def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event."""
        if event_id not in self.scheduled_events:
            return False
            
        del self.scheduled_events[event_id]
        logger.info(f"Cancelled event {event_id}")
        return True
        
    def trigger_callback(self, callback_name: str, *args, **kwargs) -> Any:
        """Immediately trigger a registered callback."""
        if callback_name not in self.callbacks:
            logger.error(f"Cannot trigger callback: '{callback_name}' not registered")
            return None
            
        try:
            result = self.callbacks[callback_name](*args, **kwargs)
            self._record_event(callback_name, args, kwargs, result)
            return result
        except Exception as e:
            logger.exception(f"Error executing callback '{callback_name}': {str(e)}")
            return None
            
    def register_process(self, process_name: str, process_type: str = "generic", 
                        initial_state: Dict[str, Any] = None) -> str:
        """Register a process with the orchestra."""
        process_id = str(uuid.uuid4())
        self.processes[process_id] = {
            "id": process_id,
            "name": process_name,
            "type": process_type,
            "state": initial_state or {},
            "registered_at": datetime.now(),
            "last_updated": datetime.now(),
            "active": True
        }
        
        logger.info(f"Registered process '{process_name}' with ID {process_id}")
        return process_id
        
    def update_process_state(self, process_id: str, state: Dict[str, Any]) -> bool:
        """Update the state of a registered process."""
        if process_id not in self.processes:
            logger.error(f"Cannot update process state: process {process_id} not registered")
            return False
            
        self.processes[process_id]["state"].update(state)
        self.processes[process_id]["last_updated"] = datetime.now()
        return True
        
    def deregister_process(self, process_id: str) -> bool:
        """Deregister a process."""
        if process_id not in self.processes:
            return False
            
        process_name = self.processes[process_id]["name"]
        del self.processes[process_id]
        logger.info(f"Deregistered process '{process_name}' with ID {process_id}")
        return True
        
    def create_sync_point(self, name: str, expected_count: int, 
                         callback_name: str = None) -> str:
        """Create a synchronization point for coordinating multiple processes."""
        sync_id = str(uuid.uuid4())
        self.sync_points[sync_id] = {
            "id": sync_id,
            "name": name,
            "expected_count": expected_count,
            "current_count": 0,
            "callback_name": callback_name,
            "created_at": datetime.now(),
            "completed": False
        }
        
        self.sync_locks[sync_id] = threading.Event()
        logger.info(f"Created sync point '{name}' with ID {sync_id}, expecting {expected_count} signals")
        return sync_id
        
    def signal_sync_point(self, sync_id: str, data: Any = None) -> bool:
        """Signal arrival at a synchronization point."""
        if sync_id not in self.sync_points:
            logger.error(f"Cannot signal sync point: {sync_id} not found")
            return False
            
        sync_point = self.sync_points[sync_id]
        if sync_point["completed"]:
            logger.warning(f"Sync point {sync_id} already completed")
            return False
            
        sync_point["current_count"] += 1
        
        # Store signal data if provided
        if data is not None:
            if "signal_data" not in sync_point:
                sync_point["signal_data"] = []
            sync_point["signal_data"].append(data)
            
        logger.info(f"Signaled sync point '{sync_point['name']}' ({sync_point['current_count']}/{sync_point['expected_count']})")
        
        # Check if all expected signals have arrived
        if sync_point["current_count"] >= sync_point["expected_count"]:
            sync_point["completed"] = True
            sync_point["completed_at"] = datetime.now()
            
            # Set the event to release any waiting threads
            self.sync_locks[sync_id].set()
            
            # Trigger callback if specified
            if sync_point["callback_name"]:
                signal_data = sync_point.get("signal_data", [])
                self.trigger_callback(sync_point["callback_name"], sync_id, signal_data)
                
            logger.info(f"Sync point '{sync_point['name']}' completed")
            
        return True
        
    def wait_for_sync_point(self, sync_id: str, timeout: float = None) -> bool:
        """Wait for a sync point to be completed."""
        if sync_id not in self.sync_points:
            logger.error(f"Cannot wait for sync point: {sync_id} not found")
            return False
            
        if self.sync_points[sync_id]["completed"]:
            return True
            
        # Wait for the event to be set
        return self.sync_locks[sync_id].wait(timeout=timeout)
        
    def get_process_info(self, process_id: str = None) -> Dict[str, Any]:
        """Get information about registered processes."""
        if process_id:
            return self.processes.get(process_id)
        return dict(self.processes)
        
    def get_sync_point_info(self, sync_id: str = None) -> Dict[str, Any]:
        """Get information about sync points."""
        if sync_id:
            return self.sync_points.get(sync_id)
        return dict(self.sync_points)
        
    def get_orchestra_state(self) -> Dict[str, Any]:
        """Get the current state of the orchestra system."""
        state = {
            "running": self.running,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "scheduled_events_count": len(self.scheduled_events),
            "processes_count": len(self.processes),
            "high_priority_queue_size": self.high_priority_queue.qsize(),
            "normal_priority_queue_size": self.normal_priority_queue.qsize(),
            "low_priority_queue_size": self.low_priority_queue.qsize(),
            "registered_callbacks": list(self.callbacks.keys()),
            "sync_points": {name: {
                "expected": info["expected_count"],
                "current": info["current_count"],
                "completed": info["completed"]
            } for name, info in self.sync_points.items()},
            "recent_events": self.event_history[-10:] if self.event_history else []
        }
        return state
        
    def _heartbeat_loop(self):
        """Main heartbeat loop that processes scheduled events."""
        while self.running:
            self.last_heartbeat = datetime.now()
            
            # Process due events from queues in priority order
            self._process_due_events(self.high_priority_queue)
            self._process_due_events(self.normal_priority_queue)
            self._process_due_events(self.low_priority_queue)
            
            # Sleep until next heartbeat
            time.sleep(self.heartbeat_interval)
            
    def _process_due_events(self, event_queue):
        """Process all due events from a queue."""
        now = datetime.now()
        
        # Check if there are events due for execution
        while not event_queue.empty():
            # Peek at the next event
            timestamp, event_id = event_queue.queue[0]
            
            # If the event is due, process it
            if timestamp <= now:
                # Remove from queue
                event_queue.get()
                
                # Check if the event still exists (wasn't cancelled)
                if event_id in self.scheduled_events:
                    timestamp, callback_name, args, kwargs = self.scheduled_events[event_id]
                    
                    # Remove from scheduled events
                    del self.scheduled_events[event_id]
                    
                    # Execute the callback
                    try:
                        if callback_name in self.callbacks:
                            result = self.callbacks[callback_name](*args, **kwargs)
                            self._record_event(callback_name, args, kwargs, result)
                        else:
                            logger.warning(f"Callback '{callback_name}' for event {event_id} not found")
                    except Exception as e:
                        logger.exception(f"Error executing event {event_id} with callback '{callback_name}': {str(e)}")
            else:
                # No more due events in this queue
                break
                
    def _record_event(self, callback_name, args, kwargs, result):
        """Record an event in the history."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "callback": callback_name,
            "args": str(args) if args else None,
            "kwargs": str(kwargs) if kwargs else None,
            "result": str(result) if result is not None else None
        }
        
        self.event_history.append(event)
        
        # Trim history if it gets too long
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]


# Create a singleton instance
system_orchestra = SystemOrchestra()

def get_orchestra() -> SystemOrchestra:
    """Get the system orchestra singleton."""
    return system_orchestra