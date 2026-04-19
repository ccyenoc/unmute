"""
Detection Routes
Real-time sign language detection from video/images
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import base64

from services.hand_detector import HandDetector
from services.sign_language_model import SignLanguageModel

router = APIRouter()

# Initialize services (singleton)
hand_detector = HandDetector(max_hands=2, min_confidence=0.5)
model = SignLanguageModel()

@router.post("/detect-image")
async def detect_image(file: UploadFile = File(...)):
    """
    Detect sign language from uploaded image
    
    Args:
        file: Image file (JPG, PNG, etc.)
        
    Returns:
        Detection results with landmarks and predicted sign
    """
    try:
        # Read image
        contents = await file.read()
        img = Image.open(BytesIO(contents))
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Detect hands
        detection_results = hand_detector.detect_hands(frame)
        
        if not detection_results["success"]:
            return {
                "success": False,
                "message": "No hands detected in image"
            }
        
        # Extract features and predict
        predictions = []
        for landmarks in detection_results["landmarks"]:
            features = hand_detector.extract_features(landmarks)
            prediction = model.predict(features)
            predictions.append(prediction)
        
        # Encode annotated image
        _, buffer = cv2.imencode('.jpg', detection_results["image"])
        img_str = base64.b64encode(buffer).decode()
        
        return {
            "success": True,
            "num_hands_detected": detection_results["num_hands_detected"],
            "predictions": predictions,
            "handedness": detection_results["handedness"],
            "annotated_image": img_str
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/detect-frame")
async def detect_frame(file: UploadFile = File(...)):
    """
    Detect from single video frame (real-time usage)
    Optimized for mobile/frontend streaming
    """
    try:
        contents = await file.read()
        img = Image.open(BytesIO(contents))
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Detect hands
        detection_results = hand_detector.detect_hands(frame)
        
        if not detection_results["success"]:
            return {
                "success": False,
                "detected": False
            }
        
        # Get prediction from first hand
        features = hand_detector.extract_features(detection_results["landmarks"][0])
        prediction = model.predict(features, confidence_threshold=0.6)
        
        return {
            "success": True,
            "detected": True,
            "prediction": prediction["prediction"],
            "confidence": prediction["confidence"],
            "handedness": detection_results["handedness"][0]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/model-info")
def get_model_info():
    """Get information about the current model"""
    return {
        "model_loaded": model.model is not None,
        "num_classes": len(model.classes),
        "classes": model.classes,
        "model_path": model.model_path
    }

@router.get("/test-detection")
def test_detection():
    """
    Test detection with a simple synthetic image
    Useful for debugging
    """
    # Create a test image (white background with black circle)
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.circle(test_image, (320, 240), 50, (0, 0, 0), -1)
    
    results = hand_detector.detect_hands(test_image)
    
    return {
        "success": results["success"],
        "message": "Test completed",
        "hands_detected": results["num_hands_detected"]
    }
