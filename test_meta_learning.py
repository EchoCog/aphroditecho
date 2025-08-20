"""
Tests for Meta-Learning System

Tests the meta-learning optimizer, experience replay, DTESN integration,
and integration with evolution engine.
"""

import asyncio
import numpy as np
from typing import Dict, Any, Tuple
from unittest.mock import Mock

# Import the components under test
from echo_self.meta_learning import (
    MetaLearningOptimizer,
    MetaLearningConfig,
    ExperienceReplay,
    ArchitecturePerformance,
    DTESNMetaLearningBridge,
    DTESNPerformanceMetrics
)
from echo_self.core.evolution_engine import EchoSelfEvolutionEngine, EvolutionConfig, Individual
from datetime import datetime


class MockIndividual(Individual):
    """Mock individual for testing."""
    
    def __init__(self, genome: Dict[str, Any]):
        super().__init__(genome)
        
    async def evaluate_fitness(self, environment) -> float:
        """Mock fitness evaluation."""
        # Simple fitness based on genome values
        return sum(float(v) for v in self.genome.values() if isinstance(v, (int, float))) / len(self.genome)
    
    def mutate(self, mutation_rate: float) -> 'MockIndividual':
        """Mock mutation."""
        new_genome = self.genome.copy()
        for key, value in new_genome.items():
            if isinstance(value, (int, float)) and np.random.random() < mutation_rate:
                new_genome[key] = value + np.random.normal(0, 0.1)
        return MockIndividual(new_genome)
    
    def crossover(self, other: 'MockIndividual') -> Tuple['MockIndividual', 'MockIndividual']:
        """Mock crossover."""
        offspring1_genome = {}
        offspring2_genome = {}
        
        for key in self.genome.keys():
            if key in other.genome:
                if np.random.random() < 0.5:
                    offspring1_genome[key] = self.genome[key]
                    offspring2_genome[key] = other.genome[key]
                else:
                    offspring1_genome[key] = other.genome[key]
                    offspring2_genome[key] = self.genome[key]
        
        return MockIndividual(offspring1_genome), MockIndividual(offspring2_genome)


class TestMetaLearningOptimizer:
    """Test cases for MetaLearningOptimizer."""
    
    async def test_initialization(self):
        """Test meta-learning optimizer initialization."""
        config = MetaLearningConfig(learning_rate=0.002, memory_size=500)
        optimizer = MetaLearningOptimizer(config)
        
        assert optimizer.config.learning_rate == 0.002
        assert optimizer.config.memory_size == 500
        assert len(optimizer.experience_replay.experiences) == 0
        assert optimizer.update_count == 0
    
    async def test_record_architecture_performance(self):
        """Test recording architecture performance."""
        optimizer = MetaLearningOptimizer(MetaLearningConfig())
        
        arch_params = {'layer_count': 3, 'hidden_size': 128, 'learning_rate': 0.001}
        await optimizer.record_architecture_performance(
            architecture_params=arch_params,
            fitness_score=0.85,
            generation=5,
            convergence_rate=0.02,
            diversity_metric=0.7
        )
        
        assert len(optimizer.experience_replay.experiences) == 1
        experience = optimizer.experience_replay.experiences[0]
        assert experience.fitness_score == 0.85
        assert experience.generation == 5
        assert experience.architecture_params == arch_params
    
    async def test_optimize_evolution_parameters(self):
        """Test optimization of evolution parameters."""
        optimizer = MetaLearningOptimizer(MetaLearningConfig(batch_size=5))
        
        # Add some experience data
        for i in range(10):
            await optimizer.record_architecture_performance(
                architecture_params={'layer_count': i + 1, 'hidden_size': 64 + i * 8},
                fitness_score=0.5 + i * 0.05,
                generation=i,
                convergence_rate=0.01,
                diversity_metric=0.5
            )
        
        current_params = {
            'mutation_rate': 0.01,
            'selection_pressure': 0.8,
            'crossover_rate': 0.7
        }
        
        optimized_params = await optimizer.optimize_evolution_parameters(current_params)
        
        assert 'mutation_rate' in optimized_params
        assert 'selection_pressure' in optimized_params
        assert 'crossover_rate' in optimized_params
    
    async def test_get_architecture_recommendations(self):
        """Test architecture recommendations."""
        optimizer = MetaLearningOptimizer(MetaLearningConfig())
        
        # Add experience data
        arch_params_list = [
            {'layer_count': 2, 'hidden_size': 64},
            {'layer_count': 3, 'hidden_size': 128},
            {'layer_count': 4, 'hidden_size': 256}
        ]
        
        fitness_scores = [0.6, 0.8, 0.9]
        
        for arch_params, fitness in zip(arch_params_list, fitness_scores):
            await optimizer.record_architecture_performance(
                architecture_params=arch_params,
                fitness_score=fitness,
                generation=1
            )
        
        recommendations = await optimizer.get_architecture_recommendations(2)
        
        assert len(recommendations) <= 2
        if recommendations:
            # Should be ordered by fitness (highest first)
            assert recommendations[0]['expected_fitness'] >= recommendations[-1]['expected_fitness']


