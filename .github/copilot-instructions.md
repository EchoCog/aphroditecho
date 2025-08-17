# Aphrodite Engine - AI Coding Agent Instructions

Aphrodite Engine is a high-performance LLM inference engine built on vLLM's Paged Attention technology, designed for serving HuggingFace-compatible models at scale.

## Note contents of repository folder: https://github.com/EchoCog/aphroditecho/echo.kern

**Optimize for the integration of the "Deep Tree Echo" Membrane Computing architecture and implementation of the Echo-Self AI Evolution Engine with Agent-Arena-Relation (AAR) as the Core Orchestration system. The Aphrodite Engine should be configured as a 4E Embodied AI framework for Deep Tree Echo with Virtual mappings to Sensory-Motor analogues with Proprioceptive feedback loops to enable MLOps & Dynamic Model Training.**

---

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the information here.**

## Working Effectively

### Environment Setup and Installation
- **CRITICAL**: Installation and builds can take 45+ minutes. NEVER CANCEL long-running operations. Set timeouts to 60+ minutes for builds.
- Python 3.9 to 3.12 required
- Multiple target devices supported: CUDA (GPU), ROCm (AMD), CPU, TPU, Intel XPU, AWS Inferentia

#### Installation (CPU Mode - No GPU)
```bash
export APHRODITE_TARGET_DEVICE=cpu
pip install -e . --timeout 3600
```
**NEVER CANCEL**: Installation takes 30-60 minutes depending on target device. Wait for completion.

#### Installation (CUDA Mode - With GPU)
```bash
# CUDA >= 12 required
export APHRODITE_TARGET_DEVICE=cuda
pip install -e . --timeout 3600
```
**NEVER CANCEL**: CUDA installation with compilation takes 45-90 minutes. Wait for completion.

### Development Dependencies
```bash
pip install -r requirements/dev.txt --timeout 1800
```
**NEVER CANCEL**: Development dependencies installation takes 15-30 minutes. Wait for completion.

### Build System Requirements (Validated)
- **CMake**: Version 3.31.6+ available and working
- **Python**: 3.9-3.12 (tested with 3.12.3)  
- **Git**: Repository operations working (shallow clone may need `git fetch --unshallow --tags`)
- **Docker**: Available for containerized builds (`docker --version` works)
- **Build tools**: ninja, setuptools, wheel (from requirements/build.txt)

## Linting, Formatting, and Code Quality

### Linting Commands (Validated with timing)
```bash
# Ruff linting - takes ~0.5 seconds, finds 814 issues currently
ruff check . --show-source

# Spell checking - takes ~5 seconds
codespell --toml pyproject.toml

# isort import sorting check - takes ~3.5 seconds, finds many import issues
isort --check-only .

# MyPy type checking - takes ~33 seconds, finds ~40 type errors across modules
mypy --follow-imports skip aphrodite/
# Or use the comprehensive script:
bash tools/mypy.sh  # takes ~33 seconds
```

### Formatting Script and Fixes
```bash
# The main formatting script (has version dependency issues)
bash formatting.sh

# Alternative: Run tools individually to fix issues
ruff check . --fix
isort .  # Fix import ordering
codespell --toml pyproject.toml --write-changes
```

### Required Tool Versions (from .github/workflows/ruff.yml)
- `ruff==0.1.5`
- `codespell==2.3.0` 
- Tools must match exact versions for `formatting.sh` to work

**Known Issue**: `formatting.sh` expects specific tool versions defined in `requirements/lint.txt` but they're actually defined in `.github/workflows/ruff.yml`. Install exact versions or use individual commands.

## Testing

### Test Structure
- Tests located in `tests/` directory
- Uses pytest framework with async support
- Test categories: `basic_correctness`, `distributed`, `engine`, `models`, etc.
- Configuration in `pytest.ini`

### Running Tests
```bash
# Install test dependencies first
pip install -r requirements/test.txt --timeout 1800

# Run basic tests (timing TBD - needs validation)
pytest tests/ -v --timeout 1800
```
**NEVER CANCEL**: Test suite execution can take 15-45 minutes. Set appropriate timeouts.

