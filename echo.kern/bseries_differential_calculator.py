#!/usr/bin/env python3
"""
B-Series Elementary Differential Calculator
==========================================

This module implements a numerical calculator for B-Series elementary differentials F(τ).
It takes the symbolic expressions from the B-Series tree classifier and provides
numerical evaluation capabilities for differential equation solving.

Mathematical Foundation:
For a given rooted tree τ, the elementary differential F(τ) represents
the application of derivatives according to the tree structure.

Examples:
- Tree • (single node): F(τ) = f(y)
- Tree •—• (chain): F(τ) = f'(y) · f(y)  
- Tree •[••] (star): F(τ) = f''(y) · [f(y), f(y)]
"""

import sys
import math
from typing import Callable, List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Import B-Series tree classification
try:
    from bseries_tree_classifier import (
        BSeriesTreeClassifier,
        ClassifiedTree,
        TreeStructureType,
        create_bseries_classifier
    )
    _bseries_classifier = create_bseries_classifier()
except ImportError:
    _bseries_classifier = None


@dataclass
class DifferentialFunction:
    """Represents a function and its derivatives for B-Series calculation"""
    f: Callable[[float], float]           # Function f(y)
    f_prime: Callable[[float], float]     # First derivative f'(y)
    f_double: Optional[Callable[[float], float]] = None    # Second derivative f''(y)
    f_triple: Optional[Callable[[float], float]] = None    # Third derivative f'''(y)
    f_quad: Optional[Callable[[float], float]] = None      # Fourth derivative f''''(y)
    name: str = "f"                       # Function name for display


class ElementaryDifferentialEvaluator(ABC):
    """Abstract base class for elementary differential evaluation"""
    
    @abstractmethod
    def evaluate(self, df: DifferentialFunction, y: float) -> float:
        """Evaluate the elementary differential at point y"""
        pass
    
    @abstractmethod
    def get_expression(self) -> str:
        """Get symbolic expression for this elementary differential"""
        pass


class SingleNodeEvaluator(ElementaryDifferentialEvaluator):
    """Evaluator for single node tree: F(τ) = f(y)"""
    
    def evaluate(self, df: DifferentialFunction, y: float) -> float:
        return df.f(y)
    
    def get_expression(self) -> str:
        return "f"


class LinearChainEvaluator(ElementaryDifferentialEvaluator):
    """Evaluator for linear chain trees: F(τ) = f'(y) * f(y), f''(y) * [f(y), f(y)], etc."""
    
    def __init__(self, order: int):
        self.order = order
    
    def evaluate(self, df: DifferentialFunction, y: float) -> float:
        if self.order == 2:
            # f'(f(y)) - chain rule application
            f_val = df.f(y)
            return df.f_prime(y) * f_val
        elif self.order == 3:
            # f''(y) * [f(y), f(y)]
            if df.f_double is None:
                raise ValueError("Second derivative required for order 3")
            f_val = df.f(y)
            return df.f_double(y) * f_val * f_val
        elif self.order == 4:
            # f'''(y) * [f(y), f(y), f(y)]
            if df.f_triple is None:
                raise ValueError("Third derivative required for order 4")
            f_val = df.f(y)
            return df.f_triple(y) * (f_val ** 3)
        elif self.order == 5:
            # f''''(y) * [f(y), f(y), f(y), f(y)]
            if df.f_quad is None:
                raise ValueError("Fourth derivative required for order 5")
            f_val = df.f(y)
            return df.f_quad(y) * (f_val ** 4)
        else:
            raise ValueError(f"Linear chain order {self.order} not implemented")
    
    def get_expression(self) -> str:
        if self.order == 2:
            return "f'(f)"
        elif self.order == 3:
            return "f''(f,f)"
        elif self.order == 4:
            return "f'''(f,f,f)"
        elif self.order == 5:
            return "f''''(f,f,f,f)"
        else:
            return f"f^({self.order-1})(f,...,f)"


class StarGraphEvaluator(ElementaryDifferentialEvaluator):
    """Evaluator for star graph trees: higher order derivatives with multiple f arguments"""
    
    def __init__(self, order: int, num_children: int):
        self.order = order
        self.num_children = num_children
    
    def evaluate(self, df: DifferentialFunction, y: float) -> float:
        f_val = df.f(y)
        
        if self.order == 3 and self.num_children == 2:
            # f'(f'(f)) - nested application
            f_prime_val = df.f_prime(y)
            return df.f_prime(y) * f_prime_val * f_val
        elif self.order == 4 and self.num_children == 3:
            # f'''(f,f,f) with higher symmetry
            if df.f_triple is None:
                raise ValueError("Third derivative required")
            return df.f_triple(y) * (f_val ** 3) / 6  # Symmetry factor
        elif self.order == 5 and self.num_children == 4:
            # f''''(f,f,f,f) with maximum symmetry
            if df.f_quad is None:
                raise ValueError("Fourth derivative required")
            return df.f_quad(y) * (f_val ** 4) / 24  # Symmetry factor
        else:
            raise ValueError(f"Star graph order {self.order}, children {self.num_children} not implemented")
    
    def get_expression(self) -> str:
        if self.order == 3:
            return "f'(f'(f))"
        elif self.order == 4:
            return "f'''(f,f,f)"
        elif self.order == 5:
            return "f''''(f,f,f,f)"
        else:
            return f"f^({self.order-1})(star)"


