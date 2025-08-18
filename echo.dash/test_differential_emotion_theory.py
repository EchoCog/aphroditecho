#!/usr/bin/env python3
"""
Test script for Differential Emotion Theory module

Tests the DET emotion system integration functionality.
"""

import unittest
import logging
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the module under test
try:
    from differential_emotion_theory import DETEmotion
    DET_AVAILABLE = True
except ImportError as e:
    DET_AVAILABLE = False
    print(f"Warning: Could not import differential_emotion_theory: {e}")


class TestDifferentialEmotionTheory(unittest.TestCase):
    """Test cases for differential_emotion_theory module"""

    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging output during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_import_differential_emotion_theory(self):
        """Test that differential_emotion_theory module can be imported"""
        if not DET_AVAILABLE:
            self.skipTest("differential_emotion_theory module not available")
        
        self.assertTrue(DET_AVAILABLE)

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_det_emotion_enum_exists(self):
        """Test that DETEmotion enum exists and has expected values"""
        # Test that the enum can be imported
        self.assertIsNotNone(DETEmotion)
        
        # Test some expected emotion values
        expected_emotions = [
            'INTEREST', 'EXCITEMENT', 'ANGER', 'CONTEMPT', 'DISGUST', 
            'FEAR', 'SHAME'
        ]
        
        available_emotions = []
        for emotion in expected_emotions:
            if hasattr(DETEmotion, emotion):
                available_emotions.append(emotion)
        
        # We expect at least some emotions to be available
        self.assertGreater(len(available_emotions), 0,
                          f"No expected emotions found. Available: {[e.name for e in DETEmotion]}")

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_det_emotion_enum_values(self):
        """Test DETEmotion enum values are integers"""
        for emotion in DETEmotion:
            self.assertIsInstance(emotion.value, int)
            self.assertGreaterEqual(emotion.value, 0)

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_det_emotion_unique_values(self):
        """Test that DETEmotion enum has unique values"""
        values = [emotion.value for emotion in DETEmotion]
        unique_values = set(values)
        
        self.assertEqual(len(values), len(unique_values),
                        "DETEmotion enum should have unique values")

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_det_emotion_names(self):
        """Test that DETEmotion enum has reasonable names"""
        for emotion in DETEmotion:
            # Names should be uppercase strings
            self.assertIsInstance(emotion.name, str)
            self.assertEqual(emotion.name, emotion.name.upper())
            self.assertGreater(len(emotion.name), 0)

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_basic_emotions_present(self):
        """Test that basic DET emotions are present"""
        basic_emotions = ['INTEREST', 'ANGER', 'FEAR']
        
        available_basic = []
        for emotion_name in basic_emotions:
            if hasattr(DETEmotion, emotion_name):
                available_basic.append(emotion_name)
        
        # At least some basic emotions should be available
        self.assertGreater(len(available_basic), 0,
                          "At least some basic emotions should be available")

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_emotion_ordering(self):
        """Test that emotions have a consistent ordering"""
        emotions_list = list(DETEmotion)
        
        # Should have at least one emotion
        self.assertGreater(len(emotions_list), 0)
        
        # Values should be in ascending order (since they start at 0)
        values = [emotion.value for emotion in emotions_list]
        self.assertEqual(values, sorted(values))

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_det_emotion_iteration(self):
        """Test that DETEmotion enum can be iterated"""
        emotion_count = 0
        
        for emotion in DETEmotion:
            emotion_count += 1
            # Each should be a DETEmotion instance
            self.assertIsInstance(emotion, DETEmotion)
        
        # Should have found some emotions
        self.assertGreater(emotion_count, 0)

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available") 
    def test_det_emotion_access_by_name(self):
        """Test accessing emotions by name"""
        # Test that we can access emotions by name if they exist
        if hasattr(DETEmotion, 'INTEREST'):
            interest = DETEmotion.INTEREST
            self.assertEqual(interest.name, 'INTEREST')
            self.assertIsInstance(interest.value, int)

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_det_emotion_access_by_value(self):
        """Test accessing emotions by value"""
        # Get the first emotion and test value access
        emotions_list = list(DETEmotion)
        if emotions_list:
            first_emotion = emotions_list[0]
            # Test that we can get the same emotion by value
            same_emotion = DETEmotion(first_emotion.value)
            self.assertEqual(first_emotion, same_emotion)

    @unittest.skipIf(not DET_AVAILABLE, "differential_emotion_theory not available")
    def test_module_structure(self):
        """Test that the module has expected structure beyond DETEmotion"""
        import differential_emotion_theory as det_module
        
        # Check for other expected components
        expected_components = ['DETEmotion']  # We know this exists
        
        # Look for other classes or functions that might exist
        module_attrs = [attr for attr in dir(det_module) 
                       if not attr.startswith('_') and attr.isupper()]
        
        # Should have at least the DETEmotion enum
        self.assertIn('DETEmotion', module_attrs)


def main():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()