
"""
Agent-Arena-Relation (AAR) Triad Simulator
Implements a self-referential framework for recursive intelligence exploration.
"""
import numpy as np
from abc import ABC, abstractmethod

class AARComponent(ABC):
    """Base class for all AAR triad components."""
    
    def __init__(self, name):
        self.name = name
        self.state = {}
        self.relations = []
    
    @abstractmethod
    def process(self, input_data):
        """Process input and update state."""
        pass
    
    def add_relation(self, relation):
        """Add a relation to this component."""
        self.relations.append(relation)
    
    def get_state(self):
        """Return the current state."""
        return self.state

class Agent(AARComponent):
    """Represents an active entity in the AAR triad."""
    
    def __init__(self, name, capabilities=None):
        super().__init__(name)
        self.capabilities = capabilities or []
        self.state = {
            'active': True,
            'energy': 100,
            'perception': {},
            'memory': []
        }
    
    def process(self, input_data):
        """Process perceptual input and generate action."""
        # Update perception
        self.state['perception'] = input_data
        
        # Generate action based on capabilities
        action = None
        for capability in self.capabilities:
            if np.random.random() < 0.3:  # 30% chance to use this capability
                action = {
                    'type': capability,
                    'intensity': np.random.uniform(0.1, 1.0),
                    'target': input_data.get('targets', [None])[0]
                }
                break
        
        # Update energy
        self.state['energy'] -= 5
        if self.state['energy'] <= 0:
            self.state['active'] = False
        
        # Store memory
        if len(self.state['memory']) >= 10:
            self.state['memory'].pop(0)
        self.state['memory'].append({
            'perception': input_data,
            'action': action
        })
        
        return action

class Arena(AARComponent):
    """Represents the environment in the AAR triad."""
    
    def __init__(self, name, size=(10, 10)):
        super().__init__(name)
        self.size = size
        self.state = {
            'grid': np.zeros(size),
            'entities': {},
            'resources': {},
            'rules': []
        }
    
    def process(self, input_data):
        """Update arena state based on agent actions."""
        actions = input_data.get('actions', [])
        
        # Process each action
        for action in actions:
            if not action:
                continue
                
            # Apply action effects to the arena
            action_type = action.get('type')
            target = action.get('target')
            intensity = action.get('intensity', 0.5)
            
            if action_type == 'modify' and target:
                x, y = target
                if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
                    self.state['grid'][x, y] += intensity
            
            elif action_type == 'create' and target:
                entity_id = f"entity_{len(self.state['entities']) + 1}"
                self.state['entities'][entity_id] = {
                    'position': target,
                    'strength': intensity * 10
                }
                
            elif action_type == 'destroy' and target:
                entities_to_remove = []
                for entity_id, entity in self.state['entities'].items():
                    if entity['position'] == target:
                        entities_to_remove.append(entity_id)
                
                for entity_id in entities_to_remove:
                    del self.state['entities'][entity_id]
        
        # Natural processes in the arena
        # Resources regeneration
        if np.random.random() < 0.2:  # 20% chance
            x = np.random.randint(0, self.size[0])
            y = np.random.randint(0, self.size[1])
            resource_id = f"resource_{len(self.state['resources']) + 1}"
            self.state['resources'][resource_id] = {
                'position': (x, y),
                'value': np.random.uniform(1, 10)
            }
        
        # Return the updated environment state
        return self.state

class Relation(AARComponent):
    """Represents the connections between agents and arenas."""
    
    def __init__(self, name, source, target, relation_type='bidirectional'):
        super().__init__(name)
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.state = {
            'active': True,
            'strength': 1.0,
            'type': relation_type,
            'history': []
        }
        
        # Register this relation with the connected components
        source.add_relation(self)
        target.add_relation(self)
    
    def process(self, input_data):
        """Process information flow between connected components."""
        source_state = self.source.get_state()
        target_state = self.target.get_state()
        
        # Calculate relation strength based on interaction history
        if len(self.state['history']) > 0:
            # Diminish strength slightly over time (decay)
            self.state['strength'] *= 0.99
        
        # Record interaction
        interaction = {
            'timestamp': input_data.get('timestamp', 0),
            'source_action': input_data.get('source_action'),
            'target_response': input_data.get('target_response')
        }
        
        # Keep history to a manageable size
        if len(self.state['history']) >= 20:
            self.state['history'].pop(0)
        self.state['history'].append(interaction)
        
        # If strength falls below threshold, deactivate relation
        if self.state['strength'] < 0.1:
            self.state['active'] = False
        
        return self.state

