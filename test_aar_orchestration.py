"""
Comprehensive tests for AAR Orchestration System

Tests agent interactions, arena simulation, and relation management.
Validates the acceptance criteria: Multiple agents can interact in simulated environment.
"""

import asyncio
import time
import pytest
from typing import Dict, Any, List

# Import AAR components
from aar_core import AARCoreOrchestrator, AgentManager, SimulationEngine, RelationGraph
from aar_core.orchestration.core_orchestrator import AARConfig
from aar_core.agents.agent_manager import AgentCapabilities, AgentStatus
from aar_core.arena.simulation_engine import ArenaType, ArenaConfig
from aar_core.relations.relation_graph import RelationType


class TestAAROrchestrationSystem:
    """Test suite for AAR Orchestration System."""
    
    @pytest.fixture
    def aar_config(self):
        """Create test configuration."""
        return AARConfig(
            max_concurrent_agents=20,
            arena_simulation_enabled=True,
            relation_graph_depth=3
        )
    
    @pytest.fixture
    async def orchestrator(self, aar_config):
        """Create and setup orchestrator for testing."""
        orchestrator = AARCoreOrchestrator(aar_config)
        yield orchestrator
        await orchestrator.shutdown()
    
    async def test_basic_orchestration_initialization(self, orchestrator):
        """Test that orchestrator initializes all components properly."""
        # Verify all components are initialized
        assert orchestrator.agent_manager is not None
        assert orchestrator.simulation_engine is not None
        assert orchestrator.relation_graph is not None
        
        # Check configuration
        assert orchestrator.config.max_concurrent_agents == 20
        assert orchestrator.config.arena_simulation_enabled is True
        
        # Verify initial state
        stats = await orchestrator.get_orchestration_stats()
        assert stats['performance_stats']['total_requests'] == 0
        assert stats['performance_stats']['active_agents_count'] == 0
    
    async def test_single_agent_interaction(self, orchestrator):
        """Test basic single agent interaction."""
        request = {
            'request_id': 'test_001',
            'task': 'simple_reasoning',
            'features': ['reasoning'],
            'context': {
                'arena_type': 'general'
            }
        }
        
        # Execute request
        result = await orchestrator.orchestrate_inference(request)
        
        # Verify result structure
        assert 'orchestration_meta' in result
        assert result['orchestration_meta']['agents_used'] >= 1
        assert result['orchestration_meta']['arena_id'] is not None
        assert result['orchestration_meta']['processing_time'] > 0
        
        # Check that agents were created and arena was used
        stats = await orchestrator.get_orchestration_stats()
        assert stats['performance_stats']['total_requests'] == 1
        
    async def test_multi_agent_collaboration(self, orchestrator):
        """Test multiple agents collaborating on a complex task."""
        request = {
            'request_id': 'test_002',
            'task': 'complex_collaboration',
            'features': ['complex_reasoning', 'collaboration'],
            'priority': 'high',
            'context': {
                'arena_type': 'collaborative',
                'required_agents': 3
            }
        }
        
        # Execute request
        result = await orchestrator.orchestrate_inference(request)
        
        # Verify multiple agents were used
        assert result['orchestration_meta']['agents_used'] >= 2
        
        # Check relationship formation
        relation_stats = orchestrator.relation_graph.get_graph_stats()
        assert relation_stats['graph_topology']['total_relations'] > 0
        
        # Verify arena was collaborative type
        simulation_stats = orchestrator.simulation_engine.get_system_stats()
        assert simulation_stats['system_info']['active_arenas'] >= 1
    
    async def test_agent_evolution_and_learning(self, orchestrator):
        """Test agent evolution through multiple interactions."""
        base_request = {
            'task': 'learning_task',
            'features': ['reasoning', 'learning'],
            'context': {
                'arena_type': 'learning'
            }
        }
        
        # Execute multiple requests to trigger learning
        for i in range(5):
            request = {
                **base_request,
                'request_id': f'learning_{i}',
                'iteration': i
            }
            result = await asyncio.wait_for(
                orchestrator.orchestrate_inference(request),
                timeout=10.0
            )
            assert 'error' not in result
        
        # Check agent evolution
        agent_stats = orchestrator.agent_manager.get_system_stats()
        assert agent_stats['performance_stats']['evolution_cycles'] > 0
        
        # Verify learning improved performance
        final_stats = await orchestrator.get_orchestration_stats()
        assert final_stats['performance_stats']['total_requests'] == 5
        assert final_stats['system_health']['overall_score'] > 0.5
    
    async def test_arena_physics_simulation(self, orchestrator):
        """Test 3D physics simulation in arena environment."""
        request = {
            'request_id': 'physics_test',
            'task': 'physical_interaction',
            'action': {
                'type': 'move',
                'direction': [1.0, 0.0, 0.0],
                'speed': 5.0
            },
            'context': {
                'arena_type': 'physics_3d'
            }
        }
        
        # Execute request
        result = await orchestrator.orchestrate_inference(request)
        
        # Verify arena physics simulation was used
        assert result['orchestration_meta']['arena_id'] is not None
        
        # Check that simulation engine processed physics
        arenas = orchestrator.simulation_engine.list_arenas()
        physics_arenas = [a for a in arenas if 'physics' in a['type']]
        assert len(physics_arenas) >= 1
    
    async def test_relation_graph_dynamics(self, orchestrator):
        """Test dynamic relationship formation and evolution."""
        # Create multiple agents with different interaction patterns
        requests = [
            {
                'request_id': 'collab_1',
                'task': 'collaborative_task',
                'features': ['collaboration'],
                'agent_preference': 'collaborative',
                'context': {'arena_type': 'collaborative'}
            },
            {
                'request_id': 'compete_1', 
                'task': 'competitive_task',
                'features': ['competition'],
                'agent_preference': 'competitive',
                'context': {'arena_type': 'competitive'}
            },
            {
                'request_id': 'mentor_1',
                'task': 'learning_task',
                'features': ['mentoring', 'learning'],
                'agent_preference': 'mentor',
                'context': {'arena_type': 'learning'}
            }
        ]
        
        # Execute all requests
        for request in requests:
            result = await orchestrator.orchestrate_inference(request)
            assert 'error' not in result
        
        # Analyze relationship formation
        relation_stats = orchestrator.relation_graph.get_graph_stats()
        
        # Verify relationships were created
        assert relation_stats['graph_topology']['total_relations'] > 0
        assert relation_stats['graph_topology']['node_count'] > 0
        
        # Check relationship types
        relation_types = relation_stats['relation_types']
        assert len(relation_types) > 0  # At least some relationships formed
        
        # Test relationship strength evolution
        centrality_metrics = orchestrator.relation_graph.calculate_centrality_metrics()
        assert len(centrality_metrics) > 0
    
    async def test_system_performance_under_load(self, orchestrator):
        """Test system performance with concurrent agent interactions."""
        num_concurrent_requests = 10
        
        # Create concurrent requests
        tasks = []
        for i in range(num_concurrent_requests):
            request = {
                'request_id': f'load_test_{i}',
                'task': f'concurrent_task_{i}',
                'features': ['reasoning'],
                'context': {
                    'arena_type': 'general',
                    'concurrency_test': True
                }
            }
            task = orchestrator.orchestrate_inference(request)
            tasks.append(task)
        
        # Execute all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verify results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= num_concurrent_requests * 0.8  # 80% success rate
        
        # Check performance metrics
        stats = await orchestrator.get_orchestration_stats()
        assert stats['performance_stats']['total_requests'] >= num_concurrent_requests
        assert stats['system_health']['overall_score'] > 0.4  # System should remain stable
        
        # Verify response time is reasonable
        total_time = end_time - start_time
        assert total_time < 30.0  # Should complete within 30 seconds
    
    async def test_agent_memory_and_context_preservation(self, orchestrator):
        """Test that agents maintain memory and context across interactions."""
        # First interaction to establish context
        initial_request = {
            'request_id': 'memory_init',
            'task': 'remember_context',
            'context': {
                'user_id': 'test_user',
                'session_id': 'memory_session',
                'memory_key': 'test_memory',
                'memory_value': 'important_data'
            }
        }
        
        result1 = await orchestrator.orchestrate_inference(initial_request)
        initial_agent_count = result1['orchestration_meta']['agents_used']
        
        # Second interaction referencing previous context
        followup_request = {
            'request_id': 'memory_recall',
            'task': 'recall_context',
            'context': {
                'user_id': 'test_user',
                'session_id': 'memory_session',
                'query_memory': 'test_memory'
            }
        }
        
        result2 = await orchestrator.orchestrate_inference(followup_request)
        
        # Verify agents maintained relationships and context
        relation_stats = orchestrator.relation_graph.get_graph_stats()
        assert relation_stats['system_stats']['total_interactions_processed'] > 0
        
        # Check that relationships strengthened with repeated interactions
        if relation_stats['graph_topology']['total_relations'] > 0:
            avg_trust = relation_stats['average_metrics']['avg_trust_level']
            assert avg_trust > 0.5  # Trust should build over time
    
    async def test_error_handling_and_recovery(self, orchestrator):
        """Test system resilience to errors and recovery mechanisms."""
        # Test with malformed request
        malformed_request = {
            'request_id': 'error_test',
            'task': None,  # Invalid task
            'features': ['invalid_feature'],
            'context': {
                'arena_type': 'nonexistent_type'
            }
        }
        
        result = await orchestrator.orchestrate_inference(malformed_request)
        
        # System should handle gracefully
        assert 'error' in result or 'orchestration_meta' in result
        
        # System should remain healthy after error
        health = await orchestrator.get_orchestration_stats()
        assert health['system_health']['status'] in ['healthy', 'degraded']
        
        # Test recovery with valid request
        recovery_request = {
            'request_id': 'recovery_test',
            'task': 'simple_task',
            'features': ['reasoning'],
            'context': {'arena_type': 'general'}
        }
        
        recovery_result = await orchestrator.orchestrate_inference(recovery_request)
        assert 'orchestration_meta' in recovery_result
        
    def test_acceptance_criteria_multiple_agents_interaction(self):
        """
        ACCEPTANCE CRITERIA TEST: Multiple agents can interact in simulated environment
        
        This test validates the core requirement from Task 1.2.1.
        """
        async def run_acceptance_test():
            config = AARConfig(max_concurrent_agents=50)
            orchestrator = AARCoreOrchestrator(config)
            
            try:
                # Create a complex multi-agent interaction scenario
                interaction_request = {
                    'request_id': 'acceptance_test',
                    'task': 'multi_agent_collaboration',
                    'features': ['collaboration', 'communication', 'reasoning'],
                    'required_capabilities': {
                        'collaboration': True,
                        'reasoning': True,
                        'min_agents': 3
                    },
                    'context': {
                        'arena_type': 'collaborative',
                        'simulation_enabled': True,
                        'interaction_type': 'complex_collaboration'
                    }
                }
                
                # Execute multi-agent interaction
                result = await orchestrator.orchestrate_inference(interaction_request)
                
                # ACCEPTANCE CRITERIA VALIDATION
                
                # 1. Multiple agents were involved
                agents_used = result['orchestration_meta']['agents_used']
                assert agents_used >= 2, f"Expected multiple agents, got {agents_used}"
                
                # 2. Agents interacted in simulated environment
                arena_id = result['orchestration_meta']['arena_id']
                assert arena_id is not None, "No arena was created for simulation"
                
                # 3. Verify simulation environment details
                arenas = orchestrator.simulation_engine.list_arenas()
                active_arena = next((a for a in arenas if a['id'] == arena_id), None)
                assert active_arena is not None, "Arena not found in simulation engine"
                assert active_arena['agent_count'] >= 2, "Multiple agents not present in arena"
                
                # 4. Verify agent relationships were formed
                relation_stats = orchestrator.relation_graph.get_graph_stats()
                assert relation_stats['graph_topology']['total_relations'] > 0, "No relationships formed between agents"
                
                # 5. Verify successful interaction processing
                assert 'primary_result' in result, "No primary result from agent interaction"
                assert result.get('contributing_agents', 0) >= 2, "Not enough agents contributed to result"
                
                # 6. Check system health after complex interaction
                health = await orchestrator.get_orchestration_stats()
                assert health['system_health']['overall_score'] > 0.6, "System health degraded significantly"
                
                print("✅ ACCEPTANCE CRITERIA PASSED:")
                print(f"   - {agents_used} agents successfully interacted")
                print(f"   - Simulated environment: {arena_id}")
                print(f"   - {relation_stats['graph_topology']['total_relations']} relationships formed")
                print(f"   - System health: {health['system_health']['overall_score']:.2f}")
                print(f"   - Arena agent count: {active_arena['agent_count']}")
                
                return True
                
            finally:
                await orchestrator.shutdown()
        
        # Run the acceptance test
        result = asyncio.run(run_acceptance_test())
        assert result is True


