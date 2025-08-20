#!/usr/bin/env python3
"""
Test for Echo Memory Demo Standardization

This test validates that the standardized Echo Memory Demo component follows
all the Echo API standards and provides the expected functionality.
"""

import sys
import unittest
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from echo_memory_demo_standardized import EchoMemoryDemoStandardized, create_memory_demo_system
from echo_component_base import EchoConfig, EchoResponse, validate_echo_component


class TestEchoMemoryDemoStandardization(unittest.TestCase):
    """Test suite for Echo Memory Demo standardization"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = EchoConfig(
            component_name="test_memory_demo",
            version="1.0.0",
            echo_threshold=0.75
        )
        self.demo = EchoMemoryDemoStandardized(self.config)
    
    def test_component_validation(self):
        """Test that component passes Echo validation"""
        self.assertTrue(validate_echo_component(self.demo))
    
    def test_initialization(self):
        """Test component initialization"""
        result = self.demo.initialize()
        
        self.assertTrue(result.success)
        self.assertIn("initialized successfully", result.message)
        self.assertTrue(self.demo._initialized)
        self.assertIsNotNone(result.metadata)
        self.assertEqual(result.metadata["component_name"], "test_memory_demo")
    
    def test_store_operation(self):
        """Test memory store operation"""
        self.demo.initialize()
        
        store_data = {
            "action": "store",
            "key": "test_key",
            "data": {"value": "test data"}
        }
        
        result = self.demo.process(store_data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["key"], "test_key")
        self.assertTrue(result.data["stored"])
        self.assertIn("Successfully stored", result.message)
    
    def test_retrieve_operation(self):
        """Test memory retrieve operation"""
        self.demo.initialize()
        
        # First store some data
        store_data = {
            "action": "store",
            "key": "retrieve_test",
            "data": {"message": "hello world"}
        }
        self.demo.process(store_data)
        
        # Then retrieve it
        retrieve_data = {
            "action": "retrieve",
            "key": "retrieve_test"
        }
        
        result = self.demo.process(retrieve_data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["key"], "retrieve_test")
        self.assertEqual(result.data["data"]["message"], "hello world")
        self.assertIn("Successfully retrieved", result.message)
    
    def test_retrieve_nonexistent(self):
        """Test retrieving non-existent memory"""
        self.demo.initialize()
        
        retrieve_data = {
            "action": "retrieve",
            "key": "nonexistent_key"
        }
        
        result = self.demo.process(retrieve_data)
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message)
        self.assertEqual(result.metadata["key"], "nonexistent_key")
        self.assertFalse(result.metadata["found"])
    
    def test_list_operation(self):
        """Test memory list operation"""
        self.demo.initialize()
        
        # Store multiple items
        for i in range(3):
            store_data = {
                "action": "store", 
                "key": f"list_test_{i}",
                "data": {"index": i}
            }
            self.demo.process(store_data)
        
        # List memories
        result = self.demo.process({"action": "list"})
        
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.data["total_memories"], 3)
        self.assertIsInstance(result.data["memory_keys"], list)
        self.assertIn("Listed", result.message)
    
    def test_demo_basic_operation(self):
        """Test basic demo operation"""
        self.demo.initialize()
        
        result = self.demo.process({"action": "demo", "demo_type": "basic"})
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["demo_type"], "basic")
        self.assertIn("demo_key", result.data)
        self.assertIn("demo_data", result.data)
        self.assertIn("message", result.data["demo_data"])
    
    def test_demo_performance_operation(self):
        """Test performance demo operation"""
        self.demo.initialize()
        
        result = self.demo.process({"action": "demo", "demo_type": "performance"})
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["demo_type"], "performance")
        self.assertEqual(result.data["operations_performed"], 5)
        self.assertGreater(result.data["duration_seconds"], 0)
        self.assertGreater(result.data["operations_per_second"], 0)
    
    def test_echo_operation(self):
        """Test echo operation"""
        self.demo.initialize()
        
        # Store some data first to make echo more interesting
        self.demo.process({
            "action": "store",
            "key": "echo_test", 
            "data": {"test": "data"}
        })
        
        test_data = {"input": "test echo"}
        result = self.demo.echo(test_data, echo_value=0.9)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["echo_value"], 0.9)
        self.assertIn("memory_state", result.data)
        self.assertGreaterEqual(result.data["memory_state"]["total_memories"], 1)
        self.assertEqual(result.data["input_echo"], test_data)
        self.assertIn("timestamp", result.data)
    
    def test_invalid_action(self):
        """Test handling of invalid actions"""
        self.demo.initialize()
        
        result = self.demo.process({"action": "invalid_action"})
        
        self.assertFalse(result.success)
        self.assertIn("Unknown action", result.message)
    
    def test_factory_function(self):
        """Test the factory function"""
        demo = create_memory_demo_system()
        
        self.assertIsInstance(demo, EchoMemoryDemoStandardized)
        self.assertTrue(validate_echo_component(demo))
        self.assertTrue(demo._initialized)
        self.assertEqual(demo.config.component_name, "EchoMemoryDemo")
    
    def test_operation_counting(self):
        """Test that operations are counted correctly"""
        self.demo.initialize()
        
        initial_count = self.demo.operation_count
        
        # Perform several operations
        self.demo.process({"action": "demo", "demo_type": "basic"})
        self.demo.process({"action": "list"})
        self.demo.process({"action": "demo", "demo_type": "performance"})
        
        # Check count increased
        self.assertEqual(self.demo.operation_count, initial_count + 3)
    
    def test_error_handling(self):
        """Test error handling with invalid input"""
        self.demo.initialize()
        
        # Test store without key
        result = self.demo.process({"action": "store", "data": "test"})
        self.assertFalse(result.success)
        self.assertIn("requires 'key'", result.message)
        
        # Test retrieve without key
        result = self.demo.process({"action": "retrieve"})
        self.assertFalse(result.success)
        self.assertIn("requires 'key'", result.message)
    
    def test_response_format_consistency(self):
        """Test that all operations return consistent EchoResponse format"""
        self.demo.initialize()
        
        operations = [
            {"action": "demo", "demo_type": "basic"},
            {"action": "list"},
            {"action": "store", "key": "format_test", "data": {"test": "data"}},
            {"action": "retrieve", "key": "format_test"}
        ]
        
        for operation in operations:
            result = self.demo.process(operation)
            
            # All results should be EchoResponse objects
            self.assertIsInstance(result, EchoResponse)
            self.assertIsInstance(result.success, bool)
            self.assertIsInstance(result.message, str)
            self.assertIsNotNone(result.timestamp)
            
            if result.success:
                self.assertIsNotNone(result.data)


def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🧪 Running Echo Memory Demo Standardization Tests")
    print("=" * 60)
    
    # Run unittest suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestEchoMemoryDemoStandardization)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    print("\n" + "=" * 60)
    
    if result.wasSuccessful():
        print("✅ All tests passed! Echo Memory Demo standardization is successful.")
        print("\n📊 Test Results:")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        print("\n🎯 Standardization Benefits Validated:")
        print("   ✅ Component passes Echo validation")
        print("   ✅ Consistent EchoResponse format")
        print("   ✅ Proper error handling")
        print("   ✅ Standard initialization pattern")
        print("   ✅ Memory component inheritance working")
        print("   ✅ Factory function integration")
        print("   ✅ Operation counting and tracking")
        
        return True
    else:
        print("❌ Some tests failed!")
        for failure in result.failures:
            print(f"   FAIL: {failure[0]}")
        for error in result.errors:
            print(f"   ERROR: {error[0]}")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)