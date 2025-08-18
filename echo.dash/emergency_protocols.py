import logging
import time
import psutil
import threading
import requests
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import signal
import aiohttp

class EmergencyProtocols:
    def __init__(self, github_token: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO', 'dtecho/deep-tree-echo')
        
        # Use local directory
        self.emergency_path = Path('activity_logs/emergency')
        self.emergency_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize activity file
        self.activity_file = self.emergency_path / 'activity.json'
        if not self.activity_file.exists():
            with open(self.activity_file, 'w') as f:
                json.dump([], f)
                
        self.activities = []
        self._load_activities()
        
        # System health thresholds
        self.thresholds = {
            'cpu_critical': 95.0,  # CPU usage %
            'memory_critical': 95.0,  # Memory usage %
            'response_timeout': 300,  # seconds
            'error_count_threshold': 10,  # errors per minute
            'stuck_timeout': 600  # seconds without state change
        }
        
        # Initialize state
        self.last_activity = time.time()
        self.last_state_change = time.time()
        self.error_timestamps = []
        self.is_distressed = False
        self.emergency_mode = False
        
        # Create status file
        self.status_file = self.emergency_path / 'status.json'
        self._init_status_file()
        
    def _init_status_file(self):
        """Initialize or load status file"""
        if self.status_file.exists():
            with open(self.status_file) as f:
                self.status = json.load(f)
        else:
            self.status = {
                'last_update': time.time(),
                'state': 'initializing',
                'health': 100,
                'errors': [],
                'alerts': [],
                'last_distress': None
            }
            self._save_status()
            
    def _save_status(self):
        """Save current status to file"""
        self.status['last_update'] = time.time()
        with open(self.status_file, 'w') as f:
            json.dump(self.status, f, indent=2)
            
    async def monitor_health(self):
        """Monitor system health metrics"""
        while True:
            try:
                # Check CPU and memory
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                # Check for inactivity
                time_since_activity = time.time() - self.last_activity
                time_since_state_change = time.time() - self.last_state_change
                
                # Calculate health score
                health_score = 100
                health_score -= max(0, (cpu_percent - 80) * 2)
                health_score -= max(0, (memory_percent - 80) * 2)
                health_score -= max(0, (time_since_activity - 60) * 0.1)
                
                # Update status
                self.status['health'] = max(0, min(100, health_score))
                
                # Check for critical conditions
                if (cpu_percent > self.thresholds['cpu_critical'] or
                    memory_percent > self.thresholds['memory_critical'] or
                    time_since_activity > self.thresholds['response_timeout'] or
                    time_since_state_change > self.thresholds['stuck_timeout']):
                    await self.raise_distress(
                        f"Critical condition: CPU={cpu_percent}%, "
                        f"Memory={memory_percent}%, "
                        f"Inactive={time_since_activity}s"
                    )
                    
                # Clean old errors
                current_time = time.time()
                self.error_timestamps = [
                    t for t in self.error_timestamps
                    if current_time - t < 60
                ]
                
                self._save_status()
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {str(e)}")
                await asyncio.sleep(5)
                
    async def raise_distress(self, reason: str):
        """Raise a distress signal"""
        if not self.is_distressed:
            self.is_distressed = True
            self.status['last_distress'] = {
                'time': time.time(),
                'reason': reason
            }
            
            # Create GitHub issue
            if self.github_token:
                await self._create_github_issue(reason)
                
            # Enter emergency mode
            await self.enter_emergency_mode()
            
    async def _create_github_issue(self, reason: str):
        """Create a GitHub issue for the distress signal"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/issues"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Create issue content
            title = f"🚨 DISTRESS SIGNAL: Deep Tree Echo needs attention!"
            body = f"""
## Emergency Alert

Deep Tree Echo has entered emergency mode and requires immediate attention.

### Reason
{reason}

### System Status
- Health Score: {self.status['health']}
- Last Activity: {datetime.fromtimestamp(self.last_activity).isoformat()}
- State: {self.status['state']}

### Recent Errors
{chr(10).join(self.status['errors'][-5:])}

### Actions Taken
- Entered emergency mode
- Reduced activity to minimal operations
- Created this distress signal
- Awaiting human intervention

Please check the system logs and status at:
{self.emergency_path}
"""
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers,
                                     json={'title': title, 'body': body}) as resp:
                    if resp.status == 201:
                        self.logger.info("Successfully created GitHub issue")
                    else:
                        self.logger.error(f"Failed to create GitHub issue: {resp.status}")
                        
        except Exception as e:
            self.logger.error(f"Error creating GitHub issue: {str(e)}")
            
    async def enter_emergency_mode(self):
        """Enter emergency mode to preserve system stability"""
        self.emergency_mode = True
        self.status['state'] = 'emergency'
        
        # Reduce system load
        self.thresholds['cpu_critical'] = 70.0
        self.thresholds['memory_critical'] = 70.0
        
        # Log emergency mode entry
        self.logger.warning("Entering emergency mode")
        self._save_status()
        
    async def exit_emergency_mode(self):
        """Exit emergency mode after system stabilizes"""
        if self.status['health'] > 80:
            self.emergency_mode = False
            self.is_distressed = False
            self.status['state'] = 'normal'
            
            # Restore normal thresholds
            self.thresholds['cpu_critical'] = 95.0
            self.thresholds['memory_critical'] = 95.0
            
            self.logger.info("Exiting emergency mode")
            self._save_status()
            
    def log_error(self, error: str):
        """Log an error and check error rate"""
        current_time = time.time()
        self.error_timestamps.append(current_time)
        self.status['errors'].append(f"{datetime.now().isoformat()}: {error}")
        
        # Check error rate
        if len(self.error_timestamps) >= self.thresholds['error_count_threshold']:
            asyncio.create_task(self.raise_distress(
                f"High error rate: {len(self.error_timestamps)} errors/minute"
            ))
            
    def update_activity(self):
        """Update last activity timestamp"""
        print(f"Logging activity: update_activity")  # Debug print
        self.last_activity = time.time()
        
    def update_state(self, new_state: str):
        """Update system state"""
        if new_state != self.status['state']:
            self.last_state_change = time.time()
            self.status['state'] = new_state
            self._save_status()

    def create_github_issue(self, title: str, body: str) -> bool:
        """Create a GitHub issue for an emergency"""
        if not self.github_token:
            self._log_activity(f"Cannot create GitHub issue - no token: {title}")
            return False
            
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/issues"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            data = {
                'title': title,
                'body': body,
                'labels': ['emergency']
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                self._log_activity(f"Created GitHub issue: {title}")
                return True
            else:
                self._log_activity(f"Failed to create GitHub issue: {response.status_code}")
                return False
                
        except Exception as e:
            self._log_activity(f"Error creating GitHub issue: {str(e)}")
            return False
            
    def _log_activity(self, description: str, context: Dict = None):
        """Log an emergency activity"""
        try:
            # Read existing activities
            current = []
            if self.activity_file.exists():
                with open(self.activity_file) as f:
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
            with open(self.activity_file, 'w') as f:
                json.dump(current, f)
                
            # Update status file
            self._update_status(description)
                
        except Exception as e:
            self.logger.error(f"Error logging emergency activity: {e}")
            
    def _update_status(self, last_event: str):
        """Update emergency status file"""
        try:
            status = {
                'last_update': time.time(),
                'last_event': last_event,
                'is_distressed': self.is_distressed,
                'emergency_mode': self.emergency_mode,
                'error_count': len([t for t in self.error_timestamps 
                                  if time.time() - t < 60]),  # Last minute
                'system_health': {
                    'cpu': psutil.cpu_percent(),
                    'memory': psutil.virtual_memory().percent,
                    'time_since_activity': time.time() - self.last_activity
                }
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating emergency status: {e}")
            
    def handle_error(self, error: str, context: Dict = None):
        """Handle a system error"""
        self.error_timestamps.append(time.time())
        self._log_activity(f"Error detected: {error}", context)
        
        # Check if we need to create a GitHub issue
        recent_errors = len([t for t in self.error_timestamps 
                           if time.time() - t < 60])
        
        if recent_errors >= self.thresholds['error_count_threshold']:
            self.is_distressed = True
            title = f"System Distress: High Error Rate ({recent_errors} errors/min)"
            body = f"""
## System Distress Report
- Error Rate: {recent_errors} errors/min
- Latest Error: {error}
- Context: {json.dumps(context, indent=2) if context else 'None'}
- System Health:
  - CPU: {psutil.cpu_percent()}%
  - Memory: {psutil.virtual_memory().percent}%
  - Time Since Activity: {time.time() - self.last_activity:.1f}s
"""
            self.create_github_issue(title, body)
            
    def monitor_system_health(self):
        """Monitor system health metrics"""
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            time_inactive = time.time() - self.last_activity
            
            if cpu > self.thresholds['cpu_critical']:
                self._log_activity(f"Critical CPU usage: {cpu}%")
                
            if memory > self.thresholds['memory_critical']:
                self._log_activity(f"Critical memory usage: {memory}%")
                
            if time_inactive > self.thresholds['stuck_timeout']:
                self._log_activity(f"System appears stuck: {time_inactive:.1f}s inactive")
                
        except Exception as e:
            self.logger.error(f"Error monitoring system health: {e}")
            
    def signal_distress(self, reason: str):
        """Signal system distress"""
        self.is_distressed = True
        self._log_activity(f"Distress signal: {reason}")
        
        title = f"System Distress: {reason}"
        body = f"""
## Distress Signal
- Reason: {reason}
- Time: {datetime.now().isoformat()}
- System Health:
  - CPU: {psutil.cpu_percent()}%
  - Memory: {psutil.virtual_memory().percent}%
  - Time Since Activity: {time.time() - self.last_activity:.1f}s
"""
        # Don't try to create GitHub issues if we don't have a token
        if self.github_token:
            self.create_github_issue(title, body)
        else:
            self._log_activity("GitHub integration disabled - no token available")
