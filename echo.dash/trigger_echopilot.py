#!/usr/bin/env python3
"""
Script to manually trigger the EchoPilot workflow for testing.
This simulates what the GitHub Actions workflow would do.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

def run_analysis():
    """Run the analysis step"""
    print("🔍 Running EchoPilot Analysis...")
    print("=" * 50)
    
    # Create a temporary file for outputs
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        output_file = f.name
    
    # Set environment variable
    env = os.environ.copy()
    env['GITHUB_OUTPUT'] = output_file
    
    # Run the analysis script from the workflow
    analysis_script = """
import os
import json
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

def run_command(cmd, capture_output=True):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

# Initialize analysis results
analysis_results = {
    'code_quality_issues': [],
    'architecture_gaps': [],
    'test_coverage_gaps': [],
    'dependency_issues': [],
    'documentation_gaps': []
}

repo_path = Path('.')

# 1. Code Quality Analysis
print("🔍 Analyzing code quality...")

# Run pylint on Python files
python_files = list(repo_path.glob('**/*.py'))
if python_files:
    # Test with a few files first
    test_files = python_files[:5]
    pylint_cmd = f"pylint {' '.join(str(f) for f in test_files)} --output-format=json --exit-zero"
    returncode, stdout, stderr = run_command(pylint_cmd)
    
    if returncode == 0 and stdout:
        try:
            pylint_results = json.loads(stdout)
            for issue in pylint_results:
                if issue.get('type') in ['error', 'warning']:
                    analysis_results['code_quality_issues'].append({
                        'file': issue.get('path', 'unknown'),
                        'line': issue.get('line', 0),
                        'message': issue.get('message', ''),
                        'type': issue.get('type', ''),
                        'symbol': issue.get('symbol', ''),
                        'severity': 'high' if issue.get('type') == 'error' else 'medium'
                    })
        except json.JSONDecodeError:
            pass

# 2. Architecture Gap Analysis
print("🏗️ Analyzing architecture gaps...")

# Check for fragmented memory system
memory_files = list(repo_path.glob('**/*memory*.py')) + list(repo_path.glob('**/*Memory*.py'))
if len(memory_files) > 3:
    analysis_results['architecture_gaps'].append({
        'gap': 'Fragmented Memory System',
        'description': f'Found {len(memory_files)} memory-related files that should be unified',
        'files': [str(f) for f in memory_files],
        'priority': 'high',
        'recommendation': 'Consolidate memory operations into unified_echo_memory.py'
    })

# Check for multiple launch scripts
launch_files = list(repo_path.glob('**/launch_*.py'))
if len(launch_files) > 3:
    analysis_results['architecture_gaps'].append({
        'gap': 'Multiple Launch Scripts',
        'description': f'Found {len(launch_files)} launch scripts that could be consolidated',
        'files': [str(f) for f in launch_files],
        'priority': 'medium',
        'recommendation': 'Consider creating a unified launcher with configuration options'
    })

# Check for test file organization
test_files = list(repo_path.glob('**/test_*.py'))
if test_files and not (repo_path / 'tests').exists():
    analysis_results['architecture_gaps'].append({
        'gap': 'Test Files Not Organized',
        'description': f'Found {len(test_files)} test files scattered throughout the codebase',
        'files': [str(f) for f in test_files[:10]],
        'priority': 'medium',
        'recommendation': 'Organize test files into a dedicated tests/ directory'
    })

# 3. Error Handling Analysis
print("🚨 Analyzing error handling...")

error_patterns = [
    r'except\\s+Exception\\s*:',  # Generic exception handling
    r'except\\s*:',  # Bare except clauses
]

error_issues = []
for pattern in error_patterns:
    for file in python_files[:10]:  # Test with first 10 files
        try:
            with open(file, 'r') as f:
                content = f.read()
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\\n') + 1
                    error_issues.append({
                        'file': str(file),
                        'line': line_num,
                        'pattern': pattern,
                        'context': content.split('\\n')[line_num-1].strip()[:100]
                    })
        except Exception:
            continue

if error_issues:
    analysis_results['code_quality_issues'].extend(error_issues[:20])

# 4. Large Files Analysis
print("📏 Analyzing file sizes...")
large_files = []
for file in python_files:
    try:
        size = file.stat().st_size
        if size > 50000:  # Files larger than 50KB
            with open(file, 'r') as f:
                lines = len(f.readlines())
            large_files.append({
                'file': str(file),
                'size_kb': size // 1024,
                'lines': lines,
                'issue': 'Large file that may need refactoring',
                'priority': 'medium'
            })
    except Exception:
        continue

if large_files:
    analysis_results['code_quality_issues'].extend(large_files[:5])

# 5. Security Analysis
print("🔒 Analyzing security patterns...")

security_patterns = [
    r'password\\s*=',  # Hardcoded passwords
    r'api_key\\s*=',  # Hardcoded API keys
    r'secret\\s*=',  # Hardcoded secrets
    r'eval\\s*\\(',  # eval() usage
    r'exec\\s*\\(',  # exec() usage
    r'os\\.system\\s*\\(',  # os.system() usage
    r'subprocess\\.call\\s*\\(',  # subprocess.call() usage
]

security_issues = []
for pattern in security_patterns:
    for file in python_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\\n') + 1
                    context = content.split('\\n')[line_num-1].strip()[:100]
                    security_issues.append({
                        'file': str(file),
                        'line': line_num,
                        'pattern': pattern,
                        'context': context,
                        'issue': 'Potential security vulnerability',
                        'priority': 'high'
                    })
        except Exception:
            continue

