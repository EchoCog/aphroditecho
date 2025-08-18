#!/usr/bin/env python3
"""
Test script to verify X server and browser automation setup in the devcontainer.
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BrowserSetupTest")

def test_x_server():
    """Test if X server is running and accessible"""
    logger.info("Testing X server configuration...")
    
    display = os.environ.get('DISPLAY', ':1')
    logger.info(f"Current DISPLAY setting: {display}")
    
    try:
        result = subprocess.run(
            ["xdpyinfo"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode == 0:
            logger.info("✓ X Server is running!")
            return True
        else:
            logger.error(f"✗ X Server test failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"✗ X Server test failed with exception: {e}")
        return False

def test_playwright_browser():
    """Test if Playwright can launch a browser"""
    logger.info("Testing Playwright browser launch...")
    
    try:
        # Only import if needed
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Try launching Firefox
            logger.info("Attempting to launch Firefox with Playwright...")
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            page.goto('about:blank')
            title = page.title()
            logger.info(f"Browser page title: {title}")
            browser.close()
            logger.info("✓ Successfully launched Firefox with Playwright!")
            return True
            
    except Exception as e:
        logger.error(f"✗ Playwright browser test failed: {e}")
        return False

def test_browser_environment():
    """Test the overall browser environment"""
    results = {
        "X Server": test_x_server(),
        "Playwright Browser": test_playwright_browser()
    }
    
    # Print summary
    logger.info("\n=== Browser Environment Test Summary ===")
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    logger.info("Starting browser environment tests...")
    
    # Print environment info
    logger.info(f"DISPLAY={os.environ.get('DISPLAY', 'not set')}")
    logger.info(f"XAUTHORITY={os.environ.get('XAUTHORITY', 'not set')}")
    logger.info(f"PLAYWRIGHT_BROWSERS_PATH={os.environ.get('PLAYWRIGHT_BROWSERS_PATH', 'not set')}")
    
    success = test_browser_environment()
    
    if success:
        logger.info("All browser environment tests passed!")
        sys.exit(0)
    else:
        logger.error("Some browser environment tests failed!")
        sys.exit(1)