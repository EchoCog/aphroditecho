"""
Echoself Introspection Module

Hypergraph-encoded recursive self-model introspection
Inspired by DeepTreeEcho/Eva Self Model and echoself.md

This module implements the recursive self-model integration with hypergraph encoding
and adaptive attention allocation as specified in the Echoself vision.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class HypergraphNode:
    """Hypergraph node representation"""
    id: str
    node_type: str
    content: str
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    salience_score: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.node_type,
            'content': self.content,
            'links': self.links,
            'metadata': self.metadata,
            'salience': self.salience_score,
            'timestamp': self.timestamp
        }


class EchoselfIntrospection:
    """
    Recursive self-model introspection system with hypergraph encoding
    and adaptive attention allocation
    """
    
    # Constants for attention allocation
    MAX_FILE_SIZE = 50000  # 50 KB maximum file size
    BASE_ATTENTION_THRESHOLD = 0.5
    
    def __init__(self, root_path: str = "."):
        self.logger = logging.getLogger(__name__)
        self.root_path = Path(root_path).resolve()
        self.hypergraph_nodes: Dict[str, HypergraphNode] = {}
        self.attention_history: List[Tuple[float, Dict[str, Any]]] = []
        
    def semantic_salience(self, path: str) -> float:
        """
        Assign salience scores based on heuristics:
        Core directories/files, recent changes, configured targets
        """
        path_str = str(path).lower()
        
        # High-priority cognitive architecture files
        if "btree-psi.scm" in path_str:
            return 0.98
        elif "eva-model" in path_str or "eva_model" in path_str:
            return 0.95
        elif "eva-behavior" in path_str or "eva_behavior" in path_str:
            return 0.92
        elif "echoself" in path_str:
            return 0.95
        elif "cognitive" in path_str:
            return 0.90
        elif "deep_tree_echo" in path_str:
            return 0.88
        
        # Documentation and architecture files
        elif path_str.endswith("readme.md") or path_str.endswith("readme"):
            return 0.9
        elif "architecture" in path_str:
            return 0.85
        elif "components" in path_str:
            return 0.82
        elif "data_flows" in path_str:
            return 0.80
        
        # Source code directories
        elif "/src/" in path_str or path_str.startswith("src/"):
            return 0.85
        elif "/core/" in path_str or path_str.startswith("core/"):
            return 0.90
        
        # Python implementation files
        elif path_str.endswith(".py"):
            if "test_" in path_str:
                return 0.70
            elif any(keyword in path_str for keyword in 
                    ["cognitive", "emotional", "memory", "personality"]):
                return 0.85
            else:
                return 0.75
        
        # Configuration and build files
        elif path_str.endswith((".json", ".yml", ".yaml", ".toml")):
            return 0.65
        elif path_str.endswith((".md", ".txt", ".rst")):
            return 0.60
        
        # Legacy or obsolete files
        elif "btree.scm" in path_str and "psi" not in path_str:
            return 0.70
        
        # Default for unknown files
        else:
            return 0.5
    
    def adaptive_attention(self, current_load: float, recent_activity: float) -> float:
        """
        Adjust attention threshold based on cognitive load and recent activity
        High load or low activity leads to higher threshold (less data)
        """
        threshold = (self.BASE_ATTENTION_THRESHOLD + 
                    (current_load * 0.3) + 
                    (0.2 - recent_activity))
        
        # Record attention decision for analysis
        self.attention_history.append((threshold, {
            "current_load": current_load,
            "recent_activity": recent_activity,
            "timestamp": time.time()
        }))
        
        # Keep only recent history
        if len(self.attention_history) > 1000:
            self.attention_history = self.attention_history[-500:]
        
        return max(0.1, min(0.95, threshold))  # Clamp to reasonable range
    
    def repo_file_list(self, root: Path, attention_threshold: float) -> List[Path]:
        """
        Recursive repository traversal with attention filtering
        """
        files = []
        
        try:
            if root.is_file():
                if self.semantic_salience(str(root)) > attention_threshold:
                    files.append(root)
            elif root.is_dir():
                # Skip hidden directories and common build/cache directories
                if (root.name.startswith('.') and 
                    root.name not in ['.github', '.vscode', '.devcontainer']):
                    return files
                if root.name in ['__pycache__', 'node_modules', 'dist', 'build', 
                                'target', '.git', 'browser_data', 'chrome_user_data']:
                    return files
                
                for child in root.iterdir():
                    files.extend(self.repo_file_list(child, attention_threshold))
        except (PermissionError, OSError) as e:
            self.logger.debug(f"Skipping {root}: {e}")
        
        return files
    
    def safe_read_file(self, path: Path) -> str:
        """
        Adaptive file reading with size constraints
        """
        try:
            if not path.exists():
                return "[File not found]"
            
            file_size = path.stat().st_size
            if file_size == 0:
                return "[Empty file]"
            elif file_size > self.MAX_FILE_SIZE:
                return f"[File too large: {file_size} bytes, summarized or omitted]"
            
            # Try to read as text
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(path, 'r', encoding='latin-1') as f:
                        content = f.read()
                        return f"[Binary/non-UTF-8 content, {len(content)} chars]"
                except:
                    return "[Binary file content unavailable]"
        except Exception as e:
            self.logger.debug(f"Error reading {path}: {e}")
            return f"[Error reading file: {e}]"
    
    def make_node(self, node_id: str, node_type: str, content: str, 
                  links: List[str] = None) -> HypergraphNode:
        """Create a hypergraph node"""
        return HypergraphNode(
            id=node_id,
            node_type=node_type,
            content=content,
            links=links or [],
            salience_score=self.semantic_salience(node_id)
        )
    
    def assemble_hypergraph_input(self, root: Path, 
                                 attention_threshold: float) -> List[HypergraphNode]:
        """
        Assemble hypergraph-encoded input from repository files
        """
        nodes = []
        try:
            for file_path in self.filter_files_by_salience(root, attention_threshold):
                content = self.safe_read_file(file_path)
                node = self.make_node(
                    node_id=str(file_path),
                    node_type="file",
                    content=content
                )
                nodes.append(node)
        except Exception as e:
            self.logger.error("Error assembling hypergraph input: %s", str(e))
        return nodes

class SemanticSalienceAssessor:
    """Semantic salience assessment based on heuristics"""
    
    def __init__(self):
        # Salience weights for different path patterns (order matters - check most specific first)
        self.salience_patterns = [
            ('btree-psi.scm', 0.98),
            ('eva-model', 0.95),
            ('echoself.md', 0.95),
            ('eva-behavior', 0.92),
            ('readme', 0.9),  # Case insensitive
            ('architecture.md', 0.9),
            ('deep_tree_echo', 0.85),
            ('components.md', 0.85),
            ('src/', 0.85),
            ('cognitive_', 0.8),
            ('memory_', 0.8),
            ('btree.scm', 0.7),
            ('.md', 0.7),
            ('.py', 0.6),
            ('test_', 0.5),
            ('__pycache__', 0.1),
            ('.git', 0.1),
            ('node_modules', 0.1),
        ]
        
    def assess_semantic_salience(self, path: str) -> float:
        """
        Assign salience scores based on heuristics
        Translated from Scheme semantic-salience function
        """
        path_str = str(path).lower()
        
        # Check patterns in order of specificity
        for pattern, salience in self.salience_patterns:
            if pattern.lower() in path_str:
                return salience
                
        # Default salience for unmatched files
        return 0.5

class AdaptiveAttentionAllocator:
    """Adaptive attention allocation mechanism"""
    
    def __init__(self):
        self.base_threshold = 0.5
        
    def adaptive_attention(self, current_load: float, recent_activity: float) -> float:
        """
        Dynamically adjust attention threshold based on cognitive load and recent activity
        Translated from Scheme adaptive-attention function
        
        High load or low activity leads to higher threshold (less data processed)
        """
        threshold = self.base_threshold + (current_load * 0.3) + (0.2 - recent_activity)
        # Ensure threshold stays within reasonable bounds
        return max(0.0, min(1.0, threshold))

class RepositoryIntrospector:
    """Recursive repository introspection with attention filtering"""
    
    def __init__(self, max_file_size: int = 50000, root_path: Path = None):
        self.max_file_size = max_file_size
        self.root_path = root_path or Path.cwd()
        self.logger = logging.getLogger(__name__)
        self.salience_assessor = SemanticSalienceAssessor()
        self.attention_allocator = AdaptiveAttentionAllocator()
        
    def is_valid_file(self, path: Path) -> bool:
        """Check if file should be processed"""
        if not path.exists() or not path.is_file():
            return False
            
        # Skip binary files and other non-text files
        binary_extensions = {'.pyc', '.so', '.dll', '.exe', '.bin', '.jpg', '.png', '.gif', '.pdf'}
        if path.suffix.lower() in binary_extensions:
            return False
            
        try:
            file_size = path.stat().st_size
            return file_size > 0 and file_size <= self.max_file_size
        except (OSError, IOError):
            return False
    
    def safe_read_file(self, path: Path) -> str:
        """
        Safely read file content with size constraints
        Translated from Scheme safe-read-file function
        """
        try:
            if not path.exists() or not path.is_file():
                return "[File not accessible]"
                
            file_size = path.stat().st_size
            
            # Check file size first
            if file_size > self.max_file_size:
                return f"[File too large: {file_size} bytes, summarized or omitted]"
            
            # Check if it's a binary file
            binary_extensions = {'.pyc', '.so', '.dll', '.exe', '.bin', '.jpg', '.png', '.gif', '.pdf'}
            if path.suffix.lower() in binary_extensions:
                return "[File not accessible or binary]"
                
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading file {path}: {e}")
            return f"[Error reading file: {e}]"
    
    def make_node(self, node_id: str, node_type: str, content: str, 
                  links: List[str] = None) -> HypergraphNode:
        """Create a hypergraph node"""
        salience = self.salience_assessor.assess_semantic_salience(node_id)
        return HypergraphNode(
            id=node_id,
            node_type=node_type,
            content=content,
            links=links or [],
            salience_score=salience
        )
    
    def repo_file_list(self, root: Path, attention_threshold: float) -> List[Path]:
        """
        Recursive repository traversal with attention filtering
        Translated from Scheme repo-file-list function
        """
        if not root.exists():
            return []
            
        if root.is_file():
            salience = self.salience_assessor.assess_semantic_salience(str(root))
            if salience > attention_threshold:
                return [root]
            else:
                return []
        
        # Directory traversal
        files = []
        try:
            for item in root.iterdir():
                if item.name.startswith('.') and item.name not in {'.gitignore', '.env.example'}:
                    continue  # Skip hidden files except important ones
                    
                files.extend(self.repo_file_list(item, attention_threshold))
                
        except (OSError, PermissionError) as e:
            logger.warning(f"Error accessing directory {root}: {e}")
            
        return files

    def assemble_hypergraph_input(self, root: Path, attention_threshold: float) -> List[HypergraphNode]:
        """
        Assemble hypergraph-encoded input from repository files
        Translated from Scheme assemble-hypergraph-input function
        """
        files = self.repo_file_list(root, attention_threshold)
        nodes = []
        for file_path in files:
            content = self.safe_read_file(file_path)
            relative_path = str(file_path.relative_to(self.root_path))
            
            node = self.make_node(relative_path, 'file', content)
            nodes.append(node)
        
        # Sort by salience score for better organization
        nodes.sort(key=lambda n: n.salience_score, reverse=True)
        
        self.logger.info(f"Assembled {len(nodes)} hypergraph nodes with "
                        f"threshold {attention_threshold:.3f}")
        
        return nodes
    
    def hypergraph_to_string(self, nodes: List[HypergraphNode]) -> str:
        """
        Convert hypergraph nodes to string representation
        """
        parts = []
        for node in nodes:
            # Truncate very long content for readability
            content = node.content
            if len(content) > 2000:
                content = content[:2000] + "\n... [content truncated]"
            
            parts.append(f'(file "{node.id}" """\n{content}\n""")')
        
        return '\n\n'.join(parts)
    
    def prompt_template(self, input_content: str) -> str:
        """
        Create prompt template for DeepTreeEcho
        """
        return f"""DeepTreeEcho Recursive Self-Model Introspection:

