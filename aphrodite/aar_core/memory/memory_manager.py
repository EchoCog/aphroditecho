"""Memory manager for AAR core."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .memory_types import MemoryRecord, MemoryType


class MemoryManager:
    """Manages memory operations and storage."""
    
    def __init__(self):
        self._memories: Dict[str, MemoryRecord] = {}
        self._working_buffer: List[MemoryRecord] = []
        self._max_working_size = 1000  # Configurable
    
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[timedelta] = None,
        tags: Optional[List[str]] = None,
        source_agent: Optional[str] = None,
        arena_id: Optional[str] = None,
        vector_embedding: Optional[List[float]] = None,
    ) -> str:
        """Add a new memory record."""
        memory_id = str(uuid.uuid4())
        
        record = MemoryRecord(
            id=memory_id,
            type=memory_type,
            content=content,
            metadata=metadata or {},
            ttl=ttl,
            tags=tags or [],
            source_agent=source_agent,
            arena_id=arena_id,
            vector_embedding=vector_embedding,
        )
        
        self._memories[memory_id] = record
        
        # Add to working buffer if it's working memory
        if memory_type == MemoryType.WORKING:
            self._working_buffer.append(record)
            # Maintain working buffer size
            if len(self._working_buffer) > self._max_working_size:
                self._working_buffer.pop(0)
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve a memory record by ID."""
        record = self._memories.get(memory_id)
        if record and record.is_expired():
            del self._memories[memory_id]
            return None
        return record
    
    def query_memory(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        arena_id: Optional[str] = None,
        limit: int = 10,
        include_expired: bool = False,
    ) -> List[MemoryRecord]:
        """Query memory records based on various criteria."""
        results = []
        
        for record in self._memories.values():
            # Skip expired records unless explicitly requested
            if not include_expired and record.is_expired():
                continue
            
            # Filter by memory type
            if memory_types and record.type not in memory_types:
                continue
            
            # Filter by tags
            if tags and not any(tag in record.tags for tag in tags):
                continue
            
            # Filter by arena
            if arena_id and record.arena_id != arena_id:
                continue
            
            # Simple text search (future: implement vector similarity)
            if query.lower() in record.content.lower():
                results.append(record)
            
            if len(results) >= limit:
                break
        
        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results
    
    def get_working_memory(self, limit: int = 100) -> List[MemoryRecord]:
        """Get recent working memory records."""
        return self._working_buffer[-limit:]
    
    def cleanup_expired(self) -> int:
        """Remove expired memory records and return count of removed records."""
        expired_ids = [
            memory_id for memory_id, record in self._memories.items()
            if record.is_expired()
        ]
        
        for memory_id in expired_ids:
            del self._memories[memory_id]
        
        return len(expired_ids)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        total_count = len(self._memories)
        type_counts = {}
        
        for record in self._memories.values():
            type_name = record.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_memories": total_count,
            "type_counts": type_counts,
            "working_buffer_size": len(self._working_buffer),
            "max_working_size": self._max_working_size,
        }