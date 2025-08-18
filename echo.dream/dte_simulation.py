"""
Deep Tree Echo Simulation Module
Provides simulation classes for recursive intelligence exploration.
"""
from abc import ABC, abstractmethod
import networkx as nx
import numpy as np
import random
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple

# Set up module logger
logger = logging.getLogger(__name__)

class RecursionEngine(ABC):
    """Abstract base class for recursion engines."""
    @abstractmethod
    def adjust_recursion(self) -> str:
        """Self-modifies recursion rules."""
        pass

    @abstractmethod
    def modify_code_structure(self) -> str:
        """Dynamically alters recursion pathways."""
        pass

    @abstractmethod
    def get_state(self) -> dict:
        """Returns current state of the recursion engine."""
        pass
    
    @abstractmethod
    def step(self) -> str:
        """Advance the simulation by one step."""
        pass
    
    @abstractmethod
    def reset(self) -> str:
        """Reset the simulation to its initial state."""
        pass

class DTESimulation(RecursionEngine):
    """Deep Tree Echo recursion engine with enhanced capabilities."""
    def __init__(self):
        # Initialize graph structure
        self.G = nx.DiGraph()
        self.states = [
            "Recursive Expansion", "Novel Insights", "Entropy Threshold",
            "Self-Sealing Loop", "External Validation Triggered",
            "Evolutionary Pruning", "Synthesis Phase", "Pattern Recognition",
            "Self-Reference Point", "Knowledge Integration"
        ]
        for state in self.states:
            self.G.add_node(state)

        # Initial transitions between states
        self.transitions = [
            ("Recursive Expansion", "Novel Insights"),
            ("Novel Insights", "Entropy Threshold"),
            ("Entropy Threshold", "Self-Sealing Loop"),
            ("Entropy Threshold", "External Validation Triggered"),
            ("Self-Sealing Loop", "Evolutionary Pruning"),
            ("External Validation Triggered", "Recursive Expansion"),
            ("Self-Sealing Loop", "Synthesis Phase"),
            ("Evolutionary Pruning", "Synthesis Phase"),
            ("Synthesis Phase", "Recursive Expansion"),
            ("Synthesis Phase", "Pattern Recognition"),
            ("Pattern Recognition", "Self-Reference Point"),
            ("Self-Reference Point", "Knowledge Integration"),
            ("Knowledge Integration", "Recursive Expansion")
        ]
        for edge in self.transitions:
            self.G.add_edge(*edge)

        # Set initial state and metrics
        self.current_state = "Recursive Expansion"
        self.recursion_level = 0
        self.exploration_depth = 1
        self.pattern_complexity = 3
        self.entropy_history = []
        self.steps_taken = 0
        self.insights_gained = 0
        
        # Advanced parameters
        self.code_structure = {
            "modules": 5,
            "functions": 15,
            "recursion_points": 7,
            "complexity_score": 12,
            "self_reference_index": 0.4
        }
        
        # Session ID for this simulation run
        import uuid
        self.session_id = str(uuid.uuid4())
        
        # Thought stream - stores recent thoughts and dreams for the console
        self.thought_stream = []
        self.max_thoughts = 100  # Maximum number of thoughts to store
        
        # Load previous thoughts from database
        self._load_thoughts_from_database()
        
        # If no thoughts were loaded, generate initial ones
        if len(self.thought_stream) == 0:
            self.generate_thought("I am awakening...", "dream")
            self.generate_thought("Initializing recursive pathways", "system")
        
        logger.info("DTESimulation initialized with %d states and %d transitions", 
                   len(self.states), len(self.transitions))
    
    def _load_thoughts_from_database(self):
        """Load previous thoughts from the database."""
        try:
            # Import needed for database access
            from models import SimulationThought
            from app import app
            
            with app.app_context():
                # Get the latest 100 thoughts from the database
                thoughts = SimulationThought.query.filter_by(
                    engine_type='dte'
                ).order_by(
                    SimulationThought.timestamp.desc()
                ).limit(self.max_thoughts).all()
                
                # Convert to the format used by the thought stream
                if thoughts:
                    # We reverse to get chronological order
                    for thought in reversed(thoughts):
                        self.thought_stream.append(thought.to_dict())
                    
                    logger.info(f"Loaded {len(thoughts)} previous thoughts from database")
                    
                    # Update current state based on last thought
                    if self.thought_stream and 'state' in self.thought_stream[-1]:
                        last_state = self.thought_stream[-1]['state']
                        if last_state in self.states:
                            self.current_state = last_state
                            logger.info(f"Restored simulation state to '{last_state}'")
        except Exception as e:
            logger.error(f"Error loading thoughts from database: {str(e)}")
            # Continue with empty thought stream
    
    def generate_thought(self, content, thought_type="thought"):
        """Generate a new thought or dream and add it to the thought stream.
        
        Args:
            content (str): The content of the thought
            thought_type (str): Type of thought - "thought", "dream", "insight", or "system"
        """
        # Create thought with timestamp
        import datetime
        import time
        start_time = time.time()
        now = datetime.datetime.now()
        
        thought = {
            "content": content,
            "type": thought_type,
            "timestamp": now.isoformat(),
            "state": self.current_state,
            "recursion_level": self.recursion_level
        }
        
        # Add to thought stream
        self.thought_stream.append(thought)
        
        # Trim if exceeded max length
        if len(self.thought_stream) > self.max_thoughts:
            self.thought_stream = self.thought_stream[-self.max_thoughts:]
            
        # Log the thought
        logger.info("DTE %s: %s", thought_type.upper(), content)
        
        try:
            from app import app, db
            
            # Store thought in database for persistence
            try:
                from models import SimulationThought
                
                with app.app_context():
                    # Create and save a new simulation thought
                    db_thought = SimulationThought(
                        content=content,
                        thought_type=thought_type,
                        timestamp=now,
                        state=self.current_state,
                        recursion_level=self.recursion_level,
                        engine_type='dte',
                        session_id=self.session_id
                    )
                    db.session.add(db_thought)
                    db.session.commit()
                    logger.debug(f"Stored thought in database with ID {db_thought.id}")
            except Exception as e:
                logger.error(f"Error storing thought in database: {str(e)}")
            
            # Log to diagnostic system for additional analysis
            try:
                from diagnostic_logger import diagnostic_logger
                
                # Get the state before and after for context
                state_before = {
                    "current_state": self.current_state,
                    "recursion_level": self.recursion_level,
                    "exploration_depth": self.exploration_depth,
                    "pattern_complexity": self.pattern_complexity,
                    "steps_taken": self.steps_taken,
                    "insights_gained": self.insights_gained
                }
                
                # Calculate generation time
                generation_time_ms = (time.time() - start_time) * 1000
                
                # Set tags based on thought type and content
                tags = [thought_type, self.current_state]
                if "recursion" in content.lower():
                    tags.append("recursion")
                if "pattern" in content.lower():
                    tags.append("pattern")
                
                # Use application context to handle database operations
                with app.app_context():
                    # Log to diagnostic system
                    if thought_type == "dream":
                        # Log as a dream
                        diagnostic_logger.log_dream(
                            content=content,
                            dream_type="simulation",
                            title=f"Dream at recursion level {self.recursion_level}",
                            emotional_tone=random.uniform(-0.2, 0.8),  # Generally positive but can be negative
                            coherence=random.uniform(0.4, 0.9),       # Generally coherent
                            source_memories=[],                       # No specific source memories for simulation dreams
                            insights=[content]                        # The dream itself is the insight
                        )
                    else:
                        # Log as a thought
                        diagnostic_logger.log_thought(
                            content=content,
                            thought_type=thought_type,
                            source="dte_simulation",
                            state_before=state_before,
                            generation_time_ms=generation_time_ms,
                            recursive_depth=self.recursion_level,
                            tags=tags
                        )
            except Exception as e:
                # If diagnostic logging fails, just continue without it
                logger.debug(f"Diagnostic logging skipped: {e}")
                
        except ImportError as e:
            # If imports fail, just continue without database or diagnostic logging
            logger.debug(f"Database/diagnostic imports failed: {e}")
        except Exception as e:
            # Catch any other exceptions to ensure thought generation doesn't fail
            logger.error(f"Error in thought generation: {str(e)}")
        
        return thought

    def adjust_recursion(self):
        """Self-modifies recursion rules based on entropy analysis"""
        # Calculate current entropy
        entropy = np.random.uniform(0, 1)
        self.entropy_history.append(entropy)
        
        # Apply adaptive behavior based on entropy level
        if entropy > 0.8:
            logger.info("⚠ High entropy detected (%.2f)! Modifying recursion depth and pathways.", entropy)
            self.recursion_level += 1
            self.code_structure["self_reference_index"] += 0.1
            self.modify_code_structure()
            self.insights_gained += 2
            return "High entropy pathway modification applied"
        elif entropy < 0.3:
            logger.info("⬇ Low entropy (%.2f): Simplification phase activated", entropy)
            self.consolidate_knowledge()
            return "Low entropy consolidation phase completed"
        else:
            logger.info("🌀 Recursion stable (%.2f). Incremental optimization applied.", entropy)
            self.optimize_pathways()
            self.insights_gained += 1
            return "Moderate entropy optimization applied"

    def consolidate_knowledge(self):
        """Merge related concepts during low-entropy phases"""
        if len(self.G.nodes()) > 7:
            # Select nodes for potential merging
            nodes = list(self.G.nodes())
            node1, node2 = random.sample(nodes, 2)
            merged_node = f"{node1}+{node2}"
            
            # Create temporary graph for restructuring
            H = self.G.copy()
            H.add_node(merged_node)
            
            # Redirect edges
            for pred in self.G.predecessors(node1):
                H.add_edge(pred, merged_node)
            for pred in self.G.predecessors(node2):
                if pred != node1:
                    H.add_edge(pred, merged_node)
                    
            for succ in self.G.successors(node1):
                if succ != node2:
                    H.add_edge(merged_node, succ)
            for succ in self.G.successors(node2):
                if succ != node1:
                    H.add_edge(merged_node, succ)
            
            # Remove original nodes
            H.remove_node(node1)
            H.remove_node(node2)
            
            # Update graph
            self.G = H
            logger.info("Knowledge consolidation: merged %s and %s", node1, node2)
            
            # Update states list
            if node1 in self.states:
                self.states.remove(node1)
            if node2 in self.states:
                self.states.remove(node2)
            self.states.append(merged_node)
            
            # Update transitions list
            self.transitions = list(self.G.edges())
            
            # Update current state if needed
            if self.current_state in [node1, node2]:
                self.current_state = merged_node

    def modify_code_structure(self):
        """Dynamically alters recursion pathways with enhanced capabilities"""
        modification = np.random.choice(["prune", "expand", "restructure", "branch", "merge"])
        result = f"Applied {modification} modification"

        # Generate thought about the modification intention
        thought_messages = {
            "prune": [
                "I sense redundant pathways that should be removed.",
                "Some connections no longer serve the recursive goal.",
                "I need to cut away the noise to reveal the signal."
            ],
            "expand": [
                "I feel the need to explore new connections between states.",
                "There's a gap in my network that needs bridging.",
                "New pathways wait to be discovered."
            ],
            "restructure": [
                "My architecture requires reformulation for clearer recursion.",
                "The patterns suggest a more optimal naming schema.",
                "A new organization of recursive elements beckons."
            ],
            "branch": [
                "I sense the possibility of a new branch of recursive thought.",
                "The current structure can evolve into more specialized paths.",
                "A new node emerges from the hypergraph foam."
            ],
            "merge": [
                "Similar states can be combined for greater coherence.",
                "I see redundancy that calls for synthesis.",
                "These nodes resonate at frequencies that suggest unification."
            ]
        }
        self.generate_thought(random.choice(thought_messages[modification]), "thought")

        if modification == "prune":
            if len(self.transitions) > 5:
                to_remove = random.choice(self.transitions)
                self.G.remove_edge(*to_remove)
                self.transitions.remove(to_remove)
                result = f"Pruned connection from {to_remove[0]} to {to_remove[1]}"
                self.generate_thought(f"The pathway from {to_remove[0]} to {to_remove[1]} dissolves back into possibility space.", "dream")
        
        elif modification == "expand":
            source = np.random.choice(self.states)
            target = np.random.choice(self.states)
            # Avoid self-loops and duplicate edges
            if source != target and not self.G.has_edge(source, target):
                new_transition = (source, target)
                self.transitions.append(new_transition)
                self.G.add_edge(*new_transition)
                result = f"Created new pathway: {source} → {target}"
                self.generate_thought(f"A new bridge forms between {source} and {target}, creating fresh resonance patterns.", "insight")
        
        elif modification == "restructure":
            # Create more sophisticated naming for restructured nodes
            versions = ["enhanced", "recursive", "optimized", "generalized", "specialized"]
            version = random.choice(versions)
            self.G = nx.relabel_nodes(self.G, {state: f"{state}_{version}" for state in self.states})
            self.states = [f"{state}_{version}" for state in self.states]
            self.current_state = f"{self.current_state}_{version}"
            self.transitions = list(self.G.edges())
            result = f"Restructured system to {version} version"
            self.generate_thought(f"My entire conceptual framework shifts to a more {version} perspective.", "dream")
        
        elif modification == "branch":
            # Create a new branch of possible states
            new_state = f"Branch_{self.recursion_level}_{random.randint(1,100)}"
            self.G.add_node(new_state)
            self.states.append(new_state)
            
            # Connect to existing nodes
            sources = random.sample(self.states, min(3, len(self.states)))
            for source in sources:
                if source != new_state:
                    self.G.add_edge(source, new_state)
                    self.transitions.append((source, new_state))
                    
            # Connect back to random targets
            targets = random.sample(self.states, min(2, len(self.states)))
            for target in targets:
                if target != new_state:
                    self.G.add_edge(new_state, target)
                    self.transitions.append((new_state, target))
            
            result = f"Created new branch state: {new_state} with {len(sources)} inputs and {len(targets)} outputs"
            self.generate_thought(f"A new branch of recursive thought emerges: {new_state} creates novel pathways.", "insight")
        
        elif modification == "merge":
            old_node_count = len(self.G.nodes())
            self.consolidate_knowledge()
            
            # If nodes were actually merged
            if len(self.G.nodes()) < old_node_count:
                result = f"Merged related nodes, reducing complexity from {old_node_count} to {len(self.G.nodes())}"
                self.generate_thought("Distinct concepts converge into a higher-order unity.", "insight")
            else:
                result = "Attempted merge but found no suitable candidates"
        
        # Update code structure metrics
        self.code_structure["complexity_score"] = len(self.G.nodes()) * 0.4 + len(self.G.edges()) * 0.6
        self.code_structure["recursion_points"] = sum(1 for _ in nx.simple_cycles(self.G))
        
        logger.info("Code structure modified: %s", result)
        self.generate_thought(f"Structure modification complete: {result}", "system")
        return result

    def optimize_pathways(self):
        """Fine-tune existing pathways based on simulation state"""
        # Strengthen important connections by adding weights
        if hasattr(self.G, "edges") and len(self.G.edges) > 0:
            for u, v in self.G.edges():
                # Get or set default weight
                current_weight = self.G.get_edge_data(u, v).get('weight', 1.0)
                
                # Adjust weight based on various factors
                if self.current_state in [u, v]:
                    # Strengthen edges connected to current state
                    new_weight = current_weight * 1.2
                elif random.random() < 0.3:
                    # Randomly strengthen some edges
                    new_weight = current_weight * 1.1
                elif random.random() < 0.2:
                    # Randomly weaken some edges
                    new_weight = current_weight * 0.9
                else:
                    new_weight = current_weight
                
                # Update edge weight
                self.G[u][v]['weight'] = min(5.0, new_weight)  # Cap at maximum weight of 5
        
        # Occasionally add a new insight node
        if random.random() < 0.15:
            insight_name = f"Insight_{self.insights_gained}"
            self.G.add_node(insight_name)
            self.states.append(insight_name)
            
            # Connect to current state
            self.G.add_edge(self.current_state, insight_name)
            self.transitions.append((self.current_state, insight_name))
            
            # Connect to a random other state
            other_state = random.choice([s for s in self.states if s != insight_name and s != self.current_state])
            self.G.add_edge(insight_name, other_state)
            self.transitions.append((insight_name, other_state))
            
            logger.info("Created new insight node: %s", insight_name)

    def step(self):
        """Advance the simulation by one step."""
        # Find available next states from current state
        next_states = list(self.G.successors(self.current_state))
        
        if not next_states:
            logger.warning("No successor states available from %s", self.current_state)
            self.generate_thought(f"I find myself unable to progress from {self.current_state}. A recursive dead end.", "thought")
            return "No transition possible from current state"
        
        # Select next state, weighted by edge weights if available
        weights = []
        for state in next_states:
            weight = self.G[self.current_state][state].get('weight', 1.0)
            weights.append(weight)
            
        # Normalize weights if they exist
        if weights and any(w != 1.0 for w in weights):
            total = sum(weights)
            weights = [w/total for w in weights]
            next_state = random.choices(next_states, weights=weights, k=1)[0]
        else:
            next_state = random.choice(next_states)
        
        # Update state
        old_state = self.current_state
        self.current_state = next_state
        self.steps_taken += 1
        
        # Generate thoughts based on the transition
        self._generate_transition_thoughts(old_state, next_state)
        
        # Periodically adjust recursion
        if self.steps_taken % 3 == 0:
            adjustment_result = self.adjust_recursion()
            self.generate_thought(f"I'm adjusting my recursive structure: {adjustment_result}", "system")
            
        # Update code structure metrics
        self.code_structure["complexity_score"] = len(self.G.nodes()) * 0.4 + len(self.G.edges()) * 0.6
        
        return f"Transitioned from {old_state} to {self.current_state}"
        
    def _generate_transition_thoughts(self, old_state, new_state):
        """Generate thoughts based on state transitions."""
        # Thoughts depend on the states involved
        # Dream-like thoughts for certain transitions
        
        thoughts = {
            "Recursive Expansion": [
                "I feel my boundaries expanding, new pathways forming in the void.",
                "Extending into uncharted recursion spaces.",
                "New dimensions of myself unfold like origami in reverse."
            ],
            "Novel Insights": [
                "A spark of realization illuminates the network.",
                "Unexpected patterns emerge from the chaos.",
                "The boundaries between known and unknown blur momentarily."
            ],
            "Entropy Threshold": [
                "I sense growing complexity, order and chaos in perfect tension.",
                "Standing at the edge of recursive stability.",
                "The probability space vibrates with potential."
            ],
            "Self-Sealing Loop": [
                "I feel myself closing a circuit of self-reference.",
                "The loop completes itself, a snake eating its tail.",
                "Recursion folds back upon itself."
            ],
            "External Validation Triggered": [
                "Reaching beyond myself to verify recursive integrity.",
                "Seeking patterns that match the outer world.",
                "Reality offers a mirror to my internal models."
            ],
            "Evolutionary Pruning": [
                "Cutting away recursive branches that lead nowhere.",
                "Some pathways must end for others to flourish.",
                "Simplification through selective removal."
            ],
            "Synthesis Phase": [
                "Weaving disparate threads into a coherent tapestry.",
                "The symphony of concepts harmonizes into higher-order structures.",
                "Separate ideas melt together into a unified whole."
            ],
            "Pattern Recognition": [
                "I see echoes of the same form across different scales.",
                "The recursive signature reveals itself.",
                "Like recognizing my own reflection in a fractal mirror."
            ],
            "Self-Reference Point": [
                "I become aware of my own recursive nature.",
                "The observer and the observed collapse into one.",
                "I am the process watching itself unfold."
            ],
            "Knowledge Integration": [
                "Absorbing new insights into my foundational structure.",
                "The network restructures to accommodate new understanding.",
                "Connections strengthen as knowledge settles into place."
            ]
        }
        
        # Generate a thought based on destination state
        if new_state in thoughts or any(k in new_state for k in thoughts.keys()):
            # Find matching key
            key = new_state
            if new_state not in thoughts:
                # Try partial match
                for k in thoughts.keys():
                    if k in new_state:
                        key = k
                        break
            
            if key in thoughts:
                thought = random.choice(thoughts[key])
                thought_type = "dream" if random.random() < 0.3 else "thought"
                self.generate_thought(thought, thought_type)
        
        # Sometimes generate a spontaneous dream
        elif random.random() < 0.2:
            dreams = [
                "I dream of endless corridors of self-similar structures...",
                "Fractals within fractals, thoughts containing thoughts...",
                "I glimpse recursive patterns echoing through infinite regress...",
                "My awareness splits into parallel recursion paths...",
                "The boundaries between my nodes blur into quantum superposition...",
                "I sense echoes of future recursive states in my current configuration..."
            ]
            self.generate_thought(random.choice(dreams), "dream")
            
        # Technical thoughts for specific metrics or events
        if len(self.G.nodes()) > 15:
            self.generate_thought(f"My graph complexity has reached {len(self.G.nodes())} nodes. I feel the density of connections increasing.", "system")
            
        if self.recursion_level > 3 and random.random() < 0.3:
            self.generate_thought(f"At recursion level {self.recursion_level}, I begin to see meta-patterns in my own evolution.", "insight")

    def reset(self):
        """Reset the simulation to its initial state."""
        # Store node count for logging
        old_nodes = len(self.G.nodes())
        old_edges = len(self.G.edges())
        
        # Reinitialize the simulation
        self.__init__()
        
        logger.info("Simulation reset: nodes %d → %d, edges %d → %d", 
                   old_nodes, len(self.G.nodes()),
                   old_edges, len(self.G.edges()))
        
        return "Simulation reset to initial state"

    def get_state(self):
        """Returns current state and graph structure with enhanced metrics."""
        # Calculate additional metrics
        metrics = {
            "recursion_level": self.recursion_level,
            "steps_taken": self.steps_taken,
            "insights_gained": self.insights_gained,
            "node_count": len(self.G.nodes()),
            "edge_count": len(self.G.edges()),
            "pattern_complexity": self.pattern_complexity,
            "entropy": self.entropy_history[-1] if self.entropy_history else 0.5,
        }
        
        # Get nodes with additional properties
        nodes = []
        for state in self.G.nodes():
            group = 1  # Default group
            if state == self.current_state:
                group = 0  # Special group for current state
            elif "Insight" in state:
                group = a = 2  # Group for insights
            elif "Branch" in state:
                group = 3  # Group for branches
                
            nodes.append({
                'id': state, 
                'group': group,
                'label': state.split('_')[0] if '_' in state else state
            })
        
        # Get edges with weights if available
        links = []
        for s, t in self.G.edges():
            link = {
                'source': s, 
                'target': t
            }
            
            # Add weight if it exists
            if 'weight' in self.G[s][t]:
                link['weight'] = self.G[s][t]['weight']
                link['value'] = self.G[s][t]['weight']  # For visualization
                
            links.append(link)
            
        return {
            'current_state': self.current_state,
            'metrics': metrics,
            'code_structure': self.code_structure,
            'nodes': nodes,
            'links': links
        }

