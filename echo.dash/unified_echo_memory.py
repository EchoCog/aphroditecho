"""
Unified Echo Memory System

This module consolidates all memory operations across the Echo ecosystem into a 
unified, standardized interface. It builds on the existing memory_management.py 
and integrates with the Echo component base classes.

This addresses the "Fragmented Memory System" architecture gap identified
in the Deep Tree Echo analysis.
"""

import json
import time
import logging
# import numpy as np  # Optional dependency
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from datetime import datetime

# Import the standardized Echo components
from echo_component_base import MemoryEchoComponent, EchoConfig, EchoResponse

# Import optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    from deep_tree_echo import TreeNode
    HAS_DEEP_TREE_ECHO = True
except ImportError:
    TreeNode = None
    HAS_DEEP_TREE_ECHO = False

# Core memory types and classes (consolidated from memory_management.py)
class MemoryType(Enum):
    DECLARATIVE = "declarative"  # Facts and concepts
    EPISODIC = "episodic"        # Personal experiences
    PROCEDURAL = "procedural"    # How to do things
    SEMANTIC = "semantic"        # General knowledge
    WORKING = "working"          # Short-term active processing
    SENSORY = "sensory"          # Perceptual information
    EMOTIONAL = "emotional"      # Feelings and emotional states
    ASSOCIATIVE = "associative"  # Connections between other memories

@dataclass
class MemoryNode:
    id: str
    content: str
    memory_type: MemoryType
    creation_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    access_count: int = 0
    salience: float = 0.5  # How important/noteworthy the memory is (0-1)
    echo_value: float = 0.0  # Related to Deep Tree Echo values
    source: str = "unknown"  # Where the memory came from
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['memory_type'] = self.memory_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryNode':
        """Create from dictionary"""
        # Convert string memory_type back to enum
        if isinstance(data['memory_type'], str):
            data['memory_type'] = MemoryType(data['memory_type'])
        return cls(**data)
    
    def access(self):
        """Mark this memory as accessed"""
        self.last_access_time = time.time()
        self.access_count += 1

@dataclass
class MemoryEdge:
    from_id: str
    to_id: str
    relation_type: str
    weight: float = 0.5  # Strength of connection (0-1)
    creation_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEdge':
        """Create from dictionary"""
        return cls(**data)
