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
import mediapipe as mp
import numpy as np

from services.emotion_detector import (
    EMOTION_LABELS,
    FEN_USE_ARGMAX_LABEL,
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
USE_FEN = os.getenv("USE_FEN", "true").strip().lower() == "true"

# Reduce "always neutral" bias from provider outputs when non-neutral signal is strong.
NEUTRAL_OVERRIDE_MARGIN = float(os.getenv("NEUTRAL_OVERRIDE_MARGIN", "45.0"))
NEUTRAL_OVERRIDE_MIN_SCORE = float(os.getenv("NEUTRAL_OVERRIDE_MIN_SCORE", "1.0"))
FEN_MIN_CONFIDENCE_PERCENT = float(os.getenv("FEN_MIN_CONFIDENCE_PERCENT", "35.0"))
FEN_STRICT_MODE = os.getenv("FEN_STRICT_MODE", "true").strip().lower() == "true"
FEN_ONLY_MODE = os.getenv("FEN_ONLY_MODE", "true").strip().lower() == "true"

BASE_DIR = Path(__file__).resolve().parent.parent
EMOTION_DATASET_DIR = BASE_DIR / "data" / "emotion_dataset"

_TRAINING_STATE: Dict[str, Any] = {
    "running": False,
    "last_job": None,
    "jobs": {},
}
_TRAINING_LOCK = threading.Lock()

_mp_face_detection = mp.solutions.face_detection


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


def _detect_face_region_mediapipe(image_bgr: np.ndarray) -> Optional[Dict[str, int]]:
    """Detect the first face bounding box using MediaPipe Face Detection."""
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    h, w = image_bgr.shape[:2]

    with _mp_face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.5,
    ) as detector:
        result = detector.process(image_rgb)

    if not result.detections:
        return None

    bbox = result.detections[0].location_data.relative_bounding_box
    x = max(0, int(bbox.xmin * w))
    y = max(0, int(bbox.ymin * h))
    bw = int(bbox.width * w)
    bh = int(bbox.height * h)

    if bw <= 0 or bh <= 0:
        return None

    # Clamp to image dimensions.
    x2 = min(w, x + bw)
    y2 = min(h, y + bh)
    x = min(x, x2 - 1)
    y = min(y, y2 - 1)

    return {
        "x": x,
        "y": y,
        "w": max(1, x2 - x),
        "h": max(1, y2 - y),
    }


def _preprocess_face_crop(face_bgr: np.ndarray, size: int = 224) -> np.ndarray:
    """Resize and normalize face crop for model input."""
    resized = cv2.resize(face_bgr, (size, size), interpolation=cv2.INTER_AREA)
    return resized.astype(np.float32) / 255.0


def _encode_image_to_jpeg_bytes(image_bgr: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".jpg", image_bgr)
    if not ok:
        raise ValueError("Failed to encode face crop")
    return encoded.tobytes()


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
    numeric_values: List[float] = []
    for emotion in EMOTIONS:
        raw_value = scores.get(emotion, 0.0)
        try:
            numeric_values.append(float(raw_value))
        except (TypeError, ValueError):
            numeric_values.append(0.0)

    # If all scores are in [0, 1], treat them as probabilities and convert once.
    is_probability_scale = bool(numeric_values) and max(numeric_values) <= 1.0

    normalized: Dict[str, float] = {}
    for emotion in EMOTIONS:
        raw_value = scores.get(emotion, 0.0)
        try:
            score_value = float(raw_value)
            if is_probability_scale:
                score_value *= 100.0
            normalized[emotion] = round(score_value, 4)
        except (TypeError, ValueError):
            normalized[emotion] = 0.0
    return normalized


def _choose_emotion_from_scores(scores: Dict[str, Any], fallback: str = "neutral") -> str:
    normalized_scores = _normalize_emotion_percentages(scores)
    if not normalized_scores:
        return fallback

    top_emotion = max(normalized_scores, key=normalized_scores.get)
    if top_emotion != "neutral":
        return top_emotion

    top_score = float(normalized_scores.get("neutral", 0.0))
    non_neutral_scores = {k: v for k, v in normalized_scores.items() if k != "neutral"}
    if not non_neutral_scores:
        return "neutral"

    candidate = max(non_neutral_scores, key=non_neutral_scores.get)
    candidate_score = float(non_neutral_scores.get(candidate, 0.0))

    # If neutral only wins by a narrow margin and non-neutral is strong, use the non-neutral label.
    if candidate_score >= NEUTRAL_OVERRIDE_MIN_SCORE and (top_score - candidate_score) <= NEUTRAL_OVERRIDE_MARGIN:
        return candidate

    return "neutral"


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


