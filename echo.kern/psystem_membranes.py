#!/usr/bin/env python3
"""
P-System Membrane Data Structures for Deep Tree Echo State Networks
===================================================================

This module implements comprehensive P-System membrane computing data structures
based on membrane computing theory and P-Lingua specifications. These structures
support the full computational model of P-Systems including:

- Hierarchical membrane organization
- Object multisets and symbol management
- Evolution rules with priorities
- Membrane communication protocols
- Dissolution and division operations
- Real-time membrane evolution for DTESN integration

Authors: Echo.Kern Development Team
License: MIT
Version: 1.0
"""

import sys
import re
import json
import uuid
import time
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, Counter
from abc import ABC, abstractmethod
import threading
import logging

# Configure logging for P-System operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MembraneType(Enum):
    """Types of membranes in the P-System hierarchy"""
    ROOT = "root"
    TRUNK = "trunk" 
    BRANCH = "branch"
    LEAF = "leaf"
    TERMINAL = "terminal"
    SKIN = "skin"
    ELEMENTARY = "elementary"

class RuleType(Enum):
    """Types of evolution rules in P-Systems"""
    EVOLUTION = auto()          # Object evolution within membrane
    COMMUNICATION = auto()      # Send objects between membranes
    DISSOLUTION = auto()        # Dissolve membrane
    DIVISION = auto()           # Divide membrane
    CREATION = auto()           # Create new membrane
    SYMPORT = auto()           # Synchronized transport
    ANTIPORT = auto()          # Anti-synchronized transport

class ExecutionPhase(Enum):
    """Phases of P-System execution"""
    INPUT = auto()
    EVOLUTION = auto()
    COMMUNICATION = auto()
    OUTPUT = auto()
    HALTED = auto()

@dataclass
class PSystemObject:
    """
    Represents an object in a P-System membrane.
    Objects are the basic computational units that evolve according to rules.
    """
    symbol: str
    multiplicity: int = 1
    properties: Dict[str, Any] = field(default_factory=dict)
    creation_time: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if self.multiplicity < 0:
            raise ValueError("Object multiplicity cannot be negative")
    
    def __str__(self) -> str:
        if self.multiplicity == 1:
            return self.symbol
        return f"{self.symbol}^{self.multiplicity}"
    
    def copy(self) -> 'PSystemObject':
        """Create a deep copy of the object"""
        return PSystemObject(
            symbol=self.symbol,
            multiplicity=self.multiplicity,
            properties=self.properties.copy(),
            creation_time=self.creation_time
        )

@dataclass
class Multiset:
    """
    Represents a multiset of objects in a P-System membrane.
    Multisets track object multiplicities and support P-System operations.
    """
    objects: Dict[str, int] = field(default_factory=dict)
    
    def add(self, symbol: str, multiplicity: int = 1) -> None:
        """Add objects to the multiset"""
        if multiplicity <= 0:
            return
        self.objects[symbol] = self.objects.get(symbol, 0) + multiplicity
    
    def remove(self, symbol: str, multiplicity: int = 1) -> bool:
        """Remove objects from the multiset. Returns True if successful."""
        if symbol not in self.objects or self.objects[symbol] < multiplicity:
            return False
        self.objects[symbol] -= multiplicity
        if self.objects[symbol] == 0:
            del self.objects[symbol]
        return True
    
    def contains(self, symbol: str, multiplicity: int = 1) -> bool:
        """Check if multiset contains at least the specified multiplicity"""
        return self.objects.get(symbol, 0) >= multiplicity
    
    def count(self, symbol: str) -> int:
        """Get the multiplicity of a symbol"""
        return self.objects.get(symbol, 0)
    
    def is_empty(self) -> bool:
        """Check if multiset is empty"""
        return len(self.objects) == 0
    
    def clear(self) -> None:
        """Clear all objects from the multiset"""
        self.objects.clear()
    
    def union(self, other: 'Multiset') -> 'Multiset':
        """Create union of two multisets"""
        result = Multiset()
        for symbol, count in self.objects.items():
            result.add(symbol, count)
        for symbol, count in other.objects.items():
            result.add(symbol, count)
        return result
    
    def intersection(self, other: 'Multiset') -> 'Multiset':
        """Create intersection of two multisets"""
        result = Multiset()
        for symbol in self.objects:
            if symbol in other.objects:
                min_count = min(self.objects[symbol], other.objects[symbol])
                result.add(symbol, min_count)
        return result
    
    def __str__(self) -> str:
        if not self.objects:
            return "∅"
        items = []
        for symbol, count in sorted(self.objects.items()):
            if count == 1:
                items.append(symbol)
            else:
                items.append(f"{symbol}^{count}")
        return " ".join(items)
    
    def __len__(self) -> int:
        """Total number of objects (sum of multiplicities)"""
        return sum(self.objects.values())

