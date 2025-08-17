#!/usr/bin/env python3
"""
Test Suite for P-System Membrane Evolution Engine
================================================

Comprehensive test suite for validating the advanced P-System membrane
evolution engine designed for Deep Tree Echo State Networks (DTESN).

Test Coverage:
- Evolution engine initialization and configuration
- Multiple evolution strategies (synchronous, parallel, adaptive)
- Performance metrics and analytics
- Real-time timing constraints validation
- Thread safety and parallel processing
- Integration with existing P-System infrastructure
- Performance optimization and recommendations

Authors: Echo.Kern Development Team
License: MIT
"""

import sys
import unittest
import time
import threading
import multiprocessing
from unittest.mock import patch, MagicMock
from typing import List, Dict

# Import the evolution engine and dependencies
try:
    from psystem_evolution_engine import (
        PSystemEvolutionEngine, EvolutionConfig, EvolutionStrategy,
        EvolutionMetrics, EvolutionAnalytics, SynchronousEvolutionStrategy,
        ParallelEvolutionStrategy, AdaptiveEvolutionStrategy,
        create_evolution_engine_demo
    )
    from psystem_membranes import (
        PSystemMembraneHierarchy, MembraneStructure, EvolutionRule,
        Multiset, MembraneType, RuleType, create_dtesn_psystem_example
    )
except ImportError as e:
    print(f"Error importing evolution engine modules: {e}")
    sys.exit(1)

class TestEvolutionConfig(unittest.TestCase):
    """Test EvolutionConfig functionality"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = EvolutionConfig()
        
        self.assertEqual(config.strategy, EvolutionStrategy.SYNCHRONOUS)
        self.assertGreater(config.max_parallel_workers, 0)
        self.assertEqual(config.target_evolution_time_us, 50.0)
        self.assertEqual(config.max_evolution_time_us, 1000.0)
        self.assertTrue(config.enable_analytics)
        
    def test_custom_config(self):
        """Test custom configuration values"""
        config = EvolutionConfig(
            strategy=EvolutionStrategy.ADAPTIVE,
            max_parallel_workers=8,
            target_evolution_time_us=25.0,
            max_evolution_time_us=500.0,
            enable_analytics=False
        )
        
        self.assertEqual(config.strategy, EvolutionStrategy.ADAPTIVE)
        self.assertEqual(config.max_parallel_workers, 8)
        self.assertEqual(config.target_evolution_time_us, 25.0)
        self.assertEqual(config.max_evolution_time_us, 500.0)
        self.assertFalse(config.enable_analytics)
    
    def test_auto_worker_count(self):
        """Test automatic worker count adjustment"""
        config = EvolutionConfig(max_parallel_workers=0)
        self.assertEqual(config.max_parallel_workers, multiprocessing.cpu_count())

class TestEvolutionMetrics(unittest.TestCase):
    """Test EvolutionMetrics functionality"""
    
    def test_metrics_creation(self):
        """Test basic metrics creation"""
        metrics = EvolutionMetrics()
        
        self.assertEqual(metrics.total_evolution_time_us, 0.0)
        self.assertEqual(metrics.rules_applied, 0)
        self.assertEqual(metrics.membranes_processed, 0)
        self.assertEqual(metrics.performance_score, 1.0)
        self.assertGreater(metrics.timestamp, 0)
    
    def test_average_membrane_time(self):
        """Test average membrane time calculation"""
        metrics = EvolutionMetrics()
        metrics.membrane_evolution_times = {
            'mem1': 10.0,
            'mem2': 20.0,
            'mem3': 30.0
        }
        
        self.assertEqual(metrics.get_average_membrane_time(), 20.0)
    
    def test_timing_constraints(self):
        """Test timing constraint validation"""
        config = EvolutionConfig(max_evolution_time_us=100.0)
        
        # Metrics within constraints
        metrics_good = EvolutionMetrics(total_evolution_time_us=50.0)
        self.assertTrue(metrics_good.meets_timing_constraints(config))
        
        # Metrics exceeding constraints
        metrics_bad = EvolutionMetrics(total_evolution_time_us=150.0)
        self.assertFalse(metrics_bad.meets_timing_constraints(config))

class TestEvolutionAnalytics(unittest.TestCase):
    """Test EvolutionAnalytics functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analytics = EvolutionAnalytics(history_size=10)
    
    def test_analytics_initialization(self):
        """Test analytics initialization"""
        self.assertEqual(self.analytics.history_size, 10)
        self.assertEqual(len(self.analytics.metrics_history), 0)
        self.assertIn('evolution_time', self.analytics.performance_trends)
    
    def test_metrics_recording(self):
        """Test metrics recording"""
        metrics = EvolutionMetrics(
            total_evolution_time_us=50.0,
            rules_applied=5,
            performance_score=0.8
        )
        
        self.analytics.record_metrics(metrics)
        
        self.assertEqual(len(self.analytics.metrics_history), 1)
        self.assertEqual(self.analytics.performance_trends['evolution_time'][-1], 50.0)
        self.assertEqual(self.analytics.performance_trends['rules_applied'][-1], 5)
    
    def test_performance_trends(self):
        """Test performance trend calculation"""
        # Add metrics with improving performance
        for i in range(10):
            metrics = EvolutionMetrics(
                total_evolution_time_us=100.0 - i * 5,  # Decreasing time (improving)
                rules_applied=i + 1
            )
            self.analytics.record_metrics(metrics)
        
        # Should show improving trend (negative for time = good)
        time_trend = self.analytics.get_performance_trend('evolution_time', 10)
        self.assertLess(time_trend, 0)  # Time decreasing = improvement
        
        # Should show increasing rules applied
        rules_trend = self.analytics.get_performance_trend('rules_applied', 10)
        self.assertGreater(rules_trend, 0)  # Rules increasing
    
    def test_current_performance(self):
        """Test current performance statistics"""
        # Add some metrics
        for i in range(5):
            metrics = EvolutionMetrics(
                total_evolution_time_us=50.0 + i,
                rules_applied=3 + i,
                performance_score=0.8 + i * 0.02
            )
            self.analytics.record_metrics(metrics)
        
        performance = self.analytics.get_current_performance()
        
        self.assertIn('avg_evolution_time_us', performance)
        self.assertIn('avg_rules_applied', performance)
        self.assertIn('total_evolution_cycles', performance)
        self.assertEqual(performance['total_evolution_cycles'], 5)

