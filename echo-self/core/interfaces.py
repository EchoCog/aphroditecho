"""
Core interfaces and protocols for Echo-Self AI Evolution Engine.

Defines the fundamental contracts for evolutionary algorithms and self-optimizing systems.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator
from dataclasses import dataclass
import uuid


@dataclass
class EvolutionConfig:
    """Configuration parameters for the evolution engine."""
    population_size: int = 100
    mutation_rate: float = 0.01
    crossover_rate: float = 0.7
    selection_pressure: float = 0.8
    elitism_ratio: float = 0.1
    max_generations: int = 1000
    fitness_threshold: float = 0.95
    tournament_size: int = 3
    diversity_threshold: float = 0.1


class Individual(ABC):
    """Abstract base class for evolvable individuals."""
    
    def __init__(self, genome: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.genome = genome
        self.fitness: float = 0.0
        self.age: int = 0
        self.generation: int = 0
        self.parent_ids: List[str] = []
        self.performance_history: List[float] = []
    
    @abstractmethod
    async def evaluate_fitness(self, evaluator: 'FitnessEvaluator') -> float:
        """Evaluate individual fitness using the provided evaluator."""
        pass
    
    @abstractmethod
    def mutate(self, mutation_rate: float) -> 'Individual':
        """Apply mutations to create a new individual."""
        pass
    
    @abstractmethod
    def crossover(self, other: 'Individual') -> Tuple['Individual', 'Individual']:
        """Perform crossover with another individual to produce offspring."""
        pass
    
    @abstractmethod
    def distance(self, other: 'Individual') -> float:
        """Calculate genetic distance from another individual."""
        pass
    
    def clone(self) -> 'Individual':
        """Create an exact copy of this individual."""
        clone = self.__class__(self.genome.copy())
        clone.fitness = self.fitness
        clone.age = self.age
        clone.generation = self.generation
        clone.parent_ids = self.parent_ids.copy()
        clone.performance_history = self.performance_history.copy()
        return clone


class Population:
    """Container for a population of individuals."""
    
    def __init__(self, individuals: List[Individual] = None):
        self.individuals: List[Individual] = individuals or []
        self.generation: int = 0
        self.best_fitness: float = 0.0
        self.average_fitness: float = 0.0
        self.diversity: float = 0.0
    
    def add_individual(self, individual: Individual) -> None:
        """Add an individual to the population."""
        self.individuals.append(individual)
    
    def remove_individual(self, individual: Individual) -> None:
        """Remove an individual from the population."""
        if individual in self.individuals:
            self.individuals.remove(individual)
    
    def size(self) -> int:
        """Return the population size."""
        return len(self.individuals)
    
    def get_best_individual(self) -> Optional[Individual]:
        """Return the individual with highest fitness."""
        if not self.individuals:
            return None
        return max(self.individuals, key=lambda x: x.fitness)
    
    def get_worst_individual(self) -> Optional[Individual]:
        """Return the individual with lowest fitness."""
        if not self.individuals:
            return None
        return min(self.individuals, key=lambda x: x.fitness)
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate population statistics."""
        if not self.individuals:
            return {"best": 0.0, "worst": 0.0, "average": 0.0, "diversity": 0.0}
        
        fitnesses = [ind.fitness for ind in self.individuals]
        self.best_fitness = max(fitnesses)
        worst_fitness = min(fitnesses)
        self.average_fitness = sum(fitnesses) / len(fitnesses)
        
        # Calculate diversity as average pairwise distance
        if len(self.individuals) > 1:
            distances = []
            for i, ind1 in enumerate(self.individuals):
                for ind2 in self.individuals[i+1:]:
                    distances.append(ind1.distance(ind2))
            self.diversity = sum(distances) / len(distances) if distances else 0.0
        else:
            self.diversity = 0.0
        
        return {
            "best": self.best_fitness,
            "worst": worst_fitness,
            "average": self.average_fitness,
            "diversity": self.diversity
        }


class FitnessEvaluator(ABC):
    """Abstract base class for fitness evaluation."""
    
    @abstractmethod
    async def evaluate(self, individual: Individual) -> float:
        """Evaluate the fitness of an individual."""
        pass
    
    @abstractmethod
    async def batch_evaluate(self, individuals: List[Individual]) -> List[float]:
        """Evaluate fitness for a batch of individuals (for optimization)."""
        pass


class EvolutionObserver(ABC):
    """Observer interface for monitoring evolution progress."""
    
    @abstractmethod
    async def on_generation_start(self, generation: int, population: Population) -> None:
        """Called at the start of each generation."""
        pass
    
    @abstractmethod
    async def on_generation_end(self, generation: int, population: Population) -> None:
        """Called at the end of each generation."""
        pass
    
    @abstractmethod
    async def on_evolution_complete(self, final_population: Population) -> None:
        """Called when evolution is complete."""
        pass


class EvolutionaryOperator(ABC):
    """Base class for evolutionary operators."""
    
    @abstractmethod
    def apply(self, population: Population, config: EvolutionConfig) -> Population:
        """Apply the evolutionary operator to a population."""
        pass