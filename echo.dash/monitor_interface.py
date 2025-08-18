import curses
import asyncio
import logging
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import psutil
import signal

class MonitorInterface:
    def __init__(self, screen):
        self.screen = screen
        self.logger = logging.getLogger(__name__)
        self.running = True
        
        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        
        # Get paths
        self.echo_dir = Path.home() / '.deep_tree_echo'
        self.log_file = self.echo_dir / 'deep_tree_echo.log'
        self.status_file = self.echo_dir / 'emergency' / 'status.json'
        
        # Initialize state
        self.log_lines = []
        self.max_log_lines = 1000
        self.status = {}
        self.system_stats = {}
        
    def update_status(self):
        """Update system status"""
        try:
            if self.status_file.exists():
                with open(self.status_file) as f:
                    self.status = json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading status: {str(e)}")
            
    def update_logs(self):
        """Update log contents"""
        try:
            if self.log_file.exists():
                with open(self.log_file) as f:
                    new_lines = f.readlines()
                    self.log_lines.extend(new_lines)
                    if len(self.log_lines) > self.max_log_lines:
                        self.log_lines = self.log_lines[-self.max_log_lines:]
        except Exception as e:
            self.logger.error(f"Error reading logs: {str(e)}")
            
    def update_system_stats(self):
        """Update system statistics"""
        try:
            self.system_stats = {
                'cpu': psutil.cpu_percent(interval=0.1),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent
            }
        except Exception as e:
            self.logger.error(f"Error updating stats: {str(e)}")
            
    def get_status_color(self, health: float) -> int:
        """Get color based on health score"""
        if health >= 80:
            return curses.color_pair(1)  # Green
        elif health >= 50:
            return curses.color_pair(2)  # Yellow
        else:
            return curses.color_pair(3)  # Red
            
    def draw_header(self):
        """Draw header section"""
        try:
            health = self.status.get('health', 0)
            state = self.status.get('state', 'unknown')
            color = self.get_status_color(health)
            
            # Draw title
            self.screen.addstr(0, 0, "Deep Tree Echo Monitor", curses.A_BOLD)
            self.screen.addstr(0, 25, f"Health: {health:.1f}%", color)
            self.screen.addstr(0, 45, f"State: {state}")
            
            # Draw system stats
            self.screen.addstr(1, 0, 
                f"CPU: {self.system_stats.get('cpu', 0):.1f}% | "
                f"Memory: {self.system_stats.get('memory', 0):.1f}% | "
                f"Disk: {self.system_stats.get('disk', 0):.1f}%"
            )
            
            # Draw last distress if any
            last_distress = self.status.get('last_distress')
            if last_distress:
                self.screen.addstr(2, 0, "Last Distress: ", curses.A_BOLD)
                self.screen.addstr(2, 14, 
                    f"{datetime.fromtimestamp(last_distress['time']).isoformat()} - "
                    f"{last_distress['reason']}", 
                    curses.color_pair(3)
                )
        except Exception as e:
            self.logger.error(f"Error drawing header: {str(e)}")
            
    def draw_logs(self):
        """Draw log section"""
        try:
            height, width = self.screen.getmaxyx()
            log_height = height - 5  # Reserve space for header and footer
            
            # Draw log header
            self.screen.addstr(4, 0, "Live Log Stream:", curses.A_BOLD)
            
            # Draw logs
            for i, line in enumerate(self.log_lines[-log_height:]):
                try:
                    # Truncate line to fit screen
                    line = line.strip()[:width-1]
                    
                    # Color based on log level
                    color = curses.color_pair(0)
                    if "ERROR" in line:
                        color = curses.color_pair(3)
                    elif "WARNING" in line:
                        color = curses.color_pair(2)
                    elif "INFO" in line:
                        color = curses.color_pair(4)
                        
                    self.screen.addstr(5 + i, 0, line, color)
                except curses.error:
                    pass  # Skip lines that don't fit
                    
        except Exception as e:
            self.logger.error(f"Error drawing logs: {str(e)}")
            
    def run(self):
        """Main interface loop"""
        try:
            # Hide cursor
            curses.curs_set(0)
            
            while self.running:
                try:
                    # Update data
                    self.update_status()
                    self.update_logs()
                    self.update_system_stats()
                    
                    # Clear screen
                    self.screen.clear()
                    
                    # Draw interface
                    self.draw_header()
                    self.draw_logs()
                    
                    # Refresh screen
                    self.screen.refresh()
                    
                    # Check for quit
                    self.screen.timeout(1000)
                    try:
                        key = self.screen.getch()
                        if key == ord('q'):
                            self.running = False
                    except curses.error:
                        pass
                        
                except Exception as e:
                    self.logger.error(f"Error in main loop: {str(e)}")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            pass
        finally:
            curses.curs_set(1)  # Show cursor again

def main(screen):
    interface = MonitorInterface(screen)
    interface.run()

if __name__ == "__main__":
    curses.wrapper(main)
