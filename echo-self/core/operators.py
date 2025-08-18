"""
Basic evolutionary operators for Echo-Self AI Evolution Engine.

Implements fundamental genetic algorithm operations: mutation, selection, and crossover.
"""

import random

# Handle both absolute and relative imports
try:
    from core.interfaces import Individual, Population, EvolutionConfig, EvolutionaryOperator
except ImportError:
    from .interfaces import Population, EvolutionConfig, EvolutionaryOperator


class MutationOperator(EvolutionaryOperator):
    """Applies mutations to individuals in the population."""
    
    def apply(self, population: Population, config: EvolutionConfig) -> Population:
        """Apply mutations to individuals based on mutation rate."""
        mutated_population = Population()
        
        for individual in population.individuals:
            if random.random() < config.mutation_rate:
                mutated_individual = individual.mutate(config.mutation_rate)
                mutated_individual.generation = population.generation + 1
                mutated_population.add_individual(mutated_individual)
            else:
                # Keep individual unchanged but update generation
                clone = individual.clone()
                clone.generation = population.generation + 1
                mutated_population.add_individual(clone)
        
        mutated_population.generation = population.generation + 1
        return mutated_population


class SelectionOperator(EvolutionaryOperator):
    """Implements various selection strategies for evolutionary algorithms."""
    
    def __init__(self, strategy: str = "tournament"):
        self.strategy = strategy
    
    def apply(self, population: Population, config: EvolutionConfig) -> Population:
        """Apply selection to create next generation."""
        if self.strategy == "tournament":
            return self._tournament_selection(population, config)
        elif self.strategy == "roulette":
            return self._roulette_selection(population, config)
        elif self.strategy == "rank":
            return self._rank_selection(population, config)
        else:
            raise ValueError(f"Unknown selection strategy: {self.strategy}")
    
    def _tournament_selection(self, population: Population, config: EvolutionConfig) -> Population:
        """Tournament selection implementation."""
        selected = Population()
        
        for _ in range(config.population_size):
            # Select tournament participants
            tournament = random.choices(
                population.individuals, 
                k=min(config.tournament_size, len(population.individuals))
            )
            
            # Select winner (highest fitness)
            winner = max(tournament, key=lambda x: x.fitness)
            selected.add_individual(winner.clone())
        
        selected.generation = population.generation
        return selected
    
    def _roulette_selection(self, population: Population, config: EvolutionConfig) -> Population:
        """Fitness-proportional selection (roulette wheel)."""
        selected = Population()
        
        # Calculate selection probabilities
        fitnesses = [max(0.001, ind.fitness) for ind in population.individuals]  # Avoid zero fitness
        total_fitness = sum(fitnesses)
        probabilities = [f / total_fitness for f in fitnesses]
        
        for _ in range(config.population_size):
            chosen = random.choices(population.individuals, weights=probabilities, k=1)[0]
            selected.add_individual(chosen.clone())
        
        selected.generation = population.generation
        return selected
    
    def _rank_selection(self, population: Population, config: EvolutionConfig) -> Population:
        """Rank-based selection."""
        selected = Population()
        
        # Sort by fitness and assign ranks
        sorted_individuals = sorted(population.individuals, key=lambda x: x.fitness)
        ranks = list(range(1, len(sorted_individuals) + 1))
        
        for _ in range(config.population_size):
            chosen = random.choices(sorted_individuals, weights=ranks, k=1)[0]
            selected.add_individual(chosen.clone())
        
        selected.generation = population.generation
        return selected


class CrossoverOperator(EvolutionaryOperator):
    """Implements crossover operations for genetic recombination."""
    
    def __init__(self, strategy: str = "uniform"):
        self.strategy = strategy
    
    def apply(self, population: Population, config: EvolutionConfig) -> Population:
        """Apply crossover to create offspring."""
        offspring_population = Population()
        individuals = population.individuals.copy()
        random.shuffle(individuals)  # Randomize pairing
        
        # Process pairs for crossover
        for i in range(0, len(individuals) - 1, 2):
            parent1 = individuals[i]
            parent2 = individuals[i + 1]
            
            if random.random() < config.crossover_rate:
                # Perform crossover
                child1, child2 = parent1.crossover(parent2)
                
                # Set generation and parent information
                child1.generation = population.generation + 1
                child1.parent_ids = [parent1.id, parent2.id]
                child2.generation = population.generation + 1
                child2.parent_ids = [parent1.id, parent2.id]
                
                offspring_population.add_individual(child1)
                offspring_population.add_individual(child2)
            else:
                # Keep parents as offspring
                clone1 = parent1.clone()
                clone2 = parent2.clone()
                clone1.generation = population.generation + 1
                clone2.generation = population.generation + 1
                
                offspring_population.add_individual(clone1)
                offspring_population.add_individual(clone2)
        
        # Handle odd number of individuals
        if len(individuals) % 2 == 1:
            clone = individuals[-1].clone()
            clone.generation = population.generation + 1
            offspring_population.add_individual(clone)
        
        # Trim to target population size if necessary
        if offspring_population.size() > config.population_size:
            # Keep the best individuals
            offspring_population.individuals.sort(key=lambda x: x.fitness, reverse=True)
            offspring_population.individuals = offspring_population.individuals[:config.population_size]
        
        offspring_population.generation = population.generation + 1
        return offspring_population


class ElitismOperator(EvolutionaryOperator):
    """Ensures the best individuals survive to the next generation."""
    
    def apply(self, population: Population, config: EvolutionConfig) -> Population:
        """Apply elitism to preserve best individuals."""
        elite_count = max(1, int(config.population_size * config.elitism_ratio))
        
        # Sort by fitness (descending)
        sorted_individuals = sorted(
            population.individuals, 
            key=lambda x: x.fitness, 
            reverse=True
        )
        
        # Create elite population
        elite_population = Population()
        for individual in sorted_individuals[:elite_count]:
            clone = individual.clone()
            clone.generation = population.generation + 1
            elite_population.add_individual(clone)
        
        elite_population.generation = population.generation + 1
        return elite_population


class DiversityOperator(EvolutionaryOperator):
    """Maintains genetic diversity in the population."""
    
    def __init__(self, diversity_threshold: float = 0.1):
        self.diversity_threshold = diversity_threshold
    
    def apply(self, population: Population, config: EvolutionConfig) -> Population:
        """Apply diversity maintenance to prevent premature convergence."""
        if population.size() < 2:
            return population
        
        # Calculate current diversity
        stats = population.calculate_statistics()
        current_diversity = stats.get("diversity", 0.0)
        
        if current_diversity < self.diversity_threshold:
            return self._increase_diversity(population, config)
        
        return population
    
    def _increase_diversity(self, population: Population, config: EvolutionConfig) -> Population:
        """Increase population diversity by introducing variations."""
        diverse_population = Population()
        
        # Keep some of the best individuals
        sorted_individuals = sorted(population.individuals, key=lambda x: x.fitness, reverse=True)
        keep_count = max(1, int(len(sorted_individuals) * 0.3))
        
        for individual in sorted_individuals[:keep_count]:
            diverse_population.add_individual(individual.clone())
        
        # Add mutated versions of good individuals
        while diverse_population.size() < config.population_size:
            source = random.choice(sorted_individuals[:keep_count * 2])
            # Apply higher mutation rate for diversity
            mutated = source.mutate(config.mutation_rate * 3)
            mutated.generation = population.generation + 1
            diverse_population.add_individual(mutated)
        
        diverse_population.generation = population.generation + 1
        return diverse_population