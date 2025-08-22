"""Memory types and data structures for AAR core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Types of memory in the AAR system."""
    WORKING = "working"      # Short-term, fast access
    EPISODIC = "episodic"    # Session events
    SEMANTIC = "semantic"    # Long-term knowledge
    PROCEDURAL = "procedural"  # Tool outputs and logs
    PROPRIOCEPTIVE = "proprioceptive"  # System metrics


@dataclass
class MemoryRecord:
    """A single memory record."""
    id: str
    type: MemoryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[timedelta] = None
    tags: List[str] = field(default_factory=list)
    source_agent: Optional[str] = None
    arena_id: Optional[str] = None
    vector_embedding: Optional[List[float]] = None
    
    def is_expired(self) -> bool:
        """Check if the memory record has expired."""
        if self.ttl is None:
            return False
        return datetime.utcnow() > self.created_at + self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "ttl": self.ttl.total_seconds() if self.ttl else None,
            "tags": self.tags,
            "source_agent": self.source_agent,
            "arena_id": self.arena_id,
            "vector_embedding": self.vector_embedding,
        }