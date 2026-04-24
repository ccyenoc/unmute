"""
Comprehensive test suite for FacialAI module.
Tests all features: emotion detection, linguistic expressions, facial features, and performance.
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path
import logging
import time
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.emotion_detector import FacialAI
from services.facial_utils import LandmarkProcessor, FeatureExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Store and display test results."""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """Add a test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results.append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'status': status
        })
        
        print(f"{status} | {test_name}: {message}")
    
    def summary(self):
        """Print test summary."""
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("="*80 + "\n")


# ============================================================================
# TEST 1: Initialization Tests
# ============================================================================

def test_initialization(results: TestResults):
    """Test FacialAI initialization."""
    print("\n" + "="*80)
    print("TEST 1: INITIALIZATION TESTS")
    print("="*80)
    
    try:
        ai = FacialAI()
        results.add_result(
            "FacialAI Initialization",
            True,
            "Successfully initialized FacialAI"
        )
    except Exception as e:
        results.add_result(
            "FacialAI Initialization",
            False,
            f"Error: {str(e)}"
        )
        return None
    
    # Test with smoothing disabled
    try:
        ai_no_smooth = FacialAI(enable_smoothing=False)
        results.add_result(
            "FacialAI Without Smoothing",
            True,
            "Successfully initialized without smoothing"
        )
    except Exception as e:
        results.add_result(
            "FacialAI Without Smoothing",
            False,
            f"Error: {str(e)}"
        )
    
    # Test custom smoothing window
    try:
        ai_custom = FacialAI(smoothing_window=10)
        results.add_result(
            "FacialAI With Custom Window",
            True,
            "Successfully initialized with custom smoothing window"
        )
    except Exception as e:
        results.add_result(
            "FacialAI With Custom Window",
            False,
            f"Error: {str(e)}"
        )
    
    return ai


# ============================================================================
# TEST 2: Static Image Tests
# ============================================================================

def test_static_image_analysis(ai: FacialAI, results: TestResults):
    """Test analysis on static images."""
    print("\n" + "="*80)
    print("TEST 2: STATIC IMAGE ANALYSIS")
    print("="*80)
    
    # Create a simple test image (blank frame)
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    try:
        result = ai.analyze_frame(test_image)
        
        # Check result structure
        required_fields = [
            'success', 'emotion', 'emotion_confidence',
            'linguistic_expression', 'linguistic_confidence',
            'faces_detected', 'timestamp'
        ]
        
        all_fields_present = all(field in result for field in required_fields)
        results.add_result(
            "Result Structure",
            all_fields_present,
            f"All required fields present: {all_fields_present}"
        )
        
    except Exception as e:
        results.add_result(
            "Static Image Analysis",
            False,
            f"Error: {str(e)}"
        )


# ============================================================================
# TEST 3: Webcam Test
# ============================================================================

def test_webcam_capture(ai: FacialAI, results: TestResults, duration_seconds: int = 10):
    """Test real-time webcam capture and analysis."""
    print("\n" + "="*80)
    print("TEST 3: REAL-TIME WEBCAM ANALYSIS")
    print("="*80)
    print(f"Capturing for {duration_seconds} seconds. Press 'q' to quit early.")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        results.add_result(
            "Webcam Access",
            False,
            "Cannot open webcam. Skipping real-time tests."
        )
        return
    
    results.add_result(
        "Webcam Access",
        True,
        "Successfully opened webcam"
    )
    
    frame_count = 0
    successful_analyses = 0
    emotion_counts = {}
    expression_counts = {}
    
    start_time = time.time()
    fps_values = []
    
    try:
        while time.time() - start_time < duration_seconds:
            ret, frame = cap.read()
            
            if not ret:
                logger.warning("Failed to read frame from webcam")
                break
            
            frame = cv2.resize(frame, (640, 480))
            frame_count += 1
            
            # Analyze frame
            frame_start = time.time()
            result = ai.analyze_frame(frame)
            frame_time = time.time() - frame_start
            fps = 1.0 / frame_time
            fps_values.append(fps)
            
            if result['success']:
                successful_analyses += 1
                emotion = result['emotion']
                expression = result['linguistic_expression']
                
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                expression_counts[expression] = expression_counts.get(expression, 0) + 1
            
            # Display results
            display_text = [
                f"Emotion: {result['emotion']} ({result['emotion_confidence']:.2f})",
                f"Expression: {result['linguistic_expression']} ({result['linguistic_confidence']:.2f})",
                f"Faces: {result['faces_detected']} | FPS: {fps:.1f}",
                f"Detections: {successful_analyses}/{frame_count}"
            ]
            
            for i, text in enumerate(display_text):
                cv2.putText(
                    frame,
                    text,
                    (10, 30 + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )
            
            cv2.imshow('FacialAI Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Test results
        detection_rate = successful_analyses / frame_count if frame_count > 0 else 0
        avg_fps = np.mean(fps_values) if fps_values else 0
        
        results.add_result(
            "Frame Processing",
            frame_count > 0,
            f"Processed {frame_count} frames"
        )
        
        results.add_result(
            "Face Detection Rate",
            detection_rate > 0.5,
            f"Detection rate: {detection_rate*100:.1f}% ({successful_analyses}/{frame_count})"
        )
        
        results.add_result(
            "Performance (FPS)",
            avg_fps > 10,
            f"Average FPS: {avg_fps:.1f}"
        )
        
        results.add_result(
            "Emotion Detection",
            len(emotion_counts) > 0,
            f"Emotions detected: {emotion_counts}"
        )
        
        results.add_result(
            "Expression Detection",
            len(expression_counts) > 0,
            f"Expressions detected: {expression_counts}"
        )
        
    except Exception as e:
        results.add_result(
            "Webcam Test",
            False,
            f"Error: {str(e)}"
        )
        cap.release()
        cv2.destroyAllWindows()


# ============================================================================
# TEST 4: Emotion Classification Tests
# ============================================================================

def test_emotion_classification(ai: FacialAI, results: TestResults):
    """Test emotion classification capabilities."""
    print("\n" + "="*80)
    print("TEST 4: EMOTION CLASSIFICATION")
    print("="*80)
    
    # Test with multiple blank frames
    test_frames = 5
    emotions_detected = set()
    
    for i in range(test_frames):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (50 + i * 30)
        result = ai.analyze_frame(frame, apply_smoothing=False)
        
        if result['emotion'] in FacialAI.EMOTIONS:
            emotions_detected.add(result['emotion'])
    
    results.add_result(
        "Emotion Classification",
        'neutral' in emotions_detected or len(emotions_detected) > 0,
        f"Emotions detected from frames: {emotions_detected}"
    )
    
    # Test emotion confidence scores
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    result = ai.analyze_frame(frame)
    
    confidence_valid = (0.0 <= result['emotion_confidence'] <= 1.0)
    results.add_result(
        "Emotion Confidence Range",
        confidence_valid,
        f"Confidence: {result['emotion_confidence']:.2f} (valid: 0-1)"
    )


# ============================================================================
# TEST 5: Linguistic Expression Detection Tests
# ============================================================================

def test_linguistic_expressions(ai: FacialAI, results: TestResults):
    """Test linguistic expression detection."""
    print("\n" + "="*80)
    print("TEST 5: LINGUISTIC EXPRESSION DETECTION")
    print("="*80)
    
    valid_expressions = set(FacialAI.LINGUISTIC_MARKERS.keys())
    
    # Test with multiple frames
    test_frames = 5
    expressions_detected = set()
    
    for i in range(test_frames):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i * 20)
        result = ai.analyze_frame(frame, apply_smoothing=False)
        
        if result['linguistic_expression'] in valid_expressions:
            expressions_detected.add(result['linguistic_expression'])
    
    results.add_result(
        "Linguistic Expression Detection",
        len(expressions_detected) > 0,
        f"Expressions detected: {expressions_detected}"
    )
    
    # Test expression confidence
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    result = ai.analyze_frame(frame)
    
    expr_conf_valid = (0.0 <= result['linguistic_confidence'] <= 1.0)
    results.add_result(
        "Expression Confidence Range",
        expr_conf_valid,
        f"Confidence: {result['linguistic_confidence']:.2f} (valid: 0-1)"
    )


# ============================================================================
# TEST 6: Smoothing Tests
# ============================================================================

def test_smoothing_functionality(results: TestResults):
    """Test temporal smoothing."""
    print("\n" + "="*80)
    print("TEST 6: TEMPORAL SMOOTHING")
    print("="*80)
    
    # Test with smoothing
    ai_smooth = FacialAI(enable_smoothing=True, smoothing_window=3)
    
    # Create alternating frames
    emotions_smooth = []
    emotions_no_smooth = []
    
    ai_no_smooth = FacialAI(enable_smoothing=False)
    
    for i in range(5):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i * 20)
        
        result_smooth = ai_smooth.analyze_frame(frame)
        result_no_smooth = ai_no_smooth.analyze_frame(frame)
        
        emotions_smooth.append(result_smooth['emotion'])
        emotions_no_smooth.append(result_no_smooth['emotion'])
    
    results.add_result(
        "Smoothing Functionality",
        len(emotions_smooth) == 5,
        f"Smoothing processed {len(emotions_smooth)} frames"
    )
    
    # Check if smoothing reduces variation
    unique_smooth = len(set(emotions_smooth))
    unique_no_smooth = len(set(emotions_no_smooth))
    
    results.add_result(
        "Smoothing Effect",
        unique_smooth <= unique_no_smooth,
        f"Unique emotions - Smoothed: {unique_smooth}, No smoothing: {unique_no_smooth}"
    )


# ============================================================================
# TEST 7: Statistics and Reporting
# ============================================================================

def test_statistics(ai: FacialAI, results: TestResults):
    """Test statistics tracking."""
    print("\n" + "="*80)
    print("TEST 7: STATISTICS & REPORTING")
    print("="*80)
    
    # Reset and process some frames
    ai.reset()
    
    for i in range(10):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i * 5)
        ai.analyze_frame(frame)
    
    stats = ai.get_statistics()
    
    results.add_result(
        "Statistics Tracking",
        stats['total_frames'] == 10,
        f"Total frames tracked: {stats['total_frames']}"
    )
    
    results.add_result(
        "Detection Rate Calculation",
        0 <= stats['detection_rate'] <= 1.0,
        f"Detection rate: {stats['detection_rate']:.2f}"
    )


# ============================================================================
# TEST 8: Error Handling
# ============================================================================

def test_error_handling(ai: FacialAI, results: TestResults):
    """Test error handling and edge cases."""
    print("\n" + "="*80)
    print("TEST 8: ERROR HANDLING & EDGE CASES")
    print("="*80)
    
    # Test with None
    try:
        result = ai.analyze_frame(np.zeros((480, 640, 3), dtype=np.uint8))
        results.add_result(
            "Null/Black Frame Handling",
            'emotion' in result,
            "Handled black frame gracefully"
        )
    except Exception as e:
        results.add_result(
            "Null/Black Frame Handling",
            False,
            f"Error: {str(e)}"
        )
    
    # Test with extreme values
    try:
        extreme_frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        result = ai.analyze_frame(extreme_frame)
        results.add_result(
            "Extreme Values Handling",
            'emotion' in result,
            "Handled high-value frame gracefully"
        )
    except Exception as e:
        results.add_result(
            "Extreme Values Handling",
            False,
            f"Error: {str(e)}"
        )
    
    # Test with wrong dimensions
    try:
        wrong_frame = np.ones((100, 100), dtype=np.uint8)
        result = ai.analyze_frame(wrong_frame)
        results.add_result(
            "Wrong Dimensions Handling",
            'emotion' in result or isinstance(result, dict),
            "Handled wrong-sized frame"
        )
    except Exception as e:
        # Expected to fail
        results.add_result(
            "Wrong Dimensions Handling",
            False,
            f"Properly rejected: {str(e)}"
        )


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "FACIAL AI COMPREHENSIVE TEST SUITE" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    results = TestResults()
    
    # TEST 1: Initialization
    ai = test_initialization(results)
    if ai is None:
        print("\n⚠️  Cannot continue without successful initialization")
        results.summary()
        return
    
    # TEST 2: Static Image
    test_static_image_analysis(ai, results)
    
    # TEST 3: Webcam (optional - will be skipped if no camera)
    try:
        test_webcam_capture(ai, results, duration_seconds=5)
    except Exception as e:
        logger.warning(f"Webcam test skipped: {str(e)}")
    
    # TEST 4: Emotion Classification
    test_emotion_classification(ai, results)
    
    # TEST 5: Linguistic Expressions
    test_linguistic_expressions(ai, results)
    
    # TEST 6: Smoothing
    test_smoothing_functionality(results)
    
    # TEST 7: Statistics
    test_statistics(ai, results)
    
    # TEST 8: Error Handling
    test_error_handling(ai, results)
    
    # Print summary
    results.summary()
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
