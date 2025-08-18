"""
Recursive Distinction Interpreter
Implements a computational framework based on G. Spencer-Brown's Laws of Form
and the bootstrapping of Lisp from pure parentheses structures.

This module enables the creation, manipulation, and evaluation of recursive
distinction structures that can be persisted to a database.
"""

import re
import json
import networkx as nx
from typing import Union, List, Dict, Any, Tuple, Optional, Callable
from models import RecursiveDistinction, SelfReferentialNode, NodeConnection, HyperGNN
from database import db

class DistinctionParser:
    """
    Parser for recursive parenthesis-based expressions.
    Transforms written expressions into an abstract syntax tree.
    """
    
    def __init__(self):
        self.tokens = []
        self.position = 0
    
    def tokenize(self, expression: str) -> List[str]:
        """Convert a string expression into tokens."""
        # Replace whitespace between parentheses with a special marker
        expression = re.sub(r'\s+', ' ', expression)
        # Separate parentheses and other tokens
        expression = expression.replace('(', ' ( ').replace(')', ' ) ')
        # Split by whitespace and filter out empty strings
        self.tokens = [token for token in expression.split(' ') if token]
        self.position = 0
        return self.tokens
    
    def parse(self, expression: str) -> Any:
        """Parse a string expression into a nested structure."""
        self.tokenize(expression)
        return self._parse_expression()
    
    def _parse_expression(self) -> Any:
        """Parse a complete expression recursively."""
        if self.position >= len(self.tokens):
            raise SyntaxError("Unexpected end of expression")
        
        token = self.tokens[self.position]
        self.position += 1
        
        if token == '(':
            # Start a new list
            sub_expr = []
            while self.position < len(self.tokens) and self.tokens[self.position] != ')':
                sub_expr.append(self._parse_expression())
            
            if self.position >= len(self.tokens):
                raise SyntaxError("Unmatched opening parenthesis")
            
            # Skip the closing parenthesis
            self.position += 1
            return sub_expr
        elif token == ')':
            raise SyntaxError("Unexpected closing parenthesis")
        else:
            # Convert to appropriate type
            try:
                return int(token)
            except ValueError:
                try:
                    return float(token)
                except ValueError:
                    return token


class DistinctionEvaluator:
    """
    Evaluates parsed distinction expressions according to 
    the Laws of Form and recursive calculus rules.
    """
    
    def __init__(self):
        self.env = {}  # Environment for storing variables and functions
        self._init_primitives()
    
    def _init_primitives(self):
        """Initialize primitive operations."""
        # Identity function: (()) -> ()
        self.env['identity'] = lambda x: x
        
        # Negation: (()()) -> ()
        self.env['negate'] = lambda x: not x if isinstance(x, bool) else not bool(x)
        
        # K combinator: K x y = x
        self.env['K'] = lambda x, y=None: x
        
        # S combinator: S x y z = (x z) (y z)
        self.env['S'] = lambda x, y, z: self.apply(self.apply(x, z), self.apply(y, z))
        
        # I combinator: I x = x (identity)
        self.env['I'] = lambda x: x
    
    def evaluate(self, expr: Any, env: Optional[Dict] = None) -> Any:
        """
        Evaluate a parsed expression in the given environment.
        """
        if env is None:
            env = self.env.copy()
        
        # Handle different expression types
        if isinstance(expr, list):
            if not expr:  # Empty list () represents "void" or "unmarked state"
                return None
            
            # Special forms
            first = expr[0]
            if first == 'define' or first == 'def':
                # (define symbol value)
                if len(expr) != 3:
                    raise SyntaxError(f"Invalid define expression: {expr}")
                
                symbol, value = expr[1], self.evaluate(expr[2], env)
                env[symbol] = value
                return value
            
            elif first == 'lambda' or first == 'λ':
                # (lambda (params) body)
                if len(expr) != 3:
                    raise SyntaxError(f"Invalid lambda expression: {expr}")
                
                params, body = expr[1], expr[2]
                if not isinstance(params, list):
                    params = [params]  # Single parameter
                
                # Create closure
                return lambda *args: self.evaluate(
                    body, 
                    {**env, **dict(zip(params, args))}
                )
            
            elif first == 'if':
                # (if condition then else)
                if len(expr) != 4:
                    raise SyntaxError(f"Invalid if expression: {expr}")
                
                condition = self.evaluate(expr[1], env)
                if condition:
                    return self.evaluate(expr[2], env)
                else:
                    return self.evaluate(expr[3], env)
            
            elif first == 'quote' or first == "'":
                # (quote expr) - return expr unevaluated
                if len(expr) != 2:
                    raise SyntaxError(f"Invalid quote expression: {expr}")
                
                return expr[1]
            
            else:
                # Function application
                fn = self.evaluate(first, env)
                args = [self.evaluate(arg, env) for arg in expr[1:]]
                return self.apply(fn, *args)
                
        elif isinstance(expr, str):
            # Symbol lookup
            if expr in env:
                return env[expr]
            raise NameError(f"Symbol '{expr}' not found")
            
        else:
            # Numbers, booleans, etc.
            return expr
    
    def apply(self, fn: Callable, *args) -> Any:
        """Apply a function to arguments."""
        if callable(fn):
            return fn(*args)
        raise TypeError(f"Cannot apply non-function: {fn}")


