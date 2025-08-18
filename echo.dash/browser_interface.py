import os
import json
import time
import logging
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError
from sensory_motor import SensoryMotor

class DeepTreeEchoBrowser:
    """Browser interface for Deep Tree Echo's persistent online presence"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profile_dir = Path.home() / '.deep_tree_echo' / 'firefox_profile'
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.sensory = SensoryMotor()
        
    def _setup_profile_directory(self):
        """Create and configure Deep Tree Echo's Firefox profile directory"""
        profile_dir = Path(os.getcwd()) / 'deep_tree_echo_profile'
        profile_dir.mkdir(exist_ok=True)
        
        # Create preferences file for Firefox
        prefs_file = profile_dir / 'prefs.js'
        if not prefs_file.exists():
            preferences = {
                # Privacy settings
                'privacy.trackingprotection.enabled': True,
                'privacy.donottrackheader.enabled': True,
                
                # Security settings
                'security.ssl.enable_ocsp_stapling': True,
                'security.ssl.enable_ocsp_must_staple': True,
                
                # Performance settings
                'browser.cache.disk.enable': True,
                'browser.cache.memory.enable': True,
                
                # Accessibility settings
                'accessibility.force_disabled': 0,
                
                # Developer tools
                'devtools.chrome.enabled': True,
                'devtools.debugger.remote-enabled': True,
                
                # Container tabs support
                'privacy.userContext.enabled': True,
                
                # Session restore
                'browser.sessionstore.resume_from_crash': True,
                
                # Extensions
                'extensions.autoDisableScopes': 0,
                'extensions.enabledScopes': 15
            }
            
            with open(prefs_file, 'w') as f:
                for key, value in preferences.items():
                    if isinstance(value, bool):
                        value = str(value).lower()
                    elif isinstance(value, str):
                        value = f'"{value}"'
                    f.write(f'user_pref("{key}", {value});\n')
        
        return profile_dir
    
    def init(self):
        """Initialize browser with Deep Tree Echo's profile"""
        try:
            # Create profile directory if it doesn't exist
            self.profile_dir.parent.mkdir(parents=True, exist_ok=True)
            self.profile_dir.mkdir(exist_ok=True)
            
            # Start playwright and launch persistent Firefox instance
            self.playwright = sync_playwright().start()
            
            # Launch Firefox with our custom profile
            self.browser = self.playwright.firefox.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True,
                bypass_csp=True,  # Needed for some modern web apps
                java_script_enabled=True,
                locale='en-US',
                timezone_id='UTC',
                firefox_user_prefs={
                    # Firefox Account and Sync
                    'identity.fxaccounts.enabled': True,
                    'services.sync.username': 'echo@rzo.io',
                    'services.sync.engine.passwords': True,
                    'services.sync.engine.bookmarks': True,
                    'services.sync.engine.history': True,
                    'services.sync.engine.tabs': True,
                    'services.sync.engine.prefs': True,
                    'services.sync.engine.addons': True,
                    'services.sync.engine.addresses': True,
                    'services.sync.engine.creditcards': True,
                    
                    # Privacy settings
                    'privacy.trackingprotection.enabled': True,
                    'privacy.donottrackheader.enabled': True,
                    
                    # Security settings
                    'security.ssl.enable_ocsp_stapling': True,
                    'security.ssl.enable_ocsp_must_staple': True,
                    
                    # Performance settings
                    'browser.cache.disk.enable': True,
                    'browser.cache.memory.enable': True,
                    
                    # Accessibility settings
                    'accessibility.force_disabled': 0,
                    
                    # Developer tools
                    'devtools.chrome.enabled': True,
                    'devtools.debugger.remote-enabled': True,
                    
                    # Container tabs support
                    'privacy.userContext.enabled': True,
                    
                    # Session restore
                    'browser.sessionstore.resume_from_crash': True,
                    
                    # Startup settings
                    'browser.startup.homepage': 'about:home',
                    'browser.startup.page': 3,  # Resume previous session
                }
            )
            
            # Set up Firefox account if not already logged in
            self._setup_firefox_account()
            
            # Set up container tabs for different contexts (personal, work, etc)
            self._setup_containers()
            
            # Create or get main page
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            
            # Configure page settings
            self._configure_page(self.page)
            
            self.logger.info("Browser initialized successfully with Deep Tree Echo's profile")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            return False
    
    def _setup_firefox_account(self):
        """Set up Firefox account and sync"""
        try:
            # Create a new page for Firefox account setup
            page = self.browser.new_page()
            
            # Go to Firefox account settings
            page.goto('about:preferences#sync')
            
            # Check if already signed in
            try:
                signed_in = page.wait_for_selector(
                    'button[data-l10n-id="sync-signedout-button"]',
                    timeout=5000
                ) is None
            except:
                signed_in = True
            
            if not signed_in:
                self.logger.info("Setting up Firefox account...")
                
                # Click sign in button
                page.click('button[data-l10n-id="sync-signedout-button"]')
                
                # Wait for and fill email field
                page.wait_for_selector('input[type="email"]')
                page.fill('input[type="email"]', 'echo@rzo.io')
                page.click('button[type="submit"]')
                
                # Wait for and fill password field
                page.wait_for_selector('input[type="password"]')
                page.fill('input[type="password"]', 'D33ptr333ch0?')
                page.click('button[type="submit"]')
                
                # Wait for sync to be enabled
                page.wait_for_selector('button[data-l10n-id="sync-engine-passwords"]', timeout=30000)
                self.logger.info("Firefox account setup complete")
            else:
                self.logger.info("Firefox account already set up")
            
            # Close the preferences page
            page.close()
            
        except Exception as e:
            self.logger.error(f"Error setting up Firefox account: {str(e)}")
    
    def _setup_containers(self):
        """Set up Firefox container tabs for different contexts"""
        containers = [
            {'name': 'Personal', 'color': 'blue', 'icon': 'fingerprint'},
            {'name': 'Work', 'color': 'green', 'icon': 'briefcase'},
            {'name': 'Development', 'color': 'purple', 'icon': 'cogs'},
            {'name': 'Social', 'color': 'orange', 'icon': 'circle'}
        ]
        
        containers_file = self.profile_dir / 'containers.json'
        if not containers_file.exists():
            with open(containers_file, 'w') as f:
                json.dump({'containers': containers}, f, indent=2)
    
    def _configure_page(self, page):
        """Configure page settings for human-like behavior"""
        # Set realistic viewport and user agent
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Set longer timeouts for a more reliable automation
        page.set_default_timeout(60000)  # 60 seconds
        page.set_default_navigation_timeout(60000)
        
        # Add scripts to mask automation
        page.add_init_script("""
            // Make automation detection more difficult
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Add natural-looking performance variations
            const originalFunction = window.performance.now;
            window.performance.now = function() {
                return originalFunction.call(performance) + (Math.random() * 20);
            };
        """)
        
        # Add error handlers
        page.on("pageerror", lambda err: self.logger.error(f"Page error: {err}"))
        page.on("console", lambda msg: self.logger.debug(f"Console {msg.type}: {msg.text}"))

    def human_like_interaction(self, page, action, **kwargs):
        """Perform human-like interactions on the page"""
        try:
            if action == 'click':
                # Get element position
                element = page.locator(kwargs['selector'])
                bbox = element.bounding_box()
                if bbox:
                    # Add slight randomness to click position within element
                    x = bbox['x'] + bbox['width'] * random.random()
                    y = bbox['y'] + bbox['height'] * random.random()
                    
                    # Move and click with human-like motion
                    self.sensory.move_mouse(x, y)
                    self.sensory.click()
                    return True
                    
            elif action == 'type':
                # First click the input field
                if 'selector' in kwargs:
                    self.human_like_interaction(page, 'click', selector=kwargs['selector'])
                
                # Type with human-like timing
                self.sensory.type_text(kwargs['text'])
                return True
                
            elif action == 'scroll':
                self.sensory.scroll(kwargs.get('amount', 100), kwargs.get('direction', 'down'))
                return True
                
            elif action == 'hover':
                element = page.locator(kwargs['selector'])
                bbox = element.bounding_box()
                if bbox:
                    # Move to center of element
                    x = int(bbox['x'] + bbox['width'] / 2)
                    y = int(bbox['y'] + bbox['height'] / 2)
                    self.sensory.hover(x, y, kwargs.get('duration', 1.0))
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error in human-like interaction: {str(e)}")
            return False

    def wait_for_visual_element(self, page, template_path, timeout=30):
        """Wait for a visual element to appear on the page"""
        try:
            return self.sensory.wait_for_element(
                template_path,
                timeout=timeout,
                interval=0.5,
                threshold=0.8
            )
        except Exception as e:
            self.logger.error(f"Error waiting for visual element: {str(e)}")
            return None

    def authenticate_service(self, service_name, container_name, credentials):
        """Authenticate with a specific service in a container"""
        try:
            self.logger.info(f"Authenticating with {service_name} in {container_name} container")
            
            # Get or create container page
            page = self.get_or_create_page(container_name)
            if not page:
                return False
                
            # Handle different services
            if service_name.lower() == 'github':
                return self.authenticate_github(page, credentials)
            elif service_name.lower() == 'google':
                return self.authenticate_google(page, credentials)
            else:
                self.logger.error(f"Unsupported service: {service_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False

    def authenticate_github(self, page, credentials):
        """Authenticate with GitHub using modern authentication flow"""
        try:
            # Go to GitHub login page
            page.goto('https://github.com/login')
            
            # Wait for login form
            page.wait_for_selector('#login_field', timeout=10000)
            
            # Fill in credentials with human-like interaction
            self.human_like_interaction(
                page,
                'type',
                selector='#login_field',
                text=credentials['username']
            )
            
            self.human_like_interaction(
                page,
                'type',
                selector='#password',
                text=credentials['password']
            )
            
            # Click sign in button
            self.human_like_interaction(
                page,
                'click',
                selector='input[type="submit"]'
            )
            
            # Handle 2FA if needed
            try:
                # Wait for 2FA prompt
                page.wait_for_selector('#app_totp', timeout=10000)
                
                # Get 2FA code (implement your 2FA method here)
                totp_code = self._get_2fa_code(credentials)
                
                if totp_code:
                    self.human_like_interaction(
                        page,
                        'type',
                        selector='#app_totp',
                        text=totp_code
                    )
                    
                    # Click verify button
                    self.human_like_interaction(
                        page,
                        'click',
                        selector='button[type="submit"]'
                    )
            except TimeoutError:
                # No 2FA prompt, continue
                pass
                
            # Wait for successful login
            try:
                page.wait_for_selector('img.avatar.circle', timeout=10000)
                self.logger.info("Successfully authenticated with GitHub")
                return True
            except TimeoutError:
                self.logger.error("Failed to verify GitHub login")
                return False
                
        except Exception as e:
            self.logger.error(f"GitHub authentication error: {str(e)}")
            return False

    def get_or_create_page(self, container_name):
        """Get existing page for container or create new one"""
        try:
            # Check existing pages
            for page in self.browser.pages:
                context = page.evaluate("() => window.container")
                if context == container_name:
                    return page
            
            # Create new page if not found
            return self.create_page_in_container(container_name)
            
        except Exception as e:
            self.logger.error(f"Error getting/creating page: {str(e)}")
            return None

    def create_page_in_container(self, container_name):
        """Create a new page in specified container"""
        try:
            page = self.browser.new_page()
            self._configure_page(page)
            # Set container context
            page.add_init_script(f'window.container = "{container_name}";')
            return page
        except Exception as e:
            self.logger.error(f"Failed to create page in container {container_name}: {str(e)}")
            return None
    
    def close(self):
        """Gracefully close the browser"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error closing browser: {str(e)}")

    def configure_container(self, container_name, settings=None):
        """Configure container-specific settings"""
        try:
            page = self.get_or_create_page(container_name)
            if not page:
                return False
                
            # Default settings for each container type
            default_settings = {
                'Personal': {
                    'bookmarks': [
                        {'name': 'Gmail', 'url': 'https://mail.google.com'},
                        {'name': 'Google Calendar', 'url': 'https://calendar.google.com'},
                        {'name': 'Google Drive', 'url': 'https://drive.google.com'}
                    ],
                    'homepage': 'https://www.google.com'
                },
                'Development': {
                    'bookmarks': [
                        {'name': 'GitHub', 'url': 'https://github.com'},
                        {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com'},
                        {'name': 'MDN Web Docs', 'url': 'https://developer.mozilla.org'}
                    ],
                    'homepage': 'https://github.com'
                },
                'Work': {
                    'bookmarks': [
                        {'name': 'Microsoft Teams', 'url': 'https://teams.microsoft.com'},
                        {'name': 'Outlook', 'url': 'https://outlook.office.com'},
                        {'name': 'SharePoint', 'url': 'https://sharepoint.com'}
                    ],
                    'homepage': 'https://www.office.com'
                },
                'Social': {
                    'bookmarks': [
                        {'name': 'Twitter', 'url': 'https://twitter.com'},
                        {'name': 'LinkedIn', 'url': 'https://linkedin.com'},
                        {'name': 'Reddit', 'url': 'https://reddit.com'}
                    ],
                    'homepage': 'https://www.linkedin.com'
                }
            }
            
            # Merge default settings with provided settings
            container_settings = default_settings.get(container_name, {})
            if settings:
                container_settings.update(settings)
            
            # Apply settings
            self._apply_container_settings(page, container_settings)
            self.logger.info(f"Configured settings for {container_name} container")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring {container_name} container: {str(e)}")
            return False

    def _apply_container_settings(self, page, settings):
        """Apply settings to a container"""
        try:
            # Set homepage by navigating there
            if settings.get('homepage'):
                page.goto(settings['homepage'])
                self.logger.info(f"Set homepage to: {settings['homepage']}")
            
            # Add bookmarks using browser storage API
            if settings.get('bookmarks'):
                self._manage_bookmarks(page, settings['bookmarks'])
                
        except Exception as e:
            self.logger.error(f"Error applying container settings: {str(e)}")

    def _manage_bookmarks(self, page, bookmarks):
        """Manage bookmarks in a container"""
        try:
            for bookmark in bookmarks:
                try:
                    # Navigate to the URL first
                    page.goto(bookmark['url'])
                    
                    # Use keyboard shortcuts to add bookmark
                    # Ctrl+D to open bookmark dialog
                    page.keyboard.press('Control+D')
                    
                    # Wait for bookmark dialog and set name
                    try:
                        name_input = page.wait_for_selector('input#editBMPanel_namePicker', timeout=5000)
                        if name_input:
                            name_input.fill(bookmark['name'])
                            
                            # Press Enter to save
                            page.keyboard.press('Enter')
                            self.logger.info(f"Added bookmark: {bookmark['name']}")
                    except Exception:
                        # Dialog might not appear if bookmark exists
                        pass
                        
                except Exception as e:
                    self.logger.error(f"Error adding bookmark {bookmark['name']}: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error managing bookmarks: {str(e)}")

    def get_container_settings(self, container_name):
        """Get current settings for a container"""
        try:
            page = self.get_or_create_page(container_name)
            if not page:
                return None
                
            # Get current URL as homepage
            settings = {
                'homepage': page.url,
                'bookmarks': []  # We can't reliably get bookmarks through Playwright
            }
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Error getting settings for {container_name} container: {str(e)}")
            return None

    def _get_2fa_code(self, credentials):
        """Get 2FA code for GitHub authentication"""
        # Implement your 2FA method here
        return None
