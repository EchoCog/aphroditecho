"""Core module for Echo-Self AI Evolution Engine."""

# Handle both absolute and relative imports
try:
    from .interfaces import (
        Individual, Population, FitnessEvaluator, EvolutionConfig, 
        EvolutionObserver, EvolutionaryOperator
    )
    from .operators import (
        MutationOperator, SelectionOperator, CrossoverOperator,
        ElitismOperator, DiversityOperator
    )
    from .evolution_engine import EchoSelfEvolutionEngine, EvolutionStats
except ImportError:
    from interfaces import (
        Individual, Population, FitnessEvaluator, EvolutionConfig, 
        EvolutionObserver, EvolutionaryOperator
    )
    from operators import (
        MutationOperator, SelectionOperator, CrossoverOperator,
        ElitismOperator, DiversityOperator
    )
    from evolution_engine import EchoSelfEvolutionEngine, EvolutionStats

__all__ = [
    "Individual", "Population", "FitnessEvaluator", "EvolutionConfig",
    "EvolutionObserver", "EvolutionaryOperator",
    "MutationOperator", "SelectionOperator", "CrossoverOperator",
    "ElitismOperator", "DiversityOperator",
    "EchoSelfEvolutionEngine", "EvolutionStats"
]