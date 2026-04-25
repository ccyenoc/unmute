"""
Detection Routes
Real-time sign language detection from video/images
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
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
        raise HTTPException(status_code=400, detail="Invalid image")

    try:
        result = predict_sign(frame)
    except Exception as e:
        print("❌ Prediction error:", e)
        raise HTTPException(status_code=500, detail="Prediction failed")

    print(f"✅ Prediction: {result.get('prediction')}")

    return result