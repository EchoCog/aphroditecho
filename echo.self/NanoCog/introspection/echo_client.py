"""
Echo Self Client

Client for interacting with Echo Self cognitive architecture and introspection capabilities.
Extends the basic AtomSpace client with Echo Self specific functionality.
"""

import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from .atomspace_client import AtomSpaceClient

class EchoSelfClient(AtomSpaceClient):
    """
    Enhanced client for Echo Self introspection and cognitive interaction.
    """
    
    def __init__(self, base_url: str = "http://localhost:8081/api/v1", timeout: int = 30):
        super().__init__(base_url, timeout)
        self.echo_depth = 3
        self.persona_dimensions = [
            'cognitive', 'introspective', 'adaptive', 'recursive',
            'synergistic', 'holographic', 'neural_symbolic', 'dynamic'
        ]
    
    def get_echo_state(self) -> Dict[str, Any]:
        """Get the current Echo Self cognitive state."""
        try:
            response = self.session.get(
                f"{self.base_url}/echo/state",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting Echo Self state: {e}")
            return self.mock_get_echo_state()
    
    def trigger_introspection(self, depth: int = 3) -> Dict[str, Any]:
        """Trigger Echo Self introspection at specified depth."""
        try:
            payload = {"depth": depth, "enable_recursion": True}
            response = self.session.post(
                f"{self.base_url}/echo/introspect",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error triggering introspection: {e}")
            return self.mock_introspection_result(depth)
    
    def get_adaptive_attention_state(self) -> Dict[str, Any]:
        """Get the current adaptive attention allocation state."""
        try:
            response = self.session.get(
                f"{self.base_url}/echo/attention",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting attention state: {e}")
            return self.mock_adaptive_attention_state()
    
    def update_cognitive_load(self, load: float, activity: float) -> Dict[str, Any]:
        """Update cognitive load and recent activity for attention calculation."""
        try:
            payload = {
                "cognitive_load": load,
                "recent_activity": activity,
                "recalculate_threshold": True
            }
            response = self.session.post(
                f"{self.base_url}/echo/attention/update",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error updating cognitive load: {e}")
            return self.mock_attention_update(load, activity)
    
    def get_persona_dimension_state(self, dimension: str) -> Dict[str, Any]:
        """Get the state of a specific persona dimension."""
        if dimension not in self.persona_dimensions:
            raise ValueError(f"Unknown persona dimension: {dimension}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/echo/persona/{dimension}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting persona dimension {dimension}: {e}")
            return self.mock_persona_dimension_state(dimension)
    
    def get_hypergraph_patterns(self, limit: int = 50) -> Dict[str, Any]:
        """Get current hypergraph pattern encoding state."""
        try:
            params = {"limit": limit, "include_semantic_links": True}
            response = self.session.get(
                f"{self.base_url}/echo/hypergraph",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting hypergraph patterns: {e}")
            return self.mock_hypergraph_patterns(limit)
    
    def evaluate_cognitive_synergy(self) -> Dict[str, Any]:
        """Evaluate the current level of cognitive synergy."""
        try:
            response = self.session.post(
                f"{self.base_url}/echo/synergy/evaluate",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error evaluating cognitive synergy: {e}")
            return self.mock_cognitive_synergy_evaluation()
    
    # Mock methods for testing and development
    
    def mock_get_echo_state(self) -> Dict[str, Any]:
        """Generate mock Echo Self state for testing."""
        return {
            "echo_depth": self.echo_depth,
            "persona_dimensions": {
                dim: {
                    "activation_level": random.uniform(0.3, 0.9),
                    "coherence_score": random.uniform(0.6, 0.95),
                    "recent_activity": random.uniform(0.1, 0.8)
                } for dim in self.persona_dimensions
            },
            "adaptive_attention_state": self.mock_adaptive_attention_state(),
            "recursive_reasoning_depth": random.randint(2, 5),
            "hypergraph_patterns": self.mock_hypergraph_patterns(25),
            "cognitive_synergy_level": random.uniform(0.5, 0.9),
            "timestamp": time.time(),
            "status": "introspecting"
        }
    
    def mock_adaptive_attention_state(self) -> Dict[str, Any]:
        """Generate mock adaptive attention state."""
        cognitive_load = random.uniform(0.2, 0.8)
        recent_activity = random.uniform(0.1, 0.7)
        threshold = 0.5 + (cognitive_load * 0.3) - (recent_activity * 0.2)
        
        return {
            "current_focus": random.choice([
                "repository_introspection", "semantic_analysis", 
                "pattern_encoding", "recursive_reasoning",
                "persona_integration", "cognitive_synergy"
            ]),
            "attention_threshold": max(0.1, min(1.0, threshold)),
            "cognitive_load": cognitive_load,
            "recent_activity": recent_activity,
            "active_patterns": random.randint(50, 500),
            "attention_distribution": {
                "high_priority": random.randint(10, 50),
                "medium_priority": random.randint(20, 100),
                "low_priority": random.randint(50, 200)
            },
            "last_adjustment": time.time() - random.randint(60, 3600)
        }
    
    def mock_introspection_result(self, depth: int) -> Dict[str, Any]:
        """Generate mock introspection result."""
        return {
            "introspection_depth": depth,
            "recursive_levels": [
                {
                    "level": i,
                    "focus": random.choice([
                        "self_examination", "cognitive_pattern_analysis",
                        "attention_optimization", "persona_coherence",
                        "reasoning_depth_assessment"
                    ]),
                    "insights": [
                        f"Level {i} insight: {random.choice([
                            'Enhanced attention allocation detected',
                            'Persona dimension coherence improved',
                            'Recursive reasoning depth optimized',
                            'Hypergraph pattern encoding refined',
                            'Cognitive synergy level increased'
                        ])}"
                    ],
                    "quality_score": random.uniform(0.6, 0.95)
                } for i in range(1, depth + 1)
            ],
            "overall_coherence": random.uniform(0.7, 0.95),
            "recommendations": [
                "Continue recursive depth exploration",
                "Enhance cross-dimensional persona integration",
                "Optimize attention threshold calculations",
                "Strengthen hypergraph semantic links"
            ],
            "timestamp": time.time()
        }
    
    def mock_persona_dimension_state(self, dimension: str) -> Dict[str, Any]:
        """Generate mock persona dimension state."""
        base_descriptions = {
            'cognitive': 'Analytical reasoning and pattern recognition capabilities',
            'introspective': 'Self-examination and meta-cognitive awareness',
            'adaptive': 'Dynamic threshold adjustment and response flexibility',
            'recursive': 'Multi-level processing and depth exploration',
            'synergistic': 'Emergent properties from component interactions',
            'holographic': 'Comprehensive modeling and perspective integration',
            'neural_symbolic': 'Hybrid reasoning combining neural and symbolic approaches',
            'dynamic': 'Continuous evolution and learning adaptation'
        }
        
        return {
            "dimension": dimension,
            "description": base_descriptions.get(dimension, "Unknown dimension"),
            "activation_level": random.uniform(0.4, 0.9),
            "coherence_score": random.uniform(0.6, 0.95),
            "interaction_strength": {
                other_dim: random.uniform(0.2, 0.8) 
                for other_dim in self.persona_dimensions if other_dim != dimension
            },
            "recent_patterns": [
                f"{dimension}_pattern_{i}" for i in range(random.randint(3, 8))
            ],
            "optimization_suggestions": [
                f"Enhance {dimension} integration with recursive reasoning",
                f"Strengthen {dimension} coherence across contexts",
                f"Optimize {dimension} response patterns"
            ],
            "timestamp": time.time()
        }
    
    def mock_hypergraph_patterns(self, limit: int) -> Dict[str, Any]:
        """Generate mock hypergraph patterns."""
        node_types = [
            'cognitive_concept', 'attention_node', 'persona_dimension',
            'reasoning_pattern', 'semantic_link', 'introspection_point'
        ]
        
        nodes = []
        for i in range(min(limit, random.randint(20, 60))):
            nodes.append({
                "id": f"node_{i}",
                "type": random.choice(node_types),
                "content": f"Echo Self pattern {i}",
                "salience": random.uniform(0.1, 0.9),
                "connections": random.randint(1, 8),
                "semantic_weight": random.uniform(0.3, 0.8)
            })
        
        return {
            "nodes": nodes,
            "edges": [
                {
                    "source": f"node_{random.randint(0, len(nodes)-1)}",
                    "target": f"node_{random.randint(0, len(nodes)-1)}",
                    "weight": random.uniform(0.2, 0.9),
                    "type": random.choice(['semantic', 'causal', 'temporal', 'associative'])
                } for _ in range(random.randint(15, 40))
            ],
            "semantic_links": [
                {
                    "concept_a": random.choice(['attention', 'recursion', 'adaptation', 'synergy']),
                    "concept_b": random.choice(['persona', 'cognition', 'introspection', 'encoding']),
                    "strength": random.uniform(0.4, 0.9),
                    "context": "Echo Self cognitive architecture"
                } for _ in range(random.randint(8, 15))
            ],
            "pattern_complexity": random.uniform(0.5, 0.9),
            "coherence_score": random.uniform(0.6, 0.95),
            "timestamp": time.time()
        }
    
    def mock_attention_update(self, load: float, activity: float) -> Dict[str, Any]:
        """Generate mock attention update result."""
        new_threshold = 0.5 + (load * 0.3) - (activity * 0.2)
        new_threshold = max(0.1, min(1.0, new_threshold))
        
        return {
            "previous_threshold": random.uniform(0.3, 0.8),
            "new_threshold": new_threshold,
            "cognitive_load": load,
            "recent_activity": activity,
            "adjustment_magnitude": abs(new_threshold - random.uniform(0.3, 0.8)),
            "attention_reallocation": {
                "patterns_promoted": random.randint(5, 25),
                "patterns_demoted": random.randint(3, 15),
                "focus_shift": random.choice([
                    "increased_depth", "broader_scope", "maintained_balance",
                    "refined_focus", "exploratory_expansion"
                ])
            },
            "timestamp": time.time()
        }
    
    def mock_cognitive_synergy_evaluation(self) -> Dict[str, Any]:
        """Generate mock cognitive synergy evaluation."""
        return {
            "overall_synergy_level": random.uniform(0.6, 0.9),
            "component_interactions": {
                "attention_persona_synergy": random.uniform(0.5, 0.9),
                "recursive_hypergraph_synergy": random.uniform(0.6, 0.85),
                "introspection_adaptation_synergy": random.uniform(0.55, 0.9),
                "cognitive_dynamic_synergy": random.uniform(0.6, 0.88)
            },
            "emergent_properties": [
                "Holographic cognitive modeling",
                "Adaptive attention optimization",
                "Recursive depth exploration",
                "Cross-dimensional coherence",
                "Dynamic pattern recognition"
            ],
            "synergy_trends": {
                "increasing": ["attention_optimization", "persona_integration"],
                "stable": ["recursive_reasoning", "hypergraph_encoding"],
                "developing": ["cognitive_synergy", "dynamic_adaptation"]
            },
            "optimization_potential": random.uniform(0.7, 0.95),
            "timestamp": time.time()
        }