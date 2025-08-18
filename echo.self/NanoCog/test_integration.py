#!/usr/bin/env python3
"""
NanoCog Integration Test Script

This script demonstrates the complete NanoCog optimization and evaluation pipeline,
testing hypergraph pattern generation, enhanced introspection, and evaluation metrics.
"""

import os
import sys
import tempfile
from typing import List, Dict, Any

# Add NanoCog to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_hypergraph_pattern_generation():
    """Test hypergraph pattern generation from prepare.py"""
    print("🧠 Testing hypergraph pattern generation...")
    
    try:
        from prepare import generate_hypergraph_samples
        
        samples = generate_hypergraph_samples()
        print(f"✓ Generated {len(samples)} hypergraph samples")
        
        # Show sample content
        if samples:
            sample_file, sample_content = samples[0]
            print(f"Sample pattern preview:")
            print(sample_content[:200] + "..." if len(sample_content) > 200 else sample_content)
        
        return True
    except Exception as e:
        print(f"✗ Error in hypergraph pattern generation: {e}")
        return False

def test_enhanced_introspection():
    """Test enhanced introspection capabilities"""
    print("\n🔍 Testing enhanced introspection capabilities...")
    
    try:
        from introspection.atomspace_client import AtomSpaceClient
        
        client = AtomSpaceClient("mock://localhost")
        
        # Test symbolic accuracy evaluation
        test_code = """
(ImplicationLink (stv 0.8 0.9)
  (ConceptNode "test-concept")
  (EvaluationLink (PredicateNode "test-relation") (VariableNode "$X")))

(define test-function
  (lambda (x)
    (set-sti! x 0.7)))
"""
        
        accuracy_result = client.evaluate_symbolic_accuracy(test_code)
        print(f"✓ Symbolic accuracy: {accuracy_result['syntax_accuracy']:.3f}")
        
        # Test emergent pattern detection
        generated_samples = [test_code, "(ConceptNode \"novel-concept\")"]
        corpus_samples = ["(ConceptNode \"existing-concept\")"]
        
        pattern_result = client.detect_emergent_patterns(generated_samples, corpus_samples)
        print(f"✓ Novelty rate: {pattern_result['novelty_rate']:.3f}")
        
        # Test cross-domain integration
        integration_text = "This combines attention allocation with learning and reasoning through PLN inference."
        integration_result = client.analyze_cross_domain_integration(integration_text)
        print(f"✓ Domain coverage: {integration_result['domain_coverage']:.3f}")
        
        return True
    except Exception as e:
        print(f"✗ Error in enhanced introspection: {e}")
        return False

def test_evaluation_metrics():
    """Test evaluation metrics module"""
    print("\n📊 Testing evaluation metrics...")
    
    try:
        from evaluation.metrics import NanoCogEvaluator
        
        evaluator = NanoCogEvaluator()
        
        # Test with sample generated content
        test_samples = [
            """
(ImplicationLink (stv 0.85 0.92)
  (AndLink
    (StateLink (ConceptNode "Context-human_interaction") (ConceptNode "active"))
    (EvaluationLink (PredicateNode "condition-present") 
                   (ListLink (VariableNode "$X") (ConceptNode "parameter-knowledge"))))
  (SequentialLink
    (ExecutionLink (SchemaNode "procedure-analyze") (VariableNode "$X"))
    (ExecutionLink (SchemaNode "procedure-respond") (VariableNode "$X"))
    (EvaluationLink (PredicateNode "goal-understand") (VariableNode "$X"))))
""",
            """
(AtomSpace
  (set-sti! (ConceptNode "attention-target") 0.8)
  (set-lti! (ConceptNode "memory_pattern") 0.6)
  (set-av! (SchemaNode "action_schema") (av 0.75 0.55)))
"""
        ]
        
        reference_corpus = [
            "(ConceptNode \"basic-concept\")",
            "(ImplicationLink (stv 0.9 0.8) ...)"
        ]
        
        results = evaluator.evaluate_model_generation(test_samples, reference_corpus)
        
        overall_score = results.get("overall_performance", {}).get("overall_score", 0)
        print(f"✓ Overall performance score: {overall_score:.3f}")
        
        # Generate report
        report = evaluator.generate_evaluation_report(results)
        print("✓ Evaluation report generated successfully")
        
        return True
    except Exception as e:
        print(f"✗ Error in evaluation metrics: {e}")
        return False

