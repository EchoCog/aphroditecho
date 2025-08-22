# Lightning AI SSH Deployment Guide

## 🌩️ Direct SSH Access to Lightning AI A100s

With your SSH setup complete, you now have **direct command-line access** to Lightning AI's A100 instances. This is the optimal approach for the Aphrodite Engine build.

### ✅ SSH Setup Complete
```bash
# Your Lightning AI SSH connection:
ssh s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai

# SSH key generated: ~/.ssh/lightning_rsa
# SSH config updated: ~/.ssh/config
```

## 🚀 One-Command Deployment

### Execute Complete Build Pipeline:
```bash
./lightning_ssh_deploy.sh
```

**What this script does:**
1. **Tests SSH connection** and verifies A100 availability
2. **Uploads repository** to Lightning AI instance
3. **Configures build environment** with optimal settings
4. **Executes 347-step build** with real-time progress monitoring
5. **Downloads artifacts** automatically when complete
6. **Sets up local testing** environment with compiled binaries

## 🎯 Deployment Advantages

### **Direct SSH Benefits:**
✅ **Real-time monitoring** - See build progress live  
✅ **Interactive debugging** - SSH into running instance  
✅ **Automatic artifact download** - Get compiled binaries locally  
✅ **Cost efficiency** - Only pay for actual build time  
✅ **Full control** - Execute any commands on A100 instance  

### **Performance Comparison:**
| Method | Build Time | Interaction | Cost Control |
|--------|------------|-------------|--------------|
| **Lightning SSH** | **2-4 hours** | **Direct terminal** | **Precise** |
| GitHub Actions | 34+ hours | Limited logs | Fixed |
| Local Build | 34+ hours | Full control | Hardware cost |

## 🔧 Manual SSH Usage

### Connect to Lightning AI:
```bash
ssh s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai
```

### Manual Build Process:
```bash
# On Lightning AI instance:
git clone https://github.com/EchoCog/aphroditecho.git
cd aphroditecho
export APHRODITE_TARGET_DEVICE=cuda
export MAX_JOBS=16
export CCACHE_MAXSIZE=30G
./lightning_build.sh
```

### Download Artifacts:
```bash
# From local machine:
scp -r s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai:/path/to/artifacts ./local_artifacts/
```

## 💰 Cost Optimization

### **Estimated Costs (Your 190 tokens):**
- **A100 Instance**: ~5-6 tokens/hour
- **3-4 Hour Build**: ~15-24 tokens total
- **Storage (100GB)**: ~1 token/hour
- **Total Cost**: **~20-30 tokens for complete build**

### **Budget Allocation:**
```
Total Budget: 190 tokens
├── Teamspace (50 tokens)
│   └── Aphrodite Build: 25 tokens ✅
│   └── Buffer: 25 tokens
└── Personal (140 tokens)
    └── Development/Testing: 140 tokens
```

## 🚀 Quick Start Commands

### **Test SSH Connection:**
```bash
ssh s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai "nvidia-smi"
```

### **Execute Full Deployment:**
```bash
./lightning_ssh_deploy.sh
```

### **Monitor Build Progress:**
```bash
# SSH into running instance
ssh s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai
# Then: tail -f /tmp/aphroditecho-build/aphroditecho/build.log
```

## 🎯 Development Workflow

### **Phase 1: Local Development** (Here with Copilot)
```bash
# Develop code with GitHub Copilot assistance
# Create configurations and scripts
# Test smaller components locally
```

### **Phase 2: Lightning AI Build** (A100 Power)
```bash
# Deploy with one command
./lightning_ssh_deploy.sh

# Or step-by-step for debugging:
ssh s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai
# ... manual build process
```

### **Phase 3: Local Integration** (Artifacts Return)
```bash
# Artifacts automatically downloaded to ./lightning_artifacts/
# Install locally: pip install ./lightning_artifacts/dist/*.whl
# Test and integrate with Deep Tree Echo components
```

## 🔍 Troubleshooting

### **SSH Connection Issues:**
```bash
# Test connection
ssh -v s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai echo "test"

# Check SSH key
ls -la ~/.ssh/lightning_rsa*

# Regenerate if needed
curl -s "https://lightning.ai/setup/ssh?t=5f2cfb5b-b043-4076-a91e-1159cba38387&s=01k361x7zy5me4s7s01d24cqzc" | bash
```

### **Build Issues:**
```bash
# SSH into instance for debugging
ssh s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai

# Check CUDA environment
nvidia-smi
nvcc --version

# Monitor build progress
tail -f /tmp/aphroditecho-build/aphroditecho/build.log
```

### **Artifact Download Issues:**
```bash
# Manual download
scp -r s_01k361x7zy5me4s7s01d24cqzc@ssh.lightning.ai:/tmp/aphroditecho-build/aphroditecho/dist ./manual_artifacts/
```

## 🎉 Success Metrics

After successful deployment:
- ✅ **Build completes in 2-4 hours** (vs 34+ hours)
- ✅ **Artifacts downloaded locally** 
- ✅ **Token usage: ~20-30 tokens**
- ✅ **Local installation works**: `python -c "import aphrodite"`
- ✅ **Ready for Deep Tree Echo integration**

This SSH approach gives you **professional-grade deployment capabilities** with **full control** and **optimal performance** for your Aphrodite Engine build!
