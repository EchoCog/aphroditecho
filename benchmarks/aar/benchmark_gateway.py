"""Gateway performance benchmarks."""

import time
from typing import Dict, Any

from aphrodite.aar_core.gateway import AARGateway
from pathlib import Path


def benchmark_gateway_operations() -> Dict[str, Any]:
    """Benchmark gateway operations performance."""
    results = {}
    
    # Initialize gateway
    contracts_dir = Path("contracts")
    gateway = AARGateway(contracts_dir)
    
    # Benchmark: Register agents
    start_time = time.perf_counter()
    for i in range(100):
        gateway.register_agent({
            "id": f"agent_{i}",
            "version": "v1.0.0",
            "capabilities": ["test"],
            "tools_allow": ["test_tool"],
            "policies": ["test_policy"],
            "prompt_profile": "test_profile",
        })
    register_time = time.perf_counter() - start_time
    results["register_100_agents_ms"] = register_time * 1000
    
    # Benchmark: List agents
    start_time = time.perf_counter()
    for i in range(100):
        agents = gateway.list_agents()
    list_time = time.perf_counter() - start_time
    results["list_agents_100_times_ms"] = list_time * 1000
    results["total_agents"] = len(agents)
    
    # Benchmark: Get functions
    start_time = time.perf_counter()
    for i in range(100):
        functions = gateway.get_functions()
    functions_time = time.perf_counter() - start_time
    results["get_functions_100_times_ms"] = functions_time * 1000
    
    return results


if __name__ == "__main__":
    results = benchmark_gateway_operations()
    print("Gateway Operations Benchmark Results:")
    for key, value in results.items():
        print(f"  {key}: {value:.2f}")