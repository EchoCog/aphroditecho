"""
AAR Agent Management Module

Provides agent lifecycle management and coordination capabilities.
"""

from .agent_manager import AgentManager, Agent, AgentCapabilities, AgentStatus

__all__ = [
    'AgentManager',
    'Agent', 
    'AgentCapabilities',
    'AgentStatus'
]