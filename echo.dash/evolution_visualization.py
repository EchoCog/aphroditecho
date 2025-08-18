#!/usr/bin/env python3
"""
Evolution Visualization System - Visualizes and tracks the self-evolution process.

This module provides visualization tools to monitor the self-evolution process,
including:
1. Terminal-based visualization for headless environments
2. Real-time metrics tracking
3. Evolution network visualization
4. Cognitive-evolution integration visualization
"""

import os
import sys
import logging
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import random
import math

try:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logging.warning("Matplotlib not available. Visualization will be limited to terminal.")

# Import our evolution systems
from echo_evolution import EchoAgent, EvolutionNetwork
from cognitive_evolution import CognitiveEvolutionBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("evolution_visualization")

class TerminalVisualizer:
    """
    Terminal-based visualization for evolution progress.
    Works in both GUI and headless environments.
    """
    
    def __init__(self):
        """Initialize the terminal visualizer"""
        self.width = 80
        self.history = {}
        self.colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m",
        }
    
    def _get_color(self, value: float) -> str:
        """Get color based on value (0-1)"""
        if value < 0.3:
            return self.colors["red"]
        elif value < 0.6:
            return self.colors["yellow"]
        else:
            return self.colors["green"]
    
    def _generate_bar(self, value: float, width: int = 20) -> str:
        """Generate a progress bar"""
        filled = int(value * width)
        bar = "█" * filled + "░" * (width - filled)
        color = self._get_color(value)
        return f"{color}{bar}{self.colors['reset']}"
    
    def visualize_network(self, network: EvolutionNetwork) -> None:
        """
        Visualize evolution network state in terminal
        
        Args:
            network: The evolution network to visualize
        """
        print("\n" + "=" * self.width)
        print(f"Evolution Network State - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * self.width)
        
        # Calculate average state
        states = [agent.state for agent in network.agents.values()]
        avg_state = sum(states) / len(states) if states else 0
        
        # Store in history for trend
        current_time = time.time()
        self.history[current_time] = avg_state
        
        # Clean history older than 60 minutes
        cutoff = current_time - 3600
        self.history = {k: v for k, v in self.history.items() if k >= cutoff}
        
        # Print overall state
        print(f"\nOverall System State: {avg_state:.2f}")
        print(self._generate_bar(avg_state, self.width - 20))
        
        # Calculate trend
        if len(self.history) > 1:
            times = list(self.history.keys())
            times.sort()
            if len(times) >= 2:
                first_time = times[0]
                last_time = times[-1]
                first_val = self.history[first_time]
                last_val = self.history[last_time]
                
                trend = last_val - first_val
                trend_symbol = "↗" if trend > 0.05 else "↘" if trend < -0.05 else "→"
                print(f"Trend: {trend_symbol} ({trend:+.2f})")
        
        # Print individual agents
        print("\nAgents:")
        for name, agent in network.agents.items():
            name_display = name[:25].ljust(25)
            state_display = f"{agent.state:.2f}".ljust(6)
            bar = self._generate_bar(agent.state, 30)
            print(f"  {name_display} {state_display} {bar}")
        
        # Print resources
        resources = network.resource_monitor.get_metrics()
        print("\nSystem Resources:")
        for resource, value in resources.items():
            normalized = min(1.0, value / 100.0)  # Normalize to 0-1
            name_display = resource.replace("_", " ").title().ljust(15)
            value_display = f"{value:.1f}%".ljust(8)
            bar = self._generate_bar(1 - normalized, 30)  # Invert so less usage = more green
            print(f"  {name_display} {value_display} {bar}")
        
        print("\n" + "=" * self.width)
    
    def visualize_cognitive_integration(self, bridge: CognitiveEvolutionBridge) -> None:
        """
        Visualize cognitive-evolution integration
        
        Args:
            bridge: Cognitive evolution bridge to visualize
        """
        print("\n" + "=" * self.width)
        print(f"Cognitive-Evolution Integration - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * self.width)
        
        # Print personality traits
        print("\nPersonality Traits:")
        for trait, value in bridge.cognitive.personality_traits.items():
            name_display = trait.title().ljust(15)
            value_display = f"{value.current_value:.2f}".ljust(6)
            bar = self._generate_bar(value.current_value, 30)
            print(f"  {name_display} {value_display} {bar}")
        
        # Print active goals
        print("\nActive Goals:")
        if bridge.cognitive.active_goals:
            for i, goal in enumerate(bridge.cognitive.active_goals[:5]):  # Show only top 5
                priority_color = self._get_color(goal.priority)
                print(f"  {i+1}. {priority_color}{goal.description}{self.colors['reset']} (p={goal.priority:.2f})")
        else:
            print("  No active goals")
        
        # Print memory metrics
        mem_count = len(bridge.cognitive.memories)
        print(f"\nMemories: {mem_count}")
        
        # Print agent constraints
        print("\nEvolution Constraints:")
        constraints = bridge.create_evolution_constraints_from_cognition()
        for agent, constraint in constraints.items():
            name_display = agent[:25].ljust(25)
            constraint_display = f"{constraint:.2f}".ljust(6)
            bar = self._generate_bar(constraint, 30)
            print(f"  {name_display} {constraint_display} {bar}")
        
        print("\n" + "=" * self.width)


class GraphicalVisualizer:
    """
    Matplotlib-based visualization for evolution progress.
    Only available if matplotlib is installed.
    """
    
    def __init__(self):
        """Initialize the graphical visualizer"""
        if not HAS_MATPLOTLIB:
            raise ImportError("Matplotlib is required for GraphicalVisualizer")
        
        self.history = {
            "timestamps": [],
            "avg_state": [],
            "agents": {},
            "resources": {},
            "personality": {}
        }
        
        # Create figure and subplots
        self.fig = plt.figure(figsize=(15, 10), constrained_layout=True)
        self.gs = self.fig.add_gridspec(3, 2)
        
        # Create subplots
        self.agent_ax = self.fig.add_subplot(self.gs[0, :])
        self.resource_ax = self.fig.add_subplot(self.gs[1, 0])
        self.personality_ax = self.fig.add_subplot(self.gs[1, 1])
        self.network_ax = self.fig.add_subplot(self.gs[2, :])
        
        # Set titles
        self.agent_ax.set_title("Agent States Over Time")
        self.resource_ax.set_title("System Resources")
        self.personality_ax.set_title("Personality Traits")
        self.network_ax.set_title("Evolution Network")
        
        # Animation setup
        self.ani = None
    
    def update_data(self, network: EvolutionNetwork, bridge: Optional[CognitiveEvolutionBridge] = None) -> None:
        """
        Update visualization data
        
        Args:
            network: The evolution network
            bridge: Optional cognitive evolution bridge
        """
        timestamp = datetime.now()
        self.history["timestamps"].append(timestamp)
        
        # Update average state
        states = [agent.state for agent in network.agents.values()]
        avg_state = sum(states) / len(states) if states else 0
        self.history["avg_state"].append(avg_state)
        
        # Update agent states
        for name, agent in network.agents.items():
            if name not in self.history["agents"]:
                self.history["agents"][name] = []
            self.history["agents"][name].append(agent.state)
            
            # Pad shorter histories
            while len(self.history["agents"][name]) < len(self.history["timestamps"]):
                self.history["agents"][name].insert(0, None)
        
        # Update resource metrics
        resources = network.resource_monitor.get_metrics()
        for name, value in resources.items():
            if name not in self.history["resources"]:
                self.history["resources"][name] = []
            self.history["resources"][name].append(value)
            
            # Pad shorter histories
            while len(self.history["resources"][name]) < len(self.history["timestamps"]):
                self.history["resources"][name].insert(0, None)
        
        # Update personality traits if bridge available
        if bridge:
            for trait, value in bridge.cognitive.personality_traits.items():
                if trait not in self.history["personality"]:
                    self.history["personality"][trait] = []
                self.history["personality"][trait].append(value.current_value)
                
                # Pad shorter histories
                while len(self.history["personality"][trait]) < len(self.history["timestamps"]):
                    self.history["personality"][trait].insert(0, None)
        
        # Limit history length
        max_history = 100
        if len(self.history["timestamps"]) > max_history:
            self.history["timestamps"] = self.history["timestamps"][-max_history:]
            self.history["avg_state"] = self.history["avg_state"][-max_history:]
            
            for name in self.history["agents"]:
                self.history["agents"][name] = self.history["agents"][name][-max_history:]
                
            for name in self.history["resources"]:
                self.history["resources"][name] = self.history["resources"][name][-max_history:]
                
            for name in self.history["personality"]:
                self.history["personality"][name] = self.history["personality"][name][-max_history:]
    
    def _update_plot(self, frame: int) -> List:
        """
        Update plot animation
        
        Args:
            frame: Animation frame number
            
        Returns:
            List of updated artists
        """
        artists = []
        
        # Clear axes
        self.agent_ax.clear()
        self.resource_ax.clear()
        self.personality_ax.clear()
        self.network_ax.clear()
        
        # Set titles
        self.agent_ax.set_title("Agent States Over Time")
        self.resource_ax.set_title("System Resources")
        self.personality_ax.set_title("Personality Traits")
        self.network_ax.set_title("Evolution Network")
        
        # Plot agent states
        for name, states in self.history["agents"].items():
            line, = self.agent_ax.plot(self.history["timestamps"], states, label=name)
            artists.append(line)
        
        # Plot average state
        avg_line, = self.agent_ax.plot(
            self.history["timestamps"], 
            self.history["avg_state"], 
            'k--', 
            linewidth=2, 
            label="Average"
        )
        artists.append(avg_line)
        
        self.agent_ax.set_ylim(0, 1)
        self.agent_ax.set_ylabel("State Value")
        self.agent_ax.legend(loc="upper left")
        self.agent_ax.grid(True, alpha=0.3)
        
        # Plot resources as bar chart
        if self.history["resources"] and self.history["timestamps"]:
            latest_resources = {
                name: values[-1] 
                for name, values in self.history["resources"].items() 
                if values
            }
            
            names = list(latest_resources.keys())
            values = list(latest_resources.values())
            
            bars = self.resource_ax.bar(
                names, 
                values, 
                color=['green' if v < 50 else 'yellow' if v < 80 else 'red' for v in values]
            )
            self.resource_ax.set_ylim(0, 100)
            self.resource_ax.set_ylabel("Usage %")
            self.resource_ax.set_xticklabels([n.replace("_", " ").title() for n in names], rotation=45)
            
            artists.extend(bars)
        
        # Plot personality traits as radar chart
        if self.history["personality"] and self.history["timestamps"]:
            latest_personality = {
                name: values[-1] 
                for name, values in self.history["personality"].items() 
                if values
            }
            
            if latest_personality:
                trait_names = list(latest_personality.keys())
                trait_values = list(latest_personality.values())
                
                # Close the radar plot
                trait_names.append(trait_names[0])
                trait_values.append(trait_values[0])
                
                # Calculate coordinates
                angles = np.linspace(0, 2*np.pi, len(trait_names), endpoint=True)
                
                # Plot radar
                self.personality_ax.plot(angles, trait_values, 'o-', linewidth=2)
                self.personality_ax.fill(angles, trait_values, alpha=0.25)
                self.personality_ax.set_thetagrids(angles * 180/np.pi, trait_names)
                self.personality_ax.set_ylim(0, 1)
                self.personality_ax.grid(True)
        
        # Plot network as graph
        if self.history["agents"] and self.history["timestamps"]:
            # Get latest agent states
            latest_states = {
                name: values[-1] 
                for name, values in self.history["agents"].items() 
                if values
            }
            
            # Create positions for nodes in a circle
            n_agents = len(latest_states)
            pos = {}
            for i, name in enumerate(latest_states.keys()):
                angle = 2 * np.pi * i / n_agents
                pos[name] = (np.cos(angle), np.sin(angle))
            
            # Draw nodes
            for name, position in pos.items():
                state = latest_states[name]
                color = f"C{list(latest_states.keys()).index(name)}"
                size = 500 + 1000 * state
                node = self.network_ax.scatter(
                    position[0], 
                    position[1], 
                    s=size, 
                    alpha=0.7, 
                    color=color, 
                    label=name
                )
                artists.append(node)
                
                # Add label
                self.network_ax.annotate(
                    name, 
                    (position[0], position[1]),
                    ha='center', 
                    va='center'
                )
            
            # Draw edges between all nodes
            for name1 in latest_states:
                for name2 in latest_states:
                    if name1 != name2:
                        # Calculate edge thickness based on states
                        state1 = latest_states[name1]
                        state2 = latest_states[name2]
                        edge_weight = (state1 + state2) / 2
                        
                        # Draw edge
                        line = self.network_ax.plot(
                            [pos[name1][0], pos[name2][0]],
                            [pos[name1][1], pos[name2][1]],
                            'k-', 
                            alpha=0.2 + 0.3 * edge_weight,
                            linewidth=0.5 + 2 * edge_weight
                        )
                        artists.extend(line)
            
            self.network_ax.set_xlim(-1.2, 1.2)
            self.network_ax.set_ylim(-1.2, 1.2)
            self.network_ax.set_aspect('equal')
            self.network_ax.axis('off')
        
        return artists
    
    def show(self) -> None:
        """Show the visualization (non-animated)"""
        self._update_plot(0)
        plt.tight_layout()
        plt.show()
    
    def start_animation(self, interval: int = 1000) -> None:
        """
        Start animation
        
        Args:
            interval: Update interval in milliseconds
        """
        self.ani = FuncAnimation(
            self.fig, 
            self._update_plot, 
            interval=interval, 
            blit=True
        )
        plt.tight_layout()
        plt.show()
    
    def save_snapshot(self, filename: str = "evolution_snapshot.png") -> str:
        """
        Save current visualization as image file
        
        Args:
            filename: File name to save image as
            
        Returns:
            Path to saved file
        """
        self._update_plot(0)
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        return os.path.abspath(filename)


class VisualizationManager:
    """
    Manages both terminal and graphical visualization
    """
    
    def __init__(self):
        """Initialize visualization manager"""
        self.terminal = TerminalVisualizer()
        self.graphical = None
        
        # Try to initialize graphical visualizer
        if HAS_MATPLOTLIB:
            try:
                self.graphical = GraphicalVisualizer()
                logger.info("Graphical visualization enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize graphical visualization: {e}")
    
    async def visualize(self, 
                        network: EvolutionNetwork, 
                        bridge: Optional[CognitiveEvolutionBridge] = None,
                        graphical: bool = False) -> None:
        """
        Visualize the current state of the evolution system
        
        Args:
            network: The evolution network to visualize
            bridge: Optional cognitive evolution bridge to visualize
            graphical: Whether to use graphical visualization
        """
        # Terminal visualization
        self.terminal.visualize_network(network)
        
        if bridge:
            self.terminal.visualize_cognitive_integration(bridge)
        
        # Graphical visualization
        if graphical and self.graphical:
            self.graphical.update_data(network, bridge)
            self.graphical.show()
    
    async def start_live_visualization(self,
                                      network: EvolutionNetwork,
                                      bridge: Optional[CognitiveEvolutionBridge] = None,
                                      interval: float = 1.0) -> None:
        """
        Start live visualization
        
        Args:
            network: The evolution network to visualize
            bridge: Optional cognitive evolution bridge to visualize
            interval: Update interval in seconds
        """
        if self.graphical:
            # Start updating data in background
            async def update_background():
                while True:
                    self.graphical.update_data(network, bridge)
                    await asyncio.sleep(interval)
            
            # Create background task
            update_task = asyncio.create_task(update_background())
            
            # Start animation on main thread
            self.graphical.start_animation(interval * 1000)
            
            # Cancel update task when animation closes
            update_task.cancel()
        else:
            # Use terminal visualization in loop
            while True:
                await self.visualize(network, bridge)
                await asyncio.sleep(interval)
    
    def save_snapshot(self, filename: str = "evolution_snapshot.png") -> Optional[str]:
        """
        Save visualization snapshot to file
        
        Args:
            filename: File name to save image as
            
        Returns:
            Path to saved file or None if graphical visualization not available
        """
        if self.graphical:
            return self.graphical.save_snapshot(filename)
        return None


async def main():
    """Main function demonstrating visualization capabilities"""
    from echo_evolution import EchoAgent, EvolutionNetwork
    from cognitive_architecture import CognitiveArchitecture
    from cognitive_evolution import CognitiveEvolutionBridge
    
    # Create evolution network
    network = EvolutionNetwork()
    
    # Add agents
    agent_domains = [
        ("CognitiveAgent", "Cognitive Processing"),
        ("MemoryAgent", "Memory Management"),
        ("SensoryAgent", "Sensory Input"),
        ("ActionAgent", "Action Generation"),
        ("IntegrationAgent", "System Integration")
    ]
    
    for name, domain in agent_domains:
        agent = EchoAgent(name, domain, initial_state=random.uniform(0.3, 0.8))
        network.add_agent(agent)
    
    # Create cognitive bridge
    bridge = CognitiveEvolutionBridge(network)
    
    # Create visualization manager
    viz = VisualizationManager()
    
    # Show single visualization
    await viz.visualize(network, bridge)
    
    # Save snapshot if graphical available
    if viz.graphical:
        path = viz.save_snapshot("evolution_demo.png")
        if path:
            logger.info(f"Saved snapshot to {path}")
    
    # Run evolution cycle
    await bridge.run_integrated_evolution(cycles=1)
    
    # Show updated visualization
    await viz.visualize(network, bridge)
    
    logger.info("Visualization demo complete. For continuous visualization, use start_live_visualization()")
    
    return network, bridge, viz

if __name__ == "__main__":
    asyncio.run(main())