def _weighted_merge_scores(score_sets: List[Dict[str, float]], weights: List[float]) -> Dict[str, float]:
    merged = {emotion: 0.0 for emotion in EMOTIONS}
    total_weight = 0.0

    for scores, weight in zip(score_sets, weights):
        if weight <= 0:
            continue
        total_weight += weight
        for emotion in EMOTIONS:
            merged[emotion] += float(scores.get(emotion, 0.0)) * weight

    if total_weight <= 0:
        return merged

    return {
        emotion: round(value / total_weight, 4)
        for emotion, value in merged.items()
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
        scores = face.get("emotion", {}) or {}
        emotion = _choose_emotion_from_scores(scores, fallback=str(face.get("dominant_emotion", "neutral")))
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


def predict_emotion_pipeline(image_bytes: bytes) -> Dict[str, Any]:
    """MediaPipe-first emotion prediction pipeline for API responses.

    Flow: decode image -> detect face bbox -> crop + preprocess -> infer emotion.
    Returns confidence in [0, 1].
    """
    image_bgr = _decode_image_bytes(image_bytes)
    face_region = _detect_face_region_mediapipe(image_bgr)

    face_crop = image_bgr
    if face_region is not None:
        x, y, w, h = face_region["x"], face_region["y"], face_region["w"], face_region["h"]
        face_crop = image_bgr[y : y + h, x : x + w]

    if face_crop.size == 0:
        return {
            "success": False,
            "emotion": "unavailable",
            "confidence": 0.0,
            "face_detected": False,
            "provider": "fen",
            "scores": _normalize_emotion_scores({}),
            "message": "Invalid face crop",
        }

    # Preprocessing step required by the pipeline contract.
    _ = _preprocess_face_crop(face_crop, size=224)

    # Option B: landmark-based model (FEN)
    if USE_FEN:
        fen_result = predict_with_fen(_encode_image_to_jpeg_bytes(face_crop))
        if fen_result is not None:
            confidence = float(fen_result.get("confidence", 0.0))
            if confidence > 1.0:
                confidence = confidence / 100.0
            confidence_percent = round(max(0.0, min(1.0, confidence)) * 100.0, 4)
            scores = _normalize_emotion_percentages(fen_result.get("scores", {}))
            fen_emotion = str(fen_result.get("emotion", "neutral"))
            if FEN_USE_ARGMAX_LABEL:
                chosen_emotion = str(fen_result.get("model_emotion", fen_emotion))
            else:
                chosen_emotion = _choose_emotion_from_scores(scores, fallback=fen_emotion)
            chosen_confidence = float(scores.get(chosen_emotion, confidence_percent))
            chosen_confidence = round(max(0.0, min(100.0, chosen_confidence)), 4)

            # Use FEN directly, but preserve the model label even when confidence is modest.
            if confidence_percent >= FEN_MIN_CONFIDENCE_PERCENT:
                return {
                    "success": True,
                    "emotion": chosen_emotion,
                    "confidence": chosen_confidence,
                    "face_detected": bool(fen_result.get("face_detected", True)),
                    "provider": "fen",
                    "scores": scores,
                }

            if confidence_percent > 0:
                return {
                    "success": True,
                    "emotion": chosen_emotion,
                    "confidence": chosen_confidence,
                    "face_detected": bool(fen_result.get("face_detected", True)),
                    "provider": "fen",
                    "scores": scores,
                    "message": "FEN confidence is low; selected the strongest emotion from model scores.",
                }

            if FEN_STRICT_MODE:
                return {
                    "success": False,
                    "emotion": "unavailable",
                    "confidence": confidence_percent,
                    "face_detected": bool(fen_result.get("face_detected", True)),
                    "provider": "fen",
                    "scores": scores,
                    "message": "FEN confidence is too low.",
                }

        elif FEN_STRICT_MODE:
            return {
                "success": False,
                "emotion": "unavailable",
                "confidence": 0.0,
                "face_detected": False,
                "provider": "fen",
                "scores": _normalize_emotion_scores({}),
                "message": "FEN model is not trained yet. Train the model before using facial emotion output.",
            }

    if FEN_ONLY_MODE:
        return {
            "success": False,
            "emotion": "unavailable",
            "confidence": 0.0,
            "face_detected": bool(face_region is not None),
            "provider": "fen",
            "scores": _normalize_emotion_scores({}),
            "message": "FEN-only mode is enabled and FEN result is unavailable.",
        }

    # Provider consensus fallback on the face crop (FER + DeepFace).
    face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    provider_score_sets: List[Dict[str, float]] = []
    provider_weights: List[float] = []
    provider_names: List[str] = []

    if FER is not None:
        detector = FER(mtcnn=False)
        detections = detector.detect_emotions(face_rgb)
        if detections:
            scores = detections[0].get("emotions", {}) or {}
            if scores:
                provider_score_sets.append(_normalize_emotion_percentages(scores))
                provider_weights.append(0.45)
                provider_names.append("fer")

    if DeepFace is not None:
        analysis = DeepFace.analyze(
            img_path=face_rgb,
            actions=["emotion"],
            enforce_detection=False,
        )
        if isinstance(analysis, list):
            analysis = analysis[0] if analysis else {}
        scores = analysis.get("emotion", {}) or {}
        if scores:
            provider_score_sets.append(_normalize_emotion_percentages(scores))
            provider_weights.append(0.55)
            provider_names.append("deepface")

    if provider_score_sets:
        merged_scores = _weighted_merge_scores(provider_score_sets, provider_weights)
        emotion = _choose_emotion_from_scores(merged_scores)
        confidence_percent = float(merged_scores.get(emotion, 0.0))

        provider = "+".join(provider_names) if provider_names else "unknown"
        return {
            "success": True,
            "emotion": emotion,
            "confidence": round(max(0.0, min(100.0, confidence_percent)), 4),
            "face_detected": True,
            "provider": provider,
            "scores": merged_scores,
        }

    raise RuntimeError("No emotion model provider is available (FEN/FER/DeepFace)")


def predict_emotion_pipeline_from_base64(image_base64: str) -> Dict[str, Any]:
    return predict_emotion_pipeline(_decode_base64_image(image_base64))


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