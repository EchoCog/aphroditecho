"""
Memory Models for Deep Tree Echo

This module contains SQLAlchemy models for the cognitive memory system,
including different memory types, temporal cycles, and pattern associations.
"""
from datetime import datetime
import json
from database import db
from models import User

# Association table for memory cycles and memory nodes
memory_cycle_association = db.Table('memory_cycle_association',
    db.Column('memory_node_id', db.Integer, db.ForeignKey('memory_node.id'), primary_key=True),
    db.Column('memory_cycle_id', db.Integer, db.ForeignKey('memory_cycle.id'), primary_key=True)
)

# Association table for pattern templates and memory nodes
pattern_node_association = db.Table('pattern_node_association',
    db.Column('memory_node_id', db.Integer, db.ForeignKey('memory_node.id'), primary_key=True),
    db.Column('pattern_template_id', db.Integer, db.ForeignKey('pattern_template.id'), primary_key=True)
)

class MemoryCycle(db.Model):
    """
    Model for timing cycles in cognitive processing.
    Represents different processing frequencies like fast sensory cycles,
    medium working memory cycles, slow consolidation, and REM-like pattern integration.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # e.g., 'alpha', 'rem', 'consolidation'
    cycle_type = db.Column(db.String(32), nullable=False)  # 'fast', 'medium', 'slow', 'ultra-slow'
    duration_ms = db.Column(db.Integer, nullable=False)  # base duration in milliseconds
    variance_percent = db.Column(db.Float, default=10.0)  # natural variance in timing
    last_execution = db.Column(db.DateTime)
    next_scheduled = db.Column(db.DateTime)
    priority = db.Column(db.Integer, default=5)  # 1-10, higher numbers = higher priority
    enabled = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    memory_nodes = db.relationship('MemoryNode', secondary=memory_cycle_association, 
                                  back_populates='processing_cycles')
    
    # Function data for the cycle's processing logic
    function_code = db.Column(db.Text)
    
    # Cycle state and history
    execution_count = db.Column(db.Integer, default=0)
    avg_execution_time_ms = db.Column(db.Float, default=0.0)
    last_result = db.Column(db.Text)  # JSON storage for last execution result
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_last_result(self):
        """Parse stored JSON last result."""
        if self.last_result:
            return json.loads(self.last_result)
        return {}
    
    def set_last_result(self, result_dict):
        """Store last result as JSON."""
        self.last_result = json.dumps(result_dict)
    
    def calculate_next_execution(self):
        """Calculate the next execution time based on duration and variance."""
        import random
        from datetime import timedelta
        
        # Apply variance to the duration
        variance_factor = 1.0 + (random.uniform(-self.variance_percent, self.variance_percent) / 100.0)
        actual_duration = self.duration_ms * variance_factor
        
        # Calculate next execution time
        if self.last_execution:
            self.next_scheduled = self.last_execution + timedelta(milliseconds=actual_duration)
        else:
            # First execution - start from now
            self.next_scheduled = datetime.utcnow() + timedelta(milliseconds=actual_duration)
        
        return self.next_scheduled

class MemoryNode(db.Model):
    """
    Extension of SelfReferentialNode with memory-specific properties.
    Represents different types of memory (semantic, episodic, procedural, etc.)
    with properties like activation level, decay, and association strength.
    """
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('self_referential_node.id'), nullable=False)
    memory_type = db.Column(db.String(32), nullable=False)  # 'semantic', 'episodic', 'procedural', etc.
    activation_level = db.Column(db.Float, default=0.0)  # current activation (0.0-1.0)
    decay_rate = db.Column(db.Float, default=0.05)  # how quickly activation decays
    consolidation_stage = db.Column(db.Integer, default=0)  # 0=new, higher=more consolidated
    emotional_valence = db.Column(db.Float, default=0.0)  # -1.0 to 1.0, negative to positive emotion
    emotional_arousal = db.Column(db.Float, default=0.0)  # 0.0 to 1.0, intensity of emotion
    salience = db.Column(db.Float, default=0.5)  # 0.0 to 1.0, importance/priority
    
    # Memory-specific metadata
    context = db.Column(db.Text)  # JSON storage for contextual information
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # When the memory was formed
    source = db.Column(db.String(64))  # Where the memory came from (e.g., 'chat', 'perception', 'dream')
    
    # Relationships
    base_node = db.relationship('SelfReferentialNode', foreign_keys=[node_id])
    processing_cycles = db.relationship('MemoryCycle', secondary=memory_cycle_association,
                                      back_populates='memory_nodes')
    pattern_templates = db.relationship('PatternTemplate', secondary=pattern_node_association,
                                      back_populates='memory_nodes')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing history
    last_activated = db.Column(db.DateTime)
    activation_count = db.Column(db.Integer, default=0)
    
    def get_context(self):
        """Parse stored JSON context."""
        if self.context:
            return json.loads(self.context)
        return {}
    
    def set_context(self, context_dict):
        """Store context as JSON."""
        self.context = json.dumps(context_dict)
    
    def activate(self, amount=0.5, record=True):
        """
        Activate this memory node by increasing its activation level.
        Returns the new activation level.
        """
        # Increase activation level, capped at 1.0
        self.activation_level = min(1.0, self.activation_level + amount)
        
        if record:
            # Record activation
            self.last_activated = datetime.utcnow()
            self.activation_count += 1
        
        return self.activation_level
    
    def decay(self, amount=None):
        """
        Decay the activation level of this memory node.
        Returns the new activation level.
        """
        if amount is None:
            amount = self.decay_rate
            
        # Decrease activation level, floored at 0.0
        self.activation_level = max(0.0, self.activation_level - amount)
        
        return self.activation_level

class MemoryAssociation(db.Model):
    """
    Represents associations between memory nodes with strength, type, and metadata.
    """
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('memory_node.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('memory_node.id'), nullable=False)
    association_type = db.Column(db.String(64), default='default')  # 'similarity', 'causality', 'temporal', etc.
    strength = db.Column(db.Float, default=0.5)  # 0.0 to 1.0, association strength
    bidirectional = db.Column(db.Boolean, default=True)  # If true, association works both ways
    
    # Additional properties
    association_metadata = db.Column(db.Text)  # JSON storage for additional properties
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = db.relationship("MemoryNode", foreign_keys=[source_id], backref="outgoing_associations")
    target = db.relationship("MemoryNode", foreign_keys=[target_id], backref="incoming_associations")
    
    def get_metadata(self):
        """Parse stored JSON metadata."""
        if self.association_metadata:
            return json.loads(self.association_metadata)
        return {}
    
    def set_metadata(self, metadata_dict):
        """Store metadata as JSON."""
        self.association_metadata = json.dumps(metadata_dict)
    
    def strengthen(self, amount=0.1):
        """
        Strengthen this association by the given amount.
        Returns the new strength.
        """
        # Increase strength, capped at 1.0
        self.strength = min(1.0, self.strength + amount)
        self.updated_at = datetime.utcnow()
        
        return self.strength
    
    def weaken(self, amount=0.1):
        """
        Weaken this association by the given amount.
        Returns the new strength.
        """
        # Decrease strength, floored at 0.0
        self.strength = max(0.0, self.strength - amount)
        self.updated_at = datetime.utcnow()
        
        return self.strength

class PatternTemplate(db.Model):
    """
    Represents pattern templates for memory association and pattern matching.
    These templates define how memories can be related and recognized in similar patterns.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    pattern_type = db.Column(db.String(64), nullable=False)  # 'spatial', 'temporal', 'causal', 'analogical', etc.
    
    # Pattern definition
    structure = db.Column(db.Text)  # JSON definition of pattern structure
    rules = db.Column(db.Text)  # JSON definition of matching rules
    activation_threshold = db.Column(db.Float, default=0.7)  # Threshold for pattern activation
    
    # Metadata
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    memory_nodes = db.relationship('MemoryNode', secondary=pattern_node_association,
                                 back_populates='pattern_templates')
    
    def get_structure(self):
        """Parse stored JSON structure."""
        if self.structure:
            return json.loads(self.structure)
        return {}
    
    def set_structure(self, structure_dict):
        """Store structure as JSON."""
        self.structure = json.dumps(structure_dict)
    
    def get_rules(self):
        """Parse stored JSON rules."""
        if self.rules:
            return json.loads(self.rules)
        return {}
    
    def set_rules(self, rules_dict):
        """Store rules as JSON."""
        self.rules = json.dumps(rules_dict)
    
    def matches(self, memory_nodes):
        """
        Check if the given memory nodes match this pattern template.
        Returns a match score between 0.0 and 1.0.
        """
        # This is a placeholder for pattern matching logic
        # In a real implementation, this would apply the rules to the memory nodes
        # and calculate a match score
        
        # For now, return a simple match if there are any nodes
        return 1.0 if memory_nodes else 0.0

