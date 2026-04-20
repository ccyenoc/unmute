"""Colab-ready Facial Emotion API.

This file provides a small FastAPI app that exposes a frontend-friendly
emotion endpoint and reuses the repository's existing facial emotion pipeline.

Usage in Colab or locally:
1. Make sure the repo files are available in the runtime.
2. Install dependencies.
3. Run: python colab_facial_emotion_api.py
4. Point the frontend to http://<host>:8000 or the Colab tunnel URL.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes.emotion import predict_emotion_pipeline, predict_emotion_pipeline_from_base64
from services.emotion_detector import get_fen_model_info

app = FastAPI(
    title="Facial Expression API",
    description="Colab-ready facial emotion detection API for frontend integration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "service": "facial-expression-api",
        "mode": "colab-ready",
    }


@app.head("/")
def root_head() -> None:
    return None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "facial-expression-api"}


@app.head("/health")
def health_head() -> None:
    return None


@app.head("/{full_path:path}")
def wildcard_head(full_path: str) -> None:
    # Many local/dev tools probe hidden paths with HEAD (for example /.aws/ or /.ssh/).
    # Return an empty successful response to avoid repetitive 404 noise.
    return None


@app.get("/model-info")
def model_info() -> dict:
    return {
        "task": "facial_emotion_recognition",
        "fen_model": get_fen_model_info(),
        "message": "Uses the repository facial emotion pipeline and model files if available.",
    }


@app.post("/predict-emotion")
async def predict_emotion(request: Request, file: UploadFile | None = File(default=None)):
    """Predict emotion from either a multipart image file or a JSON base64 payload."""
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
                "provider": result.get("provider"),
                "scores": result.get("scores", {}),
            }

        raw_body = await request.body()
        if not raw_body:
            raise HTTPException(status_code=400, detail="Provide either an image file or JSON body with 'image' base64 field")

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
            "provider": result.get("provider"),
            "scores": result.get("scores", {}),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        log_level=os.getenv("UVICORN_LOG_LEVEL", "error"),
        access_log=os.getenv("UVICORN_ACCESS_LOG", "false").strip().lower() == "true",
    )