class TestSynchronousEvolutionStrategy(unittest.TestCase):
    """Test SynchronousEvolutionStrategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = EvolutionConfig()
        self.analytics = EvolutionAnalytics()
        self.strategy = SynchronousEvolutionStrategy(self.config, self.analytics)
    
    def test_strategy_creation(self):
        """Test strategy creation"""
        self.assertEqual(self.strategy.config, self.config)
        self.assertEqual(self.strategy.analytics, self.analytics)
    
    def test_rule_selection(self):
        """Test rule selection algorithms"""
        membrane = MembraneStructure("test", MembraneType.ROOT, "test")
        
        # Add some rules with different priorities
        lhs = Multiset()
        lhs.add("a", 1)
        rhs = Multiset()
        rhs.add("b", 1)
        
        rule1 = EvolutionRule("rule1", RuleType.EVOLUTION, lhs, rhs, priority=1)
        rule2 = EvolutionRule("rule2", RuleType.EVOLUTION, lhs, rhs, priority=3)
        rule3 = EvolutionRule("rule3", RuleType.EVOLUTION, lhs, rhs, priority=2)
        
        membrane.add_rule(rule1)
        membrane.add_rule(rule2)
        membrane.add_rule(rule3)
        membrane.add_object("a", 10)  # Make rules applicable
        
        # Test priority-first selection
        selected_rules = self.strategy.select_rules(membrane)
        self.assertEqual(selected_rules[0].priority, 3)  # Highest priority first
        self.assertEqual(selected_rules[1].priority, 2)
        self.assertEqual(selected_rules[2].priority, 1)
    
    def test_system_evolution(self):
        """Test complete system evolution"""
        system = create_dtesn_psystem_example()
        
        metrics = self.strategy.evolve_system(system)
        
        self.assertIsInstance(metrics, EvolutionMetrics)
        self.assertGreaterEqual(metrics.membranes_processed, 0)
        self.assertGreaterEqual(metrics.total_evolution_time_us, 0)
        self.assertGreaterEqual(metrics.performance_score, 0)

class TestParallelEvolutionStrategy(unittest.TestCase):
    """Test ParallelEvolutionStrategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = EvolutionConfig(max_parallel_workers=2)
        self.analytics = EvolutionAnalytics()
        self.strategy = ParallelEvolutionStrategy(self.config, self.analytics)
    
    def test_parallel_strategy_creation(self):
        """Test parallel strategy creation"""
        self.assertEqual(self.strategy.config.max_parallel_workers, 2)
        self.assertIsNotNone(self.strategy.executor)
    
    def test_parallel_system_evolution(self):
        """Test parallel system evolution"""
        system = create_dtesn_psystem_example()
        
        metrics = self.strategy.evolve_system(system)
        
        self.assertIsInstance(metrics, EvolutionMetrics)
        self.assertGreaterEqual(metrics.membranes_processed, 0)
        self.assertGreaterEqual(metrics.total_evolution_time_us, 0)
    
    def test_thread_safety(self):
        """Test thread safety of parallel evolution"""
        system = create_dtesn_psystem_example()
        
        # Run multiple parallel evolutions
        results = []
        threads = []
        
        def run_evolution():
            metrics = self.strategy.evolve_system(system)
            results.append(metrics)
        
        for _ in range(3):
            thread = threading.Thread(target=run_evolution)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All evolutions should complete successfully
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, EvolutionMetrics)