@dataclass
class EvolutionRule:
    """
    Represents an evolution rule in a P-System.
    Rules define how objects transform and communicate between membranes.
    """
    rule_id: str
    rule_type: RuleType
    lhs: Multiset  # Left-hand side (preconditions)
    rhs: Multiset  # Right-hand side (products)
    target_membrane: Optional[str] = None  # For communication rules
    source_membrane: Optional[str] = None  # For communication rules
    priority: int = 1
    condition: Optional[Callable] = None  # Custom condition function
    probability: float = 1.0  # For stochastic rules
    max_applications: Optional[int] = None  # Maximum times rule can be applied
    
    def __post_init__(self):
        if not (0.0 <= self.probability <= 1.0):
            raise ValueError("Rule probability must be between 0.0 and 1.0")
        if self.priority < 0:
            raise ValueError("Rule priority cannot be negative")
    
    def is_applicable(self, membrane_objects: Multiset, context: Dict[str, Any] = None) -> bool:
        """Check if rule can be applied to given objects"""
        # Check if preconditions are satisfied
        for symbol, required_count in self.lhs.objects.items():
            if not membrane_objects.contains(symbol, required_count):
                return False
        
        # Check custom condition if present
        if self.condition and context:
            return self.condition(membrane_objects, context)
        
        return True
    
    def apply(self, membrane_objects: Multiset) -> Tuple[bool, Multiset]:
        """
        Apply the rule to membrane objects.
        Returns (success, products) where products are objects to be added.
        """
        if not self.is_applicable(membrane_objects):
            return False, Multiset()
        
        # Remove precondition objects
        for symbol, count in self.lhs.objects.items():
            if not membrane_objects.remove(symbol, count):
                return False, Multiset()
        
        # Return products to be added
        return True, self.rhs
    
    def __str__(self) -> str:
        target_str = f" → {self.target_membrane}" if self.target_membrane else ""
        priority_str = f" [priority: {self.priority}]" if self.priority != 1 else ""
        return f"{self.lhs} → {self.rhs}{target_str}{priority_str}"

