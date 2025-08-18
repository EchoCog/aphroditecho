"""
Echo9ml Integration Module

Integrates the Echo9ml persona evolution system with the existing 
cognitive_architecture.py framework, providing seamless interoperability
and enhanced cognitive capabilities.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from echo9ml import Echo9mlSystem, PersonaTraitType
from cognitive_architecture import CognitiveArchitecture, PersonalityTrait, Memory, MemoryType

logger = logging.getLogger(__name__)

class EnhancedCognitiveArchitecture(CognitiveArchitecture):
    """
    Enhanced cognitive architecture with Echo9ml persona evolution integration
    
    This class extends the existing CognitiveArchitecture with:
    - Deep Tree Echo persona evolution
    - Tensor-based persona encoding
    - Hypergraph memory integration
    - Adaptive attention allocation
    - Meta-cognitive enhancement
    """
    
    def __init__(self, enable_echo9ml: bool = True, echo9ml_save_path: Optional[str] = None):
        super().__init__()
        
        self.echo9ml_enabled = enable_echo9ml
        self.echo9ml_system = None
        
        if enable_echo9ml:
            try:
                self.echo9ml_system = Echo9mlSystem(save_path=echo9ml_save_path)
                self._sync_personality_traits()
                logger.info("Echo9ml persona evolution system integrated successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Echo9ml system: {e}")
                self.echo9ml_enabled = False
    
    def _sync_personality_traits(self):
        """Synchronize existing personality traits with Echo9ml persona traits"""
        if not self.echo9ml_system:
            return
        
        # Map existing traits to Echo9ml traits
        trait_mapping = {
            "curiosity": PersonaTraitType.GROWTH,
            "adaptability": PersonaTraitType.GROWTH,
            "persistence": PersonaTraitType.TRUNK,
            "creativity": PersonaTraitType.CANOPY,
            "analytical": PersonaTraitType.BRANCHES,
            "social": PersonaTraitType.NETWORK
        }
        
        # Update Echo9ml traits based on existing personality
        for trait_name, echo_trait in trait_mapping.items():
            if trait_name in self.personality_traits:
                current_value = self.personality_traits[trait_name].current_value
                # Blend with existing Echo9ml trait value
                existing_value = self.echo9ml_system.persona_kernel.traits[echo_trait]
                blended_value = 0.7 * existing_value + 0.3 * current_value
                self.echo9ml_system.persona_kernel.traits[echo_trait] = blended_value
        
        logger.info("Personality traits synchronized with Echo9ml persona")
    
    def enhanced_memory_storage(self, content: str, memory_type: MemoryType, 
                              context: Dict[str, Any] = None, 
                              emotional_valence: float = 0.0,
                              importance: float = 0.5) -> str:
        """
        Enhanced memory storage with Echo9ml hypergraph integration
        """
        # Create memory object
        memory = Memory(
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            emotional_valence=emotional_valence,
            importance=importance,
            context=context or {}
        )
        
        # Store in traditional cognitive architecture
        self.enhanced_memory_management(memory)
        memory_id = str(len(self.memories) - 1)  # Simple ID based on position
        
        # Also store in Echo9ml hypergraph if enabled
        if self.echo9ml_enabled and self.echo9ml_system:
            try:
                # Add memory to hypergraph
                associations = set()
                if context:
                    associations = set(str(v) for v in context.values() if isinstance(v, str))
                
                self.echo9ml_system.hypergraph_encoder.add_memory_node(
                    content, memory_type.value, associations
                )
                
                # Process as experience for persona evolution
                experience = {
                    "type": "memory_formation",
                    "content": content,
                    "memory_type": memory_type.value,
                    "success": min(1.0, importance + 0.3),  # Higher importance = higher success
                    "importance": importance,
                    "valence": emotional_valence,
                    "context": "memory"
                }
                
                self.echo9ml_system.process_experience(experience)
                
            except Exception as e:
                logger.error(f"Failed to integrate memory with Echo9ml: {e}")
        
        return memory_id
    
    def enhanced_personality_update(self, trait_name: str, value: float, 
                                  context: Dict[str, Any]):
        """Enhanced personality trait update with Echo9ml evolution"""
        # Update traditional personality trait
        super().enhanced_personality_management(
            self.personality_traits.get(trait_name), value, context
        )
        
        # Update Echo9ml persona if enabled
        if self.echo9ml_enabled and self.echo9ml_system:
            try:
                # Map trait to Echo9ml trait
                trait_mapping = {
                    "curiosity": PersonaTraitType.GROWTH,
                    "adaptability": PersonaTraitType.GROWTH,
                    "persistence": PersonaTraitType.TRUNK,
                    "creativity": PersonaTraitType.CANOPY,
                    "analytical": PersonaTraitType.BRANCHES,
                    "social": PersonaTraitType.NETWORK
                }
                
                if trait_name in trait_mapping:
                    echo_trait = trait_mapping[trait_name]
                    
                    # Create experience for trait update
                    experience = {
                        "type": "trait_update",
                        "content": f"Personality trait {trait_name} updated",
                        "success": max(0.0, min(1.0, value)),  # Normalize to [0,1]
                        "importance": 0.6,
                        "context": "personality",
                        "traits_used": [echo_trait]
                    }
                    
                    self.echo9ml_system.process_experience(experience)
                    
            except Exception as e:
                logger.error(f"Failed to update Echo9ml persona trait: {e}")
    
    def enhanced_goal_processing(self, goal_description: str, priority: float,
                               deadline: Optional[float] = None) -> str:
        """Enhanced goal processing with Echo9ml integration"""
        # Create goal object
        goal = self.generate_goal(goal_description, priority, deadline)
        
        # Store in traditional architecture
        self.enhanced_goal_management(goal)
        goal_id = str(len(self.goals) - 1)  # Simple ID based on position
        
        # Process as experience in Echo9ml
        if self.echo9ml_enabled and self.echo9ml_system:
            try:
                experience = {
                    "type": "goal_setting",
                    "content": goal_description,
                    "success": min(1.0, priority),  # Higher priority = higher success expectation
                    "importance": priority,
                    "context": "planning",
                    "traits_used": [PersonaTraitType.BRANCHES, PersonaTraitType.GROWTH]
                }
                
                self.echo9ml_system.process_experience(experience)
                
            except Exception as e:
                logger.error(f"Failed to integrate goal with Echo9ml: {e}")
        
        return goal_id
    
    def get_enhanced_cognitive_state(self) -> Dict[str, Any]:
        """Get comprehensive cognitive state including Echo9ml persona data"""
        # Get traditional cognitive state
        traditional_state = {
            "memory_count": len(self.memories),
            "goal_count": len(self.goals),
            "active_goal_count": len(self.active_goals),
            "personality_traits": {
                name: {
                    "current_value": trait.current_value,
                    "base_value": trait.base_value,
                    "history_length": len(trait.history)
                }
                for name, trait in self.personality_traits.items()
            }
        }
        
        # Add Echo9ml state if enabled
        enhanced_state = traditional_state.copy()
        
        if self.echo9ml_enabled and self.echo9ml_system:
            try:
                echo9ml_snapshot = self.echo9ml_system.get_cognitive_snapshot()
                enhanced_state["echo9ml"] = echo9ml_snapshot
                enhanced_state["integration_active"] = True
            except Exception as e:
                logger.error(f"Failed to get Echo9ml cognitive state: {e}")
                enhanced_state["integration_active"] = False
        else:
            enhanced_state["integration_active"] = False
        
        return enhanced_state
    
    def enhanced_introspection(self) -> Optional[str]:
        """Enhanced recursive introspection with Echo9ml persona awareness"""
        # Get traditional introspection
        traditional_prompt = super().perform_recursive_introspection()
        
        if not self.echo9ml_enabled or not self.echo9ml_system:
            return traditional_prompt
        
        try:
            # Get Echo9ml cognitive snapshot
            echo_snapshot = self.echo9ml_system.get_cognitive_snapshot()
            
            # Create enhanced introspection prompt
            enhanced_prompt = f"""