class HypergraphMemory:
    """Consolidated HypergraphMemory implementation (moved from memory_management.py)"""
    
    def __init__(self, storage_dir: str = "echo_memory"):
        """Initialize the hypergraph memory system
        
        Args:
            storage_dir: Directory to store memory files
        """
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: List[MemoryEdge] = []
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Index structures for efficient retrieval
        self.type_index: Dict[MemoryType, Set[str]] = {mem_type: set() for mem_type in MemoryType}
        self.source_index: Dict[str, Set[str]] = defaultdict(set)
        self.temporal_index: List[Tuple[float, str]] = []  # (timestamp, node_id)
        self.salience_index: List[Tuple[float, str]] = []  # (salience, node_id)
        self.echo_index: List[Tuple[float, str]] = []  # (echo_value, node_id)
        
        # Network representation for graph algorithms (optional)
        if HAS_NETWORKX:
            import networkx as nx
            self.graph = nx.DiGraph()
        else:
            self.graph = None
        
        # Working memory (limited capacity active nodes)
        self.working_memory: deque = deque(maxlen=7)  # Miller's Law: 7±2 items
        
        # Load existing memories if available
        self.load()
    
    def add_node(self, node: MemoryNode) -> str:
        """Add a memory node to the system"""
        if node.id in self.nodes:
            logging.getLogger(__name__).warning(f"Node with ID {node.id} already exists, updating")
            
        # Store the node
        self.nodes[node.id] = node
        
        # Update indices
        self.type_index[node.memory_type].add(node.id)
        self.source_index[node.source].add(node.id)
        self.temporal_index.append((node.creation_time, node.id))
        self.salience_index.append((node.salience, node.id))
        self.echo_index.append((node.echo_value, node.id))
        
        # Add to graph for network analysis (if available)
        if self.graph is not None:
            self.graph.add_node(node.id, **{k: v for k, v in node.to_dict().items() 
                                          if k not in ['id', 'embeddings']})
        
        # Sort indices
        self._sort_indices()
        
        return node.id
    
    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def find_nodes(self, **filters) -> List[MemoryNode]:
        """Find nodes matching filters"""
        results = []
        for node in self.nodes.values():
            match = True
            for key, value in filters.items():
                if hasattr(node, key):
                    if getattr(node, key) != value:
                        match = False
                        break
            if match:
                results.append(node)
        return results
    
    def load(self):
        """Load memories from disk"""
        try:
            nodes_file = self.storage_dir / "nodes.json"
            if nodes_file.exists():
                with open(nodes_file, 'r') as f:
                    nodes_data = json.load(f)
                    for node_data in nodes_data:
                        node = MemoryNode.from_dict(node_data)
                        self.nodes[node.id] = node
                        
                        # Rebuild indices
                        self.type_index[node.memory_type].add(node.id)
                        self.source_index[node.source].add(node.id)
                        self.temporal_index.append((node.creation_time, node.id))
                        self.salience_index.append((node.salience, node.id))
                        self.echo_index.append((node.echo_value, node.id))
                        
                logging.getLogger(__name__).info(f"Loaded {len(self.nodes)} memory nodes")
                
            # Load edges
            edges_file = self.storage_dir / "edges.json"
            if edges_file.exists():
                with open(edges_file, 'r') as f:
                    edges_data = json.load(f)
                    for edge_data in edges_data:
                        edge = MemoryEdge.from_dict(edge_data)
                        self.edges.append(edge)
                        
                logging.getLogger(__name__).info(f"Loaded {len(self.edges)} memory edges")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error loading memories: {str(e)}")
                
        # Sort indices
        self._sort_indices()
    
    def save(self):
        """Save memories to disk"""
        try:
            # Save nodes
            nodes_data = [node.to_dict() for node in self.nodes.values()]
            nodes_file = self.storage_dir / "nodes.json"
            with open(nodes_file, 'w') as f:
                json.dump(nodes_data, f, indent=2)
            
            # Save edges
            edges_data = [edge.to_dict() for edge in self.edges]
            edges_file = self.storage_dir / "edges.json"
            with open(edges_file, 'w') as f:
                json.dump(edges_data, f, indent=2)
                
            logging.getLogger(__name__).info(f"Saved {len(self.nodes)} nodes and {len(self.edges)} edges")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error saving memories: {str(e)}")
    
    def _sort_indices(self):
        """Sort indices for efficient retrieval"""
        self.temporal_index.sort(reverse=True)  # Most recent first
        self.salience_index.sort(reverse=True)  # Highest salience first
        self.echo_index.sort(reverse=True)      # Highest echo value first


@dataclass
class EchoMemoryConfig:
    """Configuration for Echo Memory System"""
    working_memory_capacity: int = 7  # Miller's Law: 7±2 items
    max_total_memories: int = 10000
    auto_save_interval: int = 300  # seconds
    memory_storage_path: str = "memory_storage"
    enable_embeddings: bool = True
    salience_decay_rate: float = 0.01
    echo_threshold: float = 0.75
    enable_graph_analysis: bool = True


