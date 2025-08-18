"""
NanoCog CogPrime Training Configuration

This configuration file implements adaptive curriculum learning and neural-symbolic
synergy principles for training NanoCog models on CogPrime-aware datasets.
"""

import math
from typing import Dict, Any, Tuple, List

# === Base Model Configuration ===
# Model architecture (nanoGPT compatible)
n_layer = 8           # Number of transformer layers
n_head = 8            # Number of attention heads  
n_embd = 512          # Embedding dimension
dropout = 0.1         # Dropout rate
bias = True           # Use bias in linear layers
block_size = 1024     # Maximum sequence length

# === Training Configuration ===
# Basic training parameters
batch_size = 16                    # Training batch size
gradient_accumulation_steps = 4    # Gradient accumulation
learning_rate = 3e-4              # Base learning rate
max_iters = 20000                 # Maximum training iterations
warmup_iters = 2000               # Learning rate warmup iterations
lr_decay_iters = 20000            # Learning rate decay iterations
min_lr = 3e-5                     # Minimum learning rate

# Evaluation and logging
eval_interval = 500               # Evaluation frequency
eval_iters = 100                  # Number of evaluation iterations
log_interval = 100                # Logging frequency
always_save_checkpoint = True     # Save checkpoints regularly

# === Curriculum Learning Configuration ===
# Curriculum learning phases for cognitive complexity progression
CURRICULUM_PHASES = {
    'basic_atomese': {
        'name': 'Basic Atomese Syntax',
        'start_ratio': 0.0,
        'end_ratio': 0.25,
        'description': 'Simple atom construction and basic link types',
        'data_weight': 1.5,  # Increase sampling for basic patterns
        'learning_rate_multiplier': 1.0
    },
    'cognitive_primitives': {
        'name': 'Cognitive Primitives',
        'start_ratio': 0.20,
        'end_ratio': 0.50,
        'description': 'ECAN attention, goals, contexts, simple inference',
        'data_weight': 1.3,
        'learning_rate_multiplier': 0.9
    },
    'complex_schematics': {
        'name': 'Complex Cognitive Schematics',
        'start_ratio': 0.45,
        'end_ratio': 0.75,
        'description': 'Multi-step schematics, pattern mining, integration',
        'data_weight': 1.2,
        'learning_rate_multiplier': 0.8
    },
    'advanced_synergy': {
        'name': 'Advanced Neural-Symbolic Synergy',
        'start_ratio': 0.70,
        'end_ratio': 1.0,
        'description': 'PLN reasoning, MOSES integration, complex hypergraphs',
        'data_weight': 1.0,
        'learning_rate_multiplier': 0.7
    }
}

# === Adaptive Attention Allocation ===
# Dynamic data resampling configuration
ATTENTION_ALLOCATION = {
    'enable_adaptive_sampling': True,
    'performance_window': 1000,        # Iterations to track for performance
    'resample_threshold': 0.05,        # Performance drop threshold for resampling
    'boost_factor': 1.5,               # Factor to boost poorly performing patterns
    'context_window_adjustment': True,  # Enable dynamic context window tuning
    'min_context_window': 256,         # Minimum context window size
    'max_context_window': 1024,        # Maximum context window size
}

# === Recursive Self-Introspection ===
# Model self-evaluation configuration
SELF_INTROSPECTION = {
    'enable_self_evaluation': True,
    'evaluation_frequency': 2000,     # Iterations between self-evaluations
    'introspection_samples': 50,      # Number of samples for self-evaluation
    'feedback_integration': True,     # Use self-analysis to adjust training
    'synthetic_generation': True,     # Generate synthetic samples from weak areas
}

# === Hypergraph Pattern Integration ===
# Configuration for injecting structured cognitive patterns
HYPERGRAPH_PATTERNS = {
    'enable_pattern_injection': True,
    'injection_ratio': 0.15,          # Ratio of training data from synthetic patterns
    'pattern_complexity_scaling': True, # Scale pattern complexity with curriculum
    'cognitive_schematic_templates': [
        'context_procedure_goal',
        'attention_allocation',
        'inference_chain',
        'goal_hierarchy',
        'pattern_mining_result'
    ]
}

# === Evaluation Metrics Configuration ===
EVALUATION_METRICS = {
    'symbolic_accuracy': {
        'enable': True,
        'syntax_validation': True,      # Check Atomese syntax correctness
        'semantic_coherence': True,     # Assess logical consistency
        'target_accuracy': 0.95        # Target syntax accuracy
    },
    'diagnostic_alignment': {
        'enable': True,
        'bottleneck_detection': True,   # Test cognitive bottleneck detection
        'attention_pattern_recognition': True,
        'target_accuracy': 0.85        # Target diagnostic accuracy
    },
    'emergent_patterns': {
        'enable': True,
        'novelty_threshold': 0.7,      # Threshold for pattern novelty
        'target_novelty_rate': 0.10    # Target rate of novel pattern generation
    }
}

# === Functions for Dynamic Configuration ===

def get_curriculum_phase(iteration: int, max_iterations: int) -> Tuple[str, Dict[str, Any]]:
    """
    Determine the current curriculum learning phase based on training progress.
    
    Args:
        iteration: Current training iteration
        max_iterations: Maximum number of training iterations
    
    Returns:
        Tuple of (phase_name, phase_config)
    """
    progress_ratio = iteration / max_iterations
    
    for phase_name, phase_config in CURRICULUM_PHASES.items():
        if phase_config['start_ratio'] <= progress_ratio <= phase_config['end_ratio']:
            return phase_name, phase_config
    
    # Default to final phase if beyond all phases
    return 'advanced_synergy', CURRICULUM_PHASES['advanced_synergy']

