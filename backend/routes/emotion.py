from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import numpy as np

from services.emotion_detector import predict_emotion

router = APIRouter()
predict_router = APIRouter()


@predict_router.post("/predict")
async def predict_emotion_api(file: UploadFile = File(...)):
    contents = await file.read()

    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    return predict_emotion(frame)