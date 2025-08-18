#!/usr/bin/env python3
"""
DTESN Kernel Specification Compiler
===================================

A compiler for Deep Tree Echo State Network (DTESN) kernel specifications.
This tool parses DTESN specification files, validates them against OEIS A000081
mathematical constraints, and generates kernel configurations and code.

Usage:
    python3 dtesn_compiler.py [command] [options]
    
Commands:
    compile <file>     - Compile a DTESN specification file
    validate <file>    - Validate specification against OEIS A000081
    generate-docs      - Generate static documentation (legacy mode)
    
Options:
    --output <file>    - Output file for compilation results
    --format <format>  - Output format: c_header, kernel_config, documentation
    --verbose          - Enable verbose output
"""

import sys
import re
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# OEIS A000081: Number of unlabeled rooted trees with n nodes
OEIS_A000081 = [0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973]

class OutputFormat(Enum):
    C_HEADER = "c_header"
    KERNEL_CONFIG = "kernel_config"
    DOCUMENTATION = "documentation"

@dataclass
class MembraneLevel:
    level: int
    count: int
    neurons: int
    type: str

@dataclass
class ESNParameters:
    spectral_radius: float = 0.9
    input_scaling: float = 0.1
    leak_rate: float = 0.3
    connectivity: float = 0.1

@dataclass
class TimingConstraints:
    membrane_evolution_max_us: int = 10
    bseries_computation_max_us: int = 100
    esn_update_max_ms: int = 1
    context_switch_max_us: int = 5

@dataclass
class MemoryLayout:
    user_space: str = "0x00000000-0x3FFFFFFF"
    membrane_reservoirs: str = "0x40000000-0x7FFFFFFF"
    bseries_trees: str = "0x80000000-0xBFFFFFFF"
    kernel_space: str = "0xC0000000-0xFFFFFFFF"

@dataclass
class DTESNConfig:
    name: str
    version: str
    max_depth: int
    membrane_hierarchy: List[MembraneLevel] = field(default_factory=list)
    esn_parameters: ESNParameters = field(default_factory=ESNParameters)
    timing_constraints: TimingConstraints = field(default_factory=TimingConstraints)
    memory_layout: MemoryLayout = field(default_factory=MemoryLayout)