class TestExperienceReplay:
    """Test cases for ExperienceReplay."""
    
    def test_initialization(self):
        """Test experience replay initialization."""
        replay = ExperienceReplay(max_size=100)
        assert replay.max_size == 100
        assert len(replay.experiences) == 0
    
    def test_add_experience(self):
        """Test adding experiences."""
        replay = ExperienceReplay(max_size=3)
        
        for i in range(5):
            experience = ArchitecturePerformance(
                architecture_params={'layer': i},
                fitness_score=float(i),
                generation=i,
                timestamp=datetime.now(),
                convergence_rate=0.01,
                diversity_metric=0.5
            )
            replay.add_experience(experience)
        
        # Should only keep the last 3 experiences (max_size=3)
        assert len(replay.experiences) == 3
        assert replay.experiences[0].architecture_params['layer'] == 2  # First kept
        assert replay.experiences[-1].architecture_params['layer'] == 4  # Last added
    
    def test_sample_batch(self):
        """Test batch sampling."""
        replay = ExperienceReplay()
        
        # Add experiences with different fitness scores
        for i in range(10):
            experience = ArchitecturePerformance(
                architecture_params={'value': i},
                fitness_score=i * 0.1,  # 0.0 to 0.9
                generation=i,
                timestamp=datetime.now(),
                convergence_rate=0.01,
                diversity_metric=0.5
            )
            replay.add_experience(experience)
        
        batch = replay.sample_batch(5)
        assert len(batch) == 5
        
        # Test sampling more than available
        small_batch = replay.sample_batch(15)
        assert len(small_batch) == 10  # Should return all available
    
    def test_get_top_performers(self):
        """Test getting top performers."""
        replay = ExperienceReplay()
        
        fitness_scores = [0.2, 0.8, 0.5, 0.9, 0.1, 0.7]
        
        for i, fitness in enumerate(fitness_scores):
            experience = ArchitecturePerformance(
                architecture_params={'id': i},
                fitness_score=fitness,
                generation=i,
                timestamp=datetime.now(),
                convergence_rate=0.01,
                diversity_metric=0.5
            )
            replay.add_experience(experience)
        
        top_performers = replay.get_top_performers(3)
        
        assert len(top_performers) == 3
        # Should be ordered by fitness (highest first)
        assert top_performers[0].fitness_score == 0.9
        assert top_performers[1].fitness_score == 0.8
        assert top_performers[2].fitness_score == 0.7


