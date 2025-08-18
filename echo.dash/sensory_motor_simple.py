import logging
import time
import random
import numpy as np
import json
from pathlib import Path
from typing import Optional, Dict, Tuple, List, Union
import os
import subprocess
import sys

# Enhanced display environment detection
DISPLAY_AVAILABLE = 'DISPLAY' in os.environ
VIRTUAL_DISPLAY = DISPLAY_AVAILABLE and os.environ.get('DISPLAY', '').startswith(':')
HEADLESS = not DISPLAY_AVAILABLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle missing .Xauthority file
def create_xauth_file():
    """Create empty .Xauthority file if missing"""
    xauth_path = os.path.expanduser('~/.Xauthority')
    if not os.path.exists(xauth_path):
        try:
            logger.info(f"Creating empty .Xauthority file at {xauth_path}")
            with open(xauth_path, 'wb') as f:
                pass  # Create empty file
            return True
        except Exception as e:
            logger.error(f"Failed to create .Xauthority file: {str(e)}")
            return False
    return True

# Attempt to create X11 auth cookie for the current display
def create_x11_auth_cookie():
    """Create X11 authentication cookie for the current display"""
    if not DISPLAY_AVAILABLE:
        return False
        
    try:
        display = os.environ.get('DISPLAY', '')
        logger.info(f"Creating X11 auth cookie for display {display}")
        
        # Extract display number
        if display and display.startswith(':'):
            display_num = display[1:]
            # Create MIT-MAGIC-COOKIE for this display
            cookie = subprocess.check_output("openssl rand -hex 16", shell=True).decode('utf-8').strip()
            
            # Create or update .Xauthority file
            xauth_path = os.path.expanduser('~/.Xauthority')
            cmd = f"touch {xauth_path} && xauth add {display} MIT-MAGIC-COOKIE-1 {cookie}"
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Added auth cookie for display {display}")
            return True
    except Exception as e:
        logger.error(f"Error creating X11 auth cookie: {str(e)}")
        return False

# Set XAUTHORITY to point to a valid file if necessary
def setup_x11_auth():
    """Set up X11 authentication environment"""
    if not DISPLAY_AVAILABLE:
        return False
        
    # Make sure .Xauthority exists
    if not create_xauth_file():
        logger.error("Failed to create .Xauthority file")
        return False
        
    # Set XAUTHORITY environment variable
    xauth_path = os.path.expanduser('~/.Xauthority')
    os.environ['XAUTHORITY'] = xauth_path
    
    # Try to add an auth cookie
    try:
        if create_x11_auth_cookie():
            logger.info("X11 authentication set up successfully")
        else:
            logger.warning("X11 authentication cookie creation failed")
    except Exception as e:
        logger.warning(f"Could not create auth cookie: {str(e)}")
    
    return True

