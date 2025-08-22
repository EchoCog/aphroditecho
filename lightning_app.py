#!/usr/bin/env python3
"""
Lightning AI App for Aphrodite Engine Deployment
This creates a Lightning App that can be deployed to Lightning AI platform with A100s
"""

import lightning as L
from lightning.app import CloudCompute
import os
import subprocess
import time

class AphroditeEngineApp(L.LightningWork):
    """Lightning Work for building and running Aphrodite Engine"""
    
    def __init__(self, **kwargs):
        super().__init__(
            # Use A100 for the build process
            cloud_compute=CloudCompute("gpu-rtx", disk_size=100),
            **kwargs
        )
        self.build_complete = False
        self.build_logs = []
    
    def run(self):
        """Main execution - build and serve Aphrodite Engine"""
        
        print("🚀 Starting Aphrodite Engine build on Lightning AI...")
        
        # Step 1: Clone the repository
        self.log_and_run([
            "git", "clone", 
            "https://github.com/EchoCog/aphroditecho.git",
            "/tmp/aphroditecho"
        ])
        
        os.chdir("/tmp/aphroditecho")
        
        # Step 2: Set up environment for A100 build
        env = os.environ.copy()
        env.update({
            "APHRODITE_TARGET_DEVICE": "cuda",
            "CMAKE_BUILD_TYPE": "Release",
            "MAX_JOBS": "16",  # Lightning instances typically have 16+ cores
            "CCACHE_MAXSIZE": "30G",
            "CUDA_VISIBLE_DEVICES": "0"
        })
        
        # Step 3: Install dependencies
        self.log_and_run([
            "python", "-m", "pip", "install", "--upgrade", 
            "pip", "wheel", "setuptools", "ninja", "cmake"
        ], env=env)
        
        # Step 4: Run the optimized build
        print("🏗️ Starting Aphrodite Engine build (estimated 2-4 hours)...")
        start_time = time.time()
        
        try:
            result = self.log_and_run([
                "timeout", "14400",  # 4 hour timeout
                "python", "-m", "pip", "install", "-e", ".",
                "--timeout", "7200", "--verbose"
            ], env=env, timeout=14400)
            
            build_time = time.time() - start_time
            print(f"✅ Build completed in {build_time/3600:.1f} hours!")
            self.build_complete = True
            
        except subprocess.TimeoutExpired:
            print("❌ Build timed out after 4 hours")
            return False
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False
        
        # Step 5: Verify installation
        try:
            self.log_and_run([
                "python", "-c", 
                "import aphrodite; print(f'Aphrodite installed: {aphrodite.__version__}')"
            ], env=env)
            
            print("🎉 Aphrodite Engine build and verification complete!")
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def log_and_run(self, cmd, env=None, timeout=3600):
        """Run command with logging"""
        print(f"🔧 Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            env=env,
            timeout=timeout
        )
        
        if result.stdout:
            print(f"📤 STDOUT:\n{result.stdout}")
            self.build_logs.append(result.stdout)
        
        if result.stderr:
            print(f"📤 STDERR:\n{result.stderr}")
            self.build_logs.append(result.stderr)
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)
        
        return result


class AphroditeApp(L.LightningApp):
    """Main Lightning App for Aphrodite Engine"""
    
    def __init__(self):
        super().__init__()
        
        # Create the build work component
        self.aphrodite_work = AphroditeEngineApp()
    
    def run(self):
        """Run the app"""
        print("🌩️ Lightning AI Aphrodite Engine App Starting...")
        
        # Run the build work
        self.aphrodite_work.run()
        
        # Keep the app alive
        while True:
            if self.aphrodite_work.build_complete:
                print("✅ App ready - Aphrodite Engine built successfully!")
                print("🔗 Access your build logs and artifacts through Lightning AI dashboard")
            else:
                print("⏳ Build in progress...")
            
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    app = AphroditeApp()
    app.run()
