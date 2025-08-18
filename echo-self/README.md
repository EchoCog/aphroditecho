# Echo-Self AI Evolution Engine

A self-optimizing AI system that evolves neural network topologies and architectures using genetic algorithms, integrated with the Deep Tree Echo System Network (DTESN).

## Features

- **Core Evolution Engine**: Implements genetic algorithms for neural architecture search
- **Neural Topology Evolution**: Evolves complete network structures including layers, connections, and parameters  
- **DTESN Integration**: Bridges with existing Deep Tree Echo components for membrane computing
- **Aphrodite Engine Integration**: Leverages high-performance model serving infrastructure
- **Modular Architecture**: Extensible design with pluggable operators and evaluators

## Quick Start

### Basic Usage

```python
import asyncio
from echo_self.core import EvolutionConfig, EchoSelfEvolutionEngine
from echo_self.neural import NeuralTopologyIndividual
from echo_self.integration import AphroditeFitnessEvaluator

# Configure evolution parameters
config = EvolutionConfig(
    population_size=20,
    max_generations=50,
    mutation_rate=0.1,
    crossover_rate=0.7
)

# Create fitness evaluator
fitness_evaluator = AphroditeFitnessEvaluator()

# Initialize evolution engine
engine = EchoSelfEvolutionEngine(
    config=config,
    fitness_evaluator=fitness_evaluator,
    individual_class=NeuralTopologyIndividual
)

# Create genome factory
def create_network_genome():
    return {
        'layers': [
            {'type': 'dense', 'size': 64},
            {'type': 'attention', 'size': 128, 'heads': 4},
            {'type': 'dense', 'size': 32}
        ],
        'connections': [
            {'from': 0, 'to': 1, 'type': 'direct'},
            {'from': 1, 'to': 2, 'type': 'direct'}
        ],
        'activation_functions': {'0': 'relu', '1': 'swish', '2': 'sigmoid'},
        'parameters': {'learning_rate': 0.001, 'batch_size': 32}
    }

async def evolve_networks():
    # Initialize population
    await engine.initialize_population(create_network_genome)
    
    # Run evolution
    final_population = await engine.evolve()
    
    # Get best individual
    best_network = final_population.get_best_individual()
    print(f"Best fitness: {best_network.fitness:.4f}")
    print(f"Network summary: {best_network.get_network_summary()}")

# Run evolution
asyncio.run(evolve_networks())
```

### Running the Example

```bash
cd echo-self
python example_usage.py
```

### Running Tests

```bash
cd echo-self/tests
python test_evolution_engine.py
```

## Architecture

### Core Components

#### Evolution Engine (`core/evolution_engine.py`)
- **EchoSelfEvolutionEngine**: Main orchestrator for evolutionary processes
- **EvolutionConfig**: Configuration parameters for evolution
- **EvolutionStats**: Statistics tracking and reporting

#### Interfaces (`core/interfaces.py`)
- **Individual**: Base class for evolvable entities
- **Population**: Container for groups of individuals
- **FitnessEvaluator**: Interface for fitness evaluation
- **EvolutionObserver**: Monitoring and logging interface

#### Operators (`core/operators.py`)
- **MutationOperator**: Genetic mutation implementation
- **SelectionOperator**: Selection strategies (tournament, roulette, rank)
- **CrossoverOperator**: Genetic recombination
- **ElitismOperator**: Elite preservation
- **DiversityOperator**: Diversity maintenance

### Neural Components

#### Topology Individual (`neural/topology_individual.py`)
- **NeuralTopologyIndividual**: Evolvable neural network representation
- Supports layer evolution (add, remove, modify, split, merge)
- Connection topology evolution
- Parameter optimization
- Activation function evolution

### Integration Components

#### DTESN Bridge (`integration/dtesn_bridge.py`)
- Connects with echo.kern components
- P-System membrane processing
- ESN reservoir dynamics
- B-Series differential calculations

#### Aphrodite Bridge (`integration/aphrodite_bridge.py`)
- High-performance model serving integration
- Distributed computing support
- Performance-based fitness evaluation
- Deployment optimization

## Evolutionary Operators

### Mutation Types

1. **Layer Mutations**:
   - Add new layers
   - Remove existing layers
   - Modify layer parameters
   - Split layers into smaller components
   - Merge adjacent layers

2. **Connection Mutations**:
   - Add skip connections
   - Remove connections
   - Modify connection weights
   - Change connection types

