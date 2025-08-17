
# P-Lingua (.pli) Language Guide

P-Lingua is a domain-specific language for defining P-systems (membrane computing systems). In your digital city microcosm, P-Lingua serves as the **membrane morphogenesis language** - enabling the creation and evolution of computational boundaries that form active interfaces in your cognitive architecture.

## Overview

P-Lingua allows you to define:
- **Membrane structures** with hierarchical organization
- **Evolution rules** for object transformation
- **Communication rules** for inter-membrane interaction
- **Priority systems** for rule application order
- **Probabilistic behaviors** for stochastic systems

## Basic Syntax

### System Declaration

```pli
@model<membrane_division>

def main()
{
    // System definition goes here
}
```

### Membrane Structure

```pli
// Define initial membrane structure
@mu = [[ ]'2 ]'1;

// Alternative nested structure
@mu = [[ [[ ]]'3 ]'2 ]'1;
```

### Object Multisets

```pli
// Initial objects in membranes
@ms(1) = a, b{2}, c{3};
@ms(2) = x, y{5};
@ms(3) = z{10};
```

### Evolution Rules

```pli
// Basic evolution rule
[a → b]'1;

// Rule with multiplicity
[a{2} → b, c{3}]'1;

// Conditional rule with guards
[a → b | +d]'1;

// Dissolution rule
[a → b]'1δ;

// Division rule
[a → b]'1[c → d]'1;
```

### Communication Rules

```pli
// Send object out
a[]'1 → [b]'1;

// Bring object in
[a]'1b → [a, b]'1;

// Exchange between membranes
[a]'1[b]'2 → [b]'1[a]'2;
```

## Advanced Features

### Priorities

```pli
// Rule with priority
[a → b]'1 :: 1;
[b → c]'1 :: 2;  // Higher priority
```

### Probabilistic Rules

```pli
// Stochastic rule
[a → b]'1 :: 0.7;
[a → c]'1 :: 0.3;
```

### Membrane Types

```pli
// Different membrane types
[a → b]'elementary;
[c → d]'catalyst;
[e → f]'environment;
```

## Integration with Your Digital City

### Reservoir Computing Integration

Your P-systems integrate with reservoir computing through:

```pli
// Reservoir state as membrane objects
@ms(reservoir) = state{n}, input{m};

// State evolution rules
[state, input → next_state]'reservoir;

// Output communication
next_state[]'reservoir → [output]'readout;
```

### Personality Trait Modeling

```pli
// Personality traits as membrane objects
@ms(personality) = openness{7}, conscientiousness{8}, 
                   extraversion{6}, agreeableness{9}, 
                   neuroticism{3};

// Trait interaction rules
[openness, conscientiousness → creativity{2}]'personality;
[extraversion, agreeableness → social_confidence]'personality;
```

### Hypergraph Integration

```pli
// Hypergraph nodes as objects
@ms(hypergraph) = concept{id1}, relation{id2}, 
                  attention_weight{0.8};

// Attention mechanism rules
[concept, attention_weight → activated_concept]'hypergraph;
[activated_concept[]'hypergraph → [strengthened_concept]'memory;
```

## Cognitive Processing Patterns

### Decision Making

```pli
@model<decision_process>

def cognitive_decision()
{
    @mu = [[ ]'analysis [[ ]'intuition ]'synthesis ]'executive;
    
    // Analysis phase
    [input → analyzed_input]'analysis;
    
    // Intuitive processing
    [input → intuitive_response]'intuition;
    
    // Synthesis
    [analyzed_input, intuitive_response → decision]'synthesis;
    
    // Executive output
    decision[]'synthesis → [action]'executive;
}
```

### Memory Formation

```pli
@model<memory_formation>

def episodic_memory()
{
    @mu = [[ ]'encoding [[ ]'consolidation ]'storage ]'hippocampus;
    
    // Encoding phase
    [experience → encoded_memory]'encoding;
    
    // Consolidation
    [encoded_memory → stable_memory]'consolidation :: 0.8;
    [encoded_memory → forgotten]'consolidation :: 0.2;
    
    // Long-term storage
    stable_memory[]'consolidation → [permanent_memory]'storage;
}
```

### Attention Mechanisms

