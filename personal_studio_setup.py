#!/usr/bin/env python3
"""
Personal Developer Studio Configuration
Reconfigured for individual developer pro instance instead of team account
"""

import os
import json
import time
import requests
import subprocess
from         print("✅ Personal Developer Studio setup complete!")
        print(f"📁 Configuration saved to: {self.config_file}")
        print("\n📋 Next Steps:")
        print("1. Install Lightning CLI: pip install lightning")
        print("2. Login to your PERSONAL account: lightning login")
        print("3. Deploy: lightning run app ./deploy_personal_studio.sh")
        print("\n💰 Cost Optimization Features:")
        print("- Auto-shutdown after 30 minutes idle")
        print("- Conservative resource limits")
        print("- Budget monitoring and alerts")
        print("- gpu-rtx compute for cost efficiency")
        
        return {
            "env_file": env_file,
            "deploy_script": deploy_script,
            "config_file": config_file
        }atetime
from pathlib import Path

class PersonalStudioManager:
    """Manager for personal developer studio Lightning AI deployments"""
    
    def __init__(self):
        self.config_file = Path.home() / ".lightning_personal_config.json"
        self.config = self.load_config()
        self.is_personal_account = True
        
    def load_config(self):
        """Load personal studio configuration"""
        default_config = {
            "account_type": "personal_pro",
            "studio_tier": "developer_pro",
            "compute_limits": {
                "gpu_hours_monthly": 100,  # Typical personal pro limit
                "max_concurrent_instances": 3,
                "storage_gb": 500
            },
            "preferred_compute": "gpu-rtx",  # Cost-effective for personal use
            "cost_optimization": True,
            "auto_shutdown_minutes": 30
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                default_config.update(loaded_config)
                return default_config
        return default_config
    
    def save_config(self):
        """Save personal studio configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_personal_environment(self):
        """Set up environment variables for personal studio"""
        env_vars = {
            "LIGHTNING_ACCOUNT_TYPE": "personal",
            "LIGHTNING_STUDIO_TIER": "developer_pro", 
            "LIGHTNING_COST_OPTIMIZATION": "true",
            "LIGHTNING_AUTO_SHUTDOWN": "30",
            "APHRODITE_TARGET_DEVICE": "cuda",
            "PERSONAL_STUDIO_MODE": "true"
        }
        
        # Create .env file for personal studio
        env_file = Path(".env.personal_studio")
        with open(env_file, 'w') as f:
            f.write("# Personal Developer Studio Configuration\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Created personal studio environment file: {env_file}")
        return env_file
    
    def create_personal_deployment_script(self):
        """Create deployment script optimized for personal developer pro account"""
        
        script_content = f'''#!/bin/bash
# Personal Developer Studio Deployment Script
# Optimized for individual developer pro subscription
# Generated: {datetime.now().isoformat()}

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
        
        print(f"💻 CPU: {{cpu_percent}}%, Memory: {{memory.percent}}%")
        time.sleep(60)

if __name__ == "__main__":
    monitor_usage()
EOF

python monitor_personal_studio.py &

echo "✅ Personal Developer Studio setup complete!"
echo "💡 Instance will auto-shutdown after 30 minutes of inactivity"
'''
        
        script_file = Path("deploy_personal_studio.sh")
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        print(f"✅ Created personal studio deployment script: {{script_file}}")
        return script_file
    
    def create_cost_optimized_config(self):
        """Create Lightning AI config optimized for personal developer pro account"""
        
        config_content = {
            "name": "aphrodite-personal-studio",
            "compute": {
                "type": "gpu-rtx",  # Cost-effective GPU option
                "disk_size": 50,    # Conservative disk size
                "auto_shutdown": 30  # Auto-shutdown after 30min idle
            },
            "environment": {
                "python_version": "3.11",
                "requirements": [
                    "torch>=2.0.0",
                    "transformers>=4.30.0"
                ]
            },
            "cost_optimization": {
                "enabled": True,
                "max_runtime_hours": 4,  # Prevent runaway costs
                "alert_threshold_usd": 10
            },
            "personal_studio": {
                "account_type": "developer_pro",
                "tier": "personal",
                "budget_limit_monthly": 100
            }
        }
        
        config_file = Path("lightning_personal.yaml")
        import yaml
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f, default_flow_style=False, indent=2)
        except ImportError:
            # Fallback to JSON if PyYAML not available
            config_file = Path("lightning_personal.json")
            with open(config_file, 'w') as f:
                json.dump(config_content, f, indent=2)
        
        print(f"✅ Created cost-optimized config: {config_file}")
        return config_file
    
    def setup_personal_studio_complete(self):
        """Complete setup for personal developer studio"""
        print("🏠 Setting up Personal Developer Studio Configuration...")
        print("=" * 60)
        
        # Step 1: Environment setup
        env_file = self.setup_personal_environment()
        
        # Step 2: Deployment script
        deploy_script = self.create_personal_deployment_script()
        
        # Step 3: Cost-optimized config
        config_file = self.create_cost_optimized_config()
        
        # Step 4: Save configuration
        self.config["setup_date"] = datetime.now().isoformat()
        self.config["files_created"] = [
            str(env_file),
            str(deploy_script), 
            str(config_file)
        ]
        self.save_config()
        
        print("\n✅ Personal Developer Studio setup complete!")
        print(f"📁 Configuration saved to: {{self.config_file}}")
        print("\n📋 Next Steps:")
        print("1. Install Lightning CLI: pip install lightning")
        print("2. Login to your PERSONAL account: lightning login")
        print("3. Deploy: lightning run app ./deploy_personal_studio.sh")
        print("\n💰 Cost Optimization Features:")
        print("- Auto-shutdown after 30 minutes idle")
        print("- Conservative resource limits")
        print("- Budget monitoring and alerts")
        print("- gpu-rtx compute for cost efficiency")
        
        return {{
            "env_file": env_file,
            "deploy_script": deploy_script,
            "config_file": config_file
        }}

if __name__ == "__main__":
    manager = PersonalStudioManager()
    result = manager.setup_personal_studio_complete()
    print(f"\n🎉 Personal Developer Studio ready! Files: {{list(result.values())}}")
