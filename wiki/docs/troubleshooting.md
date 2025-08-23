
# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues when working with Aphrodite Engine and the Deep Tree Echo system integration.

## 🚨 Common Issues

### Installation & Setup Issues

#### CUDA/GPU Related Problems

**Problem**: CUDA out of memory errors
```bash
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB (GPU 0; 23.70 GiB total capacity)
```

**Solutions**:
1. Reduce model size or tensor parallel size:
```bash
aphrodite serve --model meta-llama/Meta-Llama-3.1-7B-Instruct --tensor-parallel-size 1
```

2. Adjust GPU memory utilization:
```bash
aphrodite serve --model your-model --gpu-memory-utilization 0.8
```

3. Enable CPU offload for large models:
```bash
aphrodite serve --model your-model --cpu-offload-gb 8
```

**Problem**: CUDA version mismatch
```bash
RuntimeError: The detected CUDA version (11.8) mismatches the version that was used to compile PyTorch (12.1)
```

**Solution**: Install compatible PyTorch version:
```bash
# Check CUDA version
nvidia-smi

# Install matching PyTorch
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
```

#### Echo System Integration Issues

**Problem**: Echo systems not loading properly
```bash
ImportError: No module named 'echo.dash'
```

**Solutions**:
1. Ensure all Echo systems are properly installed:
```bash
# Check Echo system status
python -c "from aphrodite.aar_core import gateway; print(gateway.check_echo_systems())"

# Install missing Echo components
pip install -e ./echo.dash
pip install -e ./echo.dream
pip install -e ./echo.files
```

2. Verify environment variables:
```bash
export ECHO_SYSTEMS_ENABLED=true
export DEEP_TREE_ECHO_MODE=full
```

### Model Loading Issues

**Problem**: Model not found or download fails
```bash
OSError: meta-llama/Meta-Llama-3.1-70B-Instruct does not appear to be a valid repository
```

**Solutions**:
1. Check Hugging Face authentication:
```bash
huggingface-cli login
```

2. Verify model availability:
```bash
huggingface-cli repo info meta-llama/Meta-Llama-3.1-70B-Instruct
```

3. Use local model path:
```bash
aphrodite serve --model ./path/to/local/model
```

**Problem**: Quantization loading errors
```bash
ValueError: Quantization method 'awq' is not supported
```

**Solution**: Install quantization dependencies:
```bash
pip install auto-gptq autoawq
```

### API Server Issues

**Problem**: Connection refused on API calls
```bash
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**Diagnosis Steps**:
1. Check if server is running:
```bash
curl http://localhost:2242/health
```

2. Check server logs:
```bash
# If using systemd
journalctl -u aphrodite-engine -f

# If running directly
tail -f aphrodite.log
```

3. Verify port availability:
```bash
netstat -tulpn | grep 2242
```

**Problem**: High latency responses
**Diagnostic Commands**:
```bash
# Monitor GPU utilization
nvidia-smi -l 1

# Check system resources
htop

# Monitor network
iotop
```

**Solutions**:
1. Enable KV cache optimization:
```bash
aphrodite serve --model your-model --enable-prefix-caching
```

2. Adjust batch sizes:
```bash
aphrodite serve --model your-model --max-num-seqs 128
```

## 🔍 Diagnostic Tools

### Echo System Health Check
```python
# echo_diagnostics.py
import json
import subprocess
from pathlib import Path

def check_echo_systems():
    """Comprehensive Echo system health check"""
    results = {}
    
    # Check each Echo system
    echo_systems = ['dash', 'dream', 'files', 'kern', 'rkwv', 'self']
    
    for system in echo_systems:
        try:
            # Check if module can be imported
            __import__(f'echo.{system}')
            results[system] = {'status': 'OK', 'issues': []}
        except ImportError as e:
            results[system] = {'status': 'ERROR', 'issues': [str(e)]}
        except Exception as e:
            results[system] = {'status': 'WARNING', 'issues': [str(e)]}
    
    # Check configuration
    config_issues = []
    if not os.getenv('ECHO_SYSTEMS_ENABLED'):
        config_issues.append('ECHO_SYSTEMS_ENABLED not set')
    
    if not os.getenv('DEEP_TREE_ECHO_MODE'):
        config_issues.append('DEEP_TREE_ECHO_MODE not set')
    
    results['configuration'] = {
        'status': 'OK' if not config_issues else 'WARNING',
        'issues': config_issues
    }
    
    return results