# Try to set up virtual display if needed
def ensure_display():
    """Ensure a display is available, setting up virtual if necessary"""
    global DISPLAY_AVAILABLE, VIRTUAL_DISPLAY, HEADLESS
    
    if DISPLAY_AVAILABLE:
        logger.info(f"Display detected: {os.environ.get('DISPLAY')}")
        # Set up X11 authentication
        setup_x11_auth()
        return True
    
    try:
        logger.info("No display detected, attempting to set up Xvfb virtual display")
        # Check if xvfb is available
        result = subprocess.run(['which', 'Xvfb'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Xvfb not found - unable to create virtual display")
            return False
            
        # Find an available display number
        for display_num in range(99, 120):
            check_cmd = f"lsof -i :{6000+display_num} || true"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)
            if result.returncode != 0 or not result.stdout.strip():
                # This display number is available
                display = f":{display_num}"
                # Start Xvfb with access control disabled
                cmd = f"Xvfb {display} -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &"
                subprocess.run(cmd, shell=True, check=True)
                # Wait for Xvfb to start
                time.sleep(1)
                # Set environment variable
                os.environ['DISPLAY'] = display
                # Set up X11 auth
                setup_x11_auth()
                DISPLAY_AVAILABLE = True
                VIRTUAL_DISPLAY = True
                HEADLESS = False
                logger.info(f"Virtual display created on {display}")
                return True
        
        logger.error("Failed to create virtual display - no available display numbers")
        return False
        
    except Exception as e:
        logger.error(f"Error setting up virtual display: {str(e)}")
        return False

# Configure environment for X11/display
DISPLAY_CONFIGURED = ensure_display()

# Only import GUI libraries if display is available
CV2_AVAILABLE = False
PYAUTOGUI_AVAILABLE = False
PYNPUT_AVAILABLE = False
PIL_AVAILABLE = False

if DISPLAY_CONFIGURED:
    try:
        import cv2
        CV2_AVAILABLE = True
        logger.info("OpenCV imported successfully")
    except ImportError:
        logger.warning("Failed to import OpenCV (cv2)")
    
    try:
        import pyautogui
        PYAUTOGUI_AVAILABLE = True
        logger.info("PyAutoGUI imported successfully")
    except ImportError:
        logger.warning("Failed to import PyAutoGUI")
    
    try:
        from pynput import mouse, keyboard
        PYNPUT_AVAILABLE = True
        logger.info("Pynput imported successfully")
    except ImportError:
        logger.warning("Failed to import Pynput")
    
    try:
        from PIL import Image
        PIL_AVAILABLE = True
        logger.info("PIL imported successfully")
    except ImportError:
        logger.warning("Failed to import PIL")

# Always import the ML system
try:
    from ml_system import MLSystem
    ML_AVAILABLE = True
except ImportError:
    logger.warning("Failed to import MLSystem")
    ML_AVAILABLE = False

class SensoryMotorSystem:
    def __init__(self):
        """Initialize the sensory-motor system with enhanced 3D spatial awareness capabilities"""
        self.logger = logging.getLogger(__name__)
        self.headless = not DISPLAY_AVAILABLE
        
        # Initialize activity logging
        self.echo_dir = Path.home() / '.deep_tree_echo'
        self.sensory_dir = self.echo_dir / 'sensory'
        self.sensory_dir.mkdir(parents=True, exist_ok=True)
        self.activity_file = self.sensory_dir / 'activity.json'
        self.activities = []
        self._load_activities()
        
        # Initialize interaction parameters
        self.typing_speed = {
            'min': 0.1,  # Minimum delay between keystrokes
            'max': 0.3,  # Maximum delay between keystrokes
            'variance': 0.05  # Random variance in timing
        }
        
        self.mouse_speed = {
            'min': 0.3,  # Minimum movement duration
            'max': 2.0,  # Maximum movement duration
            'variance': 0.1  # Random variance in timing
        }
        
        # 3D spatial awareness parameters
        self.spatial_awareness = {
            'depth_perception': 0.8,  # 0.0 to 1.0, higher means better depth perception
            'field_of_view': 110,  # degrees
            'peripheral_vision': 0.7,  # 0.0 to 1.0, higher means better peripheral vision
            'spatial_memory': 0.85,  # 0.0 to 1.0, higher means better spatial memory
            'motion_tracking': 0.9,  # 0.0 to 1.0, higher means better tracking of moving objects
        }
        
        # Initialize state tracking
        self.last_mouse_pos = self._get_mouse_position()
        self.last_action_time = time.time()
        
        # Frame buffer for 3D environment perception
        self.frame_buffer = []
        self.frame_buffer_size = 5  # Store last 5 frames for motion analysis
        
        # 3D spatial memory (simple implementation)
        self.spatial_memory = {}  # Maps object IDs to last known positions
        
        # Initialize ML system if available
        self.ml = MLSystem() if ML_AVAILABLE else None
        
        # Configure GUI components if available
        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1  # Add small delays between actions
        
        self.logger.info(f"Sensory-Motor System initialized with 3D capabilities (headless={self.headless})")
    
    def _get_mouse_position(self) -> Tuple[int, int]:
        """Safely get mouse position"""
        if not PYAUTOGUI_AVAILABLE:
            return (0, 0)
        try:
            return pyautogui.position()
        except Exception as e:
            self.logger.error(f"Error getting mouse position: {str(e)}")
            return (0, 0)
    
    def _load_activities(self):
        """Load existing activities"""
        if self.activity_file.exists():
            try:
                with open(self.activity_file) as f:
                    self.activities = json.load(f)
            except:
                self.activities = []
                
    def _save_activities(self):
        """Save activities to file"""
        with open(self.activity_file, 'w') as f:
            json.dump(self.activities[-1000:], f)
            
    def _log_activity(self, description: str, data: Optional[Dict] = None):
        """Log a sensory activity"""
        activity = {
            'time': time.time(),
            'description': description,
            'data': data or {}
        }
        self.activities.append(activity)
        self._save_activities()
        
    async def process_all(self) -> Dict:
        """Process all sensory inputs (async-compatible)"""
        self._log_activity("Processing sensory inputs")
        if DISPLAY_AVAILABLE:
            try:
                result = self.process_input()
                return result
            except Exception as e:
                self.logger.error(f"Error in process_all: {str(e)}")
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "skipped", "reason": "display unavailable"}

    def capture_screen(self, region=None) -> Union[np.ndarray, None]:
        """Capture the screen or a specific region with depth simulation for 3D environments"""
        if not PYAUTOGUI_AVAILABLE or not CV2_AVAILABLE:
            self._log_activity("Screen capture attempted but required libraries unavailable")
            return None
            
        try:
            screenshot = pyautogui.screenshot(region=region)
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Add to frame buffer for motion analysis
            self.frame_buffer.append(frame)
            if len(self.frame_buffer) > self.frame_buffer_size:
                self.frame_buffer.pop(0)
                
            return frame
        except Exception as e:
            self.logger.error(f"Error capturing screen: {str(e)}")
            return None
    
    def process_input(self) -> Dict:
        """Process sensory input with 3D spatial awareness"""
        if not DISPLAY_AVAILABLE:
            self._log_activity("Input processing skipped - display unavailable")
            return {"status": "skipped", "reason": "display unavailable"}
            
        try:
            # Capture screen for visual processing
            frame = self.capture_screen()
            results = {"status": "processing"}
            
            if frame is not None:
                self._log_activity("Captured screen frame")
                
                # Basic motion detection if we have enough frames
                if len(self.frame_buffer) >= 2:
                    motion_data = self.detect_motion()
                    if motion_data['motion_detected']:
                        self._log_activity("Motion detected", motion_data)
                        results["motion"] = motion_data
                
                # Object detection simulation (would use ML models in a real implementation)
                if self.ml is not None:
                    # Simulated object detection
                    objects = self.simulate_object_detection(frame)
                    if objects:
                        self._log_activity("Objects detected", {"objects": objects})
                        results["objects"] = objects
                        
                        # Update spatial memory with object positions
                        self.update_spatial_memory(objects)
                
            # Track mouse movement
            mouse_pos = self._get_mouse_position()
            if mouse_pos != self.last_mouse_pos:
                self._log_activity(
                    "Mouse movement",
                    {'from': self.last_mouse_pos, 'to': mouse_pos}
                )
                self.last_mouse_pos = mouse_pos
                results["mouse_moved"] = True
                
            results["status"] = "processed"
            return results
            
        except Exception as e:
            self._log_activity("Error processing input", {'error': str(e)})
            self.logger.error(f"Error processing input: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def detect_motion(self) -> Dict:
        """Detect motion between frames in the buffer"""
        if len(self.frame_buffer) < 2 or not CV2_AVAILABLE:
            return {"motion_detected": False}
            
        try:
            # Get the two most recent frames
            prev_frame = self.frame_buffer[-2]
            curr_frame = self.frame_buffer[-1]
            
            # Convert to grayscale
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate absolute difference
            frame_diff = cv2.absdiff(prev_gray, curr_gray)
            
            # Apply threshold
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter significant contours
            significant_contours = [c for c in contours if cv2.contourArea(c) > 100]
            
            # Calculate motion regions
            motion_regions = []
            for contour in significant_contours:
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append({"x": int(x), "y": int(y), "width": int(w), "height": int(h)})
            
            motion_detected = len(significant_contours) > 0
            
            return {
                "motion_detected": motion_detected,
                "motion_count": len(significant_contours),
                "motion_regions": motion_regions
            }
            
        except Exception as e:
            self.logger.error(f"Error in motion detection: {str(e)}")
            return {"motion_detected": False, "error": str(e)}
    
    def simulate_object_detection(self, frame: np.ndarray) -> List[Dict]:
        """
        Simulate object detection for 3D environments
        
        In a real implementation, this would use ML models for object detection,
        but this is a simplified placeholder that returns simulated data
        """
        # This is a simulation - in reality would use CV models
        objects = []
        
        # Simulate detection of random objects (for demonstration)
        object_classes = ["player", "wall", "door", "item", "obstacle", "enemy"]
        for _ in range(random.randint(0, 5)):
            obj_class = random.choice(object_classes)
            obj_id = f"{obj_class}_{random.randint(1000, 9999)}"
            
            # Generate random position (would be actual detection in real implementation)
            x = random.randint(0, frame.shape[1])
            y = random.randint(0, frame.shape[0])
            w = random.randint(20, 200)
            h = random.randint(20, 200)
            
            # Simulated depth (distance from camera)
            depth = random.uniform(1.0, 10.0)
            
            objects.append({
                "id": obj_id,
                "class": obj_class,
                "position": {"x": x, "y": y, "width": w, "height": h},
                "depth": depth,
                "confidence": random.uniform(0.7, 0.99)
            })
            
        return objects
    
    def update_spatial_memory(self, objects: List[Dict]):
        """Update the spatial memory with detected objects"""
        for obj in objects:
            obj_id = obj["id"]
            position = obj["position"]
            position["depth"] = obj["depth"]  # Add depth for 3D awareness
            
            # Calculate 3D position (simplified)
            x = position["x"] + position["width"] / 2
            y = position["y"] + position["height"] / 2
            z = position["depth"]
            
            # Update spatial memory
            if obj_id in self.spatial_memory:
                # Object previously seen, calculate movement
                prev_pos = self.spatial_memory[obj_id]["position"]
                dx = x - prev_pos["x"]
                dy = y - prev_pos["y"]
                dz = z - prev_pos["z"]
                
                velocity = {
                    "dx": dx,
                    "dy": dy,
                    "dz": dz,
                    "speed": np.sqrt(dx*dx + dy*dy + dz*dz)
                }
                
                self.spatial_memory[obj_id] = {
                    "position": {"x": x, "y": y, "z": z},
                    "class": obj["class"],
                    "last_seen": time.time(),
                    "velocity": velocity
                }
            else:
                # New object
                self.spatial_memory[obj_id] = {
                    "position": {"x": x, "y": y, "z": z},
                    "class": obj["class"],
                    "last_seen": time.time(),
                    "velocity": {"dx": 0, "dy": 0, "dz": 0, "speed": 0}
                }
    
    def predict_object_position(self, obj_id: str, time_delta: float) -> Dict:
        """Predict future position of an object based on its velocity"""
        if obj_id not in self.spatial_memory:
            return None
            
        obj = self.spatial_memory[obj_id]
        pos = obj["position"]
        vel = obj["velocity"]
        
        # Simple linear prediction
        predicted_pos = {
            "x": pos["x"] + vel["dx"] * time_delta,
            "y": pos["y"] + vel["dy"] * time_delta,
            "z": pos["z"] + vel["dz"] * time_delta
        }
        
        return {
            "current": pos,
            "predicted": predicted_pos,
            "time_delta": time_delta
        }
    
    def simulate_depth_perception(self, frame: np.ndarray) -> np.ndarray:
        """
        Simulate depth perception for 3D environments
        
        In a real implementation, this would use stereo vision or ML models,
        but this is a simplified version that returns a simulated depth map
        """
        if not CV2_AVAILABLE:
            return None
            
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Create a simple simulated depth map based on intensity gradients
            # (This is just a placeholder - real depth estimation is much more complex)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Calculate gradient magnitude
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            
            # Normalize to 0-1 range
            magnitude = cv2.normalize(magnitude, None, 0, 1, cv2.NORM_MINMAX)
            
            # Create simulated depth map (inverted gradient - stronger edges closer)
            depth_map = 1 - magnitude
            
            return depth_map
            
        except Exception as e:
            self.logger.error(f"Error in depth perception simulation: {str(e)}")
            return None

# If run as main script, perform a simple test
if __name__ == "__main__":
    print(f"X11 Display Status: {'Available' if DISPLAY_AVAILABLE else 'Not Available'}")
    print(f"Virtual Display: {VIRTUAL_DISPLAY}")
    print(f"Display: {os.environ.get('DISPLAY', 'Not Set')}")
    print(f"OpenCV Available: {CV2_AVAILABLE}")
    print(f"PyAutoGUI Available: {PYAUTOGUI_AVAILABLE}")
    print(f"Pynput Available: {PYNPUT_AVAILABLE}")
    print(f"PIL Available: {PIL_AVAILABLE}")
    print(f"ML System Available: {ML_AVAILABLE}")
    
    # Initialize sensory system
    sensory = SensoryMotorSystem()
    print(f"Sensory Motor System initialized in {'headless' if sensory.headless else 'display'} mode")
    
    # Capture one frame if possible
    if CV2_AVAILABLE and PYAUTOGUI_AVAILABLE:
        print("Attempting to capture one frame...")
        frame = sensory.capture_screen()
        if frame is not None:
            print(f"Successfully captured frame with shape {frame.shape}")
            
            # Save a test image
            test_path = Path.home() / 'sensory_test_capture.png'
            cv2.imwrite(str(test_path), frame)
            print(f"Test image saved to {test_path}")
        else:
            print("Failed to capture frame")
    else:
        print("Frame capture not available - missing required libraries")