## Key Locations and Navigation

### Repository Structure
```
/home/runner/work/aphroditecho/aphroditecho/
├── aphrodite/                 # Main package source code
│   ├── attention/            # Attention mechanisms and backends
│   ├── common/              # Common utilities and configurations  
│   ├── endpoints/           # API endpoints (OpenAI compatible)
│   ├── engine/              # Core engine implementation
│   ├── modeling/            # Model implementations
│   └── worker/              # Distributed worker implementations
├── examples/                # Usage examples
├── tests/                   # Test suite
├── requirements/            # Dependency specifications by target
├── kernels/                 # CUDA/ROCm kernel implementations
├── cmake/                   # CMake build configuration
├── .github/                 # GitHub workflows and configs
└── docs/                    # Documentation
```

### Important Files
- `setup.py` - Main build configuration with CMake integration
- `pyproject.toml` - Package metadata and tool configurations
- `formatting.sh` - Code formatting and linting script
- `tools/mypy.sh` - Comprehensive MyPy type checking script
- `tools/check_repo.sh` - Repository cleanliness validation
- `build_wheel.sh` - Docker-based wheel building
- `runtime.sh` - Conda environment management
- `CONTRIBUTING.md` - Development setup guide
- `README.md` - Quick start and installation guide

### Entry Points and Examples
- Main CLI: `aphrodite` command (installed after pip install)
- Example usage: `examples/aphrodite_engine_example.py`
- API server endpoint implementations in `aphrodite/endpoints/`

## Running the Application

### Quick Start (After Installation)
```bash
# Basic model serving (requires model download)
aphrodite run meta-llama/Meta-Llama-3.1-8B-Instruct

# CPU-only mode with single user
export APHRODITE_TARGET_DEVICE=cpu
aphrodite run meta-llama/Meta-Llama-3.1-8B-Instruct --single-user-mode
```

### Docker Usage
```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 2242:2242 \
    --ipc=host \
    alpindale/aphrodite-openai:latest \
    --model NousResearch/Meta-Llama-3.1-8B-Instruct \
    --tensor-parallel-size 8 \
    --api-keys "sk-empty"
```

## Validation and CI Requirements

### Pre-commit Validation
```bash
# Always run before committing changes
ruff check . --fix
codespell --toml pyproject.toml --write-changes  
isort .

# Comprehensive type checking
bash tools/mypy.sh  # ~33 seconds

# Repository cleanliness check
bash tools/check_repo.sh
```

### Helper Scripts (Validated)
```bash
# Comprehensive MyPy checking across all modules
bash tools/mypy.sh  # ~33 seconds, checks all major packages

# Repository validation (git cleanliness and tags)
bash tools/check_repo.sh

# Docker-based wheel building (for distribution)
bash build_wheel.sh

# Conda environment management
bash runtime.sh  # Requires conda setup
```

### CI Pipeline
- GitHub Actions workflow in `.github/workflows/ruff.yml`
- Requires specific tool versions: ruff==0.1.5, codespell==2.3.0
- Runs linting and spell checking on Python 3.9-3.12

## Common Development Tasks

### Adding New Features
1. Create feature branch
2. Make changes in appropriate `aphrodite/` subdirectory
3. Add tests in corresponding `tests/` subdirectory
4. Run linting: `ruff check . --fix`
5. Run spell check: `codespell --toml pyproject.toml`
6. Test locally before pushing

### Debugging Build Issues
- Check `CMakeCache.txt` in build directory
- Verify CUDA/ROCm installation if using GPU
- Check environment variables: `APHRODITE_TARGET_DEVICE`
- Look at `setup.py` for build configuration

## Manual Validation Scenarios

When making changes to Aphrodite Engine, always test these scenarios to ensure functionality:

