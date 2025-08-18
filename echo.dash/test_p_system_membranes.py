import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deep_tree_echo import (
    DeepTreeEcho, Membrane, CognitiveMembrane, ExtensionMembrane, 
    SecurityMembrane, MembraneManager, MembraneMessage
)

class TestPSystemMembranes(unittest.TestCase):
    """Test cases for P-System Membranes implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.echo = DeepTreeEcho()
    
    def test_membrane_creation(self):
        """Test creation of different membrane types"""
        membrane = Membrane("test", "test")
        self.assertEqual(membrane.name, "test")
        self.assertEqual(membrane.membrane_type, "test")
        self.assertEqual(membrane.state, "initialized")
        
        cognitive = CognitiveMembrane()
        self.assertEqual(cognitive.name, "cognitive")
        self.assertIn("process", cognitive.permissions)
        
        extension = ExtensionMembrane()
        self.assertEqual(extension.name, "extension")
        self.assertIn("communicate", extension.permissions)
        
        security = SecurityMembrane()
        self.assertEqual(security.name, "security")
        self.assertIn("validate", security.permissions)
    
    def test_membrane_manager_initialization(self):
        """Test membrane manager initialization"""
        manager = MembraneManager()
        manager.initialize_default_membranes()
        
        self.assertTrue(manager.active)
        self.assertIn("root", manager.membranes)
        self.assertIn("cognitive", manager.membranes)
        self.assertIn("extension", manager.membranes)
        self.assertIn("security", manager.membranes)
        
        # Check hierarchy
        root = manager.membranes["root"]
        self.assertEqual(len(root.child_membranes), 3)
    
    def test_deep_tree_echo_membrane_integration(self):
        """Test DeepTreeEcho integration with membranes"""
        # Membrane manager should be initialized
        self.assertTrue(self.echo.membrane_manager.active)
        
        # Should have access to membrane methods
        status = self.echo.get_membrane_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(len(status), 4)  # root, cognitive, extension, security
    
    def test_message_passing(self):
        """Test inter-membrane communication"""
        # Send message from cognitive to extension
        success = self.echo.send_membrane_message(
            "cognitive", "extension", "test_message", {"data": "test"}
        )
        self.assertTrue(success)
        
        # Process messages
        results = self.echo.process_membrane_messages()
        self.assertIsInstance(results, dict)
    
    def test_extension_loading(self):
        """Test extension loading into membrane"""
        success = self.echo.load_extension_to_membrane(
            "test_extension", {"version": "1.0", "description": "Test extension"}
        )
        self.assertTrue(success)
        
        # Check extension was loaded
        extension_membrane = self.echo.membrane_manager.membranes["extension"]
        self.assertIn("test_extension", extension_membrane.loaded_extensions)
    
    def test_membrane_resource_allocation(self):
        """Test resource allocation for membranes"""
        membrane = Membrane("test", "test")
        
        # Allocate resources
        success = membrane.allocate_resources(memory=100, cpu=50, io=25)
        self.assertTrue(success)
        
        self.assertEqual(membrane.resources["memory"], 100)
        self.assertEqual(membrane.resources["cpu"], 50)
        self.assertEqual(membrane.resources["io"], 25)
    
    def test_membrane_message_structure(self):
        """Test membrane message creation and validation"""
        message = MembraneMessage(
            source_membrane="test_source",
            target_membrane="test_target", 
            message_type="test_type",
            data={"test": "data"}
        )
        
        self.assertEqual(message.source_membrane, "test_source")
        self.assertEqual(message.target_membrane, "test_target")
        self.assertEqual(message.message_type, "test_type")
        self.assertEqual(message.priority, 1)
        self.assertEqual(message.security_level, "standard")
    
    def test_cognitive_membrane_processing(self):
        """Test cognitive membrane specific functionality"""
        cognitive = CognitiveMembrane()
        
        # Test attention update
        message = MembraneMessage("test", "cognitive", "attention_update", 0.8)
        result = cognitive._handle_message(message)
        self.assertEqual(result["attention_level"], 0.8)
        
        # Test thought processing
        message = MembraneMessage("test", "cognitive", "process_thought", {"thought": "test"})
        result = cognitive._handle_message(message)
        self.assertEqual(result["status"], "processed")
    
    def test_security_membrane_validation(self):
        """Test security membrane functionality"""
        security = SecurityMembrane()
        
        # Test security check
        message = MembraneMessage("test", "security", "security_check", {"check": "test"})
        result = security._handle_message(message)
        self.assertEqual(result["status"], "security_validated")
        self.assertEqual(result["threat_level"], "low")
    
    def test_membrane_hierarchy(self):
        """Test membrane parent-child relationships"""
        parent = Membrane("parent", "parent")
        child = Membrane("child", "child")
        
        parent.add_child_membrane(child)
        
        self.assertEqual(child.parent_membrane, parent)
        self.assertIn(child, parent.child_membranes)
    
    def test_tree_echo_functionality_preserved(self):
        """Test that original DeepTreeEcho functionality is preserved"""
        # Create a tree
        root = self.echo.create_tree("Test content")
        self.assertIsNotNone(root)
        self.assertEqual(root.content, "Test content")
        
        # Add a child
        child = self.echo.add_child(root, "Child content")
        self.assertIsNotNone(child)
        self.assertEqual(child.content, "Child content")
        self.assertIn(child, root.children)
        
        # Calculate echo values
        echo_value = self.echo.calculate_echo_value(root)
        self.assertIsInstance(echo_value, float)
        
        # Test echo propagation
        self.echo.propagate_echoes()
        self.assertIsInstance(root.echo_value, float)

if __name__ == "__main__":
    unittest.main()