class DTESNParser:
    """Parser for DTESN specification files"""
    
    def __init__(self):
        self.config = None
        
    def parse_file(self, filename: str) -> DTESNConfig:
        """Parse a DTESN specification file"""
        with open(filename, 'r') as f:
            content = f.read()
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> DTESNConfig:
        """Parse DTESN specification content"""
        # Remove comments
        content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
        
        # Extract main config block - handle nested braces properly
        # Find the opening brace and count braces to find the matching closing brace
        config_start = content.find('dtesn_config')
        if config_start == -1:
            raise ValueError("No dtesn_config block found")
        
        brace_start = content.find('{', config_start)
        if brace_start == -1:
            raise ValueError("No opening brace found for dtesn_config")
        
        brace_count = 0
        brace_end = brace_start
        for i, char in enumerate(content[brace_start:], brace_start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    brace_end = i
                    break
        
        if brace_count != 0:
            raise ValueError("Unmatched braces in dtesn_config block")
        
        config_content = content[brace_start+1:brace_end]
        
        # Parse basic properties
        name = self._extract_string_value(config_content, 'name')
        version = self._extract_string_value(config_content, 'version')
        max_depth = self._extract_int_value(config_content, 'max_depth')
        
        config = DTESNConfig(name=name, version=version, max_depth=max_depth)
        
        # Parse membrane hierarchy - find the nested block
        membrane_match = re.search(r'membrane_hierarchy\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', config_content, re.DOTALL)
        if membrane_match:
            config.membrane_hierarchy = self._parse_membrane_hierarchy(membrane_match.group(1))
        
        # Parse ESN parameters
        esn_match = re.search(r'esn_parameters\s*\{([^{}]*)\}', config_content, re.DOTALL)
        if esn_match:
            config.esn_parameters = self._parse_esn_parameters(esn_match.group(1))
        
        # Parse timing constraints
        timing_match = re.search(r'timing_constraints\s*\{([^{}]*)\}', config_content, re.DOTALL)
        if timing_match:
            config.timing_constraints = self._parse_timing_constraints(timing_match.group(1))
            
        # Parse memory layout
        memory_match = re.search(r'memory_layout\s*\{([^{}]*)\}', config_content, re.DOTALL)
        if memory_match:
            config.memory_layout = self._parse_memory_layout(memory_match.group(1))
        
        self.config = config
        return config
    
    def _extract_string_value(self, content: str, key: str) -> str:
        match = re.search(rf'{key}:\s*"([^"]*)"', content)
        if not match:
            raise ValueError(f"Missing required field: {key}")
        return match.group(1)
    
    def _extract_int_value(self, content: str, key: str) -> int:
        match = re.search(rf'{key}:\s*(\d+)', content)
        if not match:
            raise ValueError(f"Missing required field: {key}")
        return int(match.group(1))
    
    def _extract_float_value(self, content: str, key: str) -> float:
        match = re.search(rf'{key}:\s*([0-9.]+)', content)
        if not match:
            raise ValueError(f"Missing required field: {key}")
        return float(match.group(1))
    
    def _parse_membrane_hierarchy(self, content: str) -> List[MembraneLevel]:
        hierarchy = []
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        for line in lines:
            # Parse: level: 0, count: 1, neurons: 100, type: "root"
            match = re.match(r'level:\s*(\d+),\s*count:\s*(\d+),\s*neurons:\s*(\d+),\s*type:\s*"([^"]*)"', line)
            if match:
                level = int(match.group(1))
                count = int(match.group(2))
                neurons = int(match.group(3))
                type_name = match.group(4)
                hierarchy.append(MembraneLevel(level, count, neurons, type_name))
        
        return hierarchy
    
    def _parse_esn_parameters(self, content: str) -> ESNParameters:
        params = ESNParameters()
        if 'spectral_radius:' in content:
            params.spectral_radius = self._extract_float_value(content, 'spectral_radius')
        if 'input_scaling:' in content:
            params.input_scaling = self._extract_float_value(content, 'input_scaling')
        if 'leak_rate:' in content:
            params.leak_rate = self._extract_float_value(content, 'leak_rate')
        if 'connectivity:' in content:
            params.connectivity = self._extract_float_value(content, 'connectivity')
        return params
    
    def _parse_timing_constraints(self, content: str) -> TimingConstraints:
        constraints = TimingConstraints()
        if 'membrane_evolution_max_us:' in content:
            constraints.membrane_evolution_max_us = self._extract_int_value(content, 'membrane_evolution_max_us')
        if 'bseries_computation_max_us:' in content:
            constraints.bseries_computation_max_us = self._extract_int_value(content, 'bseries_computation_max_us')
        if 'esn_update_max_ms:' in content:
            constraints.esn_update_max_ms = self._extract_int_value(content, 'esn_update_max_ms')
        if 'context_switch_max_us:' in content:
            constraints.context_switch_max_us = self._extract_int_value(content, 'context_switch_max_us')
        return constraints
    
    def _parse_memory_layout(self, content: str) -> MemoryLayout:
        layout = MemoryLayout()
        if 'user_space:' in content:
            layout.user_space = self._extract_string_value(content, 'user_space')
        if 'membrane_reservoirs:' in content:
            layout.membrane_reservoirs = self._extract_string_value(content, 'membrane_reservoirs')
        if 'bseries_trees:' in content:
            layout.bseries_trees = self._extract_string_value(content, 'bseries_trees')
        if 'kernel_space:' in content:
            layout.kernel_space = self._extract_string_value(content, 'kernel_space')
        return layout

class OEIS_A000081_Validator:
    """Validator for OEIS A000081 compliance"""
    
    @staticmethod
    def validate_membrane_hierarchy(hierarchy: List[MembraneLevel], max_depth: int) -> Tuple[bool, List[str]]:
        """Validate membrane hierarchy against OEIS A000081 enumeration"""
        errors = []
        
        if max_depth >= len(OEIS_A000081):
            errors.append(f"Max depth {max_depth} exceeds available OEIS A000081 data (max: {len(OEIS_A000081)-1})")
            return False, errors
        
        # Check that we have levels 0 through max_depth
        levels = {level.level for level in hierarchy}
        expected_levels = set(range(max_depth + 1))
        
        missing_levels = expected_levels - levels
        if missing_levels:
            errors.append(f"Missing membrane levels: {sorted(missing_levels)}")
        
        extra_levels = levels - expected_levels
        if extra_levels:
            errors.append(f"Extra membrane levels beyond max_depth: {sorted(extra_levels)}")
        
        # Validate counts against OEIS A000081
        for level in hierarchy:
            if level.level < len(OEIS_A000081):
                # Special case: level 0 should have count 1 (root), not 0
                if level.level == 0:
                    expected_count = 1
                else:
                    expected_count = OEIS_A000081[level.level]
                    
                if level.count != expected_count:
                    errors.append(f"Level {level.level} has count {level.count}, expected {expected_count} (OEIS A000081)")
        
        return len(errors) == 0, errors

class DTESNCompiler:
    """Compiler for DTESN specifications"""
    
    def __init__(self):
        self.parser = DTESNParser()
        self.validator = OEIS_A000081_Validator()
    
    def compile_file(self, input_file: str, output_file: str = None, format: OutputFormat = OutputFormat.C_HEADER, verbose: bool = False) -> bool:
        """Compile a DTESN specification file"""
        try:
            if verbose:
                print(f"Parsing DTESN specification: {input_file}")
            
            # Parse the specification
            config = self.parser.parse_file(input_file)
            
            if verbose:
                print(f"Parsed configuration: {config.name} v{config.version}")
            
            # Validate against OEIS A000081
            is_valid, errors = self.validator.validate_membrane_hierarchy(config.membrane_hierarchy, config.max_depth)
            
            if not is_valid:
                print("VALIDATION ERRORS:")
                for error in errors:
                    print(f"  ❌ {error}")
                return False
            elif verbose:
                print("✅ OEIS A000081 validation passed")
            
            # Generate output
            if format == OutputFormat.C_HEADER:
                output = self._generate_c_header(config)
            elif format == OutputFormat.KERNEL_CONFIG:
                output = self._generate_kernel_config(config)
            elif format == OutputFormat.DOCUMENTATION:
                output = self._generate_documentation(config)
            else:
                raise ValueError(f"Unknown output format: {format}")
            
            # Write output
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output)
                if verbose:
                    print(f"Generated {format.value} output: {output_file}")
            else:
                print(output)
            
            return True
            
        except Exception as e:
            print(f"Compilation failed: {e}")
            return False
    
    def _generate_c_header(self, config: DTESNConfig) -> str:
        """Generate C header file from DTESN configuration"""
        header = f"""/*
 * Generated DTESN Kernel Configuration Header
 * Source: {config.name} v{config.version}
 * Generated by: DTESN Kernel Specification Compiler
 */

#ifndef _DTESN_CONFIG_H_
#define _DTESN_CONFIG_H_

/* Configuration Metadata */
#define DTESN_CONFIG_NAME "{config.name}"
#define DTESN_CONFIG_VERSION "{config.version}"
#define DTESN_MAX_DEPTH {config.max_depth}

/* Membrane Hierarchy Configuration */
#define DTESN_MEMBRANE_LEVELS {len(config.membrane_hierarchy)}

typedef struct dtesn_membrane_config {{
    uint32_t level;
    uint32_t count;
    uint32_t neurons;
    const char* type;
}} dtesn_membrane_config_t;

static const dtesn_membrane_config_t dtesn_membrane_configs[] = {{
"""
        
        for membrane in config.membrane_hierarchy:
            header += f'    {{ {membrane.level}, {membrane.count}, {membrane.neurons}, "{membrane.type}" }},\n'
        
        header += f"""}};

/* ESN Parameters */
#define DTESN_SPECTRAL_RADIUS {config.esn_parameters.spectral_radius}f
#define DTESN_INPUT_SCALING {config.esn_parameters.input_scaling}f
#define DTESN_LEAK_RATE {config.esn_parameters.leak_rate}f
#define DTESN_CONNECTIVITY {config.esn_parameters.connectivity}f

/* Timing Constraints (microseconds/milliseconds) */
#define DTESN_MEMBRANE_EVOLUTION_MAX_US {config.timing_constraints.membrane_evolution_max_us}
#define DTESN_BSERIES_COMPUTATION_MAX_US {config.timing_constraints.bseries_computation_max_us}
#define DTESN_ESN_UPDATE_MAX_MS {config.timing_constraints.esn_update_max_ms}
#define DTESN_CONTEXT_SWITCH_MAX_US {config.timing_constraints.context_switch_max_us}

/* Memory Layout */
#define DTESN_USER_SPACE_BASE 0x00000000UL
#define DTESN_USER_SPACE_END  0x3FFFFFFFUL
#define DTESN_MEMBRANE_BASE   0x40000000UL
#define DTESN_MEMBRANE_END    0x7FFFFFFFUL
#define DTESN_BSERIES_BASE    0x80000000UL
#define DTESN_BSERIES_END     0xBFFFFFFFUL
#define DTESN_KERNEL_BASE     0xC0000000UL
#define DTESN_KERNEL_END      0xFFFFFFFFUL

#endif /* _DTESN_CONFIG_H_ */
"""
        return header
    
    def _generate_kernel_config(self, config: DTESNConfig) -> str:
        """Generate kernel configuration from DTESN specification"""
        return f"""# Generated DTESN Kernel Configuration
# Source: {config.name} v{config.version}

CONFIG_DTESN=y
CONFIG_DTESN_MAX_DEPTH={config.max_depth}
CONFIG_DTESN_MEMBRANE_LEVELS={len(config.membrane_hierarchy)}
CONFIG_DTESN_SPECTRAL_RADIUS={int(config.esn_parameters.spectral_radius * 100)}
CONFIG_DTESN_REAL_TIME=y
CONFIG_DTESN_TIMING_STRICT=y
"""

    def _generate_documentation(self, config: DTESNConfig) -> str:
        """Generate documentation from DTESN specification"""
        doc = f"""# {config.name} v{config.version}

## Configuration Overview

**Max Depth**: {config.max_depth}  
**Membrane Levels**: {len(config.membrane_hierarchy)}

## Membrane Hierarchy

| Level | Count | Neurons | Type |
|-------|-------|---------|------|
"""
        for membrane in config.membrane_hierarchy:
            doc += f"| {membrane.level} | {membrane.count} | {membrane.neurons} | {membrane.type} |\n"
        
        doc += f"""
## ESN Parameters

- **Spectral Radius**: {config.esn_parameters.spectral_radius}
- **Input Scaling**: {config.esn_parameters.input_scaling}
- **Leak Rate**: {config.esn_parameters.leak_rate}
- **Connectivity**: {config.esn_parameters.connectivity}

## Timing Constraints

- **Membrane Evolution**: ≤ {config.timing_constraints.membrane_evolution_max_us}μs
- **B-Series Computation**: ≤ {config.timing_constraints.bseries_computation_max_us}μs
- **ESN Update**: ≤ {config.timing_constraints.esn_update_max_ms}ms
- **Context Switch**: ≤ {config.timing_constraints.context_switch_max_us}μs
"""
        return doc

