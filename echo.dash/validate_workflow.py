
#!/usr/bin/env python3
"""
🛡️ Neural-Symbolic Workflow Validation Engine
=============================================

Advanced multi-layer validation system for GitHub Actions workflows,
implementing cognitive safety mechanisms and symbolic reasoning to
prevent dangerous modifications and ensure workflow integrity.

Validation Layers:
1. Syntactic Validation - YAML structure and GitHub Actions schema
2. Semantic Safety - Logic validation and security analysis  
3. Cognitive Coherence - Neural-symbolic consistency checks
4. Security Analysis - Vulnerability and privilege escalation detection

This module serves as a critical safety component in the Echoevo
cognitive evolution system, preventing chaotic divergence while
enabling safe self-improvement.
"""

import sys
import yaml
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Configure validation logging for comprehensive safety tracking
logging.basicConfig(
    level=logging.INFO,
    format='🛡️ %(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class CognitiveWorkflowValidator:
    """
    Comprehensive workflow validation system implementing multiple
    safety layers and cognitive coherence checking.
    """
    
    def __init__(self, strict_mode: bool = False, security_scan: bool = True):
        """
        Initialize the cognitive validation system
        
        Args:
            strict_mode: Enable strict validation with enhanced safety checks
            security_scan: Enable security vulnerability scanning
        """
        self.strict_mode = strict_mode
        self.security_scan = security_scan
        self.validation_history = []
        self.safety_patterns = self._load_safety_patterns()
        
    def validate_workflow(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive multi-layer workflow validation
        
        Args:
            file_path: Path to the workflow YAML file
            
        Returns:
            Validation result dictionary with safety assessment
            
        Raises:
            ValueError: If critical validation failures are detected
        """
        logger.info(f"🔍 Initiating comprehensive validation for: {file_path}")
        
        validation_result = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'overall_safety': True,
            'validation_layers': {},
            'warnings': [],
            'critical_issues': [],
            'safety_score': 1.0,
            'cognitive_coherence': True
        }
        
        try:
            # Ensure target file exists and is readable
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Workflow file not found: {file_path}")
            
            # Load workflow content for analysis
            with open(file_path, 'r') as f:
                workflow_content = f.read()
                workflow = yaml.safe_load(workflow_content)
            
            # Layer 1: Syntactic Validation
            logger.info("🔍 Layer 1: Syntactic validation...")
            syntax_result = self._validate_syntax(workflow, workflow_content)
            validation_result['validation_layers']['syntax'] = syntax_result
            
            # Layer 2: Semantic Safety Analysis  
            logger.info("🔍 Layer 2: Semantic safety analysis...")
            semantic_result = self._validate_semantic_safety(workflow)
            validation_result['validation_layers']['semantic'] = semantic_result
            
            # Layer 3: Cognitive Coherence Validation
            logger.info("🔍 Layer 3: Cognitive coherence validation...")
            coherence_result = self._validate_cognitive_coherence(workflow)
            validation_result['validation_layers']['coherence'] = coherence_result
            
            # Layer 4: Security Analysis (if enabled)
            if self.security_scan:
                logger.info("🔍 Layer 4: Security vulnerability analysis...")
                security_result = self._validate_security(workflow, workflow_content)
                validation_result['validation_layers']['security'] = security_result
            
            # Aggregate results and calculate overall safety
            validation_result = self._aggregate_validation_results(validation_result)
            
            # Log validation completion
            logger.info(f"✅ Validation completed - Safety Score: {validation_result['safety_score']:.3f}")
            
            # Store validation history for learning
            self.validation_history.append(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"💥 Critical validation error: {e}")
            validation_result['overall_safety'] = False
            validation_result['critical_issues'].append(f"Validation system failure: {e}")
            validation_result['safety_score'] = 0.0
            raise ValueError(f"Workflow validation failed: {e}")
    
    def _validate_syntax(self, workflow: Dict, content: str) -> Dict[str, Any]:
        """
        Layer 1: Comprehensive syntactic validation
        
        Validates YAML structure, GitHub Actions schema compliance,
        and basic workflow requirements.
        """
        result = {
            'passed': True,
            'issues': [],
            'score': 1.0
        }
        
        try:
            # Validate basic workflow structure
            required_keys = ['name', 'on', 'jobs']
            for key in required_keys:
                if key not in workflow:
                    result['issues'].append(f"Missing required top-level key: '{key}'")
                    result['passed'] = False
                    result['score'] *= 0.7
            
            # Validate 'on' triggers structure
            if 'on' in workflow:
                on_config = workflow['on']
                
                # Validate schedule syntax if present
                if 'schedule' in on_config:
                    if isinstance(on_config['schedule'], list):
                        for i, schedule in enumerate(on_config['schedule']):
                            if 'cron' in schedule:
                                cron_valid = self._validate_cron_syntax(schedule['cron'])
                                if not cron_valid:
                                    result['issues'].append(f"Invalid cron syntax in schedule[{i}]: {schedule['cron']}")
                                    result['passed'] = False
                                    result['score'] *= 0.8
                    else:
                        result['issues'].append("Schedule must be a list of schedule objects")
                        result['passed'] = False
                        result['score'] *= 0.6
            
            # Validate jobs structure
            if 'jobs' in workflow:
                jobs = workflow['jobs']
                if not isinstance(jobs, dict) or not jobs:
                    result['issues'].append("Jobs section must be a non-empty dictionary")
                    result['passed'] = False
                    result['score'] *= 0.5
                else:
                    for job_name, job_config in jobs.items():
                        job_issues = self._validate_job_syntax(job_name, job_config)
                        result['issues'].extend(job_issues)
                        if job_issues:
                            result['score'] *= 0.9
            
            # Validate YAML formatting quality
            formatting_issues = self._validate_yaml_formatting(content)
            result['issues'].extend(formatting_issues)
            if formatting_issues:
                result['score'] *= 0.95
                
        except Exception as e:
            result['issues'].append(f"Syntax validation error: {e}")
            result['passed'] = False
            result['score'] = 0.0
        
        return result
    
    def _validate_semantic_safety(self, workflow: Dict) -> Dict[str, Any]:
        """
        Layer 2: Deep semantic safety analysis
        
        Analyzes workflow logic for potential safety hazards,
        resource exhaustion, infinite loops, and logical inconsistencies.
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'score': 1.0
        }
        
        try:
            jobs = workflow.get('jobs', {})
            
            for job_name, job_config in jobs.items():
                # Check for timeout protection
                if 'timeout-minutes' not in job_config:
                    result['warnings'].append(f"Job '{job_name}' has no timeout protection")
                    result['score'] *= 0.95
                else:
                    timeout = job_config['timeout-minutes']
                    if timeout > 360:  # 6 hours
                        result['warnings'].append(f"Job '{job_name}' has excessive timeout: {timeout} minutes")
                        result['score'] *= 0.9
                
                # Analyze job steps for safety issues
                steps = job_config.get('steps', [])
                for i, step in enumerate(steps):
                    step_issues = self._analyze_step_safety(job_name, i, step)
                    result['issues'].extend(step_issues['critical'])
                    result['warnings'].extend(step_issues['warnings'])
                    
                    if step_issues['critical']:
                        result['passed'] = False
                        result['score'] *= 0.7
                    if step_issues['warnings']:
                        result['score'] *= 0.95
            
            # Check for resource consumption patterns
            resource_issues = self._analyze_resource_usage(workflow)
            result['issues'].extend(resource_issues['critical'])
            result['warnings'].extend(resource_issues['warnings'])
            
            if resource_issues['critical']:
                result['passed'] = False
                result['score'] *= 0.6
                
        except Exception as e:
            result['issues'].append(f"Semantic validation error: {e}")
            result['passed'] = False
            result['score'] = 0.0
        
        return result
    
    def _validate_cognitive_coherence(self, workflow: Dict) -> Dict[str, Any]:
        """
        Layer 3: Cognitive coherence validation
        
        Ensures the workflow maintains cognitive consistency and
        aligns with neural-symbolic reasoning principles.
        """
        result = {
            'passed': True,
            'issues': [],
            'score': 1.0,
            'coherence_metrics': {}
        }
        
        try:
            # Analyze cognitive structure
            coherence_metrics = {
                'structural_clarity': self._assess_structural_clarity(workflow),
                'logical_consistency': self._assess_logical_consistency(workflow),
                'cognitive_complexity': self._calculate_cognitive_complexity(workflow),
                'evolution_compatibility': self._assess_evolution_compatibility(workflow)
            }
            
            result['coherence_metrics'] = coherence_metrics
            
            # Evaluate coherence thresholds
            if coherence_metrics['structural_clarity'] < 0.6:
                result['issues'].append("Workflow structure lacks cognitive clarity")
                result['passed'] = False
                result['score'] *= 0.8
            
            if coherence_metrics['cognitive_complexity'] > 0.8:
                result['issues'].append("Workflow cognitive complexity exceeds recommended threshold")
                result['score'] *= 0.9
            
            if coherence_metrics['evolution_compatibility'] < 0.5:
                result['issues'].append("Workflow incompatible with cognitive evolution principles")
                result['passed'] = False
                result['score'] *= 0.7
            
            # Overall coherence score
            avg_coherence = sum(coherence_metrics.values()) / len(coherence_metrics)
            result['score'] *= avg_coherence
            
        except Exception as e:
            result['issues'].append(f"Cognitive coherence validation error: {e}")
            result['passed'] = False
            result['score'] = 0.0
        
        return result
    
    def _validate_security(self, workflow: Dict, content: str) -> Dict[str, Any]:
        """
        Layer 4: Security vulnerability analysis
        
        Scans for security vulnerabilities, privilege escalation attempts,
        and dangerous command patterns.
        """
        result = {
            'passed': True,
            'vulnerabilities': [],
            'security_warnings': [],
            'score': 1.0
        }
        
        try:
            # Scan for dangerous command patterns
            dangerous_patterns = [
                r'\bcurl\s+.*\|\s*bash',  # Pipe to bash
                r'\bwget\s+.*\|\s*sh',   # Pipe to shell
                r'\bsudo\s+.*',          # Sudo usage
                r'\bchmod\s+777',        # Dangerous permissions
                r'\brm\s+-rf\s+/',       # Recursive deletion
                r'\b\$\{.*\}.*\$\{.*\}', # Complex variable injection
            ]
            
            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['vulnerabilities'].append(f"Dangerous command pattern detected: {pattern}")
                    result['passed'] = False
                    result['score'] *= 0.6
            
            # Check for secret exposure risks
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ]
            
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['security_warnings'].append(f"Potential secret exposure: {pattern}")
                    result['score'] *= 0.9
            
            # Analyze job permissions
            jobs = workflow.get('jobs', {})
            for job_name, job_config in jobs.items():
                permissions = job_config.get('permissions', {})
                if permissions:
                    # Check for overly broad permissions
                    if permissions.get('contents') == 'write':
                        result['security_warnings'].append(f"Job '{job_name}' has write access to repository contents")
                        result['score'] *= 0.95
                    
                    if permissions.get('actions') == 'write':
                        result['security_warnings'].append(f"Job '{job_name}' has write access to actions")
                        result['score'] *= 0.9
                        
        except Exception as e:
            result['vulnerabilities'].append(f"Security validation error: {e}")
            result['passed'] = False
            result['score'] = 0.0
        
        return result
    
    def _validate_cron_syntax(self, cron_expr: str) -> bool:
        """Validate cron expression syntax"""
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return False
            
            # Basic validation of cron parts
            minute, hour, day, month, weekday = parts
            
            # Validate ranges (simplified check)
            for part, max_val in [(minute, 59), (hour, 23), (day, 31), (month, 12), (weekday, 7)]:
                if part != '*' and '/' not in part and '-' not in part:
                    if part.isdigit() and (int(part) > max_val or int(part) < 0):
                        return False
            
            return True
        except:
            return False
    
    def _validate_job_syntax(self, job_name: str, job_config: Dict) -> List[str]:
        """Validate individual job syntax"""
        issues = []
        
        if not isinstance(job_config, dict):
            issues.append(f"Job '{job_name}' must be a dictionary")
            return issues
        
        # Check required job fields
        if 'runs-on' not in job_config:
            issues.append(f"Job '{job_name}' missing required 'runs-on' field")
        
        # Validate steps if present
        if 'steps' in job_config:
            steps = job_config['steps']
            if not isinstance(steps, list):
                issues.append(f"Job '{job_name}' steps must be a list")
            else:
                for i, step in enumerate(steps):
                    if not isinstance(step, dict):
                        issues.append(f"Job '{job_name}' step {i} must be a dictionary")
        
        return issues
    
    def _validate_yaml_formatting(self, content: str) -> List[str]:
        """Validate YAML formatting quality"""
        issues = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for tabs (should use spaces)
            if '\t' in line:
                issues.append(f"Line {i}: Uses tabs instead of spaces")
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append(f"Line {i}: Contains trailing whitespace")
        
        return issues
    
    def _analyze_step_safety(self, job_name: str, step_index: int, step: Dict) -> Dict[str, List[str]]:
        """Analyze individual step for safety issues"""
        result = {'critical': [], 'warnings': []}
        
        if 'run' in step:
            run_command = step['run']
            
            # Check for potentially infinite operations
            infinite_patterns = [
                'while true',
                'while :',
                'for (( ; ; ))',
                'infinite',
                'forever'
            ]
            
            for pattern in infinite_patterns:
                if pattern in run_command.lower():
                    result['critical'].append(
                        f"Job '{job_name}' step {step_index}: Potential infinite operation detected"
                    )
            
            # Check for network operations without error handling
            network_patterns = ['curl', 'wget', 'npm install', 'pip install']
            if any(pattern in run_command.lower() for pattern in network_patterns):
                if '||' not in run_command and 'set -e' not in run_command:
                    result['warnings'].append(
                        f"Job '{job_name}' step {step_index}: Network operation without error handling"
                    )
        
        return result
    
    def _analyze_resource_usage(self, workflow: Dict) -> Dict[str, List[str]]:
        """Analyze potential resource consumption issues"""
        result = {'critical': [], 'warnings': []}
        
        jobs = workflow.get('jobs', {})
        
        # Check for concurrent job limits
        if len(jobs) > 20:
            result['warnings'].append(f"High job count ({len(jobs)}) may impact resource usage")
        
        # Check for matrix strategies that could explode
        for job_name, job_config in jobs.items():
            if 'strategy' in job_config and 'matrix' in job_config['strategy']:
                matrix = job_config['strategy']['matrix']
                total_combinations = 1
                
                for key, values in matrix.items():
                    if isinstance(values, list):
                        total_combinations *= len(values)
                
                if total_combinations > 50:
                    result['critical'].append(
                        f"Job '{job_name}' matrix strategy generates {total_combinations} jobs"
                    )
                elif total_combinations > 20:
                    result['warnings'].append(
                        f"Job '{job_name}' matrix strategy generates {total_combinations} jobs"
                    )
        
        return result
    
    def _assess_structural_clarity(self, workflow: Dict) -> float:
        """Assess structural clarity of the workflow"""
        # Simple metric based on nesting depth and organization
        def calculate_depth(obj, current_depth=0):
            if isinstance(obj, dict):
                return max([calculate_depth(v, current_depth + 1) for v in obj.values()], default=current_depth)
            elif isinstance(obj, list):
                return max([calculate_depth(item, current_depth + 1) for item in obj], default=current_depth)
            return current_depth
        
        max_depth = calculate_depth(workflow)
        # Normalize: shallower is clearer
        return max(0.0, 1.0 - (max_depth - 3) / 10)
    
    def _assess_logical_consistency(self, workflow: Dict) -> float:
        """Assess logical consistency of workflow structure"""
        consistency_score = 1.0
        
        # Check for logical inconsistencies
        jobs = workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            # Check if job has steps but no runs-on
            if 'steps' in job_config and 'runs-on' not in job_config:
                consistency_score *= 0.8
            
            # Check for empty steps
            steps = job_config.get('steps', [])
            if not steps:
                consistency_score *= 0.9
        
        return consistency_score
    
    def _calculate_cognitive_complexity(self, workflow: Dict) -> float:
        """Calculate cognitive complexity metric"""
        job_count = len(workflow.get('jobs', {}))
        total_steps = sum(len(job.get('steps', [])) for job in workflow.get('jobs', {}).values())
        trigger_count = len(workflow.get('on', {}))
        env_count = len(workflow.get('env', {}))
        
        # Weighted complexity calculation
        complexity = (job_count * 0.3 + total_steps * 0.4 + trigger_count * 0.2 + env_count * 0.1) / 20
        return min(1.0, complexity)
    
    def _assess_evolution_compatibility(self, workflow: Dict) -> float:
        """Assess compatibility with cognitive evolution principles"""
        compatibility_score = 0.5  # Base score
        
        # Check for evolution-friendly features
        if workflow.get('on', {}).get('workflow_dispatch'):
            compatibility_score += 0.2  # Manual trigger support
        
        if 'env' in workflow:
            env_vars = workflow['env']
            cognitive_vars = [var for var in env_vars.keys() if 'cognitive' in var.lower()]
            if cognitive_vars:
                compatibility_score += 0.2  # Cognitive awareness
        
        # Check for safety mechanisms
        jobs = workflow.get('jobs', {})
        has_validation = any('validate' in job_name.lower() for job_name in jobs.keys())
        if has_validation:
            compatibility_score += 0.1  # Validation presence
        
        return min(1.0, compatibility_score)
    
    def _aggregate_validation_results(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all validation layers"""
        layers = validation_result['validation_layers']
        
        # Collect all issues and warnings
        all_issues = []
        all_warnings = []
        
        for layer_name, layer_result in layers.items():
            all_issues.extend(layer_result.get('issues', []))
            all_issues.extend(layer_result.get('vulnerabilities', []))
            all_warnings.extend(layer_result.get('warnings', []))
            all_warnings.extend(layer_result.get('security_warnings', []))
        
        validation_result['critical_issues'] = all_issues
        validation_result['warnings'] = all_warnings
        
        # Calculate overall safety score
        layer_scores = [layer.get('score', 1.0) for layer in layers.values()]
        if layer_scores:
            validation_result['safety_score'] = sum(layer_scores) / len(layer_scores)
        
        # Determine overall safety
        validation_result['overall_safety'] = (
            validation_result['safety_score'] >= 0.7 and 
            not validation_result['critical_issues']
        )
        
        # Assess cognitive coherence
        coherence_layer = layers.get('coherence', {})
        validation_result['cognitive_coherence'] = coherence_layer.get('passed', True)
        
        return validation_result
    
    def _load_safety_patterns(self) -> Dict[str, List[str]]:
        """Load safety patterns for enhanced validation"""
        return {
            'dangerous_commands': [
                r'rm\s+-rf\s+/',
                r'sudo\s+.*',
                r'chmod\s+777',
                r'curl.*\|.*bash',
                r'wget.*\|.*sh'
            ],
            'resource_intensive': [
                r'while\s+true',
                r'for\s*\(\(\s*;\s*;\s*\)\)',
                r'infinite',
                r'forever'
            ]
        }


def validate_workflow(file_path: str, 
                     strict_mode: bool = False,
                     security_scan: bool = True,
                     output_json: bool = False) -> bool:
    """
    Main validation function with enhanced safety checking
    
    Args:
        file_path: Path to workflow file
        strict_mode: Enable strict validation mode
        security_scan: Enable security vulnerability scanning
        output_json: Output detailed results in JSON format
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValueError: If critical validation failures are detected
    """
    validator = CognitiveWorkflowValidator(strict_mode, security_scan)
    
    try:
        result = validator.validate_workflow(file_path)
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            print(f"🛡️ Workflow Validation Report for: {file_path}")
            print(f"📊 Overall Safety Score: {result['safety_score']:.3f}")
            print(f"✅ Overall Safety: {'PASS' if result['overall_safety'] else 'FAIL'}")
            print(f"🧠 Cognitive Coherence: {'PASS' if result['cognitive_coherence'] else 'FAIL'}")
            
            if result['critical_issues']:
                print(f"\n❌ Critical Issues ({len(result['critical_issues'])}):")
                for issue in result['critical_issues']:
                    print(f"  • {issue}")
            
            if result['warnings']:
                print(f"\n⚠️ Warnings ({len(result['warnings'])}):")
                for warning in result['warnings']:
                    print(f"  • {warning}")
            
            if result['overall_safety']:
                print("\n🎉 Validation passed! Workflow is cognitively safe.")
            else:
                print("\n💥 Validation failed! Workflow requires attention.")
        
        return result['overall_safety']
        
    except Exception as e:
        logger.error(f"💥 Validation system failure: {e}")
        if not output_json:
            print(f"❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='🛡️ Neural-Symbolic Workflow Validation Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Validation Modes:
  Standard   - Basic syntax and safety validation
  Strict     - Enhanced validation with strict safety checks
  Security   - Includes comprehensive security vulnerability scanning

Examples:
  %(prog)s workflow.yml
  %(prog)s workflow.yml --strict --security-scan
  %(prog)s workflow.yml --output-json --no-security-scan
        """
    )
    
    parser.add_argument('file_path',
                       help='Path to the workflow YAML file to validate')
    parser.add_argument('--strict',
                       action='store_true',
                       help='Enable strict validation mode')
    parser.add_argument('--security-scan',
                       action='store_true',
                       default=True,
                       help='Enable security vulnerability scanning (default: enabled)')
    parser.add_argument('--no-security-scan',
                       action='store_false',
                       dest='security_scan',
                       help='Disable security vulnerability scanning')
    parser.add_argument('--output-json',
                       action='store_true',
                       help='Output detailed validation results in JSON format')
    
    args = parser.parse_args()
    
    # Execute validation
    success = validate_workflow(
        args.file_path,
        strict_mode=args.strict,
        security_scan=args.security_scan,
        output_json=args.output_json
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
