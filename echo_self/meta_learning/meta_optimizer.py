"""
Meta-Learning Optimizer for Architecture Optimization

Implements meta-learning algorithms that learn from previous evolution attempts
to optimize neural architecture parameters and evolution strategies.
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
import math

logger = logging.getLogger(__name__)


@dataclass
class MetaLearningConfig:
    """Configuration for meta-learning optimizer."""
    learning_rate: float = 0.001
    adaptation_rate: float = 0.01
    memory_size: int = 1000
    batch_size: int = 32
    update_frequency: int = 10
    exploration_rate: float = 0.1
    temperature: float = 1.0


@dataclass
class ArchitecturePerformance:
    """Record of architecture performance for meta-learning."""
    architecture_params: Dict[str, Any]
    fitness_score: float
    generation: int
    timestamp: datetime
    convergence_rate: float
    diversity_metric: float
    resource_usage: Dict[str, float] = field(default_factory=dict)


class ExperienceReplay:
    """Experience replay system for storing and retrieving evolution history."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.experiences: List[ArchitecturePerformance] = []
        self.performance_index = {}  # Index by architecture hash for fast lookup
        
    def add_experience(self, experience: ArchitecturePerformance) -> None:
        """Add new architecture performance experience."""
        # Create hash for architecture params for indexing
        arch_hash = self._hash_architecture(experience.architecture_params)
        
        # Remove oldest experience if at capacity
        if len(self.experiences) >= self.max_size:
            removed = self.experiences.pop(0)
            old_hash = self._hash_architecture(removed.architecture_params)
            if old_hash in self.performance_index:
                del self.performance_index[old_hash]
        
        self.experiences.append(experience)
        self.performance_index[arch_hash] = len(self.experiences) - 1
        
        logger.debug(f"Added experience: fitness={experience.fitness_score:.4f}, gen={experience.generation}")
    
    def sample_batch(self, batch_size: int) -> List[ArchitecturePerformance]:
        """Sample a batch of experiences for training."""
        if len(self.experiences) < batch_size:
            return self.experiences.copy()
        
        # Prioritized sampling based on fitness scores
        weights = [exp.fitness_score + 1e-8 for exp in self.experiences]  # Avoid zero weights
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        # Sample without replacement
        sampled_indices = set()
        batch = []
        
        while len(batch) < batch_size and len(sampled_indices) < len(self.experiences):
            # Weighted random selection
            r = random.random()
            cumulative_prob = 0.0
            for i, prob in enumerate(probabilities):
                cumulative_prob += prob
                if r <= cumulative_prob and i not in sampled_indices:
                    sampled_indices.add(i)
                    batch.append(self.experiences[i])
                    break
        
        return batch
    
    def get_top_performers(self, n: int = 10) -> List[ArchitecturePerformance]:
        """Get top N performing architectures."""
        sorted_experiences = sorted(
            self.experiences, 
            key=lambda x: x.fitness_score, 
            reverse=True
        )
        return sorted_experiences[:n]
    
    def get_recent_experiences(self, n: int = 100) -> List[ArchitecturePerformance]:
        """Get most recent N experiences."""
        return self.experiences[-n:]
    
    def _hash_architecture(self, arch_params: Dict[str, Any]) -> str:
        """Create hash string for architecture parameters."""
        # Sort keys for consistent hashing
        sorted_params = {k: arch_params[k] for k in sorted(arch_params.keys())}
        return str(hash(json.dumps(sorted_params, sort_keys=True, default=str)))


def _mean(values: List[float]) -> float:
    """Calculate mean of values."""
    return sum(values) / len(values) if values else 0.0