Repository Hypergraph Analysis:
{input_content}

Please analyze this repository structure and content for:
1. Cognitive architecture patterns
2. Emergent self-model opportunities  
3. Neural-symbolic integration points
4. Attention allocation optimization
5. Recursive improvement pathways
"""
    
    def inject_repo_input_into_prompt(self, current_load: float = 0.5, 
                                     recent_activity: float = 0.3) -> str:
        """
        Inject repository input into prompt template with adaptive attention
        """
        attention_threshold = self.adaptive_attention(current_load, recent_activity)
        nodes = self.assemble_hypergraph_input(self.root_path, attention_threshold)
        
        hypergraph_string = self.hypergraph_to_string(nodes)
        prompt = self.prompt_template(hypergraph_string)
        
        # Log introspection metadata
        self.logger.info(f"Generated introspection prompt with {len(nodes)} files, "
                        f"attention threshold: {attention_threshold:.3f}")
        
        return prompt
    
    def get_attention_metrics(self) -> Dict[str, Any]:
        """Get attention allocation metrics for analysis"""
        if not self.attention_history:
            return {"message": "No attention history available"}
        
        recent_thresholds = [entry[0] for entry in self.attention_history[-10:]]
        recent_loads = [entry[1]["current_load"] for entry in self.attention_history[-10:]]
        
        return {
            "recent_average_threshold": sum(recent_thresholds) / len(recent_thresholds),
            "recent_average_load": sum(recent_loads) / len(recent_loads),
            "total_decisions": len(self.attention_history),
            "hypergraph_nodes": len(self.hypergraph_nodes),
            "highest_salience_files": [
                (node.id, node.salience_score) 
                for node in sorted(self.hypergraph_nodes.values(), 
                                 key=lambda n: n.salience_score, reverse=True)[:5]
            ]
        }
    
    def export_hypergraph(self, output_path: str) -> None:
        """Export hypergraph structure to JSON for analysis"""
        export_data = {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.node_type,
                    "salience_score": node.salience_score,
                    "content_length": len(node.content),
                    "links": node.links,
                    "metadata": node.metadata,
                    "timestamp": node.timestamp
                }
                for node in self.hypergraph_nodes.values()
            ],
            "attention_history": [
                {
                    "threshold": entry[0],
                    "context": entry[1]
                }
                for entry in self.attention_history[-100:]  # Last 100 entries
            ],
            "export_timestamp": time.time()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported hypergraph to {output_path}")


def main():
    """
    Example usage of EchoselfIntrospection
    """
    logging.basicConfig(level=logging.INFO)
    
    # Initialize introspection system
    introspector = EchoselfIntrospection(".")
    
    # Generate introspection prompt with current cognitive state
    prompt = introspector.inject_repo_input_into_prompt(
        current_load=0.6,  # Moderate cognitive load
        recent_activity=0.4  # Some recent activity
    )
    
    print("=== ECHOSELF INTROSPECTION PROMPT ===")
    print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
    
    # Show attention metrics
    metrics = introspector.get_attention_metrics()
    print(f"\n=== ATTENTION METRICS ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    # Export hypergraph for analysis
    introspector.export_hypergraph("echoself_hypergraph.json")

class HypergraphStringSerializer:
    """Hypergraph to string serialization for prompt integration"""
    
    @staticmethod
    def hypergraph_to_string(nodes: List[HypergraphNode]) -> str:
        """
        Convert hypergraph nodes to string representation
        Translated from Scheme hypergraph->string function
        """
        result = []
        for node in nodes:
            # Format: (file "path" "content")
            escaped_content = node.content.replace('"', '\\"').replace('\n', '\\n')[:1000]  # Limit content length
            result.append(f'(file "{node.id}" "{escaped_content}")')
        
        return '\n'.join(result)

class EchoselfIntrospector:
    """Main introspection class integrating all components"""
    
    def __init__(self, repository_root: Optional[Path] = None):
        self.repository_root = repository_root or Path.cwd()
        self.introspector = RepositoryIntrospector(root_path=self.repository_root)
        self.serializer = HypergraphStringSerializer()
        self.attention_allocator = AdaptiveAttentionAllocator()
        
    def prompt_template(self, input_content: str) -> str:
        """
        Generate prompt template with repository input
        Translated from Scheme prompt-template function
        """
        return f"DeepTreeEcho Prompt:\n{input_content}"
    
    def inject_repo_input_into_prompt(self, current_load: float = 0.6, 
                                    recent_activity: float = 0.4) -> str:
        """
        Complete introspection pipeline: inject repository input into prompt
        Translated from Scheme inject-repo-input-into-prompt function
        """
        attention_threshold = self.attention_allocator.adaptive_attention(
            current_load, recent_activity
        )
        
        logger.info(f"Using attention threshold: {attention_threshold}")
        
        nodes = self.introspector.assemble_hypergraph_input(
            self.repository_root, attention_threshold
        )
        
        logger.info(f"Assembled {len(nodes)} hypergraph nodes")
        
        hypergraph_string = self.serializer.hypergraph_to_string(nodes)
        
        return self.prompt_template(hypergraph_string)
    
    def get_cognitive_snapshot(self, current_load: float = 0.6, 
                             recent_activity: float = 0.4) -> Dict[str, Any]:
        """
        Get comprehensive cognitive snapshot for neural-symbolic integration
        """
        attention_threshold = self.attention_allocator.adaptive_attention(
            current_load, recent_activity
        )
        
        nodes = self.introspector.assemble_hypergraph_input(
            self.repository_root, attention_threshold
        )
        
        # Aggregate statistics
        total_files = len(nodes)
        avg_salience = sum(node.salience_score for node in nodes) / total_files if total_files > 0 else 0
        high_salience_files = [node for node in nodes if node.salience_score > 0.8]
        
        return {
            'timestamp': time.time(),
            'attention_threshold': attention_threshold,
            'cognitive_load': current_load,
            'recent_activity': recent_activity,
            'total_files_processed': total_files,
            'average_salience': avg_salience,
            'high_salience_count': len(high_salience_files),
            'nodes': [node.to_dict() for node in nodes],
            'repository_root': str(self.repository_root)
        }

# Example usage and integration point
def main():
    """Example usage of the introspection system"""
    introspector = EchoselfIntrospector()
    
    # Example of adaptive attention usage
    prompt = introspector.inject_repo_input_into_prompt(
        current_load=0.6, 
        recent_activity=0.4
    )
    
    print("Generated prompt snippet:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    # Get cognitive snapshot
    snapshot = introspector.get_cognitive_snapshot()
    print(f"\nCognitive snapshot: {snapshot['total_files_processed']} files, "
          f"avg salience: {snapshot['average_salience']:.3f}")

if __name__ == "__main__":
    main()