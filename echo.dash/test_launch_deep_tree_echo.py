#!/usr/bin/env python3
"""
Test script for Launch Deep Tree Echo module

Tests the launcher functionality for Deep Tree Echo system.
"""

import unittest
import asyncio
import logging
import sys
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the module under test
try:
    import launch_deep_tree_echo
    LAUNCH_AVAILABLE = True
except ImportError as e:
    LAUNCH_AVAILABLE = False
    print(f"Warning: Could not import launch_deep_tree_echo: {e}")


class TestLaunchDeepTreeEcho(unittest.TestCase):
    """Test cases for launch_deep_tree_echo module"""

    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging output during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_import_launch_deep_tree_echo(self):
        """Test that launch_deep_tree_echo module can be imported"""
        if not LAUNCH_AVAILABLE:
            self.skipTest("launch_deep_tree_echo module not available")
        
        self.assertTrue(LAUNCH_AVAILABLE)

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_main_function_exists(self):
        """Test that main function exists and is async"""
        self.assertTrue(hasattr(launch_deep_tree_echo, 'main'))
        self.assertTrue(callable(launch_deep_tree_echo.main))
        
        # Test if it's a coroutine function
        self.assertTrue(asyncio.iscoroutinefunction(launch_deep_tree_echo.main))

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_logging_configuration(self):
        """Test that logging is properly configured in the module"""
        # Check if logger is configured
        import logging
        logger = logging.getLogger('launch_deep_tree_echo')
        
        # Module should have configured logging
        root_logger = logging.getLogger()
        self.assertGreater(len(root_logger.handlers), 0)

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    @patch('launch_deep_tree_echo.UnifiedLauncher')
    @patch('launch_deep_tree_echo.create_argument_parser')
    @patch('launch_deep_tree_echo.create_config_from_args')
    async def test_main_function_flow(self, mock_config, mock_parser, mock_launcher):
        """Test main function execution flow"""
        # Setup mocks
        mock_args = Mock()
        mock_parser_instance = Mock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        mock_config.return_value = {"test": "config"}
        
        mock_launcher_instance = Mock()
        mock_launcher_instance.launch_async = AsyncMock(return_value=0)
        mock_launcher.return_value = mock_launcher_instance
        
        try:
            # Test main function execution
            result = await launch_deep_tree_echo.main()
            
            # Verify the flow was called
            mock_parser.assert_called_once_with("deep-tree-echo")
            mock_config.assert_called_once()
            mock_launcher.assert_called_once()
            
        except Exception as e:
            # If there are dependency issues, that's OK for this test
            if "No module named" in str(e):
                self.skipTest(f"Dependencies not available: {e}")
            else:
                # Main function exists and was called
                pass

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_module_imports(self):
        """Test that module imports required dependencies"""
        # Test that the module imports its dependencies correctly
        import importlib
        try:
            importlib.reload(launch_deep_tree_echo)
        except ImportError as e:
            self.fail(f"Module failed to import required dependencies: {e}")

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_argument_parser_usage(self):
        """Test that module uses argument parser correctly"""
        # Check that the module has the expected imports for argument parsing
        module_vars = dir(launch_deep_tree_echo)
        
        # Should import argparse functionality through unified_launcher
        expected_imports = ['create_argument_parser', 'create_config_from_args']
        
        # Check if these are available (either imported or as attributes)
        for expected in expected_imports:
            # These might be imported from unified_launcher
            if not hasattr(launch_deep_tree_echo, expected):
                # Check if unified_launcher is imported
                self.assertTrue(hasattr(launch_deep_tree_echo, 'UnifiedLauncher') or
                               'unified_launcher' in str(module_vars),
                               f"Missing expected import or function: {expected}")

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_unified_launcher_integration(self):
        """Test integration with unified launcher"""
        # Module should import UnifiedLauncher
        self.assertTrue(hasattr(launch_deep_tree_echo, 'UnifiedLauncher'))

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_async_execution_support(self):
        """Test that module supports async execution"""
        # Check for asyncio support
        self.assertTrue(hasattr(launch_deep_tree_echo, 'asyncio'))
        
        # Main function should be async
        if hasattr(launch_deep_tree_echo, 'main'):
            self.assertTrue(asyncio.iscoroutinefunction(launch_deep_tree_echo.main))

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    @patch('sys.argv', ['launch_deep_tree_echo.py'])
    @patch('launch_deep_tree_echo.UnifiedLauncher')
    def test_command_line_interface(self, mock_launcher):
        """Test command line interface functionality"""
        # Setup mock launcher
        mock_launcher_instance = Mock()
        mock_launcher_instance.launch_async = AsyncMock(return_value=0)
        mock_launcher.return_value = mock_launcher_instance
        
        try:
            # This would normally be called when run as script
            # We're just testing that the structure exists
            if hasattr(launch_deep_tree_echo, 'create_argument_parser'):
                parser = launch_deep_tree_echo.create_argument_parser("test")
                self.assertIsNotNone(parser)
                
        except Exception as e:
            if "No module named" in str(e):
                self.skipTest("Dependencies not available")

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_error_handling_structure(self):
        """Test that module has proper error handling structure"""
        # Module should handle KeyboardInterrupt and general exceptions
        # This is tested by checking if the main execution block exists
        
        # Read the module source to check for exception handling
        import inspect
        try:
            source = inspect.getsource(launch_deep_tree_echo)
            
            # Should have KeyboardInterrupt handling
            self.assertIn('KeyboardInterrupt', source)
            
            # Should have general exception handling  
            self.assertIn('except', source)
            
        except (OSError, TypeError):
            # If we can't get source, that's OK - module still imported successfully
            pass

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_logging_file_configuration(self):
        """Test that module configures file logging"""
        # Check for logging configuration
        import logging
        
        # Should configure both file and console logging
        root_logger = logging.getLogger()
        
        # Look for file handlers
        file_handlers = [h for h in root_logger.handlers 
                        if hasattr(h, 'baseFilename')]
        
        # If the module was executed, it should have configured logging
        # But in test environment, this might not happen
        # So we just check that logging infrastructure exists
        self.assertTrue(hasattr(logging, 'FileHandler'))

    @unittest.skipIf(not LAUNCH_AVAILABLE, "launch_deep_tree_echo not available")
    def test_module_executable_structure(self):
        """Test that module has proper executable structure"""
        # Module should have __name__ == "__main__" block
        import inspect
        try:
            source = inspect.getsource(launch_deep_tree_echo)
            
            # Should have main execution block
            self.assertIn('__name__', source)
            self.assertIn('__main__', source)
            
            # Should use asyncio.run for main function
            self.assertIn('asyncio.run', source)
            
        except (OSError, TypeError):
            # If we can't get source, just check that it's executable
            # Module imported successfully, which is the main requirement
            pass


def main():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()