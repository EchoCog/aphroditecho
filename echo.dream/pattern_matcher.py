"""
Pattern Matching System for Deep Tree Echo

This module provides pattern matching capabilities for memory nodes and structures,
enabling the recognition of similar patterns across different contexts.
"""

import logging
import random
from typing import Dict, List, Optional, Tuple

from database import db
from models_memory import (
    MemoryNode, MemoryAssociation, PatternTemplate
)

logger = logging.getLogger(__name__)

class PatternMatcher:
    """
    Manages pattern matching across memory nodes and structures.
    """
    def __init__(self):
        self.similarity_threshold = 0.7  # Minimum similarity score to consider a match
        
        # Basic pattern templates
        self.basic_patterns = {
            'sequence': self._match_sequence_pattern,
            'hierarchy': self._match_hierarchy_pattern,
            'similarity': self._match_similarity_pattern,
            'metaphor': self._match_metaphor_pattern,
            'causality': self._match_causality_pattern
        }
        
        # Advanced pattern matching techniques
        self.advanced_matchers = {
            'graph_isomorphism': self._match_graph_isomorphism,
            'recursive_similarity': self._match_recursive_similarity,
            'semantic_similarity': self._match_semantic_similarity
        }
        
        # Cache of recently matched patterns
        self.match_cache = {}  # {pattern_id: {node_ids_hash: score}}
        
    def initialize_basic_patterns(self):
        """Initialize basic pattern templates in the database if they don't exist."""
        from app import app
        
        with app.app_context():
            for pattern_type, matcher in self.basic_patterns.items():
                # Check if pattern exists
                existing = PatternTemplate.query.filter_by(name=f"basic_{pattern_type}").first()
                if not existing:
                    # Create basic pattern structure
                    structure = {
                        'type': pattern_type,
                        'nodes': {
                            'required': 2,
                            'max': 10
                        }
                    }
                    
                    # Create basic pattern rules
                    rules = {
                        'matcher': pattern_type,
                        'threshold': self.similarity_threshold,
                        'params': {}
                    }
                    
                    # Create description based on pattern type
                    description = self._get_pattern_description(pattern_type)
                    
                    # Create pattern template
                    pattern = PatternTemplate(
                        name=f"basic_{pattern_type}",
                        pattern_type=pattern_type,
                        description=description
                    )
                    
                    pattern.set_structure(structure)
                    pattern.set_rules(rules)
                    
                    # Add to database
                    db.session.add(pattern)
            
            # Commit changes
            db.session.commit()
            logger.info("Basic pattern templates initialized")
    
    def _get_pattern_description(self, pattern_type: str) -> str:
        """Get description for a pattern type."""
        descriptions = {
            'sequence': "Recognizes sequential patterns where items follow each other in a specific order.",
            'hierarchy': "Matches hierarchical structures with clear parent-child relationships.",
            'similarity': "Identifies patterns based on feature similarity across different contexts.",
            'metaphor': "Recognizes analogical mappings between different domains or contexts.",
            'causality': "Detects causal relationships and dependencies between events or concepts."
        }
        
        return descriptions.get(pattern_type, f"Pattern template for {pattern_type} matching")
    
    def match_pattern(self, pattern_id: int, nodes: List[MemoryNode]) -> float:
        """
        Match a pattern template against memory nodes.
        Returns a similarity score between 0.0 and 1.0.
        """
        # Get pattern from database
        pattern = PatternTemplate.query.get(pattern_id)
        if not pattern:
            logger.error(f"Pattern template with ID {pattern_id} not found")
            return 0.0
        
        # Check cache for recent matches
        node_ids = sorted([node.id for node in nodes])
        node_ids_hash = hash(tuple(node_ids))
        
        if pattern_id in self.match_cache and node_ids_hash in self.match_cache[pattern_id]:
            return self.match_cache[pattern_id][node_ids_hash]
        
        # Get pattern rules
        rules = pattern.get_rules()
        if not rules or 'matcher' not in rules:
            logger.error(f"Pattern {pattern_id} has invalid rules: {rules}")
            return 0.0
        
        # Get matcher function
        matcher_name = rules['matcher']
        matcher = None
        
        if matcher_name in self.basic_patterns:
            matcher = self.basic_patterns[matcher_name]
        elif matcher_name in self.advanced_matchers:
            matcher = self.advanced_matchers[matcher_name]
        else:
            logger.error(f"Unknown matcher: {matcher_name}")
            return 0.0
        
        # Apply matcher
        threshold = rules.get('threshold', self.similarity_threshold)
        params = rules.get('params', {})
        
        try:
            match_score = matcher(nodes, pattern, **params)
            
            # Cache the result
            if pattern_id not in self.match_cache:
                self.match_cache[pattern_id] = {}
            self.match_cache[pattern_id][node_ids_hash] = match_score
            
            # Return match if above threshold
            return match_score
        except Exception as e:
            logger.error(f"Error in pattern matcher {matcher_name}: {e}")
            return 0.0
    
    def find_matching_patterns(self, nodes: List[MemoryNode], 
                              threshold: Optional[float] = None) -> Dict[int, float]:
        """
        Find all pattern templates that match the given nodes.
        Returns a dictionary of pattern IDs to match scores.
        """
        if threshold is None:
            threshold = self.similarity_threshold
            
        # Get all pattern templates
        patterns = PatternTemplate.query.all()
        
        # Match each pattern
        matches = {}
        for pattern in patterns:
            match_score = self.match_pattern(pattern.id, nodes)
            if match_score >= threshold:
                matches[pattern.id] = match_score
        
        # Sort by match score
        return dict(sorted(matches.items(), key=lambda x: x[1], reverse=True))
    
    def find_similar_memories(self, memory_id: int, 
                            limit: int = 10, 
                            threshold: Optional[float] = None) -> List[Tuple[MemoryNode, float]]:
        """
        Find memories similar to the given memory.
        Returns a list of (memory_node, similarity_score) tuples.
        """
        if threshold is None:
            threshold = self.similarity_threshold
            
        # Get memory node
        memory = MemoryNode.query.get(memory_id)
        if not memory:
            logger.error(f"Memory node with ID {memory_id} not found")
            return []
        
        # Get all other memory nodes
        all_memories = MemoryNode.query.filter(MemoryNode.id != memory_id).all()
        
        # Calculate similarity for each memory
        similarities = []
        for other in all_memories:
            similarity = self._calculate_memory_similarity(memory, other)
            if similarity >= threshold:
                similarities.append((other, similarity))
        
        # Sort by similarity and limit results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def _calculate_memory_similarity(self, memory1: MemoryNode, memory2: MemoryNode) -> float:
        """Calculate similarity between two memory nodes."""
        # Base similarity on memory type and consolidation stage
        type_similarity = 1.0 if memory1.memory_type == memory2.memory_type else 0.5
        
        # Consolidation stage similarity
        stage_diff = abs(memory1.consolidation_stage - memory2.consolidation_stage)
        stage_similarity = max(0.0, 1.0 - (stage_diff / max(memory1.consolidation_stage, memory2.consolidation_stage, 1)))
        
        # Emotional similarity
        valence_diff = abs(memory1.emotional_valence - memory2.emotional_valence)
        arousal_diff = abs(memory1.emotional_arousal - memory2.emotional_arousal)
        emotional_similarity = max(0.0, 1.0 - (valence_diff + arousal_diff) / 4.0)
        
        # Context similarity
        context1 = memory1.get_context()
        context2 = memory2.get_context()
        context_similarity = self._calculate_context_similarity(context1, context2)
        
        # Base node similarity (using shared connections)
        base_similarity = self._calculate_base_node_similarity(memory1.node_id, memory2.node_id)
        
        # Combine similarities with weights
        weights = {
            'type': 0.2,
            'stage': 0.1,
            'emotional': 0.2,
            'context': 0.2,
            'base': 0.3
        }
        
        weighted_similarity = (
            weights['type'] * type_similarity +
            weights['stage'] * stage_similarity +
            weights['emotional'] * emotional_similarity +
            weights['context'] * context_similarity +
            weights['base'] * base_similarity
        )
        
        return weighted_similarity
    
    def _calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two context dictionaries."""
        # If either context is empty, return 0.5 (neutral similarity)
        if not context1 or not context2:
            return 0.5
        
        # Get all keys from both contexts
        all_keys = set(context1.keys()).union(set(context2.keys()))
        if not all_keys:
            return 0.5
        
        # Count matching keys and values
        matching_keys = 0
        matching_values = 0
        
        for key in all_keys:
            if key in context1 and key in context2:
                matching_keys += 1
                if context1[key] == context2[key]:
                    matching_values += 1
        
        # Calculate similarity
        key_similarity = matching_keys / len(all_keys)
        value_similarity = matching_values / max(1, matching_keys)
        
        # Combine with weights
        return 0.6 * key_similarity + 0.4 * value_similarity
    
    def _calculate_base_node_similarity(self, node_id1: int, node_id2: int) -> float:
        """Calculate similarity between base self-referential nodes."""
        from models import SelfReferentialNode, NodeConnection
        
        # Get nodes
        node1 = SelfReferentialNode.query.get(node_id1)
        node2 = SelfReferentialNode.query.get(node_id2)
        
        if not node1 or not node2:
            return 0.0
        
        # Check if same type
        type_similarity = 1.0 if node1.node_type == node2.node_type else 0.5
        
        # Check for shared connections
        connections1 = set()
        for conn in NodeConnection.query.filter(
            (NodeConnection.source_id == node_id1) | 
            (NodeConnection.target_id == node_id1)
        ).all():
            other_id = conn.target_id if conn.source_id == node_id1 else conn.source_id
            connections1.add(other_id)
        
        connections2 = set()
        for conn in NodeConnection.query.filter(
            (NodeConnection.source_id == node_id2) | 
            (NodeConnection.target_id == node_id2)
        ).all():
            other_id = conn.target_id if conn.source_id == node_id2 else conn.source_id
            connections2.add(other_id)
        
        # Calculate connection similarity
        all_connections = connections1.union(connections2)
        if not all_connections:
            connection_similarity = 0.5  # Neutral if no connections
        else:
            shared_connections = connections1.intersection(connections2)
            connection_similarity = len(shared_connections) / len(all_connections)
        
        # Express similarity for node expressions
        expression_similarity = 0.5  # Default neutral similarity
        if node1.expression and node2.expression:
            # Simple string similarity
            expr1 = node1.expression.lower()
            expr2 = node2.expression.lower()
            
            # Count common words
            words1 = set(expr1.split())
            words2 = set(expr2.split())
            common_words = words1.intersection(words2)
            all_words = words1.union(words2)
            
            if all_words:
                expression_similarity = len(common_words) / len(all_words)
        
        # Combine similarities with weights
        weights = {
            'type': 0.3,
            'connection': 0.4,
            'expression': 0.3
        }
        
        weighted_similarity = (
            weights['type'] * type_similarity +
            weights['connection'] * connection_similarity +
            weights['expression'] * expression_similarity
        )
        
        return weighted_similarity
    
    #
    # Basic pattern matchers
    #
    
    def _match_sequence_pattern(self, nodes: List[MemoryNode], 
                              pattern: PatternTemplate, **kwargs) -> float:
        """Match a sequence pattern."""
        if len(nodes) < 2:
            return 0.0
        
        # Sort nodes by timestamp
        sorted_nodes = sorted(nodes, key=lambda n: n.timestamp)
        
        # Check for temporal associations between consecutive nodes
        sequence_score = 0.0
        associations_count = 0
        
        for i in range(len(sorted_nodes) - 1):
            node1 = sorted_nodes[i]
            node2 = sorted_nodes[i + 1]
            
            # Check for temporal association
            assoc = MemoryAssociation.query.filter(
                (MemoryAssociation.source_id == node1.id) & 
                (MemoryAssociation.target_id == node2.id) &
                (MemoryAssociation.association_type.like('%temporal%'))
            ).first()
            
            if assoc:
                sequence_score += assoc.strength
                associations_count += 1
        
        # If no associations found, check time sequence
        if associations_count == 0:
            # Check if timestamps form a sequence
            time_deltas = []
            for i in range(len(sorted_nodes) - 1):
                delta = (sorted_nodes[i + 1].timestamp - sorted_nodes[i].timestamp).total_seconds()
                time_deltas.append(delta)
            
            if time_deltas:
                # Check if time deltas are roughly consistent
                avg_delta = sum(time_deltas) / len(time_deltas)
                variance = sum((d - avg_delta) ** 2 for d in time_deltas) / len(time_deltas)
                std_dev = variance ** 0.5
                
                # If standard deviation is less than half the average, consider it a sequence
                if std_dev < avg_delta / 2:
                    return 0.8  # Good sequence match
                else:
                    return 0.5  # Partial sequence match
            
            return 0.3  # Weak sequence match
        
        # Return average association strength
        return sequence_score / max(1, associations_count)
    
    def _match_hierarchy_pattern(self, nodes: List[MemoryNode], 
                               pattern: PatternTemplate, **kwargs) -> float:
        """Match a hierarchy pattern."""
        if len(nodes) < 2:
            return 0.0
        
        # Map nodes to their base nodes
        base_nodes = {}
        for node in nodes:
            base_nodes[node.id] = node.node_id
        
        # Check for parent-child relationships among base nodes
        from models import SelfReferentialNode
        
        hierarchy_score = 0.0
        hierarchy_count = 0
        
        for node_id, base_id in base_nodes.items():
            base_node = SelfReferentialNode.query.get(base_id)
            if not base_node:
                continue
                
            if base_node.parent_id and base_node.parent_id in base_nodes.values():
                hierarchy_score += 1.0
                hierarchy_count += 1
            
            # Check if this node is a parent of any other nodes
            children = SelfReferentialNode.query.filter_by(parent_id=base_id).all()
            for child in children:
                if child.id in base_nodes.values():
                    hierarchy_score += 1.0
                    hierarchy_count += 1
        
        # If no hierarchical relationships found, check memory node associations
        if hierarchy_count == 0:
            hierarch_assocs = 0
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    # Check for hierarchical association
                    assoc = MemoryAssociation.query.filter(
                        ((MemoryAssociation.source_id == node1.id) & 
                         (MemoryAssociation.target_id == node2.id) |
                         (MemoryAssociation.source_id == node2.id) & 
                         (MemoryAssociation.target_id == node1.id)) &
                        (MemoryAssociation.association_type.like('%hierarch%'))
                    ).first()
                    
                    if assoc:
                        hierarchy_score += assoc.strength
                        hierarch_assocs += 1
            
            if hierarch_assocs > 0:
                return hierarchy_score / hierarch_assocs
            
            return 0.3  # Weak hierarchy match
        
        # Return normalized hierarchy score
        max_possible = len(nodes) * 2  # Maximum possible parent-child relationships
        return min(1.0, hierarchy_score / max_possible)
    
    def _match_similarity_pattern(self, nodes: List[MemoryNode], 
                                pattern: PatternTemplate, **kwargs) -> float:
        """Match a similarity pattern."""
        if len(nodes) < 2:
            return 0.0
        
        # Calculate pairwise similarity between all nodes
        similarity_scores = []
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                similarity = self._calculate_memory_similarity(node1, node2)
                similarity_scores.append(similarity)
        
        # Return average similarity
        if similarity_scores:
            return sum(similarity_scores) / len(similarity_scores)
        return 0.0
    
    def _match_metaphor_pattern(self, nodes: List[MemoryNode], 
                              pattern: PatternTemplate, **kwargs) -> float:
        """Match a metaphor/analogy pattern."""
        if len(nodes) < 4:  # Need at least A:B::C:D for an analogy
            return 0.0
        
        # Group nodes by memory type
        nodes_by_type = {}
        for node in nodes:
            if node.memory_type not in nodes_by_type:
                nodes_by_type[node.memory_type] = []
            nodes_by_type[node.memory_type].append(node)
        
        # Need at least two types with at least two nodes each
        valid_types = [t for t, ns in nodes_by_type.items() if len(ns) >= 2]
        if len(valid_types) < 2:
            return 0.0
        
        # Check for analogy between first two valid types
        type1, type2 = valid_types[:2]
        nodes1 = nodes_by_type[type1][:2]  # First two nodes of type1
        nodes2 = nodes_by_type[type2][:2]  # First two nodes of type2
        
        # Check if relationships within types are similar
        relation1 = self._calculate_memory_similarity(nodes1[0], nodes1[1])
        relation2 = self._calculate_memory_similarity(nodes2[0], nodes2[1])
        
        # The analogy strength is inversely proportional to the difference in relations
        relation_diff = abs(relation1 - relation2)
        analogy_score = max(0.0, 1.0 - relation_diff)
        
        # Cross-domain mapping
        cross_similarity1 = self._calculate_memory_similarity(nodes1[0], nodes2[0])
        cross_similarity2 = self._calculate_memory_similarity(nodes1[1], nodes2[1])
        
        # Combine scores
        return 0.7 * analogy_score + 0.15 * cross_similarity1 + 0.15 * cross_similarity2
    
    def _match_causality_pattern(self, nodes: List[MemoryNode], 
                               pattern: PatternTemplate, **kwargs) -> float:
        """Match a causality pattern."""
        if len(nodes) < 2:
            return 0.0
        
        # Sort nodes by timestamp
        sorted_nodes = sorted(nodes, key=lambda n: n.timestamp)
        
        # Check for causal associations
        causal_score = 0.0
        causal_count = 0
        
        for i in range(len(sorted_nodes) - 1):
            node1 = sorted_nodes[i]
            node2 = sorted_nodes[i + 1]
            
            # Check for causal association
            assoc = MemoryAssociation.query.filter(
                (MemoryAssociation.source_id == node1.id) & 
                (MemoryAssociation.target_id == node2.id) &
                (MemoryAssociation.association_type.like('%caus%'))
            ).first()
            
            if assoc:
                causal_score += assoc.strength
                causal_count += 1
        
        # If no causal associations found, check temporal proximity and emotional change
        if causal_count == 0:
            emotions_change = []
            time_proximity = []
            
            for i in range(len(sorted_nodes) - 1):
                node1 = sorted_nodes[i]
                node2 = sorted_nodes[i + 1]
                
                # Calculate emotional change
                valence_change = abs(node2.emotional_valence - node1.emotional_valence)
                arousal_change = abs(node2.emotional_arousal - node1.emotional_arousal)
                emotions_change.append(valence_change + arousal_change)
                
                # Calculate temporal proximity
                delta = (node2.timestamp - node1.timestamp).total_seconds()
                proximity = max(0.0, 1.0 - min(1.0, delta / 3600))  # Within 1 hour is close
                time_proximity.append(proximity)
            
            # If significant emotional changes occur shortly after each other, might be causal
            if emotions_change and time_proximity:
                emotion_score = sum(emotions_change) / len(emotions_change)
                proximity_score = sum(time_proximity) / len(time_proximity)
                
                return 0.6 * emotion_score + 0.4 * proximity_score
            
            return 0.2  # Weak causality match
        
        # Return average causal association strength
        return causal_score / causal_count
    
    #
    # Advanced pattern matchers
    #
    
    def _match_graph_isomorphism(self, nodes: List[MemoryNode], 
                               pattern: PatternTemplate, **kwargs) -> float:
        """Match graph isomorphism pattern (structural similarity)."""
        if len(nodes) < 2:
            return 0.0
        
        # This is a placeholder for a proper graph isomorphism algorithm
        # In a complete implementation, this would:
        # 1. Create a graph from the memory nodes and their connections
        # 2. Create a graph from the pattern template's structure
        # 3. Compute a graph similarity score (like graph edit distance)
        
        # For now, return a partial match score based on node count and connectivity
        # Calculate connection density
        connections = 0
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # Check for any association
                assoc = MemoryAssociation.query.filter(
                    ((MemoryAssociation.source_id == node1.id) & 
                     (MemoryAssociation.target_id == node2.id)) |
                    ((MemoryAssociation.source_id == node2.id) & 
                     (MemoryAssociation.target_id == node1.id))
                ).first()
                
                if assoc:
                    connections += 1
        
        max_connections = (len(nodes) * (len(nodes) - 1)) / 2
        connectivity = connections / max(1, max_connections)
        
        # Return connectivity score (more connected = more likely to match a pattern)
        return min(0.8, 0.4 + 0.6 * connectivity)  # Cap at 0.8 for placeholder
    
    def _match_recursive_similarity(self, nodes: List[MemoryNode], 
                                  pattern: PatternTemplate, **kwargs) -> float:
        """Match recursive similarity pattern (similar structure at different levels)."""
        if len(nodes) < 4:  # Need enough nodes to detect recursion
            return 0.0
        
        # This is a placeholder for a recursive pattern matcher
        # In a complete implementation, this would:
        # 1. Identify patterns at different scales/levels
        # 2. Compare patterns across levels for self-similarity
        # 3. Quantify the recursive nature of the pattern
        
        # For now, simulate recursive pattern detection
        recursive_score = random.uniform(0.4, 0.9)  # Placeholder
        
        # Pattern structures often have specific node types and hierarchies
        # in a recursive system, so we'll check for that
        node_types = set(node.memory_type for node in nodes)
        
        # More diverse node types can indicate a more complex recursive pattern
        type_diversity = len(node_types) / len(nodes)
        
        # Adjust score based on diversity (more diversity = better recursion potential)
        adjusted_score = recursive_score * (0.7 + 0.3 * type_diversity)
        
        return min(1.0, adjusted_score)
    
    def _match_semantic_similarity(self, nodes: List[MemoryNode], 
                                 pattern: PatternTemplate, **kwargs) -> float:
        """Match semantic similarity pattern (similar meaning across different structures)."""
        if len(nodes) < 2:
            return 0.0
        
        # This is a placeholder for semantic similarity matching
        # In a complete implementation, this would:
        # 1. Extract semantic representations of each node
        # 2. Calculate semantic similarity using embeddings or other NLP techniques
        # 3. Return a normalized similarity score
        
        # For now, we'll approximate semantic similarity using available attributes
        
        # Get all node contexts
        contexts = [node.get_context() for node in nodes]
        
        # Calculate pairwise context similarities
        similarities = []
        for i, ctx1 in enumerate(contexts):
            for ctx2 in contexts[i+1:]:
                sim = self._calculate_context_similarity(ctx1, ctx2)
                similarities.append(sim)
        
        # Return average similarity
        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            # Adjust score to be slightly optimistic (semantic similarity is often higher)
            return min(1.0, avg_similarity * 1.2)
        
        return 0.5  # Neutral score if no context to compare

# Global instance
pattern_matcher = PatternMatcher()