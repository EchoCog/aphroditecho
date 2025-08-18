#!/usr/bin/env python3
"""
Test script to demonstrate Differential Emotion Theory integration with Deep Tree Echo.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from deep_tree_echo import DeepTreeEcho, TreeNode
from emotional_dynamics import CoreEmotion
from differential_emotion_theory import DETEmotion

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_tree():
    """Create a test tree with emotional content"""
    # Initialize Deep Tree Echo with DET integration
    # Set use_julia=False if Julia is not installed
    dte = DeepTreeEcho(echo_threshold=0.5, max_depth=5, use_julia=True)
    
    # Create root with content that should trigger INTEREST and EXCITEMENT
    root = dte.create_tree(
        "I'm fascinated by the curious patterns emerging from this novel approach to learning."
    )
    
    # Create children with different emotional content
    fear_node = dte.add_child(
        root, 
        "The terrifying implications make me feel ashamed of our inadequate preparation."
    )
    
    joy_node = dte.add_child(
        root, 
        "What a delightful discovery! I'm feeling so happy and amused by these playful results."
    )
    
    anger_node = dte.add_child(
        root, 
        "The obstruction of progress makes me angry and full of contempt for the opposition."
    )
    
    # Add a second level to the tree
    dte.add_child(
        fear_node,
        "I'm guilty about my fearful reaction and shy about expressing these concerns."
    )
    
    dte.add_child(
        joy_node,
        "This surprising outcome fills me with joy and makes me want to celebrate enthusiastically."
    )
    
    dte.add_child(
        anger_node,
        "The disgusting behavior deserves my righteous anger and determined response."
    )
    
    logger.info("Created test tree with DET emotional content")
    
    return dte

def show_det_states(dte):
    """Display DET emotional states for all nodes in the tree"""
    # Map from DETEmotion index to name
    det_emotion_names = [e.name for e in DETEmotion]
    
    # Collect nodes for display
    nodes = []
    queue = [dte.root]
    while queue:
        node = queue.pop(0)
        nodes.append(node)
        queue.extend(node.children)
    
    print("\nDET Emotional States:")
    print("-" * 100)
    print(f"{'Node Content':<40} | {'Active Scripts':<25} | {'Top Behavioral Responses':<30}")
    print("-" * 100)
    
    for node in nodes:
        # Get shortened content
        content = (node.content[:37] + "...") if len(node.content) > 40 else node.content
        
        # Get active scripts
        scripts = ", ".join(node.metadata.get('active_scripts', []))[:25]
        
        # Get behavioral responses
        responses = ", ".join(node.metadata.get('behavioral_responses', []))[:30]
        
        print(f"{content:<40} | {scripts:<25} | {responses:<30}")
    
    print("\nDominant DET Emotions:")
    print("-" * 100)
    print(f"{'Node Content':<40} | {'Top 3 DET Emotions':<40} | {'Echo Value':<10}")
    print("-" * 100)
    
    for node in nodes:
        if node.det_state is None:
            continue
            
        # Get shortened content
        content = (node.content[:37] + "...") if len(node.content) > 40 else node.content
        
        # Get top 3 emotions
        emotion_values = [(i, val) for i, val in enumerate(node.det_state.det_emotions)]
        emotion_values.sort(key=lambda x: x[1], reverse=True)
        top_emotions = [f"{det_emotion_names[i]}:{val:.2f}" for i, val in emotion_values[:3]]
        top_str = ", ".join(top_emotions)
        
        echo = f"{node.echo_value:.3f}"
        
        print(f"{content:<40} | {top_str:<40} | {echo:<10}")

def visualize_det_emotions(dte):
    """Create a visualization of DET emotional states in the tree"""
    # Define colormap for DET emotions (grouped by core emotion categories)
    colors = [
        'gold',      # INTEREST - gold
        'orange',    # EXCITEMENT - orange
        
        'red',       # ANGER - red
        'firebrick', # CONTEMPT - firebrick
        'darkred',   # DISGUST - dark red
        
        'purple',    # FEAR - purple
        'indigo',    # SHAME - indigo
        'slateblue', # SHYNESS - slate blue
        'darkblue',  # GUILT - dark blue
        
        'pink',      # DESIRE - pink
        
        'green',     # LOVE - green
        'lightgreen',# TENDERNESS - light green
        
        'gray',      # DISTRESS - gray
        'darkgray',  # SADNESS - dark gray
        
        'cyan',      # JOY - cyan
        'lightskyblue', # AMUSEMENT - light blue
        'yellow'     # SURPRISE - yellow
    ]
    
    emotion_cmap = LinearSegmentedColormap.from_list('det_emotions', colors, N=17)
    
    # Collect nodes and their DET emotional states
    nodes = []
    labels = []
    det_emotional_states = []
    cognitive_factors = []
    
    queue = [dte.root]
    while queue:
        node = queue.pop(0)
        if node.det_state is not None:
            nodes.append(node)
            # Create short label from content
            content = node.content[:15] + "..." if len(node.content) > 15 else node.content
            labels.append(content)
            det_emotional_states.append(node.det_state.det_emotions)
            
            # Extract cognitive factors
            factor_values = []
            for factor in ['valence', 'arousal', 'control', 'certainty', 'effort', 'attention']:
                factor_values.append(node.det_state.cognitive_factors.get(factor, 0.5))
            cognitive_factors.append(factor_values)
        
        queue.extend(node.children)
    
    # Convert to numpy arrays
    det_emotional_states = np.array(det_emotional_states)
    cognitive_factors = np.array(cognitive_factors)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(18, 10))
    
    # Plot heatmap of DET emotional states
    ax1 = fig.add_subplot(121)
    im = ax1.imshow(det_emotional_states, cmap=emotion_cmap, aspect='auto')
    ax1.set_yticks(np.arange(len(labels)))
    ax1.set_yticklabels(labels)
    ax1.set_xticks(np.arange(17))
    ax1.set_xticklabels([e.name for e in DETEmotion], rotation=90)
    ax1.set_title("DET Emotional State Distribution")
    
    # Add a color bar
    cbar = fig.colorbar(im, ax=ax1)
    cbar.set_label('Intensity')
    
    # Plot cognitive factors
    ax2 = fig.add_subplot(122)
    factor_names = ['Valence', 'Arousal', 'Control', 'Certainty', 'Effort', 'Attention']
    im2 = ax2.imshow(cognitive_factors, cmap='viridis', aspect='auto')
    ax2.set_yticks(np.arange(len(labels)))
    ax2.set_yticklabels(labels)
    ax2.set_xticks(np.arange(len(factor_names)))
    ax2.set_xticklabels(factor_names, rotation=45)
    ax2.set_title("Cognitive Factors")
    
    # Add a color bar
    cbar2 = fig.colorbar(im2, ax=ax2)
    cbar2.set_label('Factor Value')
    
    plt.tight_layout()
    plt.savefig("det_visualization.png")
    logger.info("Saved visualization to det_visualization.png")

def test_emotion_regulation():
    """Test emotion regulation strategies on a node"""
    # Create tree
    dte = create_test_tree()
    
    # First simulate without regulation
    logger.info("Simulating DET dynamics without regulation")
    dte.propagate_det_dynamics()
    
    # Show current states
    print("\n--- BEFORE REGULATION ---")
    show_det_states(dte)
    
    # Find node with highest ANGER
    anger_nodes = dte.find_det_emotional_resonance(DETEmotion.ANGER, threshold=0.3)
    
    if anger_nodes:
        target_node = anger_nodes[0]
        print(f"\nApplying reappraisal regulation to node with high anger:")
        print(f"'{target_node.content}'")
        
        # Apply reappraisal regulation to the anger
        dte.apply_emotion_regulation(
            target_node,
            DETEmotion.ANGER,
            "reappraisal"
        )
        
        # Re-simulate to propagate changes
        dte.propagate_det_dynamics()
        
        # Show updated states
        print("\n--- AFTER REGULATION ---")
        show_det_states(dte)
    
    # Return the tree for further analysis
    return dte

def analyze_scripts_and_behaviors(dte):
    """Analyze emotional scripts and behavioral responses"""
    # Analyze patterns
    analysis = dte.analyze_det_patterns()
    
    print("\nDET Pattern Analysis:")
    print("-" * 80)
    
    # Display dominant DET emotion
    if 'dominant_det_emotion' in analysis:
        print(f"Dominant DET Emotion: {analysis['dominant_det_emotion']}")
    
    # Display active scripts by frequency
    print("\nActive Scripts (by frequency):")
    for script, count in analysis['active_scripts'].items():
        print(f"  {script}: {count}")
    
    # Display behavioral responses by frequency
    print("\nBehavioral Responses (by frequency):")
    for response, count in analysis['behavioral_responses'].items():
        print(f"  {response}: {count}")
    
    # Display average cognitive factors
    print("\nAverage Cognitive Factors:")
    for factor, value in analysis['cognitive_factors'].items():
        print(f"  {factor}: {value:.3f}")
    
    # Display average regulation capacity
    print(f"\nAverage Regulation Capacity: {analysis['regulation_capacity']:.3f}")
    
    # Create script-behavior mapping visualization
    create_script_behavior_network(analysis)

def create_script_behavior_network(analysis):
    """Create a network visualization of scripts and behaviors"""
    try:
        import networkx as nx
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add script nodes
        for script in analysis['active_scripts']:
            G.add_node(script, type='script')
        
        # Add behavior nodes
        for behavior in analysis['behavioral_responses']:
            G.add_node(behavior, type='behavior')
        
        # Add edges from scripts to behaviors
        # This is simplified - in a real implementation we would track which behaviors
        # come from which scripts, but here we'll just connect all scripts to their
        # possible behaviors based on the DifferentialEmotionSystem
        for script, count in analysis['active_scripts'].items():
            # Map common scripts to their typical behaviors
            if script == "Exploration":
                behaviors = ["Approach", "Investigate", "Ask questions"]
            elif script == "Escape":
                behaviors = ["Retreat", "Hide", "Freeze", "Seek safety"]
            elif script == "Attack":
                behaviors = ["Confront", "Remove obstacle", "Express disapproval"]
            elif script == "Celebration":
                behaviors = ["Smile", "Share", "Continue activity", "Express happiness"]
            elif script == "Withdrawal":
                behaviors = ["Withdraw", "Seek comfort", "Reduce activity", "Reflect"]
            elif script == "Attachment":
                behaviors = ["Nurture", "Protect", "Stay close", "Express affection"]
            elif script == "Orientation":
                behaviors = ["Stop", "Orient", "Pay attention", "Reassess"]
            elif script == "Atonement":
                behaviors = ["Apologize", "Hide", "Repair damage", "Self-punishment"]
            else:
                behaviors = []
                
            for behavior in behaviors:
                if behavior in analysis['behavioral_responses']:
                    G.add_edge(script, behavior, weight=count)
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Define positions for nodes
        pos = nx.spring_layout(G, seed=42)  # positions for all nodes
        
        # Draw script nodes
        script_nodes = [node for node, attr in G.nodes(data=True) if attr.get('type') == 'script']
        nx.draw_networkx_nodes(G, pos, nodelist=script_nodes, node_color='lightblue', 
                              node_size=2000, alpha=0.8)
        
        # Draw behavior nodes
        behavior_nodes = [node for node, attr in G.nodes(data=True) if attr.get('type') == 'behavior']
        nx.draw_networkx_nodes(G, pos, nodelist=behavior_nodes, node_color='lightgreen', 
                              node_size=1500, alpha=0.8)
        
        # Draw edges
        edges = G.edges(data=True)
        edge_width = [data.get('weight', 1) * 0.5 for _, _, data in edges]
        nx.draw_networkx_edges(G, pos, width=edge_width, alpha=0.5, arrows=True)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos)
        
        plt.title("Emotional Scripts and Behavioral Responses Network")
        plt.axis('off')  # turn off axis
        plt.tight_layout()
        plt.savefig("det_script_behavior_network.png")
        logger.info("Saved script-behavior network to det_script_behavior_network.png")
        
    except ImportError:
        logger.warning("NetworkX not installed. Skipping network visualization.")

def main():
    """Main function to run the DET demonstration"""
    logger.info("Starting Differential Emotion Theory demonstration")
    
    # Create and populate the tree
    dte = create_test_tree()
    
    # Simulate DET dynamics on the tree
    logger.info("Simulating DET dynamics")
    dte.propagate_det_dynamics()
    
    # Show DET states
    show_det_states(dte)
    
    # Visualize DET emotions
    visualize_det_emotions(dte)
    
    # Test emotion regulation
    regulated_dte = test_emotion_regulation()
    
    # Analyze scripts and behaviors
    analyze_scripts_and_behaviors(regulated_dte)
    
    logger.info("Demonstration completed")

if __name__ == "__main__":
    main()