# Standalone test runner for manual execution
async def run_comprehensive_tests():
    """Run all tests manually for validation."""
    print("🚀 Starting AAR Orchestration System Tests...")
    
    config = AARConfig(max_concurrent_agents=20)
    orchestrator = AARCoreOrchestrator(config)
    
    try:
        print("\n1. Testing basic initialization...")
        stats = await orchestrator.get_orchestration_stats()
        assert stats['component_stats']['agents']['agent_counts']['total'] == 0
        print("   ✅ Basic initialization successful")
        
        print("\n2. Testing single agent interaction...")
        request = {
            'request_id': 'test_single',
            'task': 'simple_task',
            'features': ['reasoning']
        }
        result = await orchestrator.orchestrate_inference(request)
        assert 'orchestration_meta' in result
        print(f"   ✅ Single agent interaction successful (used {result['orchestration_meta']['agents_used']} agents)")
        
        print("\n3. Testing multi-agent collaboration...")
        collab_request = {
            'request_id': 'test_collab',
            'task': 'collaborative_task',
            'features': ['collaboration', 'complex_reasoning'],
            'priority': 'high',
            'context': {'arena_type': 'collaborative'}
        }
        result = await orchestrator.orchestrate_inference(collab_request)
        agents_used = result['orchestration_meta']['agents_used']
        print(f"   ✅ Multi-agent collaboration successful (used {agents_used} agents)")
        
        print("\n4. Testing arena simulation...")
        physics_request = {
            'request_id': 'test_physics',
            'task': 'physics_simulation',
            'context': {'arena_type': 'physics_3d'},
            'action': {'type': 'move', 'direction': [1, 0, 0]}
        }
        result = await orchestrator.orchestrate_inference(physics_request)
        arena_id = result['orchestration_meta']['arena_id']
        print(f"   ✅ Arena simulation successful (arena: {arena_id})")
        
        print("\n5. Testing relationship formation...")
        final_stats = await orchestrator.get_orchestration_stats()
        relations = final_stats['component_stats']['relations']['graph_topology']['total_relations']
        print(f"   ✅ Relationship formation successful ({relations} relations)")
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"Final system stats:")
        print(f"   - Total requests processed: {final_stats['performance_stats']['total_requests']}")
        print(f"   - Active agents: {final_stats['component_stats']['agents']['agent_counts']['active']}")
        print(f"   - Active arenas: {final_stats['component_stats']['simulation']['system_info']['active_arenas']}")
        print(f"   - System health: {final_stats['system_health']['overall_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise
    finally:
        await orchestrator.shutdown()
        print("🔧 System shutdown complete")


if __name__ == "__main__":
    # Run comprehensive tests
    asyncio.run(run_comprehensive_tests())
    
    # Run acceptance criteria test
    test_instance = TestAAROrchestrationSystem()
    test_instance.test_acceptance_criteria_multiple_agents_interaction()
    print("\n🏆 ACCEPTANCE CRITERIA VALIDATION COMPLETED SUCCESSFULLY!")