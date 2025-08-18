#!/usr/bin/env python3
"""
P-System Membranes Demonstration

This script demonstrates the new P-System membrane functionality
integrated into the Deep Tree Echo system.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deep_tree_echo import DeepTreeEcho

def demonstrate_membrane_system():
    """Demonstrate P-System membrane functionality"""
    
    print("🎪 P-System Membranes Demonstration")
    print("=" * 50)
    
    # Initialize DeepTreeEcho with membranes
    print("\n1. Initializing Deep Tree Echo with P-System Membranes...")
    echo = DeepTreeEcho()
    print("   ✓ System initialized with membrane boundaries")
    
    # Show membrane status
    print("\n2. Membrane Status:")
    status = echo.get_membrane_status()
    for membrane_name, membrane_status in status.items():
        print(f"   🧬 {membrane_name}: {membrane_status['state']}, "
              f"Queue: {membrane_status['message_queue_size']}, "
              f"Children: {membrane_status['child_count']}")
    
    # Demonstrate inter-membrane communication
    print("\n3. Testing Inter-Membrane Communication...")
    
    # Cognitive membrane processes a thought
    print("   📤 Cognitive → Extension: Sending processing request...")
    success = echo.send_membrane_message(
        "cognitive", "extension", "process_thought", 
        {"thought": "Implement neural-symbolic integration", "priority": "high"}
    )
    print(f"   ✓ Message sent: {success}")
    
    # Extension responds with capability info
    print("   📤 Extension → Security: Requesting validation...")
    success = echo.send_membrane_message(
        "extension", "security", "security_check",
        {"operation": "neural_integration", "trust_level": "medium"}
    )
    print(f"   ✓ Security check requested: {success}")
    
    # Security provides validation
    print("   📤 Security → Cognitive: Validation result...")
    success = echo.send_membrane_message(
        "security", "cognitive", "validation_result",
        {"status": "approved", "restrictions": ["memory_limit=100MB"]}
    )
    print(f"   ✓ Validation sent: {success}")
    
    # Process all messages
    print("\n4. Processing Messages...")
    results = echo.process_membrane_messages()
    for membrane_name, membrane_results in results.items():
        if membrane_results:
            print(f"   🔄 {membrane_name}: Processed {len(membrane_results)} messages")
            for result in membrane_results:
                print(f"      • {result.get('status', 'processed')}")
    
    # Demonstrate extension loading
    print("\n5. Loading Extensions into Extension Membrane...")
    extensions = [
        ("neural_bridge", {"version": "2.1", "capabilities": ["symbolic_reasoning"]}),
        ("hypergraph_engine", {"version": "1.5", "capabilities": ["graph_operations"]}),
        ("memory_optimizer", {"version": "3.0", "capabilities": ["memory_management"]})
    ]
    
    for ext_name, ext_data in extensions:
        success = echo.load_extension_to_membrane(ext_name, ext_data)
        print(f"   📦 {ext_name}: {'✓ Loaded' if success else '✗ Failed'}")
    
    # Show updated status
    print("\n6. Updated Membrane Status:")
    status = echo.get_membrane_status()
    for membrane_name, membrane_status in status.items():
        resources = membrane_status.get('resources', {})
        print(f"   🧬 {membrane_name}: Memory={resources.get('memory', 0)}, "
              f"CPU={resources.get('cpu', 0)}, IO={resources.get('io', 0)}")
    
    # Demonstrate cognitive integration with existing tree functionality  
    print("\n7. Integrating with Deep Tree Echo functionality...")
    
    # Create a traditional echo tree
    root = echo.create_tree("P-System computational boundaries enable secure processing")
    print(f"   🌳 Created root node: '{root.content[:30]}...'")
    print(f"   🎵 Root echo value: {root.echo_value:.3f}")
    
    # Add child nodes
    children = [
        "Membrane isolation provides security boundaries",
        "Inter-membrane communication enables coordination", 
        "Extension membranes contain plugin functionality"
    ]
    
    for child_content in children:
        child = echo.add_child(root, child_content)
        print(f"   🌿 Child: '{child.content[:30]}...', Echo: {child.echo_value:.3f}")
    
    # Propagate echoes through the tree
    echo.propagate_echoes()
    print(f"   🔄 After propagation - Root echo: {root.echo_value:.3f}")
    
    # Send cognitive processing message about the tree
    echo.send_membrane_message(
        "cognitive", "extension", "tree_analysis",
        {
            "total_nodes": len(root.children) + 1,
            "max_echo": root.echo_value,
            "analysis": "P-System integration successful"
        }
    )
    
    # Final message processing
    final_results = echo.process_membrane_messages()
    processed_count = sum(len(results) for results in final_results.values())
    print(f"   🎯 Final processing: {processed_count} messages handled")
    
    print("\n" + "=" * 50)
    print("🎉 P-System Membranes demonstration complete!")
    print("\nKey Features Demonstrated:")
    print("• Computational boundary isolation")
    print("• Secure inter-membrane communication")
    print("• Extension loading and management")
    print("• Integration with existing Echo functionality")
    print("• Resource allocation and monitoring")

if __name__ == "__main__":
    demonstrate_membrane_system()