class TestDTESNMetaLearningBridge:
    """Test cases for DTESNMetaLearningBridge."""
    
    async def test_initialization(self):
        """Test DTESN bridge initialization."""
        bridge = DTESNMetaLearningBridge()
        
        assert bridge.meta_optimizer is None
        assert bridge.dtesn_kernel is None
        assert 'membrane_hierarchy_depth' in bridge.dtesn_meta_params
    
    async def test_extract_dtesn_metrics(self):
        """Test DTESN metrics extraction."""
        bridge = DTESNMetaLearningBridge()
        
        metrics = await bridge.extract_dtesn_metrics()
        
        assert isinstance(metrics, DTESNPerformanceMetrics)
        assert 0 <= metrics.membrane_efficiency <= 1
        assert 0 <= metrics.reservoir_stability <= 1
        assert 0 <= metrics.b_series_convergence <= 1
        assert isinstance(metrics.memory_usage, dict)
        assert isinstance(metrics.computation_time, dict)
    
    async def test_optimize_dtesn_parameters(self):
        """Test DTESN parameter optimization."""
        bridge = DTESNMetaLearningBridge()
        
        current_config = {
            'membrane_hierarchy_depth': 8,
            'reservoir_size_factor': 1.0,
            'b_series_order': 16
        }
        
        # Create performance history with low efficiency
        performance_history = []
        for _ in range(10):
            metrics = DTESNPerformanceMetrics(
                membrane_efficiency=0.3,  # Low efficiency
                reservoir_stability=0.4,  # Low stability
                b_series_convergence=0.6, # Low convergence
                memory_usage={'total': 0.5},
                computation_time={'total': 0.001}
            )
            performance_history.append(metrics)
        
        optimized_config = await bridge.optimize_dtesn_parameters(
            current_config, performance_history
        )
        
        # Should have increased parameters to improve performance
        assert optimized_config['membrane_hierarchy_depth'] >= current_config['membrane_hierarchy_depth']
        assert optimized_config['reservoir_size_factor'] >= current_config['reservoir_size_factor']
        assert optimized_config['b_series_order'] >= current_config['b_series_order']
    
    async def test_record_dtesn_performance(self):
        """Test recording DTESN performance."""
        meta_optimizer = MetaLearningOptimizer(MetaLearningConfig())
        bridge = DTESNMetaLearningBridge(meta_optimizer)
        
        config = {'membrane_hierarchy_depth': 8, 'reservoir_size_factor': 1.0}
        metrics = DTESNPerformanceMetrics(
            membrane_efficiency=0.8,
            reservoir_stability=0.7,
            b_series_convergence=0.9,
            memory_usage={'reservoir': 0.5},
            computation_time={'forward': 0.001}
        )
        
        await bridge.record_dtesn_performance(config, metrics, generation=5)
        
        # Should have recorded in meta-optimizer
        assert len(meta_optimizer.experience_replay.experiences) == 1
        experience = meta_optimizer.experience_replay.experiences[0]
        assert experience.generation == 5
        assert experience.fitness_score > 0