# Enhanced Cognitive Introspection with Deep Tree Echo Persona

## Traditional Cognitive State
{traditional_prompt or "Traditional introspection not available"}

## Deep Tree Echo Persona Evolution State

### Current Persona Traits
{chr(10).join(f"- {trait}: {value:.3f}" for trait, value in echo_snapshot['persona_kernel']['traits'].items())}

### Cognitive Architecture Stats
- Tensor shape: {echo_snapshot['tensor_encoding']['shape']}
- Hypergraph nodes: {echo_snapshot['hypergraph']['node_count']}
- Hypergraph edges: {echo_snapshot['hypergraph']['edge_count']}
- Active attention nodes: {len(echo_snapshot['hypergraph']['active_nodes'])}

### Recent Evolution
- Total interactions: {echo_snapshot['system_stats']['interaction_count']}
- Evolution events: {echo_snapshot['system_stats']['total_evolution_events']}
- System uptime: {echo_snapshot['system_stats']['system_uptime']:.1f} seconds

### Attention Allocation (Top 3)
{chr(10).join(f"- {item}: {attention:.2f}" for item, attention in echo_snapshot['attention']['top_focus'][:3])}

### Meta-Cognitive Insights
- Confidence trend: {len(echo_snapshot['meta_cognitive']['confidence_history'])} data points
- Recent suggestions: {len(echo_snapshot['meta_cognitive']['recent_suggestions'])}

