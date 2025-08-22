"""Arena manager for AAR core."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .arena_session import ArenaSession, ArenaState


class ArenaManager:
    """Manages arena sessions and lifecycle."""
    
    def __init__(self):
        self._arenas: Dict[str, ArenaSession] = {}
    
    def create_arena(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArenaSession:
        """Create a new arena session."""
        arena_id = str(uuid.uuid4())
        
        arena = ArenaSession(
            id=arena_id,
            name=name,
            description=description,
            metadata=metadata or {},
        )
        
        self._arenas[arena_id] = arena
        return arena
    
    def get_arena(self, arena_id: str) -> Optional[ArenaSession]:
        """Get an arena session by ID."""
        return self._arenas.get(arena_id)
    
    def list_arenas(self, state: Optional[ArenaState] = None) -> List[ArenaSession]:
        """List all arenas, optionally filtered by state."""
        if state is None:
            return list(self._arenas.values())
        
        return [arena for arena in self._arenas.values() if arena.state == state]
    
    def close_arena(self, arena_id: str) -> bool:
        """Close an arena session."""
        arena = self._arenas.get(arena_id)
        if not arena:
            return False
        
        arena.transition_state(ArenaState.CLOSING)
        arena.transition_state(ArenaState.CLOSED)
        return True
    
    def add_agent_to_arena(self, arena_id: str, agent_id: str) -> bool:
        """Add an agent to an arena."""
        arena = self._arenas.get(arena_id)
        if not arena:
            return False
        
        arena.add_agent(agent_id)
        return True
    
    def remove_agent_from_arena(self, arena_id: str, agent_id: str) -> bool:
        """Remove an agent from an arena."""
        arena = self._arenas.get(arena_id)
        if not arena:
            return False
        
        arena.remove_agent(agent_id)
        return True
    
    def activate_arena(self, arena_id: str) -> bool:
        """Activate an arena session."""
        arena = self._arenas.get(arena_id)
        if not arena:
            return False
        
        arena.transition_state(ArenaState.ACTIVE)
        return True
    
    def pause_arena(self, arena_id: str) -> bool:
        """Pause an arena session."""
        arena = self._arenas.get(arena_id)
        if not arena:
            return False
        
        arena.transition_state(ArenaState.PAUSED)
        return True
    
    def get_arena_stats(self) -> Dict[str, Any]:
        """Get statistics about all arenas."""
        total_arenas = len(self._arenas)
        state_counts = {}
        
        for arena in self._arenas.values():
            state = arena.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_arenas": total_arenas,
            "state_counts": state_counts,
        }