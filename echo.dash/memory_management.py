"""
Memory Management System - Compatibility Layer

This file now serves as a compatibility layer that re-exports all memory classes
from the consolidated unified_echo_memory.py module. This maintains backward
compatibility for existing code while consolidating the implementation.

Original functionality has been moved to unified_echo_memory.py as part of the
memory system consolidation addressing the "Fragmented Memory System" issue.
"""

# Re-export all memory classes from the unified implementation
from unified_echo_memory import (
    MemoryType,
    MemoryNode, 
    MemoryEdge,
    HypergraphMemory
)

# Create a default memory instance for backward compatibility
memory_system = HypergraphMemory(storage_dir="echo_memory")

# Export all necessary symbols
__all__ = [
    'MemoryType',
    'MemoryNode', 
    'MemoryEdge',
    'HypergraphMemory',
    'memory_system'
]