import logging
from browser_interface import DeepTreeEchoBrowser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Initialize Deep Tree Echo's browser environment"""
    browser = DeepTreeEchoBrowser()
    
    try:
        # Initialize browser with profile
        if not browser.init():
            logging.error("Failed to initialize browser")
            return
            
        # Create pages in different containers
        containers = ['Personal', 'Work', 'Development', 'Social']
        pages = {}
        
        for container in containers:
            page = browser.create_page_in_container(container)
            if page:
                pages[container] = page
                logging.info(f"Created page in {container} container")
            else:
                logging.error(f"Failed to create page in {container} container")
        
        # Keep browser open for interaction
        input("Press Enter to close browser...")
        
    finally:
        browser.close()

if __name__ == "__main__":
    main()
