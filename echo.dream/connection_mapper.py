"""
Dynamic Interdisciplinary Connection Mapper

This module provides tools for mapping and visualizing connections between
different knowledge domains and concepts, enabling interdisciplinary exploration.
"""

import json
import logging
import uuid
import re
from collections import defaultdict
import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)

# Singleton instance
_CONNECTION_MAPPER = None

def get_connection_mapper():
    """Get the singleton instance of the connection mapper."""
    global _CONNECTION_MAPPER
    if _CONNECTION_MAPPER is None:
        _CONNECTION_MAPPER = DynamicConnectionMapper()
    return _CONNECTION_MAPPER

class KnowledgeDomain:
    """Represents a knowledge domain or academic discipline."""
    
    def __init__(self, name, description=None, domain_type='general', parent_domain=None, attributes=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description or ""
        self.domain_type = domain_type or "general"
        self.parent_domain_id = parent_domain
        self.attributes = attributes or {}
        self.concepts = {}  # Map of concept ID to concept data
        self.connections = {}  # Map of target domain ID to connection data
        self.terminology = set()  # Domain-specific terminology
        self.created_at = None  # Will be set by mapper
        self.updated_at = None  # Will be set by mapper
    
    def add_concept(self, concept_id, concept_data):
        """Add a concept to this domain."""
        self.concepts[concept_id] = concept_data
        
    def add_connection(self, target_domain_id, connection_data):
        """Add a connection to another domain."""
        self.connections[target_domain_id] = connection_data
        
    def add_terminology(self, terms):
        """Add domain-specific terminology."""
        if isinstance(terms, str):
            self.terminology.add(terms)
        elif isinstance(terms, (list, set)):
            self.terminology.update(terms)
            
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain_type": self.domain_type,
            "parent_domain_id": self.parent_domain_id,
            "attributes": self.attributes,
            "terminology": list(self.terminology),
            "concept_count": len(self.concepts),
            "connection_count": len(self.connections),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class ConceptNode:
    """Represents a concept node in the knowledge graph."""
    
    def __init__(self, name, domain_id=None, description=None, node_type='concept', attributes=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.domain_id = domain_id
        self.description = description or ""
        self.node_type = node_type or "concept"
        self.attributes = attributes or {}
        self.connections = {}  # Map of target concept ID to connection data
        self.vector = None  # Optional vector representation
        self.created_at = None  # Will be set by mapper
        self.updated_at = None  # Will be set by mapper
    
    def add_connection(self, target_concept_id, connection_data):
        """Add a connection to another concept."""
        self.connections[target_concept_id] = connection_data
        
    def set_vector(self, vector):
        """Set the vector representation of this concept."""
        self.vector = vector
        
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "domain_id": self.domain_id,
            "description": self.description,
            "node_type": self.node_type,
            "attributes": self.attributes,
            "has_vector": self.vector is not None,
            "connection_count": len(self.connections),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
    def similarity(self, other_concept):
        """Calculate similarity to another concept."""
        if self.vector is None or other_concept.vector is None:
            return 0.0
            
        # Cosine similarity
        dot_product = np.dot(self.vector, other_concept.vector)
        norm_a = np.linalg.norm(self.vector)
        norm_b = np.linalg.norm(other_concept.vector)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)

class DynamicConnectionMapper:
    """
    Main class for the Dynamic Interdisciplinary Connection Mapper.
    
    This class provides tools for:
    - Creating and managing knowledge domains
    - Creating and managing concepts within domains
    - Establishing connections between domains and concepts
    - Searching and visualizing the knowledge graph
    - Discovering interdisciplinary patterns
    """
    
    def __init__(self):
        """Initialize the connection mapper."""
        self.domains = {}  # Map of domain ID to KnowledgeDomain objects
        self.concepts = {}  # Map of concept ID to ConceptNode objects
        self.domain_graph = nx.DiGraph()  # NetworkX graph for domain connections
        self.concept_graph = nx.DiGraph()  # NetworkX graph for concept connections
        self.domain_index = defaultdict(list)  # Inverted index for domain search
        self.concept_index = defaultdict(list)  # Inverted index for concept search
        self.discovered_patterns = []  # Discovered connection patterns
        
        # Initialize default domain types
        self.domain_types = [
            "general", "specialized", "interdisciplinary", 
            "applied", "theoretical", "emerging"
        ]
        
        # Initialize default relation types
        self.relation_types = [
            "related", "part_of", "contains", "depends_on", 
            "influences", "derived_from", "opposes"
        ]
        
        # Load domains and concepts from database
        self._load_from_database()
        
        logger.info("Dynamic Connection Mapper initialized")
        
    def _load_from_database(self):
        """Load domains and concepts from database."""
        try:
            # Import models here to avoid circular imports
            from models_mapper import KnowledgeDomain as DBKnowledgeDomain
            from models_mapper import DomainConnection
            
            # Load domains
            db_domains = DBKnowledgeDomain.query.all()
            for db_domain in db_domains:
                domain = KnowledgeDomain(
                    name=db_domain.name,
                    description=db_domain.description,
                    domain_type=db_domain.domain_type,
                    attributes=db_domain.attributes
                )
                domain.id = db_domain.id  # Use the same ID from the database
                domain.created_at = db_domain.created_at
                domain.updated_at = db_domain.updated_at
                
                # Store the domain
                self.domains[domain.id] = domain
                
                # Add to graph
                self.domain_graph.add_node(
                    domain.id, 
                    name=domain.name, 
                    domain_type=domain.domain_type,
                    description=domain.description
                )
                
                # Index the domain
                self._index_domain(domain)
                
            # Load domain connections
            db_connections = DomainConnection.query.all()
            for db_connection in db_connections:
                source_id = db_connection.source_domain_id
                target_id = db_connection.target_domain_id
                
                # Skip if either source or target domain not found
                if source_id not in self.domains or target_id not in self.domains:
                    continue
                    
                # Add connection to source domain
                self.domains[source_id].add_connection(target_id, {
                    "id": db_connection.id,
                    "source_domain_id": source_id,
                    "target_domain_id": target_id,
                    "connection_type": db_connection.connection_type,
                    "strength": db_connection.strength,
                    "description": db_connection.description,
                    "bidirectional": db_connection.bidirectional,
                    "attributes": db_connection.attributes or {},
                    "created_at": db_connection.created_at,
                    "updated_at": db_connection.updated_at
                })
                
                # Add edge to graph
                self.domain_graph.add_edge(
                    source_id, 
                    target_id,
                    id=db_connection.id,
                    type=db_connection.connection_type,
                    strength=db_connection.strength,
                    bidirectional=db_connection.bidirectional,
                    description=db_connection.description
                )
            
            logger.info(f"Loaded {len(self.domains)} domains and {len(db_connections)} domain connections from database")
            
            # Load concepts and concept connections similarly
            # (omitted for brevity but would follow the same pattern)
            
        except Exception as e:
            logger.error(f"Error loading from database: {str(e)}")
            # Continue with empty state rather than failing
        
    def create_domain(self, name, description=None, domain_type='general', 
                     parent_domain=None, attributes=None) -> str:
        """
        Create a new knowledge domain.
        
        Args:
            name: Name of the domain
            description: Optional description
            domain_type: Type of domain (general, specialized, etc.)
            parent_domain: Optional parent domain ID
            attributes: Optional dictionary of attributes
            
        Returns:
            The ID of the created domain
        """
        domain = KnowledgeDomain(
            name=name,
            description=description,
            domain_type=domain_type,
            parent_domain=parent_domain,
            attributes=attributes
        )
        
        # Set timestamp using datetime from the database
        import datetime
        domain.created_at = datetime.datetime.now()
        domain.updated_at = domain.created_at
        
        # Store the domain
        self.domains[domain.id] = domain
        
        # Add to graph
        self.domain_graph.add_node(
            domain.id, 
            name=name, 
            domain_type=domain_type,
            description=description
        )
        
        # If parent domain specified, create parent-child connection
        if parent_domain and parent_domain in self.domains:
            self.connect_domains(
                domain.id, 
                parent_domain, 
                connection_type='child_of',
                bidirectional=False
            )
            self.connect_domains(
                parent_domain, 
                domain.id, 
                connection_type='parent_of',
                bidirectional=False
            )
        
        # Update the search index
        self._index_domain(domain)
        
        logger.info(f"Created domain '{name}' with ID {domain.id}")
        return domain.id

    def create_concept(self, name, domain_id, description=None, 
                      node_type='concept', attributes=None) -> str:
        """
        Create a new concept within a domain.
        
        Args:
            name: Name of the concept
            domain_id: ID of the domain this concept belongs to
            description: Optional description
            node_type: Type of concept (concept, entity, process, etc.)
            attributes: Optional dictionary of attributes
            
        Returns:
            The ID of the created concept
        """
        if domain_id not in self.domains:
            raise ValueError(f"Domain with ID {domain_id} not found")
            
        concept = ConceptNode(
            name=name,
            domain_id=domain_id,
            description=description,
            node_type=node_type,
            attributes=attributes
        )
        
        # Set timestamp using datetime from the database
        import datetime
        concept.created_at = datetime.datetime.now()
        concept.updated_at = concept.created_at
        
        # Store the concept
        self.concepts[concept.id] = concept
        
        # Add concept to domain
        domain = self.domains[domain_id]
        domain.add_concept(concept.id, {
            "id": concept.id,
            "name": name,
            "description": description,
            "domain_id": domain_id,
            "concept_type": node_type,
            "importance": 0.5,  # Default importance
            "attributes": attributes,
            "created_at": concept.created_at,
            "updated_at": concept.updated_at
        })
        
        # Add to graph
        self.concept_graph.add_node(
            concept.id, 
            name=name, 
            domain_id=domain_id,
            node_type=node_type,
            description=description
        )
        
        # Update the search index
        self._index_concept(concept)
        
        logger.info(f"Created concept '{name}' with ID {concept.id} in domain {domain_id}")
        return concept.id
        
    def connect_domains(self, source_domain_id, target_domain_id, connection_type='related',
                       strength=0.5, description=None, bidirectional=True, attributes=None) -> str:
        """
        Create a connection between two domains.
        
        Args:
            source_domain_id: ID of the source domain
            target_domain_id: ID of the target domain
            connection_type: Type of connection
            strength: Connection strength (0.0 to 1.0)
            description: Optional description
            bidirectional: Whether the connection is bidirectional
            attributes: Optional dictionary of attributes
            
        Returns:
            The ID of the created connection
        """
        if source_domain_id not in self.domains:
            raise ValueError(f"Source domain with ID {source_domain_id} not found")
            
        if target_domain_id not in self.domains:
            raise ValueError(f"Target domain with ID {target_domain_id} not found")
            
        if source_domain_id == target_domain_id:
            raise ValueError("Cannot connect a domain to itself")
            
        # Create connection ID
        connection_id = str(uuid.uuid4())
        
        # Prepare connection data
        connection_data = {
            "id": connection_id,
            "source_domain_id": source_domain_id,
            "target_domain_id": target_domain_id,
            "connection_type": connection_type,
            "strength": strength,
            "description": description,
            "bidirectional": bidirectional,
            "attributes": attributes or {},
            "created_at": None,  # Will be set by database
            "updated_at": None   # Will be set by database
        }
        
        # Set timestamp using datetime from the database
        import datetime
        connection_data["created_at"] = datetime.datetime.now()
        connection_data["updated_at"] = connection_data["created_at"]
        
        # Add connection to source domain
        source_domain = self.domains[source_domain_id]
        source_domain.add_connection(target_domain_id, connection_data)
        
        # Add edge to graph
        self.domain_graph.add_edge(
            source_domain_id, 
            target_domain_id,
            id=connection_id,
            type=connection_type,
            strength=strength,
            bidirectional=bidirectional,
            description=description
        )
        
        # Create reverse connection if bidirectional
        if bidirectional:
            reverse_connection_id = str(uuid.uuid4())
            
            # Prepare reverse connection data
            reverse_connection_data = {
                "id": reverse_connection_id,
                "source_domain_id": target_domain_id,
                "target_domain_id": source_domain_id,
                "connection_type": connection_type,
                "strength": strength,
                "description": description,
                "bidirectional": False,  # To prevent infinite recursion
                "attributes": attributes or {},
                "created_at": connection_data["created_at"],
                "updated_at": connection_data["updated_at"]
            }
            
            # Add reverse connection to target domain
            target_domain = self.domains[target_domain_id]
            target_domain.add_connection(source_domain_id, reverse_connection_data)
            
            # Add reverse edge to graph
            self.domain_graph.add_edge(
                target_domain_id, 
                source_domain_id,
                id=reverse_connection_id,
                type=connection_type,
                strength=strength,
                bidirectional=False,
                description=description
            )
            
        logger.info(f"Created connection from domain {source_domain_id} to domain {target_domain_id}")
        return connection_id
        
    def connect_concepts(self, source_concept_id, target_concept_id, relation_type='related',
                        strength=0.5, description=None, bidirectional=True, attributes=None) -> str:
        """
        Create a connection between two concepts.
        
        Args:
            source_concept_id: ID of the source concept
            target_concept_id: ID of the target concept
            relation_type: Type of relation
            strength: Connection strength (0.0 to 1.0)
            description: Optional description
            bidirectional: Whether the connection is bidirectional
            attributes: Optional dictionary of attributes
            
        Returns:
            The ID of the created connection
        """
        if source_concept_id not in self.concepts:
            raise ValueError(f"Source concept with ID {source_concept_id} not found")
            
        if target_concept_id not in self.concepts:
            raise ValueError(f"Target concept with ID {target_concept_id} not found")
            
        if source_concept_id == target_concept_id:
            raise ValueError("Cannot connect a concept to itself")
            
        # Create connection ID
        connection_id = str(uuid.uuid4())
        
        # Prepare connection data
        connection_data = {
            "id": connection_id,
            "source_concept_id": source_concept_id,
            "target_concept_id": target_concept_id,
            "relation_type": relation_type,
            "strength": strength,
            "description": description,
            "bidirectional": bidirectional,
            "attributes": attributes or {},
            "created_at": None,  # Will be set by database
            "updated_at": None   # Will be set by database
        }
        
        # Set timestamp using datetime from the database
        import datetime
        connection_data["created_at"] = datetime.datetime.now()
        connection_data["updated_at"] = connection_data["created_at"]
        
        # Add connection to source concept
        source_concept = self.concepts[source_concept_id]
        source_concept.add_connection(target_concept_id, connection_data)
        
        # Add edge to graph
        self.concept_graph.add_edge(
            source_concept_id, 
            target_concept_id,
            id=connection_id,
            type=relation_type,
            strength=strength,
            bidirectional=bidirectional,
            description=description
        )
        
        # Create reverse connection if bidirectional
        if bidirectional:
            reverse_connection_id = str(uuid.uuid4())
            
            # Prepare reverse connection data
            reverse_connection_data = {
                "id": reverse_connection_id,
                "source_concept_id": target_concept_id,
                "target_concept_id": source_concept_id,
                "relation_type": relation_type,
                "strength": strength,
                "description": description,
                "bidirectional": False,  # To prevent infinite recursion
                "attributes": attributes or {},
                "created_at": connection_data["created_at"],
                "updated_at": connection_data["updated_at"]
            }
            
            # Add reverse connection to target concept
            target_concept = self.concepts[target_concept_id]
            target_concept.add_connection(source_concept_id, reverse_connection_data)
            
            # Add reverse edge to graph
            self.concept_graph.add_edge(
                target_concept_id, 
                source_concept_id,
                id=reverse_connection_id,
                type=relation_type,
                strength=strength,
                bidirectional=False,
                description=description
            )
            
        # If concepts are from different domains, create a domain connection if it doesn't exist
        source_domain_id = self.concepts[source_concept_id].domain_id
        target_domain_id = self.concepts[target_concept_id].domain_id
        
        if source_domain_id and target_domain_id and source_domain_id != target_domain_id:
            if source_domain_id in self.domains and target_domain_id in self.domains:
                # Check if domain connection already exists
                if target_domain_id not in self.domains[source_domain_id].connections:
                    self.connect_domains(
                        source_domain_id,
                        target_domain_id,
                        connection_type='concept_bridge',
                        strength=strength,
                        description=f"Bridge via concepts: {source_concept.name} -> {self.concepts[target_concept_id].name}",
                        bidirectional=bidirectional,
                        attributes={"bridged_by_concepts": [source_concept_id, target_concept_id]}
                    )
            
        logger.info(f"Created connection from concept {source_concept_id} to concept {target_concept_id}")
        return connection_id
    
    def search_domains(self, query, max_results=10):
        """
        Search for domains matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching domains
        """
        search_terms = self._extract_search_terms(query)
        
        # Create a score for each domain based on term matches
        domain_scores = defaultdict(float)
        
        for term in search_terms:
            if term in self.domain_index:
                for domain_id in self.domain_index[term]:
                    # Add to score based on match quality
                    domain_scores[domain_id] += 1.0
                    
                    # Bonus for exact name match
                    if term.lower() == self.domains[domain_id].name.lower():
                        domain_scores[domain_id] += 3.0
                        
                    # Bonus for domain type match
                    if term.lower() == self.domains[domain_id].domain_type.lower():
                        domain_scores[domain_id] += 2.0
        
        # Get the top scoring domains
        top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:max_results]
        
        # Return domain data
        results = []
        for domain_id, score in top_domains:
            if domain_id in self.domains:
                domain = self.domains[domain_id]
                domain_data = domain.to_dict()
                domain_data['search_score'] = score
                results.append(domain_data)
        
        return results
    
    def search_concepts(self, query, max_results=20):
        """
        Search for concepts matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching concepts
        """
        search_terms = self._extract_search_terms(query)
        
        # Create a score for each concept based on term matches
        concept_scores = defaultdict(float)
        
        for term in search_terms:
            if term in self.concept_index:
                for concept_id in self.concept_index[term]:
                    # Add to score based on match quality
                    concept_scores[concept_id] += 1.0
                    
                    # Bonus for exact name match
                    if term.lower() == self.concepts[concept_id].name.lower():
                        concept_scores[concept_id] += 3.0
                        
                    # Bonus for node type match
                    if term.lower() == self.concepts[concept_id].node_type.lower():
                        concept_scores[concept_id] += 2.0
        
        # Get the top scoring concepts
        top_concepts = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)[:max_results]
        
        # Return concept data
        results = []
        for concept_id, score in top_concepts:
            if concept_id in self.concepts:
                concept = self.concepts[concept_id]
                concept_data = concept.to_dict()
                concept_data['search_score'] = score
                
                # Add domain information
                if concept.domain_id and concept.domain_id in self.domains:
                    domain = self.domains[concept.domain_id]
                    concept_data['domain_name'] = domain.name
                    concept_data['domain_type'] = domain.domain_type
                
                results.append(concept_data)
        
        return results
        
    def find_interdisciplinary_paths(self, source_domain_id, target_domain_id, 
                                    max_paths=3, max_length=4):
        """
        Find paths between two domains, revealing interdisciplinary connections.
        
        Args:
            source_domain_id: ID of the source domain
            target_domain_id: ID of the target domain
            max_paths: Maximum number of paths to return
            max_length: Maximum path length
            
        Returns:
            List of paths, each containing the domains and connections
        """
        if source_domain_id not in self.domains:
            raise ValueError(f"Source domain with ID {source_domain_id} not found")
            
        if target_domain_id not in self.domains:
            raise ValueError(f"Target domain with ID {target_domain_id} not found")
            
        if source_domain_id == target_domain_id:
            return [{
                "length": 0,
                "domains": [self.domains[source_domain_id].to_dict()],
                "connections": []
            }]
            
        # Find all simple paths between the domains
        try:
            all_paths = list(nx.all_simple_paths(
                self.domain_graph, 
                source=source_domain_id, 
                target=target_domain_id,
                cutoff=max_length
            ))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
            
        # If no paths found
        if not all_paths:
            return []
            
        # Sort paths by length
        all_paths.sort(key=len)
        
        # Process each path
        results = []
        for path in all_paths[:max_paths]:
            # Get domain information for each node in the path
            domains = []
            for domain_id in path:
                if domain_id in self.domains:
                    domain_data = self.domains[domain_id].to_dict()
                    domains.append(domain_data)
                    
            # Get connection information for each edge in the path
            connections = []
            for i in range(len(path) - 1):
                source_id = path[i]
                target_id = path[i + 1]
                
                # Get connection data from graph
                if self.domain_graph.has_edge(source_id, target_id):
                    edge_data = self.domain_graph.get_edge_data(source_id, target_id)
                    connection = {
                        "source_domain_id": source_id,
                        "target_domain_id": target_id,
                        "type": edge_data.get('type', 'related'),
                        "strength": edge_data.get('strength', 0.5),
                        "description": edge_data.get('description', ''),
                        "id": edge_data.get('id', '')
                    }
                    connections.append(connection)
                    
            # Add path data to results
            results.append({
                "length": len(path) - 1,
                "domains": domains,
                "connections": connections
            })
            
        return results
    
    def discover_connection_patterns(self):
        """
        Discover interesting patterns in the domain and concept connections.
        
        Returns:
            List of discovered patterns
        """
        patterns = []
        
        # Skip if not enough data
        if len(self.domains) < 3 or len(self.concepts) < 5:
            logger.info("Not enough data to discover connection patterns")
            return patterns
            
        # Pattern 1: Central domains (hub domains with many connections)
        if len(self.domains) >= 3:
            centrality = nx.degree_centrality(self.domain_graph)
            top_domains = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for domain_id, centrality_score in top_domains:
                if centrality_score > 0.1 and domain_id in self.domains:  # Only include significant hubs
                    domain = self.domains[domain_id]
                    patterns.append({
                        "pattern_type": "central_domain",
                        "domain_id": domain_id,
                        "domain_name": domain.name,
                        "centrality_score": centrality_score,
                        "connection_count": len(domain.connections),
                        "domain_type": domain.domain_type,
                        "description": f"Central hub domain with high connectivity ({len(domain.connections)} connections)"
                    })
        
        # Pattern 2: Bridge domains (high betweenness)
        if len(self.domains) >= 5:
            try:
                betweenness = nx.betweenness_centrality(self.domain_graph)
                top_bridges = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
                
                for domain_id, betweenness_score in top_bridges:
                    if betweenness_score > 0.1 and domain_id in self.domains:  # Only include significant bridges
                        domain = self.domains[domain_id]
                        patterns.append({
                            "pattern_type": "bridge_domain",
                            "domain_id": domain_id,
                            "domain_name": domain.name,
                            "betweenness_score": betweenness_score,
                            "domain_type": domain.domain_type,
                            "description": "Bridge domain connecting disparate knowledge areas"
                        })
            except:
                # Skip if there's an issue calculating betweenness (e.g., disconnected graph)
                pass
        
        # Pattern 3: Domain clusters
        if len(self.domains) >= 6:
            try:
                clusters = list(nx.community.greedy_modularity_communities(self.domain_graph.to_undirected()))
                
                for i, cluster in enumerate(clusters[:5]):  # Top 5 clusters
                    if len(cluster) >= 2:  # Only include clusters with at least 2 domains
                        cluster_domains = []
                        for domain_id in cluster:
                            if domain_id in self.domains:
                                cluster_domains.append({
                                    "id": domain_id,
                                    "name": self.domains[domain_id].name
                                })
                        
                        patterns.append({
                            "pattern_type": "domain_cluster",
                            "cluster_id": i,
                            "size": len(cluster),
                            "domains": cluster_domains,
                            "description": f"Cluster of {len(cluster)} related knowledge domains"
                        })
            except:
                # Skip if there's an issue finding clusters
                pass
        
        # Pattern 4: Interdisciplinary concept hubs
        if len(self.concepts) >= 5:
            domain_concept_map = defaultdict(list)
            for concept_id, concept in self.concepts.items():
                if concept.domain_id:
                    domain_concept_map[concept.domain_id].append(concept_id)
            
            top_concepts = []
            for domain_id, domain_concepts in domain_concept_map.items():
                for concept_id in domain_concepts:
                    concept = self.concepts[concept_id]
                    connected_domains = set()
                    
                    for connected_concept_id in concept.connections:
                        if connected_concept_id in self.concepts:
                            connected_concept = self.concepts[connected_concept_id]
                            if connected_concept.domain_id and connected_concept.domain_id != concept.domain_id:
                                connected_domains.add(connected_concept.domain_id)
                    
                    if len(connected_domains) >= 2:  # Only include concepts connecting 3+ domains
                        top_concepts.append((concept_id, len(connected_domains)))
            
            # Get top interdisciplinary concepts
            top_concepts.sort(key=lambda x: x[1], reverse=True)
            for concept_id, domain_count in top_concepts[:5]:
                concept = self.concepts[concept_id]
                
                # Get the domain names
                domain_names = []
                for connected_concept_id in concept.connections:
                    if connected_concept_id in self.concepts:
                        connected_concept = self.concepts[connected_concept_id]
                        if connected_concept.domain_id and connected_concept.domain_id != concept.domain_id:
                            if connected_concept.domain_id in self.domains:
                                domain_names.append(self.domains[connected_concept.domain_id].name)
                
                patterns.append({
                    "pattern_type": "interdisciplinary_concept",
                    "concept_id": concept_id,
                    "concept_name": concept.name,
                    "domain_count": domain_count,
                    "domain_names": list(set(domain_names)),
                    "description": f"Concept that bridges {domain_count} different knowledge domains"
                })
                
        # Save the discovered patterns
        self.discovered_patterns = patterns
        
        return patterns
    
    def generate_domain_network(self, include_connections=True):
        """
        Generate a network representation of domains for visualization.
        
        Args:
            include_connections: Whether to include connection data
            
        Returns:
            Network data with nodes and edges
        """
        nodes = []
        edges = []
        
        # Add all domains as nodes
        for domain_id, domain in self.domains.items():
            node_data = {
                "id": domain_id,
                "name": domain.name,
                "domain_type": domain.domain_type,
                "concept_count": len(domain.concepts),
                "connection_count": len(domain.connections)
            }
            nodes.append(node_data)
            
        # Add connections as edges if requested
        if include_connections:
            for source_id in self.domain_graph.nodes():
                for target_id in self.domain_graph[source_id]:
                    edge_data = self.domain_graph.get_edge_data(source_id, target_id)
                    edge = {
                        "source": source_id,
                        "target": target_id,
                        "type": edge_data.get('type', 'related'),
                        "weight": edge_data.get('strength', 0.5)
                    }
                    edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges
        }
        
    def export_data(self, format_type='json'):
        """
        Export the entire knowledge graph.
        
        Args:
            format_type: Export format ('json' or 'xml')
            
        Returns:
            Exported data as string
        """
        # Prepare data for export
        export_data = {
            "domains": [domain.to_dict() for domain in self.domains.values()],
            "concepts": [concept.to_dict() for concept in self.concepts.values()],
            "domain_connections": [],
            "concept_connections": []
        }
        
        # Add domain connections
        for source_id, targets in self.domain_graph.adjacency():
            for target_id, edge_data in targets.items():
                connection = {
                    "source_domain_id": source_id,
                    "target_domain_id": target_id,
                    "connection_type": edge_data.get('type', 'related'),
                    "strength": edge_data.get('strength', 0.5),
                    "bidirectional": edge_data.get('bidirectional', True),
                    "description": edge_data.get('description', '')
                }
                export_data["domain_connections"].append(connection)
                
        # Add concept connections
        for source_id, targets in self.concept_graph.adjacency():
            for target_id, edge_data in targets.items():
                connection = {
                    "source_concept_id": source_id,
                    "target_concept_id": target_id,
                    "relation_type": edge_data.get('type', 'related'),
                    "strength": edge_data.get('strength', 0.5),
                    "bidirectional": edge_data.get('bidirectional', True),
                    "description": edge_data.get('description', '')
                }
                export_data["concept_connections"].append(connection)
        
        # Export in requested format
        if format_type == 'json':
            return json.dumps(export_data, indent=2)
        elif format_type == 'xml':
            # Simple XML conversion
            xml_data = ['<?xml version="1.0" encoding="UTF-8"?>']
            xml_data.append('<ConnectionMapper>')
            
            # Add domains
            xml_data.append('  <Domains>')
            for domain in export_data['domains']:
                xml_data.append(f'    <Domain id="{domain["id"]}">')
                xml_data.append(f'      <Name>{domain["name"]}</Name>')
                xml_data.append(f'      <DomainType>{domain["domain_type"]}</DomainType>')
                xml_data.append(f'      <Description>{domain.get("description", "")}</Description>')
                xml_data.append('    </Domain>')
            xml_data.append('  </Domains>')
            
            # Add concepts
            xml_data.append('  <Concepts>')
            for concept in export_data['concepts']:
                xml_data.append(f'    <Concept id="{concept["id"]}">')
                xml_data.append(f'      <Name>{concept["name"]}</Name>')
                xml_data.append(f'      <DomainId>{concept.get("domain_id", "")}</DomainId>')
                xml_data.append(f'      <NodeType>{concept["node_type"]}</NodeType>')
                xml_data.append(f'      <Description>{concept.get("description", "")}</Description>')
                xml_data.append('    </Concept>')
            xml_data.append('  </Concepts>')
            
            # Add domain connections
            xml_data.append('  <DomainConnections>')
            for conn in export_data['domain_connections']:
                xml_data.append(f'    <Connection source="{conn["source_domain_id"]}" target="{conn["target_domain_id"]}">')
                xml_data.append(f'      <Type>{conn["connection_type"]}</Type>')
                xml_data.append(f'      <Strength>{conn["strength"]}</Strength>')
                xml_data.append(f'      <Bidirectional>{str(conn["bidirectional"]).lower()}</Bidirectional>')
                xml_data.append('    </Connection>')
            xml_data.append('  </DomainConnections>')
            
            # Add concept connections
            xml_data.append('  <ConceptConnections>')
            for conn in export_data['concept_connections']:
                xml_data.append(f'    <Connection source="{conn["source_concept_id"]}" target="{conn["target_concept_id"]}">')
                xml_data.append(f'      <Type>{conn["relation_type"]}</Type>')
                xml_data.append(f'      <Strength>{conn["strength"]}</Strength>')
                xml_data.append(f'      <Bidirectional>{str(conn["bidirectional"]).lower()}</Bidirectional>')
                xml_data.append('    </Connection>')
            xml_data.append('  </ConceptConnections>')
            
            xml_data.append('</ConnectionMapper>')
            return '\n'.join(xml_data)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _index_domain(self, domain):
        """Index a domain for search."""
        terms = self._extract_search_terms(domain.name, domain.description or "")
        for term in terms:
            self.domain_index[term].append(domain.id)
            
        # Add domain type to index
        if domain.domain_type:
            self.domain_index[domain.domain_type].append(domain.id)
            
        # Add terms from domain attributes
        for key, value in domain.attributes.items():
            attribute_terms = self._extract_search_terms(str(key), str(value))
            for term in attribute_terms:
                self.domain_index[term].append(domain.id)
        
        # Add terminology to index
        for term in domain.terminology:
            normalized_term = term.lower()
            if normalized_term not in self.domain_index:
                self.domain_index[normalized_term] = [domain.id]
            else:
                self.domain_index[normalized_term].append(domain.id)
    
    def _index_concept(self, concept):
        """Index a concept for search."""
        terms = self._extract_search_terms(concept.name, concept.description or "")
        for term in terms:
            self.concept_index[term].append(concept.id)
            
        # Add concept type to index
        if concept.node_type:
            self.concept_index[concept.node_type].append(concept.id)
            
        # Add terms from concept attributes
        for key, value in concept.attributes.items():
            attribute_terms = self._extract_search_terms(str(key), str(value))
            for term in attribute_terms:
                self.concept_index[term].append(concept.id)
    
    def _extract_search_terms(self, *texts):
        """Extract search terms from text."""
        combined_text = ' '.join([t for t in texts if t])
        
        # Normalize and tokenize
        normalized = combined_text.lower()
        
        # Remove punctuation and tokenize
        words = re.findall(r'\b\w+\b', normalized)
        
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'of', 'in', 
                    'to', 'for', 'with', 'on', 'at', 'by', 'this', 'that', 'it', 'as'}
        terms = [word for word in words if word not in stopwords and len(word) > 1]
        
        return set(terms)
        
    def reload_from_database(self):
        """
        Reload all data from the database into the in-memory structures.
        Used after importing data or making significant changes.
        """
        from models_mapper import KnowledgeDomain, ConceptNode, DomainConnection, ConceptConnection
        
        # Clear existing data
        self.domains = {}
        self.concepts = {}
        self.domain_graph.clear()
        self.concept_graph.clear()
        self.domain_index.clear()
        self.concept_index.clear()
        
        # Load domains
        domains = KnowledgeDomain.query.all()
        for db_domain in domains:
            domain = KnowledgeDomain(
                name=db_domain.name,
                description=db_domain.description,
                domain_type=db_domain.domain_type,
                parent_domain=db_domain.parent_domain_id,
                attributes=db_domain.attributes
            )
            domain.id = db_domain.id
            domain.created_at = db_domain.created_at
            domain.updated_at = db_domain.updated_at
            if db_domain.terminology:
                domain.terminology = set(db_domain.terminology)
            
            self.domains[domain.id] = domain
            self.domain_graph.add_node(domain.id)
            self._index_domain(domain)
        
        # Load concepts
        concepts = ConceptNode.query.all()
        for db_concept in concepts:
            concept = ConceptNode(
                name=db_concept.name,
                description=db_concept.description,
                node_type=db_concept.node_type,
                attributes=db_concept.attributes
            )
            concept.id = db_concept.id
            concept.created_at = db_concept.created_at
            concept.updated_at = db_concept.updated_at
            
            # Link to domains
            for db_domain in db_concept.domains:
                if db_domain.id in self.domains:
                    concept.domain_id = db_domain.id
                    break
            
            # Load vector if present
            if db_concept.vector_data:
                try:
                    vector = np.array(json.loads(db_concept.vector_data), dtype=float)
                    concept.set_vector(vector)
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.warning(f"Error loading vector for concept {concept.id}: {str(e)}")
            
            self.concepts[concept.id] = concept
            self.concept_graph.add_node(concept.id)
            self._index_concept(concept)
        
        # Load domain connections
        domain_connections = DomainConnection.query.all()
        for conn in domain_connections:
            if conn.source_domain_id in self.domains and conn.target_domain_id in self.domains:
                source = self.domains[conn.source_domain_id]
                
                # Add connection data to source domain
                source.connections[conn.target_domain_id] = {
                    'id': conn.id,
                    'type': conn.connection_type,
                    'strength': conn.strength,
                    'description': conn.description,
                    'bidirectional': conn.bidirectional,
                    'attributes': conn.attributes
                }
                
                # Add edge to graph
                self.domain_graph.add_edge(
                    conn.source_domain_id, 
                    conn.target_domain_id, 
                    weight=1.0 - conn.strength,  # Lower weight = stronger connection for shortest path
                    type=conn.connection_type
                )
        
        # Load concept connections
        concept_connections = ConceptConnection.query.all()
        for conn in concept_connections:
            if conn.source_concept_id in self.concepts and conn.target_concept_id in self.concepts:
                source = self.concepts[conn.source_concept_id]
                
                # Add connection data to source concept
                source.connections[conn.target_concept_id] = {
                    'id': conn.id,
                    'type': conn.relation_type,
                    'strength': conn.strength,
                    'description': conn.description,
                    'bidirectional': conn.bidirectional,
                    'attributes': conn.attributes
                }
                
                # Add edge to graph
                self.concept_graph.add_edge(
                    conn.source_concept_id, 
                    conn.target_concept_id, 
                    weight=1.0 - conn.strength,
                    type=conn.relation_type
                )
        
        logger.info(f"Reloaded connection mapper data from database: "
                  f"{len(self.domains)} domains, {len(self.concepts)} concepts, "
                  f"{self.domain_graph.number_of_edges()} domain connections, "
                  f"{self.concept_graph.number_of_edges()} concept connections")