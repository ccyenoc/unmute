"""
Facial Emotion Routes
Endpoints for analyzing emotion from uploaded images or base64 camera frames.
"""

from __future__ import annotations

import base64
import logging
import json

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, Request, UploadFile
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
    predict_emotion_pipeline,
    predict_emotion_pipeline_from_base64,
)
from services.emotion_detector import get_fen_model_info

router = APIRouter()
predict_router = APIRouter()
logger = logging.getLogger("uvicorn.error")


class EmotionFrameRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image or data URL")


class EmotionSnapshotRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded image (matches mobile snapshot payload)")


class EmotionSampleFrameRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image for sample collection")


class EmotionPredictResponse(BaseModel):
    emotion: str
    confidence: float
    face_detected: bool


class EmotionPredictSnapshotRequest(BaseModel):
    image: str | None = Field(default=None, description="Base64-encoded image payload")
    image_base64: str | None = Field(default=None, description="Base64-encoded image payload")


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
    """Snapshot endpoint for frontend camera payloads.

    Accepts payload: {"image": "<base64>"}
    Uses MediaPipe-first pipeline with FEN/FER/DeepFace providers.
    """
    try:
        logger.warning("FACIAL_API request: image_base64_length=%s", len(payload.image or ""))
        pipeline = predict_emotion_pipeline_from_base64(payload.image)
        face_detected = bool(pipeline.get("face_detected", False))
        result = {
            "success": bool(pipeline.get("success", True)),
            "face_detected": face_detected,
            "faces_detected": 1 if face_detected else 0,
            "provider": pipeline.get("provider"),
            "emotion": str(pipeline.get("emotion", "neutral")),
            "confidence": float(pipeline.get("confidence", 0.0)),
            "scores": pipeline.get("scores", {}),
            "results": [],
        }
        if not face_detected:
            result["message"] = "No face detected"
        logger.warning(
            "FACIAL_API result: emotion=%s confidence=%s provider=%s face_detected=%s",
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


@predict_router.post("/predict", response_model=EmotionPredictResponse)
async def predict_emotion(request: Request, file: UploadFile | None = File(default=None)):
    """Predict emotion from either JSON base64 payload or uploaded image file.

    Supported inputs:
    - application/json: {"image": "<base64>"}
    - multipart/form-data: file=<image>
    """
    try:
        if file is not None:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Uploaded file must be an image")
            image_bytes = await file.read()
            return predict_emotion_pipeline(image_bytes)

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

        image_base64 = payload.get("image")
        if not image_base64 or not isinstance(image_base64, str):
            raise HTTPException(status_code=400, detail="JSON payload must include 'image' base64 string")

        return predict_emotion_pipeline_from_base64(image_base64)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/predict-emotion", response_model=EmotionPredictResponse)
async def predict_emotion_compat(request: Request, file: UploadFile | None = File(default=None)):
    """Compatibility endpoint for Colab or simple frontend integrations.

    Accepts either multipart file upload or JSON base64 payload.
    """
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


@router.post("/collect-sample-frame")
def collect_sample_frame(
    payload: EmotionSampleFrameRequest,
    label: str = Query(..., description="Emotion label (happy, angry, neutral, etc.)"),
):
    try:
        image_base64 = payload.image_base64 or ""
        image_payload = image_base64.split(",", 1)[-1]
        image_bytes = base64.b64decode(image_payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid base64 payload: {exc}") from exc

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