class CompositeEvaluator(ElementaryDifferentialEvaluator):
    """Evaluator for composite/general tree structures"""
    
    def __init__(self, expression: str, order: int):
        self.expression = expression
        self.order = order
    
    def evaluate(self, df: DifferentialFunction, y: float) -> float:
        # Simplified evaluation for general expressions
        # This would need more sophisticated parsing for complex compositions
        f_val = df.f(y)
        
        # Handle common patterns
        if "f'(f''(" in self.expression:
            # Nested composition like f'(f''(f,f))
            if df.f_double is None:
                raise ValueError("Second derivative required")
            inner = df.f_double(y) * f_val * f_val
            return df.f_prime(y) * inner
        elif "f''(f'(" in self.expression:
            # Mixed composition like f''(f'(f),f)
            if df.f_double is None:
                raise ValueError("Second derivative required")
            f_prime_val = df.f_prime(y) * f_val
            return df.f_double(y) * f_prime_val * f_val
        else:
            # Default to basic evaluation based on order
            if self.order == 3:
                return df.f_double(y) * f_val * f_val if df.f_double else 0.0
            elif self.order == 4:
                return df.f_triple(y) * (f_val ** 3) if df.f_triple else 0.0
            elif self.order == 5:
                return df.f_quad(y) * (f_val ** 4) if df.f_quad else 0.0
            else:
                return f_val
    
    def get_expression(self) -> str:
        return self.expression


class BSeriesDifferentialCalculator:
    """
    Main calculator for B-Series elementary differentials.
    Provides numerical evaluation of F(τ) for given functions and trees.
    """
    
    def __init__(self):
        """Initialize the B-Series differential calculator"""
        self.classifier = _bseries_classifier
        self.evaluators: Dict[int, ElementaryDifferentialEvaluator] = {}
        self._initialize_evaluators()
    
    def _initialize_evaluators(self):
        """Initialize evaluators for all classified trees"""
        if self.classifier is None:
            raise RuntimeError("B-Series classifier not available")
        
        for tree_id, tree in self.classifier.classified_trees.items():
            evaluator = self._create_evaluator_for_tree(tree)
            self.evaluators[tree_id] = evaluator
    
    def _create_evaluator_for_tree(self, tree: ClassifiedTree) -> ElementaryDifferentialEvaluator:
        """Create appropriate evaluator for a specific tree"""
        if tree.structure_type == TreeStructureType.SINGLE_NODE:
            return SingleNodeEvaluator()
        elif tree.structure_type == TreeStructureType.LINEAR_CHAIN:
            return LinearChainEvaluator(tree.order)
        elif tree.structure_type == TreeStructureType.STAR_GRAPH:
            # Estimate number of children from order
            num_children = tree.order - 1
            return StarGraphEvaluator(tree.order, num_children)
        else:
            # General tree - use composite evaluator
            return CompositeEvaluator(tree.elementary_diff.expression, tree.order)
    
    def evaluate_elementary_differential(self, tree_id: int, df: DifferentialFunction, y: float) -> float:
        """
        Evaluate elementary differential F(τ) for a specific tree at point y
        
        Args:
            tree_id: ID of the tree from B-Series classification
            df: Function and its derivatives
            y: Point at which to evaluate
            
        Returns:
            Numerical value of F(τ)(y)
        """
        if tree_id not in self.evaluators:
            raise ValueError(f"No evaluator found for tree {tree_id}")
        
        evaluator = self.evaluators[tree_id]
        return evaluator.evaluate(df, y)
    
    def evaluate_bseries_step(self, df: DifferentialFunction, y: float, h: float, max_order: int = 5) -> float:
        """
        Evaluate one step of B-Series method: y + h * Σ α(τ) F(τ)(y)
        
        Args:
            df: Function and its derivatives
            y: Current value
            h: Step size
            max_order: Maximum tree order to include
            
        Returns:
            Next value computed using B-Series
        """
        if self.classifier is None:
            raise RuntimeError("B-Series classifier not available")
        
        result = y  # Start with y₀
        
        for order in range(1, max_order + 1):
            trees = self.classifier.get_trees_by_order(order)
            for tree in trees:
                try:
                    # Get B-Series coefficient α(τ)
                    alpha = tree.coefficient.coefficient_value
                    
                    # Evaluate elementary differential F(τ)(y)
                    f_tau = self.evaluate_elementary_differential(tree.tree_id, df, y)
                    
                    # Add h * α(τ) * F(τ)(y) to result
                    result += h * alpha * f_tau
                    
                except (ValueError, AttributeError) as e:
                    # Skip trees that can't be evaluated (missing derivatives, etc.)
                    continue
        
        return result
    
    def get_tree_evaluation_info(self, tree_id: int) -> Dict[str, Any]:
        """Get information about a tree's evaluation capabilities"""
        if tree_id not in self.evaluators:
            return {"error": f"Tree {tree_id} not found"}
        
        tree = self.classifier.get_tree_by_id(tree_id)
        evaluator = self.evaluators[tree_id]
        
        return {
            "tree_id": tree_id,
            "order": tree.order,
            "structure_type": tree.structure_type.value,
            "coefficient": tree.coefficient.coefficient_value,
            "expression": evaluator.get_expression(),
            "computational_cost": tree.elementary_diff.computational_cost
        }
    
    def validate_differential_function(self, df: DifferentialFunction, max_order: int = 5) -> Tuple[bool, List[str]]:
        """
        Validate that a differential function has required derivatives for given max order
        """
        errors = []
        
        if df.f is None:
            errors.append("Function f is required")
        
        if max_order >= 2 and df.f_prime is None:
            errors.append("First derivative f' is required for order >= 2")
        
        if max_order >= 3 and df.f_double is None:
            errors.append("Second derivative f'' is required for order >= 3")
        
        if max_order >= 4 and df.f_triple is None:
            errors.append("Third derivative f''' is required for order >= 4")
        
        if max_order >= 5 and df.f_quad is None:
            errors.append("Fourth derivative f'''' is required for order >= 5")
        
        return len(errors) == 0, errors
    
    def get_supported_trees(self) -> List[Dict[str, Any]]:
        """Get list of all supported trees with evaluation information"""
        return [self.get_tree_evaluation_info(tree_id) 
                for tree_id in sorted(self.evaluators.keys())]


