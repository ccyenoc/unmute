"""
Facial Emotion Routes
Endpoints for analyzing emotion from uploaded images or base64 camera frames.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from services.facial_emotion_service import (
    EMOTIONS,
    FER,
    DeepFace,
    analyze_facial_emotion,
    analyze_facial_emotion_from_base64,
    create_training_job,
    get_emotion_dataset_info,
    get_training_status,
    run_training_job,
    save_emotion_sample,
    USE_FEN,
)
from services.emotion_detector import get_fen_model_info

router = APIRouter()
logger = logging.getLogger("facial-emotion")


class EmotionFrameRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image or data URL")


class EmotionSnapshotRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded image (matches mobile snapshot payload)")


@router.get("/health")
def emotion_health() -> dict:
    return {
        "status": "ok",
        "service": "facial-emotion",
    }


@router.get("/model-info")
def emotion_model_info() -> dict:
    return {
        "task": "facial_emotion_recognition",
        "available_emotions": EMOTIONS,
        "use_fen": USE_FEN,
        "providers": {
            "deepface": DeepFace is not None,
            "fer": FER is not None,
        },
        "fen_model": get_fen_model_info(),
    }


@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await file.read()

    try:
        result = analyze_facial_emotion(image_bytes)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/analyze-frame")
def analyze_frame(payload: EmotionFrameRequest):
    try:
        return analyze_facial_emotion_from_base64(payload.image_base64)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/emotion")
def analyze_snapshot(payload: EmotionSnapshotRequest):
    """Simple snapshot endpoint for demos.

    Accepts payload: {"image": "<base64>"}
    """
    try:
        logger.info("snapshot request received: image_base64_length=%s", len(payload.image or ""))
        result = analyze_facial_emotion_from_base64(payload.image)
        logger.info(
            "snapshot analyzed: emotion=%s confidence=%s provider=%s face_detected=%s",
            result.get("emotion"),
            result.get("confidence"),
            result.get("provider"),
            result.get("face_detected"),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/collect-sample")
async def collect_sample(
    label: str = Query(..., description="Emotion label (happy, angry, neutral, etc.)"),
    file: UploadFile = File(...),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await file.read()

    try:
        sample = save_emotion_sample(label=label, image_bytes=image_bytes)
        dataset_info = get_emotion_dataset_info()
        return {
            "success": True,
            "sample": sample,
            "dataset": dataset_info,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/dataset-info")
def dataset_info():
    return get_emotion_dataset_info()


@router.post("/train")
def train_model(
    background_tasks: BackgroundTasks,
    epochs: int = Query(20, ge=1, le=1000),
    batch_size: int = Query(32, ge=1, le=1024),
):
    try:
        job = create_training_job(epochs=epochs, batch_size=batch_size)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    background_tasks.add_task(run_training_job, job["job_id"])

    return {
        "success": True,
        "message": "Emotion training job started",
        "job": job,
    }


@router.get("/training-status")
def training_status(job_id: str | None = Query(default=None)):
    try:
        return get_training_status(job_id=job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc