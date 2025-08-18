#!/usr/bin/env python3
"""
Test script for Echoself Recursive Self-Model Integration Demonstration

Tests the basic functionality of the echoself_demo.py module without requiring
external dependencies or GUI interaction.
"""

import unittest
import logging
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the module under test
try:
    import echoself_demo
    ECHOSELF_DEMO_AVAILABLE = True
except ImportError as e:
    ECHOSELF_DEMO_AVAILABLE = False
    print(f"Warning: Could not import echoself_demo: {e}")


class TestEchoselfDemo(unittest.TestCase):
    """Test cases for echoself_demo module"""

    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging output during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_import_echoself_demo(self):
        """Test that echoself_demo module can be imported"""
        if not ECHOSELF_DEMO_AVAILABLE:
            self.skipTest("echoself_demo module not available")
        
        self.assertTrue(ECHOSELF_DEMO_AVAILABLE)
        self.assertIsNotNone(echoself_demo)

    @unittest.skipIf(not ECHOSELF_DEMO_AVAILABLE, "echoself_demo not available")
    def test_setup_logging_function_exists(self):
        """Test that setup_logging function exists"""
        self.assertTrue(hasattr(echoself_demo, 'setup_logging'))
        self.assertTrue(callable(echoself_demo.setup_logging))

    @unittest.skipIf(not ECHOSELF_DEMO_AVAILABLE, "echoself_demo not available")
    def test_setup_logging_functionality(self):
        """Test that setup_logging configures logging correctly"""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Call setup_logging
        echoself_demo.setup_logging()
        
        # Verify logging is configured
        self.assertGreaterEqual(len(root_logger.handlers), 1)
        self.assertEqual(root_logger.level, logging.INFO)

    @unittest.skipIf(not ECHOSELF_DEMO_AVAILABLE, "echoself_demo not available")
    @patch('echoself_demo.CognitiveArchitecture')
    def test_demonstrate_introspection_cycle_function_exists(self, mock_cog_arch):
        """Test that demonstrate_introspection_cycle function exists and can be called"""
        self.assertTrue(hasattr(echoself_demo, 'demonstrate_introspection_cycle'))
        self.assertTrue(callable(echoself_demo.demonstrate_introspection_cycle))
        
        # Create a mock cognitive system
        mock_cognitive_system = Mock()
        mock_cognitive_system._calculate_current_cognitive_load.return_value = 0.5
        mock_cognitive_system._calculate_recent_activity.return_value = 0.3
        mock_cognitive_system.perform_recursive_introspection.return_value = "test prompt"
        
        # Test the function doesn't crash
        try:
            echoself_demo.demonstrate_introspection_cycle(mock_cognitive_system, 1)
        except Exception as e:
            self.fail(f"demonstrate_introspection_cycle raised an exception: {e}")

    @unittest.skipIf(not ECHOSELF_DEMO_AVAILABLE, "echoself_demo not available")
    def test_module_structure(self):
        """Test that the module has the expected structure"""
        # Check for expected functions
        expected_functions = ['setup_logging', 'demonstrate_introspection_cycle']
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(echoself_demo, func_name), 
                          f"Missing expected function: {func_name}")
            self.assertTrue(callable(getattr(echoself_demo, func_name)),
                          f"Expected function is not callable: {func_name}")

    @unittest.skipIf(not ECHOSELF_DEMO_AVAILABLE, "echoself_demo not available")
    def test_required_imports(self):
        """Test that the module imports required dependencies"""
        # Test that the module imports what it needs without crashing
        import importlib
        try:
            importlib.reload(echoself_demo)
        except ImportError as e:
            self.fail(f"Module failed to import required dependencies: {e}")

    @unittest.skipIf(not ECHOSELF_DEMO_AVAILABLE, "echoself_demo not available")
    @patch('time.time')
    @patch('echoself_demo.CognitiveArchitecture')
    def test_timing_functionality(self, mock_cog_arch, mock_time):
        """Test that timing functionality works in demonstration"""
        mock_time.side_effect = [1000.0, 1001.5]  # 1.5 second operation
        
        mock_cognitive_system = Mock()
        mock_cognitive_system._calculate_current_cognitive_load.return_value = 0.5
        mock_cognitive_system._calculate_recent_activity.return_value = 0.3
        mock_cognitive_system.perform_recursive_introspection.return_value = "test prompt"
        
        # Redirect stdout to capture print statements
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            echoself_demo.demonstrate_introspection_cycle(mock_cognitive_system, 1)
            output = sys.stdout.getvalue()
            
            # Check that timing information is displayed
            self.assertIn("1.50 seconds", output)
            self.assertIn("Current Cognitive Load:", output)
            self.assertIn("Recent Activity Level:", output)
            
        finally:
            sys.stdout = old_stdout


def main():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()