def test_curriculum_configuration():
    """Test curriculum learning configuration"""
    print("\n📚 Testing curriculum learning configuration...")
    
    try:
        from config.train_cogprime import (
            get_curriculum_phase,
            get_adaptive_learning_rate,
            get_data_sampling_weights,
            should_trigger_self_introspection
        )
        
        # Test curriculum phase detection
        phase_name, phase_config = get_curriculum_phase(5000, 20000)
        print(f"✓ Curriculum phase at 25%: {phase_name}")
        
        # Test adaptive learning rate
        lr = get_adaptive_learning_rate(5000, 20000, 3e-4)
        print(f"✓ Adaptive learning rate: {lr:.6f}")
        
        # Test data sampling weights
        performance_history = {
            "basic_atomese": [0.8, 0.7, 0.6],  # Declining performance
            "cognitive_primitives": [0.7, 0.8, 0.9]  # Improving performance
        }
        weights = get_data_sampling_weights(5000, 20000, performance_history)
        print(f"✓ Data sampling weights: {weights}")
        
        # Test self-introspection trigger
        should_introspect = should_trigger_self_introspection(2000)
        print(f"✓ Self-introspection trigger: {should_introspect}")
        
        return True
    except Exception as e:
        print(f"✗ Error in curriculum configuration: {e}")
        return False

def test_automated_evaluation_loop():
    """Test automated evaluation loop (single cycle)"""
    print("\n🔄 Testing automated evaluation loop...")
    
    try:
        from evaluation.automated_loop import AutomatedEvaluationLoop
        
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "evaluation": {
                    "interval_minutes": 1,
                    "sample_size": 5,
                    "performance_window": 3
                },
                "paths": {
                    "evaluation_results": tempfile.mkdtemp(),
                    "training_data": tempfile.mkdtemp(),
                    "feedback_samples": tempfile.mkdtemp()
                }
            }
            import json
            json.dump(test_config, f)
            config_path = f.name
        
        try:
            eval_loop = AutomatedEvaluationLoop(config_path)
            
            # Run single evaluation cycle
            eval_loop._run_evaluation_cycle(0)
            
            # Check status
            status = eval_loop.get_evaluation_status()
            print(f"✓ Evaluation loop test completed")
            print(f"  Evaluation count: {status['evaluation_count']}")
            
            return True
        finally:
            # Cleanup
            os.unlink(config_path)
            
    except Exception as e:
        print(f"✗ Error in automated evaluation loop: {e}")
        return False

def test_prepare_script_integration():
    """Test that prepare.py works with hypergraph injection"""
    print("\n📦 Testing prepare.py integration...")
    
    try:
        # Test that prepare.py can be imported and has required functions
        import prepare
        
        # Check that generate_hypergraph_samples exists
        assert hasattr(prepare, 'generate_hypergraph_samples'), "generate_hypergraph_samples not found"
        
        # Test function works
        samples = prepare.generate_hypergraph_samples()
        assert len(samples) > 0, "No hypergraph samples generated"
        
        print(f"✓ prepare.py integration successful")
        print(f"  Generated {len(samples)} hypergraph samples")
        
        return True
    except Exception as e:
        print(f"✗ Error in prepare.py integration: {e}")
        return False

def run_full_integration_test():
    """Run complete integration test of all components"""
    print("="*80)
    print("NANOCOG OPTIMIZATION & EVALUATION INTEGRATION TEST")
    print("="*80)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Hypergraph Pattern Generation", test_hypergraph_pattern_generation),
        ("Enhanced Introspection", test_enhanced_introspection),
        ("Evaluation Metrics", test_evaluation_metrics),
        ("Curriculum Configuration", test_curriculum_configuration),
        ("Automated Evaluation Loop", test_automated_evaluation_loop),
        ("Prepare Script Integration", test_prepare_script_integration)
    ]
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * (len(test_name) + 7))
        
        success = test_func()
        test_results.append((test_name, success))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:<8} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - NanoCog optimization pipeline is functional!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed - see details above")
        return False

if __name__ == "__main__":
    success = run_full_integration_test()
    sys.exit(0 if success else 1)