"""
Simple test for the Echoself introspection module without dependencies
"""

from pathlib import Path
from echoself_introspection import EchoselfIntrospector

def test_basic_introspection():
    """Test basic introspection functionality"""
    
    print("Testing Echoself Introspection Module...")
    
    # Create introspector
    introspector = EchoselfIntrospector(Path.cwd())
    
    # Test cognitive snapshot
    print("\nGenerating cognitive snapshot...")
    snapshot = introspector.get_cognitive_snapshot(
        current_load=0.6,
        recent_activity=0.4
    )
    
    print(f"Files processed: {snapshot['total_files_processed']}")
    print(f"Average salience: {snapshot['average_salience']:.3f}")
    print(f"Attention threshold: {snapshot['attention_threshold']:.3f}")
    print(f"High salience files: {snapshot['high_salience_count']}")
    
    # Test prompt generation
    print("\nGenerating hypergraph prompt...")
    prompt = introspector.inject_repo_input_into_prompt(
        current_load=0.6,
        recent_activity=0.4
    )
    
    print(f"Prompt length: {len(prompt)} characters")
    print(f"Prompt preview: {prompt[:200]}...")
    
    # Test adaptive attention
    print("\nTesting adaptive attention allocation...")
    low_load_snapshot = introspector.get_cognitive_snapshot(0.2, 0.8)
    high_load_snapshot = introspector.get_cognitive_snapshot(0.8, 0.2)
    
    print(f"Low cognitive load files: {low_load_snapshot['total_files_processed']}")
    print(f"High cognitive load files: {high_load_snapshot['total_files_processed']}")
    print(f"Adaptive filtering working: {low_load_snapshot['total_files_processed'] >= high_load_snapshot['total_files_processed']}")
    
    return True

if __name__ == "__main__":
    success = test_basic_introspection()
    if success:
        print("\n✅ Basic introspection test completed successfully!")
    else:
        print("\n❌ Basic introspection test failed!")