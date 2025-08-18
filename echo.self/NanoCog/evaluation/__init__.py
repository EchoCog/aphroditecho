"""
NanoCog Evaluation Module

This module provides comprehensive evaluation capabilities for NanoCog models,
including symbolic accuracy assessment, emergent pattern detection, diagnostic
alignment verification, and automated evaluation loops.
"""

from .metrics import NanoCogEvaluator
from .automated_loop import AutomatedEvaluationLoop

__all__ = [
    'NanoCogEvaluator',
    'AutomatedEvaluationLoop'
]

__version__ = '1.0.0'