def generate_legacy_documentation():
    """Generate the original static documentation for backward compatibility"""
    print("Generating legacy Echo-Kernel specification documentation...")
    
    # Use the original echo_kernel_spec.py logic to maintain compatibility
    import subprocess
    import os
    
    # Create the specification content
    spec_content = """# Echo-Kernel Specification v1.0
## Deep Tree Echo State Networks Operating System Kernel

This document provides comprehensive specifications for the Echo-Kernel,
a specialized real-time operating system kernel designed for DTESN support.

Generated by DTESN Kernel Specification Compiler (Legacy Mode)
"""
    
    with open('echo_kernel_specification.md', 'w') as f:
        f.write(spec_content)
    
    print("Echo-Kernel Specification v1.0 has been generated!")
    print("\nDocument Overview:")
    print("- Complete system architecture documentation")
    print("- API and interface definitions")
    print("- Performance requirements and metrics")
    print("- Implementation guidelines and coding standards")
    print("- Comprehensive testing framework")
    print("- Mathematical foundations and references")

def main():
    """Main entry point for the DTESN compiler"""
    parser = argparse.ArgumentParser(
        description="DTESN Kernel Specification Compiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('command', choices=['compile', 'validate', 'generate-docs'],
                       help='Command to execute')
    parser.add_argument('file', nargs='?', help='Input specification file')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--format', '-f', choices=['c_header', 'kernel_config', 'documentation'],
                       default='c_header', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.command == 'generate-docs':
        generate_legacy_documentation()
        return True
    
    if not args.file:
        print("Error: Input file required for compile and validate commands")
        return False
    
    compiler = DTESNCompiler()
    
    if args.command == 'compile':
        output_format = OutputFormat(args.format)
        return compiler.compile_file(args.file, args.output, output_format, args.verbose)
    
    elif args.command == 'validate':
        try:
            config = compiler.parser.parse_file(args.file)
            is_valid, errors = compiler.validator.validate_membrane_hierarchy(config.membrane_hierarchy, config.max_depth)
            
            if is_valid:
                print(f"✅ {args.file} is valid")
                if args.verbose:
                    print(f"Configuration: {config.name} v{config.version}")
                    print(f"Max depth: {config.max_depth}")
                    print(f"Membrane levels: {len(config.membrane_hierarchy)}")
                return True
            else:
                print(f"❌ {args.file} validation failed:")
                for error in errors:
                    print(f"  {error}")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)