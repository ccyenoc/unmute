"""
Utility functions for facial analysis and landmark processing.
Provides helper functions for geometric calculations, feature extraction, and data smoothing.
"""

import numpy as np
from typing import List, Dict, Tuple
from collections import deque


class LandmarkProcessor:
    """Process MediaPipe facial landmarks for feature extraction."""
    
    # MediaPipe Face Mesh landmark indices
    LANDMARKS = {
        # Eyes
        'left_eye': [33, 160, 158, 133, 153, 144],
        'right_eye': [362, 385, 387, 263, 373, 380],
        
        # Eyebrows
        'left_eyebrow': [46, 52, 53, 55, 70],
        'right_eyebrow': [276, 282, 283, 285, 295],
        
        # Mouth
        'mouth_outline': [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375],
        'mouth_inner': [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324],
        
        # Nose
        'nose_tip': [4],
        'nose_bridge': [6, 122, 351],
        
        # Face outline
        'face_outline': [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10]
    }
    
    @staticmethod
    def get_landmark_coordinates(landmarks, landmark_indices: List[int]) -> np.ndarray:
        """
        Extract coordinates for specific landmarks.
        Returns array of shape (N, 3) with x, y, z coordinates.
        """
        coords = []
        for idx in landmark_indices:
            if idx < len(landmarks):
                lm = landmarks[idx]
                coords.append([lm.x, lm.y, lm.z])
        return np.array(coords)
    
    @staticmethod
    def euclidean_distance(point1: np.ndarray, point2: np.ndarray) -> float:
        """Calculate Euclidean distance between two points."""
        return np.linalg.norm(point1 - point2)
    
    @staticmethod
    def calculate_distance_ratio(landmarks, idx1: int, idx2: int, idx3: int, idx4: int) -> float:
        """
        Calculate ratio of two distances for robust feature detection.
        Useful for scale-invariant measurements.
        """
        p1 = np.array([landmarks[idx1].x, landmarks[idx1].y])
        p2 = np.array([landmarks[idx2].x, landmarks[idx2].y])
        p3 = np.array([landmarks[idx3].x, landmarks[idx3].y])
        p4 = np.array([landmarks[idx4].x, landmarks[idx4].y])
        
        dist1 = LandmarkProcessor.euclidean_distance(p1, p2)
        dist2 = LandmarkProcessor.euclidean_distance(p3, p4)
        
        return dist1 / (dist2 + 1e-6)  # Avoid division by zero
    
    @staticmethod
    def get_face_center(landmarks) -> np.ndarray:
        """Calculate the center point of the face."""
        coords = LandmarkProcessor.get_landmark_coordinates(
            landmarks, 
            LandmarkProcessor.LANDMARKS['face_outline']
        )
        return np.mean(coords, axis=0)
    
    @staticmethod
    def get_face_dimensions(landmarks) -> Dict[str, float]:
        """
        Calculate face dimensions (width, height, aspect ratio).
        Useful for normalization and scale-invariant features.
        """
        face_coords = LandmarkProcessor.get_landmark_coordinates(
            landmarks,
            LandmarkProcessor.LANDMARKS['face_outline']
        )
        
        xs = face_coords[:, 0]
        ys = face_coords[:, 1]
        
        width = np.max(xs) - np.min(xs)
        height = np.max(ys) - np.min(ys)
        
        return {
            'width': float(width),
            'height': float(height),
            'aspect_ratio': float(width / (height + 1e-6))
        }


