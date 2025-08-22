"""Memory subsystem performance benchmarks."""

import time
from typing import Dict, Any

from aphrodite.aar_core.memory import MemoryManager, MemoryType


def benchmark_memory_operations() -> Dict[str, Any]:
    """Benchmark memory operations performance."""
    results = {}
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Benchmark: Add memory records
    start_time = time.perf_counter()
    for i in range(1000):
        memory_manager.add_memory(
            content=f"Test memory content {i}",
            memory_type=MemoryType.WORKING,
            tags=[f"tag_{i % 10}"],
        )
    add_time = time.perf_counter() - start_time
    results["add_1000_records_ms"] = add_time * 1000
    
    # Benchmark: Query memory
    start_time = time.perf_counter()
    for i in range(100):
        memory_manager.query_memory(
            query=f"test {i}",
            limit=10,
        )
    query_time = time.perf_counter() - start_time
    results["query_100_times_ms"] = query_time * 1000
    
    # Benchmark: Get working memory
    start_time = time.perf_counter()
    for i in range(100):
        memory_manager.get_working_memory(limit=100)
    working_time = time.perf_counter() - start_time
    results["get_working_memory_100_times_ms"] = working_time * 1000
    
    # Benchmark: Cleanup expired
    start_time = time.perf_counter()
    cleanup_count = memory_manager.cleanup_expired()
    cleanup_time = time.perf_counter() - start_time
    results["cleanup_expired_ms"] = cleanup_time * 1000
    results["cleanup_count"] = cleanup_count
    
    # Get memory stats
    stats = memory_manager.get_memory_stats()
    results["final_stats"] = stats
    
    return results


if __name__ == "__main__":
    results = benchmark_memory_operations()
    print("Memory Operations Benchmark Results:")
    for key, value in results.items():
        if key != "final_stats":
            print(f"  {key}: {value:.2f}")
    print(f"  Final Stats: {results['final_stats']}")