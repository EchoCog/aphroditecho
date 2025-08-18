"""
Relation Graph System

Manages dynamic relationships and communication between agents in the AAR system.
Provides graph-based relationship modeling with adaptive weights and communication routing.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """Types of relationships between agents."""
    COLLABORATION = "collaboration"
    COMPETITION = "competition"
    COMMUNICATION = "communication"
    DEPENDENCY = "dependency"
    MENTOR_STUDENT = "mentor_student"
    PEER = "peer"
    RESOURCE_SHARING = "resource_sharing"
    TASK_COORDINATION = "task_coordination"
    KNOWLEDGE_EXCHANGE = "knowledge_exchange"


class RelationStatus(Enum):
    """Status of a relationship."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EVOLVING = "evolving"
    TERMINATING = "terminating"


@dataclass
class RelationMetrics:
    """Metrics for relationship performance."""
    interaction_count: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    trust_level: float = 0.5
    collaboration_score: float = 0.0
    communication_frequency: float = 0.0
    last_interaction: float = field(default_factory=time.time)
    relationship_age: float = 0.0


class Relation:
    """Represents a relationship between two agents."""
    
    def __init__(self,
                 relation_id: str,
                 source_agent_id: str,
                 target_agent_id: str,
                 relation_type: RelationType,
                 bidirectional: bool = True,
                 initial_weight: float = 0.5):
        self.id = relation_id
        self.source_agent_id = source_agent_id
        self.target_agent_id = target_agent_id
        self.relation_type = relation_type
        self.bidirectional = bidirectional
        self.weight = initial_weight
        self.status = RelationStatus.ACTIVE
        
        self.metrics = RelationMetrics()
        self.created_at = time.time()
        self.last_update = time.time()
        
        # Relationship state
        self.properties = {}
        self.interaction_history = []
        self.max_history_length = 100
        
        # Evolution tracking
        self.evolution_data = {
            'weight_history': [initial_weight],
            'adaptation_events': [],
            'performance_trend': []
        }
        
        logger.debug(f"Created relation {self.id}: {source_agent_id} -> {target_agent_id} ({relation_type.value})")
    
    async def process_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an interaction through this relationship."""
        start_time = time.time()
        
        # Record interaction
        interaction = {
            'timestamp': start_time,
            'type': interaction_data.get('type', 'general'),
            'source': interaction_data.get('source', self.source_agent_id),
            'target': interaction_data.get('target', self.target_agent_id),
            'data': interaction_data.get('data', {}),
            'success': None  # Will be set based on result
        }
        
        try:
            # Process based on relation type
            result = await self._process_by_type(interaction_data)
            
            interaction['success'] = True
            interaction['result'] = result
            
            # Update metrics
            await self._update_metrics(start_time, True, result)
            
            # Adapt relationship weight based on success
            await self._adapt_weight(result.get('effectiveness', 0.5))
            
        except Exception as e:
            logger.error(f"Error processing interaction in relation {self.id}: {e}")
            interaction['success'] = False
            interaction['error'] = str(e)
            
            await self._update_metrics(start_time, False, {})
            await self._adapt_weight(-0.1)  # Penalize for errors
            
            result = {'error': str(e)}
        
        # Store interaction history
        self.interaction_history.append(interaction)
        if len(self.interaction_history) > self.max_history_length:
            self.interaction_history = self.interaction_history[-self.max_history_length:]
        
        self.last_update = time.time()
        
        return result
    
    async def _process_by_type(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process interaction based on relation type."""
        if self.relation_type == RelationType.COLLABORATION:
            return await self._process_collaboration(interaction_data)
        elif self.relation_type == RelationType.COMPETITION:
            return await self._process_competition(interaction_data)
        elif self.relation_type == RelationType.COMMUNICATION:
            return await self._process_communication(interaction_data)
        elif self.relation_type == RelationType.DEPENDENCY:
            return await self._process_dependency(interaction_data)
        elif self.relation_type == RelationType.MENTOR_STUDENT:
            return await self._process_mentor_student(interaction_data)
        elif self.relation_type == RelationType.RESOURCE_SHARING:
            return await self._process_resource_sharing(interaction_data)
        elif self.relation_type == RelationType.TASK_COORDINATION:
            return await self._process_task_coordination(interaction_data)
        elif self.relation_type == RelationType.KNOWLEDGE_EXCHANGE:
            return await self._process_knowledge_exchange(interaction_data)
        else:
            return await self._process_generic(interaction_data)
    
    async def _process_collaboration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process collaboration interaction."""
        task = data.get('task', {})
        contribution = data.get('contribution', {})
        
        # Calculate collaboration effectiveness
        effectiveness = min(1.0, self.weight + 0.1)  # Stronger relations are more effective
        
        return {
            'type': 'collaboration',
            'task_id': task.get('id'),
            'effectiveness': effectiveness,
            'contribution_accepted': True,
            'synergy_bonus': effectiveness * 0.2
        }
    
    async def _process_competition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process competitive interaction."""
        challenge = data.get('challenge', {})
        
        # In competition, moderate weight indicates healthy rivalry
        competitiveness = 1.0 - abs(self.weight - 0.5) * 2
        
        return {
            'type': 'competition',
            'challenge_id': challenge.get('id'),
            'competitiveness': competitiveness,
            'motivation_boost': competitiveness * 0.3
        }
    
    async def _process_communication(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process communication interaction."""
        message = data.get('message', '')
        channel = data.get('channel', 'direct')
        
        # Communication effectiveness based on trust and relationship strength
        clarity = self.metrics.trust_level * self.weight
        
        return {
            'type': 'communication',
            'message_delivered': True,
            'clarity_score': clarity,
            'channel': channel,
            'trust_factor': self.metrics.trust_level
        }
    
    async def _process_dependency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dependency relationship."""
        request = data.get('request', {})
        
        # Dependencies get stronger with successful interactions
        reliability = self.metrics.success_rate * self.weight
        
        return {
            'type': 'dependency',
            'request_fulfilled': reliability > 0.6,
            'reliability_score': reliability,
            'dependency_strength': self.weight
        }
    
    async def _process_mentor_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process mentor-student interaction."""
        learning_data = data.get('learning', {})
        
        # Mentoring effectiveness improves over time
        mentoring_quality = min(1.0, self.weight + (self.metrics.relationship_age / 1000.0))
        
        return {
            'type': 'mentoring',
            'knowledge_transferred': mentoring_quality > 0.4,
            'learning_effectiveness': mentoring_quality,
            'skill_improvement': mentoring_quality * 0.15
        }
    
    async def _process_resource_sharing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process resource sharing interaction."""
        resource_request = data.get('resource_request', {})
        
        # Resource sharing based on trust and relationship strength
        sharing_willingness = self.metrics.trust_level * self.weight
        
        return {
            'type': 'resource_sharing',
            'resources_shared': sharing_willingness > 0.5,
            'sharing_efficiency': sharing_willingness,
            'resource_value': resource_request.get('value', 1.0) * sharing_willingness
        }
    
    async def _process_task_coordination(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process task coordination interaction."""
        coordination_request = data.get('coordination', {})
        
        # Coordination effectiveness based on communication history
        coordination_quality = (self.metrics.communication_frequency / 10.0) * self.weight
        coordination_quality = min(1.0, coordination_quality)
        
        return {
            'type': 'task_coordination',
            'coordination_successful': coordination_quality > 0.4,
            'synchronization_level': coordination_quality,
            'efficiency_gain': coordination_quality * 0.25
        }
    
    async def _process_knowledge_exchange(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process knowledge exchange interaction."""
        knowledge_data = data.get('knowledge', {})
        
        # Knowledge exchange based on compatibility and trust
        exchange_quality = (self.metrics.trust_level + self.weight) / 2
        
        return {
            'type': 'knowledge_exchange',
            'knowledge_accepted': exchange_quality > 0.3,
            'exchange_quality': exchange_quality,
            'mutual_benefit': exchange_quality * 0.2
        }
    
    async def _process_generic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process generic interaction."""
        return {
            'type': 'generic',
            'processed': True,
            'effectiveness': self.weight,
            'relationship_strength': self.weight
        }
    
    async def _update_metrics(self, start_time: float, success: bool, result: Dict[str, Any]) -> None:
        """Update relationship metrics."""
        response_time = time.time() - start_time
        
        # Update interaction count and success rate
        total_interactions = self.metrics.interaction_count
        current_success_rate = self.metrics.success_rate
        
        new_success_rate = ((current_success_rate * total_interactions) + (1.0 if success else 0.0)) / (total_interactions + 1)
        self.metrics.success_rate = new_success_rate
        
        # Update average response time
        current_avg_time = self.metrics.avg_response_time
        new_avg_time = ((current_avg_time * total_interactions) + response_time) / (total_interactions + 1)
        self.metrics.avg_response_time = new_avg_time
        
        # Update interaction count
        self.metrics.interaction_count += 1
        
        # Update trust level based on success
        if success:
            self.metrics.trust_level = min(1.0, self.metrics.trust_level + 0.01)
        else:
            self.metrics.trust_level = max(0.0, self.metrics.trust_level - 0.05)
        
        # Update communication frequency (interactions per hour)
        time_since_creation = time.time() - self.created_at
        self.metrics.communication_frequency = self.metrics.interaction_count / max(time_since_creation / 3600.0, 0.1)
        
        # Update collaboration score based on result
        if 'effectiveness' in result:
            effectiveness = result['effectiveness']
            current_collab = self.metrics.collaboration_score
            self.metrics.collaboration_score = (current_collab * 0.9) + (effectiveness * 0.1)
        
        # Update relationship age
        self.metrics.relationship_age = time.time() - self.created_at
        self.metrics.last_interaction = time.time()
    
    async def _adapt_weight(self, performance_delta: float) -> None:
        """Adapt relationship weight based on performance."""
        old_weight = self.weight
        
        # Adapt weight based on performance
        adaptation_rate = 0.1
        self.weight += performance_delta * adaptation_rate
        self.weight = max(0.0, min(1.0, self.weight))  # Clamp to [0, 1]
        
        # Record weight evolution
        self.evolution_data['weight_history'].append(self.weight)
        
        # Limit history length
        if len(self.evolution_data['weight_history']) > 1000:
            self.evolution_data['weight_history'] = self.evolution_data['weight_history'][-1000:]
        
        # Record adaptation event if significant change
        if abs(self.weight - old_weight) > 0.01:
            self.evolution_data['adaptation_events'].append({
                'timestamp': time.time(),
                'old_weight': old_weight,
                'new_weight': self.weight,
                'performance_delta': performance_delta
            })
    
    def calculate_relationship_strength(self) -> float:
        """Calculate overall relationship strength."""
        # Combine multiple factors
        factors = [
            self.weight * 0.3,
            self.metrics.trust_level * 0.2,
            self.metrics.success_rate * 0.2,
            self.metrics.collaboration_score * 0.15,
            min(1.0, self.metrics.communication_frequency / 5.0) * 0.15
        ]
        
        return sum(factors)
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive relationship status."""
        return {
            'id': self.id,
            'source_agent_id': self.source_agent_id,
            'target_agent_id': self.target_agent_id,
            'relation_type': self.relation_type.value,
            'status': self.status.value,
            'bidirectional': self.bidirectional,
            'weight': self.weight,
            'relationship_strength': self.calculate_relationship_strength(),
            'metrics': {
                'interaction_count': self.metrics.interaction_count,
                'success_rate': self.metrics.success_rate,
                'avg_response_time': self.metrics.avg_response_time,
                'trust_level': self.metrics.trust_level,
                'collaboration_score': self.metrics.collaboration_score,
                'communication_frequency': self.metrics.communication_frequency,
                'relationship_age': self.metrics.relationship_age
            },
            'created_at': self.created_at,
            'last_update': self.last_update,
            'recent_interactions': len(self.interaction_history),
            'properties': self.properties
        }


class RelationGraph:
    """Manages the graph of relationships between agents."""
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.graph = nx.MultiDiGraph()  # Supports multiple relations between same agents
        self.relations: Dict[str, Relation] = {}
        
        # Graph analysis cache
        self._analysis_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 60.0  # Cache TTL in seconds
        
        # Performance tracking
        self.total_relations_created = 0
        self.total_interactions_processed = 0
        self.system_start_time = time.time()
        
        logger.info(f"Relation Graph initialized with max depth {max_depth}")
    
    async def create_relation(self,
                            source_agent_id: str,
                            target_agent_id: str,
                            relation_type: RelationType,
                            bidirectional: bool = True,
                            initial_weight: float = 0.5,
                            properties: Optional[Dict[str, Any]] = None) -> str:
        """Create a new relationship between agents."""
        relation_id = f"rel_{uuid.uuid4().hex[:8]}"
        
        # Create relation object
        relation = Relation(
            relation_id=relation_id,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            relation_type=relation_type,
            bidirectional=bidirectional,
            initial_weight=initial_weight
        )
        
        if properties:
            relation.properties.update(properties)
        
        # Add to graph
        self.graph.add_edge(
            source_agent_id,
            target_agent_id,
            relation_id=relation_id,
            weight=initial_weight,
            relation_type=relation_type.value,
            bidirectional=bidirectional
        )
        
        # Add reverse edge if bidirectional
        if bidirectional:
            self.graph.add_edge(
                target_agent_id,
                source_agent_id,
                relation_id=relation_id,
                weight=initial_weight,
                relation_type=relation_type.value,
                bidirectional=True
            )
        
        # Store relation
        self.relations[relation_id] = relation
        self.total_relations_created += 1
        
        # Invalidate cache
        self._invalidate_cache()
        
        logger.info(f"Created relation {relation_id}: {source_agent_id} <-> {target_agent_id} ({relation_type.value})")
        return relation_id
    
    async def remove_relation(self, relation_id: str) -> bool:
        """Remove a relationship."""
        if relation_id not in self.relations:
            logger.warning(f"Relation {relation_id} not found for removal")
            return False
        
        relation = self.relations[relation_id]
        
        # Remove from graph
        try:
            self.graph.remove_edge(relation.source_agent_id, relation.target_agent_id)
            if relation.bidirectional:
                self.graph.remove_edge(relation.target_agent_id, relation.source_agent_id)
        except Exception as e:
            logger.warning(f"Error removing edges for relation {relation_id}: {e}")
        
        # Remove relation
        del self.relations[relation_id]
        
        # Invalidate cache
        self._invalidate_cache()
        
        logger.info(f"Removed relation {relation_id}")
        return True
    
    async def process_interaction(self, 
                                source_agent_id: str, 
                                target_agent_id: str,
                                interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an interaction between two agents."""
        # Find direct relations between agents
        relations = self.get_relations_between_agents(source_agent_id, target_agent_id)
        
        if not relations:
            # Create a default communication relation if none exists
            relation_id = await self.create_relation(
                source_agent_id, 
                target_agent_id, 
                RelationType.COMMUNICATION,
                initial_weight=0.1
            )
            relations = [self.relations[relation_id]]
        
        # Process interaction through all applicable relations
        results = []
        for relation in relations:
            try:
                result = await relation.process_interaction(interaction_data)
                results.append({
                    'relation_id': relation.id,
                    'relation_type': relation.relation_type.value,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error processing interaction in relation {relation.id}: {e}")
                results.append({
                    'relation_id': relation.id,
                    'relation_type': relation.relation_type.value,
                    'result': {'error': str(e)}
                })
        
        self.total_interactions_processed += 1
        self._invalidate_cache()
        
        return {
            'source_agent_id': source_agent_id,
            'target_agent_id': target_agent_id,
            'processed_relations': len(results),
            'relation_results': results,
            'overall_success': all('error' not in r['result'] for r in results)
        }
    
    def get_relations_between_agents(self, agent1_id: str, agent2_id: str) -> List[Relation]:
        """Get all relations between two specific agents."""
        relations = []
        
        # Check direct relations
        if self.graph.has_edge(agent1_id, agent2_id):
            edge_data = self.graph.get_edge_data(agent1_id, agent2_id)
            for edge_key, edge_attrs in edge_data.items():
                relation_id = edge_attrs.get('relation_id')
                if relation_id in self.relations:
                    relations.append(self.relations[relation_id])
        
        return relations
    
    def get_agent_relations(self, agent_id: str) -> List[Relation]:
        """Get all relations for a specific agent."""
        relations = []
        
        for relation in self.relations.values():
            if relation.source_agent_id == agent_id or relation.target_agent_id == agent_id:
                relations.append(relation)
        
        return relations
    
    def find_path(self, source_agent_id: str, target_agent_id: str, max_depth: Optional[int] = None) -> List[str]:
        """Find shortest path between two agents."""
        if max_depth is None:
            max_depth = self.max_depth
        
        try:
            path = nx.shortest_path(
                self.graph, 
                source=source_agent_id, 
                target=target_agent_id,
                weight='weight'
            )
            
            if len(path) - 1 <= max_depth:  # Path length is number of edges
                return path
            else:
                return []
        
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def get_connected_agents(self, agent_id: str, max_depth: int = 1) -> Dict[str, int]:
        """Get all agents connected to a specific agent within max_depth."""
        connected = {}
        
        try:
            # Use BFS to find connected agents
            visited = {agent_id}
            queue = [(agent_id, 0)]
            
            while queue:
                current_agent, depth = queue.pop(0)
                
                if depth >= max_depth:
                    continue
                
                # Get neighbors
                for neighbor in self.graph.neighbors(current_agent):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        connected[neighbor] = depth + 1
                        queue.append((neighbor, depth + 1))
            
        except Exception as e:
            logger.error(f"Error finding connected agents for {agent_id}: {e}")
        
        return connected
    
    def calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate centrality metrics for all agents."""
        cache_key = 'centrality_metrics'
        
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]
        
        metrics = {}
        
        try:
            # Calculate various centrality measures
            degree_centrality = nx.degree_centrality(self.graph)
            closeness_centrality = nx.closeness_centrality(self.graph)
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            
            # Combine metrics for each agent
            all_agents = set(degree_centrality.keys())
            
            for agent_id in all_agents:
                metrics[agent_id] = {
                    'degree_centrality': degree_centrality.get(agent_id, 0.0),
                    'closeness_centrality': closeness_centrality.get(agent_id, 0.0),
                    'betweenness_centrality': betweenness_centrality.get(agent_id, 0.0)
                }
                
                # Calculate composite influence score
                influence_score = (
                    metrics[agent_id]['degree_centrality'] * 0.4 +
                    metrics[agent_id]['closeness_centrality'] * 0.3 +
                    metrics[agent_id]['betweenness_centrality'] * 0.3
                )
                metrics[agent_id]['influence_score'] = influence_score
        
        except Exception as e:
            logger.error(f"Error calculating centrality metrics: {e}")
            metrics = {}
        
        self._analysis_cache[cache_key] = metrics
        return metrics
    
    def detect_communities(self) -> Dict[str, List[str]]:
        """Detect communities in the agent relationship graph."""
        cache_key = 'communities'
        
        if self._is_cache_valid(cache_key):
            return self._analysis_cache[cache_key]
        
        communities = {}
        
        try:
            # Convert to undirected graph for community detection
            undirected_graph = self.graph.to_undirected()
            
            # Use Louvain community detection algorithm if available
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(undirected_graph)
                
                # Group agents by community
                for agent_id, community_id in partition.items():
                    community_name = f"community_{community_id}"
                    if community_name not in communities:
                        communities[community_name] = []
                    communities[community_name].append(agent_id)
            
            except ImportError:
                logger.warning("Advanced community detection requires python-louvain package")
                # Simple fallback: group all agents as single community
                communities = {'single_community': list(self.graph.nodes())}
        
        except Exception as e:
            logger.error(f"Error detecting communities: {e}")
            communities = {'single_community': list(self.graph.nodes())}
        
        self._analysis_cache[cache_key] = communities
        return communities
    
    async def update_relationships(self, agents: List[Dict[str, Any]], performance_score: float) -> None:
        """Update relationships based on agent performance."""
        if len(agents) < 2:
            return
        
        logger.debug(f"Updating relationships for {len(agents)} agents with performance score {performance_score}")
        
        # Update relationships between all agent pairs
        for i, agent1 in enumerate(agents):
            for agent2 in agents[i+1:]:
                agent1_id = agent1.get('id', str(agent1))
                agent2_id = agent2.get('id', str(agent2))
                
                # Get existing relations
                relations = self.get_relations_between_agents(agent1_id, agent2_id)
                
                if relations:
                    # Update existing relations
                    for relation in relations:
                        # Performance affects weight adaptation
                        performance_delta = (performance_score - 0.5) * 0.1
                        await relation._adapt_weight(performance_delta)
                        logger.debug(f"Updated relation {relation.id} with delta {performance_delta}")
                else:
                    # Create new relation for multi-agent interactions (more lenient threshold)
                    if performance_score >= 0.3:  # Lower threshold for initial relationship formation
                        relation_type = RelationType.COLLABORATION if performance_score > 0.6 else RelationType.COMMUNICATION
                        initial_weight = max(0.1, performance_score * 0.5)
                        
                        relation_id = await self.create_relation(
                            agent1_id, 
                            agent2_id, 
                            relation_type,
                            initial_weight=initial_weight
                        )
                        
                        logger.info(f"Created new {relation_type.value} relation {relation_id} between {agent1_id} and {agent2_id}")
        
        # Log final statistics
        stats = self.get_graph_stats()
        logger.info(f"Relationship update complete. Total relations: {stats['graph_topology']['total_relations']}")
    
    async def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple agents using relationship weights."""
        if not results:
            return {'error': 'No results to aggregate'}
        
        if len(results) == 1:
            return results[0]
        
        # Weight results based on agent relationships
        weighted_results = []
        total_weight = 0.0
        
        for i, result in enumerate(results):
            agent_id = result.get('agent_id', f'agent_{i}')
            
            # Calculate agent influence based on relationships
            agent_relations = self.get_agent_relations(agent_id)
            relationship_strength = sum(r.calculate_relationship_strength() for r in agent_relations)
            
            # Use relationship strength as weight (with minimum weight)
            weight = max(0.1, relationship_strength / max(len(agent_relations), 1))
            
            weighted_results.append({
                'result': result,
                'weight': weight,
                'agent_id': agent_id
            })
            total_weight += weight
        
        # Normalize weights
        for wr in weighted_results:
            wr['normalized_weight'] = wr['weight'] / max(total_weight, 0.1)
        
        # Calculate weighted consensus
        consensus_confidence = sum(
            wr['result'].get('confidence', 0.5) * wr['normalized_weight'] 
            for wr in weighted_results
        )
        
        # Select primary result (highest weighted)
        primary_result = max(weighted_results, key=lambda x: x['normalized_weight'])
        
        return {
            'primary_result': primary_result['result'],
            'consensus_confidence': consensus_confidence,
            'contributing_agents': len(results),
            'relationship_weighted': True,
            'weight_distribution': {
                wr['agent_id']: wr['normalized_weight'] 
                for wr in weighted_results
            }
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._analysis_cache:
            return False
        
        return time.time() - self._cache_timestamp < self._cache_ttl
    
    def _invalidate_cache(self) -> None:
        """Invalidate analysis cache."""
        self._analysis_cache.clear()
        self._cache_timestamp = time.time()
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()
        
        # Calculate density
        max_edges = node_count * (node_count - 1)  # For directed graph
        density = edge_count / max(max_edges, 1)
        
        # Relation type distribution
        relation_types = {}
        for relation in self.relations.values():
            rel_type = relation.relation_type.value
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        # Average relationship metrics
        if self.relations:
            avg_weight = sum(r.weight for r in self.relations.values()) / len(self.relations)
            avg_trust = sum(r.metrics.trust_level for r in self.relations.values()) / len(self.relations)
            avg_success_rate = sum(r.metrics.success_rate for r in self.relations.values()) / len(self.relations)
        else:
            avg_weight = avg_trust = avg_success_rate = 0.0
        
        return {
            'graph_topology': {
                'node_count': node_count,
                'edge_count': edge_count,
                'density': density,
                'total_relations': len(self.relations)
            },
            'relation_types': relation_types,
            'average_metrics': {
                'avg_relationship_weight': avg_weight,
                'avg_trust_level': avg_trust,
                'avg_success_rate': avg_success_rate
            },
            'system_stats': {
                'total_relations_created': self.total_relations_created,
                'total_interactions_processed': self.total_interactions_processed,
                'system_uptime': time.time() - self.system_start_time
            }
        }
    
    def get_relation_status(self, relation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific relation."""
        if relation_id not in self.relations:
            return None
        
        return self.relations[relation_id].get_status_info()
    
    async def optimize_graph(self) -> Dict[str, Any]:
        """Optimize the relationship graph by removing weak/inactive relations."""
        optimization_stats = {
            'relations_before': len(self.relations),
            'relations_removed': 0,
            'weak_relations_strengthened': 0,
            'inactive_relations_reactivated': 0
        }
        
        relations_to_remove = []
        current_time = time.time()
        
        for relation_id, relation in self.relations.items():
            # Remove very weak relations that haven't been used recently
            if (relation.weight < 0.1 and 
                current_time - relation.metrics.last_interaction > 3600):  # 1 hour
                relations_to_remove.append(relation_id)
            
            # Strengthen active, successful relations
            elif (relation.metrics.success_rate > 0.8 and 
                  relation.metrics.interaction_count > 10):
                old_weight = relation.weight
                relation.weight = min(1.0, relation.weight + 0.05)
                if relation.weight > old_weight:
                    optimization_stats['weak_relations_strengthened'] += 1
            
            # Reactivate dormant but historically good relations
            elif (relation.status == RelationStatus.INACTIVE and
                  relation.metrics.success_rate > 0.7):
                relation.status = RelationStatus.ACTIVE
                optimization_stats['inactive_relations_reactivated'] += 1
        
        # Remove weak relations
        for relation_id in relations_to_remove:
            await self.remove_relation(relation_id)
            optimization_stats['relations_removed'] += 1
        
        optimization_stats['relations_after'] = len(self.relations)
        
        logger.info(f"Graph optimization complete: {optimization_stats}")
        return optimization_stats
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the relation graph."""
        logger.info("Shutting down Relation Graph...")
        
        # Clear all data structures
        self.graph.clear()
        self.relations.clear()
        self._analysis_cache.clear()
        
        logger.info("Relation Graph shutdown complete")