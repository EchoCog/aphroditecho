
"""
Command Analysis Tool for DTE
Parses natural language commands into executable code for recursion operations.
"""
import re
import logging
from typing import Dict, List, Union, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandAnalyzer:
    """Analyzes natural language commands and generates executable code."""
    
    def __init__(self):
        self.patterns = {
            "create_recursive_function": [
                r"create\s+(?:a\s+)?recursive\s+function\s+(?:called\s+)?(\w+)",
                r"define\s+(?:a\s+)?recursive\s+function\s+(?:named\s+)?(\w+)",
                r"make\s+(?:a\s+)?recursive\s+function\s+(?:for\s+)?(.+?)\s+(?:that|which)"
            ],
            "fibonacci": [
                r"fibonacci\s+(?:sequence|series)(?:\s+for\s+(\d+))?",
                r"calculate\s+fibonacci\s+(?:to|up to|for)\s+(\d+)",
                r"generate\s+(?:the\s+)?fibonacci\s+(?:numbers|sequence)(?:\s+for\s+(\d+))?"
            ],
            "factorial": [
                r"factorial\s+(?:of\s+)?(\d+)",
                r"calculate\s+(?:the\s+)?factorial\s+(?:of\s+)?(\d+)",
                r"compute\s+(\d+)(?:'s|\s+)factorial"
            ],
            "tree_recursion": [
                r"(?:create|make|generate)\s+(?:a\s+)?(?:recursive\s+)?tree(?:\s+with\s+depth\s+(\d+))?",
                r"tree\s+recursion(?:\s+with\s+depth\s+(\d+))?",
                r"binary\s+tree(?:\s+(?:with|of)\s+depth\s+(\d+))?"
            ],
            "backtracking": [
                r"(?:generate|create|find)\s+(?:all\s+)?(\w+)(?:\s+using\s+backtracking)?",
                r"backtracking\s+for\s+(\w+)",
                r"solve\s+(\w+)(?:\s+using\s+backtracking)?"
            ],
            "merge_function": [
                r"(?:merge|combine)\s+functions\s+(\w+)\s+and\s+(\w+)",
                r"create\s+(?:a\s+)?function\s+that\s+uses\s+both\s+(\w+)\s+and\s+(\w+)"
            ]
        }
    
    def analyze(self, command: str) -> Dict:
        """Analyze a natural language command and extract parameters."""
        command = command.lower().strip()
        logger.info(f"Analyzing command: {command}")
        
        result = {
            "command_type": None,
            "params": {},
            "matches": []
        }
        
        # Check against all patterns
        for cmd_type, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    result["command_type"] = cmd_type
                    result["matches"].append(match.groups())
                    
                    # Extract specific parameters for each command type
                    if cmd_type == "create_recursive_function":
                        result["params"]["function_name"] = match.group(1)
                    
                    elif cmd_type == "fibonacci":
                        n = match.group(1) if match.group(1) else "10"
                        result["params"]["n"] = int(n)
                    
                    elif cmd_type == "factorial":
                        result["params"]["n"] = int(match.group(1))
                    
                    elif cmd_type == "tree_recursion":
                        depth = match.group(1) if match.group(1) else "3"
                        result["params"]["depth"] = int(depth)
                    
                    elif cmd_type == "backtracking":
                        problem_type = match.group(1)
                        # Map common terms to specific problem types
                        if problem_type in ["permutation", "permutations"]:
                            result["params"]["problem_type"] = "permutations"
                        elif problem_type in ["subset", "subsets"]:
                            result["params"]["problem_type"] = "subsets"
                        elif problem_type in ["combination", "combinations"]:
                            result["params"]["problem_type"] = "combinations"
                        else:
                            result["params"]["problem_type"] = problem_type
                    
                    elif cmd_type == "merge_function":
                        result["params"]["function1"] = match.group(1)
                        result["params"]["function2"] = match.group(2)
                    
                    return result
        
        # If no pattern matched, try to infer the command
        if "fibonacci" in command:
            result["command_type"] = "fibonacci"
            result["params"]["n"] = 10
        elif "factorial" in command:
            result["command_type"] = "factorial"
            result["params"]["n"] = 5
        elif "tree" in command:
            result["command_type"] = "tree_recursion"
            result["params"]["depth"] = 3
        elif "backtrack" in command:
            result["command_type"] = "backtracking"
            result["params"]["problem_type"] = "subsets"
        
        return result
    
    def generate_code(self, analysis: Dict) -> str:
        """Generate Python code based on command analysis."""
        cmd_type = analysis.get("command_type")
        params = analysis.get("params", {})
        
        if not cmd_type:
            return "# Could not determine what type of code to generate"
        
        code = ""
        
        if cmd_type == "fibonacci":
            n = params.get("n", 10)
            code = self._generate_fibonacci_code(n)
        
        elif cmd_type == "factorial":
            n = params.get("n", 5)
            code = self._generate_factorial_code(n)
        
        elif cmd_type == "tree_recursion":
            depth = params.get("depth", 3)
            code = self._generate_tree_recursion_code(depth)
        
        elif cmd_type == "backtracking":
            problem_type = params.get("problem_type", "subsets")
            code = self._generate_backtracking_code(problem_type)
        
        elif cmd_type == "create_recursive_function":
            function_name = params.get("function_name", "recursive_function")
            code = self._generate_custom_recursive_function(function_name)
        
        elif cmd_type == "merge_function":
            function1 = params.get("function1", "func1")
            function2 = params.get("function2", "func2")
            code = self._generate_merged_functions(function1, function2)
        
        return code
    
    def _generate_fibonacci_code(self, n: int) -> str:
        """Generate Fibonacci sequence code."""
        return f"""from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first {n} terms
result = [fibonacci(i) for i in range({n})]
print("Fibonacci sequence:", result)
"""
    
    def _generate_factorial_code(self, n: int) -> str:
        """Generate factorial calculation code."""
        return f"""def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

result = factorial({n})
print(f"Factorial of {n} is:", result)
"""
    
    def _generate_tree_recursion_code(self, depth: int) -> str:
        """Generate tree recursion code."""
        return f"""def tree_recursion(depth, value):
    if depth >= {depth}:
        return [value]
    
    result = [value]
    for i in range(2):  # Binary tree (2 branches)
        child_value = value * 10 + (i + 1)
        result.extend(tree_recursion(depth + 1, child_value))
    return result

# Generate tree with depth {depth}
result = tree_recursion(0, 1)
print("Tree structure:", result)
"""
    
    def _generate_backtracking_code(self, problem_type: str) -> str:
        """Generate backtracking algorithm code based on problem type."""
        if problem_type == "permutations":
            return """def generate_permutations(nums):
    def backtrack(start):
        if start == len(nums):
            result.append(nums.copy())
            return
        
        for i in range(start, len(nums)):
            # Swap elements
            nums[start], nums[i] = nums[i], nums[start]
            # Recurse
            backtrack(start + 1)
            # Backtrack (undo the swap)
            nums[start], nums[i] = nums[i], nums[start]
    
    result = []
    backtrack(0)
    return result

# Example usage
nums = [1, 2, 3]
permutations = generate_permutations(nums)
print(f"All permutations of {nums}:", permutations)
"""
        elif problem_type == "combinations":
            return """def generate_combinations(nums, k):
    def backtrack(start, combination):
        if len(combination) == k:
            result.append(combination.copy())
            return
        
        for i in range(start, len(nums)):
            # Add element
            combination.append(nums[i])
            # Recurse
            backtrack(i + 1, combination)
            # Backtrack
            combination.pop()
    
    result = []
    backtrack(0, [])
    return result

# Example usage
nums = [1, 2, 3, 4]
k = 2
combinations = generate_combinations(nums, k)
print(f"Combinations of {k} elements from {nums}:", combinations)
"""
        else:  # Default to subsets
            return """def generate_subsets(nums):
    def backtrack(start, current):
        result.append(current.copy())
        
        for i in range(start, len(nums)):
            # Add element
            current.append(nums[i])
            # Recurse
            backtrack(i + 1, current)
            # Backtrack
            current.pop()
    
    result = []
    backtrack(0, [])
    return result

# Example usage
nums = [1, 2, 3]
subsets = generate_subsets(nums)
print(f"All subsets of {nums}:", subsets)
"""
    
    def _generate_custom_recursive_function(self, function_name: str) -> str:
        """Generate a template for a custom recursive function."""
        return f"""def {function_name}(n, *args):
    # Base case
    if n <= 0:
        return 1
    
    # Recursive case
    return n * {function_name}(n - 1, *args)

# Example usage
result = {function_name}(5)
print(f"Result of {function_name}(5):", result)
"""
    
    def _generate_merged_functions(self, function1: str, function2: str) -> str:
        """Generate code that combines two functions."""
        return f"""def {function1}(n):
    # Example implementation
    if n <= 1:
        return n
    return {function1}(n-1) + {function1}(n-2)

def {function2}(n):
    # Example implementation
    if n <= 1:
        return 1
    return n * {function2}(n-1)

def combined_{function1}_{function2}(n):
    # Use both functions together
    result1 = {function1}(n)
    result2 = {function2}(n)
    return result1 + result2

# Example usage
n = 5
result = combined_{function1}_{function2}(n)
print(f"Combined result for n={n}:", result)
"""

# Example usage
if __name__ == "__main__":
    analyzer = CommandAnalyzer()
    
    test_commands = [
        "Calculate fibonacci sequence for 10 terms",
        "Find the factorial of 5",
        "Create a recursive tree with depth 4",
        "Generate all permutations using backtracking",
        "Define a recursive function called calculate_sum",
        "Merge functions fibonacci and factorial"
    ]
    
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        analysis = analyzer.analyze(cmd)
        print(f"Analysis: {analysis}")
        
        code = analyzer.generate_code(analysis)
        print("Generated Code:")
        print(code)