class DreamState(db.Model):
    """
    Represents a dream state record with pattern associations and insights.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    
    # Dream content
    content = db.Column(db.Text)  # JSON storage for dream content
    source_memories = db.Column(db.Text)  # JSON list of memory node IDs that fed into this dream
    pattern_activations = db.Column(db.Text)  # JSON mapping of pattern IDs to activation levels
    
    # Results
    insights_generated = db.Column(db.Text)  # JSON list of insights generated during this dream
    new_associations = db.Column(db.Text)  # JSON list of new memory associations created
    
    # Metadata
    dream_type = db.Column(db.String(64))  # 'rem', 'consolidation', 'creative', etc.
    emotional_tone = db.Column(db.Float, default=0.0)  # -1.0 to 1.0, negative to positive
    coherence = db.Column(db.Float, default=0.5)  # 0.0 to 1.0, measure of dream coherence
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def get_content(self):
        """Parse stored JSON content."""
        if self.content:
            return json.loads(self.content)
        return {}
    
    def set_content(self, content_dict):
        """Store content as JSON."""
        self.content = json.dumps(content_dict)
    
    def get_source_memories(self):
        """Parse stored JSON source memories."""
        if self.source_memories:
            return json.loads(self.source_memories)
        return []
    
    def set_source_memories(self, memory_ids):
        """Store source memories as JSON."""
        self.source_memories = json.dumps(memory_ids)
    
    def get_pattern_activations(self):
        """Parse stored JSON pattern activations."""
        if self.pattern_activations:
            return json.loads(self.pattern_activations)
        return {}
    
    def set_pattern_activations(self, activations_dict):
        """Store pattern activations as JSON."""
        self.pattern_activations = json.dumps(activations_dict)
    
    def get_insights(self):
        """Parse stored JSON insights."""
        if self.insights_generated:
            return json.loads(self.insights_generated)
        return []
    
    def set_insights(self, insights_list):
        """Store insights as JSON."""
        self.insights_generated = json.dumps(insights_list)
    
    def get_new_associations(self):
        """Parse stored JSON new associations."""
        if self.new_associations:
            return json.loads(self.new_associations)
        return []
    
    def set_new_associations(self, associations_list):
        """Store new associations as JSON."""
        self.new_associations = json.dumps(associations_list)
    
    def finalize(self):
        """
        Finalize this dream state by setting the end time and duration.
        """
        self.end_time = datetime.utcnow()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = delta.total_seconds()
        return self.duration_seconds

# Add relationships to existing User model
User.memory_cycles = db.relationship('MemoryCycle', backref='user', lazy='dynamic')
User.pattern_templates = db.relationship('PatternTemplate', backref='user', lazy='dynamic')
User.dream_states = db.relationship('DreamState', backref='user', lazy='dynamic')