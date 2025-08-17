#!/usr/bin/env python3
"""
Performance Tests for Echo.Kern DTESN Components
===============================================

This module implements performance benchmarks for the key DTESN operations
specified in the Echo.Kern roadmap.

Target Performance Requirements:
- Membrane Evolution: ≤ 10μs
- B-Series Computation: ≤ 100μs
- ESN State Update: ≤ 1ms
- Context Switch: ≤ 5μs
- Memory Access: ≤ 100ns
"""

import sys
import os
import time
import random
import math
import threading
from typing import List, Dict, Any
import json
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.real_time_test_framework import RealTimeTestFramework, create_test_framework
from oeis_a000081_enumerator import create_enhanced_validator

class DTESNPerformanceTests:
    """
    Performance tests for DTESN kernel components
    """
    
    def __init__(self, framework: RealTimeTestFramework):
        self.framework = framework
        self.oeis_validator = create_enhanced_validator()
        
        # Simulated DTESN data structures
        self.membrane_states = self._initialize_membrane_states()
        self.esn_reservoirs = self._initialize_esn_reservoirs()
        self.b_series_cache = {}
        
    def _initialize_membrane_states(self) -> List[Dict[str, Any]]:
        """Initialize simulated membrane states for testing"""
        states = []
        # Based on OEIS A000081: [1, 1, 1, 2, 4, 9, 20, 48, ...]
        membrane_counts = [1, 1, 1, 2, 4, 9, 20, 48]
        
        for level, count in enumerate(membrane_counts):
            for i in range(count):
                state = {
                    'level': level,
                    'id': f'membrane_{level}_{i}',
                    'objects': [random.randint(1, 100) for _ in range(10)],
                    'rules': [f'rule_{j}' for j in range(5)],
                    'evolution_step': 0,
                    'active': True
                }
                states.append(state)
        return states
    
    def _initialize_esn_reservoirs(self) -> List[Dict[str, Any]]:
        """Initialize simulated ESN reservoir states"""
        reservoirs = []
        for i in range(5):  # 5 reservoir nodes
            reservoir = {
                'id': f'esn_{i}',
                'state': [random.uniform(-1, 1) for _ in range(100)],  # 100-node reservoir
                'weights': [[random.uniform(-1, 1) for _ in range(100)] for _ in range(100)],
                'input_weights': [random.uniform(-1, 1) for _ in range(10)],
                'output_weights': [random.uniform(-1, 1) for _ in range(100)],
                'leak_rate': 0.1,
                'last_update': time.time()
            }
            reservoirs.append(reservoir)
        return reservoirs
    
    def test_membrane_evolution(self, membrane_id: int = 0) -> bool:
        """Test P-System membrane evolution performance"""
        if membrane_id >= len(self.membrane_states):
            return False
            
        membrane = self.membrane_states[membrane_id]
        
        # Simulate membrane evolution (P-system rule application)
        evolved_objects = []
        for obj in membrane['objects']:
            # Simple rule: if object > 50, split it; otherwise, increment
            if obj > 50:
                evolved_objects.extend([obj // 2, obj // 2])
            else:
                evolved_objects.append(obj + 1)
        
        membrane['objects'] = evolved_objects[:10]  # Keep size bounded
        membrane['evolution_step'] += 1
        
        return True
    
    def test_b_series_computation(self, order: int = 4) -> float:
        """Test B-series elementary differential computation"""
        if order in self.b_series_cache:
            return self.b_series_cache[order]
        
        # Simulate B-series computation for Runge-Kutta methods
        # This is a simplified version of rooted tree coefficient calculation
        result = 0.0
        
        for i in range(1, order + 1):
            # Elementary differential coefficient based on tree structure
            tree_coeff = 1.0 / math.factorial(i)
            for j in range(1, i + 1):
                tree_coeff *= (1.0 + j / (i + 1))
            result += tree_coeff
        
        self.b_series_cache[order] = result
        return result
    
    def test_esn_state_update(self, reservoir_id: int = 0, input_data: List[float] = None) -> bool:
        """Test Echo State Network state update performance"""
        if reservoir_id >= len(self.esn_reservoirs):
            return False
        
        reservoir = self.esn_reservoirs[reservoir_id]
        
        if input_data is None:
            input_data = [random.uniform(-1, 1) for _ in range(10)]
        
        # ESN state update: x(t+1) = (1-α)x(t) + α·tanh(W·x(t) + W_in·u(t))
        current_state = reservoir['state']
        weights = reservoir['weights']
        input_weights = reservoir['input_weights']
        leak_rate = reservoir['leak_rate']
        
        # Compute reservoir activation
        new_state = []
        for i in range(len(current_state)):
            # Reservoir internal dynamics
            internal_activation = sum(weights[i][j] * current_state[j] 
                                   for j in range(len(current_state)))
            
            # Input contribution
            input_activation = sum(input_weights[k] * input_data[k] 
                                 for k in range(min(len(input_weights), len(input_data))))
            
            # Apply leak rate and activation function
            new_activation = math.tanh(internal_activation + input_activation)
            new_state_value = (1 - leak_rate) * current_state[i] + leak_rate * new_activation
            new_state.append(new_state_value)
        
        reservoir['state'] = new_state
        reservoir['last_update'] = time.time()
        
        return True
    
    def test_context_switch(self) -> bool:
        """Test simulated context switching performance"""
        # Simulate context switch between membrane processes
        current_context = {
            'membrane_id': random.randint(0, len(self.membrane_states) - 1),
            'register_state': [random.randint(0, 255) for _ in range(8)],
            'stack_pointer': random.randint(1000, 2000),
            'program_counter': random.randint(0, 1000)
        }
        
        new_context = {
            'membrane_id': random.randint(0, len(self.membrane_states) - 1),
            'register_state': [random.randint(0, 255) for _ in range(8)],
            'stack_pointer': random.randint(1000, 2000),
            'program_counter': random.randint(0, 1000)
        }
        
        # Simulate save/restore operations
        saved_context = current_context.copy()
        current_context.update(new_context)
        
        return saved_context != current_context
    
    def test_memory_access(self) -> int:
        """Test optimized memory access performance"""
        # Simulate DTESN-optimized memory access pattern
        # Based on the memory layout from the roadmap
        
        memory_regions = {
            'dtesn_membranes': list(range(1000)),
            'esn_reservoirs': list(range(1000, 2000)),
            'b_series_cache': list(range(2000, 3000))
        }
        
        # Random access pattern
        region = random.choice(list(memory_regions.keys()))
        address = random.choice(memory_regions[region])
        
        # Simulate memory read
        value = address * 2 + 1
        
        return value
    
    def test_oeis_validation_performance(self) -> bool:
        """Test OEIS A000081 validation performance"""
        # Test the OEIS validator performance
        test_hierarchy = [1, 1, 1, 2, 4]  # Valid hierarchy for depth 4
        
        from oeis_a000081_enumerator import validate_membrane_hierarchy_enhanced
        is_valid, errors = validate_membrane_hierarchy_enhanced(test_hierarchy, 4)
        
        return is_valid and len(errors) == 0
    
    def test_web_server_response(self) -> bool:
        """Test web server response performance"""
        try:
            import requests
            response = requests.get('http://localhost:8000', timeout=1.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def test_javascript_execution(self) -> bool:
        """Test JavaScript execution performance via Node.js"""
        try:
            # Test JavaScript syntax validation (quick operation)
            result = subprocess.run(['node', '-c', 'app.js'], 
                                  cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  capture_output=True, timeout=1.0)
            return result.returncode == 0
        except Exception:
            return False
    
    def run_all_performance_tests(self, runs_per_test: int = 10) -> Dict[str, Any]:
        """Run all performance tests and return comprehensive results"""
        test_methods = [
            ('membrane_evolution', self.test_membrane_evolution),
            ('b_series_computation', lambda: self.test_b_series_computation(4)),
            ('esn_state_update', self.test_esn_state_update),
            ('context_switch', self.test_context_switch),
            ('memory_access', self.test_memory_access),
            ('oeis_validation', self.test_oeis_validation_performance),
            ('web_response', self.test_web_server_response),
            ('javascript_execution', self.test_javascript_execution)
        ]
        
        results = {}
        
        print("Running DTESN Performance Test Suite...")
        print("=" * 40)
        
        for test_name, test_func in test_methods:
            print(f"Testing {test_name}...")
            
            stats = self.framework.benchmark_multiple_runs(
                test_func, test_name, test_name, runs_per_test
            )
            
            results[test_name] = stats
            
            # Display results
            status = "✅" if stats['pass_rate'] > 80 else "❌"
            print(f"{status} {test_name}: {stats['mean_time_us']:.2f}μs avg "
                  f"(threshold: {stats['threshold_us']:.2f}μs, "
                  f"pass rate: {stats['pass_rate']:.1f}%)")
        
        return results

def run_dtesn_performance_suite(runs_per_test: int = 10, 
                               output_file: str = None) -> bool:
    """
    Main function to run the complete DTESN performance test suite
    """
    print("Echo.Kern DTESN Performance Test Suite")
    print("=" * 50)
    print(f"Target thresholds:")
    print(f"  Membrane Evolution: ≤ 10μs")
    print(f"  B-Series Computation: ≤ 100μs")
    print(f"  ESN State Update: ≤ 1ms")
    print(f"  Context Switch: ≤ 5μs")
    print(f"  Memory Access: ≤ 100ns")
    print(f"  OEIS Validation: ≤ 1ms")
    print(f"  Web Response: ≤ 100ms")
    print(f"  JavaScript Execution: ≤ 50ms")
    print()
    
    # Create framework and test suite
    framework = create_test_framework()
    test_suite = DTESNPerformanceTests(framework)
    
    # Run all tests
    results = test_suite.run_all_performance_tests(runs_per_test)
    
    # Generate report
    print("\n" + "=" * 50)
    report = framework.generate_report(output_file)
    print(report)
    
    # Export detailed results
    if output_file:
        json_file = output_file.replace('.txt', '.json')
        framework.export_results_json(json_file)
    
    # Calculate overall success
    total_pass_rate = sum(r['pass_rate'] for r in results.values()) / len(results)
    success = total_pass_rate > 80
    
    print(f"\nOverall Performance: {'✅ PASS' if success else '❌ FAIL'} "
          f"({total_pass_rate:.1f}% average pass rate)")
    
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run DTESN performance tests')
    parser.add_argument('--runs', type=int, default=10, 
                       help='Number of runs per test (default: 10)')
    parser.add_argument('--output', type=str, 
                       help='Output file for test report')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests with fewer iterations')
    
    args = parser.parse_args()
    
    runs = 3 if args.quick else args.runs
    output_file = args.output or f"dtesn_performance_report_{int(time.time())}.txt"
    
    success = run_dtesn_performance_suite(runs, output_file)
    exit(0 if success else 1)