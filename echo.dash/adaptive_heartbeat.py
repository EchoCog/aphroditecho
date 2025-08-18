#!/usr/bin/env python3

import os
import sys
import time
import threading
import logging
import signal
import json
from datetime import datetime
import psutil
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='adaptive_heartbeat.log',
    filemode='a'
)
logger = logging.getLogger('adaptive_heartbeat')

class AdaptiveHeartbeat:
    """
    Manages the heartbeat rate of DeepTreeEcho based on activity levels.
    Includes hyper drive defense mode for responding to potential attacks.
    """
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of AdaptiveHeartbeat"""
        if cls._instance is None:
            cls._instance = AdaptiveHeartbeat()
        return cls._instance
    
    def __init__(self, 
                min_interval=60.0,   # Minimum heartbeat interval in seconds (slow)
                max_interval=1.0,    # Maximum heartbeat interval in seconds (fast)
                hyper_drive_interval=0.1,  # Hyper drive mode heartbeat interval
                activity_threshold_low=2,  # Below this number of events, slow down
                activity_threshold_high=10,  # Above this number of events, speed up
                cpu_threshold=80.0,  # CPU usage percentage threshold for throttling
                activity_logs_dir="activity_logs"):
        
        # If an instance already exists, use that one
        if AdaptiveHeartbeat._instance is not None:
            return
            
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.hyper_drive_interval = hyper_drive_interval
        self.activity_threshold_low = activity_threshold_low
        self.activity_threshold_high = activity_threshold_high
        self.cpu_threshold = cpu_threshold
        self.activity_logs_dir = Path(activity_logs_dir)
        
        self.current_interval = (min_interval + max_interval) / 2  # Start at middle rate
        self.is_running = False
        self.is_hyper_drive_active = False
        self.hyper_drive_start_time = None
        self.max_hyper_drive_duration = 60  # Maximum seconds in hyper drive mode
        
        self.lock = threading.Lock()
        self.heartbeat_thread = None
        self.defense_thread = None
        
        # Initialize stats
        self.stats = {
            "heartbeats": 0,
            "hyper_drive_activations": 0,
            "last_heartbeat": None,
            "current_mode": "NORMAL",
            "current_interval": self.current_interval,
            "active_events": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0
        }
        
        # Event log list
        self.event_log = []
        self.active_events = []
        
        # Set this instance as the singleton
        AdaptiveHeartbeat._instance = self
        
        # Ensure activity logs directory exists
        if not self.activity_logs_dir.exists():
            self.activity_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create heartbeat log directory
        self.heartbeat_log_dir = self.activity_logs_dir / "heartbeat"
        if not self.heartbeat_log_dir.exists():
            self.heartbeat_log_dir.mkdir(parents=True, exist_ok=True)
            
        # Initialize activity log
        self.activity_log_file = self.heartbeat_log_dir / "activity.json"
        if not self.activity_log_file.exists():
            with open(self.activity_log_file, 'w') as f:
                json.dump([], f)
    
    def start(self):
        """Start the adaptive heartbeat system"""
        if self.is_running:
            logger.warning("Heartbeat system is already running")
            return
        
        self.is_running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        self.defense_thread = threading.Thread(target=self._defense_monitor, daemon=True)
        self.defense_thread.start()
        
        logger.info(f"Adaptive heartbeat system started with interval range: "
                   f"{self.max_interval}s to {self.min_interval}s")
        
        # Log this activity
        self._log_activity("Heartbeat system started", "startup")
    
    def stop(self):
        """Stop the adaptive heartbeat system"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
        
        if self.defense_thread:
            self.defense_thread.join(timeout=2.0)
            
        logger.info("Heartbeat system stopped")
        
        # Log this activity
        self._log_activity("Heartbeat system stopped", "shutdown")
    
    def _heartbeat_loop(self):
        """Main heartbeat loop that pulses at the current interval rate"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # Perform heartbeat actions
                self._heartbeat()
                
                # Update system stats
                self._update_system_stats()
                
                # Adjust heartbeat rate based on activity if not in hyper drive
                if not self.is_hyper_drive_active:
                    self._adjust_heartbeat_rate()
                    
                # Check if we should exit hyper drive mode
                if self.is_hyper_drive_active:
                    elapsed = time.time() - self.hyper_drive_start_time
                    if elapsed > self.max_hyper_drive_duration:
                        self._exit_hyper_drive()
                
                # Sleep until next heartbeat
                interval = self._get_current_interval()
                sleep_time = max(0.1, interval - (time.time() - current_time))
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
                time.sleep(1.0)  # Prevent tight error loops
    
    def _defense_monitor(self):
        """Monitors system for potential attacks and triggers hyper drive when needed"""
        consecutive_high_cpu = 0
        check_interval = 1.0  # Check every second
        cpu_alert_threshold = 90.0  # CPU usage that might indicate an attack
        consecutive_threshold = 3  # Number of consecutive high readings to trigger alert
        
        while self.is_running:
            try:
                # Get current CPU usage across all cores
                cpu_usage = psutil.cpu_percent(interval=None)
                
                # Check for suspicious process activity
                suspicious_activity = self._check_suspicious_processes()
                
                # Count consecutive high CPU usage
                if cpu_usage > cpu_alert_threshold or suspicious_activity:
                    consecutive_high_cpu += 1
                else:
                    consecutive_high_cpu = 0
                
                # Trigger hyper drive mode if sustained high CPU or suspicious activity
                if consecutive_high_cpu >= consecutive_threshold and not self.is_hyper_drive_active:
                    trigger_reason = "High CPU" if cpu_usage > cpu_alert_threshold else "Suspicious processes"
                    self._enter_hyper_drive(trigger_reason)
                
                time.sleep(check_interval)
                    
            except Exception as e:
                logger.error(f"Error in defense monitor: {e}", exc_info=True)
                time.sleep(1.0)
    
    def _heartbeat(self):
        """Perform a single heartbeat pulse"""
        with self.lock:
            self.stats["heartbeats"] += 1
            self.stats["last_heartbeat"] = time.time()
            
        # Signal heartbeat to any listeners
        self._signal_heartbeat()
    
    def _signal_heartbeat(self):
        """Send heartbeat signal to the DeepTreeEcho system"""
        # This could write to a shared memory or file that DeepTreeEcho monitors
        heartbeat_file = self.heartbeat_log_dir / "last_heartbeat"
        try:
            with open(heartbeat_file, 'w') as f:
                f.write(f"{time.time()}")
        except Exception as e:
            logger.error(f"Error writing heartbeat signal: {e}")
    
    def _update_system_stats(self):
        """Update the current system statistics"""
        with self.lock:
            self.stats["cpu_usage"] = psutil.cpu_percent(interval=None)
            self.stats["memory_usage"] = psutil.virtual_memory().percent
            self.stats["current_interval"] = self.current_interval
            self.stats["active_events"] = self._count_active_events()
            
            # Write stats to file for dashboard to read
            try:
                with open(self.heartbeat_log_dir / "stats.json", 'w') as f:
                    json.dump(self.stats, f)
            except Exception as e:
                logger.error(f"Error writing stats: {e}")
    
    def _count_active_events(self):
        """Count the number of active events in the system"""
        active_count = 0
        recent_window = 60  # Consider events in the last minute as "active"
        
        try:
            # Read all activity logs
            for component_dir in self.activity_logs_dir.iterdir():
                if component_dir.is_dir():
                    activity_file = component_dir / "activity.json"
                    if activity_file.exists():
                        with open(activity_file) as f:
                            try:
                                activities = json.load(f)
                                # Count recent activities
                                now = time.time()
                                for activity in activities:
                                    if now - activity.get("time", 0) < recent_window:
                                        active_count += 1
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Error counting active events: {e}")
        
        return active_count
    
    def _adjust_heartbeat_rate(self):
        """Dynamically adjust heartbeat rate based on system activity"""
        active_events = self.stats["active_events"]
        cpu_usage = self.stats["cpu_usage"]
        
        with self.lock:
            # Baseline calculation based on activity level
            if active_events <= self.activity_threshold_low:
                # Low activity: slow down toward min_interval
                target_interval = self.min_interval
            elif active_events >= self.activity_threshold_high:
                # High activity: speed up toward max_interval
                target_interval = self.max_interval
            else:
                # Medium activity: scale proportionally
                activity_range = self.activity_threshold_high - self.activity_threshold_low
                position = (active_events - self.activity_threshold_low) / activity_range
                interval_range = self.min_interval - self.max_interval
                target_interval = self.min_interval - (position * interval_range)
            
            # Adjust target based on CPU load
            if cpu_usage > self.cpu_threshold:
                # Slow down if CPU is too high
                cpu_factor = min(2.0, 1.0 + (cpu_usage - self.cpu_threshold) / 50)
                target_interval *= cpu_factor
            
            # Smooth the transition (don't change too abruptly)
            self.current_interval = (0.8 * self.current_interval) + (0.2 * target_interval)
            self.current_interval = min(self.min_interval, max(self.max_interval, self.current_interval))
    
    def _get_current_interval(self):
        """Get the current heartbeat interval based on mode"""
        if self.is_hyper_drive_active:
            return self.hyper_drive_interval
        return self.current_interval
    
    def _enter_hyper_drive(self, reason="manual"):
        """Enter hyper drive mode to allocate maximum resources to handling a situation"""
        if self.is_hyper_drive_active:
            return
        
        with self.lock:
            self.is_hyper_drive_active = True
            self.hyper_drive_start_time = time.time()
            self.stats["current_mode"] = "HYPER DRIVE"
            self.stats["hyper_drive_activations"] += 1
        
        # Log the hyper drive activation
        logger.warning(f"ENTERING HYPER DRIVE MODE: {reason}")
        self._log_activity(f"Hyper Drive mode activated: {reason}", "defense", priority="high")
        
        # Optional: Could set process priority here
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, 'HIGH_PRIORITY_CLASS') else -10)
        except Exception as e:
            logger.error(f"Failed to set process priority: {e}")
    
    def _exit_hyper_drive(self):
        """Exit hyper drive mode and return to normal operation"""
        if not self.is_hyper_drive_active:
            return
            
        with self.lock:
            self.is_hyper_drive_active = False
            self.stats["current_mode"] = "NORMAL"
            elapsed = time.time() - self.hyper_drive_start_time
            self.hyper_drive_start_time = None
        
        # Log the exit from hyper drive
        logger.info(f"Exiting hyper drive mode after {elapsed:.1f} seconds")
        self._log_activity("Hyper Drive mode deactivated", "defense")
        
        # Optional: Reset process priority
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.NORMAL_PRIORITY_CLASS if hasattr(psutil, 'NORMAL_PRIORITY_CLASS') else 0)
        except Exception as e:
            logger.error(f"Failed to reset process priority: {e}")
    
    def _check_suspicious_processes(self):
        """Check for potentially suspicious processes"""
        suspicious_count = 0
        suspicious_names = ['stress', 'stress-ng', 'fork bomb', 'dd', 'cat /dev/zero']
        cpu_hog_threshold = 95.0  # CPU usage percentage to consider a process suspicious
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
            try:
                # Check process name against suspicious list
                if any(sus in proc.info['name'].lower() for sus in suspicious_names if proc.info['name']):
                    suspicious_count += 1
                    logger.warning(f"Suspicious process found: {proc.info['name']} (PID: {proc.info['pid']})")
                    continue
                
                # Check if process is using excessive CPU
                if proc.info['cpu_percent'] > cpu_hog_threshold:
                    # Get more info about this process
                    cmdline = ' '.join(proc.cmdline()) if hasattr(proc, 'cmdline') else 'Unknown'
                    logger.warning(f"High CPU process: {proc.info['name']} ({cmdline}) "
                                  f"CPU: {proc.info['cpu_percent']}% (PID: {proc.info['pid']})")
                    suspicious_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return suspicious_count > 0
    
    def _log_activity(self, description, category, priority="normal"):
        """Log activity to the activity log file"""
        activity = {
            "time": time.time(),
            "description": description,
            "category": category,
            "priority": priority
        }
        
        try:
            # Read existing activities
            activities = []
            if self.activity_log_file.exists():
                with open(self.activity_log_file) as f:
                    try:
                        activities = json.load(f)
                    except json.JSONDecodeError:
                        activities = []
            
            # Add new activity
            activities.append(activity)
            
            # Keep only recent activities (last 1000)
            activities = activities[-1000:]
            
            # Write back
            with open(self.activity_log_file, 'w') as f:
                json.dump(activities, f)
                
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def manual_trigger_hyper_drive(self, reason="manual trigger"):
        """Manually trigger hyper drive mode (for testing or external triggers)"""
        self._enter_hyper_drive(reason)

    # === Methods needed by the GUI dashboard ===
    
    def get_current_rate(self):
        """Get the current heartbeat rate in Hz"""
        interval = self._get_current_interval()
        if interval <= 0:
            return 0
        return 1.0 / interval
    
    def is_hyper_drive_active(self):
        """Check if hyper drive mode is currently active"""
        return self.is_hyper_drive_active
    
    def get_active_events(self):
        """Get list of currently active events"""
        # Get active events from the activity logs
        active_events = []
        recent_window = 60  # Consider events in the last minute as "active"
        
        try:
            # Read all activity logs
            for component_dir in self.activity_logs_dir.iterdir():
                if component_dir.is_dir():
                    activity_file = component_dir / "activity.json"
                    if activity_file.exists():
                        with open(activity_file) as f:
                            try:
                                activities = json.load(f)
                                # Get recent activities
                                now = time.time()
                                for activity in activities:
                                    if now - activity.get("time", 0) < recent_window:
                                        active_events.append(activity)
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Error getting active events: {e}")
        
        return active_events
    
    def get_system_metrics(self):
        """Get current system metrics including CPU and memory usage"""
        # Update metrics in real-time
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_usage": disk_usage,
            "heartbeats": self.stats["heartbeats"],
            "current_interval": self.stats["current_interval"]
        }
    
    def get_recent_log_entries(self, max_entries=10):
        """Get the most recent log entries (limited to max_entries)"""
        entries = []
        
        try:
            # Read existing activities
            if self.activity_log_file.exists():
                with open(self.activity_log_file) as f:
                    try:
                        activities = json.load(f)
                        # Format the recent entries
                        for activity in activities[-max_entries:]:
                            timestamp = datetime.fromtimestamp(activity.get("time", 0)).strftime("%H:%M:%S")
                            priority = activity.get("priority", "normal").upper()
                            category = activity.get("category", "system").upper()
                            description = activity.get("description", "")
                            
                            entry = f"[{timestamp}] [{priority}] [{category}] {description}"
                            entries.append(entry)
                    except json.JSONDecodeError:
                        entries.append("[ERROR] Could not parse activity log")
        except Exception as e:
            logger.error(f"Error getting recent log entries: {e}")
            entries.append(f"[ERROR] {str(e)}")
            
        return entries
    
    def activate_hyperdrive(self, reason="Manual activation from GUI"):
        """Manually activate hyper drive mode"""
        self._enter_hyper_drive(reason)
    
    def deactivate_hyperdrive(self):
        """Manually deactivate hyper drive mode"""
        self._exit_hyper_drive()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    if heartbeat_system:
        print("\nStopping heartbeat system...")
        heartbeat_system.stop()
    sys.exit(0)

# Global heartbeat system instance
heartbeat_system = None

def main():
    """Main function to run the adaptive heartbeat system"""
    global heartbeat_system
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("Starting Adaptive Heartbeat System for DeepTreeEcho...")
        
        # Create and start heartbeat system
        # Customize parameters based on requirements
        heartbeat_system = AdaptiveHeartbeat.get_instance()
        
        heartbeat_system.start()
        
        # Stay alive and periodically report status
        while True:
            if heartbeat_system.stats.get("current_mode") == "HYPER DRIVE":
                elapsed = time.time() - heartbeat_system.hyper_drive_start_time if heartbeat_system.hyper_drive_start_time else 0
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {heartbeat_system.stats['current_mode']} MODE "
                      f"({elapsed:.1f}s) - CPU: {heartbeat_system.stats['cpu_usage']:.1f}% - "
                      f"Events: {heartbeat_system.stats['active_events']} - "
                      f"Heartbeats: {heartbeat_system.stats['heartbeats']}", end="", flush=True)
            else:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Current Rate: "
                      f"{1.0/heartbeat_system.stats['current_interval']:.2f} Hz - "
                      f"CPU: {heartbeat_system.stats['cpu_usage']:.1f}% - "
                      f"Events: {heartbeat_system.stats['active_events']} - "
                      f"Heartbeats: {heartbeat_system.stats['heartbeats']}", end="", flush=True)
            
            time.sleep(1.0)
    
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())