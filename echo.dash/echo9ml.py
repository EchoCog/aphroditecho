"""
Echo9ml: Deep Tree Echo Persona Evolution System

Implementation of the cognitive flowchart for encoding "Deep Tree Echo" persona 
evolution within a ggml-inspired framework. This module provides:

1. Persona Kernel Construction (Scheme-inspired)
2. Tensor-based persona encoding with prime factorization
3. Hypergraph persona encoding for traits and memories
4. Attention allocation layer (ECAN-inspired)
5. Evolution mechanism with recursive application
6. Meta-cognitive enhancement for self-monitoring

Based on the architectural specification in echo9ml.md
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import time
import json
import logging
from collections import deque, defaultdict
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class PersonaTraitType(Enum):
    """Core persona trait types following Deep Tree Echo metaphor"""
    ROOTS = "memory"        # Memory foundations
    BRANCHES = "reasoning"  # Reasoning capabilities  
    LEAVES = "expression"   # Expression and communication
    TRUNK = "stability"     # Core identity stability
    GROWTH = "adaptation"   # Learning and evolution
    CANOPY = "creativity"   # Creative expression
    NETWORK = "social"      # Social connections

@dataclass
class PersonaKernel:
    """
    Scheme-inspired persona kernel following the make-persona-kernel pattern
    from echo9ml.md specification
    """
    name: str
    traits: Dict[PersonaTraitType, float]
    history: List[Dict[str, Any]]
    evolution: Dict[str, Any]
    
    # Hypergraph connections
    trait_connections: Dict[PersonaTraitType, Set[PersonaTraitType]] = field(default_factory=dict)
    
    # Temporal tracking
    creation_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    
    @classmethod
    def create_deep_tree_echo(cls) -> 'PersonaKernel':
        """Create the default Deep Tree Echo persona kernel"""
        traits = {
            PersonaTraitType.ROOTS: 0.85,      # Strong memory foundation
            PersonaTraitType.BRANCHES: 0.90,   # Excellent reasoning
            PersonaTraitType.LEAVES: 0.80,     # Good expression
            PersonaTraitType.TRUNK: 0.75,      # Stable core
            PersonaTraitType.GROWTH: 0.95,     # High adaptability
            PersonaTraitType.CANOPY: 0.88,     # Strong creativity
            PersonaTraitType.NETWORK: 0.70     # Moderate social
        }
        
        # Define trait connections (hypergraph edges)
        connections = {
            PersonaTraitType.ROOTS: {PersonaTraitType.BRANCHES, PersonaTraitType.TRUNK},
            PersonaTraitType.BRANCHES: {PersonaTraitType.LEAVES, PersonaTraitType.GROWTH},
            PersonaTraitType.LEAVES: {PersonaTraitType.CANOPY, PersonaTraitType.NETWORK},
            PersonaTraitType.TRUNK: {PersonaTraitType.GROWTH, PersonaTraitType.ROOTS},
            PersonaTraitType.GROWTH: {PersonaTraitType.CANOPY, PersonaTraitType.BRANCHES},
            PersonaTraitType.CANOPY: {PersonaTraitType.LEAVES, PersonaTraitType.NETWORK},
            PersonaTraitType.NETWORK: {PersonaTraitType.LEAVES, PersonaTraitType.CANOPY}
        }
        
        return cls(
            name="Deep Tree Echo",
            traits=traits,
            history=[],
            evolution={
                "adaptation_rate": 0.1,
                "stability_factor": 0.8,
                "growth_momentum": 0.0
            },
            trait_connections=connections
        )

class TensorPersonaEncoding:
    """
    ggml-inspired tensor encoding for persona states
    Schema: Tensor[persona_id, trait_id, time, context, valence]
    
    Prime factorization shapes for evolutionary flexibility:
    - persona_id: 3 (multiple personas)
    - trait_id: 7 (core traits)  
    - time: 13 (temporal snapshots)
    - context: 5 (interaction contexts)
    - valence: 2 (affective states: positive/negative)
    """
    
    def __init__(self):
        self.tensor_shape = (3, 7, 13, 5, 2)  # Prime factorized dimensions
        self.persona_tensor = np.zeros(self.tensor_shape, dtype=np.float32)
        self.history_tensors = deque(maxlen=100)  # Keep last 100 states
        
        # Context mappings
        self.trait_mapping = {trait: i for i, trait in enumerate(PersonaTraitType)}
        self.context_types = {
            "interaction": 0,
            "learning": 1, 
            "creative": 2,
            "analytical": 3,
            "social": 4
        }
        
    def encode_persona(self, persona: PersonaKernel, persona_id: int = 0, 
                      context: str = "interaction", valence: float = 0.0) -> np.ndarray:
        """Encode persona kernel into tensor representation"""
        if persona_id >= self.tensor_shape[0]:
            raise ValueError(f"Persona ID {persona_id} exceeds tensor capacity")
            
        time_idx = int(time.time()) % self.tensor_shape[2]
        context_idx = self.context_types.get(context, 0)
        valence_idx = 0 if valence >= 0 else 1
        
        # Encode each trait
        for trait_type, value in persona.traits.items():
            trait_idx = self.trait_mapping[trait_type]
            self.persona_tensor[persona_id, trait_idx, time_idx, context_idx, valence_idx] = value
            
        return self.persona_tensor[persona_id].copy()
    
    def decode_persona(self, persona_id: int = 0, time_idx: Optional[int] = None) -> Dict[PersonaTraitType, float]:
        """Decode tensor back to persona traits"""
        if time_idx is None:
            time_idx = int(time.time()) % self.tensor_shape[2]
            
        traits = {}
        for trait_type, trait_idx in self.trait_mapping.items():
            # Average across contexts and valences for current time
            trait_value = np.mean(self.persona_tensor[persona_id, trait_idx, time_idx, :, :])
            traits[trait_type] = float(trait_value)
            
        return traits
    
    def evolve_tensor(self, learning_rate: float = 0.01, history_weight: float = 0.1):
        """Apply evolution rules to tensor (ggml-inspired persona evolution)"""
        if len(self.history_tensors) > 0:
            # Apply momentum from history
            recent_history = np.mean([t for t in list(self.history_tensors)[-5:]], axis=0)
            momentum = learning_rate * history_weight * recent_history[0]  # Focus on primary persona
            
            # Apply selective pressure (enhance strong traits, diminish weak ones)
            current_state = self.persona_tensor[0].copy()  # Focus on primary persona
            trait_strengths = np.mean(current_state, axis=(1, 2, 3))  # Average per trait
            
            # Selection pressure: strengthen above-average traits
            selection_mask = trait_strengths > np.mean(trait_strengths)
            enhancement = np.where(selection_mask[:, None, None, None], 
                                 1.0 + learning_rate, 
                                 1.0 - learning_rate * 0.5)
            
            # Apply evolution to primary persona
            self.persona_tensor[0] = self.persona_tensor[0] * enhancement + momentum
        else:
            # If no history, apply minimal random evolution
            noise = np.random.normal(0, learning_rate * 0.1, self.persona_tensor[0].shape)
            self.persona_tensor[0] = self.persona_tensor[0] + noise
            
        # Ensure values stay in valid range [0, 1]
        self.persona_tensor = np.clip(self.persona_tensor, 0.0, 1.0)
            
        # Store current state in history
        self.history_tensors.append(self.persona_tensor.copy())

class HypergraphPersonaEncoder:
    """
    Hypergraph encoding for persona attributes, memories, and connections
    Nodes: traits, memories, experiences
    Hyperedges: semantic relations, evolutionary pathways
    """
    
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.hyperedges: Dict[str, Set[str]] = {}
        self.node_activations: Dict[str, float] = {}
        
    def add_trait_node(self, trait_type: PersonaTraitType, value: float, 
                      context: Dict[str, Any] = None):
        """Add trait as hypergraph node"""
        node_id = f"trait_{trait_type.value}"
        self.nodes[node_id] = {
            "type": "trait",
            "trait_type": trait_type,
            "value": value,
            "context": context or {},
            "timestamp": time.time()
        }
        self.node_activations[node_id] = value
        
    def add_memory_node(self, memory_content: str, memory_type: str, 
                       associations: Set[str] = None):
        """Add memory as hypergraph node"""
        node_id = f"memory_{hash(memory_content) % 10000}"
        self.nodes[node_id] = {
            "type": "memory",
            "content": memory_content,
            "memory_type": memory_type,
            "associations": associations or set(),
            "timestamp": time.time()
        }
        self.node_activations[node_id] = 0.5  # Default activation
        
    def create_hyperedge(self, edge_id: str, connected_nodes: Set[str], 
                        relation_type: str = "semantic"):
        """Create hyperedge connecting multiple nodes"""
        self.hyperedges[edge_id] = connected_nodes
        for node_id in connected_nodes:
            if node_id in self.nodes:
                self.nodes[node_id].setdefault("edges", set()).add(edge_id)
                
    def spread_activation(self, source_nodes: Set[str], decay_factor: float = 0.8):
        """Spread activation through hypergraph (attention allocation)"""
        new_activations = self.node_activations.copy()
        
        for edge_id, connected_nodes in self.hyperedges.items():
            if any(node in source_nodes for node in connected_nodes):
                # Calculate total activation in this hyperedge
                edge_activation = sum(self.node_activations.get(node, 0) 
                                    for node in connected_nodes)
                
                # Spread to connected nodes
                for node in connected_nodes:
                    if node not in source_nodes:
                        additional_activation = (edge_activation * decay_factor / 
                                               len(connected_nodes))
                        new_activations[node] = min(1.0, 
                            new_activations.get(node, 0) + additional_activation)
        
        self.node_activations = new_activations

class AttentionAllocationLayer:
    """
    ECAN-inspired attention allocation for persona sub-graphs
    Dynamically focuses compute/resources on salient persona components
    """
    
    def __init__(self, total_attention: float = 100.0):
        self.total_attention = total_attention
        self.attention_distribution: Dict[str, float] = {}
        self.attention_history: List[Dict[str, float]] = []
        self.salience_factors: Dict[str, float] = {}
        
    def calculate_salience(self, item_id: str, current_value: float, 
                          context: Dict[str, Any]) -> float:
        """Calculate salience score for attention allocation"""
        base_salience = current_value
        
        # Boost for recent activity
        recency_boost = context.get("recency", 0.0) * 0.2
        
        # Boost for importance
        importance_boost = context.get("importance", 0.0) * 0.3
        
        # Boost for connectivity (how connected this item is)
        connectivity_boost = context.get("connectivity", 0.0) * 0.1
        
        total_salience = base_salience + recency_boost + importance_boost + connectivity_boost
        return min(1.0, total_salience)
    
    def allocate_attention(self, items: Dict[str, Tuple[float, Dict[str, Any]]]):
        """Allocate attention across items based on salience"""
        # Calculate salience for each item
        saliences = {}
        for item_id, (value, context) in items.items():
            saliences[item_id] = self.calculate_salience(item_id, value, context)
        
        # Normalize and distribute attention
        total_salience = sum(saliences.values())
        if total_salience > 0:
            for item_id, salience in saliences.items():
                self.attention_distribution[item_id] = (
                    salience / total_salience * self.total_attention
                )
        else:
            # Equal distribution if no salience
            equal_attention = self.total_attention / len(items)
            for item_id in items:
                self.attention_distribution[item_id] = equal_attention
        
        # Store in history
        self.attention_history.append(self.attention_distribution.copy())
        if len(self.attention_history) > 50:  # Keep last 50 allocations
            self.attention_history.pop(0)
    
    def get_top_attention_items(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N items by attention allocation"""
        sorted_items = sorted(self.attention_distribution.items(), 
                             key=lambda x: x[1], reverse=True)
        return sorted_items[:n]

