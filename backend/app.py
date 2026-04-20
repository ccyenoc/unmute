"""
Sign Language Translator - FastAPI Backend
Main application entry point
"""
import os

# Keep TensorFlow startup noise out of the server logs.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from routes.detection import router as detection_router
from routes.emotion import predict_router as emotion_predict_router
from routes.emotion import router as emotion_router
from routes.fusion import router as fusion_router
from routes.history import router as history_router
from routes.training import router as training_router

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