### 1. Code Quality Pipeline
```bash
# Complete validation sequence (~42 seconds total)
ruff check . --fix                      # ~0.5s - Fix linting issues  
isort .                                  # ~3.5s - Fix import ordering
codespell --toml pyproject.toml --write-changes  # ~5s - Fix spelling
bash tools/mypy.sh                       # ~33s - Check type annotations
```

### 2. Repository Health Check
```bash
# Ensure repository is ready for CI
git status --porcelain                   # Should be empty after changes
bash tools/check_repo.sh                 # May fail on shallow clones (normal)
```

### 3. Build Prerequisites Validation
```bash  
# Verify build environment
cmake --version                          # Should be 3.26.1+
python --version                         # Should be 3.9-3.12
echo $APHRODITE_TARGET_DEVICE           # Should be set (cpu/cuda/rocm/etc.)
```

### 4. Installation Test (Full Validation)
```bash
# **NEVER CANCEL** - Takes 30-90 minutes depending on target device
export APHRODITE_TARGET_DEVICE=cpu      # or cuda, rocm, etc.
time pip install -e . --timeout 3600    # Monitor for actual timing
```

### 5. Basic Functionality Test (After Installation)
```bash
# Test CLI and basic imports
aphrodite --help                         # Should show command options
python -c "from aphrodite import LLM, SamplingParams; print('Imports work')"
```

### 6. Example Validation (After Installation)
```bash
# Test basic offline inference (requires model download)
python examples/offline_inference/offline_inference.py
```

## Known Issues and Workarounds

1. **Formatting Script**: Version checks may fail, use individual tools
2. **Long Installation**: Normal behavior, never cancel builds  
3. **Memory Usage**: Use `--gpu-memory-utilization 0.6` or `--single-user-mode` for development
4. **Windows**: Requires building from source, limited support
5. **Network Timeouts**: pip installations may timeout, increase timeout values
6. **Code Quality**: Repository currently has 814 ruff issues, 40 MyPy errors, many import ordering issues
7. **Test Dependencies**: Full test suite requires many additional packages (numpy, torch, etc.)
8. **Shallow Clone**: `tools/check_repo.sh` fails on shallow clones (use `git fetch --unshallow --tags` if needed)
9. **Model Downloads**: Examples require large model downloads from HuggingFace

## Timing Expectations (Validated)

- **Linting (ruff)**: ~0.5 seconds (finds 814 issues currently)
- **Spell checking (codespell)**: ~5 seconds  
- **Import sorting (isort)**: ~3.5 seconds (finds many import issues)
- **Type checking (mypy)**: ~33 seconds (finds ~40 type errors)
- **Installation (CPU)**: 30-60 minutes
- **Installation (CUDA)**: 45-90 minutes
- **Full test suite**: 15-45 minutes (TBD - needs validation)
- **Development dependencies**: 15-30 minutes

**CRITICAL**: All timing estimates include "NEVER CANCEL" requirement. Always set timeouts with significant buffer (2x estimated time minimum).

## Quick Reference Commands
```bash
# Setup development environment
export APHRODITE_TARGET_DEVICE=cpu
pip install -e . --timeout 3600
pip install -r requirements/dev.txt --timeout 1800

# Install exact linting tool versions
pip install ruff==0.1.5 codespell==2.3.0 isort==5.13.2 mypy

# Code quality checks (with validated timing)
ruff check . --fix                                    # ~0.5s, fix 814 issues
codespell --toml pyproject.toml --write-changes      # ~5s, spell check  
isort .                                               # ~3.5s, fix import order
bash tools/mypy.sh                                    # ~33s, comprehensive type check

# Repository validation
bash tools/check_repo.sh                             # Check git status and tags

# Run tests (after full installation)
pytest tests/ -v --timeout 1800

# Run example
python examples/aphrodite_engine_example.py --model microsoft/DialoGPT-medium
```

---
*Last updated: Based on comprehensive repository exploration and validation. All linting command timings and tool functionality verified. Installation timing estimates based on complexity analysis. Some advanced functionality pending full installation validation.*