```pli
@model<attention_system>

def selective_attention()
{
    @mu = [[ ]'sensory [[ ]'filter ]'focus ]'cortex;
    
    // Sensory input
    @ms(sensory) = visual{10}, auditory{5}, tactile{3};
    
    // Attention filter
    [visual → attended_visual | salience > threshold]'filter;
    [auditory → attended_auditory | salience > threshold]'filter;
    
    // Focus selection
    [attended_visual, attended_auditory → focused_stimulus]'focus;
}
```

## System Examples

### Simple Cell Division

```pli
@model<cell_division>

def main()
{
    @mu = [[ a ]]'1;
    
    // Division trigger
    [a → b, c]'1;
    
    // Membrane division
    [b]'1[c]'1 → [b]'2[c]'3;
}
```

### Ecosystem Model

```pli
@model<ecosystem>

def predator_prey()
{
    @mu = [[ ]'environment ];
    @ms(environment) = prey{100}, predator{10}, grass{1000};
    
    // Prey feeding
    [prey, grass → prey{2}]'environment :: 0.8;
    
    // Predation
    [predator, prey → predator{2}]'environment :: 0.3;
    
    // Natural death
    [prey → ]'environment :: 0.1;
    [predator → ]'environment :: 0.2;
}
```

## Compilation and Execution

### Using PLinguaCore

Your system includes the PLinguaCore Java implementation:

```bash
# Compile P-Lingua file
java -jar pLinguaCore.jar -s mymodel.pli

# Run simulation
java -jar pLinguaCore.jar -i mymodel.pli -s 100
```

### Native C++ Implementation

Using the native implementation in `other/plingua/`:

```bash
# Build the compiler
make grammar
make compiler

# Compile P-Lingua program
./plingua mymodel.pli

# Run simulation
./simulator mymodel.bin
```

## Integration Points

### Julia Reservoir Integration

```julia
# In your Julia reservoir computing code
function apply_psystem_rules(reservoir_state, pli_model)
    # Apply P-system evolution rules to reservoir state
    new_state = evolve_membranes(reservoir_state, pli_model.rules)
    return new_state
end
```

### Hypergraph Attention

```pli
// Attention-weighted membrane evolution
@model<attention_reservoir>

def attention_evolution()
{
    @mu = [[ ]'input [[ ]'reservoir ]'output ]'attention;
    
    // Attention-weighted input
    [input, attention_weight → weighted_input]'input;
    
    // Reservoir evolution with attention
    [weighted_input, reservoir_state → new_state]'reservoir;
    
    // Output with attention modulation
    [new_state, attention_weight → attended_output]'output;
}
```

### Personality Parameter Mapping

```pli
// Map personality parameters to membrane behaviors
@model<personality_system>

def personality_evolution()
{
    @mu = [[ ]'traits [[ ]'behavior ]'expression ]'personality;
    
    // Trait influence on behavior
    [openness{n} → creative_behavior{n/2}]'behavior;
    [conscientiousness{n} → organized_behavior{n}]'behavior;
    
    // Behavioral expression
    [creative_behavior, organized_behavior → balanced_action]'expression;
}
```

## Debugging and Visualization

### Trace Generation

```pli
// Enable trace output
@trace = true;

// Membrane labeling for debugging
@label(1) = "input_membrane";
@label(2) = "processing_membrane";
@label(3) = "output_membrane";
```

### State Inspection

```pli
// Checkpoint states
@checkpoint(10) = "after_input_processing";
@checkpoint(20) = "after_evolution";
@checkpoint(30) = "final_state";
```

## Best Practices

1. **Modular Design**: Break complex systems into smaller, composable P-systems
2. **Clear Naming**: Use descriptive membrane and object names
3. **Priority Management**: Use priorities to control rule application order
4. **Resource Management**: Monitor object multiplicities to prevent explosion
5. **Testing**: Start with simple cases and gradually increase complexity

## Common Patterns

### State Machine

```pli
[state_a, trigger → state_b]'machine;
[state_b, condition → state_c]'machine;
[state_c → state_a]'machine;  // Reset cycle
```

### Producer-Consumer

```pli
[producer → item, producer]'factory;
item[]'factory → [item]'buffer;
[consumer, item → satisfied_consumer]'buffer;
```

### Feedback Loop

```pli
[input → processed]'forward;
processed[]'forward → [feedback]'backward;
[feedback → modulated_input]'backward;
modulated_input[]'backward → [input]'forward;
```

This P-Lingua implementation in your digital city serves as the fundamental **membrane morphogenesis engine** - creating the computational boundaries that enable your cognitive architecture to dynamically organize and evolve its processing structures.