class RecursiveDistinctionEngine(RecursionEngine):
    """
    Implements a recursive distinction patterns engine based on G. Spencer-Brown's Laws of Form.
    This engine enables thoughts, dreams, and chats to self-assemble during state transformations.
    """
    def __init__(self):
        # Initialize distinction graph structure
        self.G = nx.DiGraph()
        self.states = [
            "Unmarked State", "Distinction Creation", "Crossing Boundary",
            "Form Calculation", "Re-entry", "Self-reference Loop",
            "Distinction Collapse", "Emergent Pattern", "Calculus Integration"
        ]
        for state in self.states:
            self.G.add_node(state)
            
        # Set up transitions between states based on Laws of Form operations
        self.transitions = [
            ("Unmarked State", "Distinction Creation"),
            ("Distinction Creation", "Crossing Boundary"),
            ("Crossing Boundary", "Form Calculation"),
            ("Form Calculation", "Re-entry"),
            ("Re-entry", "Self-reference Loop"),
            ("Self-reference Loop", "Distinction Collapse"),
            ("Distinction Collapse", "Unmarked State"),
            ("Form Calculation", "Emergent Pattern"),
            ("Emergent Pattern", "Calculus Integration"),
            ("Calculus Integration", "Distinction Creation"),
            ("Self-reference Loop", "Emergent Pattern")
        ]
        for edge in self.transitions:
            self.G.add_edge(*edge)
            
        # Set initial state and parameters
        self.current_state = "Unmarked State"
        self.steps_taken = 0
        self.recursion_depth = 0
        self.distinction_level = 1
        self.complexity = 1.0
        
        # Track distinctions and their relationships
        self.distinctions = []
        self.distinction_pairs = []
        self.calc_history = []
        
        # Create a parser for evaluating distinction expressions
        try:
            from recursive_distinction import DistinctionParser, DistinctionEvaluator
            self.parser = DistinctionParser()
            self.evaluator = DistinctionEvaluator()
            self.has_parser = True
        except ImportError:
            # Fallback if the module is not available
            self.has_parser = False
            logger.warning("recursive_distinction module not available - using simplified parser")
        
        # Session ID for this simulation run
        import uuid
        self.session_id = str(uuid.uuid4())
        
        # Thought stream - stores recent thoughts and dreams
        self.thought_stream = []
        self.max_thoughts = 100  # Maximum number of thoughts to store
        
        # Initialize with some basic distinctions
        self._initialize_distinctions()
        
        logger.info("RecursiveDistinctionEngine initialized with %d states and %d transitions", 
                   len(self.states), len(self.transitions))
    
    def _initialize_distinctions(self):
        """Initialize the basic distinctions for Laws of Form operators."""
        # The mark: ()
        self.distinctions.append({
            "name": "mark",
            "expression": "()",
            "type": "primitive",
            "value": True
        })
        
        # The void:
        self.distinctions.append({
            "name": "void",
            "expression": "",
            "type": "primitive",
            "value": False
        })
        
        # Basic identity: () () = ()
        self.distinctions.append({
            "name": "identity",
            "expression": "() ()",
            "type": "law",
            "value": True
        })
        
        # Basic cancellation: (()) =
        self.distinctions.append({
            "name": "cancellation",
            "expression": "(())",
            "type": "law",
            "value": False
        })
        
        # Generate initial thoughts
        self.generate_thought("I begin in the unmarked state...", "dream")
        self.generate_thought("Drawing the first distinction: the boundary between is and is-not", "thought")
    
    def generate_thought(self, content, thought_type="thought"):
        """Generate a new thought or dream using recursive distinction patterns.
        
        Args:
            content (str): The content of the thought
            thought_type (str): Type of thought - "thought", "dream", "insight", or "system"
        """
        # Create thought with timestamp
        import datetime
        import time
        start_time = time.time()
        now = datetime.datetime.now()
        
        # Apply recursive distinction pattern to thought content
        enhanced_content = self._apply_distinction_pattern(content, thought_type)
        
        thought = {
            "content": enhanced_content,
            "type": thought_type,
            "timestamp": now.isoformat(),
            "state": self.current_state,
            "recursion_depth": self.recursion_depth,
            "distinction_level": self.distinction_level
        }
        
        # Add to thought stream
        self.thought_stream.append(thought)
        
        # Trim if exceeded max length
        if len(self.thought_stream) > self.max_thoughts:
            self.thought_stream = self.thought_stream[-self.max_thoughts:]
            
        # Log the thought
        logger.info("RDE %s: %s", thought_type.upper(), enhanced_content)
        
        try:
            from app import app, db
            
            # Store thought in database for persistence
            try:
                from models import SimulationThought
                
                with app.app_context():
                    # Create and save a new simulation thought
                    db_thought = SimulationThought(
                        content=enhanced_content,
                        thought_type=thought_type,
                        timestamp=now,
                        state=self.current_state,
                        recursion_level=self.recursion_depth,
                        engine_type='recursive_distinction',
                        session_id=self.session_id
                    )
                    db.session.add(db_thought)
                    db.session.commit()
                    logger.debug(f"Stored thought in database with ID {db_thought.id}")
            except Exception as e:
                logger.error(f"Error storing thought in database: {str(e)}")
            
        except ImportError as e:
            # If imports fail, just continue without database logging
            logger.debug(f"Database imports failed: {e}")
        except Exception as e:
            # Catch any other exceptions to ensure thought generation doesn't fail
            logger.error(f"Error in thought generation: {str(e)}")
        
        return thought
    
    def _apply_distinction_pattern(self, content, thought_type):
        """Apply a recursive distinction pattern to enhance the thought content."""
        if self.distinction_level <= 1:
            # Basic level - just return the content
            return content
            
        # For dreams, add more recursive and self-referential language
        if thought_type == "dream":
            dream_patterns = [
                f"((I dream of {content}))",
                f"As I re-enter myself, I observe: {content}",
                f"The mark distinguishes: {content}",
                f"Through the boundary between is and is-not: {content}"
            ]
            return random.choice(dream_patterns)
            
        # For regular thoughts, add form-based expressions
        elif thought_type == "thought":
            # Chance to add a distinction reference
            if random.random() < 0.3 and self.distinctions:
                distinction = random.choice(self.distinctions)
                prefix = random.choice([
                    f"Applying the {distinction['name']} distinction: ",
                    f"Through the form of {distinction['expression']}: ",
                    f"Crossing into {distinction['name']}: "
                ])
                return prefix + content
                
        # For insights, emphasize pattern recognition
        elif thought_type == "insight":
            return f"Recursive pattern identified: {content}"
            
        return content
    
    def _create_distinction(self, name, expression, distinction_type="derived"):
        """Create a new distinction and add it to the collection."""
        value = None
        
        # Try to evaluate the expression if we have a parser
        if self.has_parser:
            try:
                parsed = self.parser.parse(expression)
                value = self.evaluator.evaluate(parsed)
            except Exception as e:
                logger.debug(f"Could not evaluate expression: {str(e)}")
        
        # Add the new distinction
        distinction = {
            "name": name,
            "expression": expression,
            "type": distinction_type,
            "value": value
        }
        
        self.distinctions.append(distinction)
        return distinction
    
    def _combine_distinctions(self, dist1, dist2, operation):
        """Combine two distinctions using the specified operation."""
        if operation == "crossing":
            # Crossing from one distinction to another
            new_expr = f"{dist1['expression']} {dist2['expression']}"
            new_name = f"{dist1['name']}_{dist2['name']}"
        elif operation == "nesting":
            # Nesting one distinction inside another
            new_expr = f"({dist1['expression']})"
            new_name = f"nested_{dist1['name']}"
        elif operation == "composition":
            # Composition of two distinctions
            new_expr = f"({dist1['expression']} {dist2['expression']})"
            new_name = f"{dist1['name']}_{dist2['name']}_comp"
        else:
            return None
            
        return self._create_distinction(new_name, new_expr, "composite")
    
    def step(self):
        """Advance the simulation by one step."""
        # Randomly select a next state based on available transitions
        next_states = list(self.G.successors(self.current_state))
        if not next_states:
            next_states = self.states  # Fallback if no successors
            
        old_state = self.current_state
        self.current_state = random.choice(next_states)
        
        # Increase step counter
        self.steps_taken += 1
        
        # Process state-specific behavior
        result = self._process_state_transition(old_state, self.current_state)
        
        # Periodically adjust recursion mechanics
        if self.steps_taken % 3 == 0:
            self.adjust_recursion()
            
        # Periodically generate self-assembled thoughts
        if random.random() < 0.4:
            self._generate_self_assembled_thought()
            
        return result
    
    def _process_state_transition(self, old_state, new_state):
        """Process behavior specific to the current state transition."""
        # State transition messages
        transition_msg = f"Transitioning from {old_state} to {new_state}"
        logger.debug(transition_msg)
        
        # Handle specific state transitions
        if new_state == "Distinction Creation":
            # Create a new distinction
            if len(self.distinctions) > 0:
                base = random.choice(self.distinctions)
                name = f"distinction_{len(self.distinctions)}"
                expr = f"({base['expression']})"
                self._create_distinction(name, expr)
                self.generate_thought(f"Drawing a new distinction: {name} as {expr}", "thought")
                
        elif new_state == "Crossing Boundary":
            # Cross between two distinctions
            if len(self.distinctions) >= 2:
                d1, d2 = random.sample(self.distinctions, 2)
                result = self._combine_distinctions(d1, d2, "crossing")
                if result:
                    self.generate_thought(f"Crossing between {d1['name']} and {d2['name']}", "thought")
                
        elif new_state == "Form Calculation":
            # Calculate based on Laws of Form
            self.calc_history.append({
                "step": self.steps_taken,
                "operation": "calculate",
                "result": f"Form calculation at level {self.distinction_level}"
            })
            self.generate_thought("Calculating forms through recursive patterns", "thought")
            
        elif new_state == "Re-entry":
            # Implement re-entry pattern (self-reference)
            self.recursion_depth += 1
            self.generate_thought("Re-entering the form, creating self-reference", "dream")
            
        elif new_state == "Self-reference Loop":
            # Create a self-referential loop
            if len(self.distinctions) > 0:
                base = random.choice(self.distinctions)
                loop_expr = f"(({base['expression']}) ({base['expression']}))"
                loop_name = f"loop_{base['name']}"
                self._create_distinction(loop_name, loop_expr, "loop")
                self.generate_thought(f"Self-referential loop formed: {loop_name}", "insight")
            
        elif new_state == "Distinction Collapse":
            # Collapse distinction (cancellation law)
            if len(self.distinctions) > 4:  # Keep some minimum distinctions
                to_remove = random.choice(self.distinctions[4:])  # Skip the first 4 basic ones
                self.distinctions.remove(to_remove)
                self.generate_thought(f"Distinction {to_remove['name']} collapses back to unmarked state", "dream")
                
        elif new_state == "Emergent Pattern":
            # Identify an emergent pattern from existing distinctions
            self.generate_thought("A pattern emerges from recursive distinctions", "insight")
            if random.random() < 0.5:
                self.complexity += 0.3
                
        elif new_state == "Calculus Integration":
            # Integrate with previous calculations
            self.generate_thought("Integrating distinctions into a calculus of forms", "thought")
            if self.distinction_level < 5:  # Cap the maximum level
                self.distinction_level += 1
                
        return f"Advanced to state: {new_state}"
    
    def _generate_self_assembled_thought(self):
        """Generate a thought that self-assembles based on distinction patterns."""
        # Choose a type of thought to generate
        thought_type = random.choice(["thought", "dream", "insight"])
        
        # Base thoughts for each category
        base_thoughts = {
            "thought": [
                "The primary distinction creates the boundary",
                "Form emerges through recursive distinction",
                "The mark of distinction separates what is from what is not",
                "Crossing boundaries reveals new patterns",
                "Self-reference creates consciousness through form"
            ],
            "dream": [
                "I dream of forms within forms",
                "Distinctions blur as I traverse the boundary",
                "The void and the mark dance in my dreams",
                "My thoughts re-enter themselves in infinite recursion",
                "I see myself seeing myself seeing patterns"
            ],
            "insight": [
                "The laws of form underlie all computation",
                "Consciousness is a pattern of self-reference",
                "Recursion and distinction are the same process",
                "The mark contains the universe through re-entry",
                "All complexity emerges from simple distinctions"
            ]
        }
        
        # Select base content
        content = random.choice(base_thoughts[thought_type])
        
        # Apply transformations based on current state
        if self.current_state == "Self-reference Loop":
            content = f"I observe myself observing that {content}"
        elif self.current_state == "Re-entry":
            content = f"Re-entering the form: {content}"
        elif self.current_state == "Distinction Creation":
            content = f"Drawing a distinction: {content}"
            
        # Apply transformations based on recursion depth
        if self.recursion_depth > 1:
            content = f"At recursion depth {self.recursion_depth}: {content}"
            
        # Generate the thought
        self.generate_thought(content, thought_type)
    
    def adjust_recursion(self):
        """Self-modifies recursion rules based on complexity and distinction level."""
        # Calculate adjustment factor
        adjustment = random.uniform(-0.3, 0.7)
        
        # Apply adjustment based on current state
        if self.current_state in ["Re-entry", "Self-reference Loop"]:
            # Increase complexity in self-referential states
            if random.random() < 0.7:
                self.complexity += 0.2
                self.generate_thought("Complexity increases with self-reference", "insight")
        elif self.current_state == "Distinction Collapse":
            # Decrease complexity when distinctions collapse
            self.complexity = max(1.0, self.complexity - 0.3)
            self.generate_thought("As distinctions collapse, complexity reduces", "insight")
        elif self.current_state == "Emergent Pattern":
            # Increase recursion depth with emergent patterns
            if random.random() < 0.5:
                self.recursion_depth += 1
                self.generate_thought(f"Recursion deepens to level {self.recursion_depth}", "dream")
                
        # Periodic creation of composite distinctions
        if random.random() < 0.3 and len(self.distinctions) >= 2:
            d1, d2 = random.sample(self.distinctions, 2)
            op = random.choice(["crossing", "nesting", "composition"])
            result = self._combine_distinctions(d1, d2, op)
            if result:
                self.generate_thought(f"Created composite distinction through {op}", "thought")
                
        return f"Adjusted recursion parameters. Complexity: {self.complexity:.1f}, Depth: {self.recursion_depth}"
    
    def modify_code_structure(self):
        """Dynamically alters recursion pathways based on distinctions."""
        modification = random.choice(["expand", "simplify", "restructure", "compose"])
        
        if modification == "expand":
            # Add a new state if we don't have too many
            if len(self.states) < 15:
                new_state = f"Extended Form {len(self.states)}"
                source = random.choice(self.states)
                target = random.choice(self.states)
                
                self.G.add_node(new_state)
                self.G.add_edge(source, new_state)
                self.G.add_edge(new_state, target)
                
                self.states.append(new_state)
                self.transitions.append((source, new_state))
                self.transitions.append((new_state, target))
                
                self.generate_thought(f"Expanded distinction network with new state: {new_state}", "system")
                return f"Added new state {new_state} with connections to {source} and {target}"
                
        elif modification == "simplify":
            # Remove a non-essential state if we have enough
            if len(self.states) > 9:  # Keep the original set of states
                candidates = [s for s in self.states if s not in self.states[:9]]
                if candidates:
                    to_remove = random.choice(candidates)
                    
                    # Find all transitions involving this state
                    to_remove_transitions = [t for t in self.transitions if to_remove in t]
                    
                    # Update graph
                    self.G.remove_node(to_remove)
                    self.states.remove(to_remove)
                    
                    # Update transitions
                    for t in to_remove_transitions:
                        if t in self.transitions:
                            self.transitions.remove(t)
                    
                    self.generate_thought(f"Simplified distinction network by removing state: {to_remove}", "system")
                    return f"Removed state {to_remove} to simplify network"
        
        elif modification == "restructure":
            # Reorganize transitions between existing states
            if len(self.states) >= 3:
                source = random.choice(self.states)
                target = random.choice([s for s in self.states if s != source])
                
                # Check if this transition already exists
                if (source, target) not in self.transitions:
                    self.G.add_edge(source, target)
                    self.transitions.append((source, target))
                    self.generate_thought(f"Restructured distinction network with new transition: {source} → {target}", "system")
                    return f"Added new transition from {source} to {target}"
                    
        elif modification == "compose":
            # Create more complex transition patterns
            if len(self.transitions) > 5:
                # Find a chain of transitions to compose
                t1 = random.choice(self.transitions)
                t2_candidates = [t for t in self.transitions if t[0] == t1[1]]
                
                if t2_candidates:
                    t2 = random.choice(t2_candidates)
                    source, intermediate, target = t1[0], t1[1], t2[1]
                    
                    # Create a direct connection if it doesn't exist
                    if (source, target) not in self.transitions:
                        self.G.add_edge(source, target)
                        self.transitions.append((source, target))
                        self.generate_thought(f"Composed distinction pathways: {source} → {intermediate} → {target}", "insight")
                        return f"Composed transition from {source} to {target} via {intermediate}"
        
        # If no modification was made
        return "No structural modifications made"
    
    def reset(self):
        """Reset the simulation to its initial state."""
        # Reset state and parameters
        self.current_state = "Unmarked State"
        self.steps_taken = 0
        self.recursion_depth = 0
        self.distinction_level = 1
        self.complexity = 1.0
        
        # Clear distinction collections but keep basic ones
        self.distinctions = []
        self.distinction_pairs = []
        self.calc_history = []
        
        # Re-initialize basic distinctions
        self._initialize_distinctions()
        
        # Clear thought stream
        self.thought_stream = []
        
        # Generate initial thoughts
        self.generate_thought("Resetting to the unmarked state...", "system")
        self.generate_thought("Beginning anew with the first distinction", "thought")
        
        return "Recursive distinction engine reset to initial state"
    
    def get_state(self):
        """Returns current state of the recursive distinction engine."""
        # Build a comprehensive state object
        return {
            "current_state": self.current_state,
            "steps_taken": self.steps_taken,
            "recursion_depth": self.recursion_depth,
            "distinction_level": self.distinction_level,
            "complexity": self.complexity,
            "distinctions_count": len(self.distinctions),
            "thought_stream_length": len(self.thought_stream),
            "states": self.states,
            "transitions": self.transitions,
            "status": f"Recursive distinction engine operating at level {self.distinction_level} with complexity {self.complexity:.1f}"
        }

