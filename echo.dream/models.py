"""
Database models for Deep Tree Echo

This module contains SQLAlchemy models for persisting application data.
"""
from database import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    """User model for authentication and personalization."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    projects = db.relationship('Project', backref='creator', lazy='dynamic')
    simulations = db.relationship('Simulation', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        """Set user password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches."""
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    """Project model for organizing simulations and code."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    namespace = db.Column(db.String(64), nullable=False, default='default')
    
    # Relationships
    simulations = db.relationship('Simulation', backref='project', lazy='dynamic')
    

class Simulation(db.Model):
    """Simulation model for storing recursion results."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    engine_type = db.Column(db.String(64), nullable=False, default='dte')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    config = db.Column(db.Text)  # JSON storage for configuration
    
    # Relationships
    snapshots = db.relationship('SimulationSnapshot', backref='simulation', lazy='dynamic')
    
    def get_config(self):
        """Parse stored JSON configuration."""
        if self.config:
            return json.loads(self.config)
        return {}
    
    def set_config(self, config_dict):
        """Store configuration as JSON."""
        self.config = json.dumps(config_dict)


class SimulationSnapshot(db.Model):
    """Model for capturing the state of a simulation at a point in time."""
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulation.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    state_data = db.Column(db.Text)  # JSON storage for state
    
    def get_state(self):
        """Parse stored JSON state."""
        if self.state_data:
            return json.loads(self.state_data)
        return {}
    
    def set_state(self, state_dict):
        """Store state as JSON."""
        self.state_data = json.dumps(state_dict)


class RecursivePattern(db.Model):
    """Model for storing reusable recursive pattern templates."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    pattern_type = db.Column(db.String(64), nullable=False)
    code = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_builtin = db.Column(db.Boolean, default=False)


class DiaryEntry(db.Model):
    """Model for storing DTE's self-reflective diary entries."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.Text)  # JSON storage for tags
    
    def get_tags(self):
        """Parse stored JSON tags."""
        if self.tags:
            return json.loads(self.tags)
        return []
    
    def set_tags(self, tags_list):
        """Store tags as JSON."""
        self.tags = json.dumps(tags_list)


class AARComponent(db.Model):
    """Model for storing Agent-Arena-Relation components."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    component_type = db.Column(db.String(64), nullable=False)  # 'agent', 'arena', 'relation'
    config = db.Column(db.Text)  # JSON storage for configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_config(self):
        """Parse stored JSON configuration."""
        if self.config:
            return json.loads(self.config)
        return {}
    
    def set_config(self, config_dict):
        """Store configuration as JSON."""
        self.config = json.dumps(config_dict)


class RecursiveDistinction(db.Model):
    """
    Model for storing recursive parentheses-based structures.
    Inspired by G. Spencer-Brown's Laws of Form and Lisp's symbolic structure.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    expression = db.Column(db.Text, nullable=False)  # The parentheses expression
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('recursive_distinction.id'), nullable=True)
    
    # Self-referential relationship for nested structures
    children = db.relationship(
        'RecursiveDistinction', 
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    
    # For storing evaluation metrics and properties
    metrics = db.Column(db.Text)  # JSON storage
    
    def get_metrics(self):
        """Parse stored JSON metrics."""
        if self.metrics:
            return json.loads(self.metrics)
        return {}
    
    def set_metrics(self, metrics_dict):
        """Store metrics as JSON."""
        self.metrics = json.dumps(metrics_dict)


class HyperGNN(db.Model):
    """
    Model for storing Hypergraph Neural Network structures that can
    be synced between database and memory representations.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    structure = db.Column(db.Text)  # JSON representation of graph
    weights = db.Column(db.Text)    # JSON representation of weights
    parameters = db.Column(db.Text)  # JSON for hyperparameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # For tracking training progress
    epochs_trained = db.Column(db.Integer, default=0)
    loss_history = db.Column(db.Text)  # JSON array of loss values
    
    def get_structure(self):
        """Parse stored JSON graph structure."""
        if self.structure:
            return json.loads(self.structure)
        return {}
    
    def set_structure(self, structure_dict):
        """Store structure as JSON."""
        self.structure = json.dumps(structure_dict)
        
    def get_weights(self):
        """Parse stored JSON weights."""
        if self.weights:
            return json.loads(self.weights)
        return {}
    
    def set_weights(self, weights_dict):
        """Store weights as JSON."""
        self.weights = json.dumps(weights_dict)
    
    def get_parameters(self):
        """Parse stored JSON parameters."""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def set_parameters(self, params_dict):
        """Store parameters as JSON."""
        self.parameters = json.dumps(params_dict)
        
    def get_loss_history(self):
        """Parse stored JSON loss history."""
        if self.loss_history:
            return json.loads(self.loss_history)
        return []
    
    def set_loss_history(self, loss_list):
        """Store loss history as JSON."""
        self.loss_history = json.dumps(loss_list)


class SelfReferentialNode(db.Model):
    """
    Model for storing self-referential computational nodes
    that can recursively build themselves with persistence.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    node_type = db.Column(db.String(64), nullable=False)  # 'function', 'data', 'combinator', etc.
    expression = db.Column(db.Text)  # The S-expression or code
    value = db.Column(db.Text)       # Current evaluated value (can be serialized Python data)
    parent_id = db.Column(db.Integer, db.ForeignKey('self_referential_node.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Self-referential relationship for recursive structure
    children = db.relationship(
        'SelfReferentialNode', 
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    
    # Many-to-many relationship with itself for arbitrary connections
    connections = db.relationship(
        'NodeConnection',
        primaryjoin="or_(SelfReferentialNode.id==NodeConnection.source_id, "
                    "SelfReferentialNode.id==NodeConnection.target_id)",
        lazy='dynamic',
        overlaps="incoming_connections,outgoing_connections"
    )
    
    def get_value(self):
        """Parse stored value, which could be JSON or other serialized format."""
        if self.value:
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return self.value  # Return as string if not valid JSON
        return None


class NodeConnection(db.Model):
    """Represents connections between self-referential nodes."""
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('self_referential_node.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('self_referential_node.id'), nullable=False)
    connection_type = db.Column(db.String(64), default='default')  # 'call', 'reference', etc.
    weight = db.Column(db.Float, default=1.0)
    conn_data = db.Column(db.Text)  # JSON for additional properties
    
    source = db.relationship("SelfReferentialNode", foreign_keys=[source_id], backref="outgoing_connections", overlaps="connections")
    target = db.relationship("SelfReferentialNode", foreign_keys=[target_id], backref="incoming_connections", overlaps="connections")
    
    def get_conn_data(self):
        """Parse stored JSON connection data."""
        if self.conn_data:
            return json.loads(self.conn_data)
        return {}


class SimulationThought(db.Model):
    """Model for storing thoughts from simulation engines for persistent memory."""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thought_type = db.Column(db.String(64), default='thought')  # 'thought', 'dream', 'insight', 'system'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    state = db.Column(db.String(128))  # Current state of the simulation
    recursion_level = db.Column(db.Integer, default=0)
    engine_type = db.Column(db.String(64), default='dte')  # Which simulation engine generated this thought
    session_id = db.Column(db.String(64))  # To group thoughts by session
    
    def to_dict(self):
        """Convert to dictionary for API responses and visualization."""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.thought_type,
            'timestamp': self.timestamp.isoformat(),
            'state': self.state,
            'recursion_level': self.recursion_level
        }