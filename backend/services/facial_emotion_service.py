"""
Facial Emotion Analysis Service
Analyzes live camera frames or uploaded images and returns emotion scores.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
from uuid import uuid4

import cv2
import numpy as np

from services.emotion_detector import (
    EMOTION_LABELS,
    get_dataset_info as get_fen_dataset_info,
    get_fen_model_info,
    predict_with_fen,
    save_emotion_sample as save_fen_emotion_sample,
    train_fen_model,
)

try:
    from deepface import DeepFace
except Exception:  # pragma: no cover - optional dependency
    DeepFace = None

try:
    from fer import FER
except Exception:  # pragma: no cover - optional dependency
    try:
        from fer.fer import FER  # type: ignore
    except Exception:
        FER = None

EMOTIONS = EMOTION_LABELS
USE_FEN = os.getenv("USE_FEN", "false").strip().lower() == "true"

BASE_DIR = Path(__file__).resolve().parent.parent
EMOTION_DATASET_DIR = BASE_DIR / "data" / "emotion_dataset"

_TRAINING_STATE: Dict[str, Any] = {
    "running": False,
    "last_job": None,
    "jobs": {},
}
_TRAINING_LOCK = threading.Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_emotion_dataset_dirs() -> None:
    EMOTION_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    for emotion in EMOTIONS:
        (EMOTION_DATASET_DIR / emotion).mkdir(parents=True, exist_ok=True)


def _decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into an OpenCV BGR image."""
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image_bgr is None:
        raise ValueError("Could not decode image bytes")

    return image_bgr


def _decode_base64_image(image_base64: str) -> bytes:
    """Decode a base64 string, allowing data URLs."""
    payload = image_base64.split(",", 1)[-1]
    return base64.b64decode(payload)


