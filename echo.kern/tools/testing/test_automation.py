#!/usr/bin/env python3
"""
DTESN Integration Test Automation Script
========================================

Automated test execution and reporting for DTESN integration tests.
Provides CI/CD integration, performance monitoring, and regression detection.
"""

import sys
import os
import subprocess
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class DTESNTestAutomation:
    """DTESN integration test automation framework"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.build_dir = self.project_root / "build"
        self.results_dir = self.project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.test_timeout = 300  # 5 minutes
        self.performance_threshold = 10.0  # 10% regression threshold
        
    def run_build(self) -> bool:
        """Build the DTESN kernel and integration tests"""
        print("🔧 Building DTESN kernel and integration tests...")
        
        try:
            # Build kernel
            result = subprocess.run(
                ["make", "-f", "Makefile.kernel", "kernel"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"❌ Kernel build failed:\n{result.stderr}")
                return False
            
            # Build integration tests
            result = subprocess.run(
                ["make", "-f", "Makefile.kernel", "integration-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"❌ Integration test build failed:\n{result.stderr}")
                return False
                
            print("✅ Build completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Build timeout exceeded")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def run_integration_tests(self) -> Dict[str, any]:
        """Run all integration tests and collect results"""
        print("🧪 Running integration test suite...")
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
        
        # Integration test executables
        integration_tests = [
            "dtesn_integration_suite",
            "cross_component_tests", 
            "performance_regression"
        ]
        
        for test_name in integration_tests:
            test_path = self.build_dir / test_name
            
            print(f"   Running {test_name}...")
            
            if not test_path.exists():
                print(f"   ⚠️  Test executable not found: {test_path}")
                test_result = {
                    "name": test_name,
                    "result": "SKIP",
                    "duration": 0.0,
                    "output": "Test executable not found"
                }
                test_results["summary"]["skipped"] += 1
            else:
                test_result = self._run_single_test(test_path)
                
                if test_result["result"] == "PASS":
                    test_results["summary"]["passed"] += 1
                elif test_result["result"] == "FAIL":
                    test_results["summary"]["failed"] += 1
                else:
                    test_results["summary"]["skipped"] += 1
            
            test_results["tests"].append(test_result)
            test_results["summary"]["total"] += 1
            
            # Print result
            result_symbol = "✅" if test_result["result"] == "PASS" else \
                           "❌" if test_result["result"] == "FAIL" else "⏭️"
            print(f"   {result_symbol} {test_name}: {test_result['result']} ({test_result['duration']:.2f}s)")
        
        return test_results
    
    def _run_single_test(self, test_path: Path) -> Dict[str, any]:
        """Run a single test executable and capture results"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [str(test_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "name": test_path.name,
                "result": "PASS" if result.returncode == 0 else "FAIL",
                "duration": duration,
                "return_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "name": test_path.name,
                "result": "TIMEOUT",
                "duration": duration,
                "return_code": -1,
                "output": "",
                "error": f"Test timeout after {self.test_timeout} seconds"
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "name": test_path.name,
                "result": "ERROR",
                "duration": duration,
                "return_code": -1,
                "output": "",
                "error": str(e)
            }
    
    def run_oeis_validation(self) -> bool:
        """Run OEIS A000081 compliance validation"""
        print("🔢 Running OEIS A000081 compliance validation...")
        
        try:
            result = subprocess.run(
                ["python3", "test_oeis_a000081.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ OEIS validation passed")
                return True
            else:
                print(f"❌ OEIS validation failed:\n{result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ OEIS validation error: {e}")
            return False
    
    def generate_report(self, test_results: Dict[str, any]) -> str:
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"integration_test_report_{timestamp}.json"
        
        # Add system information
        test_results["system_info"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": str(self.project_root)
        }
        
        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        # Generate text summary
        summary_file = self.results_dir / f"integration_test_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("DTESN Integration Test Report\n")
            f.write("============================\n\n")
            f.write(f"Timestamp: {test_results['timestamp']}\n")
            f.write(f"Total tests: {test_results['summary']['total']}\n")
            f.write(f"Passed: {test_results['summary']['passed']}\n")
            f.write(f"Failed: {test_results['summary']['failed']}\n")
            f.write(f"Skipped: {test_results['summary']['skipped']}\n\n")
            
            success_rate = 0.0
            if test_results['summary']['total'] > 0:
                success_rate = (test_results['summary']['passed'] / test_results['summary']['total']) * 100.0
            
            f.write(f"Success rate: {success_rate:.1f}%\n")
            f.write(f"Target achievement: {'✅ PASS' if success_rate >= 95.0 else '❌ FAIL'} (≥95% required)\n\n")
            
            f.write("Individual Test Results:\n")
            f.write("=======================\n")
            for test in test_results['tests']:
                f.write(f"  {test['name']}: {test['result']} ({test['duration']:.2f}s)\n")
                if test['result'] == 'FAIL' and test.get('error'):
                    f.write(f"    Error: {test['error']}\n")
        
        print(f"📄 Test report generated: {report_file}")
        print(f"📝 Test summary generated: {summary_file}")
        
        return str(report_file)
    
    def check_coverage_target(self, test_results: Dict[str, any]) -> bool:
        """Check if test coverage meets target (≥95%)"""
        if test_results['summary']['total'] == 0:
            return False
        
        success_rate = (test_results['summary']['passed'] / test_results['summary']['total']) * 100.0
        return success_rate >= 95.0
    
    def run_full_suite(self, build: bool = True, oeis_validation: bool = True) -> bool:
        """Run complete integration test suite"""
        print("🚀 DTESN Integration Test Automation")
        print("====================================\n")
        
        start_time = time.time()
        
        # Build if requested
        if build:
            if not self.run_build():
                return False
            print()
        
        # Run OEIS validation if requested
        oeis_passed = True
        if oeis_validation:
            oeis_passed = self.run_oeis_validation()
            print()
        
        # Run integration tests
        test_results = self.run_integration_tests()
        
        # Generate report
        report_file = self.generate_report(test_results)
        
        # Check results
        total_duration = time.time() - start_time
        coverage_target_met = self.check_coverage_target(test_results)
        
        print(f"\n📊 Final Results")
        print("================")
        print(f"Total runtime: {total_duration:.2f} seconds")
        print(f"Tests passed: {test_results['summary']['passed']}/{test_results['summary']['total']}")
        print(f"Coverage target (≥95%): {'✅ MET' if coverage_target_met else '❌ NOT MET'}")
        print(f"OEIS validation: {'✅ PASS' if oeis_passed else '❌ FAIL'}")
        print(f"Overall result: {'✅ SUCCESS' if (coverage_target_met and oeis_passed) else '❌ FAILURE'}")
        
        # Check timing target (≤5 minutes)
        timing_target_met = total_duration <= 300.0
        print(f"Timing target (≤5 min): {'✅ MET' if timing_target_met else '❌ EXCEEDED'} ({total_duration:.1f}s)")
        
        return coverage_target_met and oeis_passed and timing_target_met

def main():
    """Main entry point for test automation"""
    parser = argparse.ArgumentParser(description="DTESN Integration Test Automation")
    parser.add_argument("--no-build", action="store_true", help="Skip build step")
    parser.add_argument("--no-oeis", action="store_true", help="Skip OEIS validation")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    automation = DTESNTestAutomation(args.project_root)
    
    success = automation.run_full_suite(
        build=not args.no_build,
        oeis_validation=not args.no_oeis
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()