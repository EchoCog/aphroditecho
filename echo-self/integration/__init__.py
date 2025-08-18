"""Integration components for Echo-Self Evolution Engine."""

from .dtesn_bridge import DTESNBridge
from .aphrodite_bridge import AphroditeBridge, AphroditeFitnessEvaluator

__all__ = ["DTESNBridge", "AphroditeBridge", "AphroditeFitnessEvaluator"]