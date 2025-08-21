# DTESN Kernel Specification Compiler

## Overview

The DTESN (Deep Tree Echo State Network) Kernel Specification Compiler is a tool for parsing, validating, and compiling DTESN kernel specifications. It validates specifications against OEIS A000081 mathematical constraints and generates various output formats including C headers, kernel configurations, and documentation.

## Features

- **Specification Parsing**: Parse DTESN specification files using a custom DSL
- **OEIS A000081 Validation**: Validate membrane hierarchy against mathematical constraints
- **Multiple Output Formats**: Generate C headers, kernel configs, and documentation
- **CLI Interface**: Command-line interface for easy integration
- **Backward Compatibility**: Maintains compatibility with original echo_kernel_spec.py

## Usage

### Command Line Interface

```bash
# Validate a specification file
python3 dtesn_compiler.py validate examples/basic_dtesn.dtspec --verbose

# Compile to C header
python3 dtesn_compiler.py compile examples/basic_dtesn.dtspec --output config.h

# Compile to kernel configuration
python3 dtesn_compiler.py compile examples/basic_dtesn.dtspec --format kernel_config --output kernel.config

# Generate documentation
python3 dtesn_compiler.py compile examples/basic_dtesn.dtspec --format documentation --output spec.md

# Generate legacy documentation
python3 dtesn_compiler.py generate-docs
```

### DTESN Specification Format

The compiler uses a custom DSL for DTESN specifications:

```dtspec
dtesn_config {
    name: "BasicEchoKernel"
    version: "1.0"
    max_depth: 4
    
    membrane_hierarchy {
        level: 0, count: 1, neurons: 100, type: "root"
        level: 1, count: 1, neurons: 200, type: "trunk" 
        level: 2, count: 1, neurons: 150, type: "branch"
        level: 3, count: 2, neurons: 100, type: "leaf"
        level: 4, count: 4, neurons: 50, type: "terminal"
    }
    
    esn_parameters {
        spectral_radius: 0.9
        input_scaling: 0.1
        leak_rate: 0.3
        connectivity: 0.1
    }
    
    timing_constraints {
        membrane_evolution_max_us: 10
        bseries_computation_max_us: 100
        esn_update_max_ms: 1
        context_switch_max_us: 5
    }
    
    memory_layout {
        user_space: "0x00000000-0x3FFFFFFF"
        membrane_reservoirs: "0x40000000-0x7FFFFFFF"
        bseries_trees: "0x80000000-0xBFFFFFFF"
        kernel_space: "0xC0000000-0xFFFFFFFF"
    }
}
```

## OEIS A000081 Validation

The compiler validates membrane hierarchy counts against the OEIS A000081 sequence (number of unlabeled rooted trees with n nodes):

- Level 0: 1 (root)
- Level 1: 1
- Level 2: 1  
- Level 3: 2
- Level 4: 4
- Level 5: 9
- ...

## Output Formats

### C Header Format
Generates C header files with configuration constants and data structures suitable for kernel compilation.

### Kernel Config Format  
Generates kernel configuration files compatible with Linux kernel build systems.

### Documentation Format
Generates markdown documentation from the specification.

## Implementation Architecture

- **DTESNParser**: Parses DTESN specification files
- **OEIS_A000081_Validator**: Validates against mathematical constraints
- **DTESNCompiler**: Orchestrates parsing, validation, and code generation
- **Output Generators**: Generate different output formats

## Backward Compatibility

The original `echo_kernel_spec.py` is maintained for backward compatibility and delegates to the new compiler for legacy documentation generation.

## Examples

See the `examples/` directory for sample DTESN specification files.