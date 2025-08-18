"""
Integration test for Echoself recursive self-model integration
"""

import unittest
import tempfile
import logging
from pathlib import Path
from cognitive_architecture import CognitiveArchitecture


class TestEchoselfIntegration(unittest.TestCase):
    """Test the integration of Echoself with CognitiveArchitecture"""
    
    def setUp(self):
        """Set up test environment"""
        # Suppress logs during testing
        logging.disable(logging.CRITICAL)
        self.cognitive_arch = CognitiveArchitecture()
    
    def tearDown(self):
        """Clean up test environment"""
        logging.disable(logging.NOTSET)
    
    def test_introspection_system_initialization(self):
        """Test that introspection system initializes properly"""
        # The system should have introspection available
        self.assertIsNotNone(self.cognitive_arch.echoself_introspection)
    
    def test_recursive_introspection_execution(self):
        """Test performing recursive introspection"""
        # Perform introspection with specific parameters
        prompt = self.cognitive_arch.perform_recursive_introspection(
            current_cognitive_load=0.6,
            recent_activity_level=0.4
        )
        
        # Should return a valid prompt
        self.assertIsNotNone(prompt)
        self.assertIsInstance(prompt, str)
        self.assertIn("DeepTreeEcho", prompt)
        self.assertIn("Repository Hypergraph Analysis", prompt)
    
    def test_introspection_with_automatic_calculation(self):
        """Test introspection with automatic cognitive load calculation"""
        prompt = self.cognitive_arch.perform_recursive_introspection()
        
        # Should still work with calculated values
        self.assertIsNotNone(prompt)
        self.assertIsInstance(prompt, str)
    
    def test_introspection_metrics_retrieval(self):
        """Test getting introspection metrics"""
        # First perform some introspection to generate metrics
        self.cognitive_arch.perform_recursive_introspection(0.5, 0.3)
        
        # Get metrics
        metrics = self.cognitive_arch.get_introspection_metrics()
        
        # Should return valid metrics
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_decisions", metrics)
        self.assertIn("hypergraph_nodes", metrics)
    
    def test_adaptive_goal_generation_with_introspection(self):
        """Test goal generation enhanced with introspection"""
        goals = self.cognitive_arch.adaptive_goal_generation_with_introspection()
        
        # Should generate some goals
        self.assertIsInstance(goals, list)
        self.assertGreater(len(goals), 0)
        
        # Check for introspection-specific goals
        introspection_goals = [
            g for g in goals 
            if "introspection" in g.description.lower() or 
               "hypergraph" in g.description.lower()
        ]
        self.assertGreater(len(introspection_goals), 0)
    
    def test_cognitive_load_calculation(self):
        """Test cognitive load calculation"""
        load = self.cognitive_arch._calculate_current_cognitive_load()
        
        # Should be a valid float between 0.1 and 0.9
        self.assertIsInstance(load, float)
        self.assertGreaterEqual(load, 0.1)
        self.assertLessEqual(load, 0.9)
    
    def test_recent_activity_calculation(self):
        """Test recent activity calculation"""
        activity = self.cognitive_arch._calculate_recent_activity()
        
        # Should be a valid float between 0.1 and 1.0
        self.assertIsInstance(activity, float)
        self.assertGreaterEqual(activity, 0.1)
        self.assertLessEqual(activity, 1.0)
    
    def test_introspection_memory_storage(self):
        """Test that introspection creates memories"""
        initial_memory_count = len(self.cognitive_arch.memories)
        
        # Perform introspection
        self.cognitive_arch.perform_recursive_introspection(0.5, 0.3)
        
        # Should have created a new memory
        self.assertGreater(len(self.cognitive_arch.memories), initial_memory_count)
        
        # Check for introspection memory
        introspection_memories = [
            m for m in self.cognitive_arch.memories.values()
            if "introspection" in m.content.lower()
        ]
        self.assertGreater(len(introspection_memories), 0)
    
    def test_export_introspection_data(self):
        """Test exporting introspection data"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Perform introspection to generate data
            self.cognitive_arch.perform_recursive_introspection(0.5, 0.3)
            
            # Export data
            success = self.cognitive_arch.export_introspection_data(tmp_path)
            
            # Should succeed
            self.assertTrue(success)
            
            # File should exist
            self.assertTrue(Path(tmp_path).exists())
            
        finally:
            # Clean up
            Path(tmp_path).unlink(missing_ok=True)


class TestIntrospectionEnhancedBehavior(unittest.TestCase):
    """Test enhanced cognitive behaviors with introspection"""
    
    def setUp(self):
        """Set up test environment"""
        logging.disable(logging.CRITICAL)
        self.cognitive_arch = CognitiveArchitecture()
    
    def tearDown(self):
        """Clean up test environment"""
        logging.disable(logging.NOTSET)
    
    def test_introspection_influences_personality(self):
        """Test that introspection can influence personality development"""
        # Get initial curiosity level
        initial_curiosity = self.cognitive_arch.personality_traits["curiosity"].current_value
        
        # Perform introspection
        self.cognitive_arch.perform_recursive_introspection()
        
        # Generate introspection-enhanced goals
        goals = self.cognitive_arch.adaptive_goal_generation_with_introspection()
        
        # Should have goals that could influence personality
        exploration_goals = [
            g for g in goals
            if "explore" in g.description.lower() or "analyze" in g.description.lower()
        ]
        self.assertGreater(len(exploration_goals), 0)
    
    def test_recursive_feedback_loop(self):
        """Test recursive feedback between introspection and goal generation"""
        initial_memory_count = len(self.cognitive_arch.memories)
        
        # Perform multiple cycles
        for i in range(3):
            # Introspect
            prompt = self.cognitive_arch.perform_recursive_introspection()
            self.assertIsNotNone(prompt)
            
            # Generate goals
            goals = self.cognitive_arch.adaptive_goal_generation_with_introspection()
            self.assertGreater(len(goals), 0)
        
        # Should have at least created some new memories over all cycles
        final_memory_count = len(self.cognitive_arch.memories)
        self.assertGreater(final_memory_count, initial_memory_count)
    
    def test_attention_allocation_adaptation(self):
        """Test that attention allocation adapts over time"""
        metrics_1 = self.cognitive_arch.get_introspection_metrics()
        
        # Perform several introspections with different loads
        for load in [0.3, 0.7, 0.5, 0.9, 0.2]:
            self.cognitive_arch.perform_recursive_introspection(load, 0.5)
        
        metrics_2 = self.cognitive_arch.get_introspection_metrics()
        
        # Should have more decisions in history
        self.assertGreater(
            metrics_2.get("total_decisions", 0), 
            metrics_1.get("total_decisions", 0)
        )


if __name__ == "__main__":
    unittest.main()