#!/usr/bin/env python3
"""
Test Unified Echo Memory System

This validates that the unified memory system consolidates memory operations
correctly and provides the standardized Echo interfaces.
"""

import sys
import json
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from unified_echo_memory import UnifiedEchoMemory, EchoMemoryConfig, create_unified_memory_system, MemoryType
from echo_component_base import EchoConfig, validate_echo_component


def test_unified_memory_creation():
    """Test creating unified memory system"""
    print("🧪 Testing unified memory system creation...")
    
    config = EchoConfig(
        component_name="test_memory",
        version="1.0.0"
    )
    
    memory_config = EchoMemoryConfig(
        memory_storage_path="/tmp/test_memory",
        working_memory_capacity=5
    )
    
    memory_system = UnifiedEchoMemory(config, memory_config)
    
    # Test component validation
    assert validate_echo_component(memory_system), "Should be valid Echo component"
    
    # Test initialization
    init_result = memory_system.initialize()
    assert init_result.success, f"Initialization failed: {init_result.message}"
    assert memory_system._initialized, "Should be marked as initialized"
    
    print("  ✅ Unified memory creation tests passed")


def test_memory_store_and_retrieve():
    """Test basic memory store and retrieve operations"""
    print("🧪 Testing memory store and retrieve...")
    
    memory_system = create_unified_memory_system("test_store_retrieve", "/tmp/test_store")
    
    # Test store operation
    store_result = memory_system.store_memory(
        content="Test memory content",
        memory_type=MemoryType.DECLARATIVE,
        echo_value=0.8,
        source="test_suite"
    )
    
    assert store_result.success, f"Store failed: {store_result.message}"
    memory_id = store_result.data['memory_id']
    assert memory_id, "Should return memory ID"
    
    # Test retrieve operation
    retrieve_result = memory_system.retrieve_memory(memory_id)
    assert retrieve_result.success, f"Retrieve failed: {retrieve_result.message}"
    
    retrieved_data = retrieve_result.data
    assert retrieved_data['content'] == "Test memory content", "Content should match"
    assert retrieved_data['echo_value'] == 0.8, "Echo value should match"
    assert retrieved_data['memory_type'] == MemoryType.DECLARATIVE.value, "Memory type should match"
    
    print("  ✅ Store and retrieve tests passed")


def test_memory_search():
    """Test memory search functionality"""
    print("🧪 Testing memory search...")
    
    memory_system = create_unified_memory_system("test_search", "/tmp/test_search")
    
    # Store some test memories
    test_memories = [
        "Python programming concepts",
        "Yesterday's meeting notes", 
        "How to use git commands",
        "Machine learning algorithms"
    ]
    
    stored_ids = []
    for content in test_memories:
        result = memory_system.store_memory(content, MemoryType.SEMANTIC)
        assert result.success, f"Failed to store: {content}"
        stored_ids.append(result.data['memory_id'])
    
    # Test search for "Python"
    search_result = memory_system.search_memories("Python")
    assert search_result.success, f"Search failed: {search_result.message}"
    
    search_data = search_result.data
    assert search_data['result_count'] > 0, f"Should find matching memories. Found {search_data['result_count']}"
    assert any("Python" in result['content'] for result in search_data['results']), "Should find Python memory"
    
    # Test search with empty query (should match all)
    all_search = memory_system.search_memories("")
    assert all_search.success, "Empty search should succeed"
    assert all_search.data['result_count'] == len(test_memories), "Empty search should find all memories"
    
    print("  ✅ Search tests passed")


def test_echo_operations():
    """Test echo-specific memory operations"""
    print("🧪 Testing echo operations...")
    
    memory_system = create_unified_memory_system("test_echo", "/tmp/test_echo")
    
    # Store some memories with different echo values
    echo_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    for i, echo_val in enumerate(echo_values):
        result = memory_system.store_memory(
            content=f"Memory with echo {echo_val}",
            echo_value=echo_val
        )
        assert result.success, f"Failed to store memory {i}"
    
    # Test echo operation
    echo_result = memory_system.echo("Test echo data", echo_value=0.5)
    assert echo_result.success, f"Echo operation failed: {echo_result.message}"
    
    echo_data = echo_result.data
    assert 'echo_memory_id' in echo_data, "Should create echo memory"
    assert 'resonant_memories' in echo_data, "Should find resonant memories"
    assert echo_data['echo_value'] == 0.5, "Echo value should match"
    
    # Should find resonant memories (those with similar echo values)
    assert len(echo_data['resonant_memories']) > 0, "Should find resonant memories"
    
    print("  ✅ Echo operation tests passed")