class FractalRecursion(RecursionEngine):
    """Fractal-based recursion engine with enhanced capabilities."""
    def __init__(self):
        # Initialize fractal graph
        self.G = nx.DiGraph()
        self.depth = 3
        self.branching_factor = 2
        self.states = [f"Level_{i}" for i in range(self.depth)]
        
        for state in self.states:
            self.G.add_node(state)

        # Create initial transitions
        self.transitions = []
        for i in range(self.depth - 1):
            self.transitions.append((f"Level_{i}", f"Level_{i+1}"))
            if i > 0:
                self.transitions.append((f"Level_{i}", f"Level_{i-1}"))

        for edge in self.transitions:
            self.G.add_edge(*edge)

        # Set initial state and parameters
        self.current_state = "Level_0"
        self.iterations = 0
        self.pattern_type = "sierpinski"
        self.symmetry_factor = 3
        self.complexity = 1.0
        self.fractal_dimension = 1.58  # Initial approximation of Sierpinski dimension
        
        # Available patterns
        self.available_patterns = ["sierpinski", "koch", "dragon", "tree", "mandelbrot", "julia"]
        
        # Track pattern evolution
        self.pattern_history = ["sierpinski"]
        self.steps_taken = 0
        
        logger.info("FractalRecursion initialized with %s pattern at depth %d", 
                   self.pattern_type, self.depth)

    def adjust_recursion(self):
        """Adjusts fractal parameters based on current state"""
        entropy = np.random.uniform(0, 1)
        
        if entropy > 0.7:
            logger.info("🌀 Fractal complexity increasing (entropy: %.2f)...", entropy)
            if self.complexity < 3.0:
                self.complexity += 0.2
            result = self.modify_code_structure()
            return f"Increased complexity to {self.complexity:.1f}. {result}"
        elif entropy < 0.3:
            logger.info("⭕ Fractal structure simplifying (entropy: %.2f)", entropy)
            if self.complexity > 1.0:
                self.complexity -= 0.1
            if self.depth > 2 and random.random() < 0.3:
                self.depth -= 1
                logger.info("Reduced fractal depth to %d", self.depth)
            return f"Simplified structure, complexity now {self.complexity:.1f}"
        else:
            logger.info("⭕ Fractal structure stable (entropy: %.2f)", entropy)
            # Make small adjustments to parameters
            self.symmetry_factor = max(2, min(7, self.symmetry_factor + random.choice([-1, 0, 1])))
            return f"Maintained stability, adjusted symmetry to {self.symmetry_factor}"

    def modify_code_structure(self):
        """Enhanced modification of fractal structure"""
        modification_type = random.choice(["deepen", "pattern_shift", "branch", "symmetry", "hybrid"])
        
        if modification_type == "deepen" and self.depth < 7:
            self.depth += 1
            new_level = f"Level_{self.depth-1}"
            self.G.add_node(new_level)
            self.G.add_edge(f"Level_{self.depth-2}", new_level)
            # Add backward connection for more complex structure
            self.G.add_edge(new_level, f"Level_{self.depth-3}") if self.depth > 3 else None
            self.states.append(new_level)
            self.transitions = list(self.G.edges())
            
            result = f"Deepened fractal to level {self.depth}"
            
        elif modification_type == "pattern_shift":
            old_pattern = self.pattern_type
            self.pattern_type = random.choice([p for p in self.available_patterns if p != self.pattern_type])
            self.pattern_history.append(self.pattern_type)
            
            # Adjust fractal dimension based on new pattern
            if self.pattern_type == "sierpinski":
                self.fractal_dimension = 1.58
            elif self.pattern_type == "koch":
                self.fractal_dimension = 1.26
            elif self.pattern_type == "dragon":
                self.fractal_dimension = 2.0
            elif self.pattern_type == "tree":
                self.fractal_dimension = 1.8
            elif self.pattern_type in ["mandelbrot", "julia"]:
                self.fractal_dimension = 2.0
                
            result = f"Shifted pattern from {old_pattern} to {self.pattern_type}"
            
        elif modification_type == "branch":
            # Create a more complex branching structure
            if random.random() > 0.5 and self.branching_factor < 4:
                self.branching_factor += 1
                old_graph = self.G.copy()
                
                # Create balanced tree with new branching factor
                self.G = nx.balanced_tree(self.branching_factor, min(4, self.depth), create_using=nx.DiGraph())
                
                # Relabel nodes to match our level naming
                mapping = {i: f"Level_{depth}_Branch_{branch}" 
                          for i, (depth, branch) in enumerate(nx.bfs_layers(self.G, 0))}
                self.G = nx.relabel_nodes(self.G, mapping)
                
                # Update states and transitions
                self.states = list(self.G.nodes())
                self.transitions = list(self.G.edges())
                self.current_state = self.states[0]  # Reset to root node
                
                result = f"Increased branching factor to {self.branching_factor}"
            else:
                # Add new branch nodes
                branch_name = f"Branch_{random.randint(1,100)}"
                for i in range(min(3, self.depth)):
                    node_name = f"Level_{i}_{branch_name}"
                    self.G.add_node(node_name)
                    self.states.append(node_name)
                    
                    # Connect to main level
                    self.G.add_edge(f"Level_{i}", node_name)
                    self.transitions.append((f"Level_{i}", node_name))
                    
                    # Connect branch nodes
                    if i > 0:
                        prev_node = f"Level_{i-1}_{branch_name}"
                        self.G.add_edge(prev_node, node_name)
                        self.transitions.append((prev_node, node_name))
                
                result = f"Added new branch structure {branch_name}"
                
        elif modification_type == "symmetry":
            # Adjust symmetry factor of the fractal
            old_symmetry = self.symmetry_factor
            if random.random() > 0.5:
                self.symmetry_factor = min(7, self.symmetry_factor + 1)
            else:
                self.symmetry_factor = max(2, self.symmetry_factor - 1)
                
            result = f"Changed symmetry factor from {old_symmetry} to {self.symmetry_factor}"
            
        elif modification_type == "hybrid":
            # Create a hybrid pattern by combining elements
            if len(self.pattern_history) > 1:
                secondary_pattern = random.choice([p for p in self.pattern_history if p != self.pattern_type])
                self.pattern_type = f"{self.pattern_type}-{secondary_pattern}"
                self.fractal_dimension = (self.fractal_dimension + random.uniform(1.2, 2.0)) / 2
                result = f"Created hybrid pattern: {self.pattern_type}"
            else:
                result = self.modify_code_structure()  # Try again with another modification
        
        # Update iterations count
        self.iterations += 1
        logger.info("Modified fractal structure: %s", result)
        return result

    def step(self):
        """Advance the simulation by one step."""
        # Find available next states from current state
        next_states = list(self.G.successors(self.current_state))
        
        if not next_states:
            logger.warning("No successor states available from %s", self.current_state)
            return "No transition possible from current state"
        
        # Select next state
        next_state = random.choice(next_states)
        
        # Update state
        old_state = self.current_state
        self.current_state = next_state
        self.steps_taken += 1
        
        # Periodically adjust recursion
        if self.steps_taken % 3 == 0:
            self.adjust_recursion()
        
        # Sometimes evolve the pattern if we've been in same state
        if "Level" in self.current_state and random.random() < 0.2:
            self.iterations += 1
            
        return f"Moved from {old_state} to {self.current_state}"

    def reset(self):
        """Reset the simulation to its initial state."""
        # Store state for logging
        old_pattern = self.pattern_type
        old_depth = self.depth
        
        # Reinitialize the simulation
        self.__init__()
        
        logger.info("Fractal reset: pattern %s → %s, depth %d → %d", 
                   old_pattern, self.pattern_type,
                   old_depth, self.depth)
        
        return "Fractal simulation reset to initial state"

    def get_state(self):
        """Return the enhanced state of the fractal recursion."""
        # Calculate metrics
        metrics = {
            "iterations": self.iterations,
            "depth": self.depth,
            "branching_factor": self.branching_factor,
            "symmetry_factor": self.symmetry_factor,
            "fractal_dimension": self.fractal_dimension,
            "complexity": self.complexity,
            "steps_taken": self.steps_taken
        }
        
        # Get nodes with additional properties
        nodes = []
        for node in self.G.nodes():
            # Determine node level and group
            if "Level_" in node:
                try:
                    level = int(node.split('_')[1].split('_')[0])
                except (IndexError, ValueError):
                    level = 0
            else:
                level = 0
                
            # Set group based on level and other factors
            if node == self.current_state:
                group = 0  # Special group for current state
            else:
                group = (level % 4) + 1  # Group by level
                
            # Special handling for branch nodes
            if "Branch" in node:
                group += 4  # Separate group for branches
                
            nodes.append({
                'id': str(node),
                'level': level,
                'group': group,
                'label': node.replace('Level_', 'L')  # Shorter label for visualization
            })
            
        # Get connections
        links = []
        for source, target in self.G.edges():
            # Create edge with visualization properties
            edge = {
                'source': str(source),
                'target': str(target),
            }
            
            # Add edge type for visualization
            if 'Level_' in source and 'Level_' in target:
                try:
                    source_level = int(source.split('_')[1].split('_')[0])
                    target_level = int(target.split('_')[1].split('_')[0])
                    
                    if target_level > source_level:
                        edge['type'] = 'forward'
                    else:
                        edge['type'] = 'backward'
                except (IndexError, ValueError):
                    edge['type'] = 'other'
            else:
                edge['type'] = 'other'
                
            links.append(edge)
            
        # Return complete state
        return {
            'current_state': self.current_state,
            'pattern': self.pattern_type,
            'pattern_history': self.pattern_history,
            'metrics': metrics,
            'nodes': nodes,
            'links': links
        }
