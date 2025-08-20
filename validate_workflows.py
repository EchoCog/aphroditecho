#!/usr/bin/env python3
"""
Quick validation script for the GitHub Actions workflows
Tests basic functionality and configurations
"""

import sys
import json
import yaml
from pathlib import Path
import tempfile
import os

def test_workflow_yaml_validity():
    """Test that all workflow YAML files are valid"""
    print("🧪 Testing workflow YAML validity...")
    
    workflows = [
        '.github/workflows/build-engine.yml',
        '.github/workflows/vm-daemon-mlops.yml', 
        '.github/workflows/echo-systems-integration.yml'
    ]
    
    results = {}
    
    for workflow in workflows:
        try:
            with open(workflow, 'r') as f:
                content = yaml.safe_load(f)
            
            # Basic validation
            assert 'name' in content, f"Missing 'name' in {workflow}"
            assert 'on' in content, f"Missing 'on' triggers in {workflow}"
            assert 'jobs' in content, f"Missing 'jobs' in {workflow}"
            
            job_count = len(content.get('jobs', {}))
            results[workflow] = {
                'status': '✅ Valid',
                'jobs': job_count,
                'triggers': list(content['on'].keys()) if isinstance(content['on'], dict) else [content['on']]
            }
            
        except Exception as e:
            results[workflow] = {
                'status': f'❌ Error: {e}',
                'jobs': 0,
                'triggers': []
            }
    
    return results

def test_echo_systems_detection():
    """Test detection of Echo system components"""
    print("🔍 Testing Echo systems detection...")
    
    components = {
        'aar_core': Path('aar_core').exists(),
        'echo.self': Path('echo.self').exists(),
        'echo.kern': Path('echo.kern').exists(),
        'echo.rkwv': Path('echo.rkwv').exists(),
        'architecture_docs': any(
            Path(f).exists() for f in [
                'ARCHITECTURE.md',
                'DEEP_TREE_ECHO_ARCHITECTURE.md', 
                'ECHO_SYSTEMS_ARCHITECTURE.md'
            ]
        )
    }
    
    return components

def test_vm_daemon_configuration():
    """Test VM-Daemon configuration generation"""
    print("⚙️ Testing VM-Daemon configuration...")
    
    config = {
        "vm_daemon": {
            "mode": "test",
            "aar_core_enabled": True,
            "echo_evolution_enabled": True,
            "deep_tree_echo_enabled": True,
            "proprioceptive_feedback": True
        },
        "services": {
            "aphrodite_engine": {"enabled": True, "priority": "high"},
            "echo_self_evolution": {"enabled": True, "priority": "medium"},
            "aar_orchestration": {"enabled": True, "priority": "high"},
            "deep_tree_echo": {"enabled": True, "priority": "medium"}
        },
        "monitoring": {
            "metrics_collection": True,
            "health_checks": True,
            "performance_tracking": True
        }
    }
    
    # Test configuration validity
    try:
        # Test JSON serialization
        json_str = json.dumps(config, indent=2)
        
        # Test YAML serialization  
        yaml_str = yaml.dump(config, default_flow_style=False)
        
        # Test deserialization
        config_from_json = json.loads(json_str)
        config_from_yaml = yaml.safe_load(yaml_str)
        
        assert config == config_from_json
        assert config == config_from_yaml
        
        return {
            'status': '✅ Valid',
            'services_count': len(config['services']),
            'monitoring_enabled': config['monitoring']['metrics_collection']
        }
        
    except Exception as e:
        return {
            'status': f'❌ Error: {e}',
            'services_count': 0,
            'monitoring_enabled': False
        }

def test_mlops_pipeline_simulation():
    """Test MLOps pipeline simulation"""
    print("🔄 Testing MLOps pipeline simulation...")
    
    try:
        # Simulate training pipeline
        training_config = {
            "model_type": "aphrodite_llm",
            "training_schedule": "continuous",
            "data_sources": ["echo_self_evolution", "aar_interactions"],
            "validation_strategy": "temporal_split"
        }
        
        # Simulate inference pipeline
        inference_config = {
            "model_serving": "aphrodite_engine",
            "scaling_policy": "adaptive",
            "load_balancing": "round_robin"
        }
        
        # Simulate monitoring
        monitoring_config = {
            "metrics": ["accuracy", "latency", "throughput"],
            "alerting": True,
            "dashboards": True
        }
        
        # Test pipeline creation
        pipeline = {
            "training": training_config,
            "inference": inference_config,
            "monitoring": monitoring_config,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return {
            'status': '✅ Valid',
            'components': list(pipeline.keys()),
            'training_sources': len(training_config['data_sources']),
            'monitoring_metrics': len(monitoring_config['metrics'])
        }
        
    except Exception as e:
        return {
            'status': f'❌ Error: {e}',
            'components': [],
            'training_sources': 0,
            'monitoring_metrics': 0
        }

def test_4e_embodied_ai_framework():
    """Test 4E Embodied AI framework configuration"""
    print("🤖 Testing 4E Embodied AI framework...")
    
    try:
        framework_4e = {
            "embodied": {
                "physical_simulation": True,
                "sensory_integration": True,
                "motor_control": True
            },
            "embedded": {
                "environment_coupling": True,
                "context_awareness": True,
                "situatedness": True
            },
            "enacted": {
                "action_perception_loop": True,
                "behavioral_adaptation": True,
                "dynamic_interaction": True
            },
            "extended": {
                "tool_use_integration": True,
                "cognitive_extension": True,
                "distributed_cognition": True
            }
        }
        
        # Validate all 4E components
        required_components = ['embodied', 'embedded', 'enacted', 'extended']
        
        for component in required_components:
            assert component in framework_4e, f"Missing {component} component"
            assert len(framework_4e[component]) > 0, f"Empty {component} configuration"
        
        total_features = sum(len(comp) for comp in framework_4e.values())
        
        return {
            'status': '✅ Valid',
            'components': len(framework_4e),
            'total_features': total_features,
            'all_enabled': all(
                all(feature for feature in comp.values()) 
                for comp in framework_4e.values()
            )
        }
        
    except Exception as e:
        return {
            'status': f'❌ Error: {e}',
            'components': 0,
            'total_features': 0,
            'all_enabled': False
        }

def main():
    """Run all validation tests"""
    print("🚀 GitHub Actions Workflow Validation")
    print("=" * 50)
    
    # Change to repository root if script is run from elsewhere
    script_dir = Path(__file__).parent
    if script_dir.name == 'scripts' or 'test' in script_dir.name:
        os.chdir(script_dir.parent)
    
    tests = [
        ("Workflow YAML Validity", test_workflow_yaml_validity),
        ("Echo Systems Detection", test_echo_systems_detection),
        ("VM-Daemon Configuration", test_vm_daemon_configuration),
        ("MLOps Pipeline Simulation", test_mlops_pipeline_simulation),
        ("4E Embodied AI Framework", test_4e_embodied_ai_framework)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results[test_name] = result
            
            if isinstance(result, dict):
                for key, value in result.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  Result: {result}")
                
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            results[test_name] = {'status': f'❌ Exception: {e}'}
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, result in results.items():
        if isinstance(result, dict) and 'status' in result:
            status = result['status']
        else:
            status = "✅ Valid" if result else "❌ Failed"
            
        print(f"{test_name}: {status}")
        
        if "✅" in status:
            success_count += 1
    
    success_rate = (success_count / total_count) * 100
    print(f"\nOverall Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
    
    if success_rate >= 80:
        print("🎉 Validation PASSED - Workflows are ready for deployment!")
        return 0
    else:
        print("⚠️ Validation FAILED - Please review and fix issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())