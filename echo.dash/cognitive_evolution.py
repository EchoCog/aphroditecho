#!/usr/bin/env python3
"""
Cognitive Evolution Integration - Integrates echo_evolution.py with cognitive_architecture.py

This module connects the self-evolving system with the cognitive architecture,
allowing agents to:
1. Generate goals based on system evolution
2. Learn from evolution experiences
3. Adapt personality traits based on evolutionary success
4. Store evolution history in cognitive memory
"""

import os
import sys
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import random

# Import our evolution system
from echo_evolution import (
    EchoAgent, 
    EvolutionNetwork, 
    ResourceMonitor, 
    EvolutionMemory
)

# Import cognitive architecture
from cognitive_architecture import (
    CognitiveArchitecture, 
    Memory, 
    Goal, 
    PersonalityTrait, 
    MemoryType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cognitive_evolution")

class CognitiveEvolutionBridge:
    """
    Connects the echo_evolution system with the cognitive_architecture.
    
    This bridge allows:
    - Evolution data to be stored as cognitive memories
    - Evolution metrics to influence personality traits
    - Evolution progress to generate cognitive goals
    - Cognitive architecture to constrain evolution pathways
    """
    
    def __init__(self, network: EvolutionNetwork):
        """
        Initialize the bridge between evolution network and cognitive architecture
        
        Args:
            network: An initialized EvolutionNetwork
        """
        self.network = network
        self.cognitive = CognitiveArchitecture()
        self.evolution_memory = EvolutionMemory()
        logger.info("CognitiveEvolutionBridge initialized")
    
    def evolution_cycle_to_experience(self, cycle_data: Dict) -> Dict:
        """
        Convert evolution cycle data to a cognitive experience
        
        Args:
            cycle_data: Data from an evolution cycle
            
        Returns:
            Dict containing the experience data
        """
        avg_state = sum(cycle_data["agents"].values()) / len(cycle_data["agents"])
        evolution_success = avg_state > 0.5
        significance = min(1.0, abs(avg_state) * 2)
        
        # Create experience based on evolution results
        experience = {
            "type": "adaptation" if evolution_success else "challenge",
            "description": f"Evolution cycle {'succeeded' if evolution_success else 'struggled'} with avg state {avg_state:.2f}",
            "effectiveness": avg_state,
            "resolution": avg_state if evolution_success else 0.5 - avg_state,
            "importance": significance,
            "emotional_impact": significance * (1 if evolution_success else -1) * 0.5,
            "area": "self_evolution",
            "timestamp": datetime.now().timestamp(),
            "details": {
                "agents": cycle_data["agents"],
                "resources": cycle_data.get("resource_metrics", {}),
                "duration": cycle_data.get("duration", 0)
            }
        }
        
        return experience
    
    def job_cycle_to_experience(self, job_data: Dict) -> Dict:
        """
        Convert job processing cycle data to a cognitive experience
        
        Args:
            job_data: Data from a job processing cycle
            
        Returns:
            Dict containing the experience data
        """
        success_rate = job_data.get("success_rate", 0)
        job_success = success_rate > 0.7
        significance = success_rate
        
        # Create experience based on job results
        experience = {
            "type": "learning" if job_success else "challenge",
            "description": f"Processing jobs with {success_rate:.0%} success rate",
            "success": success_rate,
            "importance": significance,
            "emotional_impact": (success_rate - 0.5) * 2,  # -1 to +1 scale
            "area": "job_processing",
            "timestamp": datetime.now().timestamp(),
            "details": {
                "results": job_data.get("job_results", {}),
                "duration": job_data.get("duration", 0)
            }
        }
        
        return experience
    
    def create_memory_from_evolution(self, cycle_data: Dict) -> Memory:
        """
        Create a cognitive memory from evolution data
        
        Args:
            cycle_data: Data from an evolution cycle
            
        Returns:
            Memory object containing the evolution data
        """
        # Convert cycle data to a memory
        experience = self.evolution_cycle_to_experience(cycle_data)
        
        memory = Memory(
            content=experience["description"],
            memory_type=MemoryType.EPISODIC,
            timestamp=experience["timestamp"],
            emotional_valence=experience["emotional_impact"],
            importance=experience["importance"],
            context=experience
        )
        
        # Add associations based on agent domains
        for agent_name in cycle_data["agents"].keys():
            agent = self.network.agents.get(agent_name)
            if agent:
                memory.associations.add(agent.domain)
        
        return memory
    
    def update_personality_from_evolution(self, cycle_data: Dict) -> None:
        """
        Update cognitive personality traits based on evolution results
        
        Args:
            cycle_data: Data from an evolution cycle
        """
        # Extract relevant metrics
        avg_state = sum(cycle_data["agents"].values()) / len(cycle_data["agents"])
        max_state = max(cycle_data["agents"].values()) if cycle_data["agents"] else 0
        
        # Update adaptability based on average evolution state
        self.cognitive.personality_traits["adaptability"].update(
            avg_state,
            {"source": "evolution", "data": cycle_data}
        )
        
        # Update creativity based on maximum evolution state
        self.cognitive.personality_traits["creativity"].update(
            max_state,
            {"source": "evolution", "data": cycle_data}
        )
        
        # Update persistence based on resource metrics
        if "resource_metrics" in cycle_data:
            resource_load = (
                cycle_data["resource_metrics"].get("cpu_usage", 50) + 
                cycle_data["resource_metrics"].get("memory_usage", 50)
            ) / 200  # Normalize to 0-1
            
            self.cognitive.personality_traits["persistence"].update(
                1.0 - resource_load,  # Higher persistence when resources available
                {"source": "evolution", "resources": cycle_data["resource_metrics"]}
            )
    
    def generate_evolution_goals(self) -> List[Goal]:
        """
        Generate cognitive goals based on evolution system state
        
        Returns:
            List of Goal objects
        """
        goals = []
        
        # Get summary of all agents
        summary = self.network.get_summary()
        
        # Generate improvement goals for struggling agents
        for name, info in summary["agents"].items():
            if info["state"] < 0.5:  # Struggling agent
                goals.append(Goal(
                    description=f"Improve evolution of {name} agent",
                    priority=0.9 - info["state"],  # Higher priority for lower states
                    deadline=None,
                    context={
                        "type": "evolution_improvement",
                        "agent": name,
                        "current_state": info["state"],
                        "error_rate": info["error_rate"]
                    }
                ))
        
        # Generate exploration goal if average state is high
        if summary["average_state"] > 0.7:
            goals.append(Goal(
                description=f"Explore new evolution patterns",
                priority=0.7,
                deadline=None,
                context={
                    "type": "evolution_exploration",
                    "current_avg_state": summary["average_state"]
                }
            ))
        
        return goals
    
    def create_evolution_constraints_from_cognition(self) -> Dict[str, float]:
        """
        Generate evolution constraints based on cognitive architecture state
        
        Returns:
            Dict mapping agent names to constraint values
        """
        constraints = {}
        
        # Generate constraints based on personality traits
        adaptability = self.cognitive.personality_traits["adaptability"].current_value
        creativity = self.cognitive.personality_traits["creativity"].current_value
        persistence = self.cognitive.personality_traits["persistence"].current_value
        
        # Apply personality-based constraints to each agent
        for agent_name, agent in self.network.agents.items():
            # Base constraint from personality
            if "Cognitive" in agent_name:
                # Cognitive agents are influenced more by creativity
                constraints[agent_name] = creativity
            elif "Memory" in agent_name:
                # Memory agents are influenced more by persistence
                constraints[agent_name] = persistence
            elif "Sensory" in agent_name:
                # Sensory agents are influenced more by adaptability
                constraints[agent_name] = adaptability
            else:
                # Default influence is average of traits
                constraints[agent_name] = (adaptability + creativity + persistence) / 3
        
        # Modify constraints based on active goals
        for goal in self.cognitive.active_goals:
            if goal.context.get("type") == "evolution_improvement":
                target_agent = goal.context.get("agent")
                if target_agent in constraints:
                    # Increase constraint for agents that need improvement
                    constraints[target_agent] += 0.2 * goal.priority
        
        return constraints
    
    async def process_evolution_cycle(self, cycle_data: Dict) -> None:
        """
        Process a completed evolution cycle
        
        Args:
            cycle_data: Data from an evolution cycle
        """
        # Create cognitive memory from evolution data
        memory = self.create_memory_from_evolution(cycle_data)
        self.cognitive.enhanced_memory_management(memory)
        
        # Update personality traits
        self.update_personality_from_evolution(cycle_data)
        
        # Create cognitive experience
        experience = self.evolution_cycle_to_experience(cycle_data)
        self.cognitive.learn_from_experience(experience)
        
        # Generate new goals if needed
        if experience["importance"] > 0.7:
            goals = self.generate_evolution_goals()
            for goal in goals:
                self.cognitive.enhanced_goal_management(goal)
        
        # Save cognitive state
        self.cognitive.save_state()
    
    async def process_job_cycle(self, job_data: Dict) -> None:
        """
        Process a completed job processing cycle
        
        Args:
            job_data: Data from a job processing cycle
        """
        # Create cognitive experience
        experience = self.job_cycle_to_experience(job_data)
        self.cognitive.learn_from_experience(experience)
        
        # Update personality traits based on job success
        success_rate = job_data.get("success_rate", 0)
        self.cognitive.personality_traits["persistence"].update(
            success_rate,
            {"source": "job_processing", "success_rate": success_rate}
        )
        
        # Save cognitive state
        self.cognitive.save_state()
    
    async def apply_cognitive_constraints(self) -> None:
        """Apply cognitive constraints to evolution network"""
        # Generate constraints from cognitive state
        constraints = self.create_evolution_constraints_from_cognition()
        
        # Apply constraints to network
        for agent_name, constraint in constraints.items():
            agent = self.network.agents.get(agent_name)
            if agent:
                # Apply constraint as adjustment to state
                adjustment = (constraint - 0.5) * 0.2  # Scale to modest adjustment
                agent.state = max(0, agent.state + adjustment)
                
                logger.info(
                    f"Applied cognitive constraint to {agent_name}: "
                    f"adjustment {adjustment:.2f}, new state: {agent.state:.2f}"
                )
    
    async def run_integrated_evolution(self, cycles: int = 5) -> Dict:
        """
        Run evolution cycles with cognitive integration
        
        Args:
            cycles: Number of evolution cycles to run
            
        Returns:
            Dict containing results of all cycles
        """
        results = {
            "evolution_cycles": [],
            "job_cycles": [],
            "cognitive_updates": [],
            "start_time": datetime.now().isoformat()
        }
        
        for cycle in range(cycles):
            logger.info(f"\n=== Integrated Evolution Cycle {cycle+1}/{cycles} ===")
            
            # Apply cognitive constraints before evolution
            await self.apply_cognitive_constraints()
            
            # Run evolution cycle
            evo_result = await self.network.run_cycle()
            results["evolution_cycles"].append(evo_result)
            
            # Process evolution results in cognitive system
            await self.process_evolution_cycle(evo_result)
            
            # Run job processing cycle
            logger.info(f"=== Integrated Job Cycle {cycle+1}/{cycles} ===")
            job_result = await self.network.run_job_cycle()
            results["job_cycles"].append(job_result)
            
            # Process job results in cognitive system
            await self.process_job_cycle(job_result)
            
            # Record cognitive state
            cognitive_state = {
                "personality": {
                    trait: value.current_value 
                    for trait, value in self.cognitive.personality_traits.items()
                },
                "active_goals": len(self.cognitive.active_goals),
                "memories": len(self.cognitive.memories)
            }
            results["cognitive_updates"].append(cognitive_state)
            
            # Brief pause between cycles
            await asyncio.sleep(0.5)
        
        results["end_time"] = datetime.now().isoformat()
        
        return results

async def main():
    """Main function demonstrating the Cognitive Evolution Integration"""
    # Define domains for evolution agents
    domains = [
        ("CognitiveAgent", "Cognitive Architecture"),
        ("MemoryAgent", "Memory Management"),
        ("SensoryAgent", "Sensory Processing"),
        ("IntegrationAgent", "System Integration")
    ]
    
    # Create evolution network
    network = EvolutionNetwork()
    
    # Add agents to network
    for name, domain in domains:
        agent = EchoAgent(name, domain, initial_state=random.uniform(0, 1))
        network.add_agent(agent)
    
    # Create cognitive evolution bridge
    bridge = CognitiveEvolutionBridge(network)
    
    logger.info("Starting Integrated Cognitive Evolution System")
    results = await bridge.run_integrated_evolution(cycles=3)
    
    # Print summary
    logger.info("\n=== Cognitive Evolution Summary ===")
    logger.info(f"Evolution Cycles: {len(results['evolution_cycles'])}")
    logger.info(f"Job Cycles: {len(results['job_cycles'])}")
    logger.info("Final Personality State:")
    for trait, value in results["cognitive_updates"][-1]["personality"].items():
        logger.info(f"  {trait}: {value:.2f}")
    
    # Network summary
    network_summary = network.get_summary()
    logger.info("\n=== Evolution Network Summary ===")
    logger.info(f"Average Agent State: {network_summary['average_state']:.2f}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())