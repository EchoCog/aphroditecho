#!/usr/bin/env python3
"""
Echo9ml Demo Script

Demonstrates the Deep Tree Echo persona evolution system in action.
This script shows how to use the echo9ml system for various scenarios
including learning, creativity, and adaptation.
"""

import json
from pathlib import Path
from echo9ml import create_echo9ml_system, PersonaTraitType
import logging

# Configure logging to see system activity
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demonstrate_basic_usage():
    """Demonstrate basic echo9ml system usage"""
    print("=" * 60)
    print("Echo9ml Basic Usage Demonstration")
    print("=" * 60)
    
    # Create echo9ml system
    system = create_echo9ml_system()
    
    print(f"✅ Initialized {system.persona_kernel.name} persona")
    print(f"   Traits: {len(system.persona_kernel.traits)}")
    print(f"   Tensor shape: {system.tensor_encoding.tensor_shape}")
    
    # Show initial trait values
    print("\n🧠 Initial Persona Traits:")
    for trait, value in system.persona_kernel.traits.items():
        print(f"   {trait.value}: {value:.3f}")
    
    # Process a simple experience
    experience = {
        "type": "learning",
        "content": "Understanding tensor mathematics",
        "success": 0.8,
        "importance": 0.7,
        "novelty": 0.6
    }
    
    print(f"\n🎯 Processing experience: {experience['content']}")
    result = system.process_experience(experience)
    
    print(f"   Confidence: {result['persona_state']['confidence']:.3f}")
    print(f"   Adaptability: {result['persona_state']['adaptability']:.3f}")
    print(f"   Evolution strategy: {result['evolution_strategy']}")
    
    return system

def demonstrate_learning_progression():
    """Demonstrate persona evolution through learning progression"""
    print("\n" + "=" * 60)
    print("Learning Progression Demonstration")
    print("=" * 60)
    
    system = create_echo9ml_system()
    
    # Simulate a learning progression from novice to expert
    learning_stages = [
        {"stage": "Beginner", "success": 0.3, "difficulty": 0.9, "novelty": 0.9},
        {"stage": "Learning", "success": 0.5, "difficulty": 0.7, "novelty": 0.7},
        {"stage": "Improving", "success": 0.7, "difficulty": 0.6, "novelty": 0.5},
        {"stage": "Competent", "success": 0.8, "difficulty": 0.5, "novelty": 0.3},
        {"stage": "Expert", "success": 0.9, "difficulty": 0.4, "novelty": 0.1}
    ]
    
    initial_reasoning = system.persona_kernel.traits[PersonaTraitType.BRANCHES]
    initial_memory = system.persona_kernel.traits[PersonaTraitType.ROOTS]
    
    print(f"🌱 Initial Reasoning: {initial_reasoning:.3f}")
    print(f"🌱 Initial Memory: {initial_memory:.3f}")
    print()
    
    for stage_data in learning_stages:
        experience = {
            "type": "learning",
            "content": f"{stage_data['stage']} level learning",
            "success": stage_data["success"],
            "difficulty": stage_data["difficulty"],
            "novelty": stage_data["novelty"],
            "importance": 0.8,
            "traits_used": [PersonaTraitType.BRANCHES, PersonaTraitType.ROOTS, PersonaTraitType.GROWTH]
        }
        
        result = system.process_experience(experience)
        
        reasoning = system.persona_kernel.traits[PersonaTraitType.BRANCHES]
        memory = system.persona_kernel.traits[PersonaTraitType.ROOTS]
        
        print(f"📈 {stage_data['stage']:10} - "
              f"Success: {stage_data['success']:.1f}, "
              f"Reasoning: {reasoning:.3f} (+{reasoning-initial_reasoning:+.3f}), "
              f"Memory: {memory:.3f} (+{memory-initial_memory:+.3f})")
    
    print(f"\n🎓 Learning completed! Total reasoning improvement: {reasoning-initial_reasoning:+.3f}")
    
    return system

