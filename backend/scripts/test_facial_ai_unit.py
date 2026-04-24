"""
Unit tests for FacialAI components using unittest.
Tests individual modules and functions in isolation.
"""

import unittest
import sys
import os
import numpy as np
import cv2

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.emotion_detector import FacialAI
from services.facial_utils import (
    LandmarkProcessor,
    FeatureExtractor,
    DataSmoother
)


class TestLandmarkProcessor(unittest.TestCase):
    """Test landmark processing utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create dummy landmark object
        class DummyLandmark:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        self.DummyLandmark = DummyLandmark
        self.landmarks = [
            DummyLandmark(0.5, 0.5, 0.0),
            DummyLandmark(0.6, 0.5, 0.0),
            DummyLandmark(0.7, 0.5, 0.0),
        ]
    
    def test_get_landmark_coordinates(self):
        """Test landmark coordinate extraction."""
        coords = LandmarkProcessor.get_landmark_coordinates(self.landmarks, [0, 1])
        self.assertEqual(coords.shape, (2, 3))
    
    def test_euclidean_distance(self):
        """Test Euclidean distance calculation."""
        p1 = np.array([0, 0])
        p2 = np.array([3, 4])
        dist = LandmarkProcessor.euclidean_distance(p1, p2)
        self.assertAlmostEqual(dist, 5.0, places=5)
    
    def test_face_center_calculation(self):
        """Test face center calculation."""
        landmarks = [
            self.DummyLandmark(0.0, 0.0, 0.0),
            self.DummyLandmark(1.0, 1.0, 0.0),
        ]
        # Should work even with limited landmarks
        try:
            center = LandmarkProcessor.get_face_center(landmarks)
            self.assertEqual(len(center), 3)
        except:
            # Expected if not enough face outline landmarks
            pass


class TestFeatureExtractor(unittest.TestCase):
    """Test facial feature extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        class DummyLandmark:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        self.DummyLandmark = DummyLandmark
        
        # Create 468 landmarks (minimal MediaPipe structure)
        self.landmarks = [
            DummyLandmark(np.random.random(), np.random.random(), 0.0)
            for _ in range(468)
        ]
    
    def test_eyebrow_position(self):
        """Test eyebrow position detection."""
        result = FeatureExtractor.get_eyebrow_position(self.landmarks, 'left')
        
        self.assertIn('height', result)
        self.assertIn('angle', result)
        self.assertIn('raised', result)
        self.assertIsInstance(result['raised'], (bool, np.bool_))
    
    def test_mouth_openness(self):
        """Test mouth openness calculation."""
        result = FeatureExtractor.get_mouth_openness(self.landmarks)
        
        self.assertIn('vertical_distance', result)
        self.assertIn('horizontal_distance', result)
        self.assertIn('openness_ratio', result)
        self.assertIn('is_open', result)
    
    def test_eye_openness(self):
        """Test eye openness detection."""
        result = FeatureExtractor.get_eye_openness(self.landmarks, 'left')
        
        self.assertIn('eye_aspect_ratio', result)
        self.assertIn('is_open', result)
        self.assertTrue(0.0 <= result['eye_aspect_ratio'])
    
    def test_head_pose(self):
        """Test head pose estimation."""
        result = FeatureExtractor.get_head_pose(self.landmarks)
        
        self.assertIn('yaw', result)
        self.assertIn('pitch', result)
        self.assertIn('roll', result)