class RecursiveDistinctionManager:
    """
    Manages persistence and retrieval of recursive distinction structures.
    Connects the interpreter with the database models.
    """
    
    def __init__(self):
        self.parser = DistinctionParser()
        self.evaluator = DistinctionEvaluator()
    
    def create_distinction(self, name: str, expression: str, 
                          description: Optional[str] = None,
                          user_id: Optional[int] = None,
                          parent_id: Optional[int] = None) -> RecursiveDistinction:
        """
        Create a new recursive distinction and save it to the database.
        """
        # Parse expression to validate it
        try:
            parsed = self.parser.parse(expression)
        except SyntaxError as e:
            raise ValueError(f"Invalid expression: {e}")
        
        # Create model instance
        distinction = RecursiveDistinction(
            name=name,
            expression=expression,
            description=description,
            user_id=user_id,
            parent_id=parent_id
        )
        
        # Calculate and store metrics
        metrics = self._calculate_metrics(parsed)
        distinction.set_metrics(metrics)
        
        # Save to database
        db.session.add(distinction)
        db.session.commit()
        
        return distinction
    
    def evaluate_distinction(self, distinction_id: int) -> Any:
        """
        Evaluate a stored distinction and return the result.
        """
        distinction = RecursiveDistinction.query.get(distinction_id)
        if not distinction:
            raise ValueError(f"No distinction found with id {distinction_id}")
        
        # Parse and evaluate
        parsed = self.parser.parse(distinction.expression)
        result = self.evaluator.evaluate(parsed)
        
        return result
    
    def _calculate_metrics(self, parsed_expr: Any) -> Dict[str, Any]:
        """Calculate metrics for a parsed expression."""
        metrics = {}
        
        # Calculate depth
        def get_depth(expr):
            if not isinstance(expr, list):
                return 0
            if not expr:
                return 1  # Empty list () has depth 1
            return 1 + max([get_depth(e) for e in expr], default=0)
        
        metrics['depth'] = get_depth(parsed_expr)
        
        # Count distinctions (pairs of parentheses)
        def count_distinctions(expr):
            if not isinstance(expr, list):
                return 0
            return 1 + sum(count_distinctions(e) for e in expr)
        
        metrics['distinctions'] = count_distinctions(parsed_expr)
        
        # Estimate computational complexity
        metrics['complexity'] = metrics['depth'] * metrics['distinctions']
        
        return metrics


