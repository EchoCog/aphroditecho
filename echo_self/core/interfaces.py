"""
Core interfaces for Echo-Self Evolution Engine.
Defines abstract base classes for individuals and fitness evaluators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


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
    
    def crossover(self, other: 'Individual') -> Tuple['Individual', 'Individual']:
        """Create offspring through crossover with another individual."""
        # Basic crossover implementation - to be overridden in subclasses
        child1_genome = {}
        child2_genome = {}
        
        for key in self.genome:
            if key in other.genome:
                # Simple crossover: randomly choose parent for each gene
                import random
                if random.random() < 0.5:
                    child1_genome[key] = self.genome[key]
                    child2_genome[key] = other.genome[key]
                else:
                    child1_genome[key] = other.genome[key]
                    child2_genome[key] = self.genome[key]
            else:
                child1_genome[key] = self.genome[key]
        
        # Add genes that only exist in other
        for key in other.genome:
            if key not in self.genome:
                child2_genome[key] = other.genome[key]
        
        # Create new individuals of same type
        child1 = self.__class__(child1_genome)
        child2 = self.__class__(child2_genome)
        
        return child1, child2


class FitnessEvaluator(ABC):
    """Base class for fitness evaluation strategies."""
    
    @abstractmethod
    async def evaluate(self, individual: Individual, environment: Dict) -> float:
        """Evaluate fitness of individual in given environment."""
        pass
    
    @abstractmethod
    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """Get criteria used for fitness evaluation."""
        pass


class SimpleIndividual(Individual):
    """Simple implementation of Individual for basic testing."""
    
    async def evaluate_fitness(self, environment) -> float:
        """Simple fitness evaluation based on genome values."""
        if not self.genome:
            return 0.0
        
        # Simple fitness: sum of genome values
        fitness = 0.0
        for key, value in self.genome.items():
            if isinstance(value, (int, float)):
                fitness += abs(value)
        
        self.fitness = fitness
        return fitness
    
    def mutate(self, mutation_rate: float) -> 'Individual':
        """Apply random mutations to genome."""
        import random
        import copy
        
        new_genome = copy.deepcopy(self.genome)
        
        for key, value in new_genome.items():
            if random.random() < mutation_rate:
                if isinstance(value, float):
                    new_genome[key] = value + random.gauss(0, 0.1)
                elif isinstance(value, int):
                    new_genome[key] = max(1, value + random.randint(-1, 1))
                elif isinstance(value, str):
                    # Simple string mutation: add random character
                    new_genome[key] = value + random.choice('abcdefghijklmnopqrstuvwxyz')
        
        mutated_individual = SimpleIndividual(new_genome)
        mutated_individual.age = self.age + 1
        return mutated_individual


class SimpleFitnessEvaluator(FitnessEvaluator):
    """Simple fitness evaluator for testing."""
    
    async def evaluate(self, individual: Individual, environment: Dict) -> float:
        """Evaluate based on individual's evaluate_fitness method."""
        return await individual.evaluate_fitness(environment)
    
    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """Get evaluation criteria."""
        return {
            'type': 'simple',
            'description': 'Basic fitness evaluation using individual method'
        }