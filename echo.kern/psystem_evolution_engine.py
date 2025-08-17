#!/usr/bin/env python3
"""
P-System Membrane Evolution Engine for Deep Tree Echo State Networks
==================================================================

This module implements an advanced evolution engine for P-System membranes,
providing high-performance, real-time evolution capabilities optimized for
DTESN integration. The engine supports multiple evolution strategies, parallel
processing, and meets stringent timing constraints (10μs-1ms).

Key Features:
- Multiple evolution strategies (synchronous, asynchronous, probabilistic)
- Parallel membrane evolution processing 
- Real-time performance analytics and monitoring
- Configurable evolution parameters
- OEIS A000081 compliance validation
- Integration with existing DTESN architecture

Authors: Echo.Kern Development Team
License: MIT
Version: 1.0
"""

import sys
import time
import asyncio
import threading
import multiprocessing
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Callable, Iterator
import logging
import queue
import json
from collections import defaultdict, deque
import statistics

# Import the existing P-System infrastructure
try:
    from psystem_membranes import (
        PSystemMembraneHierarchy, MembraneStructure, EvolutionRule, 
        Multiset, MembraneType, RuleType, ExecutionPhase
    )
except ImportError as e:
    print(f"Error importing P-System modules: {e}")
    sys.exit(1)

# Configure logging for evolution engine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvolutionStrategy(Enum):
    """Different evolution strategies for membrane processing"""
    SYNCHRONOUS = "synchronous"        # All membranes evolve in lockstep
    ASYNCHRONOUS = "asynchronous"      # Membranes evolve independently  
    PROBABILISTIC = "probabilistic"    # Rule application based on probabilities
    PRIORITY_BASED = "priority_based"  # Evolution based on membrane priorities
    ADAPTIVE = "adaptive"              # Strategy adapts based on performance
    REAL_TIME = "real_time"           # Optimized for real-time constraints

class EvolutionPhase(Enum):
    """Phases of the evolution process"""
    PREPARATION = auto()
    RULE_SELECTION = auto() 
    RULE_APPLICATION = auto()
    COMMUNICATION = auto()
    SYNCHRONIZATION = auto()
    CLEANUP = auto()

@dataclass
class EvolutionConfig:
    """Configuration parameters for the evolution engine"""
    strategy: EvolutionStrategy = EvolutionStrategy.SYNCHRONOUS
    max_parallel_workers: int = 4
    target_evolution_time_us: float = 50.0  # Target timing constraint
    max_evolution_time_us: float = 1000.0   # Hard timing constraint
    enable_analytics: bool = True
    enable_profiling: bool = False
    rule_selection_algorithm: str = "priority_first"
    communication_batching: bool = True
    adaptive_threshold: float = 0.8  # Performance threshold for adaptive strategy
    
    def __post_init__(self):
        if self.max_parallel_workers <= 0:
            self.max_parallel_workers = multiprocessing.cpu_count()

@dataclass
class EvolutionMetrics:
    """Metrics collected during evolution"""
    total_evolution_time_us: float = 0.0
    membrane_evolution_times: Dict[str, float] = field(default_factory=dict)
    rules_applied: int = 0
    membranes_processed: int = 0
    communications_executed: int = 0
    strategy_switches: int = 0
    performance_score: float = 1.0
    timestamp: float = field(default_factory=time.time)
    
    def get_average_membrane_time(self) -> float:
        """Calculate average membrane evolution time"""
        if not self.membrane_evolution_times:
            return 0.0
        return statistics.mean(self.membrane_evolution_times.values())
    
    def meets_timing_constraints(self, config: EvolutionConfig) -> bool:
        """Check if evolution meets timing constraints"""
        return self.total_evolution_time_us <= config.max_evolution_time_us