def _normalize_emotion_scores(scores: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for emotion in EMOTIONS:
        raw_value = scores.get(emotion, 0.0)
        try:
            normalized[emotion] = round(float(raw_value), 4)
        except (TypeError, ValueError):
            normalized[emotion] = 0.0
    return normalized


def _normalize_emotion_percentages(scores: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for emotion in EMOTIONS:
        raw_value = scores.get(emotion, 0.0)
        try:
            score_value = float(raw_value)
            if score_value <= 1.0:
                score_value *= 100.0
            normalized[emotion] = round(score_value, 4)
        except (TypeError, ValueError):
            normalized[emotion] = 0.0
    return normalized


def _build_face_result(
    emotion: str,
    confidence: float,
    scores: Dict[str, Any],
    region: Optional[Dict[str, Any]] = None,
    provider: str = "deepface",
) -> Dict[str, Any]:
    return {
        "emotion": emotion,
        "confidence": round(float(confidence), 4),
        "scores": _normalize_emotion_percentages(scores),
        "region": region or {},
        "provider": provider,
    }


def _analyze_with_deepface(image_rgb: np.ndarray) -> List[Dict[str, Any]]:
    if DeepFace is None:
        raise RuntimeError("DeepFace is not installed")

    analysis = DeepFace.analyze(
        img_path=image_rgb,
        actions=["emotion"],
        enforce_detection=False,
    )

    if isinstance(analysis, dict):
        analysis = [analysis]

    results: List[Dict[str, Any]] = []
    for face in analysis:
        emotion = str(face.get("dominant_emotion", "neutral"))
        scores = face.get("emotion", {}) or {}
        confidence = scores.get(emotion, 0.0)
        results.append(
            _build_face_result(
                emotion=emotion,
                confidence=confidence,
                scores=scores,
                region=face.get("region", {}),
                provider="deepface",
            )
        )

    return results


def _analyze_with_fer(image_rgb: np.ndarray) -> List[Dict[str, Any]]:
    if FER is None:
        raise RuntimeError("FER is not installed")

    detector = FER(mtcnn=False)
    detections = detector.detect_emotions(image_rgb)
    results: List[Dict[str, Any]] = []

    for face in detections:
        scores = face.get("emotions", {}) or {}
        if scores:
            emotion = max(scores, key=scores.get)
            confidence = scores.get(emotion, 0.0) * 100.0 if scores.get(emotion, 0.0) <= 1 else scores.get(emotion, 0.0)
        else:
            emotion = "neutral"
            confidence = 0.0

        results.append(
            _build_face_result(
                emotion=emotion,
                confidence=confidence,
                scores=scores,
                region=face.get("box", {}),
                provider="fer",
            )
        )

    return results


def analyze_facial_emotion(image_bytes: bytes) -> Dict[str, Any]:
    """Analyze a single image and return the dominant facial emotion.

    The service prefers DeepFace and falls back to FER when needed.
    """
    if USE_FEN:
        fen_result = predict_with_fen(image_bytes)
        if fen_result is not None:
            return fen_result

    image_bgr = _decode_image_bytes(image_bytes)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    analysis_errors: List[str] = []
    results: List[Dict[str, Any]] = []

    if DeepFace is not None:
        try:
            results = _analyze_with_deepface(image_rgb)
        except Exception as exc:  # pragma: no cover - model/runtime fallback
            analysis_errors.append(f"deepface: {exc}")

    if not results and FER is not None:
        try:
            results = _analyze_with_fer(image_rgb)
        except Exception as exc:  # pragma: no cover - model/runtime fallback
            analysis_errors.append(f"fer: {exc}")

    if not results:
        if analysis_errors:
            raise RuntimeError("Emotion analysis failed: " + " | ".join(analysis_errors))

        return {
            "success": True,
            "face_detected": False,
            "faces_detected": 0,
            "provider": None,
            "emotion": "neutral",
            "confidence": 0.0,
            "scores": _normalize_emotion_scores({}),
            "results": [],
            "message": "No face detected",
        }

    dominant = max(results, key=lambda item: item.get("confidence", 0.0))

    return {
        "success": True,
        "face_detected": True,
        "faces_detected": len(results),
        "provider": dominant.get("provider"),
        "emotion": dominant.get("emotion", "neutral"),
        "confidence": dominant.get("confidence", 0.0),
        "scores": dominant.get("scores", _normalize_emotion_scores({})),
        "results": results,
    }


def analyze_facial_emotion_from_base64(image_base64: str) -> Dict[str, Any]:
    return analyze_facial_emotion(_decode_base64_image(image_base64))


def save_emotion_sample(label: str, image_bytes: bytes) -> Dict[str, Any]:
    return save_fen_emotion_sample(label=label, image_bytes=image_bytes)


def get_emotion_dataset_info() -> Dict[str, Any]:
    return get_fen_dataset_info()


def create_training_job(epochs: int, batch_size: int) -> Dict[str, Any]:
    with _TRAINING_LOCK:
        if _TRAINING_STATE["running"]:
            raise RuntimeError("A training job is already running")

        job_id = uuid4().hex
        job_state = {
            "job_id": job_id,
            "status": "running",
            "epochs": epochs,
            "batch_size": batch_size,
            "started_at": _utc_now_iso(),
            "finished_at": None,
            "summary": None,
        }

        _TRAINING_STATE["running"] = True
        _TRAINING_STATE["last_job"] = job_id
        _TRAINING_STATE["jobs"][job_id] = job_state

        return dict(job_state)


def run_training_job(job_id: str) -> None:
    try:
        with _TRAINING_LOCK:
            job = _TRAINING_STATE["jobs"].get(job_id)
            epochs = int(job.get("epochs", 20)) if job else 20
            batch_size = int(job.get("batch_size", 32)) if job else 32

        meta = train_fen_model(epochs=epochs, batch_size=batch_size)
        status = "completed"
        summary = {
            "message": "FEN model training completed",
            "model": get_fen_model_info(),
            "metrics": {
                "final_train_accuracy": meta.get("final_train_accuracy"),
                "final_val_accuracy": meta.get("final_val_accuracy"),
            },
            "dataset": get_emotion_dataset_info(),
        }
    except Exception as exc:  # pragma: no cover - defensive path
        status = "failed"
        summary = {
            "reason": f"Training job failed: {exc}",
        }

    with _TRAINING_LOCK:
        job = _TRAINING_STATE["jobs"].get(job_id)
        if job is None:
            return

        job["status"] = status
        job["summary"] = summary
        job["finished_at"] = _utc_now_iso()
        _TRAINING_STATE["running"] = False


def get_training_status(job_id: Optional[str] = None) -> Dict[str, Any]:
    with _TRAINING_LOCK:
        if job_id:
            job = _TRAINING_STATE["jobs"].get(job_id)
            if job is None:
                raise ValueError("Training job not found")
            return dict(job)

        last_job_id = _TRAINING_STATE["last_job"]
        last_job = _TRAINING_STATE["jobs"].get(last_job_id) if last_job_id else None
        return {
            "running": _TRAINING_STATE["running"],
            "last_job": dict(last_job) if last_job else None,
            "jobs_count": len(_TRAINING_STATE["jobs"]),
        }