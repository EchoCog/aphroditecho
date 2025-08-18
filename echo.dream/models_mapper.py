"""
Database models for the Dynamic Interdisciplinary Connection Mapper.

These models represent knowledge domains, concepts, connections, and discovered patterns
in a database-persistent format.
"""

import json
import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from database import db

class KnowledgeDomain(db.Model):
    """Database model for knowledge domains."""
    __tablename__ = 'knowledge_domains'

    id = sa.Column(sa.String(36), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    domain_type = sa.Column(sa.String(100), default='general')
    parent_domain_id = sa.Column(sa.String(36), sa.ForeignKey('knowledge_domains.id'), nullable=True)
    attributes = sa.Column(sa.JSON, default={})
    terminology = sa.Column(sa.JSON, default=[])
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relationships
    parent_domain = relationship("KnowledgeDomain", remote_side=[id], backref="subdomains")
    concepts = relationship("ConceptNode", secondary="domain_concept_associations", back_populates="domains")
    outgoing_connections = relationship("DomainConnection", 
                                       foreign_keys="DomainConnection.source_domain_id",
                                       backref="source_domain",
                                       cascade="all, delete-orphan")
    incoming_connections = relationship("DomainConnection", 
                                       foreign_keys="DomainConnection.target_domain_id",
                                       backref="target_domain",
                                       cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "domain_type": self.domain_type,
            "parent_domain_id": self.parent_domain_id,
            "attributes": self.attributes or {},
            "terminology": self.terminology or [],
            "concept_count": len(self.concepts),
            "connection_count": len(self.outgoing_connections),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# Association table for many-to-many relationship between domains and concepts
domain_concept_association = db.Table(
    'domain_concept_associations',
    sa.Column('domain_id', sa.String(36), sa.ForeignKey('knowledge_domains.id'), primary_key=True),
    sa.Column('concept_id', sa.String(36), sa.ForeignKey('concept_nodes.id'), primary_key=True)
)

class ConceptNode(db.Model):
    """Database model for concept nodes."""
    __tablename__ = 'concept_nodes'

    id = sa.Column(sa.String(36), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    node_type = sa.Column(sa.String(100), default='concept')
    attributes = sa.Column(sa.JSON, default={})
    vector_data = sa.Column(sa.Text, nullable=True)  # JSON-serialized vector
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relationships
    domains = relationship("KnowledgeDomain", secondary="domain_concept_associations", back_populates="concepts")
    outgoing_connections = relationship("ConceptConnection", 
                                      foreign_keys="ConceptConnection.source_concept_id",
                                      backref="source_concept",
                                      cascade="all, delete-orphan")
    incoming_connections = relationship("ConceptConnection", 
                                      foreign_keys="ConceptConnection.target_concept_id",
                                      backref="target_concept",
                                      cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "node_type": self.node_type,
            "attributes": self.attributes or {},
            "has_vector": self.vector_data is not None,
            "domain_ids": [domain.id for domain in self.domains],
            "connection_count": len(self.outgoing_connections),
            "created_at": self.created_at.isoformat() if self.created_at else None, 
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_vector(self):
        """Get the vector representation if available."""
        if self.vector_data:
            try:
                return json.loads(self.vector_data)
            except json.JSONDecodeError:
                return None
        return None

class DomainConnection(db.Model):
    """Database model for connections between domains."""
    __tablename__ = 'domain_connections'

    id = sa.Column(sa.String(36), primary_key=True)
    source_domain_id = sa.Column(sa.String(36), sa.ForeignKey('knowledge_domains.id'), nullable=False)
    target_domain_id = sa.Column(sa.String(36), sa.ForeignKey('knowledge_domains.id'), nullable=False)
    connection_type = sa.Column(sa.String(100), default='related')
    strength = sa.Column(sa.Float, default=0.5)
    description = sa.Column(sa.Text, nullable=True)
    bidirectional = sa.Column(sa.Boolean, default=True)
    attributes = sa.Column(sa.JSON, default={})
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "source_domain_id": self.source_domain_id,
            "target_domain_id": self.target_domain_id,
            "connection_type": self.connection_type,
            "strength": self.strength,
            "description": self.description or "",
            "bidirectional": self.bidirectional,
            "attributes": self.attributes or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ConceptConnection(db.Model):
    """Database model for connections between concepts."""
    __tablename__ = 'concept_connections'

    id = sa.Column(sa.String(36), primary_key=True)
    source_concept_id = sa.Column(sa.String(36), sa.ForeignKey('concept_nodes.id'), nullable=False)
    target_concept_id = sa.Column(sa.String(36), sa.ForeignKey('concept_nodes.id'), nullable=False)
    relation_type = sa.Column(sa.String(100), default='related')
    strength = sa.Column(sa.Float, default=0.5)
    description = sa.Column(sa.Text, nullable=True)
    bidirectional = sa.Column(sa.Boolean, default=True)
    attributes = sa.Column(sa.JSON, default={})
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "description": self.description or "",
            "bidirectional": self.bidirectional,
            "attributes": self.attributes or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source_concept_name": self.source_concept.name if self.source_concept else None,
            "target_concept_name": self.target_concept.name if self.target_concept else None
        }

class ConnectionPattern(db.Model):
    """
    Database model for connection patterns discovered in the knowledge graph.
    These patterns represent interesting structures like central hubs, bridges between 
    domains, interdisciplinary concepts, etc.
    """
    __tablename__ = 'connection_patterns'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    pattern_type = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    score = sa.Column(sa.Float, default=1.0)
    entities = sa.Column(sa.JSON, default=[])  # List of domain/concept IDs involved
    pattern_metadata = sa.Column(sa.JSON, default={})  # Additional pattern metadata (renamed from 'metadata' which is reserved)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "description": self.description or "",
            "score": self.score,
            "entities": self.entities or [],
            "metadata": self.pattern_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }