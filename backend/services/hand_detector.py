"""
MediaPipe Hand Detection Module
Handles real-time hand tracking and keypoint extraction
"""
import mediapipe as mp
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import json

class HandDetector:
    """
    Detects hands in images/video frames using MediaPipe.
    Extracts hand landmarks (21 keypoints per hand).
    """
    
    def __init__(self, max_hands: int = 2, min_confidence: float = 0.5):
        """
        Initialize MediaPipe Hand detector
        
        Args:
            max_hands: Maximum number of hands to detect
            min_confidence: Minimum confidence threshold for detection
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=min_confidence,
            min_tracking_confidence=min_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.max_hands = max_hands
        
    def detect_hands(self, image: np.ndarray) -> Dict:
        """
        Detect hands in an image
        
        Args:
            image: Input image (numpy array, BGR format)
            
        Returns:
            Dict containing:
            - landmarks: List of hand landmarks
            - handedness: List indicating left/right hand
            - image: Annotated image with hand pose overlays
            - success: Boolean indicating if hands were detected
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)
        
        # Prepare output
        output = {
            "success": False,
            "landmarks": [],
            "handedness": [],
            "image": image.copy(),
            "num_hands_detected": 0
        }
        
        if results.multi_hand_landmarks and results.multi_handedness:
            output["success"] = True
            output["num_hands_detected"] = len(results.multi_hand_landmarks)
            
            # Extract landmarks for each hand
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness
            ):
                # Convert landmarks to list format
                landmarks_list = []
                h, w, c = image.shape
                
                for landmark in hand_landmarks.landmark:
                    # Normalize coordinates
                    x = landmark.x
                    y = landmark.y
                    z = landmark.z
                    landmarks_list.append({
                        "x": x,
                        "y": y,
                        "z": z,
                        "visibility": landmark.visibility
                    })
                
                output["landmarks"].append(landmarks_list)
                output["handedness"].append(handedness.classification[0].label)
            
            # Draw hand poses on image
            annotated_image = image.copy()
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
            output["image"] = annotated_image
        
        return output
    
    def extract_features(self, landmarks: List[Dict]) -> np.ndarray:
        """
        Extract features from hand landmarks for ML model
        
        Args:
            landmarks: List of landmark dictionaries
            
        Returns:
            Feature vector (21 * 3 = 63 dimensions for x, y, z coordinates)
        """
        features = []
        for landmark in landmarks:
            features.extend([landmark["x"], landmark["y"], landmark["z"]])
        return np.array(features)
    
    def get_hand_pose_vector(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Get pose vector from image - ready for ML model input
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (feature_vector, detection_success)
        """
        results = self.detect_hands(image)
        
        if results["success"] and len(results["landmarks"]) > 0:
            # Use first hand detected
            features = self.extract_features(results["landmarks"][0])
            return features, True
        else:
            return np.zeros(63), False  # 21 landmarks * 3 coordinates
    
    def close(self):
        """Clean up resources"""
        self.hands.close()