### Current Suggestions
{chr(10).join(f"- {s['type']}: {s['description']}" for s in echo_snapshot['meta_cognitive']['recent_suggestions'][-3:]) if echo_snapshot['meta_cognitive']['recent_suggestions'] else "No recent suggestions"}

## Integration Status
The Deep Tree Echo persona is actively evolving and adapting based on experiences.
Tensor-based encoding captures multi-dimensional trait evolution.
Hypergraph structure maintains semantic connections between memories and traits.
Meta-cognitive layer provides self-monitoring and adaptation suggestions.
"""
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced introspection: {e}")
            return traditional_prompt
    
    def save_enhanced_state(self):
        """Save both traditional and Echo9ml states"""
        # Save traditional state (create simple save method)
        try:
            memory_data = {
                'memories': [
                    {**self._memory_to_dict(mem), 'id': mem_id} 
                    for mem_id, mem in self.memories.items()
                ],
                'goals': [self._goal_to_dict(goal) for goal in self.goals]
            }
            
            memory_file = self.memory_path / 'memories.json'
            with open(memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2, default=str)
            
            # Save activities
            self._save_activities()
            
        except Exception as e:
            logger.error(f"Failed to save traditional state: {e}")
        
        # Save Echo9ml state if enabled
        if self.echo9ml_enabled and self.echo9ml_system:
            try:
                self.echo9ml_system.save_state()
                logger.info("Enhanced cognitive state saved successfully")
            except Exception as e:
                logger.error(f"Failed to save Echo9ml state: {e}")
    
    def load_enhanced_state(self):
        """Load both traditional and Echo9ml states"""
        # Load traditional state
        self._load_state()
        
        # Load Echo9ml state if enabled
        if self.echo9ml_enabled and self.echo9ml_system:
            try:
                if self.echo9ml_system.load_state():
                    logger.info("Enhanced cognitive state loaded successfully")
                    self._sync_personality_traits()  # Re-sync after loading
            except Exception as e:
                logger.error(f"Failed to load Echo9ml state: {e}")

def create_enhanced_cognitive_architecture(enable_echo9ml: bool = True,
                                         echo9ml_save_path: Optional[str] = None) -> EnhancedCognitiveArchitecture:
    """
    Factory function to create enhanced cognitive architecture
    
    Args:
        enable_echo9ml: Whether to enable Echo9ml persona evolution
        echo9ml_save_path: Optional custom save path for Echo9ml data
    
    Returns:
        Enhanced cognitive architecture with Echo9ml integration
    """
    return EnhancedCognitiveArchitecture(enable_echo9ml, echo9ml_save_path)

# Export main classes
__all__ = ['EnhancedCognitiveArchitecture', 'create_enhanced_cognitive_architecture']