class TestEvolutionEngineIntegration:
    """Test cases for evolution engine integration with meta-learning."""
    
    async def test_evolution_engine_with_meta_learning(self):
        """Test evolution engine with meta-learning enabled."""
        config = EvolutionConfig(population_size=10, max_generations=3)
        engine = EchoSelfEvolutionEngine(config, enable_meta_learning=True)
        
        assert engine.meta_optimizer is not None
        assert engine.dtesn_bridge is not None
        assert engine.enable_meta_learning is True
    
    async def test_evolution_engine_without_meta_learning(self):
        """Test evolution engine with meta-learning disabled."""
        config = EvolutionConfig(population_size=10)
        engine = EchoSelfEvolutionEngine(config, enable_meta_learning=False)
        
        assert engine.meta_optimizer is None
        assert engine.dtesn_bridge is None
        assert engine.enable_meta_learning is False
    
    async def test_meta_learning_integration_in_evolution(self):
        """Test meta-learning integration during evolution."""
        config = EvolutionConfig(population_size=5, max_generations=2)
        engine = EchoSelfEvolutionEngine(config, enable_meta_learning=True)
        
        # Initialize population with mock individuals
        def individual_factory():
            genome = {
                'layer_count': np.random.randint(2, 6),
                'hidden_size': np.random.randint(32, 128),
                'learning_rate': np.random.uniform(0.001, 0.01)
            }
            return MockIndividual(genome)
        
        await engine.initialize_population(individual_factory)
        
        # Run evolution steps
        for _ in range(2):
            stats = await engine.evolve_step()
            assert 'generation' in stats
            assert 'best_fitness' in stats
        
        # Check meta-learning data was recorded
        assert len(engine.meta_optimizer.experience_replay.experiences) > 0
        
        # Check statistics include meta-learning info
        full_stats = engine.get_statistics()
        assert 'meta_learning' in full_stats
        assert 'dtesn_integration' in full_stats
    
    async def test_dtesn_integration_setup(self):
        """Test DTESN integration setup."""
        config = EvolutionConfig(population_size=5)
        engine = EchoSelfEvolutionEngine(config, enable_meta_learning=True)
        
        # Mock DTESN kernel
        mock_dtesn = Mock()
        
        # Set DTESN integration
        engine.set_dtesn_integration(mock_dtesn)
        
        # Check integrations were set up
        assert engine.dtesn_kernel == mock_dtesn
        assert engine.meta_optimizer.dtesn_kernel == mock_dtesn
        assert engine.dtesn_bridge.dtesn_kernel == mock_dtesn
    
    async def test_aar_integration_setup(self):
        """Test AAR orchestrator integration setup."""
        config = EvolutionConfig(population_size=5)
        engine = EchoSelfEvolutionEngine(config, enable_meta_learning=True)
        
        # Mock AAR orchestrator
        mock_aar = Mock()
        
        # Set AAR integration
        engine.set_aar_integration(mock_aar)
        
        # Check integrations were set up
        assert engine.aar_orchestrator == mock_aar
        assert engine.meta_optimizer.evolution_engine == engine


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import sys
    
    async def run_manual_tests():
        """Run tests manually without pytest."""
        print("Running Meta-Learning System Tests...")
        
        # Test MetaLearningOptimizer
        print("\n--- Testing MetaLearningOptimizer ---")
        test_instance = TestMetaLearningOptimizer()
        await test_instance.test_initialization()
        print("✓ Initialization test passed")
        
        await test_instance.test_record_architecture_performance()
        print("✓ Record architecture performance test passed")
        
        await test_instance.test_optimize_evolution_parameters()
        print("✓ Optimize evolution parameters test passed")
        
        await test_instance.test_get_architecture_recommendations()
        print("✓ Architecture recommendations test passed")
        
        # Test ExperienceReplay
        print("\n--- Testing ExperienceReplay ---")
        test_instance = TestExperienceReplay()
        test_instance.test_initialization()
        print("✓ Experience replay initialization test passed")
        
        test_instance.test_add_experience()
        print("✓ Add experience test passed")
        
        test_instance.test_sample_batch()
        print("✓ Sample batch test passed")
        
        test_instance.test_get_top_performers()
        print("✓ Get top performers test passed")
        
        # Test DTESNMetaLearningBridge  
        print("\n--- Testing DTESNMetaLearningBridge ---")
        test_instance = TestDTESNMetaLearningBridge()
        await test_instance.test_initialization()
        print("✓ DTESN bridge initialization test passed")
        
        await test_instance.test_extract_dtesn_metrics()
        print("✓ Extract DTESN metrics test passed")
        
        await test_instance.test_optimize_dtesn_parameters()
        print("✓ Optimize DTESN parameters test passed")
        
        await test_instance.test_record_dtesn_performance()
        print("✓ Record DTESN performance test passed")
        
        # Test Evolution Engine Integration
        print("\n--- Testing Evolution Engine Integration ---")
        test_instance = TestEvolutionEngineIntegration()
        await test_instance.test_evolution_engine_with_meta_learning()
        print("✓ Evolution engine with meta-learning test passed")
        
        await test_instance.test_evolution_engine_without_meta_learning()
        print("✓ Evolution engine without meta-learning test passed")
        
        await test_instance.test_meta_learning_integration_in_evolution()
        print("✓ Meta-learning integration in evolution test passed")
        
        await test_instance.test_dtesn_integration_setup()
        print("✓ DTESN integration setup test passed")
        
        await test_instance.test_aar_integration_setup()
        print("✓ AAR integration setup test passed")
        
        print("\n✅ All tests passed! Meta-learning system is working correctly.")
    
    # Check if we can import pytest
    try:
        import pytest
        print("pytest available - run with: python -m pytest test_meta_learning.py -v")
    except ImportError:
        print("pytest not available - running manual tests...")
        if sys.version_info >= (3, 7):
            asyncio.run(run_manual_tests())
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_manual_tests())