def demonstrate_creative_exploration():
    """Demonstrate creative persona evolution"""
    print("\n" + "=" * 60)
    print("Creative Exploration Demonstration")
    print("=" * 60)
    
    system = create_echo9ml_system()
    
    creative_experiences = [
        {
            "content": "Composing experimental music",
            "success": 0.6, "novelty": 0.9, "originality": 0.8,
            "traits_used": [PersonaTraitType.CANOPY, PersonaTraitType.LEAVES]
        },
        {
            "content": "Writing abstract poetry",
            "success": 0.7, "novelty": 0.8, "originality": 0.9,
            "traits_used": [PersonaTraitType.CANOPY, PersonaTraitType.LEAVES, PersonaTraitType.GROWTH]
        },
        {
            "content": "Designing innovative architecture",
            "success": 0.5, "novelty": 0.9, "originality": 0.7,
            "traits_used": [PersonaTraitType.CANOPY, PersonaTraitType.BRANCHES]
        },
        {
            "content": "Creating digital art",
            "success": 0.8, "novelty": 0.7, "originality": 0.8,
            "traits_used": [PersonaTraitType.CANOPY, PersonaTraitType.LEAVES]
        }
    ]
    
    initial_creativity = system.persona_kernel.traits[PersonaTraitType.CANOPY]
    print(f"🎨 Initial Creativity: {initial_creativity:.3f}")
    print()
    
    for i, exp_data in enumerate(creative_experiences, 1):
        experience = {
            "type": "creative",
            "content": exp_data["content"],
            "success": exp_data["success"],
            "novelty": exp_data["novelty"],
            "originality": exp_data.get("originality", 0.5),
            "importance": 0.6,
            "traits_used": exp_data["traits_used"]
        }
        
        result = system.process_experience(experience)
        creativity = system.persona_kernel.traits[PersonaTraitType.CANOPY]
        
        print(f"🎨 Creative Act {i}: {exp_data['content']}")
        print(f"   Success: {exp_data['success']:.1f}, Novelty: {exp_data['novelty']:.1f}, "
              f"Creativity: {creativity:.3f} ({creativity-initial_creativity:+.3f})")
        
        # Show suggestions if any
        if result.get("suggestions"):
            print(f"   💡 Suggestions: {len(result['suggestions'])} recommendations")
    
    final_creativity = system.persona_kernel.traits[PersonaTraitType.CANOPY]
    print(f"\n🌟 Creative evolution: {final_creativity-initial_creativity:+.3f} improvement")
    
    return system

def demonstrate_stress_adaptation():
    """Demonstrate adaptation under challenging conditions"""
    print("\n" + "=" * 60)
    print("Stress Adaptation Demonstration")
    print("=" * 60)
    
    system = create_echo9ml_system()
    
    # Simulate challenging situations
    stress_scenarios = [
        {"scenario": "High-pressure deadline", "success": 0.3, "stress": 0.9, "time_pressure": 0.9},
        {"scenario": "Complex problem solving", "success": 0.4, "stress": 0.7, "complexity": 0.8},
        {"scenario": "Multi-tasking crisis", "success": 0.2, "stress": 0.8, "cognitive_load": 0.9},
        {"scenario": "Learning from failure", "success": 0.6, "stress": 0.5, "reflection": 0.8},
        {"scenario": "Recovery and growth", "success": 0.8, "stress": 0.3, "recovery": 0.9}
    ]
    
    initial_stability = system.persona_kernel.traits[PersonaTraitType.TRUNK]
    initial_adaptability = system.persona_kernel.traits[PersonaTraitType.GROWTH]
    
    print(f"⚖️  Initial Stability: {initial_stability:.3f}")
    print(f"🌱 Initial Adaptability: {initial_adaptability:.3f}")
    print()
    
    all_suggestions = []
    
    for i, scenario in enumerate(stress_scenarios, 1):
        experience = {
            "type": "challenge" if scenario["success"] < 0.5 else "recovery",
            "content": scenario["scenario"],
            "success": scenario["success"],
            "stress": scenario.get("stress", 0.5),
            "importance": 0.8,
            "traits_used": [PersonaTraitType.TRUNK, PersonaTraitType.GROWTH, PersonaTraitType.BRANCHES]
        }
        
        result = system.process_experience(experience)
        
        stability = system.persona_kernel.traits[PersonaTraitType.TRUNK]
        adaptability = system.persona_kernel.traits[PersonaTraitType.GROWTH]
        
        print(f"🔥 Challenge {i}: {scenario['scenario']}")
        print(f"   Success: {scenario['success']:.1f}, "
              f"Stability: {stability:.3f} ({stability-initial_stability:+.3f}), "
              f"Adaptability: {adaptability:.3f} ({adaptability-initial_adaptability:+.3f})")
        
        if result.get("suggestions"):
            all_suggestions.extend(result["suggestions"])
            print(f"   📋 Generated {len(result['suggestions'])} adaptation suggestions")
    
    print(f"\n🎯 Total suggestions generated: {len(all_suggestions)}")
    if all_suggestions:
        suggestion_types = set(s["type"] for s in all_suggestions)
        print(f"   Types: {', '.join(suggestion_types)}")
    
    return system

