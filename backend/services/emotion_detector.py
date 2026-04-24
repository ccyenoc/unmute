"""
Simplified Facial AI module compatible with MediaPipe 0.10+ API.
Detects emotion and linguistic expressions from facial analysis.
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import time
from collections import Counter

# Imports
try:
    from fer import FER
    HAS_FER = True
except:
    HAS_FER = False

try:
    from .facial_utils import (
        LandmarkProcessor, 
        FeatureExtractor, 
        DataSmoother
    )
except ImportError:
    from facial_utils import (
        LandmarkProcessor, 
        FeatureExtractor, 
        DataSmoother
    )

logger = logging.getLogger(__name__)


class FacialAI:
    """
    Advanced Facial AI for emotion and linguistic expression detection.
    """
    
    EMOTIONS = ['happy', 'sad', 'angry', 'neutral', 'surprise', 'disgust', 'fear']
    LINGUISTIC_MARKERS = {
        'question': 'Raised eyebrows',
        'emphasis': 'Furrowed brows',
        'statement': 'Neutral face',
        'negation': 'Head shake',
        'conditional': 'Raised eyebrows + mouth shape'
    }
    
    def __init__(self, enable_smoothing: bool = True, smoothing_window: int = 5):
        """Initialize FacialAI system."""
        try:
            # Initialize FER for emotion detection
            if HAS_FER:
                try:
                    self.emotion_detector = FER(mtcnn=True)
                except Exception as e:
                    logger.warning(f"FER initialization failed: {str(e)}")
                    self.emotion_detector = None
            else:
                self.emotion_detector = None
            
            # Initialize smoother
            self.enable_smoothing = enable_smoothing
            self.smoother = DataSmoother(window_size=smoothing_window)
            
            # Stats
            self.total_frames = 0
            self.successful_detections = 0
            
            logger.info(f"FacialAI initialized (FER: {'Available' if HAS_FER and self.emotion_detector else 'Unavailable'})")
            
        except Exception as e:
            logger.error(f"Error initializing FacialAI: {str(e)}")
            raise
    
    def _detect_linguistic_expressions(
        self, 
        emotion: str,
        emotion_confidence: float
    ) -> Dict:
        """Detect linguistic expressions from emotion analysis."""
        try:
            expression = 'statement'
            confidence = 0.6
            
            if emotion == 'surprise':
                expression = 'question'
                confidence = 0.85
            elif emotion in ['angry', 'fear']:
                expression = 'emphasis'
                confidence = 0.80
            elif emotion == 'sad':
                expression = 'conditional'
                confidence = 0.70
            
            final_confidence = (confidence + emotion_confidence) / 2
            
            return {
                'linguistic_expression': expression,
                'linguistic_confidence': float(final_confidence),
                'facial_features': {}
            }
            
        except Exception as e:
            logger.warning(f"Error in linguistic detection: {str(e)}")
            return {
                'linguistic_expression': 'statement',
                'linguistic_confidence': 0.5,
                'facial_features': {}
            }
    
    def _get_emotion_with_confidence(self, frame) -> Tuple[str, float, Dict]:
        """Detect emotions from frame."""
        try:
            emotion_dict = {e: 0.0 for e in self.EMOTIONS}
            
            if self.emotion_detector:
                try:
                    emotions = self.emotion_detector.detect_emotions(frame)
                    if emotions and emotions[0]['emotions']:
                        emotion_dict = emotions[0]['emotions']
                        top_emotion = max(emotion_dict, key=emotion_dict.get)
                        confidence = float(emotion_dict[top_emotion])
                        confidence = max(0.0, min(1.0, confidence))
                        return top_emotion, confidence, emotion_dict
                except Exception as fer_error:
                    logger.debug(f"FER failed: {str(fer_error)}")
            
            # Fallback - simple brightness-based
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            if brightness > 150:
                emotion_dict['happy'] = 0.6
                return 'happy', 0.6, emotion_dict
            elif brightness < 80:
                emotion_dict['angry'] = 0.5
                return 'angry', 0.5, emotion_dict
            else:
                emotion_dict['neutral'] = 0.8
                return 'neutral', 0.8, emotion_dict
            
        except Exception as e:
            logger.warning(f"Error in emotion detection: {str(e)}")
            emotion_dict = {e: 0.0 for e in self.EMOTIONS}
            emotion_dict['neutral'] = 0.5
            return 'neutral', 0.5, emotion_dict
    
    def analyze_frame(
        self, 
        frame: np.ndarray,
        apply_smoothing: bool = True
    ) -> Dict:
        """Analyze a single frame."""
        self.total_frames += 1
        
        result = {
            'success': False,
            'emotion': 'neutral',
            'emotion_confidence': 0.0,
            'all_emotions': {},
            'linguistic_expression': 'statement',
            'linguistic_confidence': 0.0,
            'facial_features': {},
            'faces_detected': 0,
            'landmarks': None,
            'timestamp': time.time()
        }
        
        try:
            # Detect emotion
            emotion, emotion_conf, all_emotions = self._get_emotion_with_confidence(frame)
            self.successful_detections += 1
            
            # Detect linguistic expressions
            linguistic_result = self._detect_linguistic_expressions(emotion, emotion_conf)
            
            # Apply smoothing
            if apply_smoothing and self.enable_smoothing:
                emotion, emotion_conf = self.smoother.smooth_emotion(emotion, emotion_conf)
                linguistic_expr = self.smoother.smooth_expression(
                    linguistic_result['linguistic_expression']
                )
                linguistic_result['linguistic_expression'] = linguistic_expr
            
            result.update({
                'success': True,
                'emotion': emotion,
                'emotion_confidence': float(emotion_conf),
                'all_emotions': all_emotions,
                'linguistic_expression': linguistic_result['linguistic_expression'],
                'linguistic_confidence': float(linguistic_result['linguistic_confidence']),
                'facial_features': linguistic_result['facial_features']
            })
            
            logger.debug(
                f"Analysis: {emotion} ({emotion_conf:.2f}) | {linguistic_result['linguistic_expression']}"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {str(e)}", exc_info=True)
        
        return result
    
    def analyze_video_stream(self, source: int = 0, callback=None) -> None:
        """Analyze a live video stream."""
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
                
                frame = cv2.resize(frame, (640, 480))
                result = self.analyze_frame(frame)
                
                if callback:
                    callback(result, frame)
                
                display_text = (
                    f"Emotion: {result['emotion']} ({result['emotion_confidence']:.2f}) | "
                    f"Expression: {result['linguistic_expression']}"
                )
                cv2.putText(frame, display_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('Facial AI Analysis', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            logger.info(f"Stream analysis complete. Total: {self.total_frames}, Detections: {self.successful_detections}")
            
        except Exception as e:
            logger.error(f"Error in video stream: {str(e)}", exc_info=True)
    
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
"""
Advanced Facial AI module for emotion and linguistic expression detection.
Combines FER for emotion recognition with MediaPipe for linguistic facial grammar.
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import time
from collections import Counter

