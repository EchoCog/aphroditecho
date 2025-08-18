"""
Temporal Processing System for Deep Tree Echo

This module handles the timing cycles for cognitive memory processing,
including scheduling and executing memory operations with different frequencies.
"""

import logging
import threading
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple

from database import db
from models_memory import MemoryCycle, MemoryNode, MemoryAssociation, PatternTemplate, DreamState

logger = logging.getLogger(__name__)

class TemporalProcessor:
    """
    Manages temporal processing cycles for the memory system.
    """
    def __init__(self):
        self.running = False
        self.thread = None
        self.cycle_handlers = {}  # name -> handler function
        self.default_cycles = {
            'sensory': {
                'name': 'sensory_processing',
                'cycle_type': 'fast',
                'duration_ms': 50,  # 50ms (20Hz)
                'variance_percent': 10.0,
                'description': 'Fast sensory processing cycle for immediate perceptual input',
                'function': self._process_sensory_cycle
            },
            'working_memory': {
                'name': 'working_memory',
                'cycle_type': 'medium',
                'duration_ms': 1000,  # 1 second
                'variance_percent': 15.0,
                'description': 'Medium-speed cycle for working memory operations',
                'function': self._process_working_memory_cycle
            },
            'consolidation': {
                'name': 'memory_consolidation',
                'cycle_type': 'slow',
                'duration_ms': 30000,  # 30 seconds
                'variance_percent': 20.0,
                'description': 'Slow cycle for memory consolidation and organization',
                'function': self._process_consolidation_cycle
            },
            'sleep': {
                'name': 'sleep_cycle',
                'cycle_type': 'ultra-slow',
                'duration_ms': 300000,  # 5 minutes
                'variance_percent': 30.0,
                'description': 'Ultra-slow cycle for REM-like sleep processing and dreaming',
                'function': self._process_sleep_cycle
            }
        }
        
        # Initialize active cycles
        self.active_cycles = {}  # id -> next execution time
        
        # Store most recent activations for pattern matching
        self.recent_activations = []  # List of recently activated memory nodes
        self.max_recent = 100  # Maximum size of recent activations list
        
        # Current state
        self.current_dream_state = None  # Current dream state, if any
        self.system_load = 0.0  # 0.0 to 1.0, current system load
        
    def register_handler(self, cycle_name: str, handler: Callable):
        """Register a handler function for a specific cycle."""
        self.cycle_handlers[cycle_name] = handler
        
    def initialize_default_cycles(self):
        """Initialize default cycle types in the database if they don't exist."""
        from app import app
        
        with app.app_context():
            for cycle_key, cycle_data in self.default_cycles.items():
                # Check if cycle exists
                existing = MemoryCycle.query.filter_by(name=cycle_data['name']).first()
                if not existing:
                    # Create new cycle
                    cycle = MemoryCycle(
                        name=cycle_data['name'],
                        cycle_type=cycle_data['cycle_type'],
                        duration_ms=cycle_data['duration_ms'],
                        variance_percent=cycle_data['variance_percent'],
                        description=cycle_data['description']
                    )
                    
                    # Register handler
                    self.register_handler(cycle_data['name'], cycle_data['function'])
                    
                    # Add to database
                    db.session.add(cycle)
                    
            # Commit changes
            db.session.commit()
            logger.info("Default temporal cycles initialized")
            
            # Load active cycles
            self._load_active_cycles()
    
    def _load_active_cycles(self):
        """Load active cycles from the database into memory."""
        active_cycles = MemoryCycle.query.filter_by(enabled=True).all()
        
        for cycle in active_cycles:
            # Calculate next execution time if needed
            if not cycle.next_scheduled or cycle.next_scheduled < datetime.utcnow():
                cycle.calculate_next_execution()
                db.session.commit()
            
            # Add to active cycles
            self.active_cycles[cycle.id] = cycle.next_scheduled
            
            # Register default handler if available and none is registered
            if cycle.name in self.default_cycles and cycle.name not in self.cycle_handlers:
                self.register_handler(cycle.name, self.default_cycles[cycle.name]['function'])
        
        logger.info(f"Loaded {len(self.active_cycles)} active temporal cycles")
    
    def start(self):
        """Start the temporal processor in a background thread."""
        if self.running:
            logger.warning("Temporal processor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Temporal processor started")
    
    def stop(self):
        """Stop the temporal processor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("Temporal processor stopped")
    
    def _run_loop(self):
        """Main processing loop for temporal cycles."""
        from app import app
        
        logger.info("Temporal processor loop started")
        
        while self.running:
            with app.app_context():
                current_time = datetime.utcnow()
                
                # Find cycles ready to execute
                ready_cycles = []
                for cycle_id, next_time in list(self.active_cycles.items()):
                    if next_time <= current_time:
                        ready_cycles.append(cycle_id)
                
                # Execute ready cycles
                for cycle_id in ready_cycles:
                    try:
                        self._execute_cycle(cycle_id)
                    except Exception as e:
                        logger.error(f"Error executing cycle {cycle_id}: {e}")
                
                # Calculate system load (0.0 to 1.0) based on how many cycles executed
                self.system_load = min(1.0, len(ready_cycles) / max(1, len(self.active_cycles)))
            
            # Sleep for a short time before checking again
            # Use a small interval to ensure we don't miss cycles
            time.sleep(0.01)  # 10ms
    
    def _execute_cycle(self, cycle_id: int):
        """Execute a specific temporal cycle."""
        # Get cycle from database
        cycle = MemoryCycle.query.get(cycle_id)
        if not cycle or not cycle.enabled:
            # Cycle has been disabled or deleted
            if cycle_id in self.active_cycles:
                del self.active_cycles[cycle_id]
            return
        
        start_time = datetime.utcnow()
        result = None
        
        try:
            # Execute cycle handler if available
            if cycle.name in self.cycle_handlers:
                handler = self.cycle_handlers[cycle.name]
                result = handler(cycle)
            else:
                # Default processing if no handler is registered
                result = self._default_cycle_handler(cycle)
            
            # Record execution
            cycle.last_execution = start_time
            cycle.execution_count += 1
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update average execution time
            if cycle.execution_count > 1:
                cycle.avg_execution_time_ms = (
                    (cycle.avg_execution_time_ms * (cycle.execution_count - 1) + execution_time_ms) / 
                    cycle.execution_count
                )
            else:
                cycle.avg_execution_time_ms = execution_time_ms
            
            # Store result if available
            if result:
                cycle.set_last_result(result)
            
            # Calculate next execution time
            cycle.calculate_next_execution()
            
            # Update active cycles
            self.active_cycles[cycle_id] = cycle.next_scheduled
            
            # Commit changes
            db.session.commit()
            
            logger.debug(f"Executed cycle {cycle.name} in {execution_time_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error in cycle {cycle.name}: {e}")
            # Still update next execution time to prevent repeated failures
            cycle.calculate_next_execution()
            self.active_cycles[cycle_id] = cycle.next_scheduled
            db.session.commit()
    
    def _default_cycle_handler(self, cycle: MemoryCycle) -> Dict:
        """Default handler for cycles without a specific handler."""
        return {
            'status': 'default_executed',
            'cycle_name': cycle.name,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    #
    # Default cycle handlers
    #
    
    def _process_sensory_cycle(self, cycle: MemoryCycle) -> Dict:
        """Process sensory input cycle."""
        # This would normally process immediate sensory input
        # For simulation, we'll just decay all active memory nodes slightly
        
        # Get memory nodes with non-zero activation
        active_nodes = MemoryNode.query.filter(MemoryNode.activation_level > 0).all()
        
        for node in active_nodes:
            # Apply decay
            node.decay()
        
        # Commit changes
        db.session.commit()
        
        return {
            'status': 'processed',
            'active_nodes_count': len(active_nodes),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _process_working_memory_cycle(self, cycle: MemoryCycle) -> Dict:
        """Process working memory cycle."""
        # This would normally process working memory operations
        # For simulation, we'll activate a random memory node
        
        # Get all memory nodes
        nodes = MemoryNode.query.all()
        
        if nodes:
            # Select a random node to activate
            random_node = random.choice(nodes)
            
            # Activate the node
            random_node.activate()
            
            # Add to recent activations
            self.recent_activations.append({
                'node_id': random_node.id,
                'timestamp': datetime.utcnow().isoformat(),
                'cycle_name': cycle.name
            })
            
            # Trim recent activations if needed
            if len(self.recent_activations) > self.max_recent:
                self.recent_activations = self.recent_activations[-self.max_recent:]
            
            # Commit changes
            db.session.commit()
            
            return {
                'status': 'processed',
                'activated_node': random_node.id,
                'memory_type': random_node.memory_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {
            'status': 'no_nodes',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _process_consolidation_cycle(self, cycle: MemoryCycle) -> Dict:
        """Process memory consolidation cycle."""
        # This cycle consolidates memories and creates new associations
        
        # Get recently activated memory nodes
        recent_node_ids = [a['node_id'] for a in self.recent_activations[-20:]]
        if not recent_node_ids:
            return {
                'status': 'no_recent_activations',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Get the actual nodes
        nodes = MemoryNode.query.filter(MemoryNode.id.in_(recent_node_ids)).all()
        if len(nodes) < 2:
            return {
                'status': 'insufficient_nodes',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Create new associations between nodes that don't already have one
        new_associations = []
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # Check if association already exists
                existing = MemoryAssociation.query.filter(
                    ((MemoryAssociation.source_id == node1.id) & 
                     (MemoryAssociation.target_id == node2.id)) |
                    ((MemoryAssociation.source_id == node2.id) & 
                     (MemoryAssociation.target_id == node1.id))
                ).first()
                
                if not existing:
                    # Create new association
                    assoc = MemoryAssociation(
                        source_id=node1.id,
                        target_id=node2.id,
                        association_type='temporal_co_activation',
                        strength=0.5,
                        bidirectional=True
                    )
                    db.session.add(assoc)
                    new_associations.append({
                        'source_id': node1.id,
                        'target_id': node2.id
                    })
        
        # Increase consolidation stage for all nodes
        for node in nodes:
            node.consolidation_stage += 1
        
        # Commit changes
        db.session.commit()
        
        return {
            'status': 'processed',
            'nodes_consolidated': len(nodes),
            'new_associations': len(new_associations),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _process_sleep_cycle(self, cycle: MemoryCycle) -> Dict:
        """Process sleep cycle with dream state and pattern integration."""
        # Check if we're already dreaming
        if self.current_dream_state:
            # Finalize current dream
            dream = DreamState.query.get(self.current_dream_state)
            if dream:
                dream.finalize()
                db.session.commit()
                
                result = {
                    'status': 'dream_completed',
                    'dream_id': dream.id,
                    'duration_seconds': dream.duration_seconds,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Clear current dream state
                self.current_dream_state = None
                
                return result
        
        # Start a new dream
        dream = DreamState(
            title=f"Dream {datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            dream_type='rem',
            start_time=datetime.utcnow()
        )
        
        # Get memory sources for dream (highly activated and recent nodes)
        memory_sources = MemoryNode.query.filter(
            (MemoryNode.activation_level > 0.7) |
            (MemoryNode.last_activated > (datetime.utcnow() - timedelta(hours=24)))
        ).limit(20).all()
        
        source_ids = [node.id for node in memory_sources]
        dream.set_source_memories(source_ids)
        
        # Get pattern templates for activation
        patterns = PatternTemplate.query.all()
        
        # Check which patterns are activated by the memory sources
        pattern_activations = {}
        for pattern in patterns:
            match_score = pattern.matches(memory_sources)
            if match_score >= pattern.activation_threshold:
                pattern_activations[pattern.id] = match_score
        
        dream.set_pattern_activations(pattern_activations)
        
        # Generate insights based on activated patterns
        insights = [
            f"Insight from pattern {pattern_id}: Connection strength {activation:.2f}"
            for pattern_id, activation in pattern_activations.items()
        ]
        
        dream.set_insights(insights)
        
        # Create new associations based on pattern activations
        new_associations = []
        if pattern_activations and memory_sources:
            # Create associations between nodes that match the same pattern
            for i, node1 in enumerate(memory_sources):
                for node2 in memory_sources[i+1:]:
                    # Create association with 20% probability
                    if random.random() < 0.2:
                        # Check if association already exists
                        existing = MemoryAssociation.query.filter(
                            ((MemoryAssociation.source_id == node1.id) & 
                             (MemoryAssociation.target_id == node2.id)) |
                            ((MemoryAssociation.source_id == node2.id) & 
                             (MemoryAssociation.target_id == node1.id))
                        ).first()
                        
                        if not existing:
                            # Create new association
                            assoc = MemoryAssociation(
                                source_id=node1.id,
                                target_id=node2.id,
                                association_type='dream_integration',
                                strength=0.3,
                                bidirectional=True
                            )
                            db.session.add(assoc)
                            new_associations.append({
                                'source_id': node1.id,
                                'target_id': node2.id
                            })
        
        dream.set_new_associations(new_associations)
        
        # Set dream content (placeholder)
        dream.set_content({
            'narrative': 'Dream narrative would be generated here',
            'symbols': ['symbol1', 'symbol2', 'symbol3'],
            'emotions': {
                'joy': 0.3,
                'fear': 0.1,
                'curiosity': 0.6
            }
        })
        
        # Set dream properties
        dream.emotional_tone = random.uniform(-0.3, 0.7)  # Slightly biased toward positive
        dream.coherence = random.uniform(0.3, 0.8)
        
        # Save dream state
        db.session.add(dream)
        db.session.commit()
        
        # Set current dream state
        self.current_dream_state = dream.id
        
        return {
            'status': 'dream_started',
            'dream_id': dream.id,
            'source_memories': len(source_ids),
            'patterns_activated': len(pattern_activations),
            'insights_generated': len(insights),
            'new_associations': len(new_associations),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    #
    # Public API
    #
    
    def create_memory_node(self, base_node_id: int, memory_type: str, 
                         activation: float = 0.5, **kwargs) -> MemoryNode:
        """Create a new memory node linked to a self-referential node."""
        memory_node = MemoryNode(
            node_id=base_node_id,
            memory_type=memory_type,
            activation_level=activation,
            **kwargs
        )
        
        # Add to database
        db.session.add(memory_node)
        db.session.commit()
        
        return memory_node
    
    def get_active_memories(self, threshold: float = 0.3, limit: int = 10) -> List[MemoryNode]:
        """Get currently active memory nodes above the threshold."""
        return MemoryNode.query.filter(
            MemoryNode.activation_level >= threshold
        ).order_by(MemoryNode.activation_level.desc()).limit(limit).all()
    
    def get_memory_by_type(self, memory_type: str, limit: int = 10) -> List[MemoryNode]:
        """Get memory nodes of a specific type."""
        return MemoryNode.query.filter_by(memory_type=memory_type).limit(limit).all()
    
    def activate_memory(self, memory_id: int, amount: float = 0.5) -> float:
        """Activate a specific memory node."""
        memory_node = MemoryNode.query.get(memory_id)
        if memory_node:
            activation = memory_node.activate(amount)
            db.session.commit()
            
            # Add to recent activations
            self.recent_activations.append({
                'node_id': memory_node.id,
                'timestamp': datetime.utcnow().isoformat(),
                'cycle_name': 'explicit_activation'
            })
            
            # Trim recent activations if needed
            if len(self.recent_activations) > self.max_recent:
                self.recent_activations = self.recent_activations[-self.max_recent:]
            
            return activation
        return 0.0
    
    def create_pattern_template(self, name: str, pattern_type: str, 
                              structure: Dict, rules: Dict, 
                              user_id: Optional[int] = None) -> PatternTemplate:
        """Create a new pattern template."""
        pattern = PatternTemplate(
            name=name,
            pattern_type=pattern_type,
            user_id=user_id
        )
        
        pattern.set_structure(structure)
        pattern.set_rules(rules)
        
        # Add to database
        db.session.add(pattern)
        db.session.commit()
        
        return pattern
    
    def get_dream_history(self, limit: int = 10) -> List[DreamState]:
        """Get history of dream states."""
        return DreamState.query.order_by(DreamState.start_time.desc()).limit(limit).all()
    
    def get_system_state(self) -> Dict:
        """Get current state of the temporal processing system."""
        # Count active cycles by type
        cycle_counts = {}
        for cycle_id in self.active_cycles:
            cycle = MemoryCycle.query.get(cycle_id)
            if cycle:
                cycle_type = cycle.cycle_type
                cycle_counts[cycle_type] = cycle_counts.get(cycle_type, 0) + 1
        
        # Get memory node counts by type
        memory_counts = {}
        memory_types = db.session.query(MemoryNode.memory_type, db.func.count(MemoryNode.id)).\
            group_by(MemoryNode.memory_type).all()
        for memory_type, count in memory_types:
            memory_counts[memory_type] = count
        
        # Get counts of active memories
        active_count = MemoryNode.query.filter(MemoryNode.activation_level > 0).count()
        
        # Get dream state
        current_dream = None
        if self.current_dream_state:
            dream = DreamState.query.get(self.current_dream_state)
            if dream:
                current_dream = {
                    'id': dream.id,
                    'title': dream.title,
                    'start_time': dream.start_time.isoformat() if dream.start_time else None,
                    'duration_so_far': (datetime.utcnow() - dream.start_time).total_seconds() if dream.start_time else 0,
                    'type': dream.dream_type
                }
        
        return {
            'running': self.running,
            'system_load': self.system_load,
            'active_cycles': len(self.active_cycles),
            'cycle_counts': cycle_counts,
            'memory_counts': memory_counts,
            'active_memories': active_count,
            'recent_activations': len(self.recent_activations),
            'current_dream': current_dream,
            'timestamp': datetime.utcnow().isoformat()
        }

# Global instance
temporal_processor = TemporalProcessor()