class AARTriad:
    """Manages a complete Agent-Arena-Relation triad system."""
    
    def __init__(self):
        self.agents = {}
        self.arenas = {}
        self.relations = {}
        self.timestamp = 0
    
    def create_agent(self, name, capabilities=None):
        """Create a new agent in the system."""
        agent = Agent(name, capabilities)
        self.agents[name] = agent
        return agent
    
    def create_arena(self, name, size=(10, 10)):
        """Create a new arena in the system."""
        arena = Arena(name, size)
        self.arenas[name] = arena
        return arena
    
    def create_relation(self, name, source_name, target_name, relation_type='bidirectional'):
        """Create a relation between components."""
        source = self.agents.get(source_name) or self.arenas.get(source_name)
        target = self.agents.get(target_name) or self.arenas.get(target_name)
        
        if not source or not target:
            raise ValueError("Source or target component not found")
        
        relation = Relation(name, source, target, relation_type)
        self.relations[name] = relation
        return relation
    
    def step(self):
        """Advance the system by one time step."""
        self.timestamp += 1
        
        # Process all agents
        agent_actions = {}
        for name, agent in self.agents.items():
            if agent.state.get('active', False):
                # Gather perceptual input for this agent
                perceptual_input = self._gather_agent_input(agent)
                
                # Process input and get action
                action = agent.process(perceptual_input)
                agent_actions[name] = action
        
        # Process all arenas
        arena_states = {}
        for name, arena in self.arenas.items():
            # Gather all agent actions that affect this arena
            arena_input = {
                'actions': [action for agent_name, action in agent_actions.items()]
            }
            
            # Process actions and update arena state
            state = arena.process(arena_input)
            arena_states[name] = state
        
        # Process all relations
        for name, relation in self.relations.items():
            if relation.state.get('active', False):
                # Get source action and target response
                source_name = relation.source.name
                target_name = relation.target.name
                
                relation_input = {
                    'timestamp': self.timestamp,
                    'source_action': agent_actions.get(source_name),
                    'target_response': arena_states.get(target_name)
                }
                
                # Process relation
                relation.process(relation_input)
        
        return {
            'timestamp': self.timestamp,
            'agents': {name: agent.get_state() for name, agent in self.agents.items()},
            'arenas': {name: arena.get_state() for name, arena in self.arenas.items()},
            'relations': {name: relation.get_state() for name, relation in self.relations.items()}
        }
    
    def _gather_agent_input(self, agent):
        """Gather perceptual input for an agent from connected arenas."""
        perceptual_input = {
            'timestamp': self.timestamp,
            'environments': {},
            'targets': []
        }
        
        # Find all arenas connected to this agent through relations
        for relation in agent.relations:
            if isinstance(relation.target, Arena) and relation.state.get('active', False):
                arena = relation.target
                perceptual_input['environments'][arena.name] = arena.get_state()
                
                # Add potential targets (entities in the arena)
                for entity_id, entity in arena.state.get('entities', {}).items():
                    perceptual_input['targets'].append(entity.get('position'))
                
                # Add resource targets
                for resource_id, resource in arena.state.get('resources', {}).items():
                    perceptual_input['targets'].append(resource.get('position'))
        
        return perceptual_input
    
    def get_system_state(self):
        """Return the complete state of the AAR system."""
        return {
            'timestamp': self.timestamp,
            'agents': {name: agent.get_state() for name, agent in self.agents.items()},
            'arenas': {name: arena.get_state() for name, arena in self.arenas.items()},
            'relations': {name: relation.get_state() for name, relation in self.relations.items()}
        }

# Example usage
if __name__ == "__main__":
    aar = AARTriad()
    
    # Create components
    aar.create_agent("Explorer", ["move", "observe", "modify"])
    aar.create_agent("Creator", ["create", "destroy", "modify"])
    aar.create_arena("PhysicalSpace", (20, 20))
    aar.create_arena("ConceptualSpace", (10, 10))
    
    # Create relations
    aar.create_relation("ExplorerInPhysical", "Explorer", "PhysicalSpace")
    aar.create_relation("CreatorInConceptual", "Creator", "ConceptualSpace")
    aar.create_relation("PhysicalToConceptual", "PhysicalSpace", "ConceptualSpace")
    
    # Run simulation
    states = []
    for _ in range(10):
        state = aar.step()
        states.append(state)
    
    print(f"Simulation completed with {len(states)} states")
