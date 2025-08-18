import os
import subprocess
import logging
import pwd
import grp
from pathlib import Path
from typing import List, Dict, Optional, Union
import threading
import queue
import signal

class TerminalController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_commands)
        self.worker_thread.daemon = True
        
    def start(self):
        """Start the terminal controller"""
        self.running = True
        self.worker_thread.start()
        self.logger.info("Terminal controller started")
        
    def stop(self):
        """Stop the terminal controller"""
        self.running = False
        self.command_queue.put(None)  # Signal worker to stop
        self.worker_thread.join()
        self.logger.info("Terminal controller stopped")
        
    def execute_command(self, command: Union[str, List[str]], 
                       sudo: bool = False, 
                       timeout: Optional[int] = None) -> Dict:
        """Execute a shell command with optional sudo privileges"""
        try:
            if isinstance(command, str):
                command = command.split()
                
            if sudo and command[0] != 'sudo':
                command = ['sudo', '-n'] + command
                
            self.logger.info(f"Executing command: {' '.join(command)}")
            
            # Add command to queue
            self.command_queue.put((command, timeout))
            
            # Wait for result
            result = self.result_queue.get()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
            
    def _process_commands(self):
        """Process commands from the queue"""
        while self.running:
            try:
                item = self.command_queue.get()
                if item is None:
                    break
                    
                command, timeout = item
                
                # Execute command
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        preexec_fn=os.setsid
                    )
                    
                    try:
                        stdout, stderr = process.communicate(timeout=timeout)
                        result = {
                            'success': process.returncode == 0,
                            'stdout': stdout,
                            'stderr': stderr,
                            'returncode': process.returncode
                        }
                    except subprocess.TimeoutExpired:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        result = {
                            'success': False,
                            'error': 'Command timed out',
                            'stdout': '',
                            'stderr': 'Command execution timed out',
                            'returncode': -1
                        }
                        
                except Exception as e:
                    result = {
                        'success': False,
                        'error': str(e),
                        'stdout': '',
                        'stderr': str(e),
                        'returncode': -1
                    }
                    
                self.result_queue.put(result)
                
            except Exception as e:
                self.logger.error(f"Error in command processor: {str(e)}")
                continue
                
    def verify_sudo_access(self) -> bool:
        """Verify sudo access is properly configured"""
        try:
            result = self.execute_command(['sudo', '-n', 'true'])
            return result['success']
        except Exception:
            return False
            
    def setup_sudo_access(self) -> bool:
        """Set up sudo access for Deep Tree Echo"""
        try:
            # Check if sudoers.d directory exists
            sudoers_dir = Path('/etc/sudoers.d')
            if not sudoers_dir.exists():
                self.logger.error("Sudoers directory not found")
                return False
                
            # Copy sudoers file
            src_file = Path('deep_tree_echo.sudoers')
            dst_file = sudoers_dir / 'deep-tree-echo'
            
            if not src_file.exists():
                self.logger.error("Sudoers source file not found")
                return False
                
            # Verify sudoers file syntax
            result = self.execute_command(['visudo', '-c', '-f', str(src_file)])
            if not result['success']:
                self.logger.error("Invalid sudoers file syntax")
                return False
                
            # Copy file with correct permissions
            result = self.execute_command(
                ['sudo', 'cp', str(src_file), str(dst_file)]
            )
            if not result['success']:
                return False
                
            # Set correct permissions
            result = self.execute_command(
                ['sudo', 'chmod', '0440', str(dst_file)]
            )
            if not result['success']:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up sudo access: {str(e)}")
            return False
            
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
