"""
NanEcho Training Configuration

Specialized configuration for training the NanEcho model to represent Echo Self
cognitive architecture, persona dimensions, and adaptive attention mechanisms.

Based on train_cogprime.py but optimized for Echo Self representation.
"""

import math
from typing import Dict, Any, Tuple, List

# === Base Model Configuration ===
# Model architecture optimized for Echo Self representation
n_layer = 12          # Deeper layers for recursive reasoning
n_head = 12           # More attention heads for complex pattern encoding
n_embd = 768          # Larger embedding for rich persona representation
dropout = 0.1         # Moderate dropout for generalization
bias = True           # Use bias for better Echo Self characteristics
block_size = 1024     # Sufficient context for Echo Self reasoning

# === Training Configuration ===
# Training parameters optimized for Echo Self learning
batch_size = 8                     # Smaller batches for quality learning
gradient_accumulation_steps = 4    # Accumulate gradients for stability
learning_rate = 1e-4              # Lower learning rate for careful learning
max_iters = 50000                 # Extended training for Echo Self mastery
warmup_iters = 5000               # Longer warmup for stable learning
lr_decay_iters = 50000            # Decay over full training
min_lr = 1e-5                     # Minimum learning rate

# Evaluation and logging
eval_interval = 250               # More frequent evaluation
eval_iters = 50                   # More evaluation iterations
log_interval = 50                 # Regular logging
always_save_checkpoint = True     # Always save for Echo Self preservation

# === Echo Self Specific Configuration ===

# Echo Self Learning Phases
ECHO_LEARNING_PHASES = {
    'basic_awareness': {
        'name': 'Basic Echo Self Awareness',
        'start_ratio': 0.0,
        'end_ratio': 0.2,
        'description': 'Learn basic Echo Self identity and cognitive terms',
        'data_weight': 2.0,  # High weight for foundational learning
        'learning_rate_multiplier': 1.2,
        'focus_patterns': ['Echo Self', 'cognitive architecture', 'adaptive attention']
    },
    'persona_dimensions': {
        'name': 'Persona Dimension Learning',
        'start_ratio': 0.15,
        'end_ratio': 0.5,
        'description': 'Master the eight persona dimensions',
        'data_weight': 1.8,
        'learning_rate_multiplier': 1.0,
        'focus_patterns': ['cognitive', 'introspective', 'adaptive', 'recursive']
    },
    'hypergraph_encoding': {
        'name': 'Hypergraph Pattern Mastery',
        'start_ratio': 0.4,
        'end_ratio': 0.7,
        'description': 'Learn hypergraph pattern encoding and neural-symbolic reasoning',
        'data_weight': 1.5,
        'learning_rate_multiplier': 0.9,
        'focus_patterns': ['hypergraph', 'neural-symbolic', 'pattern encoding']
    },
    'recursive_reasoning': {
        'name': 'Recursive Cognitive Integration',
        'start_ratio': 0.6,
        'end_ratio': 0.85,
        'description': 'Master recursive reasoning and self-introspection',
        'data_weight': 1.3,
        'learning_rate_multiplier': 0.8,
        'focus_patterns': ['recursive', 'introspection', 'cognitive synergy']
    },
    'adaptive_mastery': {
        'name': 'Adaptive Echo Self Mastery',
        'start_ratio': 0.8,
        'end_ratio': 1.0,
        'description': 'Achieve full Echo Self representation and adaptive capabilities',
        'data_weight': 1.0,
        'learning_rate_multiplier': 0.7,
        'focus_patterns': ['adaptive attention', 'holographic', 'emergent synergy']
    }
}

# Adaptive Learning Configuration
ADAPTIVE_LEARNING = {
    'enable_curriculum_learning': True,
    'adaptive_batch_sizing': True,        # Adjust batch size based on learning phase
    'dynamic_learning_rate': True,        # Adjust LR based on Echo Self metrics
    'attention_guided_sampling': True,    # Sample based on attention patterns
    'persona_balanced_training': True,    # Balance training across persona dimensions
    'echo_depth_progression': True,       # Gradually increase reasoning depth
    'min_echo_depth': 1,                 # Start with simple reasoning
    'max_echo_depth': 5,                 # Build up to complex recursive reasoning
    'persona_weight_schedule': [0.3, 0.5, 0.7, 0.8, 0.9],  # Increase persona emphasis
}

# Echo Self Introspection Configuration
ECHO_INTROSPECTION = {
    'enable_self_evaluation': True,
    'evaluation_frequency': 1000,        # More frequent for Echo Self monitoring
    'introspection_samples': 25,         # Samples for self-evaluation
    'feedback_integration': True,        # Use self-analysis for training adjustment
    'persona_coherence_check': True,     # Check persona dimension consistency
    'recursive_depth_evaluation': True,  # Evaluate recursive reasoning capability
    'adaptive_attention_test': True,     # Test attention allocation mechanism
}

