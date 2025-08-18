"""
Echo-Self AI Evolution Engine

A self-optimizing AI system that evolves neural network topologies and architectures
using genetic algorithms integrated with the Deep Tree Echo System Network (DTESN).

This module provides:
- Core evolution interfaces and protocols
- Basic evolutionary operators (mutation, selection, crossover)  
- Neural network topology evolution capabilities
- Integration with DTESN and Aphrodite Engine
"""

__version__ = "1.0.0"
__author__ = "Echo-Self Evolution Team"

# Handle imports gracefully to support both package and direct usage
try:
    from .core.evolution_engine import EchoSelfEvolutionEngine
    from .core.interfaces import Individual, Population, FitnessEvaluator
    from .core.operators import MutationOperator, SelectionOperator, CrossoverOperator
    from .neural.topology_individual import NeuralTopologyIndividual
    from .integration.dtesn_bridge import DTESNBridge
    from .integration.aphrodite_bridge import AphroditeBridge
except ImportError:
    # Fallback for direct execution
    from core.evolution_engine import EchoSelfEvolutionEngine
    from core.interfaces import Individual, Population, FitnessEvaluator
    from core.operators import MutationOperator, SelectionOperator, CrossoverOperator
    from neural.topology_individual import NeuralTopologyIndividual
    from integration.dtesn_bridge import DTESNBridge
    from integration.aphrodite_bridge import AphroditeBridge

__all__ = [
    "EchoSelfEvolutionEngine",
    "Individual", 
    "Population",
    "FitnessEvaluator",
    "MutationOperator",
    "SelectionOperator", 
    "CrossoverOperator",
    "NeuralTopologyIndividual",
    "DTESNBridge",
    "AphroditeBridge"
]