def _std(values: List[float]) -> float:
    """Calculate standard deviation of values."""
    if len(values) < 2:
        return 0.0
    mean_val = _mean(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def _polyfit_slope(x_values: List[float], y_values: List[float]) -> float:
    """Calculate slope of linear fit (simplified)."""
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0
    
    n = len(x_values)
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x_squared = sum(x * x for x in x_values)
    
    denominator = n * sum_x_squared - sum_x * sum_x
    if abs(denominator) < 1e-10:
        return 0.0
    
    return (n * sum_xy - sum_x * sum_y) / denominator


class MetaLearningOptimizer:
    """Meta-learning system for optimizing architecture evolution strategies."""
    
    def __init__(self, config: MetaLearningConfig):
        self.config = config
        self.experience_replay = ExperienceReplay(config.memory_size)
        self.meta_parameters = self._initialize_meta_parameters()
        self.update_count = 0
        self.performance_trends = {}
        
        # Integration points
        self.dtesn_kernel = None
        self.evolution_engine = None
        
        logger.info(f"Meta-learning optimizer initialized with config: {config}")
    
    def _initialize_meta_parameters(self) -> Dict[str, float]:
        """Initialize meta-learning parameters."""
        return {
            'mutation_rate_adaptation': 1.0,
            'selection_pressure_adaptation': 1.0,
            'crossover_rate_adaptation': 1.0,
            'population_diversity_weight': 0.5,
            'convergence_speed_weight': 0.3,
            'resource_efficiency_weight': 0.2
        }
    
    def set_dtesn_integration(self, dtesn_kernel) -> None:
        """Set DTESN kernel integration for membrane computing."""
        self.dtesn_kernel = dtesn_kernel
        logger.info("DTESN kernel integration enabled for meta-learning")
    
    def set_evolution_engine(self, evolution_engine) -> None:
        """Set evolution engine integration."""
        self.evolution_engine = evolution_engine
        logger.info("Evolution engine integration enabled for meta-learning")
    
    async def record_architecture_performance(
        self, 
        architecture_params: Dict[str, Any],
        fitness_score: float,
        generation: int,
        convergence_rate: float = 0.0,
        diversity_metric: float = 0.0,
        resource_usage: Optional[Dict[str, float]] = None
    ) -> None:
        """Record performance of an architecture for meta-learning."""
        experience = ArchitecturePerformance(
            architecture_params=architecture_params,
            fitness_score=fitness_score,
            generation=generation,
            timestamp=datetime.now(),
            convergence_rate=convergence_rate,
            diversity_metric=diversity_metric,
            resource_usage=resource_usage or {}
        )
        
        self.experience_replay.add_experience(experience)
        
        # Update meta-parameters if enough experiences collected
        if len(self.experience_replay.experiences) % self.config.update_frequency == 0:
            await self._update_meta_parameters()
    
    async def optimize_evolution_parameters(self, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize evolution parameters based on meta-learning."""
        if len(self.experience_replay.experiences) < self.config.batch_size:
            logger.debug("Insufficient experience for meta-learning optimization")
            return current_params
        
        # Analyze recent performance trends
        trends = await self._analyze_performance_trends()
        
        # Apply meta-parameter adaptations
        optimized_params = current_params.copy()
        
        # Adapt mutation rate based on convergence trends
        if trends.get('stagnation_detected', False):
            optimized_params['mutation_rate'] *= self.meta_parameters['mutation_rate_adaptation']
            logger.debug(f"Increased mutation rate to {optimized_params['mutation_rate']:.4f}")
        
        # Adapt selection pressure based on diversity trends
        if trends.get('low_diversity', False):
            optimized_params['selection_pressure'] *= 0.9  # Reduce selection pressure
            logger.debug(f"Reduced selection pressure to {optimized_params['selection_pressure']:.4f}")
        
        # Adapt crossover rate based on performance improvements
        if trends.get('crossover_beneficial', False):
            optimized_params['crossover_rate'] *= self.meta_parameters['crossover_rate_adaptation']
            logger.debug(f"Adjusted crossover rate to {optimized_params['crossover_rate']:.4f}")
        
        return optimized_params
    
    async def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends from recent experiences."""
        recent_experiences = self.experience_replay.get_recent_experiences(100)
        if len(recent_experiences) < 10:
            return {}
        
        # Calculate performance metrics
        fitness_scores = [exp.fitness_score for exp in recent_experiences]
        convergence_rates = [exp.convergence_rate for exp in recent_experiences]
        diversity_metrics = [exp.diversity_metric for exp in recent_experiences]
        
        trends = {
            'average_fitness': _mean(fitness_scores),
            'fitness_trend': _polyfit_slope(list(range(len(fitness_scores))), fitness_scores),
            'stagnation_detected': _std(fitness_scores[-20:]) < 0.001 if len(fitness_scores) >= 20 else False,
            'low_diversity': _mean(diversity_metrics[-10:]) < 0.3 if len(diversity_metrics) >= 10 else False,
            'convergence_speed': _mean(convergence_rates),
            'crossover_beneficial': self._evaluate_crossover_effectiveness(recent_experiences)
        }
        
        return trends
    
    def _evaluate_crossover_effectiveness(self, experiences: List[ArchitecturePerformance]) -> bool:
        """Evaluate if crossover operations are beneficial."""
        # Simplified heuristic: check if recent high-performing architectures
        # have parameter combinations suggesting successful crossover
        top_performers = sorted(experiences, key=lambda x: x.fitness_score, reverse=True)[:5]
        
        if len(top_performers) < 2:
            return False
        
        # Check for parameter diversity among top performers
        param_diversity = self._calculate_parameter_diversity(top_performers)
        return param_diversity > 0.5  # Threshold for beneficial crossover
    
    def _calculate_parameter_diversity(self, experiences: List[ArchitecturePerformance]) -> float:
        """Calculate diversity of architecture parameters."""
        if len(experiences) < 2:
            return 0.0
        
        # Simple diversity metric based on parameter value ranges
        param_keys = set()
        for exp in experiences:
            param_keys.update(exp.architecture_params.keys())
        
        diversity_sum = 0.0
        for key in param_keys:
            values = []
            for exp in experiences:
                if key in exp.architecture_params:
                    try:
                        values.append(float(exp.architecture_params[key]))
                    except (ValueError, TypeError):
                        continue
            
            if len(values) > 1:
                diversity_sum += _std(values) / (_mean(values) + 1e-8)
        
        return diversity_sum / len(param_keys) if param_keys else 0.0
    
    async def _update_meta_parameters(self) -> None:
        """Update meta-parameters based on recent performance data."""
        self.update_count += 1
        
        # Sample batch for meta-parameter update
        batch = self.experience_replay.sample_batch(self.config.batch_size)
        
        if len(batch) < self.config.batch_size // 2:
            return
        
        # Calculate meta-gradient updates (simplified MAML-like approach)
        performance_gradient = self._calculate_performance_gradient(batch)
        
        # Update meta-parameters with gradient descent
        for param_name, gradient in performance_gradient.items():
            if param_name in self.meta_parameters:
                self.meta_parameters[param_name] -= self.config.learning_rate * gradient
                # Clamp values to reasonable ranges
                self.meta_parameters[param_name] = max(0.1, min(2.0, self.meta_parameters[param_name]))
        
        logger.info(f"Updated meta-parameters (update #{self.update_count}): {self.meta_parameters}")
    
    def _calculate_performance_gradient(self, batch: List[ArchitecturePerformance]) -> Dict[str, float]:
        """Calculate gradients for meta-parameter updates."""
        # Simplified gradient calculation based on performance correlation
        gradients = {}
        
        # Group experiences by similar architecture characteristics
        high_performers = [exp for exp in batch if exp.fitness_score > _mean([e.fitness_score for e in batch])]
        low_performers = [exp for exp in batch if exp.fitness_score <= _mean([e.fitness_score for e in batch])]
        
        # Calculate gradients based on performance differences
        for param_name in self.meta_parameters.keys():
            if 'adaptation' in param_name:
                # Higher adaptation for stagnant populations
                stagnation_factor = 1.0 - _mean([exp.convergence_rate for exp in high_performers])
                gradients[param_name] = stagnation_factor * 0.1
            else:
                # Weight-based gradients
                performance_diff = (
                    _mean([exp.fitness_score for exp in high_performers]) - 
                    _mean([exp.fitness_score for exp in low_performers])
                )
                gradients[param_name] = performance_diff * 0.01
        
        return gradients
    
    async def get_architecture_recommendations(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get architecture recommendations based on meta-learning insights."""
        if len(self.experience_replay.experiences) < n:
            return []
        
        # Get top performers
        top_performers = self.experience_replay.get_top_performers(n * 2)
        
        # Extract common patterns and generate recommendations
        recommendations = []
        for performer in top_performers[:n]:
            # Create recommendation based on successful architecture
            recommendation = {
                'architecture_params': performer.architecture_params.copy(),
                'expected_fitness': performer.fitness_score,
                'confidence': min(1.0, performer.fitness_score / max([p.fitness_score for p in top_performers])),
                'source_generation': performer.generation
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_meta_learning_stats(self) -> Dict[str, Any]:
        """Get current meta-learning statistics."""
        return {
            'total_experiences': len(self.experience_replay.experiences),
            'update_count': self.update_count,
            'meta_parameters': self.meta_parameters.copy(),
            'recent_performance': {
                'avg_fitness': _mean([exp.fitness_score for exp in self.experience_replay.get_recent_experiences(100)]),
                'max_fitness': max([exp.fitness_score for exp in self.experience_replay.experiences]) if self.experience_replay.experiences else 0.0
            } if self.experience_replay.experiences else {}
        }