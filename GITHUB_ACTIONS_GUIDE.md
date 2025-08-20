# 🚀 Aphrodite Engine GitHub Actions Workflows

This document provides comprehensive documentation for the automated GitHub Actions workflows implemented for the Aphrodite Engine project, including the VM-Daemon-Sys MLOps orchestration system.

## 📋 Overview

Three main workflows have been implemented to provide complete automation for building, testing, deploying, and orchestrating the Aphrodite Engine with integrated Echo Systems:

1. **[Build Engine](.github/workflows/build-engine.yml)** - Core Aphrodite Engine build automation
2. **[VM-Daemon MLOps](.github/workflows/vm-daemon-mlops.yml)** - VM-Daemon-Sys service architecture and MLOps
3. **[Echo Systems Integration](.github/workflows/echo-systems-integration.yml)** - Full integration orchestration

## 🏗️ Workflow 1: Build Engine (`build-engine.yml`)

### Purpose
Automates the complete Aphrodite Engine build process across multiple Python versions and target devices with comprehensive quality gates.

### Triggers
- **Push/PR**: Changes to `aphrodite/`, `setup.py`, `pyproject.toml`, `requirements/`, `CMakeLists.txt`
- **Manual**: `workflow_dispatch` with configurable parameters

### Key Features

#### Multi-Target Device Support
```yaml
matrix:
  include:
    - target_device: 'cpu'     # All Python versions (3.9-3.12)
    - target_device: 'cuda'    # CUDA 12.4 builds
    - target_device: 'rocm'    # ROCm builds (experimental)
    - target_device: 'tpu'     # TPU builds (experimental)
```

#### Quality Gates
- **Ruff Linting**: Code style and error checking
- **CodeSpell**: Spelling validation
- **MyPy**: Type checking with 33-second timeout
- **isort**: Import sorting validation

#### Build Configuration
- **Timeout**: 120 minutes for complex builds
- **Caching**: ccache for C++ compilation, pip cache
- **Artifacts**: Wheel files with 30-day retention
- **Echo Integration**: Tests all Echo system components

### Jobs Breakdown

1. **code-quality** (15 min) - Fast feedback quality checks
2. **build-matrix** (120 min) - Multi-configuration builds
3. **echo-integration** (20 min) - Echo systems testing
4. **build-summary** - Comprehensive reporting

### Usage Examples

```bash
# Trigger manual build for CUDA
gh workflow run build-engine.yml --ref main -f target_device=cuda -f full_test_suite=true

# Monitor build progress
gh run list --workflow=build-engine.yml
```

## 🤖 Workflow 2: VM-Daemon MLOps (`vm-daemon-mlops.yml`)

### Purpose
Implements the VM-Daemon-Sys service architecture as MLOps for Aphrodite-Zero orchestrating agent with full Echo Systems integration.

### Triggers
- **Push/PR**: Changes to Echo systems (`aar_core/`, `echo.self/`, `echo.kern/`, `echo.rkwv/`)
- **Manual**: `workflow_dispatch` with deployment mode selection

### Key Architectural Components

#### 4E Embodied AI Framework
```yaml
embodied_ai_4e:
  embodied:
    physical_simulation: true
    sensory_integration: true
  embedded:
    environment_coupling: true
    context_awareness: true
  enacted:
    action_perception_loop: true
    behavioral_adaptation: true
  extended:
    tool_use_integration: true
    cognitive_extension: true
```

#### Agent-Arena-Relation (AAR) Core
- **Agent Pool**: Configurable agent instances
- **Arena Management**: Multi-arena orchestration
- **Relation Complexity**: Adaptive relationship modeling
- **Orchestration**: Core coordination system

#### Echo-Self AI Evolution Engine
- **Evolution Cycles**: Automated AI improvement
- **Sensory-Motor Mapping**: Virtual proprioceptive feedback
- **Mutation Parameters**: Configurable evolution rates
- **Fitness Functions**: Comprehensive performance evaluation

### Jobs Breakdown

1. **validate-echo-architecture** (15 min) - Architecture validation
2. **aar-core-orchestration** (20 min) - AAR system setup
3. **echo-self-evolution** (30 min) - Evolution engine initialization
4. **vm-daemon-deployment** (25 min) - Service deployment
5. **mlops-pipeline** (20 min) - MLOps integration
6. **integration-summary** - Complete status reporting

### MLOps Pipeline Features

