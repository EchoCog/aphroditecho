# Neural-Symbolic Integration in Deep Tree Echo

## Overview

The Deep Tree Echo cognitive architecture now includes neural-symbolic integration capabilities through the Cognitive Grammar Bridge. This bridge connects the comprehensive Scheme-based cognitive grammar kernel with the Python-based cognitive architecture, enabling hybrid reasoning that combines neural and symbolic approaches.

## Architecture Components

### 1. Cognitive Grammar Kernel (Scheme)
- **File**: `cognitive_grammar_kernel.scm`
- **Lines**: 379 comprehensive symbolic reasoning functions
- **Capabilities**:
  - Hypergraph memory operations (remember, recall, forget)
  - Echo propagation system
  - Reasoning primitives (infer, deduce, abduce)
  - Meta-cognitive operations (reflect, introspect, adapt)
  - Neural-symbolic conversion functions
  - Learning operations (generalize, specialize)

### 2. Cognitive Grammar Bridge (Python)
- **File**: `cognitive_grammar_bridge.py`
- **Purpose**: Python-Scheme integration layer
- **Key Classes**:
  - `CognitiveGrammarBridge`: Main integration class
  - `SymbolicExpression`: Represents symbolic expressions with activation levels
  - `NeuralPattern`: Represents neural activation patterns

### 3. Enhanced Cognitive Architecture
- **File**: `cognitive_architecture.py` (updated)
- **Integration**: Added neural-symbolic methods to CognitiveArchitecture class
- **New Capabilities**: 
  - Symbolic memory operations
  - Neural-symbolic conversions
  - Hybrid reasoning
  - Meta-cognitive reflection

## Usage Examples

### Basic Neural-Symbolic Operations

```python
from cognitive_architecture import CognitiveArchitecture

# Initialize cognitive architecture with neural-symbolic capabilities
arch = CognitiveArchitecture()

# Check if cognitive grammar is available
if arch.has_cognitive_grammar():
    # Store concepts using symbolic reasoning
    node_id = arch.symbolic_remember("recursive cognition", "meta-learning context")
    
    # Retrieve concepts using pattern matching
    matches = arch.symbolic_recall("cognition")
    
    # Convert neural activations to symbolic representations
    activations = [0.8, 0.6, 0.3, 0.9, 0.2]
    symbols = ["memory", "reasoning", "learning", "adaptation", "reflection"]
    symbolic_expr = arch.neural_to_symbolic_conversion(activations, symbols)
    
    # Convert symbolic expressions back to neural patterns
    neural_pattern = arch.symbolic_to_neural_conversion(symbolic_expr, neural_network_size=100)
    
    # Perform hybrid neural-symbolic reasoning
    result = arch.hybrid_reasoning("How can I improve my learning efficiency?")
    
    # Meta-cognitive reflection
    reflection = arch.meta_cognitive_reflection("problem-solving", depth=3)
```

### Direct Bridge Usage

```python
from cognitive_grammar_bridge import CognitiveGrammarBridge, SymbolicExpression

# Initialize bridge directly
bridge = CognitiveGrammarBridge()
bridge.initialize()

# Core memory operations
concept_id = bridge.remember("distributed cognition", "collaborative intelligence")
related_concepts = bridge.recall("cognition")

# Echo operations for activation propagation
echo_id = bridge.echo_create("learning insight", 
                           emotional_state={"valence": 0.8, "arousal": 0.6},
                           spatial_context={"domain": "cognitive_science"})
bridge.echo_propagate(echo_id, activation_threshold=0.5)

# Meta-cognitive operations
reflection = bridge.reflect("strategy_adaptation", depth=2)
current_state = {"focus": 0.8, "energy": 0.6}
introspection = bridge.introspect(current_state, granularity="high")
```

## Neural-Symbolic Conversion

### Neural → Symbolic
Converts neural activation patterns to symbolic representations:

- **Input**: List of activation values + symbol space
- **Process**: Threshold-based symbol selection and activation mapping
- **Output**: SymbolicExpression with symbols and activation levels

### Symbolic → Neural
Converts symbolic expressions to neural activation patterns:

- **Input**: SymbolicExpression + target network size
- **Process**: Symbol-to-activation mapping and pattern generation
- **Output**: NeuralPattern with activation vector

## Integration Points

### 1. Memory Systems
- **Traditional Memory**: Stores structured data (Memory objects)
- **Symbolic Memory**: Stores concepts in hypergraph with contextual links
- **Hybrid Access**: Both systems can be queried and cross-referenced

### 2. Reasoning Capabilities
- **Deductive**: Traditional logical reasoning
- **Inductive**: Pattern-based learning from examples
- **Abductive**: Best explanation finding
- **Meta-cognitive**: Reasoning about reasoning processes

### 3. Learning Integration
- **Experience Processing**: Convert experiences to both neural patterns and symbolic representations
- **Pattern Recognition**: Use both statistical and symbolic pattern matching
- **Generalization**: Create abstract concepts that bridge neural and symbolic domains

## Error Handling

The system gracefully handles missing dependencies and components:

- **Missing Scheme Interpreter**: Falls back to simulation mode
- **Bridge Unavailable**: Cognitive architecture continues without neural-symbolic features
- **Conversion Errors**: Return sensible defaults with error metadata

## Testing

Comprehensive test coverage includes:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component interaction testing
- **Error Handling Tests**: Graceful degradation testing
- **Performance Tests**: Conversion efficiency testing

### Running Tests

```bash
# Test the cognitive grammar bridge
python -m unittest test_cognitive_grammar_bridge -v

# Test cognitive architecture integration
python -m unittest test_cognitive_architecture -v
```

## Future Enhancements

### 1. Real Scheme Integration
- Replace simulation with actual Scheme interpreter
- Support for full Scheme evaluation
- Dynamic code generation and execution

### 2. Advanced Neural-Symbolic Operations
- Differentiable programming integration
- Gradient-based symbol learning
- Attention-based symbol grounding

### 3. Distributed Cognition
- Multi-agent neural-symbolic interaction
- Distributed memory and reasoning
- Collective intelligence emergence

## Architecture Benefits

### 1. **Unified Reasoning**: Combines the best of neural (pattern recognition, learning) and symbolic (logical reasoning, explanation) approaches

### 2. **Explainable AI**: Symbolic representations provide clear explanations for neural decisions

### 3. **Transfer Learning**: Symbolic abstractions enable knowledge transfer across domains

### 4. **Meta-Learning**: Symbolic reflection on neural learning processes enables meta-cognitive capabilities

### 5. **Robust Integration**: Graceful degradation ensures system stability even with component failures

This neural-symbolic integration represents a significant step toward unified artificial general intelligence, combining the pattern recognition power of neural networks with the logical reasoning capabilities of symbolic systems.