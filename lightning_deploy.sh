#!/bin/bash
# Generated Lightning AI deployment script - Personal Developer Pro
# Created: 2025-08-22T09:18:08.334140
# Build Type: cuda
# Account: Personal Developer Pro Studio

set -e

echo "🏠 Personal Developer Pro - Aphrodite Engine Lightning AI Deployment"
echo "=================================================================="
echo "💰 Cost Optimization: Enabled"
echo "⏱️ Auto-shutdown: 30 minutes idle"

# Clone repository
git clone https://github.com/EchoCog/aphroditecho.git /tmp/aphroditecho
cd /tmp/aphroditecho

# Set environment for cuda build
export APHRODITE_TARGET_DEVICE=cuda
export CMAKE_BUILD_TYPE=Release
export MAX_JOBS=16
export CCACHE_MAXSIZE=30G

# Verify environment
echo "🔍 Environment verification:"
nvidia-smi
python --version
nvcc --version

# Run optimized build
echo "🏗️ Starting build process..."
time ./lightning_build.sh

# Create artifact package
echo "📦 Creating deployment artifacts..."
mkdir -p /tmp/artifacts
cp -r dist/ /tmp/artifacts/ || true
cp build.log /tmp/artifacts/ || true

echo "✅ Deployment complete - artifacts in /tmp/artifacts/"