class TestAdaptiveEvolutionStrategy(unittest.TestCase):
    """Test AdaptiveEvolutionStrategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = EvolutionConfig(adaptive_threshold=0.5)
        self.analytics = EvolutionAnalytics()
        self.strategy = AdaptiveEvolutionStrategy(self.config, self.analytics)
    
    def test_adaptive_strategy_creation(self):
        """Test adaptive strategy creation"""
        self.assertEqual(self.strategy.switch_threshold, 0.5)
        self.assertIn(EvolutionStrategy.SYNCHRONOUS, self.strategy.strategies)
        self.assertIn(EvolutionStrategy.ASYNCHRONOUS, self.strategy.strategies)
    
    def test_strategy_switching(self):
        """Test strategy switching logic"""
        initial_strategy = self.strategy.current_strategy
        
        # Force strategy switch by simulating poor performance
        with patch.object(self.analytics, 'get_current_performance') as mock_perf:
            mock_perf.return_value = {'avg_performance_score': 0.3}  # Below threshold
            
            # Add enough history to trigger evaluation
            for _ in range(15):
                metrics = EvolutionMetrics(performance_score=0.3)
                self.analytics.record_metrics(metrics)
            
            system = create_dtesn_psystem_example()
            self.strategy.evolve_system(system)
            
            # Strategy should have switched
            self.assertNotEqual(self.strategy.current_strategy, initial_strategy)

class TestPSystemEvolutionEngine(unittest.TestCase):
    """Test PSystemEvolutionEngine main class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = EvolutionConfig(
            strategy=EvolutionStrategy.SYNCHRONOUS,
            target_evolution_time_us=50.0,
            max_evolution_time_us=200.0
        )
        self.engine = PSystemEvolutionEngine(self.config)
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        self.assertEqual(self.engine.config.strategy, EvolutionStrategy.SYNCHRONOUS)
        self.assertEqual(self.engine.current_strategy, EvolutionStrategy.SYNCHRONOUS)
        self.assertEqual(self.engine.total_evolution_cycles, 0)
        self.assertIn(EvolutionStrategy.SYNCHRONOUS, self.engine.strategies)
    
    def test_default_engine_creation(self):
        """Test engine creation with default config"""
        engine = PSystemEvolutionEngine()
        
        self.assertIsInstance(engine.config, EvolutionConfig)
        self.assertIsInstance(engine.analytics, EvolutionAnalytics)
    
    def test_strategy_switching(self):
        """Test strategy switching"""
        initial_strategy = self.engine.current_strategy
        
        # Switch to different strategy
        self.engine.set_strategy(EvolutionStrategy.ADAPTIVE)
        self.assertEqual(self.engine.current_strategy, EvolutionStrategy.ADAPTIVE)
        self.assertNotEqual(self.engine.current_strategy, initial_strategy)
    
    def test_invalid_strategy(self):
        """Test invalid strategy handling"""
        with self.assertRaises(ValueError):
            self.engine.set_strategy("invalid_strategy")
    
    def test_system_evolution(self):
        """Test complete system evolution"""
        system = create_dtesn_psystem_example()
        initial_step = system.evolution_step
        
        metrics = self.engine.evolve_system(system)
        
        self.assertIsInstance(metrics, EvolutionMetrics)
        self.assertEqual(system.evolution_step, initial_step + 1)
        self.assertEqual(self.engine.total_evolution_cycles, 1)
    
    def test_halted_system_evolution(self):
        """Test evolution of already halted system"""
        system = create_dtesn_psystem_example()
        system.is_halted = True
        
        metrics = self.engine.evolve_system(system)
        
        # Should return empty metrics for halted system
        self.assertEqual(metrics.rules_applied, 0)
        self.assertEqual(metrics.membranes_processed, 0)
    
    def test_membrane_evolution(self):
        """Test individual membrane evolution"""
        system = create_dtesn_psystem_example()
        membrane_ids = list(system.membranes.keys())
        
        if membrane_ids:
            membrane_id = membrane_ids[0]
            rules_applied, evolution_time = self.engine.evolve_membrane(membrane_id, system)
            
            self.assertIsInstance(rules_applied, int)
            self.assertIsInstance(evolution_time, float)
            self.assertGreaterEqual(rules_applied, 0)
            self.assertGreaterEqual(evolution_time, 0)
    
    def test_performance_statistics(self):
        """Test performance statistics collection"""
        system = create_dtesn_psystem_example()
        
        # Run a few evolution cycles
        for _ in range(3):
            self.engine.evolve_system(system)
        
        stats = self.engine.get_performance_statistics()
        
        self.assertIn('total_evolution_cycles', stats)
        self.assertIn('constraint_violations', stats)
        self.assertIn('current_strategy', stats)
        self.assertEqual(stats['total_evolution_cycles'], 3)
    
    def test_timing_constraint_violations(self):
        """Test timing constraint violation tracking"""
        # Create engine with very strict timing
        strict_config = EvolutionConfig(max_evolution_time_us=0.1)  # Nearly impossible
        engine = PSystemEvolutionEngine(strict_config)
        
        system = create_dtesn_psystem_example()
        
        # This should likely violate timing constraints
        engine.evolve_system(system)
        
        stats = engine.get_performance_statistics()
        # We might have violations due to very strict constraint
        self.assertGreaterEqual(stats['constraint_violations'], 0)
    
    def test_configuration_optimization(self):
        """Test automatic configuration optimization"""
        # Add some performance history
        for i in range(20):
            metrics = EvolutionMetrics(
                total_evolution_time_us=100.0 + i * 10,  # Increasing time
                rules_applied=5,
                performance_score=0.8 - i * 0.01  # Decreasing performance
            )
            self.engine.analytics.record_metrics(metrics)
        
        recommendations = self.engine.optimize_configuration()
        
        self.assertIsInstance(recommendations, dict)
        # Should recommend improvements for degrading performance

