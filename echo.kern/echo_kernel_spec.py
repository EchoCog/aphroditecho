#!/usr/bin/env python3
"""
Legacy Echo Kernel Specification Generator

This script maintains backward compatibility with the original echo_kernel_spec.py
while delegating to the new DTESN Kernel Specification Compiler.
"""

import sys
import subprocess
import os

def main():
    """Main entry point - delegates to the new DTESN compiler"""
    try:
        # Use the new compiler for legacy documentation generation
        result = subprocess.run([
            sys.executable, 'dtesn_compiler.py', 'generate-docs'
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        return result.returncode == 0
    except Exception as e:
        print(f"Error running DTESN compiler: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)