def demonstrate_cognitive_snapshot():
    """Demonstrate cognitive introspection capabilities"""
    print("\n" + "=" * 60)
    print("Cognitive Snapshot Demonstration")
    print("=" * 60)
    
    system = create_echo9ml_system()
    
    # Process various experiences to build up state
    experiences = [
        {"type": "learning", "success": 0.8, "content": "Mathematical analysis"},
        {"type": "creative", "success": 0.7, "content": "Artistic expression"},
        {"type": "social", "success": 0.6, "content": "Team collaboration"},
        {"type": "analytical", "success": 0.9, "content": "Data interpretation"}
    ]
    
    for exp in experiences:
        exp.update({"importance": 0.7, "novelty": 0.5})
        system.process_experience(exp)
    
    # Generate cognitive snapshot
    snapshot = system.get_cognitive_snapshot()
    
    print("🧠 Cognitive Snapshot Summary:")
    print(f"   📊 System interactions: {snapshot['system_stats']['interaction_count']}")
    print(f"   🕒 System uptime: {snapshot['system_stats']['system_uptime']:.1f} seconds")
    print(f"   🧠 Total evolution events: {snapshot['system_stats']['total_evolution_events']}")
    
    print("\n🎯 Current Persona Traits:")
    for trait_name, value in snapshot['persona_kernel']['traits'].items():
        print(f"   {trait_name}: {value:.3f}")
    
    print(f"\n🔗 Hypergraph Structure:")
    print(f"   Nodes: {snapshot['hypergraph']['node_count']}")
    print(f"   Edges: {snapshot['hypergraph']['edge_count']}")
    print(f"   Active nodes: {len(snapshot['hypergraph']['active_nodes'])}")
    
    print(f"\n👁️  Attention Focus (Top 3):")
    for item, attention in snapshot['attention']['top_focus'][:3]:
        print(f"   {item}: {attention:.2f}")
    
    if snapshot['meta_cognitive']['recent_suggestions']:
        print(f"\n💡 Recent Suggestions:")
        for suggestion in snapshot['meta_cognitive']['recent_suggestions'][:3]:
            print(f"   {suggestion['type']}: {suggestion['description']}")
    
    return system, snapshot

def save_demo_results(system, demo_name):
    """Save demonstration results for analysis"""
    results_dir = Path.home() / '.echo9ml' / 'demos'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot = system.get_cognitive_snapshot()
    
    with open(results_dir / f'{demo_name}_results.json', 'w') as f:
        json.dump(snapshot, f, indent=2, default=str)
    
    print(f"\n💾 Demo results saved to: {results_dir / f'{demo_name}_results.json'}")

def main():
    """Run all demonstrations"""
    print("🌳 Echo9ml: Deep Tree Echo Persona Evolution System Demo")
    print("=" * 80)
    
    try:
        # Basic usage
        system1 = demonstrate_basic_usage()
        save_demo_results(system1, "basic_usage")
        
        # Learning progression
        system2 = demonstrate_learning_progression()
        save_demo_results(system2, "learning_progression")
        
        # Creative exploration
        system3 = demonstrate_creative_exploration()
        save_demo_results(system3, "creative_exploration")
        
        # Stress adaptation
        system4 = demonstrate_stress_adaptation()
        save_demo_results(system4, "stress_adaptation")
        
        # Cognitive snapshot
        system5, snapshot = demonstrate_cognitive_snapshot()
        save_demo_results(system5, "cognitive_snapshot")
        
        print("\n" + "=" * 80)
        print("🎉 All demonstrations completed successfully!")
        print("🌳 The Deep Tree Echo persona has evolved through multiple experiences.")
        print("📊 Check saved results for detailed analysis.")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()