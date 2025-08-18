"""
Test suite for Echo9ml: Deep Tree Echo Persona Evolution System

Tests all major components and integration points of the echo9ml system
according to the specifications in echo9ml.md
"""

import unittest
import numpy as np
import tempfile
import json
from pathlib import Path
import time
from typing import Dict, Any

# Import echo9ml components
from echo9ml import (
    PersonaKernel, TensorPersonaEncoding, HypergraphPersonaEncoder,
    AttentionAllocationLayer, EvolutionEngine, MetaCognitiveEnhancer,
    Echo9mlSystem, PersonaTraitType, create_echo9ml_system
)

class TestPersonaKernel(unittest.TestCase):
    """Test PersonaKernel functionality"""
    
    def setUp(self):
        self.persona = PersonaKernel.create_deep_tree_echo()
    
    def test_persona_creation(self):
        """Test Deep Tree Echo persona kernel creation"""
        self.assertEqual(self.persona.name, "Deep Tree Echo")
        self.assertEqual(len(self.persona.traits), 7)
        
        # Check trait values are in valid range
        for trait, value in self.persona.traits.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_trait_connections(self):
        """Test hypergraph connections between traits"""
        # All traits should have connections
        for trait in PersonaTraitType:
            self.assertIn(trait, self.persona.trait_connections)
            self.assertIsInstance(self.persona.trait_connections[trait], set)
            self.assertGreater(len(self.persona.trait_connections[trait]), 0)
    
    def test_persona_initialization(self):
        """Test persona has proper initialization"""
        self.assertIsInstance(self.persona.history, list)
        self.assertIsInstance(self.persona.evolution, dict)
        self.assertIn("adaptation_rate", self.persona.evolution)
        self.assertGreater(self.persona.creation_time, 0)

class TestTensorPersonaEncoding(unittest.TestCase):
    """Test tensor encoding functionality"""
    
    def setUp(self):
        self.encoder = TensorPersonaEncoding()
        self.persona = PersonaKernel.create_deep_tree_echo()
    
    def test_tensor_shape(self):
        """Test tensor has correct prime factorized shape"""
        expected_shape = (3, 7, 13, 5, 2)  # Prime factorized dimensions
        self.assertEqual(self.encoder.tensor_shape, expected_shape)
        self.assertEqual(self.encoder.persona_tensor.shape, expected_shape)
    
    def test_encode_decode_cycle(self):
        """Test encoding and decoding persona preserves traits"""
        # Encode persona
        encoded = self.encoder.encode_persona(self.persona)
        self.assertIsInstance(encoded, np.ndarray)
        
        # Decode and compare
        decoded_traits = self.encoder.decode_persona()
        
        # Should have all trait types
        self.assertEqual(len(decoded_traits), len(PersonaTraitType))
        
        # Values should be reasonable (within [0, 1])
        for trait, value in decoded_traits.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_tensor_evolution(self):
        """Test tensor evolution mechanism"""
        # Get initial state
        self.encoder.encode_persona(self.persona)
        initial_tensor = self.encoder.persona_tensor.copy()
        
        # Apply evolution
        self.encoder.evolve_tensor(learning_rate=0.1)
        
        # Tensor should change but stay in valid range
        self.assertFalse(np.array_equal(initial_tensor, self.encoder.persona_tensor))
        self.assertTrue(np.all(self.encoder.persona_tensor >= 0))
        self.assertTrue(np.all(self.encoder.persona_tensor <= 1))
    
    def test_context_encoding(self):
        """Test different contexts are encoded correctly"""
        contexts = ["interaction", "learning", "creative", "analytical", "social"]
        
        for context in contexts:
            encoded = self.encoder.encode_persona(self.persona, context=context)
            self.assertIsInstance(encoded, np.ndarray)
            # Should not fail and should return valid tensor

