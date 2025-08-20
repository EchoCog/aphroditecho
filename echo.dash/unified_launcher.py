#!/usr/bin/env python3
"""
Unified Launcher for Deep Tree Echo

This module provides a unified interface for launching different components
of the Deep Tree Echo system, consolidating the functionality from:
- launch_deep_tree_echo.py
- launch_dashboards.py 
- launch_gui.py
- launch_gui_standalone.py

This reduces code duplication while maintaining backward compatibility.
"""

import os
import sys
import asyncio
import logging
import argparse
import subprocess
import signal
import threading
import atexit
import time
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LaunchMode(Enum):
    """Available launch modes"""
    DEEP_TREE_ECHO = "deep-tree-echo"
    GUI_DASHBOARD = "gui"
    GUI_STANDALONE = "gui-standalone"
    WEB_DASHBOARD = "web"
    DASHBOARD_MANAGER = "dashboards"

@dataclass
class LauncherConfig:
    """Configuration for the unified launcher"""
    mode: LaunchMode
    debug: bool = False
    
    # Deep Tree Echo specific options
    gui: bool = False
    browser: bool = False
    
    # GUI specific options
    no_activity: bool = False
    no_locale_fix: bool = False
    
    # Web/Dashboard specific options
    web_port: int = 8080
    gui_port: int = 5000
    gui_only: bool = False
    web_only: bool = False
    no_monitor: bool = False
    
    # General options
    log_file: Optional[str] = None
    storage_dir: str = "echo_memory"
    
    # Additional configuration
    extra_args: Dict[str, Any] = field(default_factory=dict)

