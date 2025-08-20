#!/usr/bin/env python3
"""
Automated roadmap issue generation script.
Parses roadmap markdown files and creates GitHub issues for incomplete tasks.
"""

import os
import re
import sys
from typing import List, Dict, Optional
from github import Github
from datetime import datetime


class RoadmapParser:
    """Parses roadmap markdown files and extracts tasks."""
    
    def __init__(self, roadmap_file: str):
        self.roadmap_file = roadmap_file
        self.tasks = []
    
    def parse_tasks(self) -> List[Dict]:
        """Parse tasks from markdown file."""
        if not os.path.exists(self.roadmap_file):
            print(f"Roadmap file not found: {self.roadmap_file}")
            return []
        
        with open(self.roadmap_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract tasks with checkboxes
        task_pattern = r'^- \[ \] \*\*Task ([^*]+)\*\*: (.+?)(?=\n  - |\n- |\n### |\n## |\Z)'
        phase_pattern = r'^### (Phase \d+(?:\.\d+)?): (.+?) \((.+?)\)'
        
        current_phase = None
        current_section = None
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for phase headers
            phase_match = re.match(phase_pattern, line)
            if phase_match:
                current_phase = {
                    'id': phase_match.group(1),
                    'title': phase_match.group(2),
                    'timeline': phase_match.group(3)
                }
                i += 1
                continue
            
            # Check for task items
            if line.startswith('- [ ] **Task'):
                task_match = re.match(r'- \[ \] \*\*Task ([^*]+)\*\*: (.+)', line)
                if task_match:
                    task_id = task_match.group(1)
                    task_title = task_match.group(2)
                    
                    # Extract task description and acceptance criteria
                    description_lines = []
                    acceptance_criteria = []
                    i += 1
                    
                    # Collect description and acceptance criteria
                    while i < len(lines):
                        current_line = lines[i].strip()
                        
                        # Stop if we hit the next task or major section
                        if (current_line.startswith('- [ ] **Task') or 
                            current_line.startswith('### ') or 
                            current_line.startswith('## ') or
                            current_line.startswith('#### ')):
                            break
                            
                        # Handle acceptance criteria
                        if '**Acceptance Criteria**:' in current_line:
                            acceptance_criteria.append(current_line.split(':', 1)[-1].strip())
                        # Handle bullet points in description
                        elif current_line.startswith('- ') and not current_line.startswith('- [ ]'):
                            description_lines.append(current_line[2:])
                        # Handle regular description lines
                        elif current_line and not current_line.startswith('- [ ]'):
                            description_lines.append(current_line)
                        
                        i += 1
                    
                    # Create task object
                    task = {
                        'id': task_id,
                        'title': task_title,
                        'description': '\n'.join(description_lines),
                        'acceptance_criteria': '\n'.join(acceptance_criteria),
                        'phase': current_phase['id'] if current_phase else 'Unknown',
                        'phase_title': current_phase['title'] if current_phase else 'Unknown',
                        'timeline': current_phase['timeline'] if current_phase else 'TBD',
                        'labels': self._generate_labels(current_phase, task_id)
                    }
                    self.tasks.append(task)
                    continue
            
            i += 1
        
        return self.tasks
    
    def _generate_labels(self, phase: Optional[Dict], task_id: str) -> List[str]:
        """Generate appropriate labels for the task."""
        labels = ['roadmap', 'next-steps']
        
        if phase:
            # Add phase label
            phase_label = phase['id'].lower().replace(' ', '-').replace('.', '-')
            labels.append(phase_label)
            
            # Add timeline-based labels
            timeline = phase['timeline'].lower()
            if 'week' in timeline:
                if '1-2' in timeline or '1' in timeline:
                    labels.append('immediate')
                else:
                    labels.append('short-term')
            elif 'month' in timeline:
                if '1' in timeline:
                    labels.append('short-term')
                elif '2-3' in timeline:
                    labels.append('medium-term')
                else:
                    labels.append('long-term')
        
        # Add component-specific labels
        if 'echo-self' in task_id.lower() or 'evolution' in task_id.lower():
            labels.append('echo-self-ai')
        elif 'aar' in task_id.lower() or 'agent' in task_id.lower() or 'arena' in task_id.lower():
            labels.append('aar-orchestration')
        elif 'embodied' in task_id.lower() or '4e' in task_id.lower():
            labels.append('embodied-ai')
        elif 'sensor' in task_id.lower() or 'motor' in task_id.lower():
            labels.append('sensory-motor')
        elif 'mlops' in task_id.lower() or 'training' in task_id.lower():
            labels.append('mlops')
        
        return labels


class IssueGenerator:
    """Generates GitHub issues from parsed tasks."""
    
    def __init__(self, repository: str, token: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repository)
    
    def generate_issues(self, tasks: List[Dict], force_recreation: bool = False) -> None:
        """Generate GitHub issues for tasks."""
        existing_issues = self._get_existing_roadmap_issues()
        
        for task in tasks:
            issue_title = f"[{task['id']}] {task['title']}"
            
            # Check if issue already exists
            existing_issue = None
            for issue in existing_issues:
                if issue_title in issue.title or task['id'] in issue.title:
                    existing_issue = issue
                    break
            
            if existing_issue and not force_recreation:
                print(f"Issue already exists: {issue_title}")
                continue
            
            if existing_issue and force_recreation:
                print(f"Closing existing issue: {existing_issue.title}")
                existing_issue.edit(state='closed')
            
            # Create issue description
            description = self._create_issue_description(task)
            
            # Create the issue
            try:
                issue = self.repo.create_issue(
                    title=issue_title,
                    body=description,
                    labels=task['labels']
                )
                print(f"Created issue: {issue.title} (#{issue.number})")
            except Exception as e:
                print(f"Error creating issue '{issue_title}': {e}")
    
    def _get_existing_roadmap_issues(self) -> List:
        """Get existing issues with roadmap labels."""
        issues = []
        try:
            for issue in self.repo.get_issues(state='open', labels=['roadmap']):
                issues.append(issue)
        except Exception as e:
            print(f"Error fetching existing issues: {e}")
        return issues
    
    def _create_issue_description(self, task: Dict) -> str:
        """Create detailed issue description from task data."""
        description = f"""## Task Description

{task['description']}

## Phase Information

- **Phase**: {task['phase']} - {task['phase_title']}
- **Timeline**: {task['timeline']}

## Acceptance Criteria

{task['acceptance_criteria']}

## Implementation Notes

- Review the [Deep Tree Echo Development Roadmap](DEEP_TREE_ECHO_ROADMAP.md) for full context
- Ensure integration with existing DTESN components in `echo.kern/`
- Follow the coding standards in [DEVELOPMENT.md](echo.kern/DEVELOPMENT.md)
- Add comprehensive tests for new functionality
- Update documentation as needed

## Related Components

This task is part of the Deep Tree Echo architecture integration, specifically targeting the {task['phase']} development phase.

---

*This issue was automatically generated from the development roadmap on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        return description


def main():
    """Main execution function."""
    # Get environment variables
    github_token = os.environ.get('GITHUB_TOKEN')
    repository = os.environ.get('REPOSITORY')
    force_recreation = os.environ.get('FORCE_RECREATION', 'false').lower() == 'true'
    roadmap_file = os.environ.get('ROADMAP_FILE', 'DEEP_TREE_ECHO_ROADMAP.md')
    
    if not github_token or not repository:
        print("Error: GITHUB_TOKEN and REPOSITORY environment variables are required")
        sys.exit(1)
    
    print(f"Processing roadmap: {roadmap_file}")
    print(f"Repository: {repository}")
    print(f"Force recreation: {force_recreation}")
    
    # Parse roadmap
    parser = RoadmapParser(roadmap_file)
    tasks = parser.parse_tasks()
    
    if not tasks:
        print("No tasks found in roadmap file")
        return
    
    print(f"Found {len(tasks)} tasks")
    
    # Generate issues
    generator = IssueGenerator(repository, github_token)
    generator.generate_issues(tasks, force_recreation)
    
    print("Issue generation complete")


if __name__ == '__main__':
    main()