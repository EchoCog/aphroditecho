"""
Meta-Learning System for Echo-Self AI Evolution

Provides meta-learning algorithms for architecture optimization, 
experience replay mechanisms, and DTESN integration.
"""

from .meta_optimizer import (
    MetaLearningOptimizer,
    MetaLearningConfig,
    ExperienceReplay,
    ArchitecturePerformance
)

from .dtesn_bridge import (
    DTESNMetaLearningBridge,
    DTESNPerformanceMetrics
)

__all__ = [
    'MetaLearningOptimizer',
    'MetaLearningConfig', 
    'ExperienceReplay',
    'ArchitecturePerformance',
    'DTESNMetaLearningBridge',
    'DTESNPerformanceMetrics'
]