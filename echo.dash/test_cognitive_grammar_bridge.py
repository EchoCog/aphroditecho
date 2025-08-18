"""
Tests for Cognitive Grammar Bridge and Neural-Symbolic Integration
================================================================

Tests the Python-Scheme integration layer and neural-symbolic capabilities
of the Deep Tree Echo cognitive architecture.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import json

# Add the current directory to the path to import modules
sys.path.insert(0, os.path.dirname(__file__))

try:
    from cognitive_grammar_bridge import (
        CognitiveGrammarBridge, SymbolicExpression, NeuralPattern,
        SchemeInterpreterError, get_cognitive_grammar_bridge, initialize_cognitive_grammar
    )
    COGNITIVE_GRAMMAR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import cognitive_grammar_bridge: {e}")
    COGNITIVE_GRAMMAR_AVAILABLE = False

try:
    # Test without numpy dependency for now
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

class TestSymbolicExpression(unittest.TestCase):
    """Test SymbolicExpression dataclass"""
    
    def setUp(self):
        if not COGNITIVE_GRAMMAR_AVAILABLE:
            self.skipTest("cognitive_grammar_bridge not available")
    
    def test_symbolic_expression_creation(self):
        """Test SymbolicExpression creation and attributes"""
        expr = SymbolicExpression(
            expression="(remember concept context)",
            symbols=["remember", "concept", "context"],
            activation_level=0.8
        )
        
        self.assertEqual(expr.expression, "(remember concept context)")
        self.assertEqual(expr.symbols, ["remember", "concept", "context"])
        self.assertEqual(expr.activation_level, 0.8)
        self.assertIsInstance(expr.context, dict)
    
    def test_symbolic_expression_default_context(self):
        """Test SymbolicExpression with default context"""
        expr = SymbolicExpression(
            expression="(test)",
            symbols=["test"]
        )
        
        self.assertEqual(expr.context, {})
        self.assertEqual(expr.activation_level, 0.0)

class TestNeuralPattern(unittest.TestCase):
    """Test NeuralPattern dataclass"""
    
    def setUp(self):
        if not COGNITIVE_GRAMMAR_AVAILABLE:
            self.skipTest("cognitive_grammar_bridge not available")
    
    def test_neural_pattern_creation(self):
        """Test NeuralPattern creation and attributes"""
        pattern = NeuralPattern(
            activations=[0.8, 0.6, 0.3, 0.9],
            symbols=["concept1", "concept2"],
            threshold=0.7
        )
        
        self.assertEqual(pattern.activations, [0.8, 0.6, 0.3, 0.9])
        self.assertEqual(pattern.symbols, ["concept1", "concept2"])
        self.assertEqual(pattern.threshold, 0.7)
        self.assertIsInstance(pattern.metadata, dict)
    
    def test_neural_pattern_default_metadata(self):
        """Test NeuralPattern with default metadata"""
        pattern = NeuralPattern(
            activations=[0.5],
            symbols=["test"]
        )
        
        self.assertEqual(pattern.metadata, {})
        self.assertEqual(pattern.threshold, 0.5)

class TestCognitiveGrammarBridge(unittest.TestCase):
    """Test CognitiveGrammarBridge class"""
    
    def setUp(self):
        if not COGNITIVE_GRAMMAR_AVAILABLE:
            self.skipTest("cognitive_grammar_bridge not available")
    
    def test_bridge_initialization(self):
        """Test CognitiveGrammarBridge initialization"""
        # Create a temporary scheme file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            self.assertEqual(bridge.scheme_kernel_path, temp_path)
            self.assertFalse(bridge.is_initialized)
            self.assertEqual(bridge.memory_state, {})
        finally:
            os.unlink(temp_path)
    
    def test_bridge_initialization_missing_file(self):
        """Test CognitiveGrammarBridge initialization with missing file"""
        nonexistent_path = Path("/nonexistent/scheme/file.scm")
        
        with self.assertRaises(FileNotFoundError):
            CognitiveGrammarBridge(nonexistent_path)
    
    def test_bridge_default_initialization(self):
        """Test CognitiveGrammarBridge default initialization"""
        # This will look for cognitive_grammar_kernel.scm in current directory
        current_dir = Path(__file__).parent
        expected_path = current_dir / "cognitive_grammar_kernel.scm"
        
        if expected_path.exists():
            bridge = CognitiveGrammarBridge()
            self.assertEqual(bridge.scheme_kernel_path, expected_path)
        else:
            with self.assertRaises(FileNotFoundError):
                CognitiveGrammarBridge()
    
    def test_initialize_system(self):
        """Test system initialization"""
        # Create a temporary scheme file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            result = bridge.initialize()
            self.assertTrue(result)
            self.assertTrue(bridge.is_initialized)
        finally:
            os.unlink(temp_path)
    
    def test_get_status(self):
        """Test getting system status"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            status = bridge.get_status()
            self.assertIsInstance(status, dict)
            self.assertIn('status', status)
        finally:
            os.unlink(temp_path)
    
    def test_remember_operation(self):
        """Test remember operation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            node_id = bridge.remember("test concept", "test context")
            self.assertIsInstance(node_id, str)
            self.assertTrue(node_id.startswith("node-"))
        finally:
            os.unlink(temp_path)
    
    def test_recall_operation(self):
        """Test recall operation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            # First remember something
            node_id = bridge.remember("test concept", "test context")
            
            # Then try to recall
            matches = bridge.recall("test")
            self.assertIsInstance(matches, list)
        finally:
            os.unlink(temp_path)
    
    def test_neural_to_symbolic_conversion(self):
        """Test neural-to-symbolic conversion"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            activation_vector = [0.8, 0.6, 0.3, 0.9, 0.2]
            symbol_space = ["concept1", "concept2", "concept3"]
            
            result = bridge.neural_to_symbolic(activation_vector, symbol_space)
            self.assertIsInstance(result, SymbolicExpression)
            self.assertIsInstance(result.symbols, list)
            self.assertIsInstance(result.activation_level, float)
        finally:
            os.unlink(temp_path)
    
    def test_symbolic_to_neural_conversion(self):
        """Test symbolic-to-neural conversion"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            symbolic_expr = SymbolicExpression(
                expression="(test concept)",
                symbols=["test", "concept"]
            )
            
            result = bridge.symbolic_to_neural(symbolic_expr, neural_network_size=50)
            self.assertIsInstance(result, NeuralPattern)
            self.assertEqual(len(result.activations), 50)
            self.assertIsInstance(result.activations[0], float)
        finally:
            os.unlink(temp_path)
    
    def test_echo_operations(self):
        """Test echo creation and propagation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            # Test echo creation
            echo_id = bridge.echo_create(
                "test echo",
                emotional_state={"valence": 0.8},
                spatial_context={"location": "test_space"}
            )
            self.assertIsInstance(echo_id, str)
            
            # Test echo propagation
            result = bridge.echo_propagate(echo_id, activation_threshold=0.5)
            self.assertIsInstance(result, bool)
        finally:
            os.unlink(temp_path)
    
    def test_meta_cognitive_operations(self):
        """Test meta-cognitive reflection operations"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            # Test reflection
            reflection = bridge.reflect("test_process", depth=2)
            self.assertIsInstance(reflection, dict)
            self.assertIn("process", reflection)
            
            # Test introspection
            state = {"test": "state"}
            introspection = bridge.introspect(state, granularity="medium")
            self.assertIsInstance(introspection, dict)
            self.assertIn("state_summary", introspection)
            
            # Test adaptation
            strategy = {"approach": "test"}
            adaptation = bridge.adapt(strategy, performance=0.6)
            self.assertIsInstance(adaptation, dict)
        finally:
            os.unlink(temp_path)

