"""
Topology Module for Deep Tree Echo (Root Level)

This module represents the spatial dimension at the root/unconscious level of the DTE architecture.
It defines the structural relationships between components in the system.
"""

import uuid
import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class TopologyNode:
    """A node in the topology representing a system component or concept."""
    
    def __init__(self, id: str = None, name: str = "", node_type: str = "generic", 
                 position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 attributes: Dict[str, Any] = None):
        """Initialize a topology node.
        
        Args:
            id: Unique identifier for the node
            name: Human-readable name for the node
            node_type: Type of node (generic, component, concept, etc.)
            position: 3D coordinates (x, y, z) for visualization
            attributes: Additional attributes for the node
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.node_type = node_type
        self.position = position
        self.attributes = attributes or {}
        self.created_at = None
        self.updated_at = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type,
            "position": self.position,
            "attributes": self.attributes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class SystemTopology:
    """Manages the system topology graph."""
    
    def __init__(self):
        """Initialize the topology system."""
        self.nodes = {}  # id -> node
        self.connections = defaultdict(set)  # source_id -> set of target_ids
        self.regions = {}  # region_name -> set of node_ids
        self.tags = defaultdict(set)  # tag -> set of node_ids
        
    def add_node(self, node: TopologyNode) -> str:
        """Add a node to the topology."""
        self.nodes[node.id] = node
        logger.info(f"Added node {node.name} ({node.id}) to topology")
        return node.id
        
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the topology."""
        if node_id not in self.nodes:
            return False
            
        # Remove all connections involving this node
        self.connections.pop(node_id, None)
        for source_id, targets in self.connections.items():
            targets.discard(node_id)
            
        # Remove from regions
        for region_nodes in self.regions.values():
            region_nodes.discard(node_id)
            
        # Remove from tags
        for tag_nodes in self.tags.values():
            tag_nodes.discard(node_id)
            
        # Remove the node itself
        node_name = self.nodes[node_id].name
        del self.nodes[node_id]
        logger.info(f"Removed node {node_name} ({node_id}) from topology")
        return True
        
    def get_node(self, node_id: str) -> Optional[TopologyNode]:
        """Get a node by its ID."""
        return self.nodes.get(node_id)
        
    def connect_nodes(self, source_id: str, target_id: str) -> bool:
        """Create a connection between two nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
            
        self.connections[source_id].add(target_id)
        logger.info(f"Connected nodes {source_id} -> {target_id}")
        return True
        
    def disconnect_nodes(self, source_id: str, target_id: str) -> bool:
        """Remove a connection between two nodes."""
        if source_id not in self.connections:
            return False
            
        if target_id not in self.connections[source_id]:
            return False
            
        self.connections[source_id].remove(target_id)
        logger.info(f"Disconnected nodes {source_id} -> {target_id}")
        return True
        
    def get_connected_nodes(self, node_id: str, outgoing: bool = True) -> List[str]:
        """Get nodes connected to the given node."""
        if outgoing:
            return list(self.connections.get(node_id, set()))
        else:
            return [src for src, targets in self.connections.items() 
                   if node_id in targets]
                   
    def create_region(self, region_name: str, node_ids: List[str]) -> bool:
        """Create a named region containing the specified nodes."""
        if not node_ids or not all(nid in self.nodes for nid in node_ids):
            return False
            
        self.regions[region_name] = set(node_ids)
        logger.info(f"Created region {region_name} with {len(node_ids)} nodes")
        return True
        
    def add_to_region(self, region_name: str, node_id: str) -> bool:
        """Add a node to a region."""
        if region_name not in self.regions or node_id not in self.nodes:
            return False
            
        self.regions[region_name].add(node_id)
        return True
        
    def remove_from_region(self, region_name: str, node_id: str) -> bool:
        """Remove a node from a region."""
        if region_name not in self.regions:
            return False
            
        if node_id not in self.regions[region_name]:
            return False
            
        self.regions[region_name].remove(node_id)
        return True
        
    def tag_node(self, node_id: str, tag: str) -> bool:
        """Add a tag to a node."""
        if node_id not in self.nodes:
            return False
            
        self.tags[tag].add(node_id)
        return True
        
    def untag_node(self, node_id: str, tag: str) -> bool:
        """Remove a tag from a node."""
        if tag not in self.tags or node_id not in self.tags[tag]:
            return False
            
        self.tags[tag].remove(node_id)
        return True
        
    def get_nodes_by_tag(self, tag: str) -> List[str]:
        """Get all nodes with a specific tag."""
        return list(self.tags.get(tag, set()))
        
    def get_node_tags(self, node_id: str) -> List[str]:
        """Get all tags for a specific node."""
        return [tag for tag, nodes in self.tags.items() if node_id in nodes]
        
    def get_topology_state(self) -> Dict[str, Any]:
        """Get the current state of the topology."""
        nodes_dict = {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        
        connections_list = []
        for source_id, targets in self.connections.items():
            for target_id in targets:
                connections_list.append({
                    "source": source_id,
                    "target": target_id
                })
                
        regions_dict = {name: list(nodes) for name, nodes in self.regions.items()}
        tags_dict = {tag: list(nodes) for tag, nodes in self.tags.items()}
        
        return {
            "nodes": nodes_dict,
            "connections": connections_list,
            "regions": regions_dict,
            "tags": tags_dict
        }


# Create a singleton instance
system_topology = SystemTopology()

def get_topology() -> SystemTopology:
    """Get the system topology singleton."""
    return system_topology