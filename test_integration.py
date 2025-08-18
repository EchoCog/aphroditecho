#!/usr/bin/env python3
"""
Integration test for Deep Tree Echo components.
Tests basic integration between Echo-Self and AAR modules.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add modules to path
repo_root = Path(__file__).parent
sys.path.append(str(repo_root))

# Import components (use underscore names to avoid conflicts)
from echo_self.core.evolution_engine import EchoSelfEvolutionEngine, EvolutionConfig
from aar_core.orchestration.core_orchestrator import AARCoreOrchestrator, AARConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_echo_self_basic():
    """Test basic Echo-Self Evolution Engine functionality."""
    print("🧠 Testing Echo-Self Evolution Engine...")
    
    try:
        # Create evolution engine
        config = EvolutionConfig(population_size=10, max_generations=5)
        engine = EchoSelfEvolutionEngine(config)
        
        # Test configuration
        stats = engine.get_statistics()
        assert stats['generation'] == 0
        assert stats['population_size'] == 0
        
        print("✅ Echo-Self basic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Echo-Self basic tests failed: {e}")
        return False


async def test_aar_basic():
    """Test basic AAR Core Orchestrator functionality."""
    print("🎭 Testing AAR Core Orchestrator...")
    
    try:
        # Create orchestrator
        config = AARConfig(max_concurrent_agents=10)
        orchestrator = AARCoreOrchestrator(config)
        
        # Test configuration
        stats = await orchestrator.get_orchestration_stats()
        assert stats['active_agents_count'] == 0
        assert stats['config'].max_concurrent_agents == 10
        
        print("✅ AAR basic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ AAR basic tests failed: {e}")
        return False


async def test_integration():
    """Test integration between Echo-Self and AAR."""
    print("🔗 Testing Echo-Self + AAR Integration...")
    
    try:
        # Create components
        echo_config = EvolutionConfig(population_size=5)
        echo_engine = EchoSelfEvolutionEngine(echo_config)
        
        aar_config = AARConfig(max_concurrent_agents=10)
        aar_orchestrator = AARCoreOrchestrator(aar_config)
        
        # Set up integration
        echo_engine.set_aar_integration(aar_orchestrator)
        aar_orchestrator.set_echo_self_integration(echo_engine)
        
        # Test integration status
        echo_stats = echo_engine.get_statistics()
        aar_stats = await aar_orchestrator.get_orchestration_stats()
        
        assert aar_stats['integration_status']['echo_self_engine'] == True
        
        print("✅ Integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False


async def test_module_imports():
    """Test that all modules can be imported correctly."""
    print("📦 Testing module imports...")
    
    try:
        # Test Echo-Self imports (use underscore name)
        import echo_self
        assert echo_self.get_integration_status() is not None
        
        # Test AAR imports (use underscore name)
        import aar_core
        assert aar_core.get_default_config() is not None
        
        print("✅ Module import tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Module import tests failed: {e}")
        return False


async def run_all_tests():
    """Run all integration tests."""
    print("🚀 Running Deep Tree Echo Integration Tests\n")
    
    test_results = []
    
    # Run individual tests
    test_results.append(await test_module_imports())
    test_results.append(await test_echo_self_basic())
    test_results.append(await test_aar_basic())
    test_results.append(await test_integration())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Deep Tree Echo integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        return False


async def main():
    """Main test function."""
    success = await run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())