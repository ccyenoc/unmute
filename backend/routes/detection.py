"""
Detection Routes
Real-time sign language detection from video/images
"""
from services.sign_language_model import predict_sign
from fastapi import APIRouter, UploadFile, File
import numpy as np
import cv2

from services.sign_language_model import predict_sign

router = APIRouter()

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    print("🔥 REQUEST RECEIVED")
    contents = await file.read()

    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        print("❌ Frame decode failed")
        return {
            "prediction": "No hand",
            "confidence": 0.0,
            "landmarks": []
        }

    result = predict_sign(frame)

    print(f"✅ Prediction: {result.get('prediction')}, Landmarks: {len(result.get('landmarks', []))} hands")

    return result