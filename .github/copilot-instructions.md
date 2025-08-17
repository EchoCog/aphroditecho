# Aphrodite Engine - AI Coding Agent Instructions

Aphrodite Engine is a high-performance LLM inference engine built on vLLM's Paged Attention technology, designed for serving HuggingFace-compatible models at scale.

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

### Build System
- Uses setuptools with CMake for C++/CUDA extensions
- Complex build process compiles kernels for target hardware
- Build artifacts stored in `build/` directory
- Extensions built: `_C`, `_moe_C`, `_rocm_C` (device dependent)

## Linting, Formatting, and Code Quality

### Linting Commands (Validated to work)
```bash
# Ruff linting - takes ~0.5 seconds, finds ~800 issues typically
ruff check . --show-source

# Spell checking - takes ~5 seconds
codespell --toml pyproject.toml

# isort import sorting
isort --check-only .

# MyPy type checking  
mypy aphrodite/ --ignore-missing-imports
```

### Formatting Script
```bash
# The main formatting script (has version dependency issues)
bash formatting.sh

# Alternative: Run tools individually
ruff check . --fix
isort .
codespell --toml pyproject.toml --write-changes
```

**Known Issue**: `formatting.sh` expects specific tool versions defined in `requirements/lint.txt` but they're actually defined in `.github/workflows/ruff.yml`. Use individual commands if version check fails.

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

### Performance Testing
- Use `examples/` for basic functionality testing
- Benchmark scripts available but require full installation
- Monitor memory usage (takes 90% GPU VRAM by default)

## Known Issues and Workarounds

1. **Formatting Script**: Version checks may fail, use individual tools
2. **Long Installation**: Normal behavior, never cancel builds
3. **Memory Usage**: Use `--gpu-memory-utilization 0.6` or `--single-user-mode` for development
4. **Windows**: Requires building from source, limited support

## Timing Expectations

- **Linting (ruff)**: ~0.5 seconds
- **Spell checking (codespell)**: ~5 seconds  
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

# Code quality checks
ruff check . --fix
codespell --toml pyproject.toml --write-changes
isort .

# Run tests (after full installation)
pytest tests/ -v --timeout 1800

# Run example
python examples/aphrodite_engine_example.py --model microsoft/DialoGPT-medium
```

---
*Last updated: Based on repository exploration and initial validation. Some timing estimates pending full validation.*