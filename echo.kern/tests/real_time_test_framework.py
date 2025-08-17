#!/usr/bin/env python3
"""
Real-Time Testing Framework for Echo.Kern DTESN System
======================================================

This module provides the core real-time testing framework for validating
DTESN performance requirements and interactive functionality.

Key Features:
- Microsecond-precision performance benchmarking
- Real-time monitoring capabilities
- Interactive web application testing
- DTESN component validation
- Continuous integration support

Performance Requirements (from DEVO-GENESIS.md):
- Membrane Evolution: ≤ 10μs
- B-Series Computation: ≤ 100μs
- ESN State Update: ≤ 1ms
- Context Switch: ≤ 5μs
- Memory Access: ≤ 100ns
"""

import time
import sys
import os
import threading
import json
import statistics
from typing import Dict, List, Callable, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import subprocess
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class PerformanceResult:
    """Performance test result data structure"""
    test_name: str
    execution_time_ns: int
    execution_time_us: float
    execution_time_ms: float
    threshold_us: float
    passed: bool
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    tests: List[Callable]
    performance_thresholds: Dict[str, float]  # in microseconds
    continuous_monitoring: bool = False
    monitor_interval_ms: int = 100

class RealTimeTestFramework:
    """
    Core real-time testing framework for Echo.Kern DTESN system
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.results: List[PerformanceResult] = []
        self.monitoring_active = False
        self.monitor_thread = None
        
        # DTESN Performance Thresholds (from roadmap)
        self.performance_thresholds = {
            'membrane_evolution': 10.0,     # 10μs
            'b_series_computation': 100.0,  # 100μs
            'esn_state_update': 1000.0,     # 1ms = 1000μs
            'context_switch': 5.0,          # 5μs
            'memory_access': 0.1,           # 100ns = 0.1μs
            'oeis_validation': 1000.0,      # 1ms for OEIS validation
            'web_response': 100000.0,       # 100ms for web responses
            'javascript_execution': 50000.0, # 50ms for JS execution
        }
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'performance_thresholds' in config:
                    self.performance_thresholds.update(config['performance_thresholds'])
        except Exception as e:
            print(f"Warning: Could not load config {config_file}: {e}")
    
    def measure_performance(self, func: Callable, test_name: str, 
                          threshold_key: str, *args, **kwargs) -> PerformanceResult:
        """
        Measure performance of a function with nanosecond precision
        
        Args:
            func: Function to measure
            test_name: Human-readable test name
            threshold_key: Key for performance threshold lookup
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            PerformanceResult object with timing and validation data
        """
        threshold_us = self.performance_thresholds.get(threshold_key, float('inf'))
        
        # Warm up the function (run once to avoid cold start effects)
        try:
            func(*args, **kwargs)
        except:
            pass  # Ignore warm-up errors
        
        # Measure with high precision
        start_time = time.perf_counter_ns()
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        end_time = time.perf_counter_ns()
        
        execution_time_ns = end_time - start_time
        execution_time_us = execution_time_ns / 1000.0
        execution_time_ms = execution_time_us / 1000.0
        
        passed = success and execution_time_us <= threshold_us
        
        metadata = {
            'success': success,
            'result': str(result)[:100] if result is not None else None,
            'error': error,
            'args_count': len(args),
            'kwargs_count': len(kwargs)
        }
        
        perf_result = PerformanceResult(
            test_name=test_name,
            execution_time_ns=execution_time_ns,
            execution_time_us=execution_time_us,
            execution_time_ms=execution_time_ms,
            threshold_us=threshold_us,
            passed=passed,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata
        )
        
        self.results.append(perf_result)
        return perf_result
    
    def benchmark_multiple_runs(self, func: Callable, test_name: str,
                              threshold_key: str, runs: int = 10,
                              *args, **kwargs) -> Dict[str, Any]:
        """
        Run multiple benchmarks and return statistical analysis
        """
        times_us = []
        passed_count = 0
        
        for i in range(runs):
            result = self.measure_performance(func, f"{test_name}_run_{i+1}", 
                                            threshold_key, *args, **kwargs)
            times_us.append(result.execution_time_us)
            if result.passed:
                passed_count += 1
        
        stats = {
            'test_name': test_name,
            'runs': runs,
            'passed_count': passed_count,
            'pass_rate': passed_count / runs * 100,
            'min_time_us': min(times_us),
            'max_time_us': max(times_us),
            'mean_time_us': statistics.mean(times_us),
            'median_time_us': statistics.median(times_us),
            'stdev_time_us': statistics.stdev(times_us) if len(times_us) > 1 else 0,
            'threshold_us': self.performance_thresholds.get(threshold_key, float('inf')),
            'times': times_us
        }
        
        return stats
    
    def start_continuous_monitoring(self, interval_ms: int = 100):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            print("Monitoring already active")
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval_ms,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"Started continuous monitoring (interval: {interval_ms}ms)")
    
    def stop_continuous_monitoring(self):
        """Stop continuous performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        print("Stopped continuous monitoring")
    
    def _monitor_loop(self, interval_ms: int):
        """Internal monitoring loop"""
        interval_s = interval_ms / 1000.0
        
        while self.monitoring_active:
            # Monitor web server response
            try:
                start = time.perf_counter_ns()
                response = requests.get('http://localhost:8000', timeout=1.0)
                end = time.perf_counter_ns()
                
                response_time_us = (end - start) / 1000.0
                
                if response.status_code == 200 and response_time_us <= 100000:  # 100ms
                    status = "✅"
                else:
                    status = "⚠️"
                    
                print(f"{status} Web server: {response_time_us:.1f}μs (threshold: 100ms)")
                
            except Exception as e:
                print(f"❌ Web server: {e}")
            
            time.sleep(interval_s)
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive test report"""
        if not self.results:
            return "No test results available"
        
        # Calculate summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        pass_rate = (passed_tests / total_tests) * 100
        
        # Group by test category
        categories = {}
        for result in self.results:
            category = result.test_name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Generate report
        report_lines = [
            "Echo.Kern Real-Time Testing Framework Report",
            "=" * 50,
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {total_tests - passed_tests}",
            f"Pass Rate: {pass_rate:.1f}%",
            "",
            "Performance Summary by Category:",
            "-" * 30
        ]
        
        for category, results in categories.items():
            avg_time = statistics.mean([r.execution_time_us for r in results])
            category_pass_rate = (sum(1 for r in results if r.passed) / len(results)) * 100
            
            report_lines.extend([
                f"{category.title()}:",
                f"  Tests: {len(results)}",
                f"  Average time: {avg_time:.2f}μs",
                f"  Pass rate: {category_pass_rate:.1f}%",
                ""
            ])
        
        # Detailed results
        report_lines.extend([
            "Detailed Results:",
            "-" * 20
        ])
        
        for result in self.results:
            status = "✅" if result.passed else "❌"
            report_lines.append(
                f"{status} {result.test_name}: {result.execution_time_us:.2f}μs "
                f"(threshold: {result.threshold_us:.2f}μs)"
            )
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to {output_file}")
        
        return report
    
    def export_results_json(self, filename: str):
        """Export results as JSON for further analysis"""
        data = {
            'framework_version': '1.0.0',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'performance_thresholds': self.performance_thresholds,
            'results': [asdict(result) for result in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Results exported to {filename}")
    
    def clear_results(self):
        """Clear all test results"""
        self.results.clear()
        print("Test results cleared")

def create_test_framework(config_file: Optional[str] = None) -> RealTimeTestFramework:
    """Factory function to create test framework instance"""
    return RealTimeTestFramework(config_file)

# Convenience functions for quick testing
def quick_performance_test(func: Callable, test_name: str, 
                         threshold_us: float, runs: int = 1) -> bool:
    """Quick performance test without framework setup"""
    framework = RealTimeTestFramework()
    framework.performance_thresholds['quick_test'] = threshold_us
    
    if runs == 1:
        result = framework.measure_performance(func, test_name, 'quick_test')
        print(f"{'✅' if result.passed else '❌'} {test_name}: {result.execution_time_us:.2f}μs")
        return result.passed
    else:
        stats = framework.benchmark_multiple_runs(func, test_name, 'quick_test', runs)
        print(f"{'✅' if stats['pass_rate'] > 80 else '❌'} {test_name}: "
              f"{stats['mean_time_us']:.2f}μs avg, {stats['pass_rate']:.1f}% pass rate")
        return stats['pass_rate'] > 80

if __name__ == "__main__":
    # Quick demonstration
    print("Echo.Kern Real-Time Testing Framework")
    print("=" * 40)
    
    framework = create_test_framework()
    
    # Test basic operations
    def test_function():
        return sum(range(1000))
    
    result = framework.measure_performance(test_function, "basic_computation", "memory_access")
    print(f"Test result: {result.execution_time_us:.2f}μs")
    
    # Generate quick report
    print("\n" + framework.generate_report())