def get_adaptive_learning_rate(iteration: int, max_iterations: int, base_lr: float) -> float:
    """
    Calculate adaptive learning rate based on curriculum phase and training progress.
    
    Args:
        iteration: Current training iteration
        max_iterations: Maximum training iterations
        base_lr: Base learning rate
    
    Returns:
        Adjusted learning rate
    """
    # Get current curriculum phase
    phase_name, phase_config = get_curriculum_phase(iteration, max_iterations)
    
    # Apply phase-specific learning rate multiplier
    phase_lr = base_lr * phase_config['learning_rate_multiplier']
    
    # Apply standard cosine decay within phase
    progress_ratio = iteration / max_iterations
    if iteration < warmup_iters:
        # Warmup phase
        lr = phase_lr * iteration / warmup_iters
    elif iteration > lr_decay_iters:
        # Minimum learning rate
        lr = min_lr
    else:
        # Cosine decay
        decay_ratio = (iteration - warmup_iters) / (lr_decay_iters - warmup_iters)
        lr = min_lr + (phase_lr - min_lr) * 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    
    return lr

def get_data_sampling_weights(iteration: int, max_iterations: int, 
                             performance_history: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Calculate dynamic data sampling weights based on curriculum phase and performance.
    
    Args:
        iteration: Current training iteration
        max_iterations: Maximum training iterations
        performance_history: Historical performance by pattern type
    
    Returns:
        Dictionary of sampling weights by pattern type
    """
    # Get current curriculum phase
    phase_name, phase_config = get_curriculum_phase(iteration, max_iterations)
    
    # Base weights from curriculum phase
    weights = {
        'basic_atomese': 1.0,
        'cognitive_primitives': 1.0,
        'complex_schematics': 1.0,
        'advanced_synergy': 1.0,
        'hypergraph_patterns': HYPERGRAPH_PATTERNS['injection_ratio']
    }
    
    # Apply curriculum phase emphasis
    current_emphasis = phase_name.replace('_', '_')
    if current_emphasis in weights:
        weights[current_emphasis] *= phase_config['data_weight']
    
    # Apply adaptive attention allocation
    if ATTENTION_ALLOCATION['enable_adaptive_sampling'] and performance_history:
        window_size = ATTENTION_ALLOCATION['performance_window']
        threshold = ATTENTION_ALLOCATION['resample_threshold']
        boost_factor = ATTENTION_ALLOCATION['boost_factor']
        
        for pattern_type, perf_history in performance_history.items():
            if len(perf_history) >= 2:
                recent_perf = sum(perf_history[-min(len(perf_history), window_size//10):])
                earlier_perf = sum(perf_history[-min(len(perf_history), window_size//5):-window_size//10])
                
                if recent_perf < earlier_perf - threshold:
                    # Performance dropped, boost this pattern type
                    if pattern_type in weights:
                        weights[pattern_type] *= boost_factor
    
    return weights

def get_context_window_size(iteration: int, max_iterations: int, 
                           pattern_complexity: str = "medium") -> int:
    """
    Determine dynamic context window size based on curriculum and complexity.
    
    Args:
        iteration: Current training iteration
        max_iterations: Maximum training iterations
        pattern_complexity: Current pattern complexity level
    
    Returns:
        Context window size
    """
    if not ATTENTION_ALLOCATION['context_window_adjustment']:
        return block_size
    
    # Get current curriculum phase
    phase_name, _ = get_curriculum_phase(iteration, max_iterations)
    
    # Base window size by phase
    phase_windows = {
        'basic_atomese': 256,
        'cognitive_primitives': 512,
        'complex_schematics': 768,
        'advanced_synergy': 1024
    }
    
    base_window = phase_windows.get(phase_name, 512)
    
    # Adjust for pattern complexity
    complexity_multipliers = {
        'simple': 0.75,
        'medium': 1.0,
        'complex': 1.25,
        'very_complex': 1.5
    }
    
    multiplier = complexity_multipliers.get(pattern_complexity, 1.0)
    adjusted_window = int(base_window * multiplier)
    
    # Clamp to configured limits
    min_window = ATTENTION_ALLOCATION['min_context_window']
    max_window = ATTENTION_ALLOCATION['max_context_window']
    
    return max(min_window, min(max_window, adjusted_window))

def should_trigger_self_introspection(iteration: int) -> bool:
    """
    Determine if self-introspection should be triggered at current iteration.
    
    Args:
        iteration: Current training iteration
    
    Returns:
        True if self-introspection should be performed
    """
    if not SELF_INTROSPECTION['enable_self_evaluation']:
        return False
    
    frequency = SELF_INTROSPECTION['evaluation_frequency']
    return iteration > 0 and iteration % frequency == 0

# === Export Configuration ===
# Configuration dictionary for easy access
CONFIG = {
    'model': {
        'n_layer': n_layer,
        'n_head': n_head,
        'n_embd': n_embd,
        'dropout': dropout,
        'bias': bias,
        'block_size': block_size
    },
    'training': {
        'batch_size': batch_size,
        'gradient_accumulation_steps': gradient_accumulation_steps,
        'learning_rate': learning_rate,
        'max_iters': max_iters,
        'warmup_iters': warmup_iters,
        'lr_decay_iters': lr_decay_iters,
        'min_lr': min_lr
    },
    'curriculum': CURRICULUM_PHASES,
    'attention_allocation': ATTENTION_ALLOCATION,
    'self_introspection': SELF_INTROSPECTION,
    'hypergraph_patterns': HYPERGRAPH_PATTERNS,
    'evaluation_metrics': EVALUATION_METRICS
}

# Output directory
out_dir = 'out-nanocog-cogprime'