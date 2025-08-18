"""
Core Evolution Engine for Echo-Self AI System

Main orchestrator for self-optimizing neural architectures through genetic
algorithms. Integrates with meta-learning system for architecture optimization.
"""

from typing import List, Dict, Optional, Tuple, Any
import asyncio
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Import meta-learning components
from ..meta_learning import MetaLearningOptimizer, MetaLearningConfig, DTESNMetaLearningBridge

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """Configuration for evolution engine parameters."""
    population_size: int = 100
    mutation_rate: float = 0.01
    selection_pressure: float = 0.8
    crossover_rate: float = 0.7
    elitism_ratio: float = 0.1
    max_generations: int = 1000
    fitness_threshold: float = 0.95


class Individual(ABC):
    """Base class for evolvable individuals."""
    
    def __init__(self, genome: Dict[str, Any]):
        self.genome = genome
        self.fitness = 0.0
        self.age = 0
        self.performance_history = []
    
    @abstractmethod
    async def evaluate_fitness(self, environment) -> float:
        """Evaluate individual fitness in given environment."""
        pass
    
    @abstractmethod
    def mutate(self, mutation_rate: float) -> 'Individual':
        """Apply mutations to create new individual."""
        pass
    
    @abstractmethod
    def crossover(self, other: 'Individual') -> Tuple['Individual', 'Individual']:
        """Perform crossover with another individual."""
        pass


