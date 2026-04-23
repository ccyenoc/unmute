"""
Advanced Facial AI module for emotion and linguistic expression detection.
Combines FER for emotion recognition with MediaPipe for linguistic facial grammar.
"""

import cv2
import numpy as np
import mediapipe as mp
import logging
from typing import Dict, List, Tuple, Optional
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Try to import FER, fallback to basic emotion detection if unavailable
try:
    from fer import FER
    HAS_FER = True
except (ImportError, ModuleNotFoundError):
    HAS_FER = False
    logging.warning("FER module not available, using fallback emotion detection")

import sys
import os

# Get the absolute path of the current file (emotion_detector.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add the 'services' directory to the system path so it can find facial_utils
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    # This imports the specific classes your code needs
    from facial_utils import (
        LandmarkProcessor, 
        FeatureExtractor, 
        DataSmoother
    )
except ImportError:
    # Fallback for different execution environments
    from backend.services.facial_utils import (
        LandmarkProcessor, 
        FeatureExtractor, 
        DataSmoother
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FacialAI:
    """
    Advanced Facial AI system combining emotion detection with linguistic expression recognition.
    
    Features:
    - Multi-emotion classification with confidence scores
    - Linguistic expression detection (sign language grammar markers)
    - Face tracking and smoothing across frames
    - Advanced facial feature extraction
    - Performance optimization with face detection caching
    - Comprehensive error handling and logging
    """
    
    # Emotion classes
    EMOTIONS = ['happy', 'sad', 'angry', 'neutral', 'surprise', 'disgust', 'fear']
    
    # Linguistic expression markers (sign language grammar)
    LINGUISTIC_MARKERS = {
        'question': 'Raised eyebrows, slight head tilt',
        'emphasis': 'Furrowed brows, intense expression',
        'statement': 'Neutral expression, steady gaze',
        'negation': 'Head shake, specific mouth position',
        'conditional': 'Raised eyebrows with specific mouth shape'
    }
    
    def __init__(self, enable_smoothing: bool = True, smoothing_window: int = 5):
        """
        Initialize FacialAI system using the MediaPipe Tasks API.
        """
        try:
            # Initialize MediaPipe Tasks
            model_path = 'face_landmarker.task'
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True,
                num_faces=1,
                running_mode=vision.RunningMode.VIDEO 
            )
            self.detector = vision.FaceLandmarker.create_from_options(options)
            logger.info("MediaPipe Tasks API initialized.")

            # Initialize FER for emotion detection
            if HAS_FER:
                self.emotion_detector = FER(mtcnn=True)
            else:
                self.emotion_detector = None
            
            # Initialize Support Utilities
            self.enable_smoothing = enable_smoothing
            self.smoother = DataSmoother(window_size=smoothing_window)
            self.total_frames = 0
            self.successful_detections = 0
            
            logger.info("FacialAI initialized successfully.")
            
        except Exception as e:
            logger.error(f"Critical Error initializing FacialAI: {str(e)}")
            raise

    
    def _detect_linguistic_expressions(
        self, 
        landmarks,
        emotion: str,
        emotion_confidence: float
    ) -> Dict:
        """
        Detect linguistic facial expressions (sign language grammar markers).
        
        Args:
            landmarks: MediaPipe landmarks
            emotion: Detected emotion
            emotion_confidence: Confidence score for emotion
            
        Returns:
            Dictionary with linguistic expression and confidence
        """
        try:
            # Extract facial features
            left_eyebrow = FeatureExtractor.get_eyebrow_position(landmarks, 'left')
            right_eyebrow = FeatureExtractor.get_eyebrow_position(landmarks, 'right')
            mouth_features = FeatureExtractor.get_mouth_openness(landmarks)
            left_eye = FeatureExtractor.get_eye_openness(landmarks, 'left')
            right_eye = FeatureExtractor.get_eye_openness(landmarks, 'right')
            head_pose = FeatureExtractor.get_head_pose(landmarks)
            
            # Determine linguistic expression based on facial features
            expression = 'statement'
            confidence = 0.5
            
            # QUESTION: Raised eyebrows + slight head tilt
            if (left_eyebrow['raised'] and right_eyebrow['raised'] and 
                abs(head_pose['pitch']) > 5):
                expression = 'question'
                confidence = 0.85
            
            # EMPHASIS: Furrowed brows + intense eyes
            elif (left_eyebrow['angle'] < -15 and right_eyebrow['angle'] > 15 and
                  left_eye['eye_aspect_ratio'] < 0.2):
                expression = 'emphasis'
                confidence = 0.80
            
            # NEGATION: Head shake (high yaw) + mouth closed
            elif (abs(head_pose['yaw']) > 20 and not mouth_features['is_open']):
                expression = 'negation'
                confidence = 0.75
            
            # CONDITIONAL: Raised eyebrows + specific mouth shape
            elif (left_eyebrow['raised'] and mouth_features['openness_ratio'] > 0.25):
                expression = 'conditional'
                confidence = 0.70
            
            # Default: STATEMENT
            else:
                expression = 'statement'
                confidence = 0.6
            
            # Smooth confidence based on emotion confidence
            final_confidence = (confidence + emotion_confidence) / 2
            
            return {
                'linguistic_expression': expression,
                'linguistic_confidence': float(final_confidence),
                'facial_features': {
                    'eyebrows': {
                        'left': left_eyebrow,
                        'right': right_eyebrow
                    },
                    'mouth': mouth_features,
                    'eyes': {
                        'left': left_eye,
                        'right': right_eye
                    },
                    'head_pose': head_pose
                }
            }
            
        except Exception as e:
            logger.warning(f"Error in linguistic expression detection: {str(e)}")
            return {
                'linguistic_expression': 'statement',
                'linguistic_confidence': 0.5,
                'facial_features': {}
            }
    
    def _get_emotion_with_confidence(self, frame) -> Tuple[str, float, Dict]:
        """
        Detect emotions from frame using FER.
        
        Args:
            frame: Input image/frame
            
        Returns:
            Tuple of (emotion, confidence, all_emotions_dict)
        """
        try:
            emotions = self.emotion_detector.detect_emotions(frame)
            
            if not emotions or not emotions[0]['emotions']:
                return 'neutral', 0.5, {e: 0.0 for e in self.EMOTIONS}
            
            emotion_dict = emotions[0]['emotions']
            
            # Get top emotion and confidence
            top_emotion = max(emotion_dict, key=emotion_dict.get)
            confidence = float(emotion_dict[top_emotion])
            
            # Normalize confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))
            
            return top_emotion, confidence, emotion_dict
            
        except Exception as e:
            logger.warning(f"Error in emotion detection: {str(e)}")
            return 'neutral', 0.5, {e: 0.0 for e in self.EMOTIONS}
    
    def analyze_frame(self, frame: np.ndarray, apply_smoothing: bool = True) -> Dict:
        self.total_frames += 1
        timestamp_ms = int(time.time() * 1000)
        
        # Convert to RGB and MediaPipe Image format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # 1. Detect emotion (FER)
        emotion, emotion_conf, all_emotions = self._get_emotion_with_confidence(frame)
        
        # 2. Process landmarks using Tasks API
        detection_result = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if not detection_result.face_landmarks:
            return {'success': False, 'emotion': emotion}

        # Process first detected face
        landmarks = detection_result.face_landmarks[0]
        self.successful_detections += 1
        
        # 3. Detect linguistic markers (Raised eyebrows, etc.)
        linguistic_result = self._detect_linguistic_expressions(landmarks, emotion, emotion_conf)
        
        return {
            'success': True,
            'emotion': emotion,
            'linguistic_expression': linguistic_result['linguistic_expression'],
            'timestamp': timestamp_ms
        }
         
    def analyze_video_stream(
        self,
        source: int = 0,
        callback=None
    ) -> None:
        """
        Analyze a live video stream.
        
        Args:
            source: Video source (0 for webcam, or path to video file)
            callback: Optional callback function for each frame result
        """
        try:
            cap = cv2.VideoCapture(source)
            
            if not cap.isOpened():
                logger.error(f"Cannot open video source: {source}")
                return
            
            logger.info(f"Started video stream analysis from source: {source}")
            
            while cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    logger.info("End of video stream")
                    break
                
                # Resize for faster processing (optional)
                frame = cv2.resize(frame, (640, 480))
                
                # Analyze frame
                result = self.analyze_frame(frame)
                
                # Callback
                if callback:
                    callback(result, frame)
                
                # Display (optional)
                display_text = (
                    f"Emotion: {result['emotion']} ({result['emotion_confidence']:.2f}) | "
                    f"Expression: {result['linguistic_expression']}"
                )
                cv2.putText(
                    frame, 
                    display_text, 
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 0), 
                    2
                )
                
                cv2.imshow('Facial AI Analysis', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            logger.info(
                f"Stream analysis complete. "
                f"Total frames: {self.total_frames}, "
                f"Successful detections: {self.successful_detections}"
            )
            
        except Exception as e:
            logger.error(f"Error in video stream analysis: {str(e)}", exc_info=True)
    
    def get_statistics(self) -> Dict:
        """Get analysis statistics."""
        detection_rate = (
            self.successful_detections / self.total_frames 
            if self.total_frames > 0 else 0
        )
        
        return {
            'total_frames': self.total_frames,
            'successful_detections': self.successful_detections,
            'detection_rate': float(detection_rate),
            'smoothing_enabled': self.enable_smoothing
        }
    
    def reset(self) -> None:
        """Reset all state and counters."""
        self.smoother.reset()
        self.total_frames = 0
        self.successful_detections = 0
        logger.info("FacialAI reset complete")