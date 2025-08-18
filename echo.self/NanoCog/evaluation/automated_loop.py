#!/usr/bin/env python3
"""
NanoCog Automated Evaluation Loop

This script implements continuous evaluation and feedback for NanoCog training,
providing automated assessment of model performance and adaptive curriculum adjustment.
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Add NanoCog to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import NanoCogEvaluator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation_loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedEvaluationLoop:
    """
    Automated evaluation loop for continuous NanoCog assessment and improvement.
    
    Monitors training progress, evaluates model performance, detects bottlenecks,
    and provides feedback for curriculum adjustment and training optimization.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the automated evaluation loop.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.evaluator = NanoCogEvaluator(self.config.get('evaluation', {}))
        self.evaluation_history = []
        self.performance_trends = {}
        self.running = False
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load evaluation loop configuration."""
        default_config = {
            "evaluation": {
                "interval_minutes": 30,
                "sample_size": 50,
                "performance_window": 10,
                "improvement_threshold": 0.05,
                "bottleneck_threshold": 0.3
            },
            "model": {
                "checkpoint_dir": "out-nanocog-cogprime",
                "generation_config": {
                    "max_new_tokens": 200,
                    "temperature": 0.8,
                    "top_k": 40
                }
            },
            "feedback": {
                "enable_curriculum_adjustment": True,
                "enable_synthetic_generation": True,
                "enable_performance_alerts": True
            },
            "paths": {
                "evaluation_results": "evaluation_results",
                "training_data": "data",
                "feedback_samples": "feedback_samples"
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge configurations
                self._deep_update(default_config, user_config)
        
        return default_config
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Recursively update nested dictionaries."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def start_evaluation_loop(self):
        """Start the automated evaluation loop."""
        logger.info("Starting automated evaluation loop...")
        self.running = True
        
        # Create necessary directories
        os.makedirs(self.config["paths"]["evaluation_results"], exist_ok=True)
        os.makedirs(self.config["paths"]["feedback_samples"], exist_ok=True)
        
        evaluation_count = 0
        last_evaluation = datetime.now()
        
        while self.running:
            try:
                current_time = datetime.now()
                interval = timedelta(minutes=self.config["evaluation"]["interval_minutes"])
                
                if current_time - last_evaluation >= interval:
                    logger.info(f"Running evaluation #{evaluation_count + 1}")
                    
                    # Run evaluation cycle
                    self._run_evaluation_cycle(evaluation_count)
                    
                    evaluation_count += 1
                    last_evaluation = current_time
                    
                    # Check for performance trends and bottlenecks
                    self._analyze_performance_trends()
                    
                    # Generate feedback if enabled
                    if self.config["feedback"]["enable_curriculum_adjustment"]:
                        self._generate_curriculum_feedback()
                    
                    if self.config["feedback"]["enable_synthetic_generation"]:
                        self._generate_synthetic_samples()
                
                # Sleep for a short period to avoid busy waiting
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("Evaluation loop interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in evaluation loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
        
        self.running = False
        logger.info("Evaluation loop stopped")
    
    def stop_evaluation_loop(self):
        """Stop the automated evaluation loop."""
        logger.info("Stopping evaluation loop...")
        self.running = False
    
    def _run_evaluation_cycle(self, cycle_number: int):
        """Run a single evaluation cycle."""
        try:
            # Generate samples from current model
            generated_samples = self._generate_evaluation_samples()
            
            if not generated_samples:
                logger.warning("No samples generated for evaluation")
                return
            
            # Load reference corpus
            reference_corpus = self._load_reference_corpus()
            
            # Get current AtomSpace state (mock for now)
            atomspace_state = self._get_atomspace_state()
            
            # Run comprehensive evaluation
            results = self.evaluator.evaluate_model_generation(
                generated_samples, reference_corpus, atomspace_state
            )
            
            # Add cycle metadata
            results["cycle_number"] = cycle_number
            results["cycle_timestamp"] = datetime.now().isoformat()
            
            # Store results
            self.evaluation_history.append(results)
            
            # Save results
            self._save_evaluation_results(results, cycle_number)
            
            # Log summary
            self._log_evaluation_summary(results)
            
        except Exception as e:
            logger.error(f"Error in evaluation cycle {cycle_number}: {e}")
    
    def _generate_evaluation_samples(self) -> List[str]:
        """Generate samples from the current model for evaluation."""
        try:
            # Mock sample generation - in real implementation, this would
            # load the latest checkpoint and generate samples
            
            sample_size = self.config["evaluation"]["sample_size"]
            
            # For now, generate mock samples that simulate model output
            mock_samples = []
            
            prompts = [
                "Explain the CogPrime cognitive architecture:",
                "Generate Atomese code for goal-oriented behavior:",
                "Analyze potential bottlenecks in attention allocation:",
                "Create a cognitive schematic for learning:",
                "Describe ECAN attention dynamics:",
                "Generate PLN inference rules:",
                "Create MOSES fitness evaluation code:",
                "Analyze hypergraph connectivity patterns:",
                "Generate diagnostic recommendations:",
                "Create cross-domain integration examples:"
            ]
            
            for i in range(sample_size):
                prompt = prompts[i % len(prompts)]
                
                # Mock generated response
                mock_response = f"""
{prompt}

