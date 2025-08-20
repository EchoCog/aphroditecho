#!/usr/bin/env python3
"""
Echo API Standardizer

This tool helps migrate existing Echo components to use the standardized 
base classes from echo_component_base.py, ensuring consistent interfaces
across the Echo ecosystem.

This implements the "Standardize Extension APIs" migration task identified
by the Deep Tree Echo analysis.
"""

import ast
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ComponentAnalysis:
    """Analysis results for an Echo component"""
    file_path: Path
    class_names: List[str]
    has_init: bool
    has_process_method: bool
    has_echo_method: bool
    current_inheritance: List[str]
    complexity_score: int
    recommended_base_class: str
    migration_steps: List[str]


class EchoAPIStandardizer:
    """Tool for standardizing Echo component APIs"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.analysis_results = {}
        
    def analyze_component(self, file_path: Path) -> ComponentAnalysis:
        """Analyze a single Echo component file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse the AST
            tree = ast.parse(content)
            
            # Extract information
            class_names = []
            has_init = False
            has_process_method = False
            has_echo_method = False
            current_inheritance = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_names.append(node.name)
                    
                    # Check inheritance
                    if node.bases:
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                current_inheritance.append(base.id)
                            elif isinstance(base, ast.Attribute):
                                current_inheritance.append(f"{base.value.id}.{base.attr}")
                    
                    # Check methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name == '__init__':
                                has_init = True
                            elif 'process' in item.name.lower():
                                has_process_method = True
                            elif 'echo' in item.name.lower():
                                has_echo_method = True
            
            # Calculate complexity (rough heuristic)
            complexity_score = len(content.splitlines())
            
            # Recommend base class
            recommended_base_class = self._recommend_base_class(
                file_path, content, has_process_method, has_echo_method
            )
            
            # Generate migration steps
            migration_steps = self._generate_migration_steps(
                file_path, class_names, current_inheritance, recommended_base_class
            )
            
            return ComponentAnalysis(
                file_path=file_path,
                class_names=class_names,
                has_init=has_init,
                has_process_method=has_process_method,
                has_echo_method=has_echo_method,
                current_inheritance=current_inheritance,
                complexity_score=complexity_score,
                recommended_base_class=recommended_base_class,
                migration_steps=migration_steps
            )
            
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            return None
    
    def _recommend_base_class(self, file_path: Path, content: str, 
                            has_process: bool, has_echo: bool) -> str:
        """Recommend appropriate base class for a component"""
        filename = file_path.name.lower()
        content_lower = content.lower()
        
        # Check for memory-related functionality
        memory_keywords = ['memory', 'store', 'cache', 'retrieve', 'storage']
        has_memory = any(keyword in content_lower for keyword in memory_keywords)
        
        # Check for processing functionality
        processing_keywords = ['pipeline', 'transform', 'process', 'filter', 'analyze']
        has_processing = any(keyword in content_lower for keyword in processing_keywords)
        
        # Make recommendation
        if has_memory and has_processing:
            return "MemoryEchoComponent"  # Can be extended with processing
        elif has_memory:
            return "MemoryEchoComponent"
        elif has_processing or has_process:
            return "ProcessingEchoComponent"
        else:
            return "EchoComponent"
    
    def _generate_migration_steps(self, file_path: Path, class_names: List[str],
                                current_inheritance: List[str], 
                                recommended_base: str) -> List[str]:
        """Generate specific migration steps for a component"""
        steps = []
        
        # Import step
        steps.append(f"Add import: from echo_component_base import {recommended_base}, EchoConfig, EchoResponse")
        
        # Inheritance step
        if class_names:
            main_class = class_names[0]  # Assume first class is main
            if current_inheritance:
                steps.append(f"Change {main_class} inheritance from {current_inheritance} to {recommended_base}")
            else:
                steps.append(f"Add {recommended_base} as base class for {main_class}")
        
        # Configuration step
        steps.append("Update __init__ to accept EchoConfig parameter")
        steps.append("Call super().__init__(config) in __init__")
        
        # Method standardization
        steps.append("Ensure initialize() method returns EchoResponse")
        steps.append("Ensure process() method accepts input_data and returns EchoResponse")
        steps.append("Ensure echo() method accepts data, echo_value and returns EchoResponse")
        
        # Error handling
        steps.append("Replace custom error handling with self.handle_error()")
        steps.append("Use self.validate_input() for input validation")
        
        # Logging
        steps.append("Replace custom logging with self.logger")
        
        return steps
    
    def scan_echo_components(self) -> Dict[str, ComponentAnalysis]:
        """Scan repository for Echo components and analyze them"""
        print("🔍 Scanning for Echo components...")
        
        # Pattern to find Echo-related Python files
        echo_patterns = ['*echo*.py', '*Echo*.py']
        
        components = {}
        
        for pattern in echo_patterns:
            for file_path in self.repo_path.glob(pattern):
                if (file_path.is_file() and 
                    not file_path.name.startswith('test_') and
                    file_path.name not in ['echo_component_base.py', 'echo_api_standardizer.py']):
                    
                    print(f"  📄 Analyzing: {file_path.name}")
                    analysis = self.analyze_component(file_path)
                    
                    if analysis:
                        components[str(file_path.relative_to(self.repo_path))] = analysis
        
        self.analysis_results = components
        return components
    
    def generate_migration_report(self) -> str:
        """Generate a comprehensive migration report"""
        if not self.analysis_results:
            self.scan_echo_components()
        
        report = []
        report.append("# Echo API Standardization Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        total_components = len(self.analysis_results)
        needs_migration = sum(1 for a in self.analysis_results.values() 
                            if not any(base in a.current_inheritance 
                                     for base in ['EchoComponent', 'MemoryEchoComponent', 'ProcessingEchoComponent']))
        
        report.append("## Summary")
        report.append(f"- Total Echo components found: {total_components}")
        report.append(f"- Components needing migration: {needs_migration}")
        report.append(f"- Components already standardized: {total_components - needs_migration}")
        report.append("")
        
        # Base class recommendations
        base_class_counts = {}
        for analysis in self.analysis_results.values():
            base_class = analysis.recommended_base_class
            base_class_counts[base_class] = base_class_counts.get(base_class, 0) + 1
        
        report.append("## Recommended Base Classes")
        for base_class, count in base_class_counts.items():
            report.append(f"- {base_class}: {count} components")
        report.append("")
        
        # Individual component analysis
        report.append("## Component Analysis")
        report.append("")
        
        # Sort by complexity (simpler first for easier migration)
        sorted_components = sorted(self.analysis_results.items(), 
                                 key=lambda x: x[1].complexity_score)
        
        for file_path, analysis in sorted_components:
            report.append(f"### {file_path}")
            report.append(f"- **Classes**: {', '.join(analysis.class_names) if analysis.class_names else 'None'}")
            report.append(f"- **Current inheritance**: {', '.join(analysis.current_inheritance) if analysis.current_inheritance else 'None'}")
            report.append(f"- **Recommended base**: {analysis.recommended_base_class}")
            report.append(f"- **Complexity**: {analysis.complexity_score} lines")
            report.append(f"- **Has echo method**: {'✅' if analysis.has_echo_method else '❌'}")
            report.append(f"- **Has process method**: {'✅' if analysis.has_process_method else '❌'}")
            report.append("")
            
            report.append("**Migration Steps:**")
            for i, step in enumerate(analysis.migration_steps, 1):
                report.append(f"{i}. {step}")
            report.append("")
        
        return "\n".join(report)
    
    def generate_simple_migration_for_component(self, file_path: str) -> str:
        """Generate a simple migration example for a specific component"""
        if file_path not in self.analysis_results:
            return f"Component {file_path} not found in analysis results"
        
        analysis = self.analysis_results[file_path]
        
        # Create a simple migration template
        template = f"""# Migration Template for {file_path}

## Before (Current Code):
```python
# Existing class structure
class {analysis.class_names[0] if analysis.class_names else 'ExistingClass'}:
    def __init__(self, ...):
        # Current initialization
        pass
    
    def some_method(self, data):
        # Current processing
        return result
```

## After (Standardized Code):
```python
from echo_component_base import {analysis.recommended_base_class}, EchoConfig, EchoResponse

class {analysis.class_names[0] if analysis.class_names else 'ExistingClass'}({analysis.recommended_base_class}):
    def __init__(self, config: EchoConfig):
        super().__init__(config)
        # Your specific initialization here
        
    def initialize(self) -> EchoResponse:
        try:
            self._initialized = True
            # Component-specific initialization
            return EchoResponse(success=True, message="Component initialized")
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        try:
            validation = self.validate_input(input_data)
            if not validation.success:
                return validation
            
            # Your processing logic here
            result = self.some_method(input_data)
            
            return EchoResponse(
                success=True,
                data=result,
                message="Processing completed"
            )
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        try:
            # Your echo logic here
            echoed_data = {{
                'original_data': data,
                'echo_value': echo_value,
                'timestamp': datetime.now().isoformat()
            }}
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"Echo operation completed (value: {{echo_value}})"
            )
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def some_method(self, data):
        # Migrate your existing logic here
        # Use self.logger instead of custom logging
        # Use self.handle_error() for error handling
        return processed_data
```

## Usage Example:
```python
from echo_component_base import EchoConfig

# Create configuration
config = EchoConfig(
    component_name="{analysis.class_names[0] if analysis.class_names else 'component'}",
    version="1.0.0",
    echo_threshold=0.75
)

# Create component
component = {analysis.class_names[0] if analysis.class_names else 'Component'}(config)

# Initialize
init_result = component.initialize()
if init_result.success:
    # Process data
    result = component.process(your_data)
    
    # Echo operation
    echo_result = component.echo(result.data, echo_value=0.8)
```
"""
        return template
    
    def print_migration_summary(self):
        """Print a summary of migration recommendations"""
        if not self.analysis_results:
            self.scan_echo_components()
        
        print("\n" + "=" * 60)
        print("📋 ECHO API STANDARDIZATION SUMMARY")
        print("=" * 60)
        
        # Priority recommendations
        simple_migrations = [f for f, a in self.analysis_results.items() if a.complexity_score < 300]
        medium_migrations = [f for f, a in self.analysis_results.items() if 300 <= a.complexity_score < 600]
        complex_migrations = [f for f, a in self.analysis_results.items() if a.complexity_score >= 600]
        
        print(f"\n🟢 Simple Migrations (< 300 lines): {len(simple_migrations)}")
        for file_path in simple_migrations:
            analysis = self.analysis_results[file_path]
            print(f"   - {file_path} → {analysis.recommended_base_class}")
        
        print(f"\n🟡 Medium Migrations (300-600 lines): {len(medium_migrations)}")
        for file_path in medium_migrations:
            analysis = self.analysis_results[file_path]
            print(f"   - {file_path} → {analysis.recommended_base_class}")
        
        print(f"\n🔴 Complex Migrations (> 600 lines): {len(complex_migrations)}")
        for file_path in complex_migrations:
            analysis = self.analysis_results[file_path]
            print(f"   - {file_path} → {analysis.recommended_base_class}")
        
        print("\n💡 Recommendation: Start with simple migrations first!")
        print("=" * 60)


def main():
    """Main entry point"""
    standardizer = EchoAPIStandardizer()
    
    # Scan and analyze components
    components = standardizer.scan_echo_components()
    
    if not components:
        print("❌ No Echo components found!")
        return
    
    # Print summary
    standardizer.print_migration_summary()
    
    # Generate and save full report
    report = standardizer.generate_migration_report()
    report_file = Path("echo_api_migration_report.md")
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Full migration report saved to: {report_file}")
    
    # Generate example migration for the simplest component
    if standardizer.analysis_results:
        simple_component = min(standardizer.analysis_results.items(), 
                             key=lambda x: x[1].complexity_score)
        
        example_file = Path("example_migration.md")
        example = standardizer.generate_simple_migration_for_component(simple_component[0])
        
        with open(example_file, 'w') as f:
            f.write(example)
        
        print(f"📝 Example migration saved to: {example_file}")
    
    print("\n✅ Analysis complete! Review the reports and start with simple migrations.")


if __name__ == "__main__":
    main()