if security_issues:
    analysis_results['code_quality_issues'].extend(security_issues[:10])

# Set GitHub Actions outputs
for key, value in analysis_results.items():
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"{key}={json.dumps(value)}\\n")
    else:
        print(f"Warning: GITHUB_OUTPUT not set, using fallback output")
        print(f"::set-output name={key}::{json.dumps(value)}")

print(f"✅ Analysis complete. Found:")
print(f"  - {len(analysis_results['code_quality_issues'])} code quality issues")
print(f"  - {len(analysis_results['architecture_gaps'])} architecture gaps")
print(f"  - {len(analysis_results['test_coverage_gaps'])} test coverage gaps")
print(f"  - {len(analysis_results['dependency_issues'])} dependency issues")
print(f"  - {len(analysis_results['documentation_gaps'])} documentation gaps")
"""
    
    # Run the analysis
    result = subprocess.run(['python3', '-c', analysis_script], 
                          env=env, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Read the outputs
    outputs = {}
    try:
        with open(output_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    outputs[key] = value
    except Exception as e:
        print(f"Error reading outputs: {e}")
    
    # Clean up
    os.unlink(output_file)
    
    return outputs

def create_issues(outputs):
    """Create GitHub issues based on analysis results"""
    print("\n🔧 Creating GitHub Issues...")
    print("=" * 50)
    
    # Parse outputs
    def parse_output(output_str):
        try:
            return json.loads(output_str) if output_str else []
        except json.JSONDecodeError:
            print(f"Failed to parse output: {output_str[:200]}...")
            return []
    
    code_quality_issues = parse_output(outputs.get('code_quality_issues', '[]'))
    architecture_gaps = parse_output(outputs.get('architecture_gaps', '[]'))
    test_coverage_gaps = parse_output(outputs.get('test_coverage_gaps', '[]'))
    dependency_issues = parse_output(outputs.get('dependency_issues', '[]'))
    documentation_gaps = parse_output(outputs.get('documentation_gaps', '[]'))
    
    print("📊 Analysis Results:")
    print(f"  - Code Quality Issues: {len(code_quality_issues)}")
    print(f"  - Architecture Gaps: {len(architecture_gaps)}")
    print(f"  - Test Coverage Gaps: {len(test_coverage_gaps)}")
    print(f"  - Dependency Issues: {len(dependency_issues)}")
    print(f"  - Documentation Gaps: {len(documentation_gaps)}")
    
    # Simulate issue creation
    issues_created = 0
    
    # Architecture gaps (high priority)
    for gap in architecture_gaps:
        title = f"🏗️ {gap['gap']}"
        print(f"✅ Would create issue: {title}")
        print(f"   Description: {gap['description']}")
        print(f"   Priority: {gap['priority']}")
        print(f"   Recommendation: {gap['recommendation']}")
        print()
        issues_created += 1
    
    # Documentation gaps
    for gap in documentation_gaps:
        title = f"📚 {gap['gap']}"
        print(f"✅ Would create issue: {title}")
        print(f"   Description: {gap['description']}")
        print(f"   Priority: {gap['priority']}")
        print()
        issues_created += 1
    
    # Test coverage gaps
    for gap in test_coverage_gaps:
        title = f"🧪 {gap['gap']}"
        print(f"✅ Would create issue: {title}")
        print(f"   Description: {gap['description']}")
        print(f"   Priority: {gap['priority']}")
        print()
        issues_created += 1
    
    # Dependency issues
    for issue_data in dependency_issues:
        title = f"📦 {issue_data['gap']}"
        print(f"✅ Would create issue: {title}")
        print(f"   Description: {issue_data['description']}")
        print(f"   Priority: {issue_data['priority']}")
        print()
        issues_created += 1
    
    # Code quality issues (batch them if there are many)
    if code_quality_issues:
        # Group by file to avoid spam
        issues_by_file = {}
        for issue in code_quality_issues:
            file = issue.get('file', 'unknown')
            if file not in issues_by_file:
                issues_by_file[file] = []
            issues_by_file[file].append(issue)

        for file, issues in list(issues_by_file.items())[:5]:  # Limit to 5 files
            title = f"🔧 Code Quality Issues in {Path(file).name}"
            print(f"✅ Would create issue: {title}")
            print(f"   File: {file}")
            print(f"   Issues Found: {len(issues)}")
            print("   Sample issues:")
            for issue in issues[:3]:
                if 'message' in issue:
                    print(f"     - Line {issue.get('line', 'N/A')}: {issue.get('message', 'Unknown issue')}")
                elif 'issue' in issue:
                    print(f"     - Line {issue.get('line', 'N/A')}: {issue.get('issue', 'Unknown issue')}")
                else:
                    print(f"     - Line {issue.get('line', 'N/A')}: {issue.get('pattern', 'Unknown pattern')}")
            print()
            issues_created += 1
    
    if issues_created > 0:
        print(f"🎉 Would create {issues_created} issues for dtecho to work on!")
    else:
        print("✅ No issues found! Your codebase appears to be in good shape.")
        print("💡 Consider running manual code reviews or adding more comprehensive tests.")
    
    return issues_created

def main():
    print("🚀 EchoPilot Manual Trigger")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run analysis
    outputs = run_analysis()
    
    # Create issues
    issues_created = create_issues(outputs)
    
    print("\n✅ EchoPilot run complete!")
    print(f"Total issues that would be created: {issues_created}")

if __name__ == "__main__":
    main()