"""
Simple integration test for the Echoself recursive introspection in DeepTreeEcho
"""

import sys
from pathlib import Path
import pytest

# Try importing deep_tree_echo, skip tests if not available
try:
    from deep_tree_echo import DeepTreeEcho
    DEEP_TREE_AVAILABLE = True
except ImportError:
    DEEP_TREE_AVAILABLE = False
    DeepTreeEcho = None

@pytest.mark.skipif(not DEEP_TREE_AVAILABLE, reason="deep_tree_echo not available")
def test_integration():
    """Test the integration of recursive introspection with DeepTreeEcho"""
    
    print("Testing Echoself Recursive Introspection Integration...")
    
    # Create DeepTreeEcho instance
    echo_system = DeepTreeEcho(echo_threshold=0.7)
    
    # Create initial tree
    initial_content = "Testing recursive self-model integration and neural-symbolic synergy"
    root_node = echo_system.create_tree(initial_content)
    print(f"Created initial tree with root: {root_node.content}")
    
    # Perform recursive introspection
    print("\nPerforming recursive introspection...")
    introspection_results = echo_system.perform_recursive_introspection(
        repository_root=Path.cwd(),
        current_load=0.6,
        recent_activity=0.4
    )
    
    # Display results
    if 'error' in introspection_results:
        print(f"Error during introspection: {introspection_results['error']}")
        return False
    
    print("\nIntrospection Results:")
    print(f"- Files processed: {introspection_results['cognitive_snapshot']['total_files_processed']}")
    print(f"- Average salience: {introspection_results['cognitive_snapshot']['average_salience']:.3f}")
    print(f"- Attention threshold: {introspection_results['cognitive_snapshot']['attention_threshold']:.3f}")
    print(f"- High salience files: {introspection_results['cognitive_snapshot']['high_salience_count']}")
    
    if introspection_results['echo_integration']:
        print(f"- Echo integration successful with value: {introspection_results['echo_integration']['echo_value']:.3f}")
        
    print(f"\nHypergraph prompt preview:\n{introspection_results['hypergraph_prompt'][:300]}...")
    
    # Analyze echo patterns after introspection
    echo_analysis = echo_system.analyze_echo_patterns()
    print(f"\nEcho Analysis after introspection:")
    print(f"- Total nodes: {echo_analysis['total_nodes']}")
    print(f"- Resonant nodes: {echo_analysis['resonant_nodes']}")
    print(f"- Average echo: {echo_analysis['avg_echo']:.3f}")
    print(f"- Max echo: {echo_analysis['max_echo']:.3f}")
    
    return True

if __name__ == "__main__":
    if DEEP_TREE_AVAILABLE:
        success = test_integration()
        if success:
            print("\n✅ Integration test completed successfully!")
        else:
            print("\n❌ Integration test failed!")
            sys.exit(1)
    else:
        print("Skipping integration test - deep_tree_echo not available")