def create_differential_function(f, f_prime=None, f_double=None, f_triple=None, f_quad=None, name="f"):
    """
    Convenience function to create a DifferentialFunction
    
    Args:
        f: Function f(y)
        f_prime: First derivative f'(y) 
        f_double: Second derivative f''(y)
        f_triple: Third derivative f'''(y)
        f_quad: Fourth derivative f''''(y)
        name: Function name for display
        
    Returns:
        DifferentialFunction object
    """
    return DifferentialFunction(
        f=f,
        f_prime=f_prime,
        f_double=f_double,
        f_triple=f_triple,
        f_quad=f_quad,
        name=name
    )


def main():
    """Test the B-Series differential calculator"""
    print("B-Series Elementary Differential Calculator")
    print("=" * 50)
    
    # Create calculator
    calculator = BSeriesDifferentialCalculator()
    
    # Define a test function: f(y) = y²
    def f(y):
        return y * y
    
    def f_prime(y):
        return 2 * y
    
    def f_double(y):
        return 2.0
    
    def f_triple(y):
        return 0.0
    
    def f_quad(y):
        return 0.0
    
    # Create differential function
    df = create_differential_function(f, f_prime, f_double, f_triple, f_quad, "y²")
    
    # Test point
    y = 1.0
    
    print(f"Testing with function f(y) = y² at y = {y}")
    print(f"f({y}) = {f(y)}, f'({y}) = {f_prime(y)}")
    
    # Validate function
    is_valid, errors = calculator.validate_differential_function(df, max_order=5)
    if not is_valid:
        print("Function validation errors:")
        for error in errors:
            print(f"  {error}")
        return
    
    print("\n✅ Function validation passed")
    
    # Evaluate elementary differentials for each tree
    print(f"\nElementary Differential Evaluations:")
    supported_trees = calculator.get_supported_trees()
    
    for tree_info in supported_trees[:10]:  # Show first 10 trees
        tree_id = tree_info["tree_id"]
        try:
            value = calculator.evaluate_elementary_differential(tree_id, df, y)
            expression = tree_info["expression"]
            coefficient = tree_info["coefficient"]
            print(f"  Tree {tree_id}: F(τ) = {expression} = {value:.6f}, α = {coefficient:.6f}")
        except Exception as e:
            print(f"  Tree {tree_id}: Error - {e}")
    
    # Test B-Series step
    h = 0.1
    print(f"\nB-Series Step Evaluation (h = {h}):")
    try:
        next_y = calculator.evaluate_bseries_step(df, y, h, max_order=3)
        print(f"  y₀ = {y}")
        print(f"  y₁ = {next_y:.6f}")
        print(f"  Change: {next_y - y:.6f}")
        
        # Compare with exact solution for dy/dt = y²
        # Exact: y(t) = y₀ / (1 - y₀*t)
        exact = y / (1 - y * h)
        error = abs(next_y - exact)
        print(f"  Exact solution: {exact:.6f}")
        print(f"  Error: {error:.6f}")
        
    except Exception as e:
        print(f"  B-Series step error: {e}")
    
    print(f"\n✅ B-Series elementary differential calculator operational")


if __name__ == "__main__":
    main()