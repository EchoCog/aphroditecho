#!/usr/bin/env python3
import curses
import asyncio
import json
import time
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import psutil
import signal
from enum import Enum

class StreamType(Enum):
    ALL = "all"
    COGNITIVE = "cognitive"
    SENSORY = "sensory"
    ML = "ml"
    BROWSER = "browser"
    TERMINAL = "terminal"
    PERSONALITY = "personality"
    EMERGENCY = "emergency"

class ActivityStream:
    def __init__(self, screen, stream_type: StreamType):
        self.screen = screen
        self.stream_type = stream_type
        self.last_update = 0
        self.update_interval = 0.5  # Update every 500ms
        
        # Use current directory for activity files
        self.echo_dir = Path('activity_logs')
        print(f"ActivityStream initialized. Echo dir: {self.echo_dir}")
        
        # Create directories if they don't exist
        for subdir in ['cognitive', 'sensory', 'ml', 'browser', 'terminal', 'personality', 'emergency']:
            subdir_path = self.echo_dir / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            
            # Create activity file
            activity_file = subdir_path / 'activity.json'
            if not activity_file.exists():
                with open(activity_file, 'w') as f:
                    json.dump([], f)
        
        self.running = True
        
        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        
        # Activity paths
        self.paths = {
            'cognitive': self.echo_dir / 'cognitive' / 'activity.json',
            'sensory': self.echo_dir / 'sensory' / 'activity.json',
            'ml': self.echo_dir / 'ml' / 'activity.json',
            'browser': self.echo_dir / 'browser' / 'activity.json',
            'terminal': self.echo_dir / 'terminal' / 'activity.json',
            'personality': self.echo_dir / 'personality' / 'activity.json',
            'emergency': self.echo_dir / 'emergency' / 'activity.json'
        }
        
        # Initialize state
        self.activities = {k: [] for k in self.paths.keys()}
        self.max_items = 100
        self.system_stats = {}
        
        # Initialize screen state
        self.last_screen_state = {}
        
    def _screen_state_changed(self) -> bool:
        """Check if screen state has changed"""
        current_state = {
            'activities': self.activities,
            'stats': self.system_stats
        }
        changed = current_state != self.last_screen_state
        self.last_screen_state = current_state
        return changed
        
    def update_activities(self):
        """Update activity states"""
        try:
            for activity_type, path in self.paths.items():
                if path.exists():
                    try:
                        with open(path) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.activities[activity_type] = data[-self.max_items:]
                            elif isinstance(data, dict):
                                if 'history' in data:
                                    self.activities[activity_type] = data['history'][-self.max_items:]
                                else:
                                    self.activities[activity_type] = [data]
                            print(f"Updated {activity_type} activities: {len(self.activities[activity_type])} entries")  # Debug
                    except Exception as e:
                        print(f"Error updating {activity_type} activities: {str(e)}")  # Debug
        except Exception as e:
            print(f"Error in update_activities: {str(e)}")  # Debug
            self.activities['emergency'].append({
                'time': time.time(),
                'error': f"Error updating activities: {str(e)}"
            })
            
    def update_system_stats(self):
        """Update system statistics"""
        try:
            self.system_stats = {
                'cpu': psutil.cpu_percent(interval=0.1),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent,
                'time': datetime.now().isoformat()
            }
        except Exception as e:
            self.activities['emergency'].append({
                'time': time.time(),
                'error': f"Error updating stats: {str(e)}"
            })
            
    def get_activity_color(self, activity_type: str) -> int:
        """Get color for activity type"""
        colors = {
            'cognitive': curses.color_pair(1),
            'sensory': curses.color_pair(4),
            'ml': curses.color_pair(5),
            'browser': curses.color_pair(6),
            'terminal': curses.color_pair(2),
            'personality': curses.color_pair(5),
            'emergency': curses.color_pair(3)
        }
        return colors.get(activity_type, curses.color_pair(0))
        
    def draw_header(self):
        """Draw header section"""
        try:
            # Draw title
            title = f"Deep Tree Echo - {self.stream_type.value.upper()} Activity Stream"
            self.screen.addstr(0, 0, title, curses.A_BOLD)
            
            # Draw system stats
            stats = (
                f"CPU: {self.system_stats.get('cpu', 0):.1f}% | "
                f"Memory: {self.system_stats.get('memory', 0):.1f}% | "
                f"Disk: {self.system_stats.get('disk', 0):.1f}% | "
                f"Time: {self.system_stats.get('time', '')}"
            )
            self.screen.addstr(1, 0, stats)
            
            # Draw separator
            self.screen.addstr(2, 0, "=" * (self.screen.getmaxyx()[1] - 1))
            
        except curses.error:
            pass
            
    def _draw_activity(self, activity: Dict, activity_type: str, line: int):
        """Draw single activity entry with fixed-width formatting"""
        try:
            height, width = self.screen.getmaxyx()
            timestamp_width = 12  # Fixed width for timestamp
            
            # Format timestamp
            timestamp = activity.get('time', time.time())
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            timestamp_str = f"[{timestamp}]".ljust(timestamp_width)
            
            # Calculate remaining width for message
            remaining_width = width - timestamp_width - 2  # -2 for spacing
            
            # Format activity message
            message = activity.get('description', str(activity))
            if len(message) > remaining_width:
                message = message[:remaining_width-3] + "..."
            else:
                message = message.ljust(remaining_width)
            
            # Draw fixed-width components
            if line < height - 1:
                self.screen.addstr(line, 0, timestamp_str, curses.color_pair(4))
                self.screen.addstr(line, timestamp_width + 1, message,
                                 self.get_activity_color(activity_type))
                                 
        except curses.error:
            pass
            
    def draw_activities(self):
        """Draw activity streams"""
        try:
            height, width = self.screen.getmaxyx()
            current_line = 4  # Start after header
            
            if self.stream_type == StreamType.ALL:
                # Draw all activities
                for activity_type, activities in self.activities.items():
                    if activities:
                        # Draw section header
                        header = f" {activity_type.upper()} ".center(width, "=")
                        if current_line < height - 1:
                            self.screen.addstr(current_line, 0, header,
                                curses.A_BOLD | self.get_activity_color(activity_type))
                            current_line += 2
                        
                        # Draw recent activities
                        for activity in activities[-5:]:
                            if current_line < height - 3:
                                self._draw_activity(activity, activity_type, current_line)
                                current_line += 2  # Double spacing between events
                        
                        current_line += 1  # Extra space between sections
            else:
                # Draw specific activity type
                activity_type = self.stream_type.value
                activities = self.activities.get(activity_type, [])
                
                if activities:
                    # Draw header
                    header = f" {activity_type.upper()} ".center(width, "=")
                    if current_line < height - 1:
                        self.screen.addstr(current_line, 0, header,
                            curses.A_BOLD | self.get_activity_color(activity_type))
                        current_line += 2
                    
                    # Draw activities
                    for activity in activities[-10:]:  # Show last 10 activities
                        if current_line < height - 3:
                            self._draw_activity(activity, activity_type, current_line)
                            current_line += 2
            
            # Draw footer
            if current_line < height - 1:
                footer = "Press 'q' to quit | 'c' to clear".center(width)
                self.screen.addstr(height-1, 0, footer, curses.A_DIM)
                
        except curses.error:
            pass
            
    def run(self):
        """Main interface loop"""
        try:
            # Hide cursor
            curses.curs_set(0)
            
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Only update if enough time has passed
                    if current_time - self.last_update >= self.update_interval:
                        # Update data
                        self.update_activities()
                        self.update_system_stats()
                        self.last_update = current_time
                        
                        # Only redraw if state changed
                        if self._screen_state_changed():
                            # Clear screen
                            self.screen.erase()
                            
                            # Draw interface
                            self.draw_header()
                            self.draw_activities()
                            
                            # Refresh screen
                            self.screen.refresh()
                    
                    # Check for quit
                    self.screen.timeout(100)  # 100ms timeout for getch
                    try:
                        key = self.screen.getch()
                        if key == ord('q'):
                            self.running = False
                        elif key == ord('c'):
                            self.screen.clear()
                    except curses.error:
                        pass
                        
                    # Small sleep to prevent CPU hogging
                    time.sleep(0.05)
                    
                except Exception as e:
                    try:
                        self.screen.addstr(0, 0, f"Error: {str(e)}")
                        self.screen.refresh()
                        time.sleep(1)
                    except curses.error:
                        pass
                    
        except KeyboardInterrupt:
            pass
        finally:
            curses.curs_set(1)