class FeatureExtractor:
    """Extract high-level facial features from landmarks."""
    
    @staticmethod
    def get_eyebrow_position(landmarks, side: str = 'left') -> Dict[str, float]:
        """
        Calculate eyebrow position metrics.
        Returns: height (normalized), angle, and openness.
        """
        if side == 'left':
            indices = LandmarkProcessor.LANDMARKS['left_eyebrow']
            eye_indices = LandmarkProcessor.LANDMARKS['left_eye']
        else:
            indices = LandmarkProcessor.LANDMARKS['right_eyebrow']
            eye_indices = LandmarkProcessor.LANDMARKS['right_eye']
        
        eyebrow_coords = LandmarkProcessor.get_landmark_coordinates(landmarks, indices)
        eye_coords = LandmarkProcessor.get_landmark_coordinates(landmarks, eye_indices)
        
        eyebrow_center_y = np.mean(eyebrow_coords[:, 1])
        eye_center_y = np.mean(eye_coords[:, 1])
        
        # Calculate height difference (normalized)
        height_diff = eye_center_y - eyebrow_center_y
        
        # Calculate angle of eyebrow (left to right slope)
        angle = np.arctan2(
            eyebrow_coords[-1, 1] - eyebrow_coords[0, 1],
            eyebrow_coords[-1, 0] - eyebrow_coords[0, 0]
        )
        
        return {
            'height': float(height_diff),
            'angle': float(np.degrees(angle)),
            'raised': height_diff > 0.02  # Threshold for "raised"
        }
    
    @staticmethod
    def get_mouth_openness(landmarks) -> Dict[str, float]:
        """
        Calculate mouth openness metrics.
        Returns: openness ratio and vertical/horizontal distances.
        """
        mouth_outline = LandmarkProcessor.get_landmark_coordinates(
            landmarks,
            LandmarkProcessor.LANDMARKS['mouth_outline']
        )
        
        # Top and bottom lip distances
        top_lip_y = np.mean([mouth_outline[i, 1] for i in [0, 1, 2]])
        bottom_lip_y = np.mean([mouth_outline[i, 1] for i in [6, 7, 8]])
        
        # Left and right mouth distances
        left_mouth_x = np.mean([mouth_outline[i, 0] for i in [0, 11]])
        right_mouth_x = np.mean([mouth_outline[i, 0] for i in [4, 5]])
        
        vertical_distance = bottom_lip_y - top_lip_y
        horizontal_distance = right_mouth_x - left_mouth_x
        
        # Openness ratio
        openness_ratio = vertical_distance / (horizontal_distance + 1e-6)
        
        return {
            'vertical_distance': float(vertical_distance),
            'horizontal_distance': float(horizontal_distance),
            'openness_ratio': float(openness_ratio),
            'is_open': openness_ratio > 0.3
        }
    
    @staticmethod
    def get_eye_openness(landmarks, side: str = 'left') -> Dict[str, float]:
        """
        Calculate eye openness metrics.
        Returns: openness ratio, eye aspect ratio (EAR).
        """
        if side == 'left':
            indices = LandmarkProcessor.LANDMARKS['left_eye']
        else:
            indices = LandmarkProcessor.LANDMARKS['right_eye']
        
        eye_coords = LandmarkProcessor.get_landmark_coordinates(landmarks, indices)
        
        # Eye Aspect Ratio (EAR) calculation
        # Distance between vertical eye landmarks
        vertical_dist = (
            LandmarkProcessor.euclidean_distance(eye_coords[1], eye_coords[4]) +
            LandmarkProcessor.euclidean_distance(eye_coords[2], eye_coords[3])
        ) / 2.0
        
        # Distance between horizontal eye landmarks
        horizontal_dist = LandmarkProcessor.euclidean_distance(eye_coords[0], eye_coords[5])
        
        ear = vertical_dist / (horizontal_dist + 1e-6)
        
        return {
            'eye_aspect_ratio': float(ear),
            'is_open': ear > 0.15
        }
    
    @staticmethod
    def get_head_pose(landmarks) -> Dict[str, float]:
        """
        Estimate head pose (pitch, yaw, roll) from facial landmarks.
        Returns angles in degrees.
        """
        # Use nose tip and face outline points
        nose_tip = np.array([landmarks[4].x, landmarks[4].y])
        
        # Face center
        face_coords = LandmarkProcessor.get_landmark_coordinates(
            landmarks,
            LandmarkProcessor.LANDMARKS['face_outline']
        )
        face_center = np.mean(face_coords[:, :2], axis=0)
        
        # Simplified head pose estimation
        yaw = np.degrees(np.arctan2(nose_tip[0] - face_center[0], 0.3))
        pitch = np.degrees(np.arctan2(nose_tip[1] - face_center[1], 0.3))
        
        return {
            'yaw': float(yaw),
            'pitch': float(pitch),
            'roll': 0.0  # Requires more complex calculation
        }


class DataSmoother:
    """Smooth predictions across frames to reduce jitter."""
    
    def __init__(self, window_size: int = 5):
        """Initialize smoother with specified window size."""
        self.window_size = window_size
        self.emotion_history = deque(maxlen=window_size)
        self.expression_history = deque(maxlen=window_size)
        self.confidence_history = deque(maxlen=window_size)
    
    def smooth_emotion(self, emotion: str, confidence: float) -> Tuple[str, float]:
        """
        Smooth emotion predictions using majority voting.
        Returns smoothed emotion and average confidence.
        """
        self.emotion_history.append(emotion)
        self.confidence_history.append(confidence)
        
        if len(self.emotion_history) > 0:
            # Get most common emotion
            from collections import Counter
            emotion_counts = Counter(self.emotion_history)
            smoothed_emotion = emotion_counts.most_common(1)[0][0]
            
            # Average confidence for smoothed emotion
            smoothed_confidence = np.mean([
                conf for emo, conf in zip(self.emotion_history, self.confidence_history)
                if emo == smoothed_emotion
            ])
            
            return smoothed_emotion, float(smoothed_confidence)
        
        return emotion, confidence
    
    def smooth_expression(self, expression: str) -> str:
        """Smooth expression predictions using majority voting."""
        self.expression_history.append(expression)
        
        if len(self.expression_history) > 0:
            from collections import Counter
            expr_counts = Counter(self.expression_history)
            return expr_counts.most_common(1)[0][0]
        
        return expression
    
    def reset(self):
        """Reset all histories."""
        self.emotion_history.clear()
        self.expression_history.clear()
        self.confidence_history.clear()