class HyperGNNManager:
    """
    Manages Hypergraph Neural Networks with database persistence.
    Allows syncing between memory and database representations.
    """
    
    def __init__(self):
        self.active_networks = {}  # In-memory cache of loaded networks
    
    def create_hypergnn(self, name: str, structure: Dict, 
                        weights: Optional[Dict] = None,
                        parameters: Optional[Dict] = None,
                        user_id: Optional[int] = None) -> HyperGNN:
        """
        Create a new Hypergraph Neural Network and save it to the database.
        """
        hypergnn = HyperGNN(
            name=name,
            user_id=user_id
        )
        
        hypergnn.set_structure(structure)
        
        if weights:
            hypergnn.set_weights(weights)
        
        if parameters:
            hypergnn.set_parameters(parameters)
        
        # Initialize empty loss history
        hypergnn.set_loss_history([])
        
        # Save to database
        db.session.add(hypergnn)
        db.session.commit()
        
        # Cache in memory
        self.active_networks[hypergnn.id] = {
            'structure': structure,
            'weights': weights or {},
            'parameters': parameters or {},
            'epochs': 0,
            'loss_history': []
        }
        
        return hypergnn
    
    def load_hypergnn(self, hypergnn_id: int) -> Dict:
        """
        Load a HyperGNN from the database into memory.
        """
        # Check if already in memory
        if hypergnn_id in self.active_networks:
            return self.active_networks[hypergnn_id]
        
        # Load from database
        hypergnn = HyperGNN.query.get(hypergnn_id)
        if not hypergnn:
            raise ValueError(f"No HyperGNN found with id {hypergnn_id}")
        
        # Create in-memory representation
        network = {
            'structure': hypergnn.get_structure(),
            'weights': hypergnn.get_weights(),
            'parameters': hypergnn.get_parameters(),
            'epochs': hypergnn.epochs_trained,
            'loss_history': hypergnn.get_loss_history()
        }
        
        # Cache in memory
        self.active_networks[hypergnn_id] = network
        
        return network
    
    def sync_to_db(self, hypergnn_id: int) -> None:
        """
        Sync an in-memory network to the database.
        """
        if hypergnn_id not in self.active_networks:
            raise ValueError(f"No active network with id {hypergnn_id}")
        
        network = self.active_networks[hypergnn_id]
        hypergnn = HyperGNN.query.get(hypergnn_id)
        
        if not hypergnn:
            raise ValueError(f"No HyperGNN found in database with id {hypergnn_id}")
        
        # Update database record
        hypergnn.set_structure(network['structure'])
        hypergnn.set_weights(network['weights'])
        hypergnn.set_parameters(network['parameters'])
        hypergnn.epochs_trained = network['epochs']
        hypergnn.set_loss_history(network['loss_history'])
        
        db.session.commit()
    
    def update_weights(self, hypergnn_id: int, new_weights: Dict) -> None:
        """
        Update the weights of an in-memory network.
        """
        if hypergnn_id not in self.active_networks:
            self.load_hypergnn(hypergnn_id)
        
        self.active_networks[hypergnn_id]['weights'] = new_weights
    
    def record_training(self, hypergnn_id: int, 
                        epochs: int, loss: Union[float, List[float]]) -> None:
        """
        Record training progress for a network.
        """
        if hypergnn_id not in self.active_networks:
            self.load_hypergnn(hypergnn_id)
        
        network = self.active_networks[hypergnn_id]
        
        # Update epochs
        network['epochs'] += epochs
        
        # Add loss to history
        if isinstance(loss, list):
            network['loss_history'].extend(loss)
        else:
            network['loss_history'].append(loss)


