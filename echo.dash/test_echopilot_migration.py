#!/usr/bin/env python3
"""
Test for echopilot migration - both original and standardized versions

This validates that:
1. Original echopilot.py maintains backward compatibility 
2. New standardized interfaces work correctly
3. Integration between original and standardized components
"""

import sys
import asyncio
import unittest
import logging
from pathlib import Path
from unittest.mock import patch

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import both versions
try:
    import echopilot
    from echopilot import ESMWorker, ConstraintEmitter, run_cycle, create_esm_pilot_system
    ECHOPILOT_AVAILABLE = True
except ImportError as e:
    ECHOPILOT_AVAILABLE = False
    print(f"Warning: Could not import echopilot: {e}")

try:
    from echopilot_standardized import ESMWorker as ESMWorkerStandardized, ConstraintEmitter as ConstraintEmitterStandardized, create_esm_system
    from echo_component_base import EchoConfig, validate_echo_component
    ECHOPILOT_STANDARDIZED_AVAILABLE = True
except ImportError as e:
    ECHOPILOT_STANDARDIZED_AVAILABLE = False
    print(f"Warning: Could not import echopilot_standardized: {e}")


class TestEchoPilotMigration(unittest.TestCase):
    """Test cases for echopilot migration"""

    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging output during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_import_original_echopilot(self):
        """Test that original echopilot can be imported"""
        if not ECHOPILOT_AVAILABLE:
            self.skipTest("echopilot module not available")
        
        self.assertTrue(ECHOPILOT_AVAILABLE)

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available")
    def test_original_esm_worker_functionality(self):
        """Test original ESMWorker class"""
        worker = ESMWorker("test_pattern", initial_value=0.5)
        
        self.assertEqual(worker.pattern_name, "test_pattern")
        self.assertEqual(worker.state, 0.5)
        self.assertEqual(worker.iteration, 0)

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available")
    def test_original_constraint_emitter(self):
        """Test original ConstraintEmitter class"""
        emitter = ConstraintEmitter()
        
        emitter.update("pattern1", 0.5)
        emitter.update("pattern2", 0.8)
        
        constraints = emitter.get_constraints(excluding="pattern1")
        self.assertEqual(constraints, [0.8])
        
        all_constraints = emitter.get_constraints()
        self.assertEqual(len(all_constraints), 2)

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available")
    async def test_original_run_cycle(self):
        """Test original run_cycle function"""
        workers = [ESMWorker("pattern1", 0.5), ESMWorker("pattern2", 0.3)]
        emitter = ConstraintEmitter()
        
        # Initialize emitter
        for worker in workers:
            emitter.update(worker.pattern_name, worker.state)
        
        # Run cycle
        await run_cycle(workers, emitter)
        
        # Workers should have evolved
        for worker in workers:
            self.assertEqual(worker.iteration, 1)

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available")
    def test_standardized_echo_pilot_creation(self):
        """Test creating standardized Echo pilot from updated echopilot.py"""
        try:
            pilot = create_esm_pilot_system()
            self.assertIsNotNone(pilot)
            self.assertTrue(hasattr(pilot, 'process'))
            self.assertTrue(hasattr(pilot, 'echo'))
            self.assertTrue(hasattr(pilot, 'initialize'))
        except ImportError:
            # Expected if echo components not available
            self.skipTest("Echo standardized components not available")
        except Exception as e:
            self.fail(f"Failed to create standardized pilot: {e}")

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available")
    def test_standardized_echo_pilot_functionality(self):
        """Test standardized Echo pilot functionality"""
        try:
            pilot = create_esm_pilot_system()
            
            # Test basic operations
            echo_result = pilot.echo("test")
            self.assertIsNotNone(echo_result)
            self.assertTrue(echo_result.success)
            
            # Test getting states
            states_result = pilot.process("get_states")
            self.assertTrue(states_result.success)
            self.assertIn('worker_states', states_result.data)
            
        except ImportError:
            self.skipTest("Echo standardized components not available")
        except Exception as e:
            self.fail(f"Standardized functionality failed: {e}")

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available")
    def test_standardized_echo_pilot_evolution(self):
        """Test standardized Echo pilot evolution cycles"""
        try:
            pilot = create_esm_pilot_system()
            
            # Test single evolution cycle
            result = pilot.process("evolve_cycle")
            self.assertTrue(result.success)
            self.assertIn('cycle_number', result.data)
            self.assertIn('worker_states', result.data)
            
            # Test multiple cycles
            result = pilot.process({"operation": "evolve_multiple", "params": {"cycles": 2}})
            self.assertTrue(result.success)
            self.assertEqual(result.data['total_cycles_run'], 2)
            
        except ImportError:
            self.skipTest("Echo standardized components not available")
        except Exception as e:
            self.fail(f"Evolution functionality failed: {e}")

    @unittest.skipIf(not ECHOPILOT_AVAILABLE, "echopilot not available") 
    def test_backward_compatibility_main(self):
        """Test that original main function still works"""
        # Mock the prints to avoid cluttering test output
        with patch('builtins.print'):
            try:
                # This should not raise an exception
                result = asyncio.run(echopilot.main())
                # main() doesn't return anything, so we just check it completed
                self.assertIsNone(result)
            except Exception as e:
                self.fail(f"Original main function failed: {e}")

    @unittest.skipIf(not ECHOPILOT_STANDARDIZED_AVAILABLE, "echopilot_standardized not available")
    def test_esm_worker_standardization(self):
        """Test that standardized ESMWorker follows standardized interface"""
        config = EchoConfig(
            component_name="test_worker",
            version="1.0.0",
            echo_threshold=0.75
        )
        
        worker = ESMWorkerStandardized(config, "test_pattern", initial_value=0.5)
        
        # Test component validation
        self.assertTrue(validate_echo_component(worker))
        
        # Test initialization
        init_result = worker.initialize()
        self.assertTrue(init_result.success)
        self.assertTrue(worker._initialized)
        
        # Test processing with constraints
        constraints = [0.1, 0.2, 0.3]
        process_result = worker.process(constraints)
        self.assertTrue(process_result.success)
        self.assertIsInstance(process_result.data, float)
        
        # Test echo operation
        echo_result = worker.echo(None, echo_value=0.8)
        self.assertTrue(echo_result.success)
        self.assertIn('pattern_name', echo_result.data)
        self.assertEqual(echo_result.data['echo_value'], 0.8)

    @unittest.skipIf(not ECHOPILOT_STANDARDIZED_AVAILABLE, "echopilot_standardized not available")
    def test_constraint_emitter_standardization(self):
        """Test that standardized ConstraintEmitter follows standardized interface"""
        config = EchoConfig(component_name="test_emitter")
        emitter = ConstraintEmitterStandardized(config)
        
        # Test component validation
        self.assertTrue(validate_echo_component(emitter))
        
        # Test initialization
        init_result = emitter.initialize()
        self.assertTrue(init_result.success)

    def test_module_compatibility(self):
        """Test that both modules can coexist"""
        # Both original and standardized versions should be importable
        if ECHOPILOT_AVAILABLE:
            self.assertIn('echopilot', sys.modules)
        
        if ECHOPILOT_STANDARDIZED_AVAILABLE:
            self.assertIn('echopilot_standardized', sys.modules)


def run_async_tests():
    """Run async tests that can't be run in unittest framework"""
    if not ECHOPILOT_AVAILABLE:
        print("⚠️  echopilot not available, skipping async tests")
        return
    
    async def test_original_evolution_cycle():
        print("🧪 Testing original evolution cycle...")
        workers = [ESMWorker("pattern1", 0.5), ESMWorker("pattern2", 0.3)]
        emitter = ConstraintEmitter()
        
        # Initialize emitter
        for worker in workers:
            emitter.update(worker.pattern_name, worker.state)
        
        # Run cycle
        await run_cycle(workers, emitter)
        
        # Verify evolution occurred
        for worker in workers:
            assert worker.iteration == 1, f"Worker {worker.pattern_name} should have evolved"
        
        print("  ✅ Original evolution cycle test passed")
    
    # Run the async test
    asyncio.run(test_original_evolution_cycle())


def main():
    """Run all tests"""
    print("🚀 Starting Echo Pilot Migration Tests")
    print("=" * 50)
    
    # Run async tests first
    run_async_tests()
    
    # Run unittest tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ All Echo Pilot Migration tests completed")


if __name__ == '__main__':
    main()