class EchoSelfEvolutionEngine:
    """Main evolution engine for self-optimizing AI systems."""
    
    def __init__(self, config: EvolutionConfig, enable_meta_learning: bool = True):
        self.config = config
        self.population: List[Individual] = []
        self.generation = 0
        self.best_individual: Optional[Individual] = None
        self.evolution_history = []
        
        # Integration points
        self.dtesn_kernel = None
        self.aar_orchestrator = None
        
        # Meta-learning integration
        self.enable_meta_learning = enable_meta_learning
        self.meta_optimizer = None
        self.dtesn_bridge = None
        
        if enable_meta_learning:
            meta_config = MetaLearningConfig()
            self.meta_optimizer = MetaLearningOptimizer(meta_config)
            self.dtesn_bridge = DTESNMetaLearningBridge(self.meta_optimizer)
            logger.info("Meta-learning system enabled")
        
        logger.info(f"Echo-Self Evolution Engine initialized with config: {config}")
    
    def set_dtesn_integration(self, dtesn_kernel):
        """Set DTESN kernel integration."""
        self.dtesn_kernel = dtesn_kernel
        
        # Set integration for meta-learning components
        if self.meta_optimizer:
            self.meta_optimizer.set_dtesn_integration(dtesn_kernel)
        if self.dtesn_bridge:
            self.dtesn_bridge.set_dtesn_kernel(dtesn_kernel)
        
        logger.info("DTESN kernel integration enabled")
    
    def set_aar_integration(self, aar_orchestrator):
        """Set AAR orchestrator integration.""" 
        self.aar_orchestrator = aar_orchestrator
        
        # Set integration for meta-learning components
        if self.meta_optimizer:
            self.meta_optimizer.set_evolution_engine(self)
        
        logger.info("AAR orchestrator integration enabled")
    
    async def initialize_population(self, individual_factory) -> None:
        """Initialize population with random individuals."""
        self.population = []
        
        for i in range(self.config.population_size):
            individual = individual_factory()
            self.population.append(individual)
        
        logger.info(f"Population initialized with {len(self.population)} individuals")
    
    async def evolve_step(self) -> Dict[str, Any]:
        """Execute single evolution step with meta-learning optimization."""
        if not self.population:
            raise RuntimeError("Population not initialized")
        
        # Apply meta-learning optimization to evolution parameters
        if self.meta_optimizer and self.generation > 0:
            current_params = {
                'mutation_rate': self.config.mutation_rate,
                'selection_pressure': self.config.selection_pressure,
                'crossover_rate': self.config.crossover_rate,
                'population_size': self.config.population_size,
                'elitism_ratio': self.config.elitism_ratio
            }
            
            optimized_params = await self.meta_optimizer.optimize_evolution_parameters(current_params)
            
            # Update evolution config with optimized parameters
            self.config.mutation_rate = optimized_params.get('mutation_rate', self.config.mutation_rate)
            self.config.selection_pressure = optimized_params.get('selection_pressure', self.config.selection_pressure)
            self.config.crossover_rate = optimized_params.get('crossover_rate', self.config.crossover_rate)
            
            logger.debug(f"Applied meta-learning optimization: {optimized_params}")
        
        # Evaluate fitness for all individuals
        fitness_scores = await self._evaluate_population()
        
        # Update population fitness
        for individual, fitness in zip(self.population, fitness_scores):
            individual.fitness = fitness
            individual.performance_history.append(fitness)
        
        # Track best individual
        best_idx = fitness_scores.index(max(fitness_scores))
        self.best_individual = self.population[best_idx]
        
        # Record architecture performance for meta-learning
        if self.meta_optimizer:
            await self._record_meta_learning_data(fitness_scores)
        
        # Selection and reproduction
        new_population = await self._create_next_generation()
        
        # Replace population
        self.population = new_population
        self.generation += 1
        
        # Record evolution statistics
        stats = {
            'generation': self.generation,
            'best_fitness': max(fitness_scores),
            'average_fitness': sum(fitness_scores) / len(fitness_scores),
            'population_diversity': self._calculate_diversity(),
            'convergence_rate': self._calculate_convergence_rate()
        }
        
        self.evolution_history.append(stats)
        logger.info(f"Generation {self.generation}: Best={stats['best_fitness']:.4f}, "
                   f"Avg={stats['average_fitness']:.4f}")
        
        return stats
    
    async def _evaluate_population(self) -> List[float]:
        """Evaluate fitness for entire population."""
        fitness_scores = []
        
        # Create evaluation tasks for parallel processing
        evaluation_tasks = []
        for individual in self.population:
            task = self._evaluate_individual(individual)
            evaluation_tasks.append(task)
        
        # Execute evaluations in parallel
        fitness_scores = await asyncio.gather(*evaluation_tasks)
        
        return fitness_scores
    
    async def _evaluate_individual(self, individual: Individual) -> float:
        """Evaluate single individual fitness."""
        try:
            # Create evaluation environment
            environment = await self._create_evaluation_environment(individual)
            
            # Evaluate fitness
            fitness = await individual.evaluate_fitness(environment)
            
            return fitness
        except Exception as e:
            logger.error(f"Error evaluating individual: {e}")
            return 0.0
    
    async def _create_evaluation_environment(self, individual: Individual) -> Dict:
        """Create evaluation environment for individual."""
        environment = {
            'generation': self.generation,
            'individual_id': id(individual)
        }
        
        # Add DTESN context if available
        if self.dtesn_kernel:
            environment['dtesn_state'] = await self._get_dtesn_context()
        
        # Add AAR context if available
        if self.aar_orchestrator:
            environment['aar_context'] = await self._get_aar_context()
        
        return environment
    
    async def _get_dtesn_context(self) -> Dict:
        """Get current DTESN kernel context."""
        # Placeholder for DTESN integration
        return {
            'membrane_states': [],
            'reservoir_dynamics': {},
            'b_series_coefficients': []
        }
    
    async def _get_aar_context(self) -> Dict:
        """Get current AAR orchestrator context."""
        # Placeholder for AAR integration
        return {
            'active_agents': 0,
            'arena_utilization': 0.0,
            'relation_graph_density': 0.0
        }
    
    async def _create_next_generation(self) -> List[Individual]:
        """Create next generation through selection and reproduction."""
        new_population = []
        
        # Elitism: Keep best individuals
        elite_count = int(self.config.population_size * self.config.elitism_ratio)
        elite_individuals = sorted(self.population, 
                                 key=lambda x: x.fitness, reverse=True)[:elite_count]
        new_population.extend(elite_individuals)
        
        # Fill remaining population through reproduction
        while len(new_population) < self.config.population_size:
            # Selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Reproduction
            if len(new_population) < self.config.population_size - 1:
                # Crossover
                if await self._should_crossover():
                    offspring1, offspring2 = parent1.crossover(parent2)
                    new_population.extend([offspring1, offspring2])
                else:
                    # Direct reproduction with mutation
                    offspring1 = parent1.mutate(self.config.mutation_rate)
                    offspring2 = parent2.mutate(self.config.mutation_rate)
                    new_population.extend([offspring1, offspring2])
            else:
                # Single offspring
                offspring = parent1.mutate(self.config.mutation_rate)
                new_population.append(offspring)
        
        return new_population[:self.config.population_size]
    
    def _tournament_selection(self, tournament_size: int = 3) -> Individual:
        """Tournament selection for parent selection."""
        import random
        
        tournament = random.sample(self.population, tournament_size)
        winner = max(tournament, key=lambda x: x.fitness)
        return winner
    
    async def _should_crossover(self) -> bool:
        """Determine if crossover should occur."""
        import random
        return random.random() < self.config.crossover_rate
    
    def _calculate_diversity(self) -> float:
        """Calculate population diversity metric."""
        # Placeholder diversity calculation
        # In practice, this would measure genetic diversity
        return 0.5
    
    def _calculate_convergence_rate(self) -> float:
        """Calculate convergence rate."""
        if len(self.evolution_history) < 2:
            return 0.0
        
        current_avg = self.evolution_history[-1]['average_fitness']
        previous_avg = self.evolution_history[-2]['average_fitness']
        
        return current_avg - previous_avg
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current evolution statistics."""
        stats = {
            'generation': self.generation,
            'population_size': len(self.population),
            'best_fitness': self.best_individual.fitness if self.best_individual else 0.0,
            'evolution_history': self.evolution_history.copy(),
            'config': self.config
        }
        
        # Add integration status
        stats.update(self.get_integration_status())
        
        # Add meta-learning statistics if available
        if self.meta_optimizer:
            stats['meta_learning'] = self.meta_optimizer.get_meta_learning_stats()
        if self.dtesn_bridge:
            stats['dtesn_integration'] = self.dtesn_bridge.get_dtesn_integration_stats()
        
        return stats
    
    async def _record_meta_learning_data(self, fitness_scores: List[float]) -> None:
        """Record architecture performance data for meta-learning."""
        if not self.meta_optimizer:
            return
        
        # Record performance for best performing individuals
        sorted_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)
        top_performers = sorted_indices[:min(5, len(sorted_indices))]
        
        for idx in top_performers:
            individual = self.population[idx]
            fitness = fitness_scores[idx]
            
            # Extract architecture parameters from individual
            architecture_params = self._extract_architecture_params(individual)
            
            # Calculate convergence and diversity metrics
            convergence_rate = self._calculate_convergence_rate()
            diversity_metric = self._calculate_diversity()
            
            # Record performance in meta-learning system
            await self.meta_optimizer.record_architecture_performance(
                architecture_params=architecture_params,
                fitness_score=fitness,
                generation=self.generation,
                convergence_rate=convergence_rate,
                diversity_metric=diversity_metric
            )
        
        # Also record DTESN performance if bridge is available
        if self.dtesn_bridge and self.dtesn_kernel:
            dtesn_metrics = await self.dtesn_bridge.extract_dtesn_metrics()
            dtesn_config = await self._get_dtesn_config()
            
            await self.dtesn_bridge.record_dtesn_performance(
                config=dtesn_config,
                performance_metrics=dtesn_metrics,
                generation=self.generation
            )
    
    def _extract_architecture_params(self, individual: Individual) -> Dict[str, Any]:
        """Extract architecture parameters from individual for meta-learning."""
        # Extract relevant parameters from individual's genome
        architecture_params = {}
        
        if hasattr(individual, 'genome') and isinstance(individual.genome, dict):
            # Common architecture parameters
            for key in ['layer_count', 'hidden_size', 'learning_rate', 'dropout_rate',
                       'activation_function', 'optimizer_type', 'batch_size']:
                if key in individual.genome:
                    architecture_params[key] = individual.genome[key]
            
            # DTESN-specific parameters
            for key in ['membrane_depth', 'reservoir_scaling', 'b_series_order', 'plasticity_factor']:
                if key in individual.genome:
                    architecture_params[key] = individual.genome[key]
        
        # Add default values if not present
        if not architecture_params:
            architecture_params = {
                'fitness': individual.fitness,
                'age': individual.age,
                'genome_size': len(str(individual.genome)) if hasattr(individual, 'genome') else 0
            }
        
        return architecture_params
    
    async def _get_dtesn_config(self) -> Dict[str, Any]:
        """Get current DTESN configuration."""
        # Default DTESN configuration
        default_config = {
            'membrane_hierarchy_depth': 8,
            'reservoir_size_factor': 1.0,
            'b_series_order': 16,
            'plasticity_threshold': 0.1,
            'homeostasis_target': 0.5
        }
        
        # Try to get actual config from DTESN kernel
        if self.dtesn_kernel:
            try:
                # Placeholder for actual DTESN kernel config extraction
                # In real implementation, this would query the kernel
                return default_config
            except Exception as e:
                logger.warning(f"Failed to get DTESN config: {e}")
                return default_config
        
        return default_config
    
    async def save_checkpoint(self, filepath: str) -> None:
        """Save evolution state to file."""
        import pickle
        
        checkpoint_data = {
            'config': self.config,
            'population': self.population,
            'generation': self.generation,
            'best_individual': self.best_individual,
            'evolution_history': self.evolution_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        logger.info(f"Checkpoint saved to {filepath}")
    
    async def load_checkpoint(self, filepath: str) -> None:
        """Load evolution state from file."""
        import pickle
        
        with open(filepath, 'rb') as f:
            checkpoint_data = pickle.load(f)
        
        self.config = checkpoint_data['config']
        self.population = checkpoint_data['population']
        self.generation = checkpoint_data['generation']
        self.best_individual = checkpoint_data['best_individual']
        self.evolution_history = checkpoint_data['evolution_history']
        
        logger.info(f"Checkpoint loaded from {filepath}")
    
    def enable_aar_integration(self, aar_orchestrator) -> None:
        """Enable integration with AAR Core Orchestrator."""
        self.aar_orchestrator = aar_orchestrator
        logger.info("AAR orchestrator integration enabled")
    
    def enable_aphrodite_integration(self, aphrodite_bridge) -> None:
        """Enable integration with Aphrodite Engine bridge."""
        self.aphrodite_bridge = aphrodite_bridge
        logger.info("Aphrodite Engine bridge integration enabled")
    
    def get_integration_status(self) -> Dict[str, bool]:
        """Get current integration status."""
        return {
            'aar_integration_enabled': hasattr(self, 'aar_orchestrator') and 
                                     self.aar_orchestrator is not None,
            'aphrodite_integration_enabled': hasattr(self, 'aphrodite_bridge') and 
                                           self.aphrodite_bridge is not None,
            'dtesn_integration_enabled': hasattr(self, 'dtesn_kernel') and 
                                        self.dtesn_kernel is not None,
            'meta_learning_enabled': self.meta_optimizer is not None
        }
        
        logger.info(f"Checkpoint loaded from {filepath}")