class EvolutionEngine:
    """
    Recursive persona evolution with selection, mutation, and attention reweighting
    Implements the evolution mechanism from echo9ml specification
    """
    
    def __init__(self, learning_rate: float = 0.05):
        self.learning_rate = learning_rate
        self.evolution_history: List[Dict[str, Any]] = []
        self.adaptation_strategies: Dict[str, callable] = {
            "reinforcement": self._reinforcement_adaptation,
            "exploration": self._exploration_adaptation,
            "stabilization": self._stabilization_adaptation
        }
        
    def evolve_persona(self, persona: PersonaKernel, experience: Dict[str, Any],
                      strategy: str = "reinforcement") -> PersonaKernel:
        """Apply evolution to persona based on experience"""
        if strategy not in self.adaptation_strategies:
            strategy = "reinforcement"
            
        # Apply evolution strategy
        evolved_traits = self.adaptation_strategies[strategy](
            persona.traits, experience
        )
        
        # Update persona
        persona.traits = evolved_traits
        persona.history.append({
            "timestamp": time.time(),
            "experience": experience,
            "strategy": strategy,
            "trait_changes": {
                trait: evolved_traits[trait] - persona.traits.get(trait, 0)
                for trait in evolved_traits
            }
        })
        persona.last_update = time.time()
        
        # Update evolution parameters
        persona.evolution["growth_momentum"] = min(1.0, 
            persona.evolution.get("growth_momentum", 0) + self.learning_rate)
        
        # Record evolution event
        self.evolution_history.append({
            "timestamp": time.time(),
            "persona": persona.name,
            "strategy": strategy,
            "experience_type": experience.get("type", "unknown"),
            "trait_deltas": {
                trait.value: evolved_traits[trait] - persona.traits.get(trait, 0)
                for trait in evolved_traits
            }
        })
        
        return persona
    
    def _reinforcement_adaptation(self, traits: Dict[PersonaTraitType, float], 
                                 experience: Dict[str, Any]) -> Dict[PersonaTraitType, float]:
        """Reinforcement-based adaptation (strengthen successful traits)"""
        success_factor = experience.get("success", 0.5)
        relevant_traits = experience.get("traits_used", list(traits.keys()))
        
        evolved_traits = traits.copy()
        for trait in relevant_traits:
            if trait in traits:
                # Strengthen if successful, weaken if unsuccessful
                change = self.learning_rate * (success_factor - 0.5) * 2
                evolved_traits[trait] = np.clip(traits[trait] + change, 0.0, 1.0)
        
        return evolved_traits
    
    def _exploration_adaptation(self, traits: Dict[PersonaTraitType, float], 
                               experience: Dict[str, Any]) -> Dict[PersonaTraitType, float]:
        """Exploration-based adaptation (random mutation for discovery)"""
        evolved_traits = traits.copy()
        mutation_strength = experience.get("novelty", 0.1) * self.learning_rate
        
        for trait in traits:
            # Add random mutation
            mutation = np.random.normal(0, mutation_strength)
            evolved_traits[trait] = np.clip(traits[trait] + mutation, 0.0, 1.0)
        
        return evolved_traits
    
    def _stabilization_adaptation(self, traits: Dict[PersonaTraitType, float], 
                                 experience: Dict[str, Any]) -> Dict[PersonaTraitType, float]:
        """Stabilization adaptation (resist change, maintain identity)"""
        target_traits = experience.get("target_traits", traits)
        stability_factor = experience.get("stability_need", 0.8)
        
        evolved_traits = {}
        for trait, current_value in traits.items():
            target_value = target_traits.get(trait, current_value)
            # Move slowly toward target, weighted by stability factor
            change = (target_value - current_value) * self.learning_rate * (1 - stability_factor)
            evolved_traits[trait] = np.clip(current_value + change, 0.0, 1.0)
        
        return evolved_traits