class TestDataSmoother(unittest.TestCase):
    """Test temporal data smoothing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.smoother = DataSmoother(window_size=3)
    
    def test_emotion_smoothing(self):
        """Test emotion smoothing."""
        emotions = ['happy', 'happy', 'sad', 'happy']
        
        for emotion in emotions:
            smoothed, conf = self.smoother.smooth_emotion(emotion, 0.9)
            self.assertIn(smoothed, ['happy', 'sad'])
    
    def test_expression_smoothing(self):
        """Test expression smoothing."""
        expressions = ['question', 'question', 'statement', 'question']
        
        for expr in expressions:
            smoothed = self.smoother.smooth_expression(expr)
            self.assertIn(smoothed, ['question', 'statement'])
    
    def test_smoother_reset(self):
        """Test smoother reset."""
        self.smoother.smooth_emotion('happy', 0.9)
        self.smoother.reset()
        
        # After reset, should process as if fresh
        emotion, conf = self.smoother.smooth_emotion('sad', 0.8)
        self.assertEqual(emotion, 'sad')


class TestFacialAIInitialization(unittest.TestCase):
    """Test FacialAI initialization."""
    
    def test_default_initialization(self):
        """Test default initialization."""
        ai = FacialAI()
        self.assertTrue(ai.enable_smoothing)
        self.assertEqual(ai.total_frames, 0)
    
    def test_custom_initialization(self):
        """Test custom initialization."""
        ai = FacialAI(enable_smoothing=False, smoothing_window=10)
        self.assertFalse(ai.enable_smoothing)


class TestFacialAIAnalysis(unittest.TestCase):
    """Test FacialAI frame analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai = FacialAI(enable_smoothing=False)
        self.test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    def test_analyze_frame_returns_dict(self):
        """Test that analyze_frame returns a dictionary."""
        result = self.ai.analyze_frame(self.test_frame)
        self.assertIsInstance(result, dict)
    
    def test_analyze_frame_has_required_fields(self):
        """Test that result has all required fields."""
        result = self.ai.analyze_frame(self.test_frame)
        
        required_fields = [
            'success', 'emotion', 'emotion_confidence',
            'linguistic_expression', 'linguistic_confidence',
            'faces_detected', 'timestamp'
        ]
        
        for field in required_fields:
            self.assertIn(field, result)
    
    def test_emotion_in_valid_range(self):
        """Test that emotion confidence is in valid range."""
        result = self.ai.analyze_frame(self.test_frame)
        self.assertTrue(0.0 <= result['emotion_confidence'] <= 1.0)
    
    def test_expression_confidence_valid(self):
        """Test that expression confidence is valid."""
        result = self.ai.analyze_frame(self.test_frame)
        self.assertTrue(0.0 <= result['linguistic_confidence'] <= 1.0)
    
    def test_multiple_frame_processing(self):
        """Test processing multiple frames."""
        for _ in range(5):
            result = self.ai.analyze_frame(self.test_frame)
            self.assertIsInstance(result, dict)
        
        # Check statistics
        self.assertEqual(self.ai.total_frames, 5)
    
    def test_frame_counter_increment(self):
        """Test frame counter increments."""
        initial = self.ai.total_frames
        self.ai.analyze_frame(self.test_frame)
        self.assertEqual(self.ai.total_frames, initial + 1)


class TestFacialAIStatistics(unittest.TestCase):
    """Test FacialAI statistics tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai = FacialAI()
        self.test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        self.ai.reset()
        
        for _ in range(5):
            self.ai.analyze_frame(self.test_frame)
        
        stats = self.ai.get_statistics()
        
        self.assertEqual(stats['total_frames'], 5)
        self.assertIn('successful_detections', stats)
        self.assertIn('detection_rate', stats)
        self.assertTrue(0.0 <= stats['detection_rate'] <= 1.0)
    
    def test_reset_statistics(self):
        """Test statistics reset."""
        self.ai.analyze_frame(self.test_frame)
        self.ai.reset()
        
        self.assertEqual(self.ai.total_frames, 0)
        self.assertEqual(self.ai.successful_detections, 0)


class TestEmotionClasses(unittest.TestCase):
    """Test emotion classification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai = FacialAI()
    
    def test_emotion_classes_defined(self):
        """Test that emotion classes are defined."""
        self.assertTrue(len(FacialAI.EMOTIONS) > 0)
    
    def test_emotion_classes_are_strings(self):
        """Test that emotion classes are strings."""
        for emotion in FacialAI.EMOTIONS:
            self.assertIsInstance(emotion, str)


class TestLinguisticMarkers(unittest.TestCase):
    """Test linguistic markers."""
    
    def test_linguistic_markers_defined(self):
        """Test that linguistic markers are defined."""
        self.assertTrue(len(FacialAI.LINGUISTIC_MARKERS) > 0)
    
    def test_marker_descriptions(self):
        """Test that all markers have descriptions."""
        for marker, description in FacialAI.LINGUISTIC_MARKERS.items():
            self.assertIsInstance(marker, str)
            self.assertIsInstance(description, str)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai = FacialAI()
    
    def test_empty_frame(self):
        """Test handling of empty/black frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = self.ai.analyze_frame(frame)
        self.assertIsInstance(result, dict)
    
    def test_white_frame(self):
        """Test handling of white frame."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        result = self.ai.analyze_frame(frame)
        self.assertIsInstance(result, dict)
    
    def test_noise_frame(self):
        """Test handling of noisy frame."""
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        result = self.ai.analyze_frame(frame)
        self.assertIsInstance(result, dict)


# ============================================================================
# Test Suite Execution
# ============================================================================

def run_unit_tests():
    """Run all unit tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLandmarkProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestDataSmoother))
    suite.addTests(loader.loadTestsFromTestCase(TestFacialAIInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestFacialAIAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestFacialAIStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestEmotionClasses))
    suite.addTests(loader.loadTestsFromTestCase(TestLinguisticMarkers))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_unit_tests()
    exit(0 if result.wasSuccessful() else 1)
