#!/usr/bin/env python3
"""
Test script to validate the comprehensive architecture documentation
"""

import os
import re
from pathlib import Path


def test_architecture_documentation():
    """Test that ARCHITECTURE.md exists and has proper structure"""
    arch_path = Path('ARCHITECTURE.md')
    
    if not arch_path.exists():
        print("❌ ARCHITECTURE.md file not found")
        return False
    
    with open(arch_path, 'r') as f:
        content = f.read()
    
    # Test for required sections
    required_sections = [
        '# 🏛️ EchoCog/Deep Tree Echo: Comprehensive Architecture Documentation',
        '## 🌐 High-Level System Architecture Overview',
        '## 🔄 Module Interaction and Cognitive Flow',
        '## 📡 Data and Signal Propagation Pathways',
        '## 🧠 Cognitive Architecture Deep Dive',
        '## 🔒 Multi-Layer Safety Architecture',
        '## 🌊 Adaptive Attention Allocation Mechanisms',
        '## 🌌 Cognitive Synergy Optimization Points'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing required sections in ARCHITECTURE.md: {missing_sections}")
        return False
    
    print("✅ ARCHITECTURE.md has all required sections")
    return True


def test_data_flows_documentation():
    """Test that DATA_FLOWS.md exists and has proper structure"""
    flows_path = Path('DATA_FLOWS.md')
    
    if not flows_path.exists():
        print("❌ DATA_FLOWS.md file not found")
        return False
    
    with open(flows_path, 'r') as f:
        content = f.read()
    
    # Test for required sections
    required_sections = [
        '# 🌊 EchoCog Data Flow and Signal Propagation Documentation',
        '## 🔄 Primary Cognitive Processing Flow',
        '## 🧠 Memory System Data Architecture',
        '## ⚡ Echo Propagation Signal Flow',
        '## 🔒 Safety Protocol Data Validation Flow',
        '## 🤖 AI Integration Service Communication'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing required sections in DATA_FLOWS.md: {missing_sections}")
        return False
    
    print("✅ DATA_FLOWS.md has all required sections")
    return True


def test_components_documentation():
    """Test that COMPONENTS.md exists and has proper structure"""
    comp_path = Path('COMPONENTS.md')
    
    if not comp_path.exists():
        print("❌ COMPONENTS.md file not found")
        return False
    
    with open(comp_path, 'r') as f:
        content = f.read()
    
    # Test for required sections
    required_sections = [
        '# 🧩 EchoCog Component Architecture: Detailed Module Documentation',
        '## 🧠 Cognitive Architecture Module',
        '## 🌳 Deep Tree Echo Engine',
        '## 🤖 AI Integration Layer',
        '## 🔒 Emergency Protocols and Safety System',
        '## 💬 Chat and Interaction Systems',
        '## 📊 Memory Management and Hypergraph System'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing required sections in COMPONENTS.md: {missing_sections}")
        return False
    
    print("✅ COMPONENTS.md has all required sections")
    return True


def test_documentation_index():
    """Test that DOCUMENTATION_INDEX.md exists and has proper structure"""
    index_path = Path('DOCUMENTATION_INDEX.md')
    
    if not index_path.exists():
        print("❌ DOCUMENTATION_INDEX.md file not found")
        return False
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    # Test for required sections
    required_sections = [
        '# 📚 EchoCog Architecture Documentation Index',
        '## 📖 Documentation Structure',
        '### 🏛️ [Architecture Overview](./ARCHITECTURE.md)',
        '### 🌊 [Data Flows and Signal Propagation](./DATA_FLOWS.md)',
        '### 🧩 [Component Architecture](./COMPONENTS.md)',
        '## 🎯 Quick Navigation Guide'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing required sections in DOCUMENTATION_INDEX.md: {missing_sections}")
        return False
    
    print("✅ DOCUMENTATION_INDEX.md has all required sections")
    return True


def test_mermaid_diagrams_comprehensive():
    """Test that all documentation files contain properly formatted Mermaid diagrams"""
    doc_files = ['ARCHITECTURE.md', 'DATA_FLOWS.md', 'COMPONENTS.md']
    total_diagrams = 0
    
    for doc_file in doc_files:
        if not Path(doc_file).exists():
            print(f"❌ {doc_file} not found")
            return False
        
        with open(doc_file, 'r') as f:
            content = f.read()
        
        # Check for Mermaid code blocks
        mermaid_pattern = r'```mermaid\n(.*?)\n```'
        mermaid_blocks = re.findall(mermaid_pattern, content, re.DOTALL)
        
        if not mermaid_blocks:
            print(f"❌ No Mermaid diagrams found in {doc_file}")
            return False
        
        # Validate basic Mermaid syntax
        for i, block in enumerate(mermaid_blocks):
            if not any(diagram_type in block for diagram_type in ['graph TD', 'graph LR', 'sequenceDiagram', 'stateDiagram']):
                print(f"❌ {doc_file} Mermaid block {i+1} missing valid diagram declaration")
                return False
            
            # Check for basic node connections or sequence elements
            if '-->' not in block and '->>' not in block and '-->>' not in block:
                print(f"❌ {doc_file} Mermaid block {i+1} missing connections")
                return False
        
        total_diagrams += len(mermaid_blocks)
        print(f"✅ {doc_file}: Found {len(mermaid_blocks)} properly formatted Mermaid diagram(s)")
    
    print(f"✅ Total Mermaid diagrams across all documentation: {total_diagrams}")
    return True


def test_neural_symbolic_coverage():
    """Test that neural-symbolic terminology is comprehensively covered"""
    doc_files = ['ARCHITECTURE.md', 'DATA_FLOWS.md', 'COMPONENTS.md']
    
    neural_symbolic_terms = [
        'neural-symbolic',
        'cognitive architecture',
        'recursive',
        'hypergraph',
        'echo propagation',
        'attention allocation',
        'emergent',
        'adaptive',
        'feedback loop',
        'self-improvement'
    ]
    
    for doc_file in doc_files:
        if not Path(doc_file).exists():
            continue
        
        with open(doc_file, 'r') as f:
            content = f.read().lower()
        
        found_terms = []
        for term in neural_symbolic_terms:
            if term.lower() in content:
                found_terms.append(term)
        
        coverage_ratio = len(found_terms) / len(neural_symbolic_terms)
        if coverage_ratio < 0.7:  # At least 70% coverage
            print(f"❌ {doc_file}: Insufficient neural-symbolic terminology coverage ({coverage_ratio:.2%})")
            return False
        
        print(f"✅ {doc_file}: Good neural-symbolic terminology coverage ({coverage_ratio:.2%})")
    
    return True


def test_diagram_type_diversity():
    """Test that different types of Mermaid diagrams are used appropriately"""
    doc_files = ['ARCHITECTURE.md', 'DATA_FLOWS.md', 'COMPONENTS.md']
    diagram_types_found = set()
    
    for doc_file in doc_files:
        if not Path(doc_file).exists():
            continue
        
        with open(doc_file, 'r') as f:
            content = f.read()
        
        # Check for different diagram types
        if 'graph TD' in content:
            diagram_types_found.add('graph TD')
        if 'graph LR' in content:
            diagram_types_found.add('graph LR')
        if 'sequenceDiagram' in content:
            diagram_types_found.add('sequenceDiagram')
        if 'stateDiagram' in content:
            diagram_types_found.add('stateDiagram')
    
    expected_types = {'graph TD', 'graph LR', 'sequenceDiagram', 'stateDiagram'}
    missing_types = expected_types - diagram_types_found
    
    if missing_types:
        print(f"❌ Missing diagram types: {missing_types}")
        return False
    
    print(f"✅ All expected diagram types found: {diagram_types_found}")
    return True


def test_cross_references():
    """Test that documentation files properly cross-reference each other"""
    index_path = Path('DOCUMENTATION_INDEX.md')
    
    if not index_path.exists():
        print("❌ DOCUMENTATION_INDEX.md not found for cross-reference testing")
        return False
    
    with open(index_path, 'r') as f:
        index_content = f.read()
    
    # Check for proper markdown links
    expected_links = [
        './ARCHITECTURE.md',
        './DATA_FLOWS.md',
        './COMPONENTS.md'
    ]
    
    missing_links = []
    for link in expected_links:
        if link not in index_content:
            missing_links.append(link)
    
    if missing_links:
        print(f"❌ Missing cross-references in index: {missing_links}")
        return False
    
    print("✅ All cross-references properly established")
    return True


def main():
    """Run all tests for the comprehensive architecture documentation"""
    print("🧪 Testing comprehensive architecture documentation...")
    print("=" * 70)
    
    tests = [
        ("Architecture Documentation", test_architecture_documentation),
        ("Data Flows Documentation", test_data_flows_documentation),
        ("Components Documentation", test_components_documentation),
        ("Documentation Index", test_documentation_index),
        ("Mermaid Diagrams Comprehensive", test_mermaid_diagrams_comprehensive),
        ("Neural-Symbolic Coverage", test_neural_symbolic_coverage),
        ("Diagram Type Diversity", test_diagram_type_diversity),
        ("Cross-References", test_cross_references)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"💥 {test_name} test error: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Comprehensive architecture documentation is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    main()