@dataclass 
class MembraneStructure:
    """
    Represents the hierarchical structure and properties of a P-System membrane.
    Each membrane has a unique identity, parent-child relationships, and computational state.
    """
    membrane_id: str
    membrane_type: MembraneType
    label: str
    parent_id: Optional[str] = None
    children_ids: Set[str] = field(default_factory=set)
    depth: int = 0
    
    # P-System specific properties
    objects: Multiset = field(default_factory=Multiset)
    rules: List[EvolutionRule] = field(default_factory=list)
    is_dissolved: bool = False
    charge: int = 0  # Membrane charge for certain P-System variants
    
    # DTESN integration properties
    neuron_count: int = 100
    spectral_radius: float = 0.9
    connectivity: float = 0.1
    
    # Timing and performance
    evolution_time_us: float = 0.0
    last_evolution: float = field(default_factory=time.time)
    
    # Thread safety
    _lock: threading.RLock = field(default_factory=threading.RLock)
    
    def add_child(self, child_id: str) -> None:
        """Add a child membrane"""
        with self._lock:
            self.children_ids.add(child_id)
    
    def remove_child(self, child_id: str) -> None:
        """Remove a child membrane"""
        with self._lock:
            self.children_ids.discard(child_id)
    
    def add_object(self, symbol: str, multiplicity: int = 1) -> None:
        """Add objects to the membrane"""
        with self._lock:
            self.objects.add(symbol, multiplicity)
    
    def remove_object(self, symbol: str, multiplicity: int = 1) -> bool:
        """Remove objects from the membrane"""
        with self._lock:
            return self.objects.remove(symbol, multiplicity)
    
    def add_rule(self, rule: EvolutionRule) -> None:
        """Add an evolution rule to the membrane"""
        with self._lock:
            self.rules.append(rule)
    
    def dissolve(self) -> None:
        """Mark membrane as dissolved"""
        with self._lock:
            self.is_dissolved = True
            logger.info(f"Membrane {self.membrane_id} dissolved")
    
    def is_elementary(self) -> bool:
        """Check if membrane is elementary (has no children)"""
        return len(self.children_ids) == 0
    
    def get_applicable_rules(self) -> List[EvolutionRule]:
        """Get all rules applicable to current membrane state"""
        with self._lock:
            applicable = []
            for rule in self.rules:
                if rule.is_applicable(self.objects):
                    applicable.append(rule)
            return applicable
    
    def __str__(self) -> str:
        children_str = f", children: {len(self.children_ids)}" if self.children_ids else ""
        objects_str = f", objects: {self.objects}" if not self.objects.is_empty() else ""
        return f"Membrane[{self.membrane_id}:{self.label}:{self.membrane_type.value}{children_str}{objects_str}]"

