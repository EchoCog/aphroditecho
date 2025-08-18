"""
Main Evolution Engine for Echo-Self AI System.

Orchestrates the evolutionary process for self-optimizing neural architectures
through genetic algorithms integrated with DTESN and Aphrodite Engine.
"""

import logging
from typing import List, Optional, Type
from dataclasses import dataclass

# Handle both absolute and relative imports
try:
    from core.interfaces import (
        Individual, Population, FitnessEvaluator, EvolutionConfig, 
        EvolutionObserver
    )
    from core.operators import (
        MutationOperator, SelectionOperator, CrossoverOperator, 
        ElitismOperator, DiversityOperator
    )
except ImportError:
    from .interfaces import (
        Individual, Population, FitnessEvaluator, EvolutionConfig, 
        EvolutionObserver
    )
    from .operators import (
        MutationOperator, SelectionOperator, CrossoverOperator, 
        ElitismOperator, DiversityOperator
    )

logger = logging.getLogger(__name__)


@dataclass
class EvolutionStats:
    """Statistics from an evolution run."""
    generation: int
    best_fitness: float
    average_fitness: float
    worst_fitness: float
    diversity: float
    convergence_rate: float
    elapsed_time: float


class EchoSelfEvolutionEngine:
    """Main evolution engine for self-optimizing AI systems."""
    
    def __init__(
        self,
        config: EvolutionConfig,
        fitness_evaluator: FitnessEvaluator,
        individual_class: Type[Individual],
        observers: Optional[List[EvolutionObserver]] = None
    ):
        self.config = config
        self.fitness_evaluator = fitness_evaluator
        self.individual_class = individual_class
        self.observers = observers or []
        
        # Evolution operators
        self.selection_operator = SelectionOperator("tournament")
        self.crossover_operator = CrossoverOperator("uniform")
        self.mutation_operator = MutationOperator()
        self.elitism_operator = ElitismOperator()
        self.diversity_operator = DiversityOperator(config.diversity_threshold)
        
        # Evolution state
        self.current_population: Optional[Population] = None
        self.generation: int = 0
        self.evolution_stats: List[EvolutionStats] = []
        self.is_running: bool = False
        
        # Integration components (will be set by bridges)
        self.dtesn_kernel = None
        self.aar_orchestrator = None
        
        logger.info(f"EchoSelfEvolutionEngine initialized with config: {config}")
    
    async def initialize_population(self, genome_factory) -> None:
        """Initialize population with random individuals."""
        self.current_population = Population()
        
        logger.info(f"Initializing population of size {self.config.population_size}")
        
        for i in range(self.config.population_size):
            genome = genome_factory()
            individual = self.individual_class(genome)
            individual.generation = 0
            self.current_population.add_individual(individual)
        
        # Evaluate initial population
        await self._evaluate_population(self.current_population)
        
        # Calculate initial statistics
        self.current_population.calculate_statistics()
        
        logger.info(
            f"Population initialized. Best fitness: {self.current_population.best_fitness:.4f}"
        )
    
    async def evolve(self, num_generations: Optional[int] = None) -> Population:
        """Run the evolutionary algorithm."""
        if self.current_population is None:
            raise ValueError(
                "Population not initialized. Call initialize_population() first."
            )
        
        max_generations = num_generations or self.config.max_generations
        self.is_running = True
        self.generation = 0
        
        logger.info(f"Starting evolution for {max_generations} generations")
        
        try:
            while self.generation < max_generations and self.is_running:
                await self._notify_observers_generation_start()
                
                # Create next generation
                await self._evolve_generation()
                
                # Update statistics
                stats = self._calculate_generation_stats()
                self.evolution_stats.append(stats)
                
                await self._notify_observers_generation_end()
                
                # Check for convergence
                if self._check_convergence():
                    logger.info(f"Evolution converged at generation {self.generation}")
                    break
                
                self.generation += 1
                
                # Log progress
                if self.generation % 10 == 0:
                    logger.info(
                        f"Generation {self.generation}: "
                        f"Best={stats.best_fitness:.4f}, "
                        f"Avg={stats.average_fitness:.4f}, "
                        f"Diversity={stats.diversity:.4f}"
                    )
        
        finally:
            self.is_running = False
            await self._notify_observers_evolution_complete()
        
        logger.info(f"Evolution completed after {self.generation} generations")
        return self.current_population
    
    async def _evolve_generation(self) -> None:
        """Evolve one generation."""
        if self.current_population is None:
            raise ValueError("No current population")
        
        # 1. Selection
        selected_population = self.selection_operator.apply(
            self.current_population, self.config
        )
        
        # 2. Crossover
        offspring_population = self.crossover_operator.apply(
            selected_population, self.config
        )
        
        # 3. Mutation
        mutated_population = self.mutation_operator.apply(
            offspring_population, self.config
        )
        
        # 4. Evaluate new individuals
        await self._evaluate_population(mutated_population)
        
        # 5. Apply elitism (combine with current population)
        elite_population = self.elitism_operator.apply(
            self.current_population, self.config
        )
        
        # 6. Combine elite with offspring
        combined_population = self._combine_populations(
            elite_population, mutated_population
        )
        
        # 7. Apply diversity maintenance
        diverse_population = self.diversity_operator.apply(
            combined_population, self.config
        )
        
        # 8. Trim to target population size
        self.current_population = self._trim_population(diverse_population)
        
        # Update generation counter
        self.current_population.generation = self.generation + 1
    
    async def _evaluate_population(self, population: Population) -> None:
        """Evaluate fitness for all individuals in the population."""
        logger.debug(f"Evaluating population of size {population.size()}")
        
        # Batch evaluate for efficiency
        fitnesses = await self.fitness_evaluator.batch_evaluate(population.individuals)
        
        # Update individual fitnesses
        for individual, fitness in zip(population.individuals, fitnesses):
            individual.fitness = fitness
            individual.performance_history.append(fitness)
        
        # Update population statistics
        population.calculate_statistics()
    
    def _combine_populations(self, pop1: Population, pop2: Population) -> Population:
        """Combine two populations into one."""
        combined = Population()
        combined.individuals = pop1.individuals + pop2.individuals
        combined.generation = max(pop1.generation, pop2.generation)
        return combined
    
    def _trim_population(self, population: Population) -> Population:
        """Trim population to target size, keeping the best individuals."""
        if population.size() <= self.config.population_size:
            return population
        
        # Sort by fitness (descending) and keep the best
        sorted_individuals = sorted(
            population.individuals, 
            key=lambda x: x.fitness, 
            reverse=True
        )
        
        trimmed = Population()
        for individual in sorted_individuals[:self.config.population_size]:
            trimmed.add_individual(individual)
        
        trimmed.generation = population.generation
        return trimmed
    
    def _calculate_generation_stats(self) -> EvolutionStats:
        """Calculate statistics for the current generation."""
        if self.current_population is None:
            raise ValueError("No current population")
        
        stats_dict = self.current_population.calculate_statistics()
        
        # Calculate convergence rate
        convergence_rate = 0.0
        if len(self.evolution_stats) > 0:
            prev_best = self.evolution_stats[-1].best_fitness
            current_best = stats_dict["best"]
            convergence_rate = abs(current_best - prev_best)
        
        return EvolutionStats(
            generation=self.generation,
            best_fitness=stats_dict["best"],
            average_fitness=stats_dict["average"],
            worst_fitness=stats_dict["worst"],
            diversity=stats_dict["diversity"],
            convergence_rate=convergence_rate,
            elapsed_time=0.0  # TODO: Add timing
        )
    
    def _check_convergence(self) -> bool:
        """Check if evolution has converged."""
        if self.current_population is None:
            return False
        
        # Check fitness threshold
        if self.current_population.best_fitness >= self.config.fitness_threshold:
            return True
        
        # Check for stagnation (no improvement over last N generations)
        stagnation_threshold = 50
        if len(self.evolution_stats) >= stagnation_threshold:
            recent_stats = self.evolution_stats[-stagnation_threshold:]
            if all(stats.convergence_rate < 0.001 for stats in recent_stats):
                return True
        
        return False
    
    async def _notify_observers_generation_start(self) -> None:
        """Notify observers of generation start."""
        for observer in self.observers:
            try:
                await observer.on_generation_start(
                    self.generation, self.current_population
                )
            except Exception as e:
                logger.error(f"Observer error in generation start: {e}")
    
    async def _notify_observers_generation_end(self) -> None:
        """Notify observers of generation end."""
        for observer in self.observers:
            try:
                await observer.on_generation_end(
                    self.generation, self.current_population
                )
            except Exception as e:
                logger.error(f"Observer error in generation end: {e}")
    
    async def _notify_observers_evolution_complete(self) -> None:
        """Notify observers of evolution completion."""
        for observer in self.observers:
            try:
                await observer.on_evolution_complete(self.current_population)
            except Exception as e:
                logger.error(f"Observer error in evolution complete: {e}")
    
    def get_best_individual(self) -> Optional[Individual]:
        """Get the best individual from the current population."""
        if self.current_population is None:
            return None
        return self.current_population.get_best_individual()
    
    def get_evolution_statistics(self) -> List[EvolutionStats]:
        """Get evolution statistics history."""
        return self.evolution_stats.copy()
    
    def stop_evolution(self) -> None:
        """Stop the evolution process."""
        self.is_running = False
        logger.info("Evolution stop requested")
    
    def set_dtesn_kernel(self, kernel) -> None:
        """Set DTESN kernel for integration."""
        self.dtesn_kernel = kernel
        logger.info("DTESN kernel integration enabled")
    
    def set_aar_orchestrator(self, orchestrator) -> None:
        """Set AAR orchestrator for integration."""
        self.aar_orchestrator = orchestrator
        logger.info("AAR orchestrator integration enabled")