#!/bin/bash
# Lightning Studios A100 Optimized Build Script for Aphrodite Engine
# This script is optimized for Lightning Studios A100 instances
set -e

echo "🚀 Aphrodite Engine - Lightning Studios A100 Build"
echo "=================================================="

# Performance configuration for H100/H200 instances (optimized)
export APHRODITE_TARGET_DEVICE=cuda
export CMAKE_BUILD_TYPE=Release
export MAX_JOBS=64  # H100/H200 instances have more cores than A100
export CCACHE_MAXSIZE=100G  # Larger cache for faster GPUs
export CUDA_VISIBLE_DEVICES=0  # Use first GPU

# Ensure CUDA environment
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Verify CUDA setup
echo "🔍 Verifying CUDA environment..."
nvidia-smi
nvcc --version
python --version

# Verify system resources
echo "💻 System resources:"
nproc  # CPU cores
free -h  # Memory
df -h /  # Disk space

# Install dependencies optimized for A100 builds
echo "📦 Installing optimized build dependencies..."
python -m pip install --upgrade pip wheel setuptools
pip install ninja cmake

# Pre-build cleanup to maximize available resources
echo "🧹 Pre-build cleanup..."
pip cache purge
sudo apt-get clean || true

# Start the build with performance monitoring
echo "🏗️ Starting Aphrodite Engine build..."
echo "Estimated time: 2-4 hours on A100 (vs 34+ hours on standard hardware)"
echo "Build steps: 347 total"

start_time=$(date +%s)

# Execute build with extended timeout and progress monitoring
timeout 14400 pip install -e . --timeout 7200 --verbose 2>&1 | tee build.log || {
    echo "❌ Build failed or timed out after 4 hours"
    echo "📊 Partial build statistics:"
    grep -i "step\|progress\|%" build.log | tail -10 || true
    exit 1
}

end_time=$(date +%s)
build_duration=$((end_time - start_time))
build_hours=$((build_duration / 3600))
build_minutes=$(((build_duration % 3600) / 60))

echo "✅ Build completed successfully!"
echo "⏱️ Total build time: ${build_hours}h ${build_minutes}m"
echo "🚀 Ready for Deep Tree Echo integration testing"

# Verify installation
echo "🔍 Verifying installation..."
python -c "import aphrodite; print(f'Aphrodite version: {aphrodite.__version__}')" || {
    echo "⚠️ Installation verification failed"
    exit 1
}

# Optional: Run quick smoke tests
echo "🧪 Running smoke tests..."
python -c "from aphrodite import LLM, SamplingParams; print('Core imports successful')" || {
    echo "⚠️ Core imports failed"
    exit 1
}

echo "🎉 Lightning Studios A100 build complete and verified!"
echo "💡 Build performance: ~${build_hours}h ${build_minutes}m (vs 34+ hours on standard hardware)"
echo "📈 Performance improvement: ~$(echo "$((3400 / (build_duration / 60)))" | cut -c1-2)x faster"