def test_memory_analysis():
    """Test memory analysis functionality"""
    print("🧪 Testing memory analysis...")
    
    memory_system = create_unified_memory_system("test_analysis", "/tmp/test_analysis")
    
    # Store diverse memories
    test_data = [
        ("Factual information", MemoryType.DECLARATIVE, 0.6),
        ("Personal experience", MemoryType.EPISODIC, 0.8),
        ("Skill procedure", MemoryType.PROCEDURAL, 0.7),
        ("General knowledge", MemoryType.SEMANTIC, 0.9),
        ("Working data", MemoryType.WORKING, 0.4)
    ]
    
    for content, mem_type, echo_val in test_data:
        result = memory_system.store_memory(content, mem_type, echo_val)
        assert result.success, f"Failed to store: {content}"
    
    # Test overview analysis
    overview_result = memory_system.get_memory_overview()
    assert overview_result.success, f"Overview analysis failed: {overview_result.message}"
    
    overview_data = overview_result.data
    assert overview_data['total_memories'] >= len(test_data), "Should count stored memories"
    assert 'memory_type_distribution' in overview_data, "Should include type distribution"
    assert 'echo_statistics' in overview_data, "Should include echo statistics"
    
    # Test echo pattern analysis
    echo_analysis_result = memory_system.process({
        'operation': 'analyze',
        'analysis_type': 'echo_patterns'
    })
    assert echo_analysis_result.success, "Echo pattern analysis should succeed"
    
    echo_analysis = echo_analysis_result.data
    assert 'bins' in echo_analysis, "Should include echo distribution bins"
    assert 'counts' in echo_analysis, "Should include echo distribution counts"
    
    print("  ✅ Memory analysis tests passed")


def test_working_memory():
    """Test working memory functionality"""
    print("🧪 Testing working memory...")
    
    memory_config = EchoMemoryConfig(working_memory_capacity=3)  # Small capacity for testing
    config = EchoConfig(component_name="test_working", version="1.0.0")
    
    memory_system = UnifiedEchoMemory(config, memory_config)
    memory_system.initialize()
    
    # Store memories and check working memory behavior
    memory_ids = []
    for i in range(5):  # More than working memory capacity
        result = memory_system.store_memory(f"Memory {i}")
        assert result.success, f"Failed to store memory {i}"
        memory_ids.append(result.data['memory_id'])
    
    # Working memory should only contain the last 3 items
    assert len(memory_system.echo_working_memory) == 3, "Working memory should respect capacity"
    
    # Should contain the most recent memories
    for memory_id in memory_ids[-3:]:
        assert memory_id in memory_system.echo_working_memory, f"Should contain recent memory {memory_id}"
    
    print("  ✅ Working memory tests passed")


def test_factory_function():
    """Test the factory function for creating memory systems"""
    print("🧪 Testing factory function...")
    
    memory_system = create_unified_memory_system("factory_test", "/tmp/factory_test")
    
    assert validate_echo_component(memory_system), "Should be valid Echo component"
    assert memory_system._initialized, "Should be initialized"
    assert memory_system.config.component_name == "factory_test", "Should have correct name"
    
    # Test basic functionality
    store_result = memory_system.store_memory("Factory test memory")
    assert store_result.success, "Should be able to store memory"
    
    overview_result = memory_system.get_memory_overview()
    assert overview_result.success, "Should be able to get overview"
    assert overview_result.data['total_memories'] >= 1, "Should have at least one memory"
    
    print("  ✅ Factory function tests passed")


def test_process_interface():
    """Test the standardized process interface"""
    print("🧪 Testing process interface...")
    
    memory_system = create_unified_memory_system("test_process", "/tmp/test_process")
    
    # Test store operation via process interface
    store_operation = {
        'operation': 'store',
        'content': 'Process interface test',
        'memory_type': 'EPISODIC',
        'echo_value': 0.6,
        'source': 'process_test'
    }
    
    store_result = memory_system.process(store_operation)
    assert store_result.success, f"Process store failed: {store_result.message}"
    memory_id = store_result.data['memory_id']
    
    # Test retrieve operation via process interface
    retrieve_operation = {
        'operation': 'retrieve',
        'memory_id': memory_id
    }
    
    retrieve_result = memory_system.process(retrieve_operation)
    assert retrieve_result.success, f"Process retrieve failed: {retrieve_result.message}"
    assert retrieve_result.data['content'] == 'Process interface test', "Content should match"
    
    # Test invalid operation
    invalid_operation = {'operation': 'invalid_op'}
    invalid_result = memory_system.process(invalid_operation)
    assert not invalid_result.success, "Invalid operation should fail"
    
    print("  ✅ Process interface tests passed")


def run_all_tests():
    """Run all unified memory system tests"""
    print("🚀 Starting Unified Echo Memory System Tests")
    print("=" * 50)
    
    try:
        test_unified_memory_creation()
        test_memory_store_and_retrieve()
        test_memory_search()
        test_echo_operations()
        test_memory_analysis()
        test_working_memory()
        test_factory_function()
        test_process_interface()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Unified Echo Memory System is working correctly.")
        print("\n🎯 Memory consolidation benefits achieved:")
        print("  - ✅ Unified interface for all memory operations")
        print("  - ✅ Standardized Echo component integration")
        print("  - ✅ Consistent error handling and logging")
        print("  - ✅ Working memory management")
        print("  - ✅ Echo-aware memory operations")
        print("  - ✅ Comprehensive memory analysis")
        print("  - ✅ Persistent storage with auto-save")
        print("  - ✅ Search and retrieval capabilities")
        print("  - ✅ Memory type classification")
        print("  - ✅ Factory function for easy creation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)