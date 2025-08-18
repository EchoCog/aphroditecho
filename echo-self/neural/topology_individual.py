"""
Neural Network Topology Individual for evolutionary algorithms.

Implements an individual that represents and evolves neural network topologies,
enabling the Echo-Self system to optimize network architectures.
"""

import random
from typing import Dict, Any, Tuple
from copy import deepcopy

# Import interfaces - handle both absolute and relative imports
try:
    from core.interfaces import Individual, FitnessEvaluator
except ImportError:
    from ..core.interfaces import Individual, FitnessEvaluator


class NeuralTopologyIndividual(Individual):
    """Individual representing an evolvable neural network topology."""
    
    def __init__(self, genome: Dict[str, Any]):
        super().__init__(genome)
        self.network_structure = self._initialize_network_structure()
    
    def _initialize_network_structure(self) -> Dict[str, Any]:
        """Initialize the neural network structure from genome."""
        return {
            "layers": self.genome.get("layers", []),
            "connections": self.genome.get("connections", []),
            "activation_functions": self.genome.get("activation_functions", {}),
            "parameters": self.genome.get("parameters", {}),
            "metadata": self.genome.get("metadata", {})
        }
    
    async def evaluate_fitness(self, evaluator: FitnessEvaluator) -> float:
        """Evaluate fitness of this neural topology."""
        return await evaluator.evaluate(self)
    
    def mutate(self, mutation_rate: float) -> 'NeuralTopologyIndividual':
        """Apply mutations to create a new topology individual."""
        mutated_genome = deepcopy(self.genome)
        
        # Apply different types of mutations based on probability
        if random.random() < mutation_rate:
            mutated_genome = self._mutate_layers(mutated_genome, mutation_rate)
        
        if random.random() < mutation_rate:
            mutated_genome = self._mutate_connections(
                mutated_genome, mutation_rate
            )
        
        if random.random() < mutation_rate:
            mutated_genome = self._mutate_activations(
                mutated_genome, mutation_rate
            )
        
        if random.random() < mutation_rate:
            mutated_genome = self._mutate_parameters(
                mutated_genome, mutation_rate
            )
        
        # Create new individual
        mutated = NeuralTopologyIndividual(mutated_genome)
        mutated.parent_ids = [self.id]
        
        return mutated
    
    def _mutate_layers(
        self, genome: Dict[str, Any], mutation_rate: float
    ) -> Dict[str, Any]:
        """Mutate layer structure."""
        layers = genome.get("layers", []).copy()
        
        # Mutation types for layers
        mutation_type = random.choice(
            ["add", "remove", "modify", "split", "merge"]
        )
        
        if mutation_type == "add" and len(layers) < 20:  # Max layers limit
            # Add a new layer
            layer_types = ["dense", "conv1d", "lstm", "attention", "dropout"]
            new_layer = {
                "type": random.choice(layer_types),
                "size": random.randint(8, 512),
                "position": random.randint(0, len(layers))
            }
            
            if new_layer["type"] == "conv1d":
                new_layer["kernel_size"] = random.randint(3, 7)
                new_layer["stride"] = random.randint(1, 3)
            elif new_layer["type"] == "dropout":
                new_layer["rate"] = random.uniform(0.1, 0.5)
            elif new_layer["type"] == "attention":
                new_layer["heads"] = random.choice([1, 2, 4, 8])
            
            layers.insert(new_layer["position"], new_layer)
        
        elif mutation_type == "remove" and len(layers) > 1:
            # Remove a random layer (but keep at least one)
            layers.pop(random.randint(0, len(layers) - 1))
        
        elif mutation_type == "modify" and layers:
            # Modify an existing layer
            layer_idx = random.randint(0, len(layers) - 1)
            layer = layers[layer_idx]
            
            if layer["type"] in ["dense", "conv1d", "lstm"]:
                # Modify size
                current_size = layer.get("size", 64)
                size_change = random.randint(
                    -current_size // 4, current_size // 4
                )
                layer["size"] = max(8, current_size + size_change)
            
            if layer["type"] == "conv1d":
                # Modify kernel size
                layer["kernel_size"] = random.randint(3, 9)
        
        elif mutation_type == "split" and layers:
            # Split a layer into two smaller layers
            layer_idx = random.randint(0, len(layers) - 1)
            original_layer = layers[layer_idx]
            
            if original_layer.get("size", 0) > 16:
                size1 = original_layer["size"] // 2
                size2 = original_layer["size"] - size1
                
                layer1 = original_layer.copy()
                layer1["size"] = size1
                
                layer2 = original_layer.copy()
                layer2["size"] = size2
                
                layers[layer_idx] = layer1
                layers.insert(layer_idx + 1, layer2)
        
        elif mutation_type == "merge" and len(layers) > 1:
            # Merge two adjacent layers
            layer_idx = random.randint(0, len(layers) - 2)
            layer1 = layers[layer_idx]
            layer2 = layers[layer_idx + 1]
            
            if layer1["type"] == layer2["type"]:
                merged_layer = layer1.copy()
                merged_layer["size"] = (
                    layer1.get("size", 64) + layer2.get("size", 64)
                )
                layers[layer_idx] = merged_layer
                layers.pop(layer_idx + 1)
        
        genome["layers"] = layers
        return genome
    
    def _mutate_connections(
        self, genome: Dict[str, Any], mutation_rate: float
    ) -> Dict[str, Any]:
        """Mutate connection structure."""
        connections = genome.get("connections", []).copy()
        layers = genome.get("layers", [])
        
        if len(layers) < 2:
            return genome
        
        # Add or remove connections
        if random.random() < 0.5:
            # Add a new connection
            source = random.randint(0, len(layers) - 2)
            target = random.randint(source + 1, len(layers) - 1)
            
            connection = {
                "from": source,
                "to": target,
                "weight": random.uniform(-1.0, 1.0),
                "type": random.choice(["direct", "skip", "residual"])
            }
            
            # Avoid duplicate connections
            existing = [(c["from"], c["to"]) for c in connections]
            if (source, target) not in existing:
                connections.append(connection)
        
        elif connections:
            # Remove a random connection
            connections.pop(random.randint(0, len(connections) - 1))
        
        genome["connections"] = connections
        return genome
    
    def _mutate_activations(
        self, genome: Dict[str, Any], mutation_rate: float
    ) -> Dict[str, Any]:
        """Mutate activation functions."""
        activations = genome.get("activation_functions", {}).copy()
        layers = genome.get("layers", [])
        
        activation_choices = [
            "relu", "tanh", "sigmoid", "leaky_relu", "elu", "swish", "gelu"
        ]
        
        for i, layer in enumerate(layers):
            if random.random() < mutation_rate:
                activations[str(i)] = random.choice(activation_choices)
        
        genome["activation_functions"] = activations
        return genome
    
    def _mutate_parameters(
        self, genome: Dict[str, Any], mutation_rate: float
    ) -> Dict[str, Any]:
        """Mutate network parameters."""
        params = genome.get("parameters", {}).copy()
        
        # Learning rate
        if random.random() < mutation_rate:
            current_lr = params.get("learning_rate", 0.001)
            lr_factor = random.uniform(0.5, 2.0)
            params["learning_rate"] = max(
                1e-6, min(1.0, current_lr * lr_factor)
            )
        
        # Batch size
        if random.random() < mutation_rate:
            batch_sizes = [16, 32, 64, 128, 256]
            params["batch_size"] = random.choice(batch_sizes)
        
        # Optimization parameters
        if random.random() < mutation_rate:
            params["optimizer"] = random.choice(
                ["adam", "sgd", "rmsprop", "adamw"]
            )
        
        # Regularization
        if random.random() < mutation_rate:
            params["l2_reg"] = random.uniform(1e-6, 1e-3)
        
        genome["parameters"] = params
        return genome
    
    def crossover(
        self, other: 'NeuralTopologyIndividual'
    ) -> Tuple['NeuralTopologyIndividual', 'NeuralTopologyIndividual']:
        """Perform crossover with another neural topology individual."""
        child1_genome = deepcopy(self.genome)
        child2_genome = deepcopy(other.genome)
        
        # Layer crossover
        child1_genome, child2_genome = self._crossover_layers(
            child1_genome, child2_genome, other.genome
        )
        
        # Connection crossover
        child1_genome, child2_genome = self._crossover_connections(
            child1_genome, child2_genome, other.genome
        )
        
        # Parameter crossover
        child1_genome, child2_genome = self._crossover_parameters(
            child1_genome, child2_genome, other.genome
        )
        
        child1 = NeuralTopologyIndividual(child1_genome)
        child2 = NeuralTopologyIndividual(child2_genome)
        
        return child1, child2
    
    def _crossover_layers(
        self, genome1: Dict, genome2: Dict, other_genome: Dict
    ) -> Tuple[Dict, Dict]:
        """Perform crossover on layer structures."""
        layers1 = genome1.get("layers", [])
        layers2 = other_genome.get("layers", [])
        
        if not layers1 or not layers2:
            return genome1, genome2
        
        # Single-point crossover for layers
        crossover_point = random.randint(1, min(len(layers1), len(layers2)))
        
        new_layers1 = layers1[:crossover_point] + layers2[crossover_point:]
        new_layers2 = layers2[:crossover_point] + layers1[crossover_point:]
        
        genome1["layers"] = new_layers1
        genome2["layers"] = new_layers2
        
        return genome1, genome2
    
    def _crossover_connections(
        self, genome1: Dict, genome2: Dict, other_genome: Dict
    ) -> Tuple[Dict, Dict]:
        """Perform crossover on connection structures."""
        connections1 = genome1.get("connections", [])
        connections2 = other_genome.get("connections", [])
        
        # Uniform crossover for connections
        new_connections1 = []
        new_connections2 = []
        
        all_connections = set()
        for conn in connections1 + connections2:
            all_connections.add((conn["from"], conn["to"]))
        
        for from_idx, to_idx in all_connections:
            if random.random() < 0.5:
                # Find connection in first parent
                for conn in connections1:
                    if conn["from"] == from_idx and conn["to"] == to_idx:
                        new_connections1.append(conn)
                        break
            else:
                # Find connection in second parent
                for conn in connections2:
                    if conn["from"] == from_idx and conn["to"] == to_idx:
                        new_connections2.append(conn)
                        break
        
        genome1["connections"] = new_connections1
        genome2["connections"] = new_connections2
        
        return genome1, genome2
    
    def _crossover_parameters(
        self, genome1: Dict, genome2: Dict, other_genome: Dict
    ) -> Tuple[Dict, Dict]:
        """Perform crossover on parameters."""
        params1 = genome1.get("parameters", {})
        params2 = other_genome.get("parameters", {})
        
        # Uniform crossover for parameters
        all_param_keys = set(params1.keys()) | set(params2.keys())
        
        new_params1 = {}
        new_params2 = {}
        
        for key in all_param_keys:
            if random.random() < 0.5:
                if key in params1:
                    new_params1[key] = params1[key]
                if key in params2:
                    new_params2[key] = params2[key]
            else:
                if key in params2:
                    new_params1[key] = params2[key]
                if key in params1:
                    new_params2[key] = params1[key]
        
        genome1["parameters"] = new_params1
        genome2["parameters"] = new_params2
        
        return genome1, genome2
    
    def distance(self, other: 'NeuralTopologyIndividual') -> float:
        """Calculate genetic distance from another neural topology."""
        if not isinstance(other, NeuralTopologyIndividual):
            return float('inf')
        
        # Layer structure distance
        layer_distance = self._layer_distance(other)
        
        # Connection distance
        connection_distance = self._connection_distance(other)
        
        # Parameter distance
        parameter_distance = self._parameter_distance(other)
        
        # Weighted combination
        total_distance = (
            0.4 * layer_distance + 
            0.3 * connection_distance + 
            0.3 * parameter_distance
        )
        
        return total_distance
    
    def _layer_distance(self, other: 'NeuralTopologyIndividual') -> float:
        """Calculate distance between layer structures."""
        layers1 = self.genome.get("layers", [])
        layers2 = other.genome.get("layers", [])
        
        # Simple distance based on layer count and sizes
        size_diff = abs(len(layers1) - len(layers2))
        
        common_layers = min(len(layers1), len(layers2))
        size_sum_diff = 0
        
        for i in range(common_layers):
            size1 = layers1[i].get("size", 0)
            size2 = layers2[i].get("size", 0)
            size_sum_diff += abs(size1 - size2)
        
        return (
            (size_diff + size_sum_diff / 100.0) / 
            max(1, max(len(layers1), len(layers2)))
        )
    
    def _connection_distance(self, other: 'NeuralTopologyIndividual') -> float:
        """Calculate distance between connection structures."""
        connections1 = set(
            (c["from"], c["to"]) for c in self.genome.get("connections", [])
        )
        connections2 = set(
            (c["from"], c["to"]) for c in other.genome.get("connections", [])
        )
        
        union_size = len(connections1 | connections2)
        if union_size == 0:
            return 0.0
        
        intersection_size = len(connections1 & connections2)
        return 1.0 - (intersection_size / union_size)
    
    def _parameter_distance(self, other: 'NeuralTopologyIndividual') -> float:
        """Calculate distance between parameters."""
        params1 = self.genome.get("parameters", {})
        params2 = other.genome.get("parameters", {})
        
        all_keys = set(params1.keys()) | set(params2.keys())
        if not all_keys:
            return 0.0
        
        distance_sum = 0.0
        for key in all_keys:
            val1 = params1.get(key, 0)
            val2 = params2.get(key, 0)
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                distance_sum += abs(val1 - val2) / max(
                    abs(val1), abs(val2), 1.0
                )
            elif val1 != val2:
                distance_sum += 1.0
        
        return distance_sum / len(all_keys)
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Get a summary of the network topology."""
        layers = self.genome.get("layers", [])
        connections = self.genome.get("connections", [])
        
        total_params = sum(layer.get("size", 0) for layer in layers)
        layer_types = [layer.get("type", "unknown") for layer in layers]
        
        return {
            "num_layers": len(layers),
            "layer_types": layer_types,
            "total_parameters": total_params,
            "num_connections": len(connections),
            "fitness": self.fitness,
            "generation": self.generation
        }