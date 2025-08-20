"""
DTESN Integration Bridge for Meta-Learning System

Connects meta-learning optimizer with DTESN kernel components including
membrane computing, B-Series ridges, and ESN reservoir dynamics.
"""

from typing import Dict, List, Any
import logging
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


def _mean(values: List[float]) -> float:
    """Calculate mean of values."""
    return sum(values) / len(values) if values else 0.0


def _std(values: List[float]) -> float:
    """Calculate standard deviation of values."""
    if len(values) < 2:
        return 0.0
    mean_val = _mean(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    return variance ** 0.5


@dataclass
class DTESNPerformanceMetrics:
    """Performance metrics from DTESN kernel components."""
    membrane_efficiency: float
    reservoir_stability: float
    b_series_convergence: float
    memory_usage: Dict[str, float]
    computation_time: Dict[str, float]


class DTESNMetaLearningBridge:
    """Bridge between meta-learning optimizer and DTESN kernel components."""
    
    def __init__(self, meta_optimizer=None):
        self.meta_optimizer = meta_optimizer
        self.dtesn_kernel = None
        self.performance_cache = {}
        
        # DTESN-specific meta-parameters
        self.dtesn_meta_params = {
            'membrane_hierarchy_depth': 8,
            'reservoir_size_factor': 1.0,
            'b_series_order': 16,
            'plasticity_threshold': 0.1,
            'homeostasis_target': 0.5
        }
        
        logger.info("DTESN meta-learning bridge initialized")
    
    def set_dtesn_kernel(self, dtesn_kernel) -> None:
        """Set DTESN kernel reference."""
        self.dtesn_kernel = dtesn_kernel
        logger.info("DTESN kernel integration enabled in meta-learning bridge")
    
    async def extract_dtesn_metrics(self) -> DTESNPerformanceMetrics:
        """Extract performance metrics from DTESN kernel."""
        if not self.dtesn_kernel:
            # Return mock metrics for testing
            return DTESNPerformanceMetrics(
                membrane_efficiency=0.8,
                reservoir_stability=0.7,
                b_series_convergence=0.9,
                memory_usage={'reservoir': 0.6, 'membranes': 0.3},
                computation_time={'forward': 0.001, 'learning': 0.01}
            )
        
        # Extract real metrics from DTESN kernel
        try:
            metrics = DTESNPerformanceMetrics(
                membrane_efficiency=await self._get_membrane_efficiency(),
                reservoir_stability=await self._get_reservoir_stability(),
                b_series_convergence=await self._get_b_series_convergence(),
                memory_usage=await self._get_memory_usage(),
                computation_time=await self._get_computation_times()
            )
            return metrics
        except Exception as e:
            logger.warning(f"Failed to extract DTESN metrics: {e}")
            # Return default metrics
            return DTESNPerformanceMetrics(
                membrane_efficiency=0.5,
                reservoir_stability=0.5,
                b_series_convergence=0.5,
                memory_usage={'unknown': 0.5},
                computation_time={'unknown': 0.001}
            )
    
    async def _get_membrane_efficiency(self) -> float:
        """Get P-System membrane computing efficiency."""
        # Placeholder for actual DTESN kernel integration
        # In real implementation, this would query the membrane computing system
        return random.uniform(0.6, 0.9)  # Mock efficiency
    
    async def _get_reservoir_stability(self) -> float:
        """Get ESN reservoir stability metric."""
        # Placeholder for actual reservoir dynamics measurement
        return random.uniform(0.5, 0.8)  # Mock stability
    
    async def _get_b_series_convergence(self) -> float:
        """Get B-Series ridge convergence rate."""
        # Placeholder for B-Series differential operator convergence
        return random.uniform(0.7, 0.95)  # Mock convergence
    
    async def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics from DTESN components."""
        return {
            'reservoir': random.uniform(0.4, 0.8),
            'membranes': random.uniform(0.2, 0.6),
            'b_series': random.uniform(0.1, 0.3)
        }
    
    async def _get_computation_times(self) -> Dict[str, float]:
        """Get computation time statistics from DTESN components."""
        return {
            'membrane_evolution': random.uniform(0.001, 0.01),  # 1μs to 10μs
            'reservoir_update': random.uniform(0.0001, 0.001),  # 0.1ms to 1ms
            'b_series_computation': random.uniform(0.00001, 0.0001)  # 10μs to 100μs
        }
    
    async def optimize_dtesn_parameters(
        self, 
        current_config: Dict[str, Any],
        performance_history: List[DTESNPerformanceMetrics]
    ) -> Dict[str, Any]:
        """Optimize DTESN parameters based on performance history."""
        if len(performance_history) < 5:
            return current_config
        
        optimized_config = current_config.copy()
        
        # Analyze performance trends
        recent_metrics = performance_history[-10:]
        
        # Optimize membrane hierarchy depth
        avg_membrane_efficiency = _mean([m.membrane_efficiency for m in recent_metrics])
        if avg_membrane_efficiency < 0.6:
            # Increase hierarchy depth for better efficiency
            optimized_config['membrane_hierarchy_depth'] = min(12, 
                current_config.get('membrane_hierarchy_depth', 8) + 1)
            logger.debug("Increased membrane hierarchy depth for better efficiency")
        
        # Optimize reservoir size
        avg_stability = _mean([m.reservoir_stability for m in recent_metrics])
        if avg_stability < 0.5:
            # Increase reservoir size factor for better stability
            optimized_config['reservoir_size_factor'] = min(2.0,
                current_config.get('reservoir_size_factor', 1.0) * 1.1)
            logger.debug("Increased reservoir size factor for better stability")
        
        # Optimize B-Series order
        avg_convergence = _mean([m.b_series_convergence for m in recent_metrics])
        if avg_convergence < 0.7:
            # Increase B-Series order for better convergence
            optimized_config['b_series_order'] = min(32,
                current_config.get('b_series_order', 16) + 2)
            logger.debug("Increased B-Series order for better convergence")
        
        # Memory usage optimization
        avg_memory = _mean([
            sum(m.memory_usage.values()) for m in recent_metrics
        ])
        if avg_memory > 0.8:
            # Reduce parameters if memory usage is too high
            optimized_config['reservoir_size_factor'] *= 0.9
            logger.debug("Reduced reservoir size due to high memory usage")
        
        return optimized_config
    
    async def apply_meta_learning_to_dtesn(
        self, 
        architecture_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply meta-learning insights to DTESN configuration."""
        if not self.meta_optimizer:
            return architecture_params
        
        # Get meta-learning recommendations
        recommendations = await self.meta_optimizer.get_architecture_recommendations(3)
        
        if not recommendations:
            return architecture_params
        
        # Apply top recommendation to DTESN parameters
        top_recommendation = recommendations[0]
        optimized_params = architecture_params.copy()
        
        # Map meta-learning parameters to DTESN configuration
        rec_params = top_recommendation['architecture_params']
        
        # Membrane computing optimizations
        if 'membrane_depth' in rec_params:
            optimized_params['membrane_hierarchy_depth'] = int(rec_params['membrane_depth'])
        
        # Reservoir computing optimizations  
        if 'reservoir_scaling' in rec_params:
            optimized_params['reservoir_size_factor'] = float(rec_params['reservoir_scaling'])
        
        # B-Series optimizations
        if 'b_series_order' in rec_params:
            optimized_params['b_series_order'] = int(rec_params['b_series_order'])
        
        # Learning rate adaptations
        if 'plasticity_factor' in rec_params:
            optimized_params['plasticity_threshold'] = float(rec_params['plasticity_factor'])
        
        logger.info(f"Applied meta-learning recommendations to DTESN config: {optimized_params}")
        
        return optimized_params
    
    async def record_dtesn_performance(
        self,
        config: Dict[str, Any],
        performance_metrics: DTESNPerformanceMetrics,
        generation: int
    ) -> None:
        """Record DTESN performance for meta-learning."""
        if not self.meta_optimizer:
            return
        
        # Convert DTESN metrics to meta-learning architecture parameters
        architecture_params = {
            'membrane_hierarchy_depth': config.get('membrane_hierarchy_depth', 8),
            'reservoir_size_factor': config.get('reservoir_size_factor', 1.0),
            'b_series_order': config.get('b_series_order', 16),
            'plasticity_threshold': config.get('plasticity_threshold', 0.1)
        }
        
        # Calculate composite fitness score
        fitness_score = self._calculate_composite_fitness(performance_metrics)
        
        # Calculate convergence and diversity metrics
        convergence_rate = performance_metrics.b_series_convergence
        diversity_metric = self._calculate_dtesn_diversity(performance_metrics)
        
        # Record in meta-learning optimizer
        await self.meta_optimizer.record_architecture_performance(
            architecture_params=architecture_params,
            fitness_score=fitness_score,
            generation=generation,
            convergence_rate=convergence_rate,
            diversity_metric=diversity_metric,
            resource_usage={
                'memory_total': sum(performance_metrics.memory_usage.values()),
                'compute_time': sum(performance_metrics.computation_time.values())
            }
        )
    
    def _calculate_composite_fitness(self, metrics: DTESNPerformanceMetrics) -> float:
        """Calculate composite fitness score from DTESN metrics."""
        # Weighted combination of performance metrics
        weights = {
            'membrane_efficiency': 0.3,
            'reservoir_stability': 0.3,
            'b_series_convergence': 0.2,
            'memory_efficiency': 0.1,
            'compute_efficiency': 0.1
        }
        
        # Memory efficiency (inverse of usage)
        total_memory = sum(metrics.memory_usage.values())
        memory_efficiency = max(0.0, 1.0 - total_memory)
        
        # Compute efficiency (inverse of time)
        total_compute_time = sum(metrics.computation_time.values())
        compute_efficiency = max(0.0, 1.0 - min(1.0, total_compute_time * 1000))  # Scale to reasonable range
        
        fitness = (
            weights['membrane_efficiency'] * metrics.membrane_efficiency +
            weights['reservoir_stability'] * metrics.reservoir_stability +
            weights['b_series_convergence'] * metrics.b_series_convergence +
            weights['memory_efficiency'] * memory_efficiency +
            weights['compute_efficiency'] * compute_efficiency
        )
        
        return max(0.0, min(1.0, fitness))
    
    def _calculate_dtesn_diversity(self, metrics: DTESNPerformanceMetrics) -> float:
        """Calculate diversity metric for DTESN configuration."""
        # Simple diversity based on variance of component performances
        performance_values = [
            metrics.membrane_efficiency,
            metrics.reservoir_stability,
            metrics.b_series_convergence
        ]
        
        return _std(performance_values) if len(performance_values) > 1 else 0.5
    
    def get_dtesn_integration_stats(self) -> Dict[str, Any]:
        """Get DTESN integration statistics."""
        return {
            'dtesn_kernel_connected': self.dtesn_kernel is not None,
            'meta_optimizer_connected': self.meta_optimizer is not None,
            'dtesn_meta_params': self.dtesn_meta_params.copy(),
            'performance_cache_size': len(self.performance_cache)
        }