;; Generated Atomese/Scheme code
(ImplicationLink (stv 0.8 0.9)
  (EvaluationLink (PredicateNode "context-active") (VariableNode "$X"))
  (ExecutionLink (SchemaNode "respond-appropriately") (VariableNode "$X")))

(define cognitive-schematic-{i}
  (lambda (context goal)
    (let ((attention-value (get-sti context)))
      (if (> attention-value 0.5)
          (execute-procedure goal)
          (increase-attention context)))))

;; ECAN attention allocation
(set-sti! (ConceptNode "important-concept-{i}") 0.7)
(set-lti! (ConceptNode "memory-pattern-{i}") 0.6)
"""
                mock_samples.append(mock_response.strip())
            
            logger.info(f"Generated {len(mock_samples)} evaluation samples")
            return mock_samples
            
        except Exception as e:
            logger.error(f"Error generating evaluation samples: {e}")
            return []
    
    def _load_reference_corpus(self) -> List[str]:
        """Load reference corpus for comparison."""
        try:
            corpus_path = os.path.join(self.config["paths"]["training_data"], "reference_corpus.txt")
            
            if os.path.exists(corpus_path):
                with open(corpus_path, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            else:
                # Return mock reference corpus
                return [
                    "(ConceptNode \"basic-concept\")",
                    "(ImplicationLink (stv 0.9 0.8) ...)",
                    "(define example-function (lambda (x) ...))",
                    "(set-sti! (ConceptNode \"example\") 0.5)"
                ]
        except Exception as e:
            logger.error(f"Error loading reference corpus: {e}")
            return []
    
    def _get_atomspace_state(self) -> Dict[str, Any]:
        """Get current AtomSpace state for evaluation."""
        # Mock AtomSpace state - in real implementation, this would
        # connect to actual AtomSpace instance
        return {
            "timestamp": datetime.now().isoformat(),
            "atom_count": 15000,
            "active_goals": [
                {"name": "goal1", "sti": 0.8, "priority": 5},
                {"name": "goal2", "sti": 0.6, "priority": 3}
            ],
            "attention_distribution": {
                "high_sti_count": 150,
                "medium_sti_count": 500,
                "low_sti_count": 2000
            },
            "bottlenecks": [
                {"type": "attention_concentration", "severity": "medium"},
                {"type": "goal_proliferation", "severity": "low"}
            ]
        }
    
    def _save_evaluation_results(self, results: Dict[str, Any], cycle_number: int):
        """Save evaluation results to files."""
        try:
            # Save to evaluation results directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON results
            json_filename = f"evaluation_cycle_{cycle_number:03d}_{timestamp}.json"
            json_path = os.path.join(self.config["paths"]["evaluation_results"], json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Human-readable report
            report_filename = f"evaluation_report_{cycle_number:03d}_{timestamp}.txt"
            report_path = os.path.join(self.config["paths"]["evaluation_results"], report_filename)
            
            self.evaluator.generate_evaluation_report(results, report_path)
            
            logger.info(f"Evaluation results saved: {json_filename}")
            
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")
    
    def _log_evaluation_summary(self, results: Dict[str, Any]):
        """Log a summary of evaluation results."""
        try:
            metrics = results.get("evaluation_metrics", {})
            overall = results.get("overall_performance", {})
            
            logger.info("Evaluation Summary:")
            logger.info(f"  Overall Score: {overall.get('overall_score', 0):.3f}")
            logger.info(f"  Performance Level: {overall.get('performance_level', 'unknown')}")
            
            if "symbolic_accuracy" in metrics:
                sa = metrics["symbolic_accuracy"]
                logger.info(f"  Syntax Accuracy: {sa.get('syntax_accuracy', 0):.3f}")
                logger.info(f"  Semantic Accuracy: {sa.get('semantic_accuracy', 0):.3f}")
            
            if "emergent_patterns" in metrics:
                ep = metrics["emergent_patterns"]
                logger.info(f"  Novelty Rate: {ep.get('novelty_rate', 0):.3f}")
            
            if "cross_domain_integration" in metrics:
                cdi = metrics["cross_domain_integration"]
                logger.info(f"  Domain Coverage: {cdi.get('domain_coverage', 0):.3f}")
            
        except Exception as e:
            logger.error(f"Error logging evaluation summary: {e}")
    
    def _analyze_performance_trends(self):
        """Analyze performance trends across evaluation cycles."""
        if len(self.evaluation_history) < 2:
            return
        
        try:
            window_size = self.config["evaluation"]["performance_window"]
            recent_evaluations = self.evaluation_history[-window_size:]
            
            # Extract performance metrics
            performance_metrics = {}
            
            for eval_result in recent_evaluations:
                overall = eval_result.get("overall_performance", {})
                score = overall.get("overall_score", 0)
                
                timestamp = eval_result.get("timestamp", "")
                performance_metrics[timestamp] = score
            
            # Calculate trend
            if len(performance_metrics) >= 2:
                scores = list(performance_metrics.values())
                
                # Simple trend calculation (slope of recent scores)
                if len(scores) >= 3:
                    recent_trend = (scores[-1] - scores[-3]) / 2
                else:
                    recent_trend = scores[-1] - scores[-2]
                
                self.performance_trends["recent_slope"] = recent_trend
                self.performance_trends["current_score"] = scores[-1]
                self.performance_trends["score_history"] = scores
                
                # Log trend analysis
                if recent_trend > self.config["evaluation"]["improvement_threshold"]:
                    logger.info(f"Performance improving: +{recent_trend:.3f}")
                elif recent_trend < -self.config["evaluation"]["improvement_threshold"]:
                    logger.warning(f"Performance declining: {recent_trend:.3f}")
                else:
                    logger.info(f"Performance stable: {recent_trend:.3f}")
        
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
    
    def _generate_curriculum_feedback(self):
        """Generate curriculum adjustment recommendations."""
        try:
            if not self.evaluation_history:
                return
            
            latest_eval = self.evaluation_history[-1]
            metrics = latest_eval.get("evaluation_metrics", {})
            
            feedback = {
                "timestamp": datetime.now().isoformat(),
                "recommendations": []
            }
            
            # Analyze symbolic accuracy
            if "symbolic_accuracy" in metrics:
                sa = metrics["symbolic_accuracy"]
                syntax_acc = sa.get("syntax_accuracy", 0)
                semantic_acc = sa.get("semantic_accuracy", 0)
                
                if syntax_acc < 0.8:
                    feedback["recommendations"].append({
                        "type": "curriculum_emphasis",
                        "area": "basic_atomese",
                        "reason": f"Syntax accuracy low: {syntax_acc:.3f}",
                        "action": "Increase basic Atomese syntax examples",
                        "weight_adjustment": 1.5
                    })
                
                if semantic_acc < 0.7:
                    feedback["recommendations"].append({
                        "type": "curriculum_emphasis",
                        "area": "cognitive_primitives",
                        "reason": f"Semantic accuracy low: {semantic_acc:.3f}",
                        "action": "Add more cognitive schematic examples",
                        "weight_adjustment": 1.3
                    })
            
            # Analyze emergent patterns
            if "emergent_patterns" in metrics:
                ep = metrics["emergent_patterns"]
                novelty_rate = ep.get("novelty_rate", 0)
                
                if novelty_rate < 0.05:
                    feedback["recommendations"].append({
                        "type": "training_adjustment",
                        "area": "creativity",
                        "reason": f"Low novelty rate: {novelty_rate:.3f}",
                        "action": "Increase temperature and diversity in training",
                        "parameter_adjustment": {"temperature": 0.9, "top_k": 50}
                    })
            
            # Save feedback
            if feedback["recommendations"]:
                feedback_path = os.path.join(
                    self.config["paths"]["feedback_samples"],
                    f"curriculum_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                with open(feedback_path, 'w', encoding='utf-8') as f:
                    json.dump(feedback, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Generated {len(feedback['recommendations'])} curriculum recommendations")
            
        except Exception as e:
            logger.error(f"Error generating curriculum feedback: {e}")
    
    def _generate_synthetic_samples(self):
        """Generate synthetic training samples based on performance gaps."""
        try:
            if not self.evaluation_history:
                return
            
            latest_eval = self.evaluation_history[-1]
            metrics = latest_eval.get("evaluation_metrics", {})
            
            synthetic_samples = []
            
            # Generate samples for weak areas
            if "symbolic_accuracy" in metrics:
                sa = metrics["symbolic_accuracy"]
                if sa.get("syntax_accuracy", 0) < 0.8:
                    # Generate basic syntax examples
                    basic_examples = [
                        "(ConceptNode \"learning-target\")",
                        "(PredicateNode \"knowledge-relation\")",
                        "(EvaluationLink (PredicateNode \"example\") (ListLink (ConceptNode \"A\") (ConceptNode \"B\")))",
                        "(InheritanceLink (ConceptNode \"specific\") (ConceptNode \"general\"))"
                    ]
                    synthetic_samples.extend(basic_examples)
            
            if "cross_domain_integration" in metrics:
                cdi = metrics["cross_domain_integration"]
                if cdi.get("domain_coverage", 0) < 0.6:
                    # Generate cross-domain examples
                    integration_examples = [
                        """