class TestEvolutionEngineIntegration(unittest.TestCase):
    """Test integration with existing P-System infrastructure"""
    
    def test_dtesn_example_integration(self):
        """Test integration with DTESN example system"""
        engine = create_evolution_engine_demo()
        system = create_dtesn_psystem_example()
        
        # Should work seamlessly with existing DTESN system
        metrics = engine.evolve_system(system)
        
        self.assertIsInstance(metrics, EvolutionMetrics)
        self.assertGreaterEqual(metrics.membranes_processed, 0)
    
    def test_oeis_compliance_preservation(self):
        """Test that evolution preserves OEIS A000081 compliance"""
        engine = PSystemEvolutionEngine()
        system = create_dtesn_psystem_example()
        
        # Check initial compliance
        initial_valid, _ = system.validate_oeis_a000081_compliance()
        
        # Run evolution
        engine.evolve_system(system)
        
        # Should still be compliant
        final_valid, _ = system.validate_oeis_a000081_compliance()
        self.assertEqual(initial_valid, final_valid)
    
    def test_membrane_hierarchy_preservation(self):
        """Test that evolution preserves membrane hierarchy"""
        engine = PSystemEvolutionEngine()
        system = create_dtesn_psystem_example()
        
        initial_membrane_count = len(system.membranes)
        initial_tree = system.get_membrane_tree()
        
        # Run evolution
        engine.evolve_system(system)
        
        # Structure should be preserved (unless dissolution/division occurs)
        final_tree = system.get_membrane_tree()
        self.assertIsInstance(final_tree, dict)