class UnifiedEchoMemory(MemoryEchoComponent):
    """
    Unified Echo Memory System
    
    Consolidates all memory operations in the Echo ecosystem with standardized interfaces.
    Extends MemoryEchoComponent to provide Echo-standard methods while wrapping
    the comprehensive memory management functionality.
    """
    
    def __init__(self, config: EchoConfig, memory_config: Optional[EchoMemoryConfig] = None):
        super().__init__(config)
        
        # Memory-specific configuration
        self.memory_config = memory_config or EchoMemoryConfig()
        
        # Initialize the comprehensive memory manager
        self.memory_manager = HypergraphMemory(
            storage_dir=self.memory_config.memory_storage_path
        )
        
        # Additional Echo-specific memory tracking
        self.echo_memory_stats = {
            'total_operations': 0,
            'last_operation_time': None,
            'memory_types_used': set(),
            'most_accessed_memories': [],
            'echo_value_distribution': {}
        }
        
        # Working memory for active processing (Echo-specific)
        self.echo_working_memory = deque(maxlen=self.memory_config.working_memory_capacity)
        
        # Auto-save timer tracking
        self.last_save_time = time.time()
        
        # Add missing adapter methods to memory manager
        self._add_adapter_methods()
    
    def _add_adapter_methods(self):
        """Add adapter methods to bridge interface differences"""
        # Add search_memories method to HypergraphMemory instance
        def search_memories(query: str, memory_type: Optional[MemoryType] = None) -> List[MemoryNode]:
            """Search memories by content (simple text matching)"""
            results = []
            for node in self.memory_manager.nodes.values():
                # Filter by memory type if specified
                if memory_type and node.memory_type != memory_type:
                    continue
                    
                # Simple text search in content
                if query.lower() in node.content.lower():
                    results.append(node)
            
            # Sort by relevance (access count and salience)
            results.sort(key=lambda n: (n.access_count * n.salience), reverse=True)
            return results
        
        # Add get_memory method
        def get_memory(memory_id: str) -> Optional[MemoryNode]:
            """Get memory by ID"""
            return self.memory_manager.nodes.get(memory_id)
        
        # Add add_memory method
        def add_memory(content: str, memory_type: MemoryType, 
                      echo_value: float = 0.0, source: str = "unified_echo") -> str:
            """Add a new memory"""
            memory_id = f"mem_{int(time.time() * 1000000)}_{len(self.memory_manager.nodes)}"
            node = MemoryNode(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                echo_value=echo_value,
                source=source
            )
            self.memory_manager.add_node(node)
            return memory_id
        
        # Bind methods to memory manager instance
        self.memory_manager.search_memories = search_memories
        self.memory_manager.get_memory = get_memory
        self.memory_manager.add_memory = add_memory
    
    def initialize(self) -> EchoResponse:
        """Initialize the unified memory system"""
        try:
            # Load existing memories
            self.memory_manager.load()
            
            # Initialize Echo memory stats
            self._update_memory_stats()
            
            self._initialized = True
            
            memory_count = len(self.memory_manager.nodes)
            self.logger.info(f"Unified Echo Memory initialized with {memory_count} existing memories")
            
            return EchoResponse(
                success=True,
                message=f"Unified Echo Memory initialized with {memory_count} memories",
                metadata={
                    'memory_count': memory_count,
                    'working_memory_capacity': self.memory_config.working_memory_capacity,
                    'storage_path': self.memory_config.memory_storage_path
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Process memory operations
        
        Args:
            input_data: Memory operation data (dict with 'operation' and parameters)
            **kwargs: Additional parameters
            
        Expected input_data format:
        {
            'operation': 'store|retrieve|update|delete|search|analyze',
            'memory_id': 'optional_id',
            'content': 'memory_content',
            'memory_type': 'MemoryType_value',
            'metadata': {},
            ...
        }
        """
        try:
            validation = self.validate_input(input_data)
            if not validation.success:
                return validation
            
            if not isinstance(input_data, dict) or 'operation' not in input_data:
                return EchoResponse(
                    success=False,
                    message="Input must be dict with 'operation' key"
                )
            
            operation = input_data['operation'].lower()
            
            # Route to appropriate operation
            if operation == 'store':
                return self._process_store_operation(input_data)
            elif operation == 'retrieve':
                return self._process_retrieve_operation(input_data)
            elif operation == 'update':
                return self._process_update_operation(input_data)
            elif operation == 'delete':
                return self._process_delete_operation(input_data)
            elif operation == 'search':
                return self._process_search_operation(input_data)
            elif operation == 'analyze':
                return self._process_analyze_operation(input_data)
            else:
                return EchoResponse(
                    success=False,
                    message=f"Unknown operation: {operation}"
                )
                
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """
        Perform echo operation on memory system
        
        Creates an echo-enhanced memory entry and analyzes memory resonance
        """
        try:
            # Create echo memory entry
            echo_memory = MemoryNode(
                id=f"echo_{int(time.time() * 1000)}",
                content=json.dumps(data) if not isinstance(data, str) else data,
                memory_type=MemoryType.ASSOCIATIVE,
                echo_value=echo_value,
                source="echo_operation",
                metadata={
                    'echo_timestamp': datetime.now().isoformat(),
                    'echo_value': echo_value,
                    'original_data': data
                }
            )
            
            # Store the echo memory
            self.memory_manager.add_node(echo_memory)
            
            # Find resonant memories (similar echo values)
            resonant_memories = self._find_resonant_memories(echo_value)
            
            # Update working memory with echo
            self.echo_working_memory.append(echo_memory.id)
            
            # Analyze echo patterns
            echo_analysis = self._analyze_echo_patterns(echo_value, resonant_memories)
            
            echo_data = {
                'echo_memory_id': echo_memory.id,
                'echo_value': echo_value,
                'resonant_memories': [mem.id for mem in resonant_memories],
                'echo_analysis': echo_analysis,
                'working_memory_state': list(self.echo_working_memory),
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echo_data,
                message=f"Echo operation completed (value: {echo_value})",
                metadata={
                    'echo_value': echo_value,
                    'resonant_count': len(resonant_memories),
                    'memory_id': echo_memory.id
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def _process_store_operation(self, data: Dict) -> EchoResponse:
        """Process memory store operation"""
        try:
            # Extract parameters
            content = data.get('content', '')
            memory_type_str = data.get('memory_type', 'DECLARATIVE')
            echo_value = data.get('echo_value', 0.0)
            source = data.get('source', 'echo_system')
            metadata = data.get('metadata', {})
            
            # Convert memory type
            try:
                if isinstance(memory_type_str, str):
                    # Try direct lookup first, then case-insensitive
                    try:
                        memory_type = MemoryType(memory_type_str.lower())
                    except ValueError:
                        memory_type = MemoryType.from_string(memory_type_str)
                else:
                    memory_type = memory_type_str
            except (ValueError, AttributeError):
                memory_type = MemoryType.DECLARATIVE  # Default fallback
            
            # Create memory node
            memory_node = MemoryNode(
                id=data.get('memory_id', f"mem_{int(time.time() * 1000000)}_{len(self.memory_manager.nodes)}"),  # More unique ID
                content=content,
                memory_type=memory_type,
                echo_value=echo_value,
                source=source,
                metadata=metadata
            )
            
            # Store in memory manager
            node_id = self.memory_manager.add_node(memory_node)
            
            # Update working memory
            self.echo_working_memory.append(node_id)
            
            # Update stats
            self._update_operation_stats('store', memory_type)
            
            # Auto-save if needed
            self._check_auto_save()
            
            return EchoResponse(
                success=True,
                data={'memory_id': node_id, 'memory_type': memory_type.value},
                message=f"Memory stored with ID: {node_id}",
                metadata={'memory_id': node_id, 'memory_type': memory_type.value}
            )
            
        except Exception as e:
            return self.handle_error(e, "_process_store_operation")
    
    def _process_retrieve_operation(self, data: Dict) -> EchoResponse:
        """Process memory retrieve operation"""
        try:
            memory_id = data.get('memory_id')
            
            if not memory_id:
                return EchoResponse(
                    success=False,
                    message="memory_id required for retrieve operation"
                )
            
            # Retrieve from memory manager
            memory_node = self.memory_manager.get_node(memory_id)
            
            if not memory_node:
                return EchoResponse(
                    success=False,
                    message=f"Memory not found: {memory_id}"
                )
            
            # Update access stats
            memory_node.last_access_time = time.time()
            memory_node.access_count += 1
            
            # Add to working memory
            if memory_id not in self.echo_working_memory:
                self.echo_working_memory.append(memory_id)
            
            # Update stats
            self._update_operation_stats('retrieve', memory_node.memory_type)
            
            return EchoResponse(
                success=True,
                data=memory_node.to_dict(),
                message=f"Memory retrieved: {memory_id}",
                metadata={'memory_id': memory_id, 'access_count': memory_node.access_count}
            )
            
        except Exception as e:
            return self.handle_error(e, "_process_retrieve_operation")
    
    def _process_search_operation(self, data: Dict) -> EchoResponse:
        """Process memory search operation"""
        try:
            query = data.get('query', '')
            memory_type = data.get('memory_type')
            echo_threshold = data.get('echo_threshold', self.memory_config.echo_threshold)
            max_results = data.get('max_results', 10)
            
            # Perform search
            results = self.memory_manager.search_memories(
                query=query,
                memory_type=MemoryType(memory_type) if memory_type else None
            )
            
            # Filter by echo threshold if specified
            if echo_threshold > 0:
                results = [r for r in results if r.echo_value >= echo_threshold]
            
            # Limit results
            results = results[:max_results]
            
            # Update stats
            self._update_operation_stats('search')
            
            search_data = {
                'query': query,
                'results': [node.to_dict() for node in results],
                'result_count': len(results),
                'search_parameters': {
                    'memory_type': memory_type,
                    'echo_threshold': echo_threshold,
                    'max_results': max_results
                }
            }
            
            return EchoResponse(
                success=True,
                data=search_data,
                message=f"Search completed: {len(results)} results found",
                metadata={'query': query, 'result_count': len(results)}
            )
            
        except Exception as e:
            return self.handle_error(e, "_process_search_operation")
    
    def _process_analyze_operation(self, data: Dict) -> EchoResponse:
        """Process memory analysis operation"""
        try:
            analysis_type = data.get('analysis_type', 'overview')
            
            if analysis_type == 'overview':
                analysis = self._get_memory_overview()
            elif analysis_type == 'echo_patterns':
                analysis = self._get_echo_distribution()  # Fix method name
            elif analysis_type == 'temporal':
                analysis = self._analyze_temporal_patterns()
            elif analysis_type == 'network':
                analysis = self._analyze_memory_network()
            else:
                return EchoResponse(
                    success=False,
                    message=f"Unknown analysis type: {analysis_type}"
                )
            
            self._update_operation_stats('analyze')
            
            return EchoResponse(
                success=True,
                data=analysis,
                message=f"Memory analysis completed: {analysis_type}",
                metadata={'analysis_type': analysis_type}
            )
            
        except Exception as e:
            return self.handle_error(e, "_process_analyze_operation")
    
    def _find_resonant_memories(self, echo_value: float, tolerance: float = 0.1) -> List[MemoryNode]:
        """Find memories with similar echo values"""
        resonant = []
        for node in self.memory_manager.nodes.values():
            if abs(node.echo_value - echo_value) <= tolerance:
                resonant.append(node)
        return resonant
    
    def _analyze_echo_patterns(self, echo_value: float, resonant_memories: List[MemoryNode]) -> Dict:
        """Analyze echo patterns in memory"""
        try:
            # Use numpy if available, otherwise basic calculations
            try:
                import numpy as np
                avg_resonant = np.mean([m.echo_value for m in resonant_memories]) if resonant_memories else 0
            except ImportError:
                avg_resonant = sum(m.echo_value for m in resonant_memories) / len(resonant_memories) if resonant_memories else 0
                
            return {
                'echo_value': echo_value,
                'resonant_count': len(resonant_memories),
                'average_resonant_echo': avg_resonant,
                'echo_distribution': self._get_echo_distribution(),
                'pattern_strength': len(resonant_memories) / max(len(self.memory_manager.nodes), 1)
            }
        except Exception as e:
            return {'error': str(e), 'echo_value': echo_value}
    
    def _get_memory_overview(self) -> Dict:
        """Get comprehensive memory system overview"""
        total_memories = len(self.memory_manager.nodes)
        
        type_distribution = defaultdict(int)
        echo_values = []
        access_counts = []
        
        for node in self.memory_manager.nodes.values():
            type_distribution[node.memory_type.value] += 1
            echo_values.append(node.echo_value)
            access_counts.append(node.access_count)
        
        # Calculate statistics with or without numpy
        try:
            import numpy as np
            echo_stats = {
                'mean': float(np.mean(echo_values)) if echo_values else 0,
                'std': float(np.std(echo_values)) if echo_values else 0,
                'min': float(np.min(echo_values)) if echo_values else 0,
                'max': float(np.max(echo_values)) if echo_values else 0
            }
            access_stats = {
                'mean': float(np.mean(access_counts)) if access_counts else 0,
                'total': sum(access_counts)
            }
        except ImportError:
            echo_stats = {
                'mean': sum(echo_values) / len(echo_values) if echo_values else 0,
                'std': 0,  # Standard deviation calculation would be complex without numpy
                'min': min(echo_values) if echo_values else 0,
                'max': max(echo_values) if echo_values else 0
            }
            access_stats = {
                'mean': sum(access_counts) / len(access_counts) if access_counts else 0,
                'total': sum(access_counts)
            }
        
        return {
            'total_memories': total_memories,
            'memory_type_distribution': dict(type_distribution),
            'working_memory_size': len(self.echo_working_memory),
            'working_memory_capacity': self.memory_config.working_memory_capacity,
            'echo_statistics': echo_stats,
            'access_statistics': access_stats,
            'echo_memory_stats': self.echo_memory_stats
        }
    
    def _get_echo_distribution(self) -> Dict:
        """Get distribution of echo values"""
        echo_values = [node.echo_value for node in self.memory_manager.nodes.values()]
        
        if not echo_values:
            return {'bins': [], 'counts': []}
        
        try:
            import numpy as np
            # Create histogram
            hist, bins = np.histogram(echo_values, bins=10)
            return {
                'bins': bins.tolist(),
                'counts': hist.tolist(),
                'total_memories': len(echo_values)
            }
        except ImportError:
            # Simple binning without numpy
            min_val, max_val = min(echo_values), max(echo_values)
            bin_size = (max_val - min_val) / 10 if max_val > min_val else 0.1
            
            bins = [min_val + i * bin_size for i in range(11)]
            counts = [0] * 10
            
            for val in echo_values:
                bin_idx = min(int((val - min_val) / bin_size), 9) if bin_size > 0 else 0
                counts[bin_idx] += 1
            
            return {
                'bins': bins,
                'counts': counts,
                'total_memories': len(echo_values)
            }
    
    def _analyze_temporal_patterns(self) -> Dict:
        """Analyze temporal patterns in memory"""
        nodes = list(self.memory_manager.nodes.values())
        
        if not nodes:
            return {'message': 'No memories to analyze'}
        
        creation_times = [node.creation_time for node in nodes]
        access_times = [node.last_access_time for node in nodes]
        
        return {
            'creation_time_range': {
                'earliest': min(creation_times),
                'latest': max(creation_times),
                'span_hours': (max(creation_times) - min(creation_times)) / 3600
            },
            'access_patterns': {
                'recent_accesses': len([t for t in access_times if time.time() - t < 3600]),
                'never_accessed': len([node for node in nodes if node.access_count == 0])
            },
            'memory_age_distribution': self._get_age_distribution(nodes)
        }
    
    def _analyze_memory_network(self) -> Dict:
        """Analyze memory network structure"""
        if not self.memory_config.enable_graph_analysis:
            return {'message': 'Graph analysis disabled'}
        
        try:
            import networkx as nx
            graph = self.memory_manager.graph
            
            return {
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'density': nx.density(graph) if graph.number_of_nodes() > 0 else 0,
                'connected_components': nx.number_connected_components(graph.to_undirected()),
                'average_clustering': nx.average_clustering(graph.to_undirected()) if graph.number_of_nodes() > 0 else 0
            }
        except ImportError:
            return {
                'message': 'NetworkX not available for graph analysis',
                'nodes': len(self.memory_manager.nodes),
                'basic_stats': True
            }
    
    def _get_age_distribution(self, nodes: List[MemoryNode]) -> Dict:
        """Get distribution of memory ages"""
        current_time = time.time()
        ages_hours = [(current_time - node.creation_time) / 3600 for node in nodes]
        
        if not ages_hours:
            return {'bins': [], 'counts': []}
        
        try:
            import numpy as np
            hist, bins = np.histogram(ages_hours, bins=5)
            return {
                'bins_hours': bins.tolist(),
                'counts': hist.tolist()
            }
        except ImportError:
            # Simple binning without numpy
            min_age, max_age = min(ages_hours), max(ages_hours)
            bin_size = (max_age - min_age) / 5 if max_age > min_age else 1.0
            
            bins = [min_age + i * bin_size for i in range(6)]
            counts = [0] * 5
            
            for age in ages_hours:
                bin_idx = min(int((age - min_age) / bin_size), 4) if bin_size > 0 else 0
                counts[bin_idx] += 1
            
            return {
                'bins_hours': bins,
                'counts': counts
            }
    
    def _update_operation_stats(self, operation: str, memory_type: Optional[MemoryType] = None):
        """Update operation statistics"""
        self.echo_memory_stats['total_operations'] += 1
        self.echo_memory_stats['last_operation_time'] = time.time()
        
        if memory_type:
            self.echo_memory_stats['memory_types_used'].add(memory_type.value)
    
    def _update_memory_stats(self):
        """Update comprehensive memory statistics"""
        nodes = self.memory_manager.nodes.values()
        
        # Most accessed memories
        sorted_by_access = sorted(nodes, key=lambda n: n.access_count, reverse=True)
        self.echo_memory_stats['most_accessed_memories'] = [
            {'id': n.id, 'access_count': n.access_count, 'content': n.content[:50] + '...' if len(n.content) > 50 else n.content}
            for n in sorted_by_access[:5]
        ]
        
        # Echo value distribution
        self.echo_memory_stats['echo_value_distribution'] = self._get_echo_distribution()
    
    def _check_auto_save(self):
        """Check if auto-save is needed"""
        if time.time() - self.last_save_time > self.memory_config.auto_save_interval:
            self.memory_manager.save()
            self.last_save_time = time.time()
            self.logger.debug("Auto-saved memory system")
    
    # Convenience methods for common operations
    def store_memory(self, content: str, memory_type: MemoryType = MemoryType.DECLARATIVE, 
                    echo_value: float = 0.0, source: str = "echo_system", 
                    metadata: Optional[Dict] = None) -> EchoResponse:
        """Convenience method to store a memory"""
        result = self.process({
            'operation': 'store',
            'content': content,
            'memory_type': memory_type.value,
            'echo_value': echo_value,
            'source': source,
            'metadata': metadata or {}
        })
        
        # Debug logging
        if result.success:
            self.logger.debug(f"Stored memory: '{content[:50]}...' with ID: {result.data.get('memory_id')}")
        
        return result
    
    def retrieve_memory(self, memory_id: str) -> EchoResponse:
        """Convenience method to retrieve a memory"""
        return self.process({
            'operation': 'retrieve',
            'memory_id': memory_id
        })
    
    def search_memories(self, query: str, memory_type: Optional[MemoryType] = None,
                       echo_threshold: float = 0.0, max_results: int = 10) -> EchoResponse:
        """Convenience method to search memories"""
        return self.process({
            'operation': 'search',
            'query': query,
            'memory_type': memory_type.value if memory_type else None,
            'echo_threshold': echo_threshold,
            'max_results': max_results
        })
    
    def get_memory_overview(self) -> EchoResponse:
        """Convenience method to get memory overview"""
        return self.process({'operation': 'analyze', 'analysis_type': 'overview'})
    
    def save_memories(self) -> EchoResponse:
        """Save all memories to persistent storage"""
        try:
            self.memory_manager.save()
            self.last_save_time = time.time()
            
            return EchoResponse(
                success=True,
                message="Memories saved successfully",
                metadata={'save_time': self.last_save_time}
            )
        except Exception as e:
            return self.handle_error(e, "save_memories")


def create_unified_memory_system(component_name: str = "UnifiedEchoMemory",
                                storage_path: str = "memory_storage") -> UnifiedEchoMemory:
    """
    Factory function to create a unified Echo memory system
    
    Args:
        component_name: Name for the memory component
        storage_path: Path for persistent memory storage
        
    Returns:
        Configured UnifiedEchoMemory instance
    """
    # Create Echo configuration
    echo_config = EchoConfig(
        component_name=component_name,
        version="1.0.0",
        echo_threshold=0.75,
        debug_mode=False
    )
    
    # Create memory-specific configuration
    memory_config = EchoMemoryConfig(
        memory_storage_path=storage_path,
        working_memory_capacity=7,
        auto_save_interval=300,
        enable_embeddings=True,
        enable_graph_analysis=True
    )
    
    # Create and initialize the memory system
    memory_system = UnifiedEchoMemory(echo_config, memory_config)
    init_result = memory_system.initialize()
    
    if not init_result.success:
        raise RuntimeError(f"Failed to initialize memory system: {init_result.message}")
    
    return memory_system