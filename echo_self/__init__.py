"""
Echo-Self AI Evolution Engine

Main module for self-optimizing artificial intelligence systems.
Integrates with Aphrodite Engine and DTESN kernel for advanced AI evolution.
"""

__version__ = "0.1.0"
__author__ = "EchoCog Deep Tree Echo Team"

from .core.evolution_engine import EchoSelfEvolutionEngine
# from .meta_learning.meta_learner import MetaLearner  # Placeholder
# from .adaptive_architecture.topology_mutator import TopologyMutator

__all__ = [
    'EchoSelfEvolutionEngine',
    # 'MetaLearner', 
    # 'TopologyMutator'
]

# Integration status
INTEGRATION_STATUS = {
    'aphrodite_engine': False,
    'dtesn_kernel': False,
    'aar_orchestrator': False
}

def get_integration_status():
    """Get current integration status with other components."""
    return INTEGRATION_STATUS.copy()

def enable_integration(component: str, enabled: bool = True):
    """Enable/disable integration with specified component."""
    if component in INTEGRATION_STATUS:
        INTEGRATION_STATUS[component] = enabled
        return True
    return False