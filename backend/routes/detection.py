from fastapi import APIRouter, UploadFile, File
import numpy as np
import cv2

router = APIRouter()

# temporary test endpoint (to confirm backend works)
@router.post("/test")
async def test_route():
    return {"message": "Detection route working"}