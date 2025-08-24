"""
AAR Core Orchestrator

Central orchestration system for agent-arena-relation management.
Integrates with Aphrodite Engine and Echo-Self Evolution Engine.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
from dataclasses import dataclass

from ..agents.agent_manager import AgentManager, AgentCapabilities
from ..arena.simulation_engine import SimulationEngine, ArenaType
from ..relations.relation_graph import RelationGraph, RelationType

logger = logging.getLogger(__name__)


@dataclass
class AARConfig:
    """Configuration for AAR orchestration system."""
    max_concurrent_agents: int = 1000
    arena_simulation_enabled: bool = True
    relation_graph_depth: int = 3
    resource_allocation_strategy: str = "adaptive"
    agent_lifecycle_timeout: int = 300  # seconds
    performance_monitoring_interval: int = 10  # seconds


class AARCoreOrchestrator:
    """Central orchestration system for agent-arena-relation management."""
    
    def __init__(self, config: AARConfig):
        self.config = config
        
        # Initialize core components
        self.agent_manager = AgentManager(config.max_concurrent_agents)
        self.simulation_engine = SimulationEngine() if config.arena_simulation_enabled else None
        self.relation_graph = RelationGraph(config.relation_graph_depth)
        
        # Integration points
        self.aphrodite_engine = None
        self.dtesn_kernel = None
        self.echo_self_engine = None
        
        # Performance metrics
        self.performance_stats = {
            'total_requests': 0,
            'active_agents_count': 0,
            'arena_utilization': 0.0,
            'avg_response_time': 0.0,
            'error_rate': 0.0
        }
        
        logger.info(f"AAR Core Orchestrator initialized with config: {config}")
    
    def set_aphrodite_integration(self, aphrodite_engine):
        """Set Aphrodite Engine integration."""
        self.aphrodite_engine = aphrodite_engine
        logger.info("Aphrodite Engine integration enabled")
    
    def set_dtesn_integration(self, dtesn_kernel):
        """Set DTESN kernel integration."""
        self.dtesn_kernel = dtesn_kernel
        logger.info("DTESN kernel integration enabled")
    
    def set_echo_self_integration(self, echo_self_engine):
        """Set Echo-Self evolution engine integration."""
        self.echo_self_engine = echo_self_engine
        logger.info("Echo-Self evolution engine integration enabled")
    
    def enable_echo_self_integration(self, echo_self_engine):
        """Enable integration with Echo-Self evolution engine (alias)."""
        self.set_echo_self_integration(echo_self_engine)
    
    async def orchestrate_inference(self, 
                                      request: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate inference through agent-arena system."""
        try:
            self.performance_stats['total_requests'] += 1
            start_time = asyncio.get_event_loop().time()
            
            # Step 1: Allocate appropriate agents for request
            allocated_agents = await self._allocate_agents(request)
            
            if not allocated_agents:
                return {'error': 'No agents available for request'}
            
            # Step 2: Create or select virtual arena if simulation enabled
            arena_id = None
            if self.simulation_engine:
                arena_id = await self._get_arena(request.get('context', {}))
            
            # Step 3: Execute distributed inference
            results = []
            for agent_id in allocated_agents:
                # Get agent data
                agent_data = self.agent_manager.get_agent_status(agent_id)
                if not agent_data:
                    continue
                
                # Update agent with current membrane states
                await self._sync_agent_membranes(agent_data)
                
                # Execute in virtual arena or directly
                if arena_id and self.simulation_engine:
                    agent_result = await self.simulation_engine.execute_agent_in_arena(
                        arena_id, agent_data, request
                    )
                else:
                    # Execute directly through agent manager
                    agent_result = await self.agent_manager.process_agent_request(
                        agent_id, request
                    )
                
                results.append(agent_result)
            
            # Step 4: Aggregate results through relation graph
            final_result = await self.relation_graph.aggregate_results(results)
            
            # Step 5: Update relationships based on performance
            await self._update_relations(allocated_agents, final_result)
            
            # Update performance metrics
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            await self._update_performance_stats(response_time, success=True)
            
            # Add orchestration metadata
            final_result.update({
                'orchestration_meta': {
                    'agents_used': len(allocated_agents),
                    'arena_id': arena_id,
                    'processing_time': response_time,
                    'request_id': request.get('request_id', 'unknown')
                }
            })
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in orchestrate_inference: {e}")
            await self._update_performance_stats(0.0, success=False)
            return {'error': str(e)}
    
    async def _allocate_agents(self, request: Dict[str, Any]) -> List[str]:
        """Allocate appropriate agents for request."""
        # Determine required agent count and capabilities
        agent_count = self._calculate_required_agents(request)
        
        # Use agent manager to allocate agents
        allocated_agents = await self.agent_manager.allocate_agents(request, agent_count)
        
        logger.debug(f"Allocated {len(allocated_agents)} agents for request")
        return allocated_agents
    
    def _calculate_required_agents(self, request: Dict[str, Any]) -> int:
        """Calculate number of agents required for request."""
        # Basic heuristic - in practice this would be more sophisticated
        base_agents = 1
        
        # Adjust based on request complexity
        if 'complex_reasoning' in request.get('features', []):
            base_agents += 2
        
        if 'collaboration' in request.get('features', []):
            base_agents += 2  # Collaboration requires multiple agents
            
        if 'multi_modal' in request.get('features', []):
            base_agents += 1
        
        if request.get('priority', 'normal') == 'high':
            base_agents += 1
        
        # Check for explicit minimum agent requirement
        min_agents = request.get('required_capabilities', {}).get('min_agents', 1)
        base_agents = max(base_agents, min_agents)
        
        # Check context requirements
        context = request.get('context', {})
        if context.get('interaction_type') == 'complex_collaboration':
            base_agents = max(base_agents, 3)
        
        return min(base_agents, 10)  # Cap at reasonable limit
    
    async def _get_arena(self, context: Dict[str, Any]) -> str:
        """Create or select virtual arena."""
        if not self.simulation_engine:
            return None
        
        # Determine arena type from context
        arena_type_name = context.get('arena_type', 'GENERAL')
        arena_type = ArenaType.GENERAL
        
        try:
            arena_type = ArenaType(arena_type_name.lower())
        except ValueError:
            logger.warning(f"Unknown arena type {arena_type_name}, using GENERAL")
        
        # Get or create arena
        arena_id = await self.simulation_engine.get_or_create_arena(context, arena_type)
        
        return arena_id
    
    async def _sync_agent_membranes(self, agent_data: Dict[str, Any]) -> None:
        """Update agent with current membrane states."""
        if self.dtesn_kernel:
            # Get current membrane states from DTESN kernel
            membrane_states = await self._get_dtesn_membrane_states()
            agent_data['membrane_states'] = membrane_states
    
    async def _get_dtesn_membrane_states(self) -> Dict[str, Any]:
        """Get current DTESN membrane states."""
        # Placeholder for DTESN integration
        return {
            'hierarchy_depth': 4,
            'active_membranes': [],
            'reservoir_dynamics': {},
            'evolution_state': {}
        }
    
    async def _update_relations(self, agent_ids: List[str], result: Dict[str, Any]) -> None:
        """Update relationships based on performance."""
        if len(agent_ids) < 2:
            return
        
        # Create agent data for relation graph
        agents = [{'id': agent_id} for agent_id in agent_ids]
        
        # Extract performance score from result
        performance_score = result.get('consensus_confidence', 0.5)
        
        # Update relationships through relation graph
        await self.relation_graph.update_relationships(agents, performance_score)
    
    async def _update_performance_stats(self, response_time: float, success: bool) -> None:
        """Update system performance statistics."""
        # Update average response time
        total_requests = self.performance_stats['total_requests']
        current_avg = self.performance_stats['avg_response_time']
        
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.performance_stats['avg_response_time'] = new_avg
        
        # Update error rate
        if not success:
            errors = self.performance_stats.get('total_errors', 0) + 1
            self.performance_stats['total_errors'] = errors
            self.performance_stats['error_rate'] = errors / total_requests
        
        # Update active agents count
        if self.agent_manager:
            agent_stats = self.agent_manager.get_system_stats()
            self.performance_stats['active_agents_count'] = agent_stats['agent_counts']['active']
        
        # Update arena utilization
        if self.simulation_engine:
            arenas = self.simulation_engine.list_arenas()
            active_arenas = len([a for a in arenas if a['active_sessions'] > 0])
            total_arenas = len(arenas)
            self.performance_stats['arena_utilization'] = active_arenas / max(total_arenas, 1)
    
    async def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get current orchestration statistics."""
        agent_stats = self.agent_manager.get_system_stats() if self.agent_manager else {}
        simulation_stats = self.simulation_engine.get_system_stats() if self.simulation_engine else {}
        relation_stats = self.relation_graph.get_graph_stats() if self.relation_graph else {}
        
        return {
            'performance_stats': self.performance_stats,
            'config': self.config,
            'integration_status': {
                'aphrodite_engine': self.aphrodite_engine is not None,
                'dtesn_kernel': self.dtesn_kernel is not None,
                'echo_self_engine': self.echo_self_engine is not None
            },
            'component_stats': {
                'agents': agent_stats,
                'simulation': simulation_stats,
                'relations': relation_stats
            },
            'system_health': await self._calculate_system_health()
        }
    
    async def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health metrics."""
        health_score = 1.0
        
        # Adjust based on error rate
        error_rate = self.performance_stats.get('error_rate', 0.0)
        health_score -= error_rate
        
        # Adjust based on agent manager health
        if self.agent_manager:
            agent_health = self.agent_manager.get_system_stats()['health_status']
            health_score *= agent_health['overall_score']
        
        return {
            'overall_score': max(0.0, min(1.0, health_score)),
            'components_healthy': {
                'agent_manager': self.agent_manager is not None,
                'simulation_engine': self.simulation_engine is not None,
                'relation_graph': self.relation_graph is not None
            },
            'error_rate': error_rate,
            'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'critical'
        }
    
    async def shutdown(self) -> None:
        """Graceful shutdown of orchestration system."""
        logger.info("Shutting down AAR Core Orchestrator...")
        
        # Shutdown components in order
        if self.agent_manager:
            await self.agent_manager.shutdown()
        
        if self.simulation_engine:
            await self.simulation_engine.shutdown()
        
        if self.relation_graph:
            await self.relation_graph.shutdown()
        
        logger.info("AAR Core Orchestrator shutdown complete")