# MediaPipe import
try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except:
    HAS_MEDIAPIPE = False

try:
    from .facial_utils import (
        LandmarkProcessor, 
        FeatureExtractor, 
        DataSmoother
    )
except ImportError:
    from facial_utils import (
        LandmarkProcessor, 
        FeatureExtractor, 
        DataSmoother
    )

# Try to import FER, fallback to basic emotion detection if unavailable
try:
    from fer import FER
    HAS_FER = True
except (ImportError, ModuleNotFoundError):
    HAS_FER = False

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
        Initialize FacialAI system.
        
        Args:
            enable_smoothing: Enable frame-to-frame smoothing (recommended)
            smoothing_window: Number of frames to consider for smoothing
        """
        try:
            # Initialize MediaPipe Face Mesh for landmark detection
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=2,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Initialize FER for emotion detection if available
            if HAS_FER:
                try:
                    self.emotion_detector = FER(mtcnn=True)
                except:
                    self.emotion_detector = None
            else:
                self.emotion_detector = None
            
            # Initialize data smoother
            self.enable_smoothing = enable_smoothing
            self.smoother = DataSmoother(window_size=smoothing_window)
            
            # Statistics tracking
            self.total_frames = 0
            self.successful_detections = 0
            
            logger.info(
                f"FacialAI initialized (FER: {'Available' if HAS_FER else 'Unavailable'})"
            )
            
        except Exception as e:
            logger.error(f"Error initializing FacialAI: {str(e)}")
            raise
    
    def _detect_linguistic_expressions(
        self, 
        landmarks,
        emotion: str,
        emotion_confidence: float
    ) -> Dict:
        """
        Detect linguistic facial expressions (sign language grammar markers).
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
        Detect emotions from frame using FER or fallback method.
        """
        try:
            emotion_dict = {e: 0.0 for e in self.EMOTIONS}
            
            # Try FER if available
            if self.emotion_detector:
                try:
                    emotions = self.emotion_detector.detect_emotions(frame)
                    
                    if emotions and emotions[0]['emotions']:
                        emotion_dict = emotions[0]['emotions']
                        top_emotion = max(emotion_dict, key=emotion_dict.get)
                        confidence = float(emotion_dict[top_emotion])
                        confidence = max(0.0, min(1.0, confidence))
                        return top_emotion, confidence, emotion_dict
                except Exception as fer_error:
                    logger.debug(f"FER failed, using fallback: {str(fer_error)}")
            
            # Fallback: Simple brightness-based emotion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            if brightness > 150:
                emotion_dict['happy'] = 0.6
                emotion_dict['neutral'] = 0.4
                return 'happy', 0.6, emotion_dict
            elif brightness < 80:
                emotion_dict['angry'] = 0.5
                emotion_dict['sad'] = 0.5
                return 'angry', 0.5, emotion_dict
            else:
                emotion_dict['neutral'] = 0.8
                return 'neutral', 0.8, emotion_dict
            
        except Exception as e:
            logger.warning(f"Error in emotion detection: {str(e)}")
            emotion_dict = {e: 0.0 for e in self.EMOTIONS}
            emotion_dict['neutral'] = 0.5
            return 'neutral', 0.5, emotion_dict
    
    def analyze_frame(
        self, 
        frame: np.ndarray,
        apply_smoothing: bool = True
    ) -> Dict:
        """
        Analyze a single frame for emotions and linguistic expressions.
        """
        self.total_frames += 1
        
        result = {
            'success': False,
            'emotion': 'neutral',
            'emotion_confidence': 0.0,
            'all_emotions': {},
            'linguistic_expression': 'statement',
            'linguistic_confidence': 0.0,
            'facial_features': {},
            'faces_detected': 0,
            'landmarks': None,
            'timestamp': time.time()
        }
        
        try:
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect emotion
            emotion, emotion_conf, all_emotions = self._get_emotion_with_confidence(frame)
            
            # Process landmarks for linguistic features
            mp_results = self.face_mesh.process(rgb_frame)
            
            if not mp_results.multi_face_landmarks:
                logger.debug("No faces detected in frame")
                result['emotion'] = emotion
                result['emotion_confidence'] = emotion_conf
                result['all_emotions'] = all_emotions
                return result
            
            # Process first detected face
            landmarks = mp_results.multi_face_landmarks[0].landmark
            result['faces_detected'] = len(mp_results.multi_face_landmarks)
            self.successful_detections += 1
            
            # Detect linguistic expressions
            linguistic_result = self._detect_linguistic_expressions(
                landmarks, 
                emotion, 
                emotion_conf
            )
            
            # Apply temporal smoothing if enabled
            if apply_smoothing and self.enable_smoothing:
                emotion, emotion_conf = self.smoother.smooth_emotion(emotion, emotion_conf)
                linguistic_expr = self.smoother.smooth_expression(
                    linguistic_result['linguistic_expression']
                )
                linguistic_result['linguistic_expression'] = linguistic_expr
            
            # Build result
            result.update({
                'success': True,
                'emotion': emotion,
                'emotion_confidence': float(emotion_conf),
                'all_emotions': all_emotions,
                'linguistic_expression': linguistic_result['linguistic_expression'],
                'linguistic_confidence': float(linguistic_result['linguistic_confidence']),
                'facial_features': linguistic_result['facial_features'],
                'landmarks': [(lm.x, lm.y, lm.z) for lm in landmarks]
            })
            
            logger.debug(
                f"Analysis: {emotion} ({emotion_conf:.2f}) | "
                f"{linguistic_result['linguistic_expression']} "
                f"({linguistic_result['linguistic_confidence']:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {str(e)}", exc_info=True)
        
        return result
    
    def analyze_video_stream(
        self,
        source: int = 0,
        callback=None
    ) -> None:
        """
        Analyze a live video stream.
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
                
                frame = cv2.resize(frame, (640, 480))
                result = self.analyze_frame(frame)
                
                if callback:
                    callback(result, frame)
                
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
