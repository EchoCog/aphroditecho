import os
import time
import logging
import cv2
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import numpy as np
from PIL import Image
import io
from urllib.parse import urlparse
import base64
from dotenv import load_dotenv
from deep_tree_echo import DeepTreeEcho, TreeNode
import requests
from datetime import datetime
import json

# Import session manager for automatic conversation saving
try:
    from chat_session_manager import (session_manager, ChatPlatform, 
                                     log_chat_message, create_chat_session)
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False
    logging.warning("Session manager not available - conversations won't be auto-saved")

# Create templates directory
os.makedirs('templates', exist_ok=True)

load_dotenv()

class SeleniumInterface:
    def __init__(self):
        """Initialize the ChatGPT interface with advanced capabilities"""
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.echo_system = DeepTreeEcho(echo_threshold=0.75)
        self.conversation_history = []
        self.session_start_time = datetime.now()
        self.last_action_time = time.time()
        self.memory_file = os.path.join("activity_logs", "browser", "chat_memory.json")
        
        # Session management for automatic conversation saving
        self.chat_session_id = None
        self.auto_save_enabled = SESSION_MANAGER_AVAILABLE
        
        # Ensure memory directory exists
        os.makedirs(os.path.join("activity_logs", "browser"), exist_ok=True)
        
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Initialize session manager if available
        if SESSION_MANAGER_AVAILABLE:
            try:
                self.chat_session_id = create_chat_session(
                    "browser", 
                    f"Browser Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                self.logger.info(f"Created browser chat session: {self.chat_session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize session manager: {str(e)}")
                self.auto_save_enabled = False
        
        # User simulation settings for more human-like behavior
        self.typing_speed_wpm = random.randint(30, 80)  # Words per minute
        self.human_delay_min = 0.1  # Minimum delay between actions
        self.human_delay_max = 1.0  # Maximum delay between actions
        
    def find_existing_browser(self):
        """Try to find an existing browser with ChatGPT open"""
        try:
            # Try different debugging ports
            ports = [9222, 9223, 9224, 9225]
            for port in ports:
                try:
                    browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
                    for context in browser.contexts:
                        for page in context.pages:
                            parsed_url = urlparse(page.url)
                            if parsed_url.hostname and (parsed_url.hostname == "chatgpt.com" or parsed_url.hostname.endswith(".chatgpt.com")):
                                self.browser = browser
                                self.page = page
                                self.logger.info(f"Connected to existing ChatGPT session on port {port}")
                                return True
                except Exception:
                    continue
        except Exception as e:
            self.logger.debug(f"Error finding existing browser: {str(e)}")
        return False
    
    def init(self):
        """Initialize the browser with anti-detection measures"""
        try:
            self.playwright = sync_playwright().start()
            
            # First try to find existing browser
            if self.find_existing_browser():
                return True
            
            self.logger.info("No existing browser session found, creating new one...")
            
            # Use the dedicated chrome user data directory for persistence
            user_data_dir = os.path.join(os.getcwd(), 'chrome_user_data')
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Create new browser context with more robust settings
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--remote-debugging-port=9222',
                    '--disable-features=IsolateOrigins,site-per-process',  # For dealing with iframes
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'  # Modern user agent
                ],
                ignore_https_errors=True,
                viewport={"width": 1920, "height": 1080}
            )
            
            # Get or create page
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            
            # Set default timeout and viewport
            self.page.set_default_timeout(60000)
            
            # Add advanced stealth scripts to avoid detection
            self.page.add_init_script("""
                // Overwrite the 'chrome' property to avoid detection
                Object.defineProperty(window, 'chrome', {
                    value: new Proxy({}, {
                        get: function(target, name) {
                            if (name === 'runtime') return {};
                            return function() {};
                        }
                    })
                });
                
                // Modify navigator properties
                const originalNavigator = window.navigator;
                const navigatorProxy = new Proxy(originalNavigator, {
                    get: function(target, name) {
                        switch (name) {
                            case 'webdriver':
                                return undefined;
                            case 'languages':
                                return ['en-US', 'en'];
                            case 'plugins':
                                return [
                                    {description: 'PDF Viewer', filename: 'internal-pdf-viewer'},
                                    {description: 'Chrome PDF Viewer', filename: 'chrome-pdf-viewer'},
                                    {description: 'Chromium PDF Viewer', filename: 'chromium-pdf-viewer'},
                                    {description: 'Microsoft Edge PDF Viewer', filename: 'edge-pdf-viewer'},
                                    {description: 'WebKit built-in PDF', filename: 'webkit-pdf-viewer'}
                                ];
                            default:
                                return typeof target[name] === 'function' ? target[name].bind(target) : target[name];
                        }
                    }
                });
                Object.defineProperty(window, 'navigator', {
                    value: navigatorProxy
                });
                
                // Overwrite permissions
                const originalPermissions = window.Permissions;
                window.Permissions = {
                    query: async () => { return { state: 'granted', onchange: null }; }
                };
                
                // Add fake canvas fingerprinting
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    if (window.canvas_fingerprint_warned) return originalToDataURL.apply(this, arguments);
                    const canvas = this;
                    window.canvas_fingerprint_warned = true;
                    return originalToDataURL.apply(canvas, arguments);
                };
            """)
            
            # Set up page event listeners
            self._setup_event_listeners()
            
            # Navigate to chat page only if needed
            if "chat.openai.com" not in self.page.url and "chatgpt.com" not in self.page.url:
                self.logger.info("Navigating to chat page...")
                
                # Try navigation with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.page.goto("https://chat.openai.com", wait_until="networkidle")
                        self.logger.info(f"Current URL: {self.page.url}")
                        
                        # Handle Cloudflare
                        if not self.wait_for_cloudflare():
                            if attempt < max_retries - 1:
                                self.logger.warning(f"Cloudflare challenge failed, attempt {attempt + 1}/{max_retries}")
                                time.sleep(5)
                                continue
                            else:
                                self.logger.error("Failed to pass Cloudflare challenge after all retries")
                                return False
                        
                        # Additional waits for page stability
                        self._wait_for_page_stability()
                        
                        break  # Success
                        
                    except Exception as e:
                        self.logger.error(f"Navigation attempt {attempt + 1} failed: {str(e)}")
                        if attempt < max_retries - 1:
                            self._simulate_human_delay()
                        else:
                            raise
            
            # Load previous conversation history
            self._load_memory()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            if self.page:
                self.page.screenshot(path="init_error.png")
            return False
    
    def _setup_event_listeners(self):
        """Set up event listeners for monitoring page activities"""
        # Listen for console messages
        self.page.on("console", lambda msg: self._handle_console_message(msg))
        
        # Listen for page errors
        self.page.on("pageerror", lambda err: self.logger.error(f"Page error: {err}"))
        
        # Listen for dialog events
        self.page.on("dialog", lambda dialog: self._handle_dialog(dialog))
        
        # Listen for navigation events
        self.page.on("framenavigated", lambda frame: self._handle_navigation(frame))
    
    def _handle_console_message(self, msg):
        """Handle console messages from the page"""
        if msg.type == "error":
            self.logger.warning(f"Console error: {msg.text}")
        elif "cloudflare" in msg.text.lower():
            self.logger.info(f"Cloudflare related message: {msg.text}")
    
    def _handle_dialog(self, dialog):
        """Handle dialogs like alerts, confirms, and prompts"""
        self.logger.info(f"Dialog: {dialog.type} - {dialog.message}")
        
        # Accept all dialogs
        if dialog.type == "confirm" or dialog.type == "beforeunload":
            dialog.accept()
        else:
            dialog.dismiss()
    
    def _handle_navigation(self, frame):
        """Handle page navigations"""
        if frame == self.page.main_frame:
            self.logger.info(f"Navigated to: {frame.url}")
            
            # Check for Cloudflare
            if "cloudflare" in frame.url.lower() or "challenge" in frame.url.lower():
                self.logger.info("Detected Cloudflare navigation, waiting...")
    
    def find_element_by_image(self, template_path, threshold=0.8):
        """Find an element on the page by matching a template image
        
        Args:
            template_path (str): Path to the template image file
            threshold (float): Matching threshold (0-1), higher is more strict
            
        Returns:
            tuple: (x, y) coordinates of the match, or None if not found
        """
        try:
            # Take screenshot of the page
            screenshot_bytes = self.page.screenshot(type="png")
            
            # Convert bytes to OpenCV format
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Load the template
            template = cv2.imread(template_path)
            
            if template is None:
                self.logger.error(f"Could not load template image: {template_path}")
                return None
                
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Get the center point of the match
                h, w = template.shape[:2]
                center_x = max_loc[0] + w//2
                center_y = max_loc[1] + h//2
                
                self.logger.info(f"Found match for {template_path} at ({center_x}, {center_y}) with confidence {max_val}")
                return (center_x, center_y)
            else:
                self.logger.debug(f"No match found for {template_path} (best match: {max_val})")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in visual search: {str(e)}")
            return None
    
    def _simulate_human_delay(self, min_delay=None, max_delay=None):
        """Simulate a human-like delay between actions"""
        if min_delay is None:
            min_delay = self.human_delay_min
        if max_delay is None:
            max_delay = self.human_delay_max
            
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        return delay
    
    def _calculate_typing_delay(self, text):
        """Calculate a human-like typing delay for the given text"""
        # Average word length in English is ~5 characters
        char_count = len(text)
        word_count = char_count / 5
        
        # Calculate time in minutes, then convert to seconds
        minutes = word_count / self.typing_speed_wpm
        seconds = minutes * 60
        
        # Add some randomness
        seconds = seconds * random.uniform(0.8, 1.2)
        
        return seconds
    
    def _human_like_type(self, element, text):
        """Type text in a human-like manner with variable speed and occasional mistakes"""
        if not text:
            return
            
        # Clear the field
        element.click()
        element.press("Control+A")
        element.press("Backspace")
        
        # Calculate overall time needed for typing
        total_time = self._calculate_typing_delay(text)
        per_char_time = total_time / len(text)
        
        typed_text = ""
        for i, char in enumerate(text):
            # Occasional typo with immediate correction (1% chance)
            if random.random() < 0.01:
                # Choose a random adjacent key on keyboard
                typo_chars = "qwertyuiopasdfghjklzxcvbnm"
                wrong_char = random.choice(typo_chars)
                
                # Type wrong character
                element.type(wrong_char)
                typed_text += wrong_char
                
                # Brief pause to "notice" error
                self._simulate_human_delay(0.1, 0.3)
                
                # Delete wrong character
                element.press("Backspace")
                typed_text = typed_text[:-1]
            
            # Type the correct character
            element.type(char)
            typed_text += char
            
            # Occasional pause (5% chance)
            if random.random() < 0.05:
                self._simulate_human_delay(0.3, 1.0)
            else:
                # Normal typing rhythm
                char_delay = per_char_time * random.uniform(0.5, 1.5)
                time.sleep(char_delay)
    
    def _wait_for_page_stability(self):
        """Wait for the page to become stable"""
        try:
            self.page.wait_for_load_state("networkidle", timeout=30000)
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            self.page.wait_for_load_state("load", timeout=10000)
            
            # Wait for any animations to complete
            self._simulate_human_delay(1.0, 2.0)
            
            return True
        except Exception as e:
            self.logger.warning(f"Page stability wait error: {str(e)}")
            return False
    
    def _load_memory(self):
        """Load conversation memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.conversation_history = json.load(f)
                self.logger.info(f"Loaded {len(self.conversation_history)} previous conversations")
        except Exception as e:
            self.logger.error(f"Error loading memory: {str(e)}")
    
    def _save_memory(self):
        """Save conversation memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving memory: {str(e)}")
            
    def click_by_vision(self, template_path, threshold=0.8):
        """Click an element using computer vision
        
        Args:
            template_path (str): Path to the template image
            threshold (float): Matching threshold (0-1)
            
        Returns:
            bool: True if clicked successfully, False otherwise
        """
        try:
            coords = self.find_element_by_image(template_path, threshold)
            if coords:
                x, y = coords
                
                # Move mouse in a human-like way
                self._human_like_mouse_movement(x, y)
                
                self.page.mouse.click(x, y)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error clicking by vision: {str(e)}")
            return False
    
    def _human_like_mouse_movement(self, target_x, target_y):
        """Move the mouse to target position in a human-like manner"""
        try:
            # Get current position
            current_pos = self.page.evaluate("""() => { 
                return {x: window.mousePosX || 0, y: window.mousePosY || 0}
            }""")
            
            current_x = current_pos.get('x', 0)
            current_y = current_pos.get('y', 0)
            
            # Create a curved path with slight randomness
            # Using Bezier curve approximation with control points
            start_x, start_y = current_x, current_y
            end_x, end_y = target_x, target_y
            
            # Calculate distance
            distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
            
            # Determine number of steps based on distance
            steps = max(10, min(int(distance / 10), 100))
            
            # Generate control point(s) with some randomness
            control_x = (start_x + end_x) / 2 + random.uniform(-distance/4, distance/4)
            control_y = (start_y + end_y) / 2 + random.uniform(-distance/4, distance/4)
            
            # Create the movement path
            for step in range(1, steps + 1):
                t = step / steps
                
                # Quadratic Bezier calculation
                px = (1-t)*(1-t)*start_x + 2*(1-t)*t*control_x + t*t*end_x
                py = (1-t)*(1-t)*start_y + 2*(1-t)*t*control_y + t*t*end_y
                
                # Add small random movement
                px += random.uniform(-2, 2)
                py += random.uniform(-2, 2)
                
                # Move to this position
                self.page.mouse.move(px, py)
                
                # Record position for future movements
                self.page.evaluate(f"""() => {{ 
                    window.mousePosX = {px}; 
                    window.mousePosY = {py}; 
                }}""")
                
                # Wait a small amount before next movement
                time.sleep(random.uniform(0.001, 0.01))
                
        except Exception as e:
            self.logger.warning(f"Error in human-like mouse movement: {str(e)}")
            # Fall back to direct movement
            self.page.mouse.move(target_x, target_y)
            
    def authenticate(self):
        """Authenticate with ChatGPT using username and password"""
        try:
            username = os.getenv("CHAT_USERNAME")
            password = os.getenv("CHAT_PASSWORD")
            
            if not username or not password:
                self.logger.error("CHAT_USERNAME or CHAT_PASSWORD not found in environment")
                return False
                
            # Check if already authenticated by looking for chat UI
            try:
                # Try to locate chat input
                input_selectors = [
                    'textarea[placeholder*="Message"]',
                    'textarea[placeholder*="Send a message"]',
                    '[role="textbox"]',
                    '#prompt-textarea'
                ]
                
                for selector in input_selectors:
                    try:
                        chat_input = self.page.wait_for_selector(selector, timeout=3000)
                        if chat_input:
                            self.logger.info("Already authenticated")
                            return True
                    except:
                        continue
            except:
                pass
                
            # Load login page directly
            self.page.goto("https://auth0.openai.com/u/login/identifier", wait_until="networkidle")
            self.logger.info("Loaded login page")
            self._wait_for_page_stability()
            
            # Fill in email with human-like typing
            email_selectors = [
                'input[name="username"]',
                'input[type="email"]',
                'input[placeholder*="email" i]'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        self.logger.info(f"Found email input with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                # Try vision-based approach
                if os.path.exists("templates/email_input.png"):
                    self.logger.info("Trying to find email input using vision")
                    coords = self.find_element_by_image("templates/email_input.png")
                    if coords:
                        x, y = coords
                        self.page.mouse.click(x, y)
                        email_input = self.page.wait_for_selector('input:focus')
            
            if not email_input:
                self.logger.error("Could not find email input field")
                self.page.screenshot(path="email_input_not_found.png")
                return False
            
            self._human_like_type(email_input, username)
            self.logger.info("Entered email")
            
            # Click continue button
            continue_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Continue")',
                'button:has-text("Next")'
            ]
            
            continue_button = None
            for selector in continue_button_selectors:
                try:
                    continue_button = self.page.wait_for_selector(selector, timeout=3000)
                    if continue_button:
                        self.logger.info(f"Found continue button with selector: {selector}")
                        break
                except:
                    continue
            
            if not continue_button:
                # Try vision-based approach
                if os.path.exists("templates/continue_button.png"):
                    self.logger.info("Trying to find continue button using vision")
                    if self.click_by_vision("templates/continue_button.png"):
                        continue_button = True
            
            if not continue_button:
                self.logger.error("Could not find continue button")
                self.page.screenshot(path="continue_button_not_found.png")
                return False
            
            if continue_button is not True:  # Skip if we already clicked via vision
                self._simulate_human_delay(0.5, 1.0)
                continue_button.click()
            
            self.logger.info("Clicked continue")
            self._wait_for_page_stability()
            
            # Fill in password with human-like typing
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.page.wait_for_selector(selector, timeout=10000)
                    if password_input:
                        self.logger.info(f"Found password input with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                # Try vision-based approach
                if os.path.exists("templates/password_input.png"):
                    self.logger.info("Trying to find password input using vision")
                    coords = self.find_element_by_image("templates/password_input.png")
                    if coords:
                        x, y = coords
                        self.page.mouse.click(x, y)
                        password_input = self.page.wait_for_selector('input:focus')
            
            if not password_input:
                self.logger.error("Could not find password input field")
                self.page.screenshot(path="password_input_not_found.png")
                return False
            
            self._human_like_type(password_input, password)
            self.logger.info("Entered password")
            
            # Click login button
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Continue")',
                'button:has-text("Log in")'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = self.page.wait_for_selector(selector, timeout=3000)
                    if login_button:
                        self.logger.info(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                # Try vision-based approach
                if os.path.exists("templates/login_button.png"):
                    self.logger.info("Trying to find login button using vision")
                    if self.click_by_vision("templates/login_button.png"):
                        login_button = True
            
            if not login_button:
                self.logger.error("Could not find login button")
                self.page.screenshot(path="login_button_not_found.png")
                return False
            
            if login_button is not True:  # Skip if we already clicked via vision
                self._simulate_human_delay(0.5, 1.0)
                login_button.click()
            
            self.logger.info("Clicked login")
            
            # Wait for chat interface with multiple retries
            chat_interface_found = False
            chat_input_selectors = [
                '[data-testid="chat-input"]',
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="Send a message"]',
                '[role="textbox"]',
                '#prompt-textarea'
            ]
            
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Wait for page to be fully loaded
                    self._wait_for_page_stability()
                    
                    # Check for Cloudflare
                    if "cloudflare" in self.page.url.lower() or "challenge" in self.page.url.lower():
                        self.logger.info("Detected Cloudflare page, waiting...")
                        self.wait_for_cloudflare()
                        self._wait_for_page_stability()
                    
                    # Try to find chat input
                    for selector in chat_input_selectors:
                        try:
                            chat_input = self.page.wait_for_selector(selector, timeout=5000)
                            if chat_input:
                                self.logger.info(f"Successfully found chat interface using selector: {selector}")
                                chat_interface_found = True
                                break
                        except:
                            continue
                    
                    if chat_interface_found:
                        break
                    
                    self.logger.warning(f"Chat interface not found on attempt {attempt + 1}, waiting...")
                    self._simulate_human_delay(2.0, 5.0)
                    
                except Exception as e:
                    self.logger.warning(f"Authentication check attempt {attempt + 1} error: {str(e)}")
                    self._simulate_human_delay(2.0, 5.0)
            
            if not chat_interface_found:
                self.logger.error("Failed to find chat interface after authentication")
                self.page.screenshot(path="chat_interface_not_found.png")
                return False
                
            self.logger.info("Successfully authenticated and found chat interface")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            self.page.screenshot(path="auth_error.png")
            return False
            
    def wait_for_cloudflare(self, max_retries=3):
        """Wait for Cloudflare challenge to complete"""
        try:
            self.logger.info("Checking for Cloudflare challenge...")
            
            # Check if we're on a Cloudflare page
            if "challenge" not in self.page.title().lower() and "cloudflare" not in self.page.content().lower():
                return True
                
            self.logger.info("Detected Cloudflare challenge, waiting...")
            
            # Wait for the challenge to complete
            for attempt in range(max_retries):
                try:
                    # First try automation-friendly approach
                    self.page.wait_for_function(
                        """() => {
                            return !document.title.toLowerCase().includes('cloudflare') && 
                                   !document.title.toLowerCase().includes('challenge') &&
                                   !document.title.toLowerCase().includes('checking');
                        }""",
                        timeout=30000
                    )
                    
                    # Additional wait for page to stabilize
                    self._wait_for_page_stability()
                    
                    self.logger.info("Cloudflare challenge completed")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Cloudflare wait attempt {attempt + 1} failed: {str(e)}")
                    
                    # For the last attempt, try some random mouse movement to help pass the check
                    if attempt == max_retries - 1:
                        self.logger.info("Trying mouse movement to pass Cloudflare check")
                        for _ in range(5):
                            x = random.randint(100, 1000)
                            y = random.randint(100, 600)
                            self._human_like_mouse_movement(x, y)
                            self._simulate_human_delay(1.0, 3.0)
                            
                            # Try scrolling
                            self.page.evaluate("window.scrollBy(0, 100)")
                            self._simulate_human_delay(1.0, 2.0)
                            self.page.evaluate("window.scrollBy(0, -50)")
                    
                    if attempt < max_retries - 1:
                        self._simulate_human_delay(5.0, 10.0)  # Longer wait before retrying
                    else:
                        raise
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for Cloudflare: {str(e)}")
            self.page.screenshot(path="cloudflare_error.png")
            return False
    
    def send_message(self, message):
        """Send a message to the chat and store the conversation"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get current URL and check if we need to navigate
                self.logger.info(f"Current URL before sending message: {self.page.url}")
                parsed_url = urlparse(self.page.url)
                if not (parsed_url.hostname == "chat.openai.com" or parsed_url.hostname == "chatgpt.com"):
                    self.logger.info("Not on chat page, navigating...")
                    self.page.goto("https://chat.openai.com", wait_until="networkidle")
                    self.logger.info(f"Navigated to: {self.page.url}")
                    
                    # Handle Cloudflare if needed
                    if not self.wait_for_cloudflare():
                        if attempt < max_retries - 1:
                            self.logger.warning(f"Cloudflare challenge failed, attempt {attempt + 1}/{max_retries}")
                            self._simulate_human_delay(5.0, 10.0)
                            continue
                        else:
                            self.logger.error("Failed to pass Cloudflare challenge after all retries")
                            return None
                
                self.logger.info("Waiting for page to be ready...")
                self._wait_for_page_stability()
                
                # Try different selectors for the chat input
                input_selectors = [
                    'textarea[placeholder*="Message"]',
                    'textarea[placeholder*="Send a message"]',
                    '[role="textbox"]',
                    'div[contenteditable="true"]',
                    '[data-testid="chat-input"]',
                    '#prompt-textarea',
                    'div[class*="input"]',
                    'div[class*="chat"] textarea'
                ]
                
                chat_input = None
                for selector in input_selectors:
                    try:
                        self.logger.info(f"Trying selector: {selector}")
                        chat_input = self.page.wait_for_selector(selector, timeout=10000, state="visible")
                        if chat_input:
                            self.logger.info(f"Found input using selector: {selector}")
                            break
                    except Exception as e:
                        self.logger.info(f"Selector {selector} failed: {str(e)}")
                
                if not chat_input:
                    # Try vision-based approach
                    if os.path.exists("templates/chat_input.png"):
                        self.logger.info("Trying to find chat input using vision")
                        coords = self.find_element_by_image("templates/chat_input.png")
                        if coords:
                            x, y = coords
                            self.page.mouse.click(x, y)
                            chat_input = self.page.wait_for_selector('textarea:focus')
                
                if not chat_input:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Could not find chat input, attempt {attempt + 1}/{max_retries}")
                        self.page.screenshot(path=f"chat_input_error_{attempt + 1}.png")
                        self._simulate_human_delay(5.0, 10.0)
                        continue
                    else:
                        self.logger.error("Could not find chat input after all retries")
                        self.page.screenshot(path="no_input.png")
                        return None
                
                # Type the message in a human-like manner
                self._human_like_type(chat_input, message)
                self._simulate_human_delay(0.5, 1.0)
                
                # Log user message to session manager if available
                if self.auto_save_enabled and self.chat_session_id:
                    try:
                        log_chat_message(
                            session_id=self.chat_session_id,
                            role="user",
                            content=message,
                            metadata={
                                "url": self.page.url,
                                "platform": "browser",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to log user message to session manager: {str(e)}")
                
                # Send the message (try different methods)
                try:
                    # First try pressing Enter
                    chat_input.press("Enter")
                except Exception:
                    try:
                        # Then try looking for a send button
                        send_button_selectors = [
                            'button[aria-label="Send message"]',
                            'button svg[data-icon="paper-plane"]',
                            'button.send-button'
                        ]
                        
                        for selector in send_button_selectors:
                            try:
                                send_button = self.page.wait_for_selector(selector, timeout=3000)
                                if send_button:
                                    self._simulate_human_delay(0.2, 0.5)
                                    send_button.click()
                                    break
                            except:
                                continue
                    except Exception:
                        # Last resort, try pressing Enter again
                        chat_input.press("Enter")
                
                # Record message send time
                message_time = datetime.now().isoformat()
                
                # Wait for response to start
                response_selectors = [
                    '[data-message-author="assistant"]',
                    '.message-content .markdown',
                    '.assistant-message'
                ]
                
                response_elem = None
                response_text = None
                
                for selector in response_selectors:
                    try:
                        response_elem = self.page.wait_for_selector(selector, timeout=30000)
                        if response_elem:
                            self.logger.info(f"Found response using selector: {selector}")
                            break
                    except Exception as e:
                        self.logger.info(f"Response selector {selector} failed: {str(e)}")
                
                if not response_elem:
                    self.logger.warning("Could not detect response element")
                else:
                    # Wait for the response to complete
                    try:
                        # Wait for assistant typing indicator to disappear
                        try:
                            self.page.wait_for_function(
                                """() => {
                                    // Look for typing indicators or "thinking" states
                                    return !document.querySelector('.typing-indicator') &&
                                           !document.querySelector('.loading-indicator') &&
                                           !document.querySelector('[data-state="thinking"]');
                                }""",
                                timeout=60000
                            )
                        except Exception as e:
                            self.logger.warning(f"Could not detect response completion: {str(e)}")
                        
                        # Get response content
                        response_text = response_elem.text_content()
                    except Exception as e:
                        self.logger.warning(f"Error getting response text: {str(e)}")
                
                # Store conversation
                conversation_entry = {
                    "timestamp": message_time,
                    "message": message,
                    "response": response_text,
                    "url": self.page.url
                }
                
                self.conversation_history.append(conversation_entry)
                self._save_memory()
                
                # Log assistant response to session manager if available
                if self.auto_save_enabled and self.chat_session_id and response_text:
                    try:
                        log_chat_message(
                            session_id=self.chat_session_id,
                            role="assistant",
                            content=response_text,
                            metadata={
                                "url": self.page.url,
                                "platform": "browser",
                                "timestamp": datetime.now().isoformat(),
                                "response_time": datetime.now().isoformat()
                            }
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to log assistant response to session manager: {str(e)}")
                
                self.logger.info(f"Successfully processed message. Response length: {len(response_text) if response_text else 0}")
                
                # Update the last action time
                self.last_action_time = time.time()
                
                return response_text
                
            except Exception as e:
                self.logger.error(f"Error in send_message attempt {attempt + 1}: {str(e)}")
                self.page.screenshot(path=f"send_error_{attempt + 1}.png")
                if attempt < max_retries - 1:
                    self._simulate_human_delay(5.0, 10.0)
                else:
                    return None
        
        return None
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history
    
    def get_last_response(self):
        """Get the most recent response from ChatGPT"""
        if self.conversation_history:
            return self.conversation_history[-1].get('response')
        return None
    
    def capture_conversation_screenshot(self, filename=None):
        """Capture a screenshot of the current conversation"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"conversation_{timestamp}.png"
            
        try:
            self.page.screenshot(path=filename)
            self.logger.info(f"Captured conversation screenshot: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {str(e)}")
            return None
    
    def clear_conversation(self):
        """Clear the current conversation in ChatGPT"""
        try:
            # Look for the "New chat" or "Clear chat" button
            clear_chat_selectors = [
                'nav a:has-text("New chat")',
                'button:has-text("New chat")',
                'button:has-text("Clear chat")',
                'button[aria-label="New chat"]'
            ]
            
            for selector in clear_chat_selectors:
                try:
                    button = self.page.wait_for_selector(selector, timeout=3000)
                    if button:
                        self._simulate_human_delay(0.5, 1.0)
                        button.click()
                        self._wait_for_page_stability()
                        self.logger.info("Cleared conversation")
                        return True
                except:
                    continue
            
            # Try vision-based approach if selectors fail
            if os.path.exists("templates/new_chat_button.png"):
                if self.click_by_vision("templates/new_chat_button.png"):
                    self._wait_for_page_stability()
                    self.logger.info("Cleared conversation using vision")
                    return True
            
            self.logger.warning("Could not find clear conversation button")
            return False
            
        except Exception as e:
            self.logger.error(f"Error clearing conversation: {str(e)}")
            return False
    
    def browse_url_in_chat(self, url):
        """Ask ChatGPT to browse a URL
        
        Args:
            url (str): The URL to browse
            
        Returns:
            str: The response from ChatGPT about the browsed content or None on failure
        """
        browse_command = f"Please browse this URL and summarize the content: {url}"
        return self.send_message(browse_command)
    
    def create_echo_from_response(self, response_text):
        """Create an echo node from the ChatGPT response"""
        if not response_text:
            return None
            
        # Create tree with response content
        root = self.echo_system.create_tree("ChatGPT Response Root")
        
        # Split response into paragraphs for child nodes
        paragraphs = response_text.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                child = TreeNode(content=paragraph, parent=root)
                root.children.append(child)
        
        # Propagate echoes
        self.echo_system.propagate_echoes()
        
        # Analyze and return echo patterns
        return self.echo_system.analyze_echo_patterns()
    
    def close(self):
        """Close the browser"""
        # Save any pending memory
        self._save_memory()
        
        if self.page:
            try:
                self.page.close()
            except:
                pass
                
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
                
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass

def main():
    chat = SeleniumInterface()
    if not chat.init():
        print("Failed to initialize browser")
        return
        
    if not chat.authenticate():
        print("Authentication failed")
        chat.close()
        return
        
    print("Successfully authenticated")
    
    # Send a test message
    response = chat.send_message("Tell me about Deep Tree Echo and Echo State Networks in a brief summary.")
    
    if response:
        print("\nResponse received:")
        print("-" * 50)
        print(response[:500] + "..." if len(response) > 500 else response)
        print("-" * 50)
        
        # Create echo from response
        echo_patterns = chat.create_echo_from_response(response)
        if echo_patterns:
            print("\nEcho Patterns:")
            for key, value in echo_patterns.items():
                print(f"  {key}: {value}")
    
    chat.close()

if __name__ == "__main__":
    main()