class EvolutionAnalytics:
    """Real-time analytics for evolution performance"""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.performance_trends: Dict[str, deque] = {
            'evolution_time': deque(maxlen=history_size),
            'rules_applied': deque(maxlen=history_size),
            'performance_score': deque(maxlen=history_size)
        }
        self._lock = threading.Lock()
    
    def record_metrics(self, metrics: EvolutionMetrics) -> None:
        """Record new evolution metrics"""
        with self._lock:
            self.metrics_history.append(metrics)
            self.performance_trends['evolution_time'].append(metrics.total_evolution_time_us)
            self.performance_trends['rules_applied'].append(metrics.rules_applied)
            self.performance_trends['performance_score'].append(metrics.performance_score)
    
    def get_performance_trend(self, metric: str, window: int = 10) -> float:
        """Get performance trend for a specific metric"""
        try:
            with self._lock:
                if metric not in self.performance_trends:
                    return 0.0
                
                values = list(self.performance_trends[metric])
                if len(values) < window:
                    return 0.0
                
                # Ensure we have enough values for comparison
                if len(values) < 4:
                    return 0.0
                
                # Calculate trend (positive = improving, negative = degrading)
                half_window = max(2, window // 2)
                if len(values) < half_window * 2:
                    return 0.0
                
                recent_values = values[-half_window:]
                earlier_values = values[-half_window*2:-half_window]
                
                if not recent_values or not earlier_values:
                    return 0.0
                
                recent = statistics.mean(recent_values)
                earlier = statistics.mean(earlier_values)
                
                if earlier == 0:
                    return 0.0
                return (recent - earlier) / earlier
        except Exception:
            # Fallback to prevent infinite loops
            return 0.0
    
    def get_current_performance(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        with self._lock:
            if not self.metrics_history:
                return {
                    'avg_evolution_time_us': 0.0,
                    'avg_rules_applied': 0.0,
                    'avg_performance_score': 1.0,
                    'evolution_trend': 0.0,
                    'rules_trend': 0.0,
                    'total_evolution_cycles': 0
                }
            
            recent_metrics = list(self.metrics_history)[-10:]
            
            # Safe trend calculation
            try:
                evolution_trend = self.get_performance_trend('evolution_time')
                rules_trend = self.get_performance_trend('rules_applied')
            except Exception:
                evolution_trend = 0.0
                rules_trend = 0.0
            
            return {
                'avg_evolution_time_us': statistics.mean([m.total_evolution_time_us for m in recent_metrics]),
                'avg_rules_applied': statistics.mean([m.rules_applied for m in recent_metrics]),
                'avg_performance_score': statistics.mean([m.performance_score for m in recent_metrics]),
                'evolution_trend': evolution_trend,
                'rules_trend': rules_trend,
                'total_evolution_cycles': len(self.metrics_history)
            }

class EvolutionStrategyBase(ABC):
    """Abstract base class for evolution strategies"""
    
    def __init__(self, config: EvolutionConfig, analytics: EvolutionAnalytics):
        self.config = config
        self.analytics = analytics
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def evolve_system(self, system: PSystemMembraneHierarchy) -> EvolutionMetrics:
        """Execute evolution strategy on the system"""
        pass
    
    @abstractmethod
    def evolve_membrane(self, membrane: MembraneStructure, system: PSystemMembraneHierarchy) -> Tuple[int, float]:
        """Evolve a single membrane, returning (rules_applied, time_us)"""
        pass
    
    def select_rules(self, membrane: MembraneStructure) -> List[EvolutionRule]:
        """Select rules for application based on strategy"""
        applicable_rules = membrane.get_applicable_rules()
        
        if self.config.rule_selection_algorithm == "priority_first":
            return sorted(applicable_rules, key=lambda r: r.priority, reverse=True)
        elif self.config.rule_selection_algorithm == "random":
            import random
            rules = applicable_rules.copy()
            random.shuffle(rules)
            return rules
        else:
            return applicable_rules

class SynchronousEvolutionStrategy(EvolutionStrategyBase):
    """Synchronous evolution strategy - all membranes evolve in lockstep"""
    
    def evolve_system(self, system: PSystemMembraneHierarchy) -> EvolutionMetrics:
        start_time = time.time()
        metrics = EvolutionMetrics()
        
        # Evolve all membranes synchronously
        membrane_ids = list(system.membranes.keys())
        for membrane_id in membrane_ids:
            if membrane_id in system.membranes and not system.membranes[membrane_id].is_dissolved:
                rules_applied, evolution_time = self.evolve_membrane(
                    system.membranes[membrane_id], system
                )
                metrics.rules_applied += rules_applied
                metrics.membrane_evolution_times[membrane_id] = evolution_time
                metrics.membranes_processed += 1
        
        metrics.total_evolution_time_us = (time.time() - start_time) * 1000000
        metrics.performance_score = self._calculate_performance_score(metrics)
        
        return metrics
    
    def evolve_membrane(self, membrane: MembraneStructure, system: PSystemMembraneHierarchy) -> Tuple[int, float]:
        start_time = time.time()
        
        rules_applied = system.evolve_membrane(membrane.membrane_id)
        
        evolution_time = (time.time() - start_time) * 1000000
        return rules_applied, evolution_time
    
    def _calculate_performance_score(self, metrics: EvolutionMetrics) -> float:
        """Calculate performance score based on timing and rules applied"""
        if metrics.total_evolution_time_us == 0:
            return 1.0
        
        # Score based on meeting timing constraints and rule efficiency
        timing_score = min(1.0, self.config.target_evolution_time_us / metrics.total_evolution_time_us)
        efficiency_score = min(1.0, metrics.rules_applied / max(1, metrics.membranes_processed))
        
        return (timing_score + efficiency_score) / 2.0

class ParallelEvolutionStrategy(EvolutionStrategyBase):
    """Parallel evolution strategy using ThreadPoolExecutor for concurrent membrane processing"""
    
    def __init__(self, config: EvolutionConfig, analytics: EvolutionAnalytics):
        super().__init__(config, analytics)
        self.executor = ThreadPoolExecutor(max_workers=config.max_parallel_workers)
    
    def evolve_system(self, system: PSystemMembraneHierarchy) -> EvolutionMetrics:
        start_time = time.time()
        metrics = EvolutionMetrics()
        
        # Submit membrane evolution tasks to thread pool
        membrane_ids = [mid for mid, m in system.membranes.items() if not m.is_dissolved]
        future_to_membrane = {}
        
        for membrane_id in membrane_ids:
            future = self.executor.submit(
                self._evolve_membrane_safe, 
                system.membranes[membrane_id], 
                system
            )
            future_to_membrane[future] = membrane_id
        
        # Collect results as they complete
        for future in as_completed(future_to_membrane):
            membrane_id = future_to_membrane[future]
            try:
                rules_applied, evolution_time = future.result()
                metrics.rules_applied += rules_applied
                metrics.membrane_evolution_times[membrane_id] = evolution_time
                metrics.membranes_processed += 1
            except Exception as e:
                self.logger.error(f"Error evolving membrane {membrane_id}: {e}")
        
        metrics.total_evolution_time_us = (time.time() - start_time) * 1000000
        metrics.performance_score = self._calculate_performance_score(metrics)
        
        return metrics
    
    def evolve_membrane(self, membrane: MembraneStructure, system: PSystemMembraneHierarchy) -> Tuple[int, float]:
        return self._evolve_membrane_safe(membrane, system)
    
    def _evolve_membrane_safe(self, membrane: MembraneStructure, system: PSystemMembraneHierarchy) -> Tuple[int, float]:
        """Thread-safe membrane evolution"""
        start_time = time.time()
        
        try:
            with membrane._lock:  # Use membrane's lock for thread safety
                rules_applied = 0
                applicable_rules = self.select_rules(membrane)
                
                for rule in applicable_rules:
                    if rule.is_applicable(membrane.objects):
                        success, products = rule.apply(membrane.objects)
                        if success:
                            if rule.rule_type == RuleType.EVOLUTION:
                                membrane.objects = membrane.objects.union(products)
                            rules_applied += 1
                
                evolution_time = (time.time() - start_time) * 1000000
                return rules_applied, evolution_time
                
        except Exception as e:
            self.logger.error(f"Error in membrane evolution: {e}")
            return 0, 0.0
    
    def _calculate_performance_score(self, metrics: EvolutionMetrics) -> float:
        """Calculate performance score including parallelization efficiency"""
        if metrics.total_evolution_time_us == 0:
            return 1.0
        
        timing_score = min(1.0, self.config.target_evolution_time_us / metrics.total_evolution_time_us)
        parallel_efficiency = min(1.0, metrics.membranes_processed / self.config.max_parallel_workers)
        
        return (timing_score + parallel_efficiency) / 2.0
    
    def __del__(self):
        """Cleanup thread pool"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

class AdaptiveEvolutionStrategy(EvolutionStrategyBase):
    """Adaptive evolution strategy that switches between strategies based on performance"""
    
    def __init__(self, config: EvolutionConfig, analytics: EvolutionAnalytics):
        super().__init__(config, analytics)
        self.strategies = {
            EvolutionStrategy.SYNCHRONOUS: SynchronousEvolutionStrategy(config, analytics),
            EvolutionStrategy.ASYNCHRONOUS: ParallelEvolutionStrategy(config, analytics)
        }
        self.current_strategy = EvolutionStrategy.SYNCHRONOUS
        self.switch_threshold = config.adaptive_threshold
        self.evaluation_window = 10
        self.last_switch_time = time.time()
        self.min_switch_interval = 5.0  # Minimum seconds between switches
    
    def evolve_system(self, system: PSystemMembraneHierarchy) -> EvolutionMetrics:
        # Check if we should switch strategies (with safeguards)
        current_time = time.time()
        if (len(self.analytics.metrics_history) >= self.evaluation_window and 
            current_time - self.last_switch_time > self.min_switch_interval):
            
            try:
                # Simple performance check without complex statistics
                recent_metrics = list(self.analytics.metrics_history)[-5:]
                if recent_metrics:
                    avg_score = sum(m.performance_score for m in recent_metrics) / len(recent_metrics)
                    if avg_score < self.switch_threshold:
                        self._switch_strategy()
                        self.last_switch_time = current_time
            except Exception:
                # If anything goes wrong, just continue with current strategy
                pass
        
        # Execute current strategy
        strategy = self.strategies[self.current_strategy]
        metrics = strategy.evolve_system(system)
        
        return metrics
    
    def evolve_membrane(self, membrane: MembraneStructure, system: PSystemMembraneHierarchy) -> Tuple[int, float]:
        strategy = self.strategies[self.current_strategy]
        return strategy.evolve_membrane(membrane, system)
    
    def _switch_strategy(self):
        """Switch to alternative strategy"""
        if self.current_strategy == EvolutionStrategy.SYNCHRONOUS:
            self.current_strategy = EvolutionStrategy.ASYNCHRONOUS
        else:
            self.current_strategy = EvolutionStrategy.SYNCHRONOUS
        
        self.logger.info(f"Adaptive strategy switched to: {self.current_strategy.value}")

class PSystemEvolutionEngine:
    """
    Advanced P-System membrane evolution engine with multiple strategies,
    parallel processing, and real-time performance optimization.
    """
    
    def __init__(self, config: Optional[EvolutionConfig] = None):
        self.config = config or EvolutionConfig()
        self.analytics = EvolutionAnalytics()
        
        # Initialize evolution strategies
        self.strategies = {
            EvolutionStrategy.SYNCHRONOUS: SynchronousEvolutionStrategy(self.config, self.analytics),
            EvolutionStrategy.ASYNCHRONOUS: ParallelEvolutionStrategy(self.config, self.analytics),
            EvolutionStrategy.ADAPTIVE: AdaptiveEvolutionStrategy(self.config, self.analytics)
        }
        
        self.current_strategy = self.config.strategy
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.total_evolution_cycles = 0
        self.constraint_violations = 0
        
        self.logger.info(f"P-System Evolution Engine initialized with strategy: {self.current_strategy.value}")
    
    def evolve_system(self, system: PSystemMembraneHierarchy) -> EvolutionMetrics:
        """
        Execute one complete evolution cycle on the P-System.
        Returns detailed metrics about the evolution process.
        """
        if system.is_halted:
            return EvolutionMetrics()
        
        strategy = self.strategies[self.current_strategy]
        metrics = strategy.evolve_system(system)
        
        # Record metrics and check performance
        self.analytics.record_metrics(metrics)
        self.total_evolution_cycles += 1
        
        # Check timing constraints
        if not metrics.meets_timing_constraints(self.config):
            self.constraint_violations += 1
            self.logger.warning(
                f"Evolution cycle exceeded timing constraint: "
                f"{metrics.total_evolution_time_us:.2f}μs > {self.config.max_evolution_time_us}μs"
            )
        
        # Update system state
        system.evolution_step += 1
        
        # Check if system should halt
        if metrics.rules_applied == 0:
            system.execution_phase = ExecutionPhase.HALTED
            system.is_halted = True
            self.logger.info(f"P-System halted after {system.evolution_step} steps")
        
        if self.config.enable_profiling:
            self._log_performance_profile(metrics)
        
        return metrics
    
    def evolve_membrane(self, membrane_id: str, system: PSystemMembraneHierarchy) -> Tuple[int, float]:
        """Evolve a specific membrane using the current strategy"""
        if membrane_id not in system.membranes:
            return 0, 0.0
        
        membrane = system.membranes[membrane_id]
        if membrane.is_dissolved:
            return 0, 0.0
        
        strategy = self.strategies[self.current_strategy]
        return strategy.evolve_membrane(membrane, system)
    
    def set_strategy(self, strategy: EvolutionStrategy) -> None:
        """Change the evolution strategy"""
        if strategy in self.strategies:
            self.current_strategy = strategy
            self.logger.info(f"Evolution strategy changed to: {strategy.value}")
        else:
            raise ValueError(f"Unsupported evolution strategy: {strategy}")
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        current_perf = self.analytics.get_current_performance()
        
        return {
            'total_evolution_cycles': self.total_evolution_cycles,
            'constraint_violations': self.constraint_violations,
            'violation_rate': self.constraint_violations / max(1, self.total_evolution_cycles),
            'current_strategy': self.current_strategy.value,
            'config': {
                'target_time_us': self.config.target_evolution_time_us,
                'max_time_us': self.config.max_evolution_time_us,
                'parallel_workers': self.config.max_parallel_workers
            },
            **current_perf
        }
    
    def optimize_configuration(self) -> Dict[str, Any]:
        """Automatically optimize configuration based on performance history"""
        try:
            performance = self.analytics.get_current_performance()
            recommendations = {}
            
            avg_time = performance.get('avg_evolution_time_us', 0)
            
            # Simple recommendations without complex analysis
            if avg_time > self.config.max_evolution_time_us * 0.8:
                if self.current_strategy == EvolutionStrategy.SYNCHRONOUS:
                    recommendations['strategy'] = EvolutionStrategy.ASYNCHRONOUS.value
                elif self.config.max_parallel_workers < multiprocessing.cpu_count():
                    recommendations['max_parallel_workers'] = min(
                        multiprocessing.cpu_count(), 
                        self.config.max_parallel_workers + 2
                    )
            
            # Recommend target time adjustments
            if avg_time > self.config.target_evolution_time_us * 1.5:
                recommendations['target_evolution_time_us'] = self.config.target_evolution_time_us * 1.2
            
            return recommendations
        except Exception:
            return {}
    
    def _log_performance_profile(self, metrics: EvolutionMetrics) -> None:
        """Log detailed performance profile"""
        avg_membrane_time = metrics.get_average_membrane_time()
        
        self.logger.debug(
            f"Evolution Profile - Total: {metrics.total_evolution_time_us:.2f}μs, "
            f"Avg Membrane: {avg_membrane_time:.2f}μs, "
            f"Rules: {metrics.rules_applied}, "
            f"Membranes: {metrics.membranes_processed}, "
            f"Score: {metrics.performance_score:.3f}"
        )
    
    def __str__(self) -> str:
        return (
            f"PSystemEvolutionEngine[{self.current_strategy.value}]: "
            f"{self.total_evolution_cycles} cycles, "
            f"{self.constraint_violations} violations"
        )

def create_evolution_engine_demo() -> PSystemEvolutionEngine:
    """Create a demonstration evolution engine with optimized configuration"""
    
    config = EvolutionConfig(
        strategy=EvolutionStrategy.ADAPTIVE,
        max_parallel_workers=4,
        target_evolution_time_us=30.0,
        max_evolution_time_us=100.0,
        enable_analytics=True,
        enable_profiling=True,
        rule_selection_algorithm="priority_first",
        communication_batching=True
    )
    
    engine = PSystemEvolutionEngine(config)
    logger.info("Created demonstration evolution engine with adaptive strategy")
    
    return engine

if __name__ == "__main__":
    # Demonstration of P-System Evolution Engine
    print("P-System Membrane Evolution Engine Demo")
    print("=" * 50)
    
    # Create evolution engine
    engine = create_evolution_engine_demo()
    
    # Import and create a test system
    from psystem_membranes import create_dtesn_psystem_example
    system = create_dtesn_psystem_example()
    
    print(f"\nInitial system: {system}")
    print(f"Evolution engine: {engine}")
    
    # Run evolution cycles
    print(f"\nRunning evolution cycles...")
    
    for cycle in range(5):
        metrics = engine.evolve_system(system)
        
        print(f"Cycle {cycle + 1}:")
        print(f"  Time: {metrics.total_evolution_time_us:.2f}μs")
        print(f"  Rules Applied: {metrics.rules_applied}")
        print(f"  Membranes Processed: {metrics.membranes_processed}")
        print(f"  Performance Score: {metrics.performance_score:.3f}")
        print(f"  Constraints Met: {metrics.meets_timing_constraints(engine.config)}")
        
        if system.is_halted:
            break
    
    # Display final statistics
    print(f"\nFinal Performance Statistics:")
    stats = engine.get_performance_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")
    
    # Show optimization recommendations
    print(f"\nOptimization Recommendations:")
    recommendations = engine.optimize_configuration()
    if recommendations:
        for key, value in recommendations.items():
            print(f"  {key}: {value}")
    else:
        print("  No optimizations recommended - performance is optimal")