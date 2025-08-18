import os
import logging
import pytest

# Try importing browser_interface, skip tests if not available
try:
    from browser_interface import DeepTreeEchoBrowser
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False
    DeepTreeEchoBrowser = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_credentials(filename='.env'):
    """Load credentials from environment file"""
    credentials = {}
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    credentials[key] = value
    
    return credentials

@pytest.mark.skipif(not BROWSER_AVAILABLE, reason="browser_interface not available")
def main():
    """Test authentication for Deep Tree Echo's services"""
    browser = DeepTreeEchoBrowser()
    
    try:
        # Initialize browser
        if not browser.init():
            logging.error("Failed to initialize browser")
            return
            
        # Load credentials
        creds = load_credentials()
        
        # Service configurations
        services = {
            'github': {
                'container': 'Development',
                'credentials': {
                    'username': creds.get('GITHUB_USERNAME'),
                    'password': creds.get('GITHUB_PASSWORD'),
                    '2fa_method': 'authenticator' if creds.get('GITHUB_2FA') else None
                }
            },
            'google': {
                'container': 'Personal',
                'credentials': {
                    'email': creds.get('GOOGLE_EMAIL'),
                    'password': creds.get('GOOGLE_PASSWORD'),
                    '2fa_method': 'authenticator' if creds.get('GOOGLE_2FA') else None
                }
            },
            'openai': {
                'container': 'Development',
                'credentials': {
                    'email': creds.get('OPENAI_EMAIL'),
                    'password': creds.get('OPENAI_PASSWORD'),
                    'use_google_sso': creds.get('OPENAI_USE_GOOGLE_SSO', '').lower() == 'true'
                }
            }
        }
        
        # Authenticate each service
        for service_name, config in services.items():
            if any(config['credentials'].values()):  # Only try if we have credentials
                logging.info("Authenticating a service...")
                success = browser.authenticate_service(
                    service_name,
                    config['container'],
                    config['credentials']
                )
                if success:
                    logging.info("Successfully authenticated %s", service_name)
                else:
                    logging.error("Failed to authenticate %s", service_name)
        
        # Keep browser open for interaction
        input("Press Enter to close browser...")
        
    finally:
        browser.close()

if __name__ == "__main__":
    main()
