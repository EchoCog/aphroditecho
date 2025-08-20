#!/usr/bin/env python3
"""
Deep Tree Echo Manual Analysis Tool

This script performs the analysis that would normally be done by the 
deep-tree-echo-auto-issues.yml workflow, but runs it manually to identify
and implement fixes for architecture gaps, migration tasks, and fragment issues.

Based on the workflow file: .github/workflows/deep-tree-echo-auto-issues.yml
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class DeepTreeEchoAnalyzer:
    """Analyzes Deep Tree Echo codebase for issues and generates manual implementation plan"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.results = {
            'fragments': [],
            'architecture_gaps': [],
            'migration_tasks': [],
            'analysis_timestamp': datetime.now().isoformat(),
            'recommendations': []
        }
    
    def analyze_fragments(self) -> List[Dict[str, Any]]:
        """Find and analyze all Deep Tree Echo related files"""
        print("🔍 Analyzing Deep Tree Echo fragments...")
        
        fragments = []
        patterns = ['*deep_tree_echo*.py', '*echo*.py', '*Echo*.py']
        
        for pattern in patterns:
            for file in self.repo_path.glob(pattern):
                if file.is_file() and not file.name.startswith('test_'):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Analyze file content
                        lines = len(content.splitlines())
                        classes = re.findall(r'class\s+(\w*[Ee]cho\w*)', content)
                        functions = re.findall(r'def\s+(\w*echo\w*)', content, re.IGNORECASE)
                        imports = re.findall(r'from\s+(\w*echo\w*)', content, re.IGNORECASE)
                        imports.extend(re.findall(r'import\s+(\w*echo\w*)', content, re.IGNORECASE))
                        
                        # Determine file type and status
                        file_type = 'core' if 'deep_tree_echo.py' in str(file) else 'extension'
                        if 'test_' in str(file):
                            file_type = 'test'
                        elif any(v in str(file) for v in ['-v1', '-v2', '.backup']):
                            file_type = 'legacy'
                            
                        # Check modification time to determine if active
                        mod_time = file.stat().st_mtime
                        status = 'active' if mod_time > 1700000000 else 'legacy'  # Nov 2023
                        
                        fragment = {
                            'file': str(file.relative_to(self.repo_path)),
                            'lines': lines,
                            'classes': classes,
                            'functions': functions,
                            'imports': imports,
                            'type': file_type,
                            'status': status,
                            'last_modified': datetime.fromtimestamp(mod_time).isoformat()
                        }
                        
                        fragments.append(fragment)
                        print(f"  📄 Found: {file.name} ({lines} lines, {len(classes)} classes, {len(functions)} functions)")
                        
                    except Exception as e:
                        print(f"  ⚠️  Error analyzing {file}: {e}")
        
        self.results['fragments'] = fragments
        return fragments
    
    def identify_architecture_gaps(self) -> List[Dict[str, Any]]:
        """Identify architecture gaps based on codebase analysis"""
        print("\n🏗️  Identifying architecture gaps...")
        
        gaps = [
            {
                'gap': 'Fragmented Memory System',
                'description': 'Memory operations scattered across multiple files without unified interface',
                'priority': 'high',
                'files': ['memory_management.py', 'deep_tree_echo.py', 'cognitive_architecture.py'],
                'evidence': 'Multiple files handle memory operations independently'
            },
            {
                'gap': 'Missing Cognitive Grammar',
                'description': 'RESOLVED: Python-Scheme integration layer implemented for neural-symbolic reasoning',
                'priority': 'resolved', 
                'files': ['cognitive_grammar_kernel.scm', 'cognitive_grammar_bridge.py', 'cognitive_architecture.py'],
                'evidence': 'CognitiveGrammarBridge provides complete Python-Scheme integration with neural-symbolic conversion capabilities'
            },
            {
                'gap': 'Inconsistent APIs',
                'description': 'Different interfaces across Echo fragments creating integration challenges',
                'priority': 'medium',
                'files': [f['file'] for f in self.results.get('fragments', [])],
                'evidence': 'Multiple Echo classes with varying method signatures'
            },
            {
                'gap': 'Legacy Code Retention',
                'description': 'Deprecated versions (v1, v2) still present causing confusion',
                'priority': 'medium',
                'files': ['deep_tree_echo-v1.py', 'deep_tree_echo-v2.py', 'Echoevo.md.backup'],
                'evidence': 'Multiple version files coexist without clear migration path'
            },
            {
                'gap': 'Incomplete P-System',
                'description': 'Missing membrane boundary implementation for computational isolation',
                'priority': 'low',
                'files': ['deep_tree_echo.py'],
                'evidence': 'P-System concepts mentioned but membrane boundaries not implemented'
            }
        ]
        
        # Validate gaps against actual files
        validated_gaps = []
        for gap in gaps:
            existing_files = [f for f in gap['files'] if (self.repo_path / f).exists()]
            if existing_files:
                gap['existing_files'] = existing_files
                validated_gaps.append(gap)
                print(f"  🔍 Gap: {gap['gap']} (Priority: {gap['priority']})")
            
        self.results['architecture_gaps'] = validated_gaps
        return validated_gaps
    
    def generate_migration_tasks(self) -> List[Dict[str, Any]]:
        """Generate specific migration tasks to address identified issues"""
        print("\n🚀 Generating migration tasks...")
        
        tasks = [
            {
                'task': 'Archive Legacy Versions',
                'description': 'Move v1/v2 implementations to archive directory to reduce confusion',
                'type': 'cleanup',
                'files': ['deep_tree_echo-v1.py', 'deep_tree_echo-v2.py', 'Echoevo.md.backup'],
                'estimated_effort': 'small',
                'implementation': 'Create archive/ directory and move legacy files'
            },
            {
                'task': 'Unify Memory Systems', 
                'description': 'Consolidate memory operations into single, well-defined module',
                'type': 'refactor',
                'files': ['memory_management.py', 'deep_tree_echo.py'],
                'estimated_effort': 'large',
                'implementation': 'Create unified MemorySystem class with consistent interface'
            },
            {
                'task': 'Implement Cognitive Grammar',
                'description': 'Add Python integration layer for Scheme-based symbolic reasoning',
                'type': 'feature',
                'files': ['cognitive_grammar_kernel.scm'],
                'estimated_effort': 'large', 
                'implementation': 'Create CognitiveGrammar class to bridge Python and Scheme'
            },
            {
                'task': 'Standardize Extension APIs',
                'description': 'Create consistent interface across all Echo components',
                'type': 'refactor',
                'files': [],  # Will be populated based on fragment analysis
                'estimated_effort': 'medium',
                'implementation': 'Define EchoComponent base class with standard methods'
            },
            {
                'task': 'Add P-System Membranes',
                'description': 'Implement computational boundary system for process isolation',
                'type': 'feature',
                'files': ['deep_tree_echo.py'],
                'estimated_effort': 'medium',
                'implementation': 'Add Membrane class for computational boundaries'
            }
        ]
        
        # Update extension API task with actual fragment files
        extension_files = [f['file'] for f in self.results.get('fragments', []) 
                          if f['type'] == 'extension']
        tasks[3]['files'] = extension_files
        
        # Validate tasks against existing files
        validated_tasks = []
        for task in tasks:
            existing_files = [f for f in task['files'] if (self.repo_path / f).exists()]
            if existing_files or task['task'] == 'Standardize Extension APIs':
                task['existing_files'] = existing_files
                validated_tasks.append(task)
                print(f"  📋 Task: {task['task']} (Effort: {task['estimated_effort']})")
        
        self.results['migration_tasks'] = validated_tasks
        return validated_tasks
    
    def generate_recommendations(self):
        """Generate specific implementation recommendations"""
        print("\n💡 Generating recommendations...")
        
        recommendations = []
        
        # Prioritize tasks by effort and impact
        high_impact_low_effort = [
            {
                'action': 'Archive Legacy Files',
                'rationale': 'Quick win to reduce code confusion',
                'steps': [
                    'Create archive/legacy/ directory',
                    'Move deep_tree_echo-v1.py to archive/legacy/',
                    'Move deep_tree_echo-v2.py to archive/legacy/', 
                    'Move backup files to archive/',
                    'Update documentation to reflect archive structure'
                ]
            },
            {
                'action': 'Create Echo Component Base Class',
                'rationale': 'Establishes foundation for API standardization',
                'steps': [
                    'Define EchoComponent abstract base class',
                    'Standardize init, process, and echo methods',
                    'Add common logging and error handling',
                    'Create documentation template'
                ]
            }
        ]
        
        medium_impact_tasks = [
            {
                'action': 'Consolidate Memory Management',
                'rationale': 'Reduces complexity and improves maintainability',
                'steps': [
                    'Analyze current memory operations',
                    'Design unified MemorySystem interface',
                    'Implement consolidated memory manager',
                    'Migrate existing code to use new system',
                    'Add comprehensive tests'
                ]
            }
        ]
        
        recommendations.extend(high_impact_low_effort)
        recommendations.extend(medium_impact_tasks)
        
        self.results['recommendations'] = recommendations
        
        for rec in recommendations:
            print(f"  💡 {rec['action']}: {rec['rationale']}")
    
    def save_analysis(self, filename: str = 'deep_tree_echo_analysis.json'):
        """Save analysis results to JSON file"""
        output_file = self.repo_path / filename
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Analysis saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("📈 DEEP TREE ECHO ANALYSIS SUMMARY")
        print("="*60)
        
        fragments = self.results.get('fragments', [])
        gaps = self.results.get('architecture_gaps', [])
        tasks = self.results.get('migration_tasks', [])
        
        print(f"🔍 Fragments Found: {len(fragments)}")
        print(f"   - Core files: {len([f for f in fragments if f['type'] == 'core'])}")
        print(f"   - Extensions: {len([f for f in fragments if f['type'] == 'extension'])}")
        print(f"   - Legacy files: {len([f for f in fragments if f['type'] == 'legacy'])}")
        
        print(f"\n🏗️  Architecture Gaps: {len(gaps)}")
        for gap in gaps:
            print(f"   - {gap['gap']} (Priority: {gap['priority']})")
        
        print(f"\n🚀 Migration Tasks: {len(tasks)}")
        for task in tasks:
            print(f"   - {task['task']} (Effort: {task['estimated_effort']})")
        
        print(f"\n💡 Recommendations: {len(self.results.get('recommendations', []))}")
        print("\n" + "="*60)
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("🤖 Starting Deep Tree Echo Analysis...")
        print("="*60)
        
        self.analyze_fragments()
        self.identify_architecture_gaps()
        self.generate_migration_tasks()
        self.generate_recommendations()
        
        self.print_summary()
        return self.save_analysis()


def main():
    """Main entry point for analysis tool"""
    analyzer = DeepTreeEchoAnalyzer()
    analysis_file = analyzer.run_full_analysis()
    
    print(f"\n✅ Analysis complete! Results saved to: {analysis_file}")
    print("\n🚀 Next steps:")
    print("1. Review analysis results")
    print("2. Implement high-impact, low-effort tasks first")
    print("3. Plan larger refactoring efforts")
    print("4. Create issues for tracking progress")


if __name__ == "__main__":
    main()