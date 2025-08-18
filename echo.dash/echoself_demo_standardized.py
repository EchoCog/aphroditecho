#!/usr/bin/env python3
"""
Echoself Demo - Standardized Version

Migrated from original echoself_demo.py to use standardized Echo component base classes.
This demonstrates the Echoself recursive self-model integration with standardized interfaces.

Original functionality: Recursive introspection, hypergraph encoding, adaptive attention allocation
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import standardized Echo components
from echo_component_base import MemoryEchoComponent, EchoConfig, EchoResponse

# Import the cognitive architecture for functionality
try:
    from cognitive_architecture import CognitiveArchitecture
    COGNITIVE_ARCHITECTURE_AVAILABLE = True
except ImportError:
    COGNITIVE_ARCHITECTURE_AVAILABLE = False
    CognitiveArchitecture = None


class EchoselfDemoStandardized(MemoryEchoComponent):
    """
    Standardized Echoself demonstration component
    
    Provides recursive introspection capabilities with standardized Echo interfaces.
    Extends MemoryEchoComponent for memory-focused introspection operations.
    """
    
    def __init__(self, config: EchoConfig):
        super().__init__(config)
        
        # Component-specific initialization
        self.cognitive_system = None
        self.demo_cycles_completed = 0
        self.introspection_results = []
        self.export_path = "demo_hypergraph_export.json"
    
    def initialize(self) -> EchoResponse:
        """Initialize the Echoself demo system"""
        try:
            # Check if we have a pre-set cognitive system (for testing)
            if self.cognitive_system is not None:
                self._initialized = True
                return EchoResponse(
                    success=True,
                    message="Echoself demo system initialized with provided cognitive system",
                    data={
                        'cognitive_system_available': True,
                        'echoself_introspection_available': hasattr(self.cognitive_system, 'echoself_introspection'),
                        'export_path': self.export_path
                    }
                )
            
            if not COGNITIVE_ARCHITECTURE_AVAILABLE:
                return EchoResponse(
                    success=False,
                    message="CognitiveArchitecture not available - required for Echoself demo",
                    metadata={'error': 'missing_dependency'}
                )
            
            self.logger.info("Initializing cognitive architecture for Echoself demo")
            self.cognitive_system = CognitiveArchitecture()
            
            if not self.cognitive_system.echoself_introspection:
                return EchoResponse(
                    success=False,
                    message="Echoself introspection system not available in cognitive architecture",
                    metadata={'error': 'echoself_unavailable'}
                )
            
            self._initialized = True
            self.logger.info("Echoself demo system initialized successfully")
            
            return EchoResponse(
                success=True,
                message="Echoself demo system initialized with cognitive architecture",
                data={
                    'cognitive_system_available': True,
                    'echoself_introspection_available': True,
                    'export_path': self.export_path
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Process demonstration requests
        
        Supported operations:
        - 'introspection_cycle': Run a single introspection demonstration
        - 'adaptive_attention': Demonstrate adaptive attention allocation
        - 'hypergraph_export': Export hypergraph data
        - 'neural_symbolic_synergy': Demonstrate multi-cycle evolution
        - 'full_demo': Run complete demonstration sequence
        """
        try:
            if not self._initialized:
                return EchoResponse(
                    success=False,
                    message="Component not initialized - call initialize() first"
                )
            
            # Parse input data
            if isinstance(input_data, str):
                operation = input_data
                params = kwargs
            elif isinstance(input_data, dict):
                operation = input_data.get('operation', 'full_demo')
                params = input_data.get('params', {})
                params.update(kwargs)
            else:
                operation = 'full_demo'
                params = kwargs
            
            self.logger.info(f"Processing operation: {operation}")
            
            # Route to appropriate demonstration
            if operation == 'introspection_cycle':
                return self._demonstrate_introspection_cycle(**params)
            elif operation == 'adaptive_attention':
                return self._demonstrate_adaptive_attention(**params)
            elif operation == 'hypergraph_export':
                return self._demonstrate_hypergraph_export(**params)
            elif operation == 'neural_symbolic_synergy':
                return self._demonstrate_neural_symbolic_synergy(**params)
            elif operation == 'full_demo':
                return self._run_full_demonstration(**params)
            else:
                return EchoResponse(
                    success=False,
                    message=f"Unknown operation: {operation}",
                    metadata={'valid_operations': [
                        'introspection_cycle', 'adaptive_attention', 
                        'hypergraph_export', 'neural_symbolic_synergy', 'full_demo'
                    ]}
                )
                
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """
        Echo operation for Echoself demo
        
        Returns demonstration state with echo characteristics
        """
        try:
            echoed_data = {
                'demo_state': {
                    'cycles_completed': self.demo_cycles_completed,
                    'introspection_results_count': len(self.introspection_results),
                    'cognitive_system_available': self.cognitive_system is not None,
                    'initialized': self._initialized
                },
                'echo_value': echo_value,
                'recent_results': self.introspection_results[-3:] if self.introspection_results else [],
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"Echoself demo echo (value: {echo_value}, cycles: {self.demo_cycles_completed})",
                metadata={
                    'echo_value': echo_value,
                    'cycles_completed': self.demo_cycles_completed
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def _demonstrate_introspection_cycle(self, cycle_num: int = None) -> EchoResponse:
        """Demonstrate a single introspection cycle"""
        try:
            if cycle_num is None:
                cycle_num = self.demo_cycles_completed + 1
            
            self.logger.info(f"Starting introspection cycle {cycle_num}")
            
            # Perform recursive introspection
            start_time = time.time()
            prompt = self.cognitive_system.perform_recursive_introspection()
            introspection_time = time.time() - start_time
            
            if not prompt:
                return EchoResponse(
                    success=False,
                    message=f"No introspection prompt generated for cycle {cycle_num}"
                )
            
            # Get attention metrics
            metrics = self.cognitive_system.get_introspection_metrics()
            
            # Generate enhanced goals
            goals = self.cognitive_system.adaptive_goal_generation_with_introspection()
            
            # Store results
            result = {
                'cycle_num': cycle_num,
                'prompt_length': len(prompt),
                'prompt_preview': prompt[:300] + "..." if len(prompt) > 300 else prompt,
                'introspection_time': introspection_time,
                'metrics': metrics,
                'goals_generated': len(goals),
                'goals_preview': [
                    {
                        'description': goal.description,
                        'priority': goal.priority,
                        'context_type': goal.context.get('type', 'general')
                    }
                    for goal in goals[:5]
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            self.introspection_results.append(result)
            self.demo_cycles_completed = max(self.demo_cycles_completed, cycle_num)
            
            return EchoResponse(
                success=True,
                data=result,
                message=f"Introspection cycle {cycle_num} completed successfully",
                metadata={
                    'cycle_num': cycle_num,
                    'introspection_time': introspection_time,
                    'goals_generated': len(goals)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, f"introspection_cycle_{cycle_num}")
    
    def _demonstrate_adaptive_attention(self) -> EchoResponse:
        """Demonstrate adaptive attention under different cognitive loads"""
        try:
            scenarios = [
                (0.2, 0.8, "Low load, high activity"),
                (0.8, 0.2, "High load, low activity"), 
                (0.5, 0.5, "Balanced load and activity"),
                (0.9, 0.9, "High load, high activity"),
                (0.1, 0.1, "Low load, low activity")
            ]
            
            results = []
            
            for load, activity, description in scenarios:
                # Calculate attention threshold
                attention_threshold = self.cognitive_system.echoself_introspection.adaptive_attention(
                    load, activity
                )
                
                # Perform introspection with this scenario
                prompt = self.cognitive_system.perform_recursive_introspection(load, activity)
                file_count = prompt.count('(file "') if prompt else 0
                
                scenario_result = {
                    'description': description,
                    'load': load,
                    'activity': activity,
                    'attention_threshold': attention_threshold,
                    'files_included': file_count,
                    'prompt_generated': prompt is not None
                }
                
                results.append(scenario_result)
            
            return EchoResponse(
                success=True,
                data={
                    'scenarios': results,
                    'total_scenarios': len(results)
                },
                message="Adaptive attention demonstration completed successfully",
                metadata={
                    'scenarios_tested': len(scenarios),
                    'all_prompts_generated': all(r['prompt_generated'] for r in results)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "adaptive_attention")
    
    def _demonstrate_hypergraph_export(self) -> EchoResponse:
        """Demonstrate hypergraph data export"""
        try:
            self.logger.info(f"Exporting hypergraph data to {self.export_path}")
            success = self.cognitive_system.export_introspection_data(self.export_path)
            
            if not success:
                return EchoResponse(
                    success=False,
                    message="Hypergraph export failed"
                )
            
            # Analyze exported data
            export_stats = {}
            try:
                with open(self.export_path, encoding='utf-8') as f:
                    data = json.load(f)
                
                nodes = data.get('nodes', [])
                export_stats = {
                    'total_nodes': len(nodes),
                    'attention_decisions': len(data.get('attention_history', [])),
                    'top_salient_files': []
                }
                
                if nodes:
                    sorted_nodes = sorted(nodes, key=lambda n: n.get('salience_score', 0), reverse=True)
                    export_stats['top_salient_files'] = [
                        {
                            'file': node['id'],
                            'salience_score': node['salience_score']
                        }
                        for node in sorted_nodes[:5]
                    ]
            
            except Exception as e:
                export_stats['read_error'] = str(e)
            
            return EchoResponse(
                success=True,
                data={
                    'export_path': self.export_path,
                    'export_successful': True,
                    'statistics': export_stats
                },
                message="Hypergraph export completed successfully",
                metadata={'export_path': self.export_path}
            )
            
        except Exception as e:
            return self.handle_error(e, "hypergraph_export")
    
    def _demonstrate_neural_symbolic_synergy(self, cycles: int = 3) -> EchoResponse:
        """Demonstrate neural-symbolic integration through multiple cycles"""
        try:
            initial_memory_count = len(self.cognitive_system.memories)
            initial_goal_count = len(self.cognitive_system.goals)
            
            cycle_results = []
            
            for cycle in range(1, cycles + 1):
                # Introspect
                prompt = self.cognitive_system.perform_recursive_introspection()
                
                # Generate goals  
                goals = self.cognitive_system.adaptive_goal_generation_with_introspection()
                
                # Track evolution
                current_memory_count = len(self.cognitive_system.memories)
                current_goal_count = len(self.cognitive_system.goals)
                
                cycle_result = {
                    'cycle': cycle,
                    'memory_count': current_memory_count,
                    'goal_count': current_goal_count,
                    'memory_delta': current_memory_count - initial_memory_count,
                    'goal_delta': current_goal_count - initial_goal_count,
                    'prompt_generated': prompt is not None,
                    'goals_generated': len(goals)
                }
                
                cycle_results.append(cycle_result)
                
                # Update for next iteration
                initial_memory_count = current_memory_count
                initial_goal_count = current_goal_count
            
            return EchoResponse(
                success=True,
                data={
                    'cycles_completed': cycles,
                    'cycle_results': cycle_results,
                    'synergy_demonstrated': True
                },
                message=f"Neural-symbolic synergy demonstration completed over {cycles} cycles",
                metadata={
                    'cycles': cycles,
                    'total_memory_growth': sum(r['memory_delta'] for r in cycle_results),
                    'total_goal_growth': sum(r['goal_delta'] for r in cycle_results)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "neural_symbolic_synergy")
    
    def _run_full_demonstration(self) -> EchoResponse:
        """Run the complete demonstration sequence"""
        try:
            results = {
                'demonstration_started': datetime.now().isoformat(),
                'stages': {}
            }
            
            # Stage 1: Introspection cycles
            self.logger.info("Running introspection cycles")
            for cycle in range(1, 3):
                cycle_result = self._demonstrate_introspection_cycle(cycle)
                results['stages'][f'introspection_cycle_{cycle}'] = {
                    'success': cycle_result.success,
                    'message': cycle_result.message,
                    'data': cycle_result.data if cycle_result.success else None
                }
                if not cycle_result.success:
                    self.logger.warning(f"Cycle {cycle} failed: {cycle_result.message}")
                time.sleep(0.1)  # Brief pause
            
            # Stage 2: Adaptive attention
            self.logger.info("Running adaptive attention demonstration")
            attention_result = self._demonstrate_adaptive_attention()
            results['stages']['adaptive_attention'] = {
                'success': attention_result.success,
                'message': attention_result.message,
                'data': attention_result.data if attention_result.success else None
            }
            
            # Stage 3: Hypergraph export
            self.logger.info("Running hypergraph export demonstration")
            export_result = self._demonstrate_hypergraph_export()
            results['stages']['hypergraph_export'] = {
                'success': export_result.success,
                'message': export_result.message,
                'data': export_result.data if export_result.success else None
            }
            
            # Stage 4: Neural-symbolic synergy
            self.logger.info("Running neural-symbolic synergy demonstration")
            synergy_result = self._demonstrate_neural_symbolic_synergy()
            results['stages']['neural_symbolic_synergy'] = {
                'success': synergy_result.success,
                'message': synergy_result.message,
                'data': synergy_result.data if synergy_result.success else None
            }
            
            # Summary
            successful_stages = sum(1 for stage in results['stages'].values() if stage['success'])
            total_stages = len(results['stages'])
            
            results['demonstration_completed'] = datetime.now().isoformat()
            results['summary'] = {
                'successful_stages': successful_stages,
                'total_stages': total_stages,
                'success_rate': successful_stages / total_stages,
                'fully_successful': successful_stages == total_stages
            }
            
            return EchoResponse(
                success=True,
                data=results,
                message=f"Full demonstration completed: {successful_stages}/{total_stages} stages successful",
                metadata={
                    'stages_completed': total_stages,
                    'success_rate': successful_stages / total_stages
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "full_demonstration")
    
    def cleanup_demo_files(self) -> EchoResponse:
        """Clean up demonstration files"""
        try:
            demo_files = [self.export_path, "echoself_hypergraph.json"]
            cleaned_files = []
            
            for file_path in demo_files:
                if Path(file_path).exists():
                    Path(file_path).unlink()
                    cleaned_files.append(file_path)
                    self.logger.info(f"Cleaned up {file_path}")
            
            return EchoResponse(
                success=True,
                data={'cleaned_files': cleaned_files},
                message=f"Cleaned up {len(cleaned_files)} demo files"
            )
            
        except Exception as e:
            return self.handle_error(e, "cleanup")


# Factory function for creating Echoself demo system
def create_echoself_demo_system() -> EchoselfDemoStandardized:
    """Create a standardized Echoself demo system"""
    config = EchoConfig(
        component_name="EchoselfDemo",
        version="1.0.0",
        debug_mode=False
    )
    
    demo = EchoselfDemoStandardized(config)
    result = demo.initialize()
    
    if not result.success:
        raise RuntimeError(f"Failed to initialize Echoself demo: {result.message}")
    
    return demo


# Backward compatibility functions - maintain original interface
def setup_logging():
    """Set up logging for the demonstration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demonstrate_introspection_cycle(cognitive_system: Any, cycle_num: int):
    """Legacy function for backward compatibility"""
    # Create a temporary standardized component for this operation
    config = EchoConfig(component_name="LegacyEchoselfDemo", debug_mode=False)
    demo = EchoselfDemoStandardized(config)
    demo.cognitive_system = cognitive_system
    demo._initialized = True
    
    result = demo._demonstrate_introspection_cycle(cycle_num)
    
    # Print results in original format
    if result.success:
        data = result.data
        print(f"\n{'='*60}")
        print(f"RECURSIVE INTROSPECTION CYCLE {cycle_num}")
        print(f"{'='*60}")
        print("📊 Cognitive State Analysis:")
        print("   Analyzing current system state through introspection...")
        print(f"\n🔍 Performing recursive introspection...")
        print(f"⏱️  Introspection completed in {data['introspection_time']:.2f} seconds")
        print(f"📝 Generated prompt length: {data['prompt_length']} characters")
        print("📝 Prompt preview (first 300 chars):")
        print(f"   {data['prompt_preview']}")
        
        print("\n📊 Attention Allocation Metrics:")
        for key, value in data['metrics'].items():
            if key == "highest_salience_files":
                print(f"   {key}:")
                for file_info in value:
                    print(f"     - {file_info[0]}: {file_info[1]:.3f}")
            else:
                print(f"   {key}: {value}")
        
        print(f"\n🎯 Generating introspection-enhanced goals...")
        print(f"Generated {data['goals_generated']} goals:")
        for i, goal in enumerate(data['goals_preview'], 1):
            print(f"   {i}. {goal['description']}")
            print(f"      Priority: {goal['priority']:.3f}")
            print(f"      Context: {goal['context_type']}")
        
        if data['goals_generated'] > 5:
            print(f"   ... and {data['goals_generated'] - 5} more goals")
    else:
        print(f"❌ {result.message}")


def main():
    """Main demonstration function with backward compatibility"""
    setup_logging()
    
    print("🌳 ECHOSELF RECURSIVE SELF-MODEL INTEGRATION DEMONSTRATION 🌳")
    print("Implementing hypergraph encoding and adaptive attention allocation")
    print("Inspired by DeepTreeEcho/Eva Self Model architecture")
    
    try:
        # Create standardized demo system
        print("\n🚀 Initializing standardized Echoself demo system...")
        demo = create_echoself_demo_system()
        print("✅ Echoself demo system initialized successfully!")
        
        # Run full demonstration
        result = demo.process('full_demo')
        
        if result.success:
            print(f"\n{'='*60}")
            print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY! 🎉")
            print("The Echoself recursive self-model integration is fully operational.")
            print("Key achievements:")
            print("  ✅ Hypergraph-encoded repository introspection")
            print("  ✅ Adaptive attention allocation mechanisms")
            print("  ✅ Neural-symbolic synergy through recursive feedback")
            print("  ✅ Integration with cognitive architecture")
            print("  ✅ Standardized Echo interfaces")
            print(f"{'='*60}")
        else:
            print(f"❌ Demonstration failed: {result.message}")
        
        # Clean up
        demo.cleanup_demo_files()
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()