class SelfReferentialNodeManager:
    """
    Manages self-referential computational nodes with database persistence.
    Enables recursive construction of computational structures.
    """
    
    def __init__(self):
        self.parser = DistinctionParser()
        self.evaluator = DistinctionEvaluator()
    
    def create_node(self, name: str, node_type: str, 
                   expression: Optional[str] = None,
                   value: Optional[Any] = None,
                   parent_id: Optional[int] = None,
                   user_id: Optional[int] = None) -> SelfReferentialNode:
        """
        Create a self-referential node and save it to the database.
        """
        # Validate and parse expression if provided
        if expression:
            try:
                parsed = self.parser.parse(expression)
            except SyntaxError as e:
                raise ValueError(f"Invalid expression: {e}")
        
        # Serialize value if needed
        value_str = None
        if value is not None:
            if isinstance(value, (dict, list, int, float, bool, str)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
        
        # Create node
        node = SelfReferentialNode(
            name=name,
            node_type=node_type,
            expression=expression,
            value=value_str,
            parent_id=parent_id,
            user_id=user_id
        )
        
        # Save to database
        db.session.add(node)
        db.session.commit()
        
        return node
    
    def connect_nodes(self, source_id: int, target_id: int, 
                     connection_type: str = 'default',
                     weight: float = 1.0,
                     metadata: Optional[Dict] = None) -> NodeConnection:
        """
        Create a connection between two nodes.
        """
        # Verify nodes exist
        source = SelfReferentialNode.query.get(source_id)
        target = SelfReferentialNode.query.get(target_id)
        
        if not source or not target:
            missing = "source" if not source else "target"
            raise ValueError(f"No {missing} node found with provided id")
        
        # Create connection
        connection = NodeConnection(
            source_id=source_id,
            target_id=target_id,
            connection_type=connection_type,
            weight=weight
        )
        
        if metadata:
            connection.conn_data = json.dumps(metadata)
        
        # Save to database
        db.session.add(connection)
        db.session.commit()
        
        return connection
    
    def evaluate_node(self, node_id: int, args: Optional[List] = None) -> Any:
        """
        Evaluate a node's expression with optional arguments.
        """
        node = SelfReferentialNode.query.get(node_id)
        if not node:
            raise ValueError(f"No node found with id {node_id}")
        
        # If node has no expression, return its value
        if not node.expression:
            return node.get_value()
        
        # Parse expression
        parsed = self.parser.parse(node.expression)
        
        # Build environment with children's values
        env = self.evaluator.env.copy()
        
        # Add children as variables
        for child in node.children:
            env[child.name] = child.get_value()
        
        # Add connected nodes
        for conn in node.connections:
            if conn.source_id == node_id:
                env[f"_{conn.target.name}"] = conn.target.get_value()
            else:
                env[f"_{conn.source.name}"] = conn.source.get_value()
        
        # Add arguments if provided
        if args:
            env['args'] = args
        
        # Evaluate
        result = self.evaluator.evaluate(parsed, env)
        
        # Update node's value
        if isinstance(result, (dict, list, int, float, bool, str)):
            node.value = json.dumps(result)
        else:
            node.value = str(result)
        
        db.session.commit()
        
        return result
    
    def build_recursive_system(self, structure: Dict) -> int:
        """
        Build a recursive system of nodes from a structure definition.
        Returns the root node id.
        
        Structure format example:
        {
            "name": "root",
            "type": "function",
            "expression": "(lambda (x) (S identity identity x))",
            "children": [
                {
                    "name": "child1",
                    "type": "data",
                    "value": 5
                },
                {
                    "name": "child2",
                    "type": "function",
                    "expression": "(lambda (x) (* x x))"
                }
            ],
            "connections": [
                {"from": "child1", "to": "child2", "type": "input"}
            ]
        }
        """
        # Create root node
        root = self.create_node(
            name=structure["name"],
            node_type=structure["type"],
            expression=structure.get("expression"),
            value=structure.get("value")
        )
        
        # Track created nodes by name
        nodes = {structure["name"]: root}
        
        # Create children recursively
        if "children" in structure:
            for child_struct in structure["children"]:
                child = self.build_recursive_system(child_struct)
                # Update child's parent to root
                child_node = SelfReferentialNode.query.get(child)
                child_node.parent_id = root.id
                nodes[child_struct["name"]] = child_node
        
        # Create connections
        if "connections" in structure:
            for conn in structure["connections"]:
                source = nodes[conn["from"]]
                target = nodes[conn["to"]]
                self.connect_nodes(
                    source_id=source.id,
                    target_id=target.id,
                    connection_type=conn.get("type", "default"),
                    weight=conn.get("weight", 1.0),
                    metadata=conn.get("metadata")
                )
        
        db.session.commit()
        return root.id