;; Cross-domain: Attention + Learning
(ImplicationLink (stv 0.8 0.9)
  (EvaluationLink (PredicateNode "high-attention") (VariableNode "$X"))
  (ExecutionLink (SchemaNode "enhance-learning") (VariableNode "$X")))
""",
                        """
;; Cross-domain: Goals + Reasoning
(BindLink
  (VariableNode "$goal")
  (AndLink
    (InheritanceLink (VariableNode "$goal") (ConceptNode "active-goal"))
    (EvaluationLink (PredicateNode "pln-reasoning-required") (VariableNode "$goal")))
  (ExecutionLink (SchemaNode "apply-pln-inference") (VariableNode "$goal")))
"""
                    ]
                    synthetic_samples.extend(integration_examples)
            
            # Save synthetic samples
            if synthetic_samples:
                samples_path = os.path.join(
                    self.config["paths"]["feedback_samples"],
                    f"synthetic_samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
                
                with open(samples_path, 'w', encoding='utf-8') as f:
                    for sample in synthetic_samples:
                        f.write(sample.strip() + "\n\n")
                
                logger.info(f"Generated {len(synthetic_samples)} synthetic training samples")
        
        except Exception as e:
            logger.error(f"Error generating synthetic samples: {e}")
    
    def get_evaluation_status(self) -> Dict[str, Any]:
        """Get current evaluation loop status."""
        return {
            "running": self.running,
            "evaluation_count": len(self.evaluation_history),
            "latest_performance": self.performance_trends.get("current_score", 0),
            "performance_trend": self.performance_trends.get("recent_slope", 0),
            "last_evaluation": self.evaluation_history[-1]["timestamp"] if self.evaluation_history else None
        }


def main():
    """Command-line interface for automated evaluation loop."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NanoCog Automated Evaluation Loop")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--single-cycle", action="store_true", help="Run single evaluation cycle")
    
    args = parser.parse_args()
    
    # Create evaluation loop
    eval_loop = AutomatedEvaluationLoop(args.config)
    
    if args.single_cycle:
        # Run single evaluation cycle
        logger.info("Running single evaluation cycle...")
        eval_loop._run_evaluation_cycle(0)
        logger.info("Single evaluation cycle complete")
    else:
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            eval_loop.stop_evaluation_loop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start evaluation loop
        if args.daemon:
            logger.info("Starting in daemon mode...")
            # In a real implementation, this would fork and run as daemon
        
        eval_loop.start_evaluation_loop()


if __name__ == "__main__":
    main()