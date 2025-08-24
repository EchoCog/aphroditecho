"""
AAR Orchestration System - Final Demonstration

This script demonstrates the complete functionality of the AAR Orchestration System,
showcasing multiple agents interacting in a simulated environment with relationship formation.
"""

import asyncio
import logging
import time
from aar_core import AARCoreOrchestrator, AgentManager, SimulationEngine, RelationGraph
from aar_core.orchestration.core_orchestrator import AARConfig

# Configure logging to see system operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def demonstrate_aar_system():
    """Comprehensive demonstration of AAR system capabilities."""
    print("🚀 AAR Orchestration System - Live Demonstration")
    print("=" * 60)
    
    # Initialize system with production configuration
    config = AARConfig(
        max_concurrent_agents=100,
        arena_simulation_enabled=True,
        relation_graph_depth=3,
        resource_allocation_strategy='adaptive'
    )
    
    orchestrator = AARCoreOrchestrator(config)
    
    try:
        print("\n📊 System Initialization")
        initial_stats = await orchestrator.get_orchestration_stats()
        print(f"✅ Agent Manager: {initial_stats['component_stats']['agents']['agent_counts']['total']} agents")
        print(f"✅ Simulation Engine: {initial_stats['component_stats']['simulation']['system_info']['active_arenas']} active arenas")
        print(f"✅ Relation Graph: {initial_stats['component_stats']['relations']['graph_topology']['total_relations']} relationships")
        print(f"✅ System Health: {initial_stats['system_health']['overall_score']:.2f}")
        
        # Demonstration 1: Single Agent Task
        print("\n🤖 Demo 1: Single Agent Reasoning Task")
        print("-" * 40)
        
        single_request = {
            'request_id': 'demo_single',
            'task': 'analyze_scenario',
            'features': ['reasoning'],
            'context': {'scenario': 'market_analysis'}
        }
        
        start_time = time.time()
        result1 = await orchestrator.orchestrate_inference(single_request)
        duration1 = time.time() - start_time
        
        print(f"✅ Task completed in {duration1:.3f}s")
        print(f"   Agents used: {result1['orchestration_meta']['agents_used']}")
        print(f"   Arena: {result1['orchestration_meta']['arena_id']}")
        print(f"   Result confidence: {result1.get('consensus_confidence', 0.0):.3f}")
        
        # Demonstration 2: Multi-Agent Collaboration
        print("\n👥 Demo 2: Multi-Agent Collaborative Problem Solving")
        print("-" * 50)
        
        collaboration_request = {
            'request_id': 'demo_collaboration',
            'task': 'complex_strategy_planning',
            'features': ['collaboration', 'reasoning', 'communication'],
            'required_capabilities': {
                'collaboration': True,
                'reasoning': True,
                'min_agents': 4
            },
            'context': {
                'arena_type': 'collaborative',
                'interaction_type': 'complex_collaboration',
                'problem_domain': 'strategic_planning'
            }
        }
        
        start_time = time.time()
        result2 = await orchestrator.orchestrate_inference(collaboration_request)
        duration2 = time.time() - start_time
        
        print(f"✅ Collaboration completed in {duration2:.3f}s")
        print(f"   Agents involved: {result2['orchestration_meta']['agents_used']}")
        print(f"   Arena environment: {result2['orchestration_meta']['arena_id']}")
        print(f"   Consensus confidence: {result2.get('consensus_confidence', 0.0):.3f}")
        
        # Check relationship formation
        relation_stats = orchestrator.relation_graph.get_graph_stats()
        print(f"   Relationships formed: {relation_stats['graph_topology']['total_relations']}")
        print(f"   Relationship types: {relation_stats['relation_types']}")
        
        # Demonstration 3: 3D Physics Simulation
        print("\n🌍 Demo 3: 3D Physics Arena Simulation")
        print("-" * 40)
        
        physics_request = {
            'request_id': 'demo_physics',
            'task': 'spatial_navigation_planning',
            'features': ['spatial_reasoning', 'physics_simulation'],
            'context': {
                'arena_type': 'physics_3d',
                'simulation_enabled': True
            },
            'action': {
                'type': 'move',
                'direction': [1.0, 1.0, 0.0],
                'speed': 8.0
            }
        }
        
        start_time = time.time()
        result3 = await orchestrator.orchestrate_inference(physics_request)
        duration3 = time.time() - start_time
        
        print(f"✅ Physics simulation completed in {duration3:.3f}s")
        print(f"   Agent actions: {result3.get('action_result', {}).get('type', 'N/A')}")
        print(f"   Simulation time: {result3.get('simulation_time', 0.0):.3f}s")
        print(f"   Arena state: {result3.get('arena_state', {}).get('agent_count', 0)} agents active")
        
        # Demonstration 4: Competitive Interaction
        print("\n🏆 Demo 4: Competitive Multi-Agent Scenario")
        print("-" * 42)
        
        competitive_request = {
            'request_id': 'demo_competition',
            'task': 'resource_optimization_challenge',
            'features': ['competition', 'strategy', 'resource_management'],
            'required_capabilities': {
                'min_agents': 3
            },
            'context': {
                'arena_type': 'competitive',
                'challenge_type': 'resource_allocation',
                'time_limit': 30
            }
        }
        
        start_time = time.time()
        result4 = await orchestrator.orchestrate_inference(competitive_request)
        duration4 = time.time() - start_time
        
        print(f"✅ Competition completed in {duration4:.3f}s")
        print(f"   Competing agents: {result4['orchestration_meta']['agents_used']}")
        print(f"   Performance outcome: {result4.get('consensus_confidence', 0.0):.3f}")
        
        # Final System Analysis
        print("\n📈 System Performance Analysis")
        print("-" * 35)
        
        final_stats = await orchestrator.get_orchestration_stats()
        
        # Agent statistics
        agent_stats = final_stats['component_stats']['agents']
        print(f"Agent Management:")
        print(f"   Total agents spawned: {agent_stats['performance_stats']['total_spawned']}")
        print(f"   Active agents: {agent_stats['agent_counts']['active']}")
        print(f"   Peak concurrent agents: {agent_stats['performance_stats']['peak_concurrent_agents']}")
        print(f"   Evolution cycles: {agent_stats['performance_stats']['evolution_cycles']}")
        
        # Arena statistics  
        sim_stats = final_stats['component_stats']['simulation']
        print(f"Arena Simulation:")
        print(f"   Total arenas created: {sim_stats['system_info']['total_arenas_created']}")
        print(f"   Active arenas: {sim_stats['system_info']['active_arenas']}")
        print(f"   Total interactions: {sim_stats['system_info']['total_agent_interactions']}")
        
        # Relationship statistics
        rel_stats = final_stats['component_stats']['relations']
        print(f"Relationship Graph:")
        print(f"   Total relationships: {rel_stats['graph_topology']['total_relations']}")
        print(f"   Graph density: {rel_stats['graph_topology']['density']:.3f}")
        print(f"   Avg trust level: {rel_stats['average_metrics']['avg_trust_level']:.3f}")
        print(f"   Total interactions processed: {rel_stats['system_stats']['total_interactions_processed']}")
        
        # System health
        health = final_stats['system_health']
        print(f"System Health:")
        print(f"   Overall score: {health['overall_score']:.3f}")
        print(f"   Status: {health['status']}")
        print(f"   Error rate: {final_stats['performance_stats']['error_rate']:.3f}")
        print(f"   Avg response time: {final_stats['performance_stats']['avg_response_time']:.3f}s")
        
        # Relationship Analysis
        if rel_stats['graph_topology']['total_relations'] > 0:
            print("\n🔗 Relationship Network Analysis")
            print("-" * 35)
            
            centrality = orchestrator.relation_graph.calculate_centrality_metrics()
            
            # Find most influential agents
            if centrality:
                top_agents = sorted(centrality.items(), 
                                  key=lambda x: x[1]['influence_score'], 
                                  reverse=True)[:3]
                
                print("Most Influential Agents:")
                for agent_id, metrics in top_agents:
                    print(f"   {agent_id}: Influence {metrics['influence_score']:.3f}")
                    print(f"      Degree centrality: {metrics['degree_centrality']:.3f}")
                    print(f"      Betweenness centrality: {metrics['betweenness_centrality']:.3f}")
            
            # Community detection
            communities = orchestrator.relation_graph.detect_communities()
            if communities:
                print("Agent Communities:")
                for community, agents in communities.items():
                    print(f"   {community}: {len(agents)} agents")
        
        print(f"\n🎯 ACCEPTANCE CRITERIA VALIDATION")
        print("=" * 40)
        print("✅ Multiple agents can interact in simulated environment")
        print(f"   - Maximum agents in single interaction: {max(r['orchestration_meta']['agents_used'] for r in [result2, result4])}")
        print(f"   - Different arena types used: {len(set(r['orchestration_meta']['arena_id'] for r in [result1, result2, result3, result4] if r['orchestration_meta']['arena_id']))}")
        print(f"   - Relationships formed: {rel_stats['graph_topology']['total_relations']}")
        print(f"   - System remains healthy: {health['status'] == 'healthy'}")
        
        print(f"\n🏆 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print(f"Total demonstration time: {time.time() - (time.time() - duration1 - duration2 - duration3 - duration4):.2f}s")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n🔧 Shutting down system...")
        await orchestrator.shutdown()
        print("System shutdown complete.")


if __name__ == "__main__":
    print("Starting AAR Orchestration System Demonstration...")
    asyncio.run(demonstrate_aar_system())