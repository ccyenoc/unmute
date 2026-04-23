from fastapi import APIRouter, UploadFile, File
from services.emotion_detector import FacialAI
import cv2
import numpy as np

router = APIRouter()
facial_ai = FacialAI()

@router.post("/analyze-facial")
async def analyze_facial(file: UploadFile = File(...)):
    # Convert uploaded file to OpenCV format
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Run AI analysis
    result = facial_ai.analyze_frame(frame)

    return {
        "status": "success",
        "data": result
    }