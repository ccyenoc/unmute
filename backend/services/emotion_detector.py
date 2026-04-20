"""
MediaPipe + FEN emotion detector.

This module implements the custom facial pipeline:
- dataset collection
- MediaPipe face feature extraction
- TensorFlow/Keras model training and .h5 persistence
- emotion prediction from image bytes
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import to_categorical

EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data" / "emotion_dataset"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "emotion_fen_model.h5"
META_PATH = MODELS_DIR / "emotion_fen_model_meta.json"

mp_face_mesh = mp.solutions.face_mesh

# Dense but still compact subset focusing on brows, eyes, and mouth areas.
LANDMARK_IDX = [
    10, 151, 9, 8,
    70, 63, 105, 66, 107, 336, 296, 334, 293, 300,
    33, 160, 158, 133, 153, 144, 362, 385, 387, 263, 373, 380,
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
    13, 14, 78, 308,
]


def ensure_dirs() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for label in EMOTION_LABELS:
        (DATASET_DIR / label).mkdir(parents=True, exist_ok=True)


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("Could not decode image bytes")
    return image_bgr


def extract_face_features(image_bgr: np.ndarray) -> Optional[np.ndarray]:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
    ) as face_mesh:
        result = face_mesh.process(image_rgb)

    if not result.multi_face_landmarks:
        return None

    landmarks = result.multi_face_landmarks[0].landmark
    feat: List[float] = []
    for idx in LANDMARK_IDX:
        point = landmarks[idx]
        feat.extend([point.x, point.y, point.z])

    return np.array(feat, dtype=np.float32)


def save_emotion_sample(label: str, image_bytes: bytes) -> Dict[str, Any]:
    ensure_dirs()
    normalized = label.lower().strip()
    if normalized not in EMOTION_LABELS:
        raise ValueError(f"Unsupported emotion label: {label}")

    image_bgr = decode_image_bytes(image_bytes)
    # Validate that at least one face exists for usable sample quality.
    if extract_face_features(image_bgr) is None:
        raise ValueError("No face detected in sample")

    file_name = f"{normalized}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    out_path = DATASET_DIR / normalized / file_name
    ok, encoded = cv2.imencode(".jpg", image_bgr)
    if not ok:
        raise ValueError("Failed to encode sample image")
    out_path.write_bytes(encoded.tobytes())

    return {
        "label": normalized,
        "file_name": file_name,
        "file_path": str(out_path.relative_to(BASE_DIR)),
    }


def get_dataset_info() -> Dict[str, Any]:
    ensure_dirs()
    per_emotion: Dict[str, int] = {}
    total = 0
    for label in EMOTION_LABELS:
        count = len(list((DATASET_DIR / label).glob("*.jpg")))
        per_emotion[label] = count
        total += count

    return {
        "dataset_dir": str(DATASET_DIR.relative_to(BASE_DIR)),
        "total_images": total,
        "per_emotion": per_emotion,
        "classes_with_data": [k for k, v in per_emotion.items() if v > 0],
    }


def _load_training_data() -> Tuple[np.ndarray, np.ndarray, Dict[int, str]]:
    features: List[np.ndarray] = []
    label_ids: List[int] = []

    idx_to_label: Dict[int, str] = {}
    label_to_idx: Dict[str, int] = {}

    for label in EMOTION_LABELS:
        image_files = list((DATASET_DIR / label).glob("*.jpg"))
        if not image_files:
            continue

        label_idx = len(label_to_idx)
        label_to_idx[label] = label_idx
        idx_to_label[label_idx] = label

        for image_path in image_files:
            image_bgr = cv2.imread(str(image_path))
            if image_bgr is None:
                continue
            feat = extract_face_features(image_bgr)
            if feat is None:
                continue
            features.append(feat)
            label_ids.append(label_idx)

    if not features:
        raise ValueError("No usable facial features found in dataset")

    return np.vstack(features), np.array(label_ids, dtype=np.int32), idx_to_label


def train_fen_model(epochs: int = 30, batch_size: int = 32) -> Dict[str, Any]:
    ensure_dirs()
    X, y, idx_to_label = _load_training_data()

    if len(np.unique(y)) < 2:
        raise ValueError("Need at least 2 emotion classes with valid face samples")

    num_classes = len(idx_to_label)
    y_cat = to_categorical(y, num_classes=num_classes)

    model = Sequential(
        [
            Input(shape=(X.shape[1],)),
            Dense(256, activation="relu"),
            Dropout(0.3),
            Dense(128, activation="relu"),
            Dropout(0.2),
            Dense(64, activation="relu"),
            Dense(num_classes, activation="softmax"),
        ]
    )

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    history = model.fit(
        X,
        y_cat,
        validation_split=0.2,
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
    )

    model.save(MODEL_PATH)

    meta = {
        "model_path": str(MODEL_PATH.relative_to(BASE_DIR)),
        "feature_size": int(X.shape[1]),
        "labels": idx_to_label,
        "epochs": epochs,
        "batch_size": batch_size,
        "samples": int(X.shape[0]),
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "final_train_loss": float(history.history["loss"][-1]),
        "final_train_accuracy": float(history.history["accuracy"][-1]),
        "final_val_loss": float(history.history["val_loss"][-1]),
        "final_val_accuracy": float(history.history["val_accuracy"][-1]),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return meta


def get_fen_model_info() -> Dict[str, Any]:
    ensure_dirs()
    if not MODEL_PATH.exists() or not META_PATH.exists():
        return {
            "ready": False,
            "model_path": str(MODEL_PATH.relative_to(BASE_DIR)),
            "message": "FEN model not trained yet",
        }

    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    return {
        "ready": True,
        **meta,
    }


def predict_with_fen(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    if not MODEL_PATH.exists() or not META_PATH.exists():
        return None

    image_bgr = decode_image_bytes(image_bytes)
    feat = extract_face_features(image_bgr)
    if feat is None:
        return {
            "success": True,
            "face_detected": False,
            "emotion": "neutral",
            "confidence": 0.0,
            "scores": {label: 0.0 for label in EMOTION_LABELS},
            "provider": "fen",
            "message": "No face detected",
        }

    model = load_model(MODEL_PATH)
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    idx_to_label = {int(k): v for k, v in meta["labels"].items()}

    probs = model.predict(np.expand_dims(feat, axis=0), verbose=0)[0]
    best_idx = int(np.argmax(probs))
    emotion = idx_to_label.get(best_idx, "neutral")

    scores = {label: 0.0 for label in EMOTION_LABELS}
    for idx, label in idx_to_label.items():
        scores[label] = round(float(probs[idx] * 100.0), 4)

    return {
        "success": True,
        "face_detected": True,
        "faces_detected": 1,
        "emotion": emotion,
        "confidence": round(float(probs[best_idx] * 100.0), 4),
        "scores": scores,
        "provider": "fen",
    }