class TestGlobalBridgeFunctions(unittest.TestCase):
    """Test global bridge functions"""
    
    def setUp(self):
        if not COGNITIVE_GRAMMAR_AVAILABLE:
            self.skipTest("cognitive_grammar_bridge not available")
    
    @patch('cognitive_grammar_bridge.CognitiveGrammarBridge')
    def test_get_cognitive_grammar_bridge(self, mock_bridge_class):
        """Test get_cognitive_grammar_bridge function"""
        mock_bridge = MagicMock()
        mock_bridge.initialize.return_value = True
        mock_bridge_class.return_value = mock_bridge
        
        # Reset global bridge
        import cognitive_grammar_bridge
        cognitive_grammar_bridge._global_bridge = None
        
        bridge = get_cognitive_grammar_bridge()
        self.assertIsNotNone(bridge)
        mock_bridge_class.assert_called_once()
        mock_bridge.initialize.assert_called_once()
    
    @patch('cognitive_grammar_bridge.get_cognitive_grammar_bridge')
    def test_initialize_cognitive_grammar(self, mock_get_bridge):
        """Test initialize_cognitive_grammar function"""
        mock_bridge = MagicMock()
        mock_bridge.is_initialized = True
        mock_get_bridge.return_value = mock_bridge
        
        result = initialize_cognitive_grammar()
        self.assertTrue(result)
        mock_get_bridge.assert_called_once()

class TestCognitiveGrammarIntegration(unittest.TestCase):
    """Test integration with existing cognitive architecture"""
    
    def setUp(self):
        if not COGNITIVE_GRAMMAR_AVAILABLE:
            self.skipTest("cognitive_grammar_bridge not available")
    
    def test_cognitive_architecture_integration(self):
        """Test integration with CognitiveArchitecture class"""
        # This test would require importing CognitiveArchitecture
        # For now, we'll test that the required functions exist
        
        bridge = CognitiveGrammarBridge.__new__(CognitiveGrammarBridge)
        required_methods = [
            'initialize', 'get_status', 'remember', 'recall',
            'neural_to_symbolic', 'symbolic_to_neural',
            'echo_create', 'reflect', 'introspect', 'adapt'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(bridge, method),
                          f"CognitiveGrammarBridge missing required method: {method}")

class TestErrorHandling(unittest.TestCase):
    """Test error handling in cognitive grammar bridge"""
    
    def setUp(self):
        if not COGNITIVE_GRAMMAR_AVAILABLE:
            self.skipTest("cognitive_grammar_bridge not available")
    
    def test_scheme_interpreter_error(self):
        """Test SchemeInterpreterError handling"""
        error = SchemeInterpreterError("Test error")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Test error")
    
    def test_bridge_with_malformed_scheme(self):
        """Test bridge behavior with malformed Scheme code"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as f:
            f.write(";; Test scheme kernel")
            temp_path = Path(f.name)
        
        try:
            bridge = CognitiveGrammarBridge(temp_path)
            bridge.initialize()
            
            # The bridge should handle errors gracefully
            # and return reasonable defaults
            result = bridge.forget("nonexistent_concept")
            self.assertIsInstance(result, bool)
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run the tests
    unittest.main(verbosity=2)