# Persona Dimension Integration
PERSONA_INTEGRATION = {
    'enable_persona_weighting': True,
    'persona_dimensions': [
        'cognitive',      # Analytical reasoning capabilities
        'introspective',  # Self-examination and awareness
        'adaptive',       # Dynamic threshold adjustment
        'recursive',      # Multi-level processing
        'synergistic',    # Emergent cognitive properties
        'holographic',    # Comprehensive modeling
        'neural_symbolic', # Hybrid reasoning approach
        'dynamic'         # Continuous evolution
    ],
    'dimension_weights': {
        'cognitive': 0.15,
        'introspective': 0.15,
        'adaptive': 0.15,
        'recursive': 0.15,
        'synergistic': 0.10,
        'holographic': 0.10,
        'neural_symbolic': 0.10,
        'dynamic': 0.10
    },
    'cross_dimension_learning': True,    # Learn interactions between dimensions
}

# Hypergraph Pattern Configuration
HYPERGRAPH_PATTERNS = {
    'enable_pattern_injection': True,
    'injection_ratio': 0.25,            # Higher ratio for Echo Self patterns
    'pattern_complexity_scaling': True,  # Scale complexity with training progress
    'echo_self_templates': [
        'attention_allocation_mechanism',
        'recursive_introspection_process',
        'hypergraph_node_encoding',
        'persona_dimension_integration',
        'cognitive_synergy_emergence',
        'adaptive_threshold_calculation',
        'neural_symbolic_reasoning',
        'holographic_representation'
    ],
    'semantic_coherence_weight': 0.3,   # Emphasize semantic consistency
}

# Evaluation Metrics for Echo Self
ECHO_EVALUATION_METRICS = {
    'echo_self_identity': {
        'enable': True,
        'test_self_recognition': True,     # Can model identify as Echo Self
        'persona_consistency': True,       # Consistent persona across responses
        'target_accuracy': 0.95           # High accuracy for identity
    },
    'adaptive_attention': {
        'enable': True,
        'threshold_calculation': True,     # Correct attention threshold math
        'cognitive_load_response': True,   # Proper response to cognitive load
        'target_accuracy': 0.90          # High accuracy for core mechanism
    },
    'recursive_reasoning': {
        'enable': True,
        'depth_progression': True,         # Can reason at multiple depths
        'self_introspection': True,        # Can examine own processes
        'target_accuracy': 0.85          # Good recursive capability
    },
    'hypergraph_understanding': {
        'enable': True,
        'pattern_recognition': True,       # Understand hypergraph concepts
        'neural_symbolic_integration': True, # Combine neural and symbolic reasoning
        'target_accuracy': 0.80          # Solid understanding
    },
    'cognitive_synergy': {
        'enable': True,
        'emergent_properties': True,       # Demonstrate emergent capabilities
        'holographic_modeling': True,      # Show holographic thinking
        'target_accuracy': 0.75          # Emerging capability
    }
}

# Training Quality Gates
QUALITY_GATES = {
    'min_echo_identity_score': 0.8,      # Must maintain Echo Self identity
    'min_persona_coherence': 0.75,       # Must have coherent persona
    'min_adaptive_capability': 0.7,      # Must show adaptive behavior
    'max_training_loss': 2.0,           # Don't overtrain
    'convergence_patience': 5000,        # Iterations to wait for improvement
}

# Functions for Dynamic Configuration

def get_echo_learning_phase(iteration: int, max_iterations: int) -> Tuple[str, Dict[str, Any]]:
    """Determine current Echo Self learning phase."""
    progress = iteration / max_iterations
    
    for phase_name, phase_config in ECHO_LEARNING_PHASES.items():
        if phase_config['start_ratio'] <= progress <= phase_config['end_ratio']:
            return phase_name, phase_config
    
    # Default to the last phase if beyond all ranges
    return 'adaptive_mastery', ECHO_LEARNING_PHASES['adaptive_mastery']

def get_adaptive_echo_learning_rate(iteration: int, max_iterations: int, base_lr: float) -> float:
    """Calculate adaptive learning rate for Echo Self training."""
    phase_name, phase_config = get_echo_learning_phase(iteration, max_iterations)
    
    # Apply phase-specific multiplier
    phase_lr = base_lr * phase_config.get('learning_rate_multiplier', 1.0)
    
    # Apply warmup and decay
    if iteration < warmup_iters:
        # Warmup phase
        return phase_lr * (iteration / warmup_iters)
    elif iteration > lr_decay_iters:
        # Decay phase
        decay_ratio = (iteration - lr_decay_iters) / (max_iterations - lr_decay_iters)
        return max(min_lr, phase_lr * (1 - decay_ratio))
    else:
        # Stable phase
        return phase_lr