class TestHypergraphPersonaEncoder(unittest.TestCase):
    """Test hypergraph encoding functionality"""
    
    def setUp(self):
        self.encoder = HypergraphPersonaEncoder()
    
    def test_add_trait_node(self):
        """Test adding trait nodes to hypergraph"""
        trait = PersonaTraitType.ROOTS
        value = 0.8
        
        self.encoder.add_trait_node(trait, value)
        
        node_id = f"trait_{trait.value}"
        self.assertIn(node_id, self.encoder.nodes)
        self.assertEqual(self.encoder.nodes[node_id]["value"], value)
        self.assertEqual(self.encoder.node_activations[node_id], value)
    
    def test_add_memory_node(self):
        """Test adding memory nodes to hypergraph"""
        content = "Test memory content"
        memory_type = "episodic"
        
        self.encoder.add_memory_node(content, memory_type)
        
        # Should have created a memory node
        memory_nodes = [n for n in self.encoder.nodes.values() if n["type"] == "memory"]
        self.assertEqual(len(memory_nodes), 1)
        self.assertEqual(memory_nodes[0]["content"], content)
        self.assertEqual(memory_nodes[0]["memory_type"], memory_type)
    
    def test_hyperedge_creation(self):
        """Test creating hyperedges between nodes"""
        # Add some nodes first
        self.encoder.add_trait_node(PersonaTraitType.ROOTS, 0.8)
        self.encoder.add_trait_node(PersonaTraitType.BRANCHES, 0.9)
        
        node1 = "trait_memory"
        node2 = "trait_reasoning"
        edge_id = "test_edge"
        
        self.encoder.create_hyperedge(edge_id, {node1, node2})
        
        self.assertIn(edge_id, self.encoder.hyperedges)
        self.assertEqual(self.encoder.hyperedges[edge_id], {node1, node2})
    
    def test_activation_spreading(self):
        """Test activation spreading through hypergraph"""
        # Create a simple hypergraph
        self.encoder.add_trait_node(PersonaTraitType.ROOTS, 0.8)
        self.encoder.add_trait_node(PersonaTraitType.BRANCHES, 0.3)
        
        node1 = "trait_memory" 
        node2 = "trait_reasoning"
        
        # Create connection
        self.encoder.create_hyperedge("connection", {node1, node2})
        
        # Spread activation from high-activation node
        initial_activation = self.encoder.node_activations[node2]
        self.encoder.spread_activation({node1})
        
        # Node2 should have increased activation
        self.assertGreater(self.encoder.node_activations[node2], initial_activation)

class TestAttentionAllocationLayer(unittest.TestCase):
    """Test attention allocation functionality"""
    
    def setUp(self):
        self.attention = AttentionAllocationLayer(total_attention=100.0)
    
    def test_salience_calculation(self):
        """Test salience score calculation"""
        item_id = "test_item"
        current_value = 0.7
        context = {
            "recency": 0.8,
            "importance": 0.9,
            "connectivity": 0.5
        }
        
        salience = self.attention.calculate_salience(item_id, current_value, context)
        
        # Should be a valid probability
        self.assertGreaterEqual(salience, 0.0)
        self.assertLessEqual(salience, 1.0)
        
        # Should be influenced by context
        self.assertGreater(salience, current_value)  # Should be boosted
    
    def test_attention_allocation(self):
        """Test attention allocation across items"""
        items = {
            "item1": (0.8, {"importance": 0.9, "recency": 0.8}),
            "item2": (0.5, {"importance": 0.3, "recency": 0.2}),
            "item3": (0.6, {"importance": 0.7, "recency": 0.5})
        }
        
        self.attention.allocate_attention(items)
        
        # Should have allocation for all items
        self.assertEqual(len(self.attention.attention_distribution), 3)
        
        # Total attention should sum to total_attention
        total_allocated = sum(self.attention.attention_distribution.values())
        self.assertAlmostEqual(total_allocated, 100.0, places=1)
        
        # Higher importance item should get more attention
        self.assertGreater(
            self.attention.attention_distribution["item1"],
            self.attention.attention_distribution["item2"]
        )
    
    def test_top_attention_items(self):
        """Test getting top attention items"""
        items = {
            f"item{i}": (0.5, {"importance": i * 0.1}) 
            for i in range(10)
        }
        
        self.attention.allocate_attention(items)
        top_items = self.attention.get_top_attention_items(3)
        
        self.assertEqual(len(top_items), 3)
        
        # Should be sorted by attention (descending)
        attentions = [attention for _, attention in top_items]
        self.assertEqual(attentions, sorted(attentions, reverse=True))