3. **Parameter Mutations**:
   - Learning rate optimization
   - Batch size adjustment
   - Optimizer selection
   - Regularization tuning

### Selection Strategies

- **Tournament Selection**: Compete individuals in small groups
- **Roulette Selection**: Fitness-proportional selection
- **Rank Selection**: Rank-based probability assignment

### Crossover Methods

- **Uniform Crossover**: Random selection from both parents
- **Single-point Crossover**: Split and recombine at random point
- **Multi-point Crossover**: Multiple split points

## Configuration Options

### EvolutionConfig Parameters

```python
config = EvolutionConfig(
    population_size=100,        # Number of individuals per generation
    mutation_rate=0.01,         # Probability of mutation
    crossover_rate=0.7,         # Probability of crossover
    selection_pressure=0.8,     # Selection intensity
    elitism_ratio=0.1,          # Fraction of elite individuals preserved
    max_generations=1000,       # Maximum evolution generations
    fitness_threshold=0.95,     # Early stopping threshold
    tournament_size=3,          # Tournament selection size
    diversity_threshold=0.1     # Minimum diversity maintenance
)
```

## Integration with DTESN

The Echo-Self engine integrates with existing DTESN components:

```python
from echo_self.integration import DTESNBridge

# Initialize DTESN bridge
dtesn_bridge = DTESNBridge()
if dtesn_bridge.initialize():
    # Process individuals through DTESN
    dtesn_results = dtesn_bridge.process_individual_through_dtesn(individual)
    
    # Update individual with DTESN feedback
    updated_individual = dtesn_bridge.update_individual_with_dtesn_feedback(
        individual, dtesn_results
    )
```

## Integration with Aphrodite Engine

For high-performance model serving:

```python
from echo_self.integration import AphroditeBridge

# Initialize Aphrodite bridge
aphrodite_bridge = AphroditeBridge()
if aphrodite_bridge.initialize("meta-llama/Llama-2-7b-hf"):
    # Evaluate performance
    performance = aphrodite_bridge.evaluate_individual_performance(individual)
    
    # Optimize for deployment
    optimized_config = aphrodite_bridge.optimize_for_deployment(individual)
```

## Acceptance Criteria Validation

The system meets the Phase 1.1.1 acceptance criteria:

✅ **Engine can evolve simple neural network topologies**
- Supports layer structure evolution
- Implements connection topology modification  
- Optimizes network parameters
- Maintains population diversity
- Demonstrates fitness improvement over generations

## Development Guidelines

### Adding New Operators

```python
from echo_self.core.interfaces import EvolutionaryOperator

class CustomOperator(EvolutionaryOperator):
    def apply(self, population, config):
        # Implement custom evolutionary logic
        return modified_population
```

### Custom Fitness Evaluators  

```python
from echo_self.core.interfaces import FitnessEvaluator

class CustomFitnessEvaluator(FitnessEvaluator):
    async def evaluate(self, individual):
        # Implement fitness calculation
        return fitness_score
    
    async def batch_evaluate(self, individuals):
        return [await self.evaluate(ind) for ind in individuals]
```

### Custom Individual Types

```python
from echo_self.core.interfaces import Individual

class CustomIndividual(Individual):
    def mutate(self, mutation_rate):
        # Implement mutation logic
        return mutated_individual
    
    def crossover(self, other):
        # Implement crossover logic  
        return child1, child2
    
    def distance(self, other):
        # Implement distance calculation
        return genetic_distance
```

## Testing

The module includes comprehensive tests:

- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end evolution process
- **Performance Tests**: Fitness evaluation and optimization
- **DTESN Integration Tests**: Bridge functionality validation

## Logging and Monitoring

Configure logging for detailed evolution tracking:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('echo-self')
```

## Performance Considerations

- Use batch evaluation for better performance
- Configure appropriate population sizes for available compute
- Enable DTESN integration for enhanced evaluation
- Use Aphrodite bridge for production-scale fitness evaluation

## License

This module is part of the Aphrodite Echo system and follows the same licensing terms.

## Contributing

See the main project [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## References

- [Deep Tree Echo Development Roadmap](../DEEP_TREE_ECHO_ROADMAP.md)
- [Deep Tree Echo Architecture](../DEEP_TREE_ECHO_ARCHITECTURE.md)
- [Echo.Kern Development](../echo.kern/DEVELOPMENT.md)