class UnifiedLauncher:
    """Unified launcher for Deep Tree Echo components"""
    
    def __init__(self):
        self.processes = []
        self.gui_process = None
        self.web_process = None
        self.components = {}
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._cleanup)
    
    def _signal_handler(self, sig, frame):
        """Handle exit signals properly"""
        logger.info("Shutdown signal received")
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Clean up all processes and resources"""
        logger.info("Cleaning up processes and resources")
        
        for proc in self.processes:
            try:
                if proc.poll() is None:  # Still running
                    logger.info(f"Terminating process {proc.pid}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Process {proc.pid} did not terminate gracefully, forcing")
                        proc.kill()
            except Exception as e:
                logger.error(f"Error cleaning up process: {e}")
    
    def _determine_mode(self, args) -> LaunchMode:
        """Determine launch mode from arguments"""
        if hasattr(args, 'mode') and args.mode:
            try:
                return LaunchMode(args.mode)
            except ValueError:
                logger.warning(f"Unknown mode: {args.mode}, defaulting to GUI")
                return LaunchMode.GUI_DASHBOARD
        
        # Default fallback
        return LaunchMode.GUI_DASHBOARD
    
    def _initialize_components(self, config: LauncherConfig) -> Dict[str, Any]:
        """Initialize core components based on configuration"""
        components = {}
        
        try:
            # Create directory structure if needed
            for dir_path in ["activity_logs", "deep_tree_echo_profile", "ai_cache", config.storage_dir]:
                Path(dir_path).mkdir(exist_ok=True)
            
            # Initialize memory system
            logger.info("Initializing HypergraphMemory")
            try:
                from memory_management import HypergraphMemory
                components['memory'] = HypergraphMemory(storage_dir=config.storage_dir)
                logger.info("HypergraphMemory initialized")
            except Exception as e:
                logger.error(f"Failed to initialize HypergraphMemory: {e}")
                components['memory'] = None
            
            # Initialize cognitive architecture
            logger.info("Initializing CognitiveArchitecture")
            try:
                from cognitive_architecture import CognitiveArchitecture
                components['cognitive'] = CognitiveArchitecture()
                logger.info("CognitiveArchitecture initialized")
            except Exception as e:
                logger.warning(f"CognitiveArchitecture not available: {e}")
                components['cognitive'] = None
            
            # Initialize personality system
            logger.info("Initializing PersonalitySystem")
            try:
                from personality_system import PersonalitySystem
                components['personality'] = PersonalitySystem()
                logger.info("PersonalitySystem initialized")
            except Exception as e:
                logger.warning(f"PersonalitySystem not available: {e}")
                components['personality'] = None
            
            # Initialize sensory motor system
            logger.info("Initializing SensoryMotorSystem")
            try:
                from sensory_motor_simple import SensoryMotorSystem
                components['sensory'] = SensoryMotorSystem()
                logger.info("SensoryMotorSystem initialized")
            except Exception as e:
                logger.warning(f"SensoryMotorSystem not available: {e}")
                try:
                    from sensory_motor import SensoryMotorSystem
                    components['sensory'] = SensoryMotorSystem()
                    logger.info("SensoryMotorSystem (fallback) initialized")
                except Exception as e2:
                    logger.warning(f"No SensoryMotorSystem available: {e2}")
                    components['sensory'] = None
            
            # Initialize emergency protocols
            logger.info("Initializing EmergencyProtocols")
            try:
                from emergency_protocols import EmergencyProtocols
                components['emergency'] = EmergencyProtocols()
                logger.info("EmergencyProtocols initialized")
            except Exception as e:
                logger.warning(f"EmergencyProtocols not available: {e}")
                components['emergency'] = None
            
            # Initialize activity regulation
            if not config.no_activity:
                logger.info("Initializing ActivityRegulation")
                try:
                    from activity_regulation import ActivityRegulation
                    components['activity'] = ActivityRegulation()
                    logger.info("ActivityRegulation initialized")
                except Exception as e:
                    logger.warning(f"ActivityRegulation not available: {e}")
                    components['activity'] = None
            else:
                components['activity'] = None
            
            # Initialize AI manager
            logger.info("Initializing AI manager")
            try:
                from ai_integration import ai_manager
                components['ai_manager'] = ai_manager
                logger.info("AI manager initialized")
            except Exception as e:
                logger.warning(f"AI manager not available: {e}")
                components['ai_manager'] = None
            
            # Initialize browser if requested
            if config.browser:
                logger.info("Initializing BrowserInterface")
                try:
                    from browser_interface import BrowserInterface
                    components['browser'] = BrowserInterface()
                    logger.info("BrowserInterface initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize browser: {e}")
                    components['browser'] = None
            else:
                components['browser'] = None
            
        except Exception as e:
            logger.error(f"Error during component initialization: {e}")
        
        return components
    
    async def _launch_deep_tree_echo(self, config: LauncherConfig) -> int:
        """Launch Deep Tree Echo system in async mode"""
        logger.info("Launching Deep Tree Echo system")
        
        try:
            components = self._initialize_components(config)
            
            # Initialize browser interface if requested
            if config.browser and components.get('browser'):
                try:
                    await components['browser'].initialize()
                    logger.info("Browser automation initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize browser: {e}")
                    if components.get('emergency'):
                        components['emergency'].register_incident("browser_init_failure", str(e))
            
            # Launch GUI if requested
            if config.gui:
                try:
                    from gui_dashboard import launch_dashboard
                    logger.info("Launching GUI dashboard...")
                    launch_dashboard(**components)
                except Exception as e:
                    logger.error(f"Failed to launch GUI dashboard: {e}")
                    if components.get('emergency'):
                        components['emergency'].register_incident("gui_launch_failure", str(e))
            
            # Keep the event loop running
            logger.info("Deep Tree Echo is now operational")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown initiated by keyboard interrupt")
                
        except Exception as e:
            logger.error(f"Critical error in Deep Tree Echo: {e}")
            return 1
        finally:
            logger.info("Deep Tree Echo shutdown complete")
        
        return 0
    
    def _launch_gui_dashboard(self, config: LauncherConfig) -> int:
        """Launch GUI dashboard"""
        logger.info("Launching GUI dashboard")
        
        try:
            # Check display environment for GUI
            if 'DISPLAY' not in os.environ:
                logger.error("No display environment detected. GUI requires X11 display.")
                return 1
            
            components = self._initialize_components(config)
            
            # Import GUI components
            try:
                from tkinterdnd2 import TkinterDnD
                from gui_dashboard import GUIDashboard
            except ImportError as e:
                logger.error(f"Failed to import GUI components: {e}")
                return 1
            
            # Create tkinter root window
            root = TkinterDnD.Tk()
            
            # Initialize GUI dashboard
            app = GUIDashboard(root, **components)
            
            # Configure window
            root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
            root.title("Deep Tree Echo Dashboard")
            
            # Start main event loop
            logger.info("GUI dashboard ready")
            root.mainloop()
            logger.info("GUI dashboard closed")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error launching GUI dashboard: {e}")
            return 1
    
    def _launch_web_dashboard(self, config: LauncherConfig) -> int:
        """Launch web dashboard"""
        logger.info(f"Launching web dashboard on port {config.web_port}")
        
        try:
            # Start web dashboard process
            self.web_process = subprocess.Popen(
                [sys.executable, "web_gui.py", "--port", str(config.web_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes.append(self.web_process)
            
            # Monitor the process
            self._monitor_process(self.web_process, "Web Dashboard")
            
            logger.info(f"Web dashboard started with PID: {self.web_process.pid}")
            return 0
            
        except Exception as e:
            logger.error(f"Error launching web dashboard: {e}")
            return 1
    
    def _launch_dashboard_manager(self, config: LauncherConfig) -> int:
        """Launch dashboard manager (both GUI and web)"""
        logger.info("Launching dashboard manager")
        
        launched_gui = False
        launched_web = False
        
        # Launch GUI if not web-only
        if not config.web_only:
            script = "launch_gui_standalone.py" if config.no_locale_fix else "fix_locale_gui.py"
            try:
                env = os.environ.copy()
                env['GUI_DASHBOARD_PORT'] = str(config.gui_port)
                
                self.gui_process = subprocess.Popen(
                    [sys.executable, script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    env=env
                )
                self.processes.append(self.gui_process)
                self._monitor_process(self.gui_process, "GUI Dashboard")
                launched_gui = True
                logger.info(f"GUI dashboard started with PID: {self.gui_process.pid}")
            except Exception as e:
                logger.error(f"Error launching GUI dashboard: {e}")
        
        # Launch web if not gui-only
        if not config.gui_only:
            try:
                self.web_process = subprocess.Popen(
                    [sys.executable, "web_gui.py", "--port", str(config.web_port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                self.processes.append(self.web_process)
                self._monitor_process(self.web_process, "Web Dashboard")
                launched_web = True
                logger.info(f"Web dashboard started with PID: {self.web_process.pid}")
            except Exception as e:
                logger.error(f"Error launching web dashboard: {e}")
        
        if not launched_gui and not launched_web:
            logger.error("Failed to launch any dashboards")
            return 1
        
        # Monitor dashboards if not disabled
        if not config.no_monitor:
            try:
                while True:
                    time.sleep(10)
                    # Check if processes are still running
                    gui_running = self.gui_process and self.gui_process.poll() is None
                    web_running = self.web_process and self.web_process.poll() is None
                    
                    if not gui_running and not web_running:
                        logger.info("All dashboards have terminated")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
        
        return 0
    
    def _monitor_process(self, process, name):
        """Monitor and log process output"""
        def monitor():
            while process.poll() is None:
                try:
                    for line in process.stdout:
                        if line:
                            logger.info(f"{name} output: {line.strip()}")
                    for line in process.stderr:
                        if line:
                            logger.error(f"{name} error: {line.strip()}")
                except Exception as e:
                    logger.error(f"Error reading {name} output: {e}")
                    time.sleep(1)
            
            exit_code = process.returncode
            logger.info(f"{name} process exited with code: {exit_code}")
        
        threading.Thread(target=monitor, daemon=True).start()
    
    async def launch_async(self, config: LauncherConfig) -> int:
        """Launch in async mode"""
        if config.mode == LaunchMode.DEEP_TREE_ECHO:
            return await self._launch_deep_tree_echo(config)
        else:
            # For non-async modes, run in thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await asyncio.get_event_loop().run_in_executor(
                    executor, self.launch_sync, config
                )
    
    def launch_sync(self, config: LauncherConfig) -> int:
        """Launch in sync mode"""
        if config.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        if config.log_file:
            handler = logging.FileHandler(config.log_file)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logging.getLogger().addHandler(handler)
        
        logger.info(f"Starting launcher in {config.mode.value} mode")
        
        try:
            if config.mode == LaunchMode.DEEP_TREE_ECHO:
                # This should use async mode
                return asyncio.run(self._launch_deep_tree_echo(config))
            elif config.mode in [LaunchMode.GUI_DASHBOARD, LaunchMode.GUI_STANDALONE]:
                return self._launch_gui_dashboard(config)
            elif config.mode == LaunchMode.WEB_DASHBOARD:
                return self._launch_web_dashboard(config)
            elif config.mode == LaunchMode.DASHBOARD_MANAGER:
                return self._launch_dashboard_manager(config)
            else:
                logger.error(f"Unknown launch mode: {config.mode}")
                return 1
                
        except Exception as e:
            logger.error(f"Error during launch: {e}")
            return 1

def create_config_from_args(mode_name: str, args) -> LauncherConfig:
    """Create launcher config from command line arguments"""
    try:
        mode = LaunchMode(mode_name)
    except ValueError:
        mode = LaunchMode.GUI_DASHBOARD
    
    config = LauncherConfig(mode=mode)
    
    # Copy common arguments
    if hasattr(args, 'debug'):
        config.debug = args.debug
    if hasattr(args, 'gui'):
        config.gui = args.gui
    if hasattr(args, 'browser'):
        config.browser = args.browser
    if hasattr(args, 'no_activity'):
        config.no_activity = args.no_activity
    if hasattr(args, 'no_locale_fix'):
        config.no_locale_fix = args.no_locale_fix
    if hasattr(args, 'web_port'):
        config.web_port = args.web_port
    if hasattr(args, 'gui_port'):
        config.gui_port = args.gui_port
    if hasattr(args, 'gui_only'):
        config.gui_only = args.gui_only
    if hasattr(args, 'web_only'):
        config.web_only = args.web_only
    if hasattr(args, 'no_monitor'):
        config.no_monitor = args.no_monitor
    
    return config

def create_argument_parser(mode: str) -> argparse.ArgumentParser:
    """Create argument parser for a specific mode"""
    parser = argparse.ArgumentParser(description=f"Deep Tree Echo Launcher - {mode} mode")
    
    # Common arguments
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-file", type=str, help="Log file path")
    parser.add_argument("--storage-dir", type=str, default="echo_memory", help="Storage directory")
    
    if mode == "deep-tree-echo":
        parser.add_argument("--gui", action="store_true", help="Launch GUI dashboard")
        parser.add_argument("--browser", action="store_true", help="Initialize browser automation")
    
    elif mode in ["gui", "gui-standalone"]:
        parser.add_argument("--no-activity", action="store_true", help="Disable activity monitoring")
    
    elif mode == "dashboards":
        parser.add_argument("--gui-only", action="store_true", help="Launch only the GUI dashboard")
        parser.add_argument("--web-only", action="store_true", help="Launch only the Web dashboard")
        parser.add_argument("--no-locale-fix", action="store_true", help="Don't use the locale fix for the GUI dashboard")
        parser.add_argument("--web-port", type=int, default=8080, help="Port for the Web dashboard (default: 8080)")
        parser.add_argument("--gui-port", type=int, default=5000, help="Port for the GUI dashboard (default: 5000)")
        parser.add_argument("--no-monitor", action="store_true", help="Don't monitor dashboard status")
    
    elif mode == "web":
        parser.add_argument("--port", type=int, default=8080, help="Port for the web server (default: 8080)")
    
    return parser

if __name__ == "__main__":
    # Default mode if launched directly
    mode = "gui"
    parser = create_argument_parser(mode)
    args = parser.parse_args()
    
    config = create_config_from_args(mode, args)
    launcher = UnifiedLauncher()
    
    sys.exit(launcher.launch_sync(config))