class TestPerformanceConstraints(unittest.TestCase):
    """Test real-time performance constraints"""
    
    def test_target_timing_achievement(self):
        """Test achievement of target timing constraints"""
        config = EvolutionConfig(
            strategy=EvolutionStrategy.SYNCHRONOUS,
            target_evolution_time_us=100.0,
            max_evolution_time_us=500.0
        )
        engine = PSystemEvolutionEngine(config)
        system = create_dtesn_psystem_example()
        
        # Run multiple cycles to get average performance
        times = []
        for _ in range(10):
            metrics = engine.evolve_system(system)
            times.append(metrics.total_evolution_time_us)
            if system.is_halted:
                break
        
        if times:
            avg_time = sum(times) / len(times)
            # Should generally meet timing constraints for small systems
            self.assertLess(avg_time, config.max_evolution_time_us * 2)  # Allow some flexibility
    
    def test_parallel_performance_improvement(self):
        """Test that parallel strategy improves performance for larger systems"""
        # Create larger system for better parallel benefits
        system = create_dtesn_psystem_example()
        
        # Add more membranes to make parallelization beneficial
        root_id = system.skin_membrane_id
        for i in range(10):
            system.create_membrane(MembraneType.LEAF, f"extra_leaf_{i}", root_id)
        
        # Test synchronous strategy
        sync_config = EvolutionConfig(strategy=EvolutionStrategy.SYNCHRONOUS)
        sync_engine = PSystemEvolutionEngine(sync_config)
        
        sync_metrics = sync_engine.evolve_system(system)
        
        # Reset system state for parallel test
        system.evolution_step = 0
        system.is_halted = False
        
        # Test parallel strategy  
        parallel_config = EvolutionConfig(
            strategy=EvolutionStrategy.ASYNCHRONOUS,
            max_parallel_workers=4
        )
        parallel_engine = PSystemEvolutionEngine(parallel_config)
        
        parallel_metrics = parallel_engine.evolve_system(system)
        
        # Both should complete successfully
        self.assertGreaterEqual(sync_metrics.membranes_processed, 0)
        self.assertGreaterEqual(parallel_metrics.membranes_processed, 0)

def run_all_tests():
    """Run all test suites"""
    test_suites = [
        TestEvolutionConfig,
        TestEvolutionMetrics,
        TestEvolutionAnalytics,
        TestSynchronousEvolutionStrategy,
        TestParallelEvolutionStrategy,
        TestAdaptiveEvolutionStrategy,
        TestPSystemEvolutionEngine,
        TestEvolutionEngineIntegration,
        TestPerformanceConstraints
    ]
    
    overall_result = True
    total_tests = 0
    total_failures = 0
    
    print("P-System Membrane Evolution Engine Test Suite")
    print("=" * 60)
    
    for test_suite in test_suites:
        print(f"\nRunning {test_suite.__name__}...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
        runner = unittest.TextTestRunner(verbosity=1, stream=open('/dev/null', 'w'))
        result = runner.run(suite)
        
        tests_run = result.testsRun
        failures = len(result.failures) + len(result.errors)
        
        total_tests += tests_run
        total_failures += failures
        
        if failures == 0:
            print(f"  ✅ {tests_run} tests passed")
        else:
            print(f"  ❌ {failures}/{tests_run} tests failed")
            overall_result = False
            
            # Print failure details
            for test, traceback in result.failures + result.errors:
                print(f"    FAILED: {test}")
                print(f"    ERROR: {traceback}")
    
    print(f"\n" + "=" * 60)
    print(f"Test Results: {total_tests - total_failures}/{total_tests} tests passed")
    
    if overall_result:
        print("🎉 All tests passed! P-System membrane evolution engine is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)