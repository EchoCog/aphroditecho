#!/usr/bin/env python3

import os
import sys
import logging
import signal
import argparse
import threading
import socket

# Set up logging to file instead of console
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='gui_dashboard.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Global references to prevent garbage collection
app = None
root = None

def signal_handler(sig, frame):
    """Handle exit signals properly"""
    logger.info("Shutdown signal received, closing application")
    if root:
        root.quit()
    sys.exit(0)

def patch_ttkbootstrap_locale():
    """Monkey patch ttkbootstrap to fix the locale issue"""
    try:
        # Find the ttkbootstrap dialogs module
        import importlib.util
        import sys
        from pathlib import Path
        
        # First, try to find the module path
        try:
            import ttkbootstrap
            dialogs_path = Path(ttkbootstrap.__file__).parent / "dialogs" / "dialogs.py"
        except ImportError:
            # Find in site-packages if not directly importable
            python_path = Path(sys.executable).parent / "lib"
            site_packages = list(python_path.glob("*/site-packages"))
            if not site_packages:
                logger.warning("Could not find site-packages directory")
                return False
                
            dialogs_path = None
            for sp in site_packages:
                possible_path = sp / "ttkbootstrap" / "dialogs" / "dialogs.py"
                if possible_path.exists():
                    dialogs_path = possible_path
                    break
        
        if not dialogs_path or not dialogs_path.exists():
            logger.warning("Could not find ttkbootstrap dialogs.py")
            return False
            
        # Read the file content
        content = dialogs_path.read_text()
        
        # Check if the problematic code is present
        if "locale.setlocale(locale.LC_ALL, locale.setlocale(locale.LC_TIME, \"\"))" in content:
            logger.info("Found problematic locale code, patching...")
            
            # Create a backup
            backup_path = dialogs_path.with_suffix(".py.bak")
            if not backup_path.exists():
                dialogs_path.rename(backup_path)
                
                # Replace the problematic line with a safer version
                patched_content = content.replace(
                    "locale.setlocale(locale.LC_ALL, locale.setlocale(locale.LC_TIME, \"\"))",
                    "# Patched by fix_locale_gui.py\ntry:\n            locale.setlocale(locale.LC_ALL, '')\n        except locale.Error:\n            pass"
                )
                
                # Write the patched content back
                dialogs_path.write_text(patched_content)
                logger.info("Successfully patched ttkbootstrap dialogs.py")
                return True
            else:
                logger.info("Backup already exists, assuming already patched")
                return True
        else:
            logger.info("Problematic locale code not found, may already be patched")
            return True
            
    except Exception as e:
        logger.error(f"Error patching ttkbootstrap: {str(e)}", exc_info=True)
        return False

def get_ip_and_hostname():
    """Get IP address and hostname for connecting to the GUI"""
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except:
        ip = "127.0.0.1"
    
    # Check for forwarded ports
    forwarded_ports = []
    try:
        # Try to detect forwarded ports from the environment
        for key, value in os.environ.items():
            if key.startswith('FORWARDED_PORT_'):
                forwarded_ports.append(value)
    except Exception as e:
        logger.warning(f"Error detecting forwarded ports: {e}")
    
    return ip, hostname, forwarded_ports

def main():
    global app, root
    
    parser = argparse.ArgumentParser(description="Launch Deep Tree Echo GUI Dashboard with locale fix")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-activity", action="store_true", help="Disable activity monitoring")
    parser.add_argument("--port", type=int, help="Specify port to use for the GUI")
    args = parser.parse_args()
    
    # Check if port is provided as environment variable
    port = args.port
    if not port and 'GUI_DASHBOARD_PORT' in os.environ:
        try:
            port = int(os.environ['GUI_DASHBOARD_PORT'])
        except ValueError:
            logger.warning(f"Invalid port in GUI_DASHBOARD_PORT: {os.environ['GUI_DASHBOARD_PORT']}")
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Set up signal handlers for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Try to set LC_ALL and LANG environment variables
    os.environ['LC_ALL'] = 'C'
    os.environ['LANG'] = 'C'
    
    # Get network information
    ip, hostname, forwarded_ports = get_ip_and_hostname()
    
    # Print connection information to both terminal and log
    connection_info = f"GUI Dashboard running on {hostname} ({ip})"
    if port:
        connection_info += f" on port {port}"
    if forwarded_ports:
        connection_info += f", forwarded ports: {', '.join(forwarded_ports)}"
        
    print("\n" + "="*80)
    print(connection_info)
    print("Environment variables:")
    print(f"  DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"  XAUTHORITY: {os.environ.get('XAUTHORITY', 'Not set')}")
    print("="*80 + "\n")
    
    logger.info(connection_info)
    
    # Apply the ttkbootstrap locale patch
    if not patch_ttkbootstrap_locale():
        logger.warning("Failed to patch ttkbootstrap, attempting to continue anyway")
    
    try:
        # Now try to import tkinter
        import tkinter as tk
        from tkinterdnd2 import TkinterDnD
        
        # Import necessary components
        from gui_dashboard import GUIDashboard
        from memory_management import HypergraphMemory
        
        # Create tkinter root window
        root = TkinterDnD.Tk()
        
        # Prepare optional components with safe defaults
        memory = HypergraphMemory(storage_dir="echo_memory")
        cognitive = None
        personality = None
        sensory = None
        emergency = None
        browser = None
        ai_manager = None
        
        # Only import and initialize ActivityRegulator if not disabled
        if args.no_activity:
            activity = None
        else:
            from activity_regulation import ActivityRegulator
            activity = ActivityRegulator()
        
        # Initialize the GUI dashboard with available components
        app = GUIDashboard(
            root, 
            memory=memory,
            cognitive=cognitive,
            personality=personality,
            sensory=sensory, 
            activity=activity,
            emergency=emergency,
            browser=browser,
            ai_manager=ai_manager
        )
        
        # Configure window settings
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        
        # Center window on screen
        window_width = 1200
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Set window title with version and connection info
        title = f"Deep Tree Echo Dashboard v1.0 - {hostname}:{os.environ.get('DISPLAY', ':0')}"
        if port:
            title += f" (Port: {port})"
        root.title(title)
        
        # Log GUI ready
        logger.info("GUI dashboard initialized and ready")
        print(f"GUI dashboard initialized and ready on display {os.environ.get('DISPLAY', ':0')}")
        
        # Start the main event loop
        root.mainloop()
        
        # After mainloop exits
        logger.info("GUI dashboard closed")
        
        # Clean up (if activity monitoring was enabled)
        if activity:
            activity.shutdown()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error launching GUI dashboard: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())