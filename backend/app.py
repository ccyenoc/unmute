"""
Sign Language Translator - FastAPI Backend
Main application entry point
"""
import os

# Keep TensorFlow startup noise out of the server logs.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from dotenv import load_dotenv
import json

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from routes.detection import router as detection_router
from routes.emotion import predict_router as emotion_predict_router
from routes.emotion import router as emotion_router
from routes.fusion import router as fusion_router
from routes.history import router as history_router
from routes.training import router as training_router
from services.facial_emotion_service import predict_emotion_pipeline, predict_emotion_pipeline_from_base64

load_dotenv()

app = FastAPI(
    title="Sign Language Translator API",
    description="Backend API for real-time sign language detection",
    version="1.0.0"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detection_router, prefix="/api/detection", tags=["Detection"])
app.include_router(emotion_router, prefix="/api/facial-emotion", tags=["Facial Emotion"])
app.include_router(emotion_predict_router, prefix="/api/emotion", tags=["Emotion API"])
app.include_router(fusion_router, prefix="/api/fusion", tags=["Fusion"])
app.include_router(history_router, prefix="/api/history", tags=["History"])
app.include_router(training_router, prefix="/api/training", tags=["Training"])

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Sign Language Translator API",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "message": "Backend is running"
    }


@app.post("/predict-emotion")
async def predict_emotion_root(request: Request, file: UploadFile | None = File(default=None)):
    """Compatibility endpoint for older facial emotion clients."""
    try:
        if file is not None:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Uploaded file must be an image")
            image_bytes = await file.read()
            result = predict_emotion_pipeline(image_bytes)
            return {
                "emotion": str(result.get("emotion", "neutral")),
                "confidence": float(result.get("confidence", 0.0)),
                "face_detected": bool(result.get("face_detected", False)),
            }

        raw_body = await request.body()
        if not raw_body:
            raise HTTPException(
                status_code=400,
                detail="Provide either an image file or JSON body with 'image' base64 field",
            )

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

        image_base64 = payload.get("image") or payload.get("image_base64")
        if not image_base64 or not isinstance(image_base64, str):
            raise HTTPException(status_code=400, detail="JSON payload must include 'image' or 'image_base64' string")

        result = predict_emotion_pipeline_from_base64(image_base64)
        return {
            "emotion": str(result.get("emotion", "neutral")),
            "confidence": float(result.get("confidence", 0.0)),
            "face_detected": bool(result.get("face_detected", False)),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