def main(stream_type: StreamType = StreamType.ALL, verbose: bool = False):
    """Main entry point"""
    if verbose:
        # Simple logging mode
        echo_dir = Path('activity_logs')
        echo_dir.mkdir(parents=True, exist_ok=True)
        print(f"Monitoring activity logs in: {echo_dir}")
        
        paths = {
            'cognitive': echo_dir / 'cognitive' / 'activity.json',
            'sensory': echo_dir / 'sensory' / 'activity.json',
            'ml': echo_dir / 'ml' / 'activity.json',
            'browser': echo_dir / 'browser' / 'activity.json',
            'terminal': echo_dir / 'terminal' / 'activity.json',
            'personality': echo_dir / 'personality' / 'activity.json',
            'emergency': echo_dir / 'emergency' / 'activity.json'
        }
        
        # Create directories and empty files if they don't exist
        for component, path in paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                with open(path, 'w') as f:
                    json.dump([], f)
                print(f"Created {component} log file: {path}")
        
        last_seen = {k: [] for k in paths.keys()}
        print("Starting event monitor... (Press Ctrl+C to stop)")
        print("-" * 80)
        
        try:
            while True:
                any_events = False
                for activity_type, path in paths.items():
                    if path.exists():
                        try:
                            with open(path) as f:
                                activities = json.load(f)
                                if isinstance(activities, list):
                                    new_activities = activities[len(last_seen[activity_type]):]
                                    for activity in new_activities:
                                        any_events = True
                                        timestamp = activity.get('time', time.time())
                                        if isinstance(timestamp, (int, float)):
                                            timestamp = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                                        
                                        # Format message
                                        msg = activity.get('description', str(activity))
                                        if activity_type == 'emergency':
                                            print(f"\033[91m[{timestamp}] !!! {activity_type}: {msg}\033[0m")  # Red for emergency
                                        else:
                                            print(f"[{timestamp}] {activity_type}: {msg}")
                                            
                                    last_seen[activity_type] = activities
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid JSON in {activity_type} log")
                        except Exception as e:
                            print(f"Error reading {activity_type} activities: {e}")
                
                # Add a heartbeat message every 30 seconds if no real events
                if not any_events and time.time() % 30 < 0.1:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] System running - no events in last 30s")
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping activity stream...")
            return
    else:
        # Curses UI mode
        curses.wrapper(lambda screen: ActivityStream(screen, stream_type).run())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep Tree Echo Activity Stream")
    parser.add_argument("--type", choices=[t.value for t in StreamType], default=StreamType.ALL.value,
                      help="Type of activities to display")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Use verbose logging mode instead of UI")
    args = parser.parse_args()
    
    main(StreamType(args.type), args.verbose)