def print_health_report():
    """Print formatted health report"""
    results = check_echo_systems()
    
    print("🔍 Echo Systems Health Check")
    print("=" * 50)
    
    for system, status in results.items():
        indicator = "✅" if status['status'] == 'OK' else "❌" if status['status'] == 'ERROR' else "⚠️"
        print(f"{indicator} {system.upper()}: {status['status']}")
        
        if status['issues']:
            for issue in status['issues']:
                print(f"   └── {issue}")
    
    print("\n📊 Overall Status:", "HEALTHY" if all(s['status'] == 'OK' for s in results.values()) else "ISSUES DETECTED")

if __name__ == "__main__":
    print_health_report()
```

### Performance Monitoring Script
```python
# performance_monitor.py
import psutil
import GPUtil
import time
import requests
import threading
from collections import deque

class AphroditeMonitor:
    def __init__(self, api_url="http://localhost:2242"):
        self.api_url = api_url
        self.metrics = {
            'cpu_usage': deque(maxlen=60),
            'memory_usage': deque(maxlen=60),
            'gpu_usage': deque(maxlen=60),
            'api_latency': deque(maxlen=60)
        }
        self.running = False
    
    def start_monitoring(self):
        """Start monitoring system metrics"""
        self.running = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_system, daemon=True).start()
        threading.Thread(target=self._monitor_api, daemon=True).start()
        
        print("🔍 Monitoring started. Press Ctrl+C to stop.")
        try:
            while self.running:
                self._print_status()
                time.sleep(5)
        except KeyboardInterrupt:
            self.running = False
            print("\n📊 Monitoring stopped.")
    
    def _monitor_system(self):
        """Monitor system resources"""
        while self.running:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].append(cpu_percent)
            
            # Memory usage
            memory_percent = psutil.virtual_memory().percent
            self.metrics['memory_usage'].append(memory_percent)
            
            # GPU usage
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_percent = gpus[0].load * 100
                    self.metrics['gpu_usage'].append(gpu_percent)
            except Exception:
                pass
            
            time.sleep(1)
    
    def _monitor_api(self):
        """Monitor API response times"""
        test_payload = {
            "model": "default",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 1
        }
        
        while self.running:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_url}/v1/chat/completions",
                    json=test_payload,
                    timeout=30
                )
                latency = (time.time() - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    self.metrics['api_latency'].append(latency)
                else:
                    self.metrics['api_latency'].append(-1)  # Error indicator
                
            except Exception:
                self.metrics['api_latency'].append(-1)  # Error indicator
            
            time.sleep(10)  # Check API every 10 seconds
    
    def _print_status(self):
        """Print current status"""
        print("\n" + "="*60)
        print("📊 APHRODITE ENGINE PERFORMANCE MONITOR")
        print("="*60)
        
        # System metrics
        if self.metrics['cpu_usage']:
            cpu_avg = sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage'])
            print(f"🖥️  CPU Usage: {cpu_avg:.1f}%")
        
        if self.metrics['memory_usage']:
            mem_avg = sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
            print(f"💾 Memory Usage: {mem_avg:.1f}%")
        
        if self.metrics['gpu_usage']:
            gpu_avg = sum(self.metrics['gpu_usage']) / len(self.metrics['gpu_usage'])
            print(f"🎮 GPU Usage: {gpu_avg:.1f}%")
        
        # API metrics
        if self.metrics['api_latency']:
            valid_latencies = [l for l in self.metrics['api_latency'] if l > 0]
            if valid_latencies:
                latency_avg = sum(valid_latencies) / len(valid_latencies)
                print(f"⚡ API Latency: {latency_avg:.1f}ms")
            
            error_count = len([l for l in self.metrics['api_latency'] if l < 0])
            if error_count > 0:
                print(f"❌ API Errors: {error_count}")

if __name__ == "__main__":
    monitor = AphroditeMonitor()
    monitor.start_monitoring()
```

### Log Analysis Tool
```python
# log_analyzer.py
import re
import json
from collections import defaultdict, Counter
from datetime import datetime

class LogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.patterns = {
            'error': re.compile(r'ERROR.*?(?=\n|\r|$)', re.IGNORECASE),
            'warning': re.compile(r'WARNING.*?(?=\n|\r|$)', re.IGNORECASE),
            'cuda_oom': re.compile(r'CUDA out of memory', re.IGNORECASE),
            'request_id': re.compile(r'request_id[:\s]+([a-f0-9-]+)', re.IGNORECASE),
            'timestamp': re.compile(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}')
        }
    
    def analyze(self):
        """Analyze log file and generate report"""
        with open(self.log_file_path, 'r') as f:
            log_content = f.read()
        
        analysis = {
            'summary': self._generate_summary(log_content),
            'errors': self._extract_errors(log_content),
            'warnings': self._extract_warnings(log_content),
            'performance': self._analyze_performance(log_content),
            'recommendations': self._generate_recommendations(log_content)
        }
        
        return analysis
    
    def _generate_summary(self, log_content):
        """Generate log summary statistics"""
        lines = log_content.split('\n')
        
        return {
            'total_lines': len(lines),
            'error_count': len(self.patterns['error'].findall(log_content)),
            'warning_count': len(self.patterns['warning'].findall(log_content)),
            'cuda_oom_count': len(self.patterns['cuda_oom'].findall(log_content))
        }
    
    def _extract_errors(self, log_content):
        """Extract and categorize errors"""
        errors = self.patterns['error'].findall(log_content)
        error_categories = defaultdict(list)
        
        for error in errors:
            if 'CUDA' in error.upper():
                error_categories['CUDA'].append(error)
            elif 'MODEL' in error.upper():
                error_categories['Model'].append(error)
            elif 'NETWORK' in error.upper() or 'CONNECTION' in error.upper():
                error_categories['Network'].append(error)
            else:
                error_categories['Other'].append(error)
        
        return dict(error_categories)
    
    def _extract_warnings(self, log_content):
        """Extract warnings"""
        warnings = self.patterns['warning'].findall(log_content)
        return warnings[:10]  # Return first 10 warnings
    
    def _analyze_performance(self, log_content):
        """Analyze performance indicators"""
        # Look for timing information, request rates, etc.
        request_ids = self.patterns['request_id'].findall(log_content)
        
        return {
            'unique_requests': len(set(request_ids)),
            'total_requests': len(request_ids)
        }
    
    def _generate_recommendations(self, log_content):
        """Generate recommendations based on log analysis"""
        recommendations = []
        
        if 'CUDA out of memory' in log_content:
            recommendations.append("Consider reducing model size or enabling CPU offload")
        
        if self.patterns['error'].findall(log_content):
            recommendations.append("Check error logs for recurring issues")
        
        if 'timeout' in log_content.lower():
            recommendations.append("Consider increasing timeout values for long-running requests")
        
        return recommendations

def analyze_logs(log_file_path):
    """Main function to analyze logs and print report"""
    analyzer = LogAnalyzer(log_file_path)
    analysis = analyzer.analyze()
    
    print("📋 LOG ANALYSIS REPORT")
    print("=" * 50)
    
    # Summary
    summary = analysis['summary']
    print(f"📊 Total log lines: {summary['total_lines']}")
    print(f"❌ Errors: {summary['error_count']}")
    print(f"⚠️  Warnings: {summary['warning_count']}")
    print(f"🎮 CUDA OOM errors: {summary['cuda_oom_count']}")
    
    # Errors by category
    if analysis['errors']:
        print("\n🔍 ERROR BREAKDOWN:")
        for category, errors in analysis['errors'].items():
            print(f"   {category}: {len(errors)} errors")
    
    # Recommendations
    if analysis['recommendations']:
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"   {i}. {rec}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python log_analyzer.py <log_file_path>")
        sys.exit(1)
    
    analyze_logs(sys.argv[1])
