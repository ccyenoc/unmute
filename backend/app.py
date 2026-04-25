"""
Sign Language Translator - FastAPI Backend
Main application entry point
"""
import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routes.detection import router as detection_router
from routes.emotion import router as emotion_router
from routes.fusion import router as fusion_router
from routes.emotion import router as emotion_router
from routes.emotion import predict_router as emotion_predict_router

from routes.emotion import predict_router as emotion_predict_router

load_dotenv()

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Sign Language Translator API",
    description="Backend API for real-time sign language detection",
    version="1.0.0",
)


app.include_router(emotion_predict_router, prefix="/api/emotion", tags=["Emotion"])

# ✅ CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers (ONLY what you actually use)
app.include_router(detection_router, prefix="/api/detection", tags=["Detection"])
app.include_router(fusion_router, prefix="/api/fusion", tags=["Fusion"])
app.include_router(emotion_router, prefix="/api/emotion", tags=["Emotion"])
app.include_router(emotion_predict_router, prefix="/api/emotion", tags=["Emotion"])


# ✅ Health endpoints
@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Sign Language Translator API",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend is running",
    }


# ✅ Run server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )