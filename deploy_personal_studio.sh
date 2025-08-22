#!/bin/bash
# Personal Developer Studio Deployment Script
# Optimized for individual developer pro subscription
# Generated: 2025-08-22T07:56:16.257975

set -e

echo "🏠 Personal Developer Studio - Aphrodite Engine"
echo "=============================================="
echo "Account Type: Personal Pro Developer"
echo "Cost Optimization: Enabled"
echo "Auto-shutdown: 30 minutes idle"

# Load personal studio environment
source .env.personal_studio

# Personal studio optimized build
export LIGHTNING_ACCOUNT_TYPE="personal"
export LIGHTNING_STUDIO_TIER="developer_pro"
export MAX_JOBS=8  # Conservative for personal tier
export CCACHE_MAXSIZE="10G"  # Reduced for cost optimization

# Clone and setup
echo "📦 Cloning repository..."
git clone https://github.com/EchoCog/aphroditecho.git /workspace/aphroditecho
cd /workspace/aphroditecho

# Personal studio build (cost-optimized)
echo "🔨 Building Aphrodite Engine (Personal Studio Optimized)..."
export APHRODITE_TARGET_DEVICE=cuda
pip install --timeout 3600 -e .

# Setup personal studio monitoring
echo "📊 Setting up personal studio monitoring..."
cat > monitor_personal_studio.py << 'EOF'
#!/usr/bin/env python3
import time
import psutil
import os

def monitor_usage():
    """Monitor resource usage for personal studio cost optimization"""
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Auto-shutdown if idle for too long (cost optimization)
        if cpu_percent < 5 and memory.percent < 50:
            idle_time = getattr(monitor_usage, 'idle_time', 0) + 1
            monitor_usage.idle_time = idle_time
            
            if idle_time > 30:  # 30 minutes idle
                print("💰 Auto-shutdown triggered for cost optimization")
                os.system("lightning stop")
                break
        else:
            monitor_usage.idle_time = 0
        
        print(f"💻 CPU: {cpu_percent}%, Memory: {memory.percent}%")
        time.sleep(60)

if __name__ == "__main__":
    monitor_usage()
EOF

python monitor_personal_studio.py &

echo "✅ Personal Developer Studio setup complete!"
echo "💡 Instance will auto-shutdown after 30 minutes of inactivity"