```

## 🛠️ Quick Fixes

### Memory Issues
```bash
# Clear GPU memory
python -c "import torch; torch.cuda.empty_cache()"

# Check available memory
python -c "import torch; print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')"
```

### Service Management
```bash
# Restart Aphrodite service (if using systemd)
sudo systemctl restart aphrodite-engine

# Check service status
sudo systemctl status aphrodite-engine

# View recent logs
sudo journalctl -u aphrodite-engine --since "10 minutes ago"
```

### Network Troubleshooting
```bash
# Test API endpoint
curl -X POST http://localhost:2242/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'

# Check port binding
ss -tlnp | grep :2242
```

## 📞 Getting Help

### Log Files Location
- **System logs**: `/var/log/aphrodite/`
- **Application logs**: `./aphrodite.log`
- **Echo system logs**: `./echo_*.log`

### Debug Mode
Enable debug logging for detailed information:
```bash
aphrodite serve --model your-model --log-level DEBUG
```

### Community Support
- **GitHub Issues**: [Report bugs and issues](https://github.com/PygmalionAI/aphrodite-engine/issues)
- **Documentation**: [Official documentation](https://aphrodite.pygmalion.chat)
- **Discord**: Join the community for real-time help

This troubleshooting guide should help you quickly identify and resolve most common issues with Aphrodite Engine and Deep Tree Echo integration.


# Troubleshooting Guide

Common issues and their solutions when working with the Deep Tree Echo system.

## Installation and Setup Issues

### Port Conflicts
**Problem**: Services fail to start due to port conflicts
**Solution**: 
- Check which ports are in use: `netstat -tulpn`
- Configure alternative ports in service configuration files
- Ensure port forwarding is properly configured in Replit

### Memory Issues
**Problem**: System runs out of memory or performs poorly
**Solution**:
- Check memory usage: `htop` or `top`
- Adjust memory limits in configuration files
- Clear temporary files and caches
- Restart memory-intensive components

### Permission Errors
**Problem**: File or directory access denied
**Solution**:
- Check file permissions: `ls -la`
- Ensure proper ownership of files
- Verify Replit environment permissions

## Runtime Issues

### Service Connectivity
**Problem**: Components cannot communicate with each other
**Solution**:
- Verify all services are running
- Check network configuration
- Review firewall/security settings
- Test API endpoints individually

### Memory System Errors
**Problem**: Memory operations fail or return unexpected results
**Solution**:
- Check memory system logs
- Verify memory database integrity
- Clear corrupted memory entries
- Restart memory management service

### Performance Degradation
**Problem**: System becomes slow or unresponsive
**Solution**:
- Monitor CPU and memory usage
- Check for infinite loops or resource leaks
- Review recent configuration changes
- Restart affected components

## API and Integration Issues

### Authentication Failures
**Problem**: API requests fail with authentication errors
**Solution**:
- Verify API keys and tokens
- Check authentication configuration
- Ensure proper request headers
- Review user permissions

### Data Serialization Errors
**Problem**: Data cannot be properly serialized/deserialized
**Solution**:
- Validate data format and structure
- Check for unsupported data types
- Review encoding settings
- Update serialization libraries

### Timeout Issues
**Problem**: Requests timeout or take too long to complete
**Solution**:
- Increase timeout values in configuration
- Optimize query complexity
- Check network connectivity
- Review system performance

## Development Issues

### Build Failures
**Problem**: Code fails to compile or build
**Solution**:
- Check compiler errors and warnings
- Verify all dependencies are installed
- Review build configuration
- Clean and rebuild from scratch

### Test Failures
**Problem**: Unit or integration tests fail
**Solution**:
- Review test error messages
- Check test data and fixtures
- Verify test environment setup
- Update tests for code changes

### Extension Problems
**Problem**: Custom extensions don't load or work properly
**Solution**:
- Check extension configuration
- Review extension logs
- Verify API compatibility
- Test extension in isolation

## Diagnostic Tools

### Log Analysis
Check system logs for error details:
```bash
# Main system logs
tail -f echo.dash/logs/system.log

# Memory system logs
tail -f echo.memory/logs/memory.log

# API logs
tail -f echo.api/logs/api.log
```

### Health Checks
Run built-in diagnostic tools:
```bash
# System health check
python echo.dash/diagnostic.py --full

# Memory integrity check
python echo.memory/check_integrity.py

# API endpoint test
python echo.api/test_endpoints.py
```

### Performance Monitoring
Monitor system performance:
```bash
# Resource usage
htop

# Network connections
netstat -tulpn

# Disk usage
df -h
```

## Getting Help

### Documentation Resources
- [Architecture Overview](architecture/overview.md)
- [API Reference](technical/specifications.md)
- [Development Guide](guides/dev/development-environment.md)

### Community Support
- GitHub Issues: Report bugs and request features
- Discussion Forums: Ask questions and share solutions
- Code Reviews: Get feedback on implementations

### Professional Support
For enterprise deployments:
- Priority support channels
- Custom integration assistance
- Performance optimization consulting

## Prevention Tips

### Regular Maintenance
- Keep system updated
- Monitor resource usage
- Review logs regularly
- Backup important data

### Best Practices
- Follow coding standards
- Write comprehensive tests
- Document configuration changes
- Use version control effectively

### Monitoring Setup
- Configure alerting for critical issues
- Set up automated health checks
- Monitor performance metrics
- Track error rates and patterns
