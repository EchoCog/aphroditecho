#!/usr/bin/env python3
"""
Environment verification script for EchoSurface development container.
Run this script to verify that all components of the development environment
are working correctly, especially the browser automation features.
"""

import os
import sys
import time
import subprocess
import importlib.util
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnvironmentVerifier")

def check_display():
    """Verify X server display is working"""
    logger.info("Checking X server display...")
    
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
            logger.info("✅ X Server is running correctly")
            # Get screen resolution
            for line in result.stdout.split('\n'):
                if "dimensions" in line:
                    logger.info(f"  - Screen resolution: {line.strip()}")
            return True
        else:
            logger.error(f"❌ X Server test failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ X Server test failed with exception: {e}")
        return False

def check_package_installation(packages):
    """Check if Python packages are installed"""
    logger.info("Checking required Python packages...")
    
    results = {}
    for package in packages:
        spec = importlib.util.find_spec(package)
        if spec is not None:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown version')
                logger.info(f"✅ {package} is installed ({version})")
                results[package] = True
            except ImportError:
                logger.warning(f"⚠️ {package} found but failed to import")
                results[package] = False
        else:
            logger.error(f"❌ {package} is not installed")
            results[package] = False
    
    return results

def check_browser_executables():
    """Check if browser executables are available"""
    logger.info("Checking browser executables...")
    
    browsers = ['firefox', 'chromium', 'chromium-browser']
    results = {}
    
    for browser in browsers:
        try:
            result = subprocess.run(
                ["which", browser],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.info(f"✅ {browser} found at: {path}")
                
                # Try to get version
                try:
                    version_result = subprocess.run(
                        [browser, "--version"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if version_result.returncode == 0:
                        logger.info(f"  - Version: {version_result.stdout.strip()}")
                except Exception:
                    pass
                    
                results[browser] = True
            else:
                logger.warning(f"⚠️ {browser} executable not found")
                results[browser] = False
        except Exception as e:
            logger.error(f"❌ Error checking {browser}: {e}")
            results[browser] = False
    
    return results

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
            logger.info("✅ Successfully launched Firefox with Playwright!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Playwright browser test failed: {e}")
        return False

def test_browser_environment():
    """Run comprehensive tests of the browser environment"""
    results = {
        "X Server": check_display(),
        "Required Packages": check_package_installation([
            "playwright", "selenium", "pyautogui", "PIL", "numpy", 
            "tkinter", "ttkbootstrap"
        ]),
        "Browser Executables": check_browser_executables(),
    }
    
    # Only run playwright test if display is working
    if results["X Server"]:
        results["Playwright Browser"] = test_playwright_browser()
    
    # Print summary
    logger.info("\n=== Browser Environment Test Summary ===")
    all_passed = True
    
    for test_name, result in results.items():
        if isinstance(result, dict):
            # This is a group of results
            logger.info(f"{test_name}:")
            group_passed = all(result.values())
            for item, passed in result.items():
                status = "✅ PASSED" if passed else "❌ FAILED"
                logger.info(f"  - {item}: {status}")
            if not group_passed:
                all_passed = False
        else:
            # This is a single result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if not result:
                all_passed = False
    
    return all_passed

if __name__ == "__main__":
    logger.info("Starting browser environment verification...")
    
    # Print environment info
    logger.info(f"Python version: {sys.version}")
    logger.info(f"DISPLAY={os.environ.get('DISPLAY', 'not set')}")
    logger.info(f"XAUTHORITY={os.environ.get('XAUTHORITY', 'not set')}")
    logger.info(f"PLAYWRIGHT_BROWSERS_PATH={os.environ.get('PLAYWRIGHT_BROWSERS_PATH', 'not set')}")
    
    success = test_browser_environment()
    
    if success:
        logger.info("🎉 All browser environment tests passed!")
        sys.exit(0)
    else:
        logger.error("⚠️ Some browser environment tests failed!")
        sys.exit(1)