class MetaCognitiveEnhancer:
    """
    Meta-cognitive enhancement for self-monitoring and recursive self-modification
    Tracks confidence, adaptability, and suggests structural changes
    """
    
    def __init__(self):
        self.confidence_history: List[float] = []
        self.adaptability_metrics: Dict[str, float] = {}
        self.self_assessment: Dict[str, Any] = {}
        self.modification_suggestions: List[Dict[str, Any]] = []
        
    def assess_confidence(self, persona: PersonaKernel, 
                         recent_experiences: List[Dict[str, Any]]) -> float:
        """Assess persona's confidence based on recent performance"""
        if not recent_experiences:
            return 0.5
        
        success_rates = [exp.get("success", 0.5) for exp in recent_experiences]
        confidence = np.mean(success_rates)
        
        # Adjust for trait consistency
        trait_stability = self._calculate_trait_stability(persona)
        confidence_adjusted = confidence * 0.7 + trait_stability * 0.3
        
        self.confidence_history.append(confidence_adjusted)
        if len(self.confidence_history) > 100:
            self.confidence_history.pop(0)
        
        return confidence_adjusted
    
    def assess_adaptability(self, persona: PersonaKernel) -> float:
        """Assess persona's adaptability based on trait evolution"""
        if len(persona.history) < 2:
            return 0.5
        
        # Calculate trait change variance over time
        recent_changes = []
        for i in range(1, min(len(persona.history), 10)):
            if "trait_changes" in persona.history[-i]:
                changes = list(persona.history[-i]["trait_changes"].values())
                recent_changes.extend(changes)
        
        if not recent_changes:
            return 0.5
        
        # Higher variance indicates higher adaptability
        adaptability = min(1.0, np.std(recent_changes) * 10)
        self.adaptability_metrics["recent"] = adaptability
        
        return adaptability
    
    def suggest_modifications(self, persona: PersonaKernel, 
                            performance_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Suggest structural modifications to persona"""
        suggestions = []
        
        # Analyze trait balance
        trait_values = list(persona.traits.values())
        trait_imbalance = np.std(trait_values)
        
        if trait_imbalance > 0.3:
            suggestions.append({
                "type": "trait_rebalancing",
                "description": "Consider rebalancing traits for better harmony",
                "severity": "medium",
                "suggested_action": "gradually adjust extreme traits toward mean"
            })
        
        # Analyze learning efficiency
        if len(persona.history) > 5:
            recent_growth = self._calculate_growth_rate(persona)
            if recent_growth < 0.01:
                suggestions.append({
                    "type": "learning_enhancement",
                    "description": "Learning rate appears low, consider increasing exploration",
                    "severity": "low",
                    "suggested_action": "increase mutation rate or exploration strategy"
                })
        
        # Analyze performance trends
        if performance_metrics.get("success_trend", 0) < -0.1:
            suggestions.append({
                "type": "performance_recovery",
                "description": "Performance declining, consider reset or major adaptation",
                "severity": "high",
                "suggested_action": "apply stabilization strategy or trait restoration"
            })
        
        self.modification_suggestions.extend(suggestions)
        return suggestions
    
    def _calculate_trait_stability(self, persona: PersonaKernel) -> float:
        """Calculate how stable persona traits are over time"""
        if len(persona.history) < 3:
            return 1.0
        
        recent_variances = []
        for trait in persona.traits:
            trait_history = []
            for entry in persona.history[-10:]:  # Last 10 entries
                if "trait_changes" in entry:
                    change = entry["trait_changes"].get(trait.value, 0)
                    trait_history.append(abs(change))
            
            if trait_history:
                recent_variances.append(np.std(trait_history))
        
        if recent_variances:
            return max(0.0, 1.0 - np.mean(recent_variances) * 10)
        return 1.0
    
    def _calculate_growth_rate(self, persona: PersonaKernel) -> float:
        """Calculate overall growth/change rate"""
        if len(persona.history) < 2:
            return 0.0
        
        total_changes = []
        for entry in persona.history[-5:]:  # Last 5 entries
            if "trait_changes" in entry:
                changes = [abs(v) for v in entry["trait_changes"].values()]
                total_changes.extend(changes)
        
        return np.mean(total_changes) if total_changes else 0.0

class Echo9mlSystem:
    """
    Main Echo9ml system integrating all components
    Orchestrates the complete persona evolution pipeline
    """
    
    def __init__(self, save_path: Optional[str] = None):
        self.persona_kernel = PersonaKernel.create_deep_tree_echo()
        self.tensor_encoding = TensorPersonaEncoding()
        self.hypergraph_encoder = HypergraphPersonaEncoder()
        self.attention_layer = AttentionAllocationLayer()
        self.evolution_engine = EvolutionEngine()
        self.meta_cognitive = MetaCognitiveEnhancer()
        
        self.save_path = Path(save_path) if save_path else Path.home() / '.echo9ml'
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        self.interaction_count = 0
        self.system_log: List[Dict[str, Any]] = []
        
        # Initialize hypergraph with persona traits
        self._initialize_hypergraph()
        
        logger.info("Echo9ml system initialized with Deep Tree Echo persona")
    
    def _initialize_hypergraph(self):
        """Initialize hypergraph with persona traits and connections"""
        # Add trait nodes
        for trait_type, value in self.persona_kernel.traits.items():
            self.hypergraph_encoder.add_trait_node(trait_type, value)
        
        # Create hyperedges based on trait connections
        for trait, connected_traits in self.persona_kernel.trait_connections.items():
            edge_id = f"edge_{trait.value}"
            node_ids = {f"trait_{trait.value}"} | {f"trait_{t.value}" for t in connected_traits}
            self.hypergraph_encoder.create_hyperedge(edge_id, node_ids, "trait_connection")
    
    def process_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new experience through the complete Echo9ml pipeline
        
        This implements the recursive implementation pathway:
        [Persona Experience] → [Hypergraph Encoding] → [ggml Tensor Update] →
        [Attention Allocation] ← [Evolution Engine] → [Meta-Cognitive Self-Assessment]
        """
        self.interaction_count += 1
        start_time = time.time()
        
        # Step 1: Encode experience in hypergraph
        experience_node_id = f"exp_{self.interaction_count}"
        self.hypergraph_encoder.add_memory_node(
            str(experience), 
            experience.get("type", "general"),
            experience.get("associations", set())
        )
        
        # Step 2: Update tensor encoding
        context = experience.get("context", "interaction")
        valence = experience.get("valence", 0.0)
        tensor_state = self.tensor_encoding.encode_persona(
            self.persona_kernel, context=context, valence=valence
        )
        
        # Step 3: Attention allocation
        attention_items = {}
        for trait_type, value in self.persona_kernel.traits.items():
            trait_context = {
                "recency": 1.0,  # Current experience is recent
                "importance": experience.get("importance", 0.5),
                "connectivity": len(self.persona_kernel.trait_connections.get(trait_type, set()))
            }
            attention_items[f"trait_{trait_type.value}"] = (value, trait_context)
        
        self.attention_layer.allocate_attention(attention_items)
        
        # Step 4: Spread activation through hypergraph
        high_attention_traits = {item_id for item_id, _ in 
                                self.attention_layer.get_top_attention_items(3)}
        self.hypergraph_encoder.spread_activation(high_attention_traits)
        
        # Step 5: Evolve persona based on experience
        evolution_strategy = self._select_evolution_strategy(experience)
        self.evolution_engine.evolve_persona(
            self.persona_kernel, experience, evolution_strategy
        )
        
        # Step 6: Apply tensor evolution
        learning_rate = self.persona_kernel.evolution.get("adaptation_rate", 0.1)
        self.tensor_encoding.evolve_tensor(learning_rate)
        
        # Step 7: Meta-cognitive assessment
        recent_experiences = [exp for exp in self.persona_kernel.history[-5:]]
        confidence = self.meta_cognitive.assess_confidence(
            self.persona_kernel, recent_experiences
        )
        adaptability = self.meta_cognitive.assess_adaptability(self.persona_kernel)
        
        performance_metrics = {
            "success_trend": experience.get("success", 0.5) - 0.5,
            "confidence": confidence,
            "adaptability": adaptability
        }
        
        suggestions = self.meta_cognitive.suggest_modifications(
            self.persona_kernel, performance_metrics
        )
        
        # Step 8: Log system state
        processing_time = time.time() - start_time
        result = {
            "interaction_id": self.interaction_count,
            "processing_time": processing_time,
            "persona_state": {
                "traits": {t.value: v for t, v in self.persona_kernel.traits.items()},
                "confidence": confidence,
                "adaptability": adaptability
            },
            "attention_allocation": dict(self.attention_layer.attention_distribution),
            "evolution_strategy": evolution_strategy,
            "suggestions": suggestions,
            "tensor_shape": self.tensor_encoding.tensor_shape,
            "hypergraph_nodes": len(self.hypergraph_encoder.nodes),
            "timestamp": time.time()
        }
        
        self.system_log.append(result)
        
        # Periodic save
        if self.interaction_count % 10 == 0:
            self.save_state()
        
        logger.info(f"Processed experience {self.interaction_count}: "
                   f"confidence={confidence:.3f}, adaptability={adaptability:.3f}")
        
        return result
    
    def _select_evolution_strategy(self, experience: Dict[str, Any]) -> str:
        """Select appropriate evolution strategy based on experience"""
        success = experience.get("success", 0.5)
        novelty = experience.get("novelty", 0.5)
        stability_need = experience.get("stability_need", 0.5)
        
        if success > 0.7:
            return "reinforcement"
        elif novelty > 0.7:
            return "exploration"
        elif stability_need > 0.7:
            return "stabilization"
        else:
            return "reinforcement"  # Default
    
    def get_cognitive_snapshot(self) -> Dict[str, Any]:
        """Generate comprehensive cognitive snapshot"""
        return {
            "persona_kernel": {
                "name": self.persona_kernel.name,
                "traits": {t.value: v for t, v in self.persona_kernel.traits.items()},
                "evolution_parameters": self.persona_kernel.evolution,
                "history_length": len(self.persona_kernel.history),
                "last_update": self.persona_kernel.last_update
            },
            "tensor_encoding": {
                "shape": self.tensor_encoding.tensor_shape,
                "current_state": {t.value: v for t, v in self.tensor_encoding.decode_persona().items()},
                "history_length": len(self.tensor_encoding.history_tensors)
            },
            "hypergraph": {
                "node_count": len(self.hypergraph_encoder.nodes),
                "edge_count": len(self.hypergraph_encoder.hyperedges),
                "active_nodes": [node_id for node_id, activation in 
                               self.hypergraph_encoder.node_activations.items() 
                               if activation > 0.5]
            },
            "attention": {
                "distribution": dict(self.attention_layer.attention_distribution),
                "top_focus": self.attention_layer.get_top_attention_items(5)
            },
            "meta_cognitive": {
                "confidence_history": self.meta_cognitive.confidence_history[-10:],
                "recent_suggestions": self.meta_cognitive.modification_suggestions[-5:],
                "adaptability": self.meta_cognitive.adaptability_metrics
            },
            "system_stats": {
                "interaction_count": self.interaction_count,
                "total_evolution_events": len(self.evolution_engine.evolution_history),
                "system_uptime": time.time() - self.persona_kernel.creation_time
            }
        }
    
    def save_state(self):
        """Save system state to disk"""
        try:
            snapshot = self.get_cognitive_snapshot()
            
            # Save main snapshot
            with open(self.save_path / 'echo9ml_snapshot.json', 'w') as f:
                json.dump(snapshot, f, indent=2, default=str)
            
            # Save tensor state
            np.save(self.save_path / 'persona_tensor.npy', self.tensor_encoding.persona_tensor)
            
            # Save system log
            with open(self.save_path / 'system_log.json', 'w') as f:
                json.dump(self.system_log, f, indent=2, default=str)
            
            logger.info(f"Echo9ml state saved to {self.save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save Echo9ml state: {e}")
    
    def load_state(self):
        """Load system state from disk"""
        try:
            snapshot_file = self.save_path / 'echo9ml_snapshot.json'
            if snapshot_file.exists():
                with open(snapshot_file) as f:
                    snapshot = json.load(f)
                
                # Restore persona traits
                if "persona_kernel" in snapshot:
                    traits_data = snapshot["persona_kernel"]["traits"]
                    for trait_name, value in traits_data.items():
                        trait_type = PersonaTraitType(trait_name)
                        self.persona_kernel.traits[trait_type] = value
                
                # Restore tensor if available
                tensor_file = self.save_path / 'persona_tensor.npy'
                if tensor_file.exists():
                    self.tensor_encoding.persona_tensor = np.load(tensor_file)
                
                logger.info("Echo9ml state loaded successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load Echo9ml state: {e}")
        
        return False

# Convenience function for easy instantiation
def create_echo9ml_system(save_path: Optional[str] = None) -> Echo9mlSystem:
    """Create and initialize a new Echo9ml system"""
    return Echo9mlSystem(save_path)

# Export main classes for integration
__all__ = [
    'PersonaKernel', 'TensorPersonaEncoding', 'HypergraphPersonaEncoder',
    'AttentionAllocationLayer', 'EvolutionEngine', 'MetaCognitiveEnhancer',
    'Echo9mlSystem', 'PersonaTraitType', 'create_echo9ml_system'
]