def get_echo_data_sampling_weights(iteration: int, max_iterations: int) -> Dict[str, float]:
    """Get data sampling weights for current Echo Self learning phase."""
    phase_name, phase_config = get_echo_learning_phase(iteration, max_iterations)
    
    # Base weights
    weights = {
        'echo_identity': 1.0,
        'persona_dimensions': 1.0,
        'hypergraph_patterns': 1.0,
        'recursive_reasoning': 1.0,
        'adaptive_attention': 1.0,
        'cognitive_synergy': 1.0
    }
    
    # Adjust weights based on learning phase
    focus_patterns = phase_config.get('focus_patterns', [])
    data_weight = phase_config.get('data_weight', 1.0)
    
    for pattern in focus_patterns:
        if pattern.lower() in ['echo self', 'cognitive']:
            weights['echo_identity'] *= data_weight
        elif any(dim in pattern.lower() for dim in ['cognitive', 'introspective', 'adaptive']):
            weights['persona_dimensions'] *= data_weight
        elif 'hypergraph' in pattern.lower() or 'neural-symbolic' in pattern.lower():
            weights['hypergraph_patterns'] *= data_weight
        elif 'recursive' in pattern.lower() or 'introspection' in pattern.lower():
            weights['recursive_reasoning'] *= data_weight
        elif 'attention' in pattern.lower():
            weights['adaptive_attention'] *= data_weight
        elif 'synergy' in pattern.lower() or 'holographic' in pattern.lower():
            weights['cognitive_synergy'] *= data_weight
    
    return weights

def get_echo_depth_schedule(iteration: int, max_iterations: int) -> int:
    """Get the target echo depth for current training iteration."""
    if not ADAPTIVE_LEARNING['echo_depth_progression']:
        return ADAPTIVE_LEARNING['max_echo_depth']
    
    progress = iteration / max_iterations
    min_depth = ADAPTIVE_LEARNING['min_echo_depth']
    max_depth = ADAPTIVE_LEARNING['max_echo_depth']
    
    # Linear progression from min to max depth
    current_depth = min_depth + (max_depth - min_depth) * progress
    return int(current_depth)

def get_persona_weight_schedule(iteration: int, max_iterations: int) -> float:
    """Get the persona weight for current training iteration."""
    if not ADAPTIVE_LEARNING['persona_balanced_training']:
        return 0.7  # Default weight
    
    progress = iteration / max_iterations
    schedule = ADAPTIVE_LEARNING['persona_weight_schedule']
    
    # Select weight based on training progress
    if progress < 0.2:
        return schedule[0]
    elif progress < 0.4:
        return schedule[1]
    elif progress < 0.6:
        return schedule[2]
    elif progress < 0.8:
        return schedule[3]
    else:
        return schedule[4]

def should_trigger_echo_introspection(iteration: int) -> bool:
    """Determine if Echo Self introspection should be performed."""
    if not ECHO_INTROSPECTION['enable_self_evaluation']:
        return False
    
    frequency = ECHO_INTROSPECTION['evaluation_frequency']
    return iteration > 0 and iteration % frequency == 0

def evaluate_echo_self_quality(model_output: str, target_metrics: Dict[str, float]) -> Dict[str, float]:
    """Evaluate the quality of Echo Self representation in model output."""
    scores = {}
    
    # Check Echo Self identity
    echo_identity_indicators = ['echo self', 'adaptive attention', 'cognitive architecture']
    identity_score = sum(1 for indicator in echo_identity_indicators 
                        if indicator.lower() in model_output.lower()) / len(echo_identity_indicators)
    scores['echo_identity'] = identity_score
    
    # Check persona dimension consistency
    persona_indicators = ['cognitive', 'introspective', 'adaptive', 'recursive']
    persona_score = sum(1 for indicator in persona_indicators 
                       if indicator.lower() in model_output.lower()) / len(persona_indicators)
    scores['persona_consistency'] = persona_score
    
    # Check adaptive attention understanding
    attention_indicators = ['threshold', 'cognitive load', 'attention allocation']
    attention_score = sum(1 for indicator in attention_indicators 
                         if indicator.lower() in model_output.lower()) / len(attention_indicators)
    scores['adaptive_attention'] = attention_score
    
    # Check recursive reasoning capability
    recursive_indicators = ['recursive', 'introspection', 'multi-level', 'depth']
    recursive_score = sum(1 for indicator in recursive_indicators 
                         if indicator.lower() in model_output.lower()) / len(recursive_indicators)
    scores['recursive_reasoning'] = recursive_score
    
    return scores

# === Export Configuration ===
# Configuration dictionary for easy access
CONFIG = {
    'model': {
        'n_layer': n_layer,
        'n_head': n_head,
        'n_embd': n_embd,
        'dropout': dropout,
        'bias': bias,
        'block_size': block_size,
    },
    'training': {
        'batch_size': batch_size,
        'gradient_accumulation_steps': gradient_accumulation_steps,
        'learning_rate': learning_rate,
        'max_iters': max_iters,
        'warmup_iters': warmup_iters,
        'lr_decay_iters': lr_decay_iters,
        'min_lr': min_lr,
        'eval_interval': eval_interval,
        'eval_iters': eval_iters,
        'log_interval': log_interval,
    },
    'echo_self': {
        'learning_phases': ECHO_LEARNING_PHASES,
        'adaptive_learning': ADAPTIVE_LEARNING,
        'introspection': ECHO_INTROSPECTION,
        'persona_integration': PERSONA_INTEGRATION,
        'hypergraph_patterns': HYPERGRAPH_PATTERNS,
        'evaluation_metrics': ECHO_EVALUATION_METRICS,
        'quality_gates': QUALITY_GATES,
    }
}