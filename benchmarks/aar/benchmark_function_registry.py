"""Function registry performance benchmarks."""

import time
from typing import Dict, Any

from aphrodite.aar_core.functions.registry import FunctionRegistry


def benchmark_function_registry() -> Dict[str, Any]:
    """Benchmark function registry operations performance."""
    results = {}
    
    # Initialize function registry
    registry = FunctionRegistry()
    
    # Register test functions
    def test_function_1(a: int, b: int) -> int:
        return a + b
    
    def test_function_2(text: str) -> str:
        return text.upper()
    
    def test_function_3(data: dict) -> dict:
        return {"processed": True, "data": data}
    
    registry.register(
        test_function_1,
        name="test.add",
        description="Add two integers",
        params_schema={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]},
        safety_class="low",
        cost_unit=0.1,
        tags=["math"],
    )
    
    registry.register(
        test_function_2,
        name="test.upper",
        description="Convert text to uppercase",
        params_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        safety_class="low",
        cost_unit=0.05,
        tags=["text"],
    )
    
    registry.register(
        test_function_3,
        name="test.process",
        description="Process data dictionary",
        params_schema={"type": "object", "properties": {"data": {"type": "object"}}, "required": ["data"]},
        safety_class="low",
        cost_unit=0.2,
        tags=["data"],
    )
    
    # Benchmark: Function listing
    start_time = time.perf_counter()
    for i in range(100):
        functions = registry.list_functions()
    list_time = time.perf_counter() - start_time
    results["list_functions_100_times_ms"] = list_time * 1000
    
    # Benchmark: Function invocation
    start_time = time.perf_counter()
    for i in range(100):
        result = registry.invoke("test.add", {"a": i, "b": i + 1})
    invoke_time = time.perf_counter() - start_time
    results["invoke_add_100_times_ms"] = invoke_time * 1000
    
    # Benchmark: Function existence check
    start_time = time.perf_counter()
    for i in range(100):
        exists = registry.has("test.add")
    has_time = time.perf_counter() - start_time
    results["has_check_100_times_ms"] = has_time * 1000
    
    # Benchmark: Multiple function types
    start_time = time.perf_counter()
    for i in range(100):
        registry.invoke("test.upper", {"text": f"test_{i}"})
        registry.invoke("test.process", {"data": {"id": i}})
    multi_invoke_time = time.perf_counter() - start_time
    results["multi_invoke_100_times_ms"] = multi_invoke_time * 1000
    
    return results


if __name__ == "__main__":
    results = benchmark_function_registry()
    print("Function Registry Benchmark Results:")
    for key, value in results.items():
        print(f"  {key}: {value:.2f}")