class TestEvolutionEngine(unittest.TestCase):
    """Test persona evolution functionality"""
    
    def setUp(self):
        self.engine = EvolutionEngine(learning_rate=0.1)
        self.persona = PersonaKernel.create_deep_tree_echo()
    
    def test_reinforcement_evolution(self):
        """Test reinforcement-based evolution"""
        initial_traits = self.persona.traits.copy()
        
        # Successful experience
        experience = {
            "type": "learning",
            "success": 0.9,
            "traits_used": [PersonaTraitType.BRANCHES, PersonaTraitType.GROWTH]
        }
        
        evolved_persona = self.engine.evolve_persona(self.persona, experience, "reinforcement")
        
        # Used traits should be strengthened
        self.assertGreater(
            evolved_persona.traits[PersonaTraitType.BRANCHES],
            initial_traits[PersonaTraitType.BRANCHES]
        )
        self.assertGreater(
            evolved_persona.traits[PersonaTraitType.GROWTH],
            initial_traits[PersonaTraitType.GROWTH]
        )
        
        # History should be updated
        self.assertGreater(len(evolved_persona.history), 0)
        self.assertEqual(evolved_persona.history[-1]["strategy"], "reinforcement")
    
    def test_exploration_evolution(self):
        """Test exploration-based evolution"""
        initial_traits = self.persona.traits.copy()
        
        # Novel experience
        experience = {
            "type": "exploration", 
            "novelty": 0.8,
            "success": 0.5
        }
        
        evolved_persona = self.engine.evolve_persona(self.persona, experience, "exploration")
        
        # Traits should change (mutation)
        changed_traits = 0
        for trait in PersonaTraitType:
            if abs(evolved_persona.traits[trait] - initial_traits[trait]) > 0.001:
                changed_traits += 1
        
        self.assertGreater(changed_traits, 0)  # At least some traits should change
    
    def test_stabilization_evolution(self):
        """Test stabilization-based evolution"""
        # Modify some traits first
        self.persona.traits[PersonaTraitType.ROOTS] = 0.3
        
        target_traits = {PersonaTraitType.ROOTS: 0.8}
        experience = {
            "type": "stabilization",
            "target_traits": target_traits,
            "stability_need": 0.7
        }
        
        initial_value = self.persona.traits[PersonaTraitType.ROOTS]
        evolved_persona = self.engine.evolve_persona(self.persona, experience, "stabilization")
        
        # Should move toward target but slowly due to high stability need
        final_value = evolved_persona.traits[PersonaTraitType.ROOTS]
        self.assertGreater(final_value, initial_value)
        self.assertLess(final_value, target_traits[PersonaTraitType.ROOTS])  # Not full jump

class TestMetaCognitiveEnhancer(unittest.TestCase):
    """Test meta-cognitive enhancement functionality"""
    
    def setUp(self):
        self.enhancer = MetaCognitiveEnhancer()
        self.persona = PersonaKernel.create_deep_tree_echo()
    
    def test_confidence_assessment(self):
        """Test confidence assessment"""
        # Good experiences
        experiences = [
            {"success": 0.8, "type": "learning"},
            {"success": 0.9, "type": "problem_solving"},
            {"success": 0.7, "type": "interaction"}
        ]
        
        confidence = self.enhancer.assess_confidence(self.persona, experiences)
        
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertGreater(confidence, 0.7)  # Should be high for good experiences
    
    def test_adaptability_assessment(self):
        """Test adaptability assessment"""
        # Add some history with trait changes
        self.persona.history = [
            {"trait_changes": {"memory": 0.1, "reasoning": -0.05}},
            {"trait_changes": {"memory": -0.08, "reasoning": 0.12}},
            {"trait_changes": {"expression": 0.06, "reasoning": 0.03}}
        ]
        
        adaptability = self.enhancer.assess_adaptability(self.persona)
        
        self.assertGreaterEqual(adaptability, 0.0)
        self.assertLessEqual(adaptability, 1.0)
    
    def test_modification_suggestions(self):
        """Test modification suggestions"""
        # Create imbalanced traits
        self.persona.traits = {
            PersonaTraitType.ROOTS: 0.9,
            PersonaTraitType.BRANCHES: 0.9,
            PersonaTraitType.LEAVES: 0.1,  # Very low
            PersonaTraitType.TRUNK: 0.8,
            PersonaTraitType.GROWTH: 0.9,
            PersonaTraitType.CANOPY: 0.1,  # Very low
            PersonaTraitType.NETWORK: 0.8
        }
        
        performance_metrics = {"success_trend": 0.0}
        suggestions = self.enhancer.suggest_modifications(self.persona, performance_metrics)
        
        self.assertIsInstance(suggestions, list)
        # Should suggest trait rebalancing
        suggestion_types = [s["type"] for s in suggestions]
        self.assertIn("trait_rebalancing", suggestion_types)

