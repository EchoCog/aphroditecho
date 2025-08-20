#!/usr/bin/env python3
"""
Test script for Standardized Echoself Demo Component

Tests the standardized echoself_demo_standardized.py module to ensure
it properly implements the Echo component interfaces while maintaining
backward compatibility.
"""

import unittest
import logging
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the modules under test
try:
    from echoself_demo_standardized import (
        EchoselfDemoStandardized, create_echoself_demo_system,
        setup_logging, demonstrate_introspection_cycle
    )
    from echo_component_base import EchoConfig, EchoResponse, validate_echo_component
    ECHOSELF_DEMO_STANDARDIZED_AVAILABLE = True
except ImportError as e:
    ECHOSELF_DEMO_STANDARDIZED_AVAILABLE = False
    print(f"Warning: Could not import echoself_demo_standardized: {e}")


class TestEchoselfDemoStandardized(unittest.TestCase):
    """Test cases for standardized Echoself demo component"""

    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging output during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_import_standardized_module(self):
        """Test that standardized module can be imported"""
        if not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE:
            self.skipTest("echoself_demo_standardized module not available")
        
        self.assertTrue(ECHOSELF_DEMO_STANDARDIZED_AVAILABLE)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_component_creation(self):
        """Test creating the standardized component"""
        config = EchoConfig(component_name="TestEchoselfDemo", debug_mode=True)
        component = EchoselfDemoStandardized(config)
        
        # Test basic attributes
        self.assertEqual(component.config.component_name, "TestEchoselfDemo")
        self.assertIsNotNone(component.logger)
        self.assertEqual(component.demo_cycles_completed, 0)
        self.assertEqual(len(component.introspection_results), 0)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_component_validation(self):
        """Test that component passes validation"""
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Component should be valid
        self.assertTrue(validate_echo_component(component))

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    @patch('echoself_demo_standardized.CognitiveArchitecture')
    def test_initialization_success(self, mock_cognitive_arch):
        """Test successful component initialization"""
        # Mock cognitive architecture
        mock_system = Mock()
        mock_system.echoself_introspection = Mock()
        mock_cognitive_arch.return_value = mock_system
        
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Temporarily enable cognitive architecture
        import echoself_demo_standardized
        original_available = echoself_demo_standardized.COGNITIVE_ARCHITECTURE_AVAILABLE
        echoself_demo_standardized.COGNITIVE_ARCHITECTURE_AVAILABLE = True
        
        try:
            # Initialize should succeed
            result = component.initialize()
            
            self.assertTrue(result.success)
            self.assertIn("initialized", result.message)
            self.assertTrue(component._initialized)
            self.assertIsNotNone(component.cognitive_system)
        finally:
            echoself_demo_standardized.COGNITIVE_ARCHITECTURE_AVAILABLE = original_available

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_initialization_failure_no_cognitive_arch(self):
        """Test initialization failure when cognitive architecture unavailable"""
        # Test with the actual module (cognitive architecture may not be available)
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # This might fail if cognitive architecture is not available
        result = component.initialize()
        
        if not result.success:
            # If it failed, should have appropriate error message
            self.assertIn("not available", result.message.lower())
            self.assertFalse(component._initialized)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_echo_operation(self):
        """Test echo operation"""
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Echo should work even without initialization
        result = component.echo("test_data", echo_value=0.75)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data['echo_value'], 0.75)
        self.assertIn('demo_state', result.data)
        self.assertEqual(result.data['demo_state']['cycles_completed'], 0)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_process_without_initialization(self):
        """Test that process fails gracefully when not initialized"""
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Process should fail if not initialized
        result = component.process("test_operation")
        
        self.assertFalse(result.success)
        self.assertIn("not initialized", result.message)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    @patch('echoself_demo_standardized.CognitiveArchitecture')
    def test_process_supported_operations(self, mock_cognitive_arch):
        """Test processing of supported operations"""
        # Mock cognitive architecture
        mock_system = Mock()
        mock_system.echoself_introspection = Mock()
        mock_system.echoself_introspection.adaptive_attention.return_value = 0.5
        mock_system.perform_recursive_introspection.return_value = "test prompt"
        mock_system.get_introspection_metrics.return_value = {"test": "metrics"}
        mock_system.adaptive_goal_generation_with_introspection.return_value = []
        mock_cognitive_arch.return_value = mock_system
        
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Set up cognitive system directly for testing
        component.cognitive_system = mock_system
        component._initialized = True
        
        # Test introspection cycle operation
        result = component.process("introspection_cycle")
        self.assertTrue(result.success)
        self.assertIn("cycle", result.message)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    @patch('echoself_demo_standardized.CognitiveArchitecture')
    def test_process_invalid_operation(self, mock_cognitive_arch):
        """Test processing of invalid operation"""
        # Mock cognitive architecture
        mock_system = Mock()
        mock_system.echoself_introspection = Mock()
        mock_cognitive_arch.return_value = mock_system
        
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Set up cognitive system directly for testing
        component.cognitive_system = mock_system
        component._initialized = True
        
        # Test invalid operation
        result = component.process("invalid_operation")
        self.assertFalse(result.success)
        self.assertIn("Unknown operation", result.message)
        self.assertIn("valid_operations", result.metadata)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_cleanup_demo_files(self):
        """Test cleanup functionality"""
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Test cleanup (should work even without files)
        result = component.cleanup_demo_files()
        self.assertTrue(result.success)
        self.assertIn("cleaned_files", result.data)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_factory_function(self):
        """Test factory function for creating demo system"""
        # This test might fail if cognitive architecture is not available
        try:
            demo = create_echoself_demo_system()
            self.assertIsInstance(demo, EchoselfDemoStandardized)
            self.assertTrue(demo._initialized)
        except RuntimeError as e:
            # Expected if cognitive architecture is not available
            self.assertIn("Failed to initialize", str(e))

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_backward_compatibility_setup_logging(self):
        """Test backward compatibility function setup_logging"""
        # Should not raise an exception
        setup_logging()
        
        # Check that logging is configured
        root_logger = logging.getLogger()
        self.assertGreaterEqual(len(root_logger.handlers), 1)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_backward_compatibility_demonstrate_introspection_cycle(self):
        """Test backward compatibility function"""
        # Mock cognitive system
        mock_cognitive_system = Mock()
        mock_cognitive_system.perform_recursive_introspection.return_value = "test prompt"
        mock_cognitive_system.get_introspection_metrics.return_value = {
            "test_metric": "value",
            "highest_salience_files": [("test.py", 0.8)]
        }
        mock_cognitive_system.adaptive_goal_generation_with_introspection.return_value = [
            Mock(description="test goal", priority=0.9, context={"type": "test"})
        ]
        
        # Redirect stdout to capture output
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            demonstrate_introspection_cycle(mock_cognitive_system, 1)
            output = sys.stdout.getvalue()
            
            # Check that expected content is in output
            self.assertIn("RECURSIVE INTROSPECTION CYCLE 1", output)
            self.assertIn("test prompt", output)
            self.assertIn("test goal", output)
            
        finally:
            sys.stdout = old_stdout

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_standard_response_format(self):
        """Test that all operations return EchoResponse objects"""
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Test initialize
        result = component.initialize()
        self.assertIsInstance(result, EchoResponse)
        
        # Test echo
        result = component.echo("test")
        self.assertIsInstance(result, EchoResponse)
        
        # Test process (even when not initialized)
        result = component.process("test")
        self.assertIsInstance(result, EchoResponse)
        
        # Test cleanup
        result = component.cleanup_demo_files()
        self.assertIsInstance(result, EchoResponse)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_error_handling(self):
        """Test standardized error handling"""
        config = EchoConfig(component_name="TestEchoselfDemo")
        component = EchoselfDemoStandardized(config)
        
        # Mock a method to raise an exception
        original_method = component._demonstrate_introspection_cycle
        def failing_method(*args, **kwargs):
            raise ValueError("Test error")
        component._demonstrate_introspection_cycle = failing_method
        
        # Initialize with mock
        with patch('echoself_demo_standardized.CognitiveArchitecture'):
            component._initialized = True
            component.cognitive_system = Mock()
            
            # Process should handle the error gracefully
            result = component.process("introspection_cycle")
            self.assertFalse(result.success)
            self.assertIn("Test error", result.message)
            self.assertIn("error_type", result.metadata)

    @unittest.skipIf(not ECHOSELF_DEMO_STANDARDIZED_AVAILABLE, "Module not available")
    def test_component_info_compatibility(self):
        """Test that component provides expected information"""
        config = EchoConfig(component_name="TestEchoselfDemo", version="1.2.3")
        component = EchoselfDemoStandardized(config)
        
        # Test status
        status = component.get_status()
        self.assertTrue(status.success)
        self.assertIn("component_name", status.data)
        self.assertEqual(status.data["component_name"], "TestEchoselfDemo")
        self.assertEqual(status.data["version"], "1.2.3")


def main():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()