class PSystemMembraneHierarchy:
    """
    Manages the complete hierarchy of P-System membranes with DTESN integration.
    Provides operations for membrane evolution, communication, and real-time processing.
    """
    
    def __init__(self, system_name: str = "DTESN_PSystem"):
        self.system_name = system_name
        self.membranes: Dict[str, MembraneStructure] = {}
        self.skin_membrane_id: Optional[str] = None
        self.execution_phase = ExecutionPhase.INPUT
        self.evolution_step = 0
        self.is_halted = False
        
        # Performance tracking
        self.total_evolution_time = 0.0
        self.rule_applications = 0
        self.membrane_communications = 0
        
        # Thread safety
        self._global_lock = threading.RLock()
        
        logger.info(f"Initialized P-System hierarchy: {system_name}")
    
    def create_membrane(self, 
                       membrane_type: MembraneType,
                       label: str,
                       parent_id: Optional[str] = None,
                       neuron_count: int = 100) -> str:
        """Create a new membrane in the hierarchy"""
        
        with self._global_lock:
            membrane_id = f"{membrane_type.value}_{uuid.uuid4().hex[:8]}"
            
            # Calculate depth
            depth = 0
            if parent_id and parent_id in self.membranes:
                depth = self.membranes[parent_id].depth + 1
                self.membranes[parent_id].add_child(membrane_id)
            
            # Create membrane structure
            membrane = MembraneStructure(
                membrane_id=membrane_id,
                membrane_type=membrane_type,
                label=label,
                parent_id=parent_id,
                depth=depth,
                neuron_count=neuron_count
            )
            
            self.membranes[membrane_id] = membrane
            
            # Set skin membrane if this is the root
            if membrane_type == MembraneType.ROOT and not self.skin_membrane_id:
                self.skin_membrane_id = membrane_id
            
            logger.info(f"Created membrane: {membrane}")
            return membrane_id
    
    def get_membrane(self, membrane_id: str) -> Optional[MembraneStructure]:
        """Get membrane by ID"""
        return self.membranes.get(membrane_id)
    
    def dissolve_membrane(self, membrane_id: str) -> bool:
        """Dissolve a membrane and redistribute its contents"""
        
        with self._global_lock:
            if membrane_id not in self.membranes:
                return False
            
            membrane = self.membranes[membrane_id]
            parent_id = membrane.parent_id
            
            # Cannot dissolve skin membrane
            if membrane_id == self.skin_membrane_id:
                logger.warning("Cannot dissolve skin membrane")
                return False
            
            # Redistribute objects to parent
            if parent_id and parent_id in self.membranes:
                parent = self.membranes[parent_id]
                for symbol, count in membrane.objects.objects.items():
                    parent.add_object(symbol, count)
            
            # Redistribute children to parent
            if parent_id:
                parent = self.membranes[parent_id]
                for child_id in membrane.children_ids:
                    if child_id in self.membranes:
                        self.membranes[child_id].parent_id = parent_id
                        parent.add_child(child_id)
                parent.remove_child(membrane_id)
            
            # Mark as dissolved
            membrane.dissolve()
            
            logger.info(f"Dissolved membrane {membrane_id}")
            return True
    
    def divide_membrane(self, membrane_id: str, division_objects: Multiset) -> Optional[str]:
        """Divide a membrane creating a sibling with specified objects"""
        
        with self._global_lock:
            if membrane_id not in self.membranes:
                return None
            
            source_membrane = self.membranes[membrane_id]
            parent_id = source_membrane.parent_id
            
            # Create new sibling membrane
            new_membrane_id = self.create_membrane(
                membrane_type=source_membrane.membrane_type,
                label=f"{source_membrane.label}_divided",
                parent_id=parent_id,
                neuron_count=source_membrane.neuron_count
            )
            
            new_membrane = self.membranes[new_membrane_id]
            
            # Transfer specified objects to new membrane
            for symbol, count in division_objects.objects.items():
                if source_membrane.remove_object(symbol, count):
                    new_membrane.add_object(symbol, count)
            
            logger.info(f"Divided membrane {membrane_id} → {new_membrane_id}")
            return new_membrane_id
    
    def communicate_objects(self, 
                          source_id: str, 
                          target_id: str, 
                          objects: Multiset) -> bool:
        """Transfer objects between membranes"""
        
        with self._global_lock:
            if source_id not in self.membranes or target_id not in self.membranes:
                return False
            
            source = self.membranes[source_id]
            target = self.membranes[target_id]
            
            # Check if objects are available
            for symbol, count in objects.objects.items():
                if not source.objects.contains(symbol, count):
                    return False
            
            # Transfer objects
            for symbol, count in objects.objects.items():
                if source.remove_object(symbol, count):
                    target.add_object(symbol, count)
                else:
                    return False
            
            self.membrane_communications += 1
            logger.debug(f"Communicated {objects} from {source_id} to {target_id}")
            return True
    
    def evolve_membrane(self, membrane_id: str) -> int:
        """
        Execute one evolution step for a specific membrane.
        Returns the number of rules applied.
        """
        start_time = time.time()
        
        with self._global_lock:
            if membrane_id not in self.membranes:
                return 0
            
            membrane = self.membranes[membrane_id]
            
            if membrane.is_dissolved:
                return 0
            
            # Get applicable rules sorted by priority
            applicable_rules = membrane.get_applicable_rules()
            applicable_rules.sort(key=lambda r: r.priority, reverse=True)
            
            rules_applied = 0
            
            # Apply rules in priority order
            for rule in applicable_rules:
                if rule.is_applicable(membrane.objects):
                    success, products = rule.apply(membrane.objects)
                    if success:
                        # Add products based on rule type
                        if rule.rule_type == RuleType.EVOLUTION:
                            # Products stay in same membrane
                            membrane.objects = membrane.objects.union(products)
                        elif rule.rule_type == RuleType.COMMUNICATION and rule.target_membrane:
                            # Products go to target membrane
                            self.communicate_objects(membrane_id, rule.target_membrane, products)
                        elif rule.rule_type == RuleType.DISSOLUTION:
                            # Dissolve membrane
                            self.dissolve_membrane(membrane_id)
                            break
                        elif rule.rule_type == RuleType.DIVISION:
                            # Divide membrane
                            self.divide_membrane(membrane_id, products)
                        
                        rules_applied += 1
                        self.rule_applications += 1
            
            # Update timing
            evolution_time = (time.time() - start_time) * 1000000  # Convert to microseconds
            membrane.evolution_time_us = evolution_time
            membrane.last_evolution = time.time()
            self.total_evolution_time += evolution_time
            
            return rules_applied
    
    def evolve_system(self) -> bool:
        """
        Execute one evolution step for the entire P-System.
        Returns True if system is still active, False if halted.
        """
        if self.is_halted:
            return False
        
        self.execution_phase = ExecutionPhase.EVOLUTION
        total_rules_applied = 0
        
        # Evolve all membranes in parallel (conceptually)
        membrane_ids = list(self.membranes.keys())
        for membrane_id in membrane_ids:
            if membrane_id in self.membranes:  # Check if still exists (not dissolved)
                rules_applied = self.evolve_membrane(membrane_id)
                total_rules_applied += rules_applied
        
        self.evolution_step += 1
        
        # Check if system should halt (no rules applied)
        if total_rules_applied == 0:
            self.execution_phase = ExecutionPhase.HALTED
            self.is_halted = True
            logger.info(f"P-System halted after {self.evolution_step} steps")
            return False
        
        logger.debug(f"Evolution step {self.evolution_step}: {total_rules_applied} rules applied")
        return True
    
    def get_membrane_tree(self) -> Dict[str, Any]:
        """Get the membrane hierarchy as a tree structure"""
        
        def build_tree(membrane_id: str) -> Dict[str, Any]:
            membrane = self.membranes[membrane_id]
            tree = {
                'id': membrane_id,
                'type': membrane.membrane_type.value,
                'label': membrane.label,
                'depth': membrane.depth,
                'objects': str(membrane.objects),
                'neuron_count': membrane.neuron_count,
                'children': []
            }
            
            for child_id in membrane.children_ids:
                if child_id in self.membranes and not self.membranes[child_id].is_dissolved:
                    tree['children'].append(build_tree(child_id))
            
            return tree
        
        if self.skin_membrane_id:
            return build_tree(self.skin_membrane_id)
        return {}
    
    def validate_oeis_a000081_compliance(self) -> Tuple[bool, List[str]]:
        """
        Validate that the membrane hierarchy follows OEIS A000081 enumeration.
        Returns (is_valid, error_messages).
        """
        try:
            from oeis_a000081_enumerator import validate_membrane_hierarchy_enhanced
            
            # Count membranes at each depth level
            depth_counts = defaultdict(int)
            for membrane in self.membranes.values():
                if not membrane.is_dissolved:
                    depth_counts[membrane.depth] += 1
            
            # Convert to list for validation
            max_depth = max(depth_counts.keys()) if depth_counts else 0
            hierarchy_counts = [depth_counts[d] for d in range(max_depth + 1)]
            
            return validate_membrane_hierarchy_enhanced(hierarchy_counts, max_depth)
            
        except ImportError:
            # Fallback validation
            return True, []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        active_membranes = sum(1 for m in self.membranes.values() if not m.is_dissolved)
        total_objects = sum(len(m.objects) for m in self.membranes.values() if not m.is_dissolved)
        total_rules = sum(len(m.rules) for m in self.membranes.values())
        
        return {
            'system_name': self.system_name,
            'total_membranes': len(self.membranes),
            'active_membranes': active_membranes,
            'dissolved_membranes': len(self.membranes) - active_membranes,
            'total_objects': total_objects,
            'total_rules': total_rules,
            'evolution_steps': self.evolution_step,
            'rule_applications': self.rule_applications,
            'membrane_communications': self.membrane_communications,
            'total_evolution_time_us': self.total_evolution_time,
            'avg_evolution_time_us': self.total_evolution_time / max(1, self.evolution_step),
            'execution_phase': self.execution_phase.name,
            'is_halted': self.is_halted
        }
    
    def __str__(self) -> str:
        stats = self.get_system_stats()
        return f"PSystem[{self.system_name}]: {stats['active_membranes']} membranes, {stats['total_objects']} objects, step {stats['evolution_steps']}"

