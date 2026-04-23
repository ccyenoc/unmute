
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Import routers
from backend.routes.detection import router as detection_router
from backend.routes.emotion import router as emotion_router

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
app.include_router(emotion_router, prefix="/api/emotion", tags=["Emotion Detection"])

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

