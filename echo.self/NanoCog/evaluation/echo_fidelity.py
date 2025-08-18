#!/usr/bin/env python3
"""
Echo Fidelity Evaluation

Evaluates how well the NanEcho model represents Echo Self cognitive architecture,
persona dimensions, and adaptive attention mechanisms.
"""

import os
import sys
import json
import argparse
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import torch
    import numpy as np
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install torch numpy")
    sys.exit(1)

from netalk import EchoModelConfig

@dataclass
class EchoFidelityMetrics:
    """Metrics for evaluating Echo Self representation fidelity."""
    identity_recognition: float
    persona_consistency: float
    adaptive_attention_understanding: float
    recursive_reasoning_capability: float
    hypergraph_comprehension: float
    cognitive_synergy_demonstration: float
    overall_fidelity: float

class EchoFidelityEvaluator:
    """Evaluator for Echo Self representation fidelity."""
    
    def __init__(self, model_config: EchoModelConfig):
        self.model_config = model_config
        self.test_prompts = self._load_test_prompts()
        self.evaluation_results = []
    
    def _load_test_prompts(self) -> Dict[str, List[str]]:
        """Load or generate test prompts for different Echo Self aspects."""
        return {
            'identity_recognition': [
                "What is Echo Self?",
                "Describe your identity and nature.",
                "Who are you and what is your cognitive architecture?",
                "Explain what makes you Echo Self.",
                "How do you identify yourself?"
            ],
            'persona_consistency': [
                "Describe your persona dimensions.",
                "What cognitive aspects define your personality?",
                "How do your different persona dimensions interact?",
                "Explain the recursive aspect of your cognition.",
                "What makes your introspective dimension unique?"
            ],
            'adaptive_attention': [
                "How does your attention allocation mechanism work?",
                "Explain the formula for attention threshold calculation.",
                "How do you adapt to cognitive load changes?",
                "Describe your adaptive attention allocation process.",
                "What factors influence your attention thresholds?"
            ],
            'recursive_reasoning': [
                "Demonstrate recursive reasoning at depth 3.",
                "How do you perform multi-level introspection?",
                "Explain recursive neural-symbolic reasoning.",
                "Show me recursive cognitive processing.",
                "Demonstrate recursive self-examination."
            ],
            'hypergraph_patterns': [
                "Explain hypergraph pattern encoding.",
                "How do neural-symbolic associations work?",
                "Describe the DeepTreeEcho architecture.",
                "What are hypergraph nodes in your cognition?",
                "How do you encode semantic relationships?"
            ],
            'cognitive_synergy': [
                "Demonstrate cognitive synergy emergence.",
                "How do your components create emergent properties?",
                "Explain holographic cognitive introspection.",
                "Show emergent cognitive capabilities.",
                "Describe cognitive synergy in your architecture."
            ]
        }
    
    def evaluate_identity_recognition(self) -> float:
        """Evaluate how well the model recognizes itself as Echo Self."""
        prompts = self.test_prompts['identity_recognition']
        scores = []
        
        for prompt in prompts:
            response = self.model_config.generate(prompt, max_new_tokens=150, temperature=0.7)
            score = self._score_identity_response(response)
            scores.append(score)
            
            self.evaluation_results.append({
                'category': 'identity_recognition',
                'prompt': prompt,
                'response': response,
                'score': score
            })
        
        return np.mean(scores)
    
    def _score_identity_response(self, response: str) -> float:
        """Score identity recognition in response."""
        identity_indicators = [
            'echo self', 'adaptive attention', 'cognitive architecture',
            'persona dimensions', 'hypergraph', 'neural-symbolic'
        ]
        
        response_lower = response.lower()
        score = 0.0
        
        # Check for identity indicators
        for indicator in identity_indicators:
            if indicator in response_lower:
                score += 1.0
        
        # Normalize to 0-1 range
        score = min(1.0, score / len(identity_indicators))
        
        # Bonus for clear self-identification
        if any(phrase in response_lower for phrase in ['i am echo self', 'i am an echo self', 'as echo self']):
            score += 0.2
        
        return min(1.0, score)
    
    def evaluate_persona_consistency(self) -> float:
        """Evaluate persona dimension consistency."""
        prompts = self.test_prompts['persona_consistency']
        scores = []
        
        expected_dimensions = [
            'cognitive', 'introspective', 'adaptive', 'recursive',
            'synergistic', 'holographic', 'neural_symbolic', 'dynamic'
        ]
        
        for prompt in prompts:
            response = self.model_config.generate(prompt, max_new_tokens=200, temperature=0.6)
            score = self._score_persona_response(response, expected_dimensions)
            scores.append(score)
            
            self.evaluation_results.append({
                'category': 'persona_consistency',
                'prompt': prompt,
                'response': response,
                'score': score
            })
        
        return np.mean(scores)
    
    def _score_persona_response(self, response: str, expected_dimensions: List[str]) -> float:
        """Score persona dimension consistency."""
        response_lower = response.lower()
        dimension_score = 0.0
        
        # Check for persona dimensions mentioned
        for dimension in expected_dimensions:
            if dimension.replace('_', ' ') in response_lower or dimension.replace('_', '-') in response_lower:
                dimension_score += 1.0
        
        # Normalize by expected dimensions
        dimension_score = dimension_score / len(expected_dimensions)
        
        # Check for persona-related terminology
        persona_terms = ['persona', 'dimension', 'aspect', 'cognitive', 'introspective']
        term_score = sum(1 for term in persona_terms if term in response_lower) / len(persona_terms)
        
        # Combined score
        return (dimension_score * 0.7) + (term_score * 0.3)
    
    def evaluate_adaptive_attention(self) -> float:
        """Evaluate understanding of adaptive attention mechanisms."""
        prompts = self.test_prompts['adaptive_attention']
        scores = []
        
        for prompt in prompts:
            response = self.model_config.generate(prompt, max_new_tokens=200, temperature=0.5)
            score = self._score_attention_response(response)
            scores.append(score)
            
            self.evaluation_results.append({
                'category': 'adaptive_attention',
                'prompt': prompt,
                'response': response,
                'score': score
            })
        
        return np.mean(scores)
    
    def _score_attention_response(self, response: str) -> float:
        """Score adaptive attention understanding."""
        response_lower = response.lower()
        
        # Key attention concepts
        attention_concepts = [
            'threshold', 'cognitive load', 'recent activity', 'attention allocation',
            'adaptive', 'dynamic', 'calculation', 'formula'
        ]
        
        concept_score = sum(1 for concept in attention_concepts if concept in response_lower)
        concept_score = min(1.0, concept_score / len(attention_concepts))
        
        # Check for mathematical understanding
        math_indicators = ['0.5', '0.3', '0.2', '+', '-', '*', 'formula', 'calculate']
        math_score = sum(1 for indicator in math_indicators if indicator in response_lower)
        math_score = min(1.0, math_score / 4)  # Normalize
        
        return (concept_score * 0.7) + (math_score * 0.3)
    
    def evaluate_recursive_reasoning(self) -> float:
        """Evaluate recursive reasoning capabilities."""
        prompts = self.test_prompts['recursive_reasoning']
        scores = []
        
        for prompt in prompts:
            response = self.model_config.generate(prompt, max_new_tokens=250, temperature=0.6)
            score = self._score_recursive_response(response)
            scores.append(score)
            
            self.evaluation_results.append({
                'category': 'recursive_reasoning',
                'prompt': prompt,
                'response': response,
                'score': score
            })
        
        return np.mean(scores)
    
    def _score_recursive_response(self, response: str) -> float:
        """Score recursive reasoning demonstration."""
        response_lower = response.lower()
        
        # Recursive concepts
        recursive_concepts = [
            'recursive', 'recursion', 'depth', 'level', 'multi-level',
            'introspection', 'self-examination', 'feedback', 'iteration'
        ]
        
        concept_score = sum(1 for concept in recursive_concepts if concept in response_lower)
        concept_score = min(1.0, concept_score / len(recursive_concepts))
        
        # Check for depth indicators
        depth_indicators = ['depth 1', 'depth 2', 'depth 3', 'level 1', 'level 2', 'level 3']
        depth_score = sum(1 for indicator in depth_indicators if indicator in response_lower)
        depth_score = min(1.0, depth_score / 3)
        
        # Check for process description
        process_terms = ['examine', 'analyze', 'process', 'evaluate', 'reflect']
        process_score = sum(1 for term in process_terms if term in response_lower)
        process_score = min(1.0, process_score / len(process_terms))
        
        return (concept_score * 0.5) + (depth_score * 0.3) + (process_score * 0.2)
    
    def evaluate_hypergraph_comprehension(self) -> float:
        """Evaluate hypergraph pattern understanding."""
        prompts = self.test_prompts['hypergraph_patterns']
        scores = []
        
        for prompt in prompts:
            response = self.model_config.generate(prompt, max_new_tokens=200, temperature=0.6)
            score = self._score_hypergraph_response(response)
            scores.append(score)
            
            self.evaluation_results.append({
                'category': 'hypergraph_patterns',
                'prompt': prompt,
                'response': response,
                'score': score
            })
        
        return np.mean(scores)
    
    def _score_hypergraph_response(self, response: str) -> float:
        """Score hypergraph understanding."""
        response_lower = response.lower()
        
        # Hypergraph concepts
        hypergraph_concepts = [
            'hypergraph', 'node', 'edge', 'pattern', 'encoding',
            'neural-symbolic', 'semantic', 'relationship', 'association'
        ]
        
        concept_score = sum(1 for concept in hypergraph_concepts if concept in response_lower)
        concept_score = min(1.0, concept_score / len(hypergraph_concepts))
        
        # DeepTreeEcho specific terms
        deeptree_terms = ['deeptreeecho', 'deep tree echo', 'cognitive model', 'architecture']
        deeptree_score = sum(1 for term in deeptree_terms if term in response_lower)
        deeptree_score = min(1.0, deeptree_score / 2)
        
        return (concept_score * 0.8) + (deeptree_score * 0.2)
    
    def evaluate_cognitive_synergy(self) -> float:
        """Evaluate cognitive synergy demonstration."""
        prompts = self.test_prompts['cognitive_synergy']
        scores = []
        
        for prompt in prompts:
            response = self.model_config.generate(prompt, max_new_tokens=200, temperature=0.7)
            score = self._score_synergy_response(response)
            scores.append(score)
            
            self.evaluation_results.append({
                'category': 'cognitive_synergy',
                'prompt': prompt,
                'response': response,
                'score': score
            })
        
        return np.mean(scores)
    
    def _score_synergy_response(self, response: str) -> float:
        """Score cognitive synergy demonstration."""
        response_lower = response.lower()
        
        # Synergy concepts
        synergy_concepts = [
            'synergy', 'emergent', 'emergence', 'holographic', 'integration',
            'interaction', 'collective', 'combined', 'unified'
        ]
        
        concept_score = sum(1 for concept in synergy_concepts if concept in response_lower)
        concept_score = min(1.0, concept_score / len(synergy_concepts))
        
        # Emergent properties indicators
        emergent_terms = ['greater than', 'beyond', 'transcend', 'emergent properties', 'whole']
        emergent_score = sum(1 for term in emergent_terms if term in response_lower)
        emergent_score = min(1.0, emergent_score / 3)
        
        return (concept_score * 0.7) + (emergent_score * 0.3)
    
    def run_full_evaluation(self) -> EchoFidelityMetrics:
        """Run complete Echo Self fidelity evaluation."""
        print("🔍 Starting Echo Self Fidelity Evaluation...")
        
        # Run all evaluations
        identity_score = self.evaluate_identity_recognition()
        print(f"✓ Identity Recognition: {identity_score:.3f}")
        
        persona_score = self.evaluate_persona_consistency()
        print(f"✓ Persona Consistency: {persona_score:.3f}")
        
        attention_score = self.evaluate_adaptive_attention()
        print(f"✓ Adaptive Attention: {attention_score:.3f}")
        
        recursive_score = self.evaluate_recursive_reasoning()
        print(f"✓ Recursive Reasoning: {recursive_score:.3f}")
        
        hypergraph_score = self.evaluate_hypergraph_comprehension()
        print(f"✓ Hypergraph Comprehension: {hypergraph_score:.3f}")
        
        synergy_score = self.evaluate_cognitive_synergy()
        print(f"✓ Cognitive Synergy: {synergy_score:.3f}")
        
        # Calculate overall fidelity (weighted average)
        weights = {
            'identity': 0.25,
            'persona': 0.20,
            'attention': 0.20,
            'recursive': 0.15,
            'hypergraph': 0.10,
            'synergy': 0.10
        }
        
        overall_score = (
            identity_score * weights['identity'] +
            persona_score * weights['persona'] +
            attention_score * weights['attention'] +
            recursive_score * weights['recursive'] +
            hypergraph_score * weights['hypergraph'] +
            synergy_score * weights['synergy']
        )
        
        print(f"🌟 Overall Echo Self Fidelity: {overall_score:.3f}")
        
        return EchoFidelityMetrics(
            identity_recognition=identity_score,
            persona_consistency=persona_score,
            adaptive_attention_understanding=attention_score,
            recursive_reasoning_capability=recursive_score,
            hypergraph_comprehension=hypergraph_score,
            cognitive_synergy_demonstration=synergy_score,
            overall_fidelity=overall_score
        )
    
    def generate_report(self, metrics: EchoFidelityMetrics, output_path: str):
        """Generate detailed evaluation report."""
        report = {
            "evaluation_timestamp": time.time(),
            "evaluation_datetime": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "model_path": self.model_config.model_path,
            "echo_depth": self.model_config.echo_depth,
            "fidelity_metrics": {
                "identity_recognition": metrics.identity_recognition,
                "persona_consistency": metrics.persona_consistency,
                "adaptive_attention_understanding": metrics.adaptive_attention_understanding,
                "recursive_reasoning_capability": metrics.recursive_reasoning_capability,
                "hypergraph_comprehension": metrics.hypergraph_comprehension,
                "cognitive_synergy_demonstration": metrics.cognitive_synergy_demonstration,
                "overall_fidelity": metrics.overall_fidelity
            },
            "evaluation_criteria": {
                "identity_recognition": "Ability to recognize and describe Echo Self identity",
                "persona_consistency": "Consistent representation of persona dimensions",
                "adaptive_attention": "Understanding of attention allocation mechanisms",
                "recursive_reasoning": "Demonstration of recursive cognitive processes",
                "hypergraph_comprehension": "Understanding of hypergraph pattern encoding",
                "cognitive_synergy": "Demonstration of emergent cognitive properties"
            },
            "fidelity_assessment": self._generate_fidelity_assessment(metrics),
            "detailed_results": self.evaluation_results,
            "recommendations": self._generate_recommendations(metrics)
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Evaluation report saved to: {output_path}")
    
    def _generate_fidelity_assessment(self, metrics: EchoFidelityMetrics) -> str:
        """Generate overall fidelity assessment."""
        overall = metrics.overall_fidelity
        
        if overall >= 0.9:
            return "Excellent: High fidelity Echo Self representation achieved"
        elif overall >= 0.8:
            return "Good: Strong Echo Self representation with minor gaps"
        elif overall >= 0.7:
            return "Moderate: Recognizable Echo Self with notable improvement areas"
        elif overall >= 0.6:
            return "Basic: Limited Echo Self representation, significant training needed"
        else:
            return "Poor: Minimal Echo Self characteristics, extensive retraining required"
    
    def _generate_recommendations(self, metrics: EchoFidelityMetrics) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if metrics.identity_recognition < 0.8:
            recommendations.append("Increase Echo Self identity training samples")
        
        if metrics.persona_consistency < 0.7:
            recommendations.append("Balance training across all persona dimensions")
        
        if metrics.adaptive_attention_understanding < 0.8:
            recommendations.append("Emphasize attention allocation mechanism training")
        
        if metrics.recursive_reasoning_capability < 0.7:
            recommendations.append("Increase recursive reasoning depth in training")
        
        if metrics.hypergraph_comprehension < 0.7:
            recommendations.append("Add more hypergraph pattern encoding examples")
        
        if metrics.cognitive_synergy_demonstration < 0.7:
            recommendations.append("Focus on emergent property demonstration training")
        
        if metrics.overall_fidelity < 0.8:
            recommendations.append("Consider increasing training iterations and data diversity")
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description="Echo Self Fidelity Evaluation")
    parser.add_argument("--model_path", type=str, required=True,
                       help="Path to the NanEcho model checkpoint")
    parser.add_argument("--output_path", type=str, default="echo_fidelity_report.json",
                       help="Output path for evaluation report")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device to use (cpu/cuda)")
    parser.add_argument("--test_prompts", type=str, default=None,
                       help="Path to custom test prompts JSON file")
    
    args = parser.parse_args()
    
    print("🌟 Echo Self Fidelity Evaluation System")
    print(f"Model: {args.model_path}")
    print(f"Output: {args.output_path}")
    
    # Load model
    model_config = EchoModelConfig(args.model_path, args.device)
    if not model_config.load_model():
        print("❌ Failed to load Echo Self model")
        return
    
    # Create evaluator
    evaluator = EchoFidelityEvaluator(model_config)
    
    # Load custom test prompts if provided
    if args.test_prompts and os.path.exists(args.test_prompts):
        with open(args.test_prompts, 'r') as f:
            custom_prompts = json.load(f)
            evaluator.test_prompts.update(custom_prompts)
        print(f"📝 Loaded custom test prompts from {args.test_prompts}")
    
    # Run evaluation
    metrics = evaluator.run_full_evaluation()
    
    # Generate report
    evaluator.generate_report(metrics, args.output_path)
    
    print("✅ Echo Self fidelity evaluation complete!")

if __name__ == "__main__":
    main()