class TestEcho9mlSystem(unittest.TestCase):
    """Test complete Echo9ml system integration"""
    
    def setUp(self):
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.system = Echo9mlSystem(save_path=self.temp_dir)
    
    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initializes all components"""
        self.assertIsInstance(self.system.persona_kernel, PersonaKernel)
        self.assertIsInstance(self.system.tensor_encoding, TensorPersonaEncoding)
        self.assertIsInstance(self.system.hypergraph_encoder, HypergraphPersonaEncoder)
        self.assertIsInstance(self.system.attention_layer, AttentionAllocationLayer)
        self.assertIsInstance(self.system.evolution_engine, EvolutionEngine)
        self.assertIsInstance(self.system.meta_cognitive, MetaCognitiveEnhancer)
        
        self.assertEqual(self.system.interaction_count, 0)
        self.assertIsInstance(self.system.system_log, list)
    
    def test_experience_processing_pipeline(self):
        """Test complete experience processing pipeline"""
        experience = {
            "type": "learning",
            "content": "Learning about tensor operations",
            "success": 0.8,
            "novelty": 0.6,
            "importance": 0.7,
            "context": "learning",
            "valence": 0.3
        }
        
        result = self.system.process_experience(experience)
        
        # Check result structure
        self.assertIn("interaction_id", result)
        self.assertIn("persona_state", result)
        self.assertIn("attention_allocation", result)
        self.assertIn("evolution_strategy", result)
        self.assertIn("suggestions", result)
        
        # Check system state updated
        self.assertEqual(self.system.interaction_count, 1)
        self.assertEqual(len(self.system.system_log), 1)
        
        # Check persona evolved
        self.assertGreater(len(self.system.persona_kernel.history), 0)
    
    def test_multiple_experiences(self):
        """Test processing multiple experiences"""
        experiences = [
            {"type": "learning", "success": 0.8, "importance": 0.7},
            {"type": "creative", "success": 0.6, "novelty": 0.9},
            {"type": "social", "success": 0.7, "importance": 0.5},
            {"type": "analytical", "success": 0.9, "importance": 0.8}
        ]
        
        results = []
        for exp in experiences:
            result = self.system.process_experience(exp)
            results.append(result)
        
        self.assertEqual(len(results), 4)
        self.assertEqual(self.system.interaction_count, 4)
        
        # Check interactions are numbered correctly
        for i, result in enumerate(results):
            self.assertEqual(result["interaction_id"], i + 1)
    
    def test_cognitive_snapshot(self):
        """Test cognitive snapshot generation"""
        # Process some experiences first
        for i in range(3):
            self.system.process_experience({
                "type": "test",
                "success": 0.7 + i * 0.1,
                "importance": 0.5
            })
        
        snapshot = self.system.get_cognitive_snapshot()
        
        # Check snapshot structure
        required_keys = [
            "persona_kernel", "tensor_encoding", "hypergraph",
            "attention", "meta_cognitive", "system_stats"
        ]
        for key in required_keys:
            self.assertIn(key, snapshot)
        
        # Check system stats
        self.assertEqual(snapshot["system_stats"]["interaction_count"], 3)
        self.assertGreater(snapshot["system_stats"]["total_evolution_events"], 0)
    
    def test_save_and_load_state(self):
        """Test saving and loading system state"""
        # Process some experiences
        for i in range(2):
            self.system.process_experience({
                "type": "test",
                "success": 0.8,
                "traits_used": [PersonaTraitType.BRANCHES]
            })
        
        initial_traits = self.system.persona_kernel.traits.copy()
        initial_count = self.system.interaction_count
        
        # Save state
        self.system.save_state()
        
        # Verify files were created
        save_path = Path(self.temp_dir)
        self.assertTrue((save_path / 'echo9ml_snapshot.json').exists())
        self.assertTrue((save_path / 'persona_tensor.npy').exists())
        self.assertTrue((save_path / 'system_log.json').exists())
        
        # Create new system and load state
        new_system = Echo9mlSystem(save_path=self.temp_dir)
        loaded = new_system.load_state()
        
        self.assertTrue(loaded)
        
        # Check traits were restored (approximately)
        for trait in PersonaTraitType:
            self.assertAlmostEqual(
                new_system.persona_kernel.traits[trait],
                initial_traits[trait],
                places=2
            )
    
    def test_convenience_function(self):
        """Test convenience function for system creation"""
        system = create_echo9ml_system()
        self.assertIsInstance(system, Echo9mlSystem)
        
        # Should work with custom path too
        system_with_path = create_echo9ml_system(self.temp_dir)
        self.assertIsInstance(system_with_path, Echo9mlSystem)

class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.system = Echo9mlSystem(save_path=self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_learning_scenario(self):
        """Test a realistic learning scenario"""
        # Simulate learning progression
        learning_experiences = [
            {"type": "learning", "success": 0.3, "novelty": 0.8, "difficulty": 0.9},  # Hard start
            {"type": "learning", "success": 0.5, "novelty": 0.6, "difficulty": 0.8},  # Getting better
            {"type": "learning", "success": 0.7, "novelty": 0.4, "difficulty": 0.7},  # Improving
            {"type": "learning", "success": 0.8, "novelty": 0.2, "difficulty": 0.6},  # Mastery
            {"type": "learning", "success": 0.9, "novelty": 0.1, "difficulty": 0.5}   # Expert
        ]
        
        initial_reasoning = self.system.persona_kernel.traits[PersonaTraitType.BRANCHES]
        
        for exp in learning_experiences:
            exp["traits_used"] = [PersonaTraitType.BRANCHES, PersonaTraitType.GROWTH]
            result = self.system.process_experience(exp)
        
        final_reasoning = self.system.persona_kernel.traits[PersonaTraitType.BRANCHES]
        
        # Reasoning should improve with successful learning
        self.assertGreater(final_reasoning, initial_reasoning)
        
        # Confidence should improve or at least stay stable
        snapshot = self.system.get_cognitive_snapshot()
        confidence_trend = self.system.meta_cognitive.confidence_history
        if len(confidence_trend) >= 2:
            # Either improved or remained stable (allowing for small numerical differences)
            self.assertGreaterEqual(confidence_trend[-1], confidence_trend[0] - 0.01)
    
    def test_creative_exploration_scenario(self):
        """Test creative exploration with novel experiences"""
        creative_experiences = [
            {"type": "creative", "success": 0.6, "novelty": 0.9, "originality": 0.8},
            {"type": "creative", "success": 0.7, "novelty": 0.8, "originality": 0.9},
            {"type": "creative", "success": 0.5, "novelty": 0.9, "originality": 0.7},  # Experimental failure
            {"type": "creative", "success": 0.8, "novelty": 0.7, "originality": 0.8}
        ]
        
        initial_creativity = self.system.persona_kernel.traits[PersonaTraitType.CANOPY]
        
        for exp in creative_experiences:
            exp["traits_used"] = [PersonaTraitType.CANOPY, PersonaTraitType.LEAVES]
            result = self.system.process_experience(exp)
        
        # Should show adaptation to creative challenges
        self.assertGreater(len(self.system.system_log), 0)
        
        # Evolution history should show creativity-focused adaptations
        evolution_events = self.system.evolution_engine.evolution_history
        self.assertGreater(len(evolution_events), 0)
    
    def test_adaptation_under_stress(self):
        """Test system adaptation under challenging conditions"""
        # Simulate challenging/stressful experiences
        stress_experiences = [
            {"type": "challenge", "success": 0.2, "stress": 0.9, "time_pressure": 0.8},
            {"type": "challenge", "success": 0.3, "stress": 0.8, "time_pressure": 0.9},
            {"type": "challenge", "success": 0.4, "stress": 0.7, "time_pressure": 0.7},
            {"type": "recovery", "success": 0.8, "stress": 0.3, "time_pressure": 0.2}  # Recovery
        ]
        
        results = []
        for exp in stress_experiences:
            result = self.system.process_experience(exp)
            results.append(result)
        
        # System should generate suggestions for handling stress
        all_suggestions = []
        for result in results:
            all_suggestions.extend(result.get("suggestions", []))
        
        # Should have some suggestions by the end
        self.assertGreater(len(all_suggestions), 0)
        
        # Meta-cognitive system should track changes
        self.assertGreater(len(self.system.meta_cognitive.confidence_history), 0)

if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run all tests
    unittest.main(verbosity=2)