#!/usr/bin/env python3
"""
Test script for Unified Launcher

This script validates that the new unified launcher can handle all the
functionality from the existing launch scripts while reducing code duplication.
"""

import sys
import os
import tempfile
import unittest
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

class TestUnifiedLauncher(unittest.TestCase):
    """Test unified launcher functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        
    def test_launcher_config_creation(self):
        """Test that launcher config can be created with different modes"""
        from unified_launcher import LauncherConfig, LaunchMode
        
        # Test deep tree echo config
        config = LauncherConfig(
            mode=LaunchMode.DEEP_TREE_ECHO,
            debug=True,
            gui=True,
            browser=True
        )
        self.assertEqual(config.mode, LaunchMode.DEEP_TREE_ECHO)
        self.assertTrue(config.debug)
        self.assertTrue(config.gui)
        self.assertTrue(config.browser)
        
        # Test GUI standalone config
        gui_config = LauncherConfig(
            mode=LaunchMode.GUI_STANDALONE,
            debug=False,
            no_activity=True
        )
        self.assertEqual(gui_config.mode, LaunchMode.GUI_STANDALONE)
        self.assertFalse(gui_config.debug)
        self.assertTrue(gui_config.no_activity)
        
    def test_launcher_mode_selection(self):
        """Test that launcher can select appropriate launch mode"""
        from unified_launcher import UnifiedLauncher, LaunchMode
        
        launcher = UnifiedLauncher()
        
        # Test deep tree echo mode detection
        args = Mock()
        args.mode = 'deep-tree-echo'
        mode = launcher._determine_mode(args)
        self.assertEqual(mode, LaunchMode.DEEP_TREE_ECHO)
        
        # Test GUI mode detection
        args.mode = 'gui'
        mode = launcher._determine_mode(args)
        self.assertEqual(mode, LaunchMode.GUI_DASHBOARD)
        
    @patch('memory_management.HypergraphMemory')
    def test_component_initialization(self, mock_memory):
        """Test that core components can be initialized properly"""
        from unified_launcher import UnifiedLauncher, LauncherConfig, LaunchMode
        
        # Mock the memory system
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        
        launcher = UnifiedLauncher()
        config = LauncherConfig(mode=LaunchMode.GUI_STANDALONE)
        
        components = launcher._initialize_components(config)
        
        # Verify memory was initialized
        self.assertIsNotNone(components['memory'])
        mock_memory.assert_called_once()
        
    def test_backward_compatibility(self):
        """Test that existing launch script arguments are supported"""
        from unified_launcher import create_config_from_args
        
        # Test launch_deep_tree_echo.py style args
        args = Mock()
        args.gui = True
        args.browser = True
        args.debug = False
        
        config = create_config_from_args('deep-tree-echo', args)
        self.assertTrue(config.gui)
        self.assertTrue(config.browser)
        self.assertFalse(config.debug)
        
        # Test launch_gui_standalone.py style args
        args = Mock()
        args.debug = True
        args.no_activity = True
        
        config = create_config_from_args('gui-standalone', args)
        self.assertTrue(config.debug)
        self.assertTrue(config.no_activity)

def run_tests():
    """Run all tests"""
    # Suppress logging during tests
    logging.getLogger().setLevel(logging.WARNING)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUnifiedLauncher)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)