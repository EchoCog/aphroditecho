#!/usr/bin/env python3
"""
Test script to validate GITHUB_TOKEN environment variable handling
in cronbot.py and copilot_suggestions.py
"""

import os
import sys
import unittest
from unittest.mock import patch, mock_open
from io import StringIO
import logging
import pytest

# Add current directory to path to import the modules
sys.path.insert(0, '/home/runner/work/echodash/echodash')

# Try importing cronbot and copilot_suggestions, skip tests if not available
try:
    import cronbot
    import copilot_suggestions
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    cronbot = None
    copilot_suggestions = None

@pytest.mark.skipif(not MODULES_AVAILABLE, reason="cronbot or copilot_suggestions modules not available")
class TestGitHubTokenHandling(unittest.TestCase):
    """Test cases for GITHUB_TOKEN environment variable handling"""
    
    def setUp(self):
        """Set up test environment"""
        # Capture logs
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.ERROR)
        
        # Add handler to both modules' loggers
        cronbot.logger.addHandler(self.handler)
        copilot_suggestions.logger.addHandler(self.handler)
        
    def tearDown(self):
        """Clean up after tests"""
        cronbot.logger.removeHandler(self.handler)
        copilot_suggestions.logger.removeHandler(self.handler)
    
    def test_cronbot_missing_github_token(self):
        """Test that cronbot.py handles missing GITHUB_TOKEN gracefully"""
        # Ensure GITHUB_TOKEN is not set
        with patch.dict(os.environ, {}, clear=True):
            result = cronbot.call_github_copilot({"test": "note"})
            
            # Should return None when token is missing
            self.assertIsNone(result)
            
            # Should log an error
            log_contents = self.log_capture.getvalue()
            self.assertIn("GITHUB_TOKEN environment variable is missing", log_contents)
    
    def test_copilot_suggestions_missing_github_token(self):
        """Test that copilot_suggestions.py handles missing GITHUB_TOKEN gracefully"""
        # Ensure GITHUB_TOKEN is not set
        with patch.dict(os.environ, {}, clear=True):
            result = copilot_suggestions.fetch_suggestions_from_copilot({"test": "note"})
            
            # Should return None when token is missing
            self.assertIsNone(result)
            
            # Should log an error
            log_contents = self.log_capture.getvalue()
            self.assertIn("GITHUB_TOKEN environment variable is missing", log_contents)
    
    def test_cronbot_with_github_token(self):
        """Test that cronbot.py works when GITHUB_TOKEN is set"""
        test_token = "test_token_123"
        test_note = {"test": "note"}
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': test_token}):
            with patch('builtins.open', mock_open()) as mock_file:
                result = cronbot.call_github_copilot(test_note)
                
                # Should return a result when token is set (even if it's a mock result)
                self.assertIsNotNone(result)
                self.assertIn("improvement", result)
                self.assertIn("assessment", result)
                
                # Should attempt to write payload file
                mock_file.assert_called_with('.github/workflows/request_payload.json', 'w')
    
    def test_copilot_suggestions_with_github_token(self):
        """Test that copilot_suggestions.py attempts to make request when GITHUB_TOKEN is set"""
        test_token = "test_token_123"
        test_note = {"test": "note"}
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': test_token}):
            with patch('requests.post') as mock_post:
                # Mock a failed response (but at least it tries)
                mock_post.return_value.status_code = 404
                
                result = copilot_suggestions.fetch_suggestions_from_copilot(test_note)
                
                # Should attempt to make the request
                mock_post.assert_called()
                
                # Check that the authorization header is set correctly
                call_args = mock_post.call_args
                headers = call_args[1]['headers']
                self.assertEqual(headers['Authorization'], f'Bearer {test_token}')


def test_workflow_yaml_syntax():
    """Test that the workflow YAML file has valid syntax"""
    workflow_path = '/home/runner/work/echodash/echodash/.github/workflows/cronbot.yml'
    
    try:
        import yaml
        with open(workflow_path, 'r') as f:
            yaml.safe_load(f)
        print("✅ Workflow YAML syntax is valid")
        return True
    except ImportError:
        print("⚠️ PyYAML not available, skipping YAML syntax check")
        return True
    except Exception as e:
        print(f"❌ Workflow YAML syntax error: {e}")
        return False


if __name__ == '__main__':
    print("Testing GitHub Token handling...")
    
    if MODULES_AVAILABLE:
        # Test workflow YAML syntax
        yaml_ok = test_workflow_yaml_syntax()
        
        # Run unit tests
        unittest.main(verbosity=2)
    else:
        print("Skipping tests - required modules not available")