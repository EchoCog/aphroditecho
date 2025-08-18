import logging
from browser_interface import DeepTreeEchoBrowser
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_human_like_interaction(browser):
    """Test human-like interactions in different scenarios"""
    try:
        # Get Development container page
        page = browser.get_or_create_page('Development')
        if not page:
            logging.error("Failed to get Development container page")
            return False
            
        # Test 1: Navigate to Python.org and interact with search
        logging.info("Testing search interaction...")
        page.goto('https://www.python.org')
        
        # Wait for page load and search box
        time.sleep(2)  # Let the page settle
        
        # Click search box and type with human-like timing
        browser.human_like_interaction(
            page,
            'click',
            selector='input[name="q"]'
        )
        browser.human_like_interaction(
            page,
            'type',
            text='machine learning'
        )
        time.sleep(1)  # Wait for suggestions
        
        # Test 2: Scroll through results
        logging.info("Testing scroll behavior...")
        browser.human_like_interaction(
            page,
            'scroll',
            amount=500,
            direction='down'
        )
        time.sleep(2)
        
        browser.human_like_interaction(
            page,
            'scroll',
            amount=200,
            direction='up'
        )
        
        # Test 3: Hover over elements
        logging.info("Testing hover behavior...")
        browser.human_like_interaction(
            page,
            'hover',
            selector='#container >> a[href="/about/"]',
            duration=1.5
        )
        
        return True
        
    except Exception as e:
        logging.error(f"Error in human-like interaction test: {str(e)}")
        return False

def main():
    """Test Deep Tree Echo's sensory-motor capabilities"""
    browser = DeepTreeEchoBrowser()
    
    try:
        # Initialize browser
        if not browser.init():
            logging.error("Failed to initialize browser")
            return
            
        # Run interaction tests
        if test_human_like_interaction(browser):
            logging.info("Successfully completed human-like interaction tests")
        else:
            logging.error("Failed to complete human-like interaction tests")
        
        # Keep browser open for observation
        input("Press Enter to close browser...")
        
    finally:
        browser.close()

if __name__ == "__main__":
    main()