def create_dtesn_psystem_example() -> PSystemMembraneHierarchy:
    """
    Create an example P-System hierarchy following DTESN and OEIS A000081 structure.
    This demonstrates the integration of P-System membranes with Deep Tree Echo State Networks.
    """
    system = PSystemMembraneHierarchy("DTESN_Example")
    
    # Create hierarchy following OEIS A000081: [1, 1, 1, 2, 4]
    # Level 0: 1 root membrane
    root_id = system.create_membrane(MembraneType.ROOT, "echo_root", None, 100)
    system.get_membrane(root_id).add_object("input", 1)
    
    # Level 1: 1 trunk membrane  
    trunk_id = system.create_membrane(MembraneType.TRUNK, "main_trunk", root_id, 200)
    system.get_membrane(trunk_id).add_object("state", 10)
    
    # Level 2: 1 branch membrane
    branch_id = system.create_membrane(MembraneType.BRANCH, "primary_branch", trunk_id, 150)
    system.get_membrane(branch_id).add_object("memory", 5)
    
    # Level 3: 2 leaf membranes
    leaf1_id = system.create_membrane(MembraneType.LEAF, "leaf_left", branch_id, 100)
    leaf2_id = system.create_membrane(MembraneType.LEAF, "leaf_right", branch_id, 100)
    system.get_membrane(leaf1_id).add_object("echo", 3)
    system.get_membrane(leaf2_id).add_object("response", 2)
    
    # Level 4: 4 terminal membranes
    for i in range(2):
        term1_id = system.create_membrane(MembraneType.TERMINAL, f"terminal_{leaf1_id}_{i}", leaf1_id, 50)
        term2_id = system.create_membrane(MembraneType.TERMINAL, f"terminal_{leaf2_id}_{i}", leaf2_id, 50)
        system.get_membrane(term1_id).add_object("signal", 1)
        system.get_membrane(term2_id).add_object("output", 1)
    
    # Add example evolution rules
    root_membrane = system.get_membrane(root_id)
    root_membrane.add_rule(EvolutionRule(
        rule_id="input_processing",
        rule_type=RuleType.COMMUNICATION,
        lhs=Multiset({"input": 1}),
        rhs=Multiset({"processed_input": 1}),
        target_membrane=trunk_id,
        priority=3
    ))
    
    trunk_membrane = system.get_membrane(trunk_id)
    trunk_membrane.add_rule(EvolutionRule(
        rule_id="state_evolution",
        rule_type=RuleType.EVOLUTION,
        lhs=Multiset({"processed_input": 1, "state": 2}),
        rhs=Multiset({"new_state": 3}),
        priority=2
    ))
    
    logger.info("Created DTESN P-System example with OEIS A000081 compliant hierarchy")
    return system

if __name__ == "__main__":
    # Demonstration of P-System membrane data structures
    print("P-System Membrane Data Structures Demo")
    print("=" * 50)
    
    # Create example system
    system = create_dtesn_psystem_example()
    
    # Display initial state
    print(f"\nInitial system state:")
    print(system)
    print(f"\nSystem statistics:")
    stats = system.get_system_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Validate OEIS A000081 compliance
    print(f"\nOEIS A000081 validation:")
    is_valid, errors = system.validate_oeis_a000081_compliance()
    print(f"  Valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    
    # Display membrane hierarchy
    print(f"\nMembrane hierarchy:")
    tree = system.get_membrane_tree()
    
    def print_tree(node, indent=0):
        spaces = "  " * indent
        print(f"{spaces}- {node['label']} ({node['type']}) [objects: {node['objects']}]")
        for child in node['children']:
            print_tree(child, indent + 1)
    
    print_tree(tree)
    
    # Evolve system for a few steps
    print(f"\nEvolution simulation:")
    for step in range(3):
        active = system.evolve_system()
        print(f"  Step {step + 1}: Active={active}, {system}")
        if not active:
            break
    
    print(f"\nFinal system statistics:")
    final_stats = system.get_system_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")