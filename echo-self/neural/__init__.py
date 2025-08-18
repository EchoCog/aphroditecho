"""Neural network components for Echo-Self Evolution Engine."""

try:
    from .topology_individual import NeuralTopologyIndividual
except ImportError:
    from topology_individual import NeuralTopologyIndividual

__all__ = ["NeuralTopologyIndividual"]