```yaml
mlops_pipeline:
  training:
    - continuous_training: enabled
    - model_versioning: automated
    - hyperparameter_optimization: bayesian
  inference:
    - model_serving: aphrodite_engine
    - auto_scaling: adaptive
    - load_balancing: round_robin
  monitoring:
    - performance_tracking: real_time
    - alerting: automated
    - dashboards: comprehensive
  deployment:
    - strategy: blue_green
    - rollback: automated
    - canary_releases: enabled
```

### Configuration Modes

#### Development Mode
```yaml
vm_daemon:
  mode: development
  agent_pool_size: 5
  arena_instances: 2
  continuous_training: basic
```

#### Production Mode
```yaml
vm_daemon:
  mode: production
  agent_pool_size: 50
  arena_instances: 10
  continuous_training: advanced
  monitoring: comprehensive
```

## 🌟 Workflow 3: Echo Systems Integration (`echo-systems-integration.yml`)

### Purpose
Orchestrates complete integration testing across all Echo systems with parallel workflow execution and comprehensive validation.

### Triggers
- **Push**: Main branch changes to core systems
- **Manual**: `workflow_dispatch` with integration level selection

### Integration Levels

#### Basic Integration
- Core component detection
- Basic functionality testing
- Architecture validation

#### Comprehensive Integration
- Full component testing
- Cross-system validation
- Echo systems interaction testing

#### Performance Integration
- Performance benchmarking
- Load testing
- Optimization validation

#### Production-Ready Integration
- Complete system validation
- Production deployment readiness
- Full monitoring setup

### Jobs Breakdown

1. **trigger-builds** - Parallel workflow orchestration
2. **integration-tests** (45 min) - Comprehensive testing suite
3. **validate-parallel-workflows** (10 min) - Status validation
4. **integration-complete** - Final summary and validation

### Performance Benchmarking

```python
performance_metrics = {
    "import_speed": "Module loading performance",
    "async_performance": "Concurrent operation handling", 
    "memory_usage": "Resource utilization patterns",
    "concurrent_processing": "Multi-threaded capabilities"
}
```

## 🔧 Configuration and Customization

### Environment Variables

#### Core Configuration
```yaml
env:
  CMAKE_BUILD_TYPE: Release
  MAX_JOBS: 2
  CCACHE_MAXSIZE: 2G
  APHRODITE_TARGET_DEVICE: cpu
```

#### Echo Systems Configuration
```yaml
env:
  ECHO_ENABLE_DEEP_TREE: true
  ECHO_ENABLE_VM_DAEMON: true
  AAR_CORE_ENABLED: true
  ECHO_EVOLUTION_ENABLED: true
  PROPRIOCEPTIVE_FEEDBACK_ENABLED: true
```

#### MLOps Configuration
```yaml
env:
  MLOPS_NAMESPACE: vm-daemon-sys
  CONTAINER_REGISTRY: ghcr.io
  VM_DAEMON_MODE: development|staging|production
```

### Customization Options

#### Build Matrix Customization
```yaml
strategy:
  matrix:
    include:
      # Add new target devices
      - os: ubuntu-22.04
        target_device: 'custom_device'
        experimental: true
      
      # Add new Python versions
      - python-version: '3.13'
        target_device: 'cpu'
        experimental: true
```

#### Echo Systems Customization
```yaml
# Add new Echo components
echo_components:
  echo_new_system:
    enabled: true
    priority: medium
    config:
      custom_parameter: value
```

## 📊 Monitoring and Observability

### Workflow Monitoring

#### GitHub Actions Dashboard
- Real-time workflow status
- Build duration tracking
- Failure rate monitoring
- Resource usage metrics

#### Artifact Management
- Build artifacts with 30-day retention
- Model checkpoints and configurations
- Performance benchmark results
- Integration test reports

#### Status Reporting
```markdown
## Workflow Status Summary
- Build Engine: ✅ Success (87 min)
- VM-Daemon MLOps: ✅ Success (45 min)
- Echo Integration: ✅ Success (32 min)

Total Integration Time: 2h 44min
Success Rate: 100%
```

### Performance Metrics

#### Build Performance
- **Compilation Time**: Tracked per target device
- **Cache Hit Rate**: ccache effectiveness
- **Artifact Size**: Build output optimization
- **Test Coverage**: Quality assurance metrics

#### MLOps Performance
- **Training Speed**: Model evolution rate
- **Inference Latency**: Response time optimization
- **Resource Utilization**: CPU/Memory efficiency
- **Scaling Effectiveness**: Auto-scaling responsiveness

## 🚀 Deployment and Operations

### Automated Deployment Pipeline

#### Staging Deployment
```yaml
deploy-staging:
  environment:
    name: staging
    url: https://staging.aphrodite-echo.example.com
  triggers:
    - main branch push
    - successful build completion
```

#### Production Deployment
```yaml
deploy-production:
  environment:
    name: production
    url: https://aphrodite-echo.example.com
  triggers:
    - manual approval required
    - staging validation success
```

### Rollback Procedures

#### Automated Rollback
- **Trigger**: Performance degradation detection
- **Action**: Automatic revert to last known good version
- **Validation**: Post-rollback health checks

#### Manual Rollback
```bash
# Trigger manual rollback
gh workflow run rollback.yml --ref main \
  -f environment=production \
  -f rollback_version=v1.2.3 \
  -f reason="Performance regression detected"
```

## 🛠️ Troubleshooting Guide

### Common Issues and Solutions

#### Build Failures

**CUDA Installation Issues**
```bash
# Check CUDA availability
nvidia-smi
nvcc --version

# Verify CUDA paths
echo $CUDA_HOME
echo $LD_LIBRARY_PATH
```

**Memory Issues**
```bash
# Reduce parallel jobs
export MAX_JOBS=1

# Clear build cache
rm -rf build/
ccache -C
```

**Dependency Conflicts**
```bash
# Clean pip cache
pip cache purge

# Reinstall dependencies
pip install -r requirements/build.txt --force-reinstall
```

#### MLOps Issues

**VM-Daemon Service Failures**
```yaml
# Check service status
kubectl get pods -n vm-daemon-sys

# View service logs
kubectl logs -f deployment/vm-daemon-orchestrator
```

**Echo Systems Integration Issues**
```bash
# Test Echo component availability
python -c "
import sys
from pathlib import Path

components = ['aar_core', 'echo.self', 'echo.kern', 'echo.rkwv']
for comp in components:
    status = '✅' if Path(comp).exists() else '❌'
    print(f'{status} {comp}')
"
```

#### Performance Issues

**Slow Build Times**
- Enable ccache: `ccache -s`
- Increase MAX_JOBS: `export MAX_JOBS=4`
- Use faster storage: SSD recommended

**Memory Usage**
- Monitor: `free -h`
- Optimize: `export PYTHON_GC_THRESHOLD=700,10,10`
- Clean: `pip cache purge && ccache -C`

### Debugging Commands

#### Workflow Debugging
```bash
# View workflow logs
gh run view <run-id> --log

# Download artifacts
gh run download <run-id>

# Re-run failed jobs
gh run rerun <run-id> --failed
```

#### Local Testing
```bash
# Test build locally
export APHRODITE_TARGET_DEVICE=cpu
python setup.py build_ext --inplace

# Test Echo integration
python test_integration.py

# Test MLOps pipeline
python vm-daemon-sys/main_orchestrator.py
```

## 📚 Additional Resources

### Documentation Links
- [Aphrodite Engine Documentation](https://aphrodite.pygmalion.chat)
- [Deep Tree Echo Architecture](DEEP_TREE_ECHO_ARCHITECTURE.md)
- [Echo Systems Architecture](ECHO_SYSTEMS_ARCHITECTURE.md)
- [VM-Daemon-Sys Guide](echo.rkwv/docs/vm-daemon-sys.md)

### Development Guides
- [Contributing Guidelines](CONTRIBUTING.md)
- [Development Setup](docs/installation/installation.md)
- [Testing Framework](echo.kern/docs/testing/integration-testing-guide.md)

### Community Resources
- [GitHub Issues](https://github.com/EchoCog/aphroditecho/issues)
- [Discussions](https://github.com/EchoCog/aphroditecho/discussions)
- [Project Board](https://github.com/EchoCog/aphroditecho/projects)

---

## 🎯 Quick Start Commands

### Run Full Integration
```bash
# Trigger complete integration
gh workflow run echo-systems-integration.yml --ref main \
  -f integration_level=comprehensive \
  -f enable_all_echo_systems=true
```

### Build for Production
```bash
# Build for CUDA production
gh workflow run build-engine.yml --ref main \
  -f target_device=cuda \
  -f full_test_suite=true
```

### Deploy MLOps Pipeline
```bash
# Deploy to production
gh workflow run vm-daemon-mlops.yml --ref main \
  -f deployment_mode=production \
  -f enable_aar_core=true \
  -f enable_echo_evolution=true
```

This comprehensive automation system provides production-ready CI/CD for the Aphrodite Engine with full Echo Systems integration, enabling continuous development, testing, and deployment of advanced AI systems with 4E Embodied AI architecture and proprioceptive feedback loops.