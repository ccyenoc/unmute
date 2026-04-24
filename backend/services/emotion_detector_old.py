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
import os
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from keras.models import load_model as keras_load_model
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import load_model as tf_load_model
from tensorflow.keras.utils import to_categorical

EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
DEFAULT_FEN_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
FACE_EXPAND_RATIO = float(os.getenv("FEN_FACE_EXPAND_RATIO", "0.2"))
NEUTRAL_SCORE_DAMPING = float(os.getenv("FEN_NEUTRAL_SCORE_DAMPING", "0.6"))
FEAR_SCORE_DAMPING = float(os.getenv("FEN_FEAR_SCORE_DAMPING", "0.82"))
FEAR_OVERRIDE_MARGIN = float(os.getenv("FEN_FEAR_OVERRIDE_MARGIN", "12.0"))
FEAR_OVERRIDE_MIN_SCORE = float(os.getenv("FEN_FEAR_OVERRIDE_MIN_SCORE", "15.0"))
FEN_USE_ARGMAX_LABEL = os.getenv("FEN_USE_ARGMAX_LABEL", "true").strip().lower() == "true"
FEN_USE_TTA = os.getenv("FEN_USE_TTA", "true").strip().lower() == "true"
FEN_SMILE_CALIBRATION = os.getenv("FEN_SMILE_CALIBRATION", "true").strip().lower() == "true"
FEN_SMILE_TRIGGER_MIN = float(os.getenv("FEN_SMILE_TRIGGER_MIN", "65.0"))
FEN_BASE_HAPPY_MIN = float(os.getenv("FEN_BASE_HAPPY_MIN", "18.0"))
FEN_HAPPY_PROMOTE_MARGIN = float(os.getenv("FEN_HAPPY_PROMOTE_MARGIN", "12.0"))
FEN_SMILE_STRONG_MIN = float(os.getenv("FEN_SMILE_STRONG_MIN", "75.0"))
FEN_SMILE_MAX_HAPPY_GAP = float(os.getenv("FEN_SMILE_MAX_HAPPY_GAP", "22.0"))
FEN_SMILE_HAPPY_BOOST_SCALE = float(os.getenv("FEN_SMILE_HAPPY_BOOST_SCALE", "0.9"))
FEN_SMILE_SAD_SUPPRESS = float(os.getenv("FEN_SMILE_SAD_SUPPRESS", "0.72"))
FEN_POST_LOGIC_ENABLED = os.getenv("FEN_POST_LOGIC_ENABLED", "true").strip().lower() == "true"
FEN_HAPPY_RESCUE_SMILE_MIN = float(os.getenv("FEN_HAPPY_RESCUE_SMILE_MIN", "68.0"))
FEN_HAPPY_RESCUE_HAPPY_MIN = float(os.getenv("FEN_HAPPY_RESCUE_HAPPY_MIN", "10.0"))
FEN_HAPPY_RESCUE_GAP_MAX = float(os.getenv("FEN_HAPPY_RESCUE_GAP_MAX", "16.0"))

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data" / "emotion_dataset"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = Path(os.getenv("FEN_MODEL_PATH", str(MODELS_DIR / "emotion_fen_model.h5")))
META_PATH = Path(os.getenv("FEN_META_PATH", str(MODELS_DIR / "emotion_fen_model_meta.json")))
MODEL_CANDIDATES = [
    MODEL_PATH,
    MODELS_DIR / "fen_model.h5",
    MODELS_DIR / "emotion_fen_model.h5",
]

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


def _resolve_existing_model_path() -> Optional[Path]:
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _resolve_meta_path_for_model(model_path: Path) -> Optional[Path]:
    candidate_names = [
        META_PATH,
        model_path.with_name(f"{model_path.stem}_meta.json"),
        model_path.with_name(f"{model_path.stem}_metadata.json"),
        model_path.with_suffix(".json"),
        MODELS_DIR / "fen_model_meta.json",
        MODELS_DIR / "emotion_fen_model_meta.json",
        MODELS_DIR / "metadata.json",
    ]
    for candidate in candidate_names:
        if candidate.exists():
            return candidate
    return None


def _infer_num_classes(model: Any) -> int:
    try:
        output_shape = tuple(model.output_shape or ())
        if len(output_shape) >= 2 and output_shape[-1]:
            return int(output_shape[-1])
    except Exception:
        pass
    return len(DEFAULT_FEN_LABELS)


def _default_labels_for_size(size: int) -> List[str]:
    if size <= 0:
        return list(DEFAULT_FEN_LABELS)

    labels = list(DEFAULT_FEN_LABELS)
    if size <= len(labels):
        return labels[:size]

    extras_needed = size - len(labels)
    extras = [label for label in EMOTION_LABELS if label not in labels]
    labels.extend(extras[:extras_needed])
    if len(labels) < size:
        labels.extend([f"class_{idx}" for idx in range(len(labels), size)])
    return labels


def _extract_labels_from_meta(meta: Dict[str, Any], num_classes: int) -> Optional[List[str]]:
    candidate_keys = ["labels", "label_map", "idx_to_label", "classes", "class_names"]

    for key in candidate_keys:
        value = meta.get(key)

        if isinstance(value, list) and value:
            labels = [str(item).strip().lower() for item in value]
        elif isinstance(value, dict) and value:
            labels = []
            if all(str(k).isdigit() for k in value.keys()):
                labels = [str(value[str(idx)]).strip().lower() for idx in sorted(int(k) for k in value.keys())]
            elif all(isinstance(v, int) for v in value.values()):
                inverse = {int(v): str(k).strip().lower() for k, v in value.items()}
                labels = [inverse[idx] for idx in sorted(inverse.keys())]
            else:
                labels = [str(item).strip().lower() for item in value.values()]
        else:
            continue

        labels = [label for label in labels if label]
        if not labels:
            continue

        if num_classes > 0:
            if len(labels) < num_classes:
                defaults = _default_labels_for_size(num_classes)
                labels.extend(defaults[len(labels) : num_classes])
            else:
                labels = labels[:num_classes]

        return labels

    return None


def _create_generated_meta_if_missing(model_path: Path, labels: List[str], input_mode: str) -> Optional[Path]:
    meta_path = model_path.with_name(f"{model_path.stem}_meta.json")
    if meta_path.exists():
        return meta_path

    payload = {
        "model_path": str(model_path.relative_to(BASE_DIR)),
        "labels": {str(idx): label for idx, label in enumerate(labels)},
        "input_mode": input_mode,
        "generated": True,
        "saved_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return meta_path
    except Exception:
        return None


def _expand_face_region(region: Dict[str, int], image_width: int, image_height: int, ratio: float) -> Dict[str, int]:
    x, y, w, h = region["x"], region["y"], region["w"], region["h"]
    if ratio <= 0:
        return {"x": x, "y": y, "w": w, "h": h}

    expand_w = int(w * ratio)
    expand_h = int(h * ratio)

    x1 = max(0, x - expand_w)
    y1 = max(0, y - expand_h)
    x2 = min(image_width, x + w + expand_w)
    y2 = min(image_height, y + h + expand_h)

    return {
        "x": x1,
        "y": y1,
        "w": max(1, x2 - x1),
        "h": max(1, y2 - y1),
    }


def _prepare_image_model_input(image_bgr: np.ndarray, input_shape: Tuple[Any, ...]) -> np.ndarray:
    height = int(input_shape[1]) if len(input_shape) > 1 and input_shape[1] else 48
    width = int(input_shape[2]) if len(input_shape) > 2 and input_shape[2] else 48
    channels = int(input_shape[3]) if len(input_shape) > 3 and input_shape[3] else 1

    if channels == 1:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        # Improve contrast in low-light frames to avoid flat predictions.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        face = cv2.resize(gray, (width, height), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        return np.expand_dims(face, axis=(0, -1))

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    face = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    return np.expand_dims(face, axis=0)


def _select_emotion_from_scores(scores: Dict[str, float], fallback: str = "neutral") -> str:
    if not scores:
        return fallback

    decision_scores = dict(scores)
    if "neutral" in decision_scores:
        decision_scores["neutral"] = round(float(decision_scores["neutral"]) * NEUTRAL_SCORE_DAMPING, 4)
    if "fear" in decision_scores:
        decision_scores["fear"] = round(float(decision_scores["fear"]) * FEAR_SCORE_DAMPING, 4)

    best_emotion = max(decision_scores, key=decision_scores.get)
    if best_emotion == "fear":
        fear_score = float(scores.get("fear", 0.0))
        alt_scores = {
            "angry": float(scores.get("angry", 0.0)),
            "sad": float(scores.get("sad", 0.0)),
        }
        alt_emotion = max(alt_scores, key=alt_scores.get)
        alt_score = float(alt_scores.get(alt_emotion, 0.0))
        if alt_score >= FEAR_OVERRIDE_MIN_SCORE and (fear_score - alt_score) <= FEAR_OVERRIDE_MARGIN:
            return alt_emotion

    if best_emotion != "neutral":
        return best_emotion

    neutral_score = float(scores.get("neutral", 0.0))
    non_neutral_scores = {key: value for key, value in scores.items() if key != "neutral"}
    if not non_neutral_scores:
        return "neutral"

    candidate = max(non_neutral_scores, key=non_neutral_scores.get)
    candidate_score = float(non_neutral_scores.get(candidate, 0.0))
    if candidate_score >= 5.0 and (neutral_score - candidate_score) <= 35.0:
        return candidate

    if candidate_score >= max(5.0, neutral_score * 0.7):
        return candidate

    return "neutral"


def _predict_probs_with_tta(model: Any, image_bgr: np.ndarray, input_shape: Tuple[Any, ...]) -> np.ndarray:
    """Predict probabilities with a light TTA pass to stabilize facial emotion output."""
    base_input = _prepare_image_model_input(image_bgr, input_shape)
    base_probs = model.predict(base_input, verbose=0)[0]

    if not FEN_USE_TTA:
        return base_probs

    flipped = cv2.flip(image_bgr, 1)
    flip_input = _prepare_image_model_input(flipped, input_shape)
    flip_probs = model.predict(flip_input, verbose=0)[0]

    return (base_probs + flip_probs) / 2.0


@lru_cache(maxsize=1)
def _load_model_artifacts() -> Optional[Dict[str, Any]]:
    model_path = _resolve_existing_model_path()
    if model_path is None:
        return None

    try:
        model = keras_load_model(model_path, compile=False)
    except Exception:
        model = tf_load_model(model_path, compile=False)
    meta_path = _resolve_meta_path_for_model(model_path)

    num_classes = _infer_num_classes(model)
    labels = _default_labels_for_size(num_classes)
    if meta_path is not None:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            extracted_labels = _extract_labels_from_meta(meta, num_classes)
            if extracted_labels:
                labels = extracted_labels
        except Exception:
            pass

    input_shape = tuple(model.input_shape or ())
    input_mode = "landmark"
    if len(input_shape) >= 4:
        input_mode = "image"

    if meta_path is None:
        meta_path = _create_generated_meta_if_missing(model_path, labels, input_mode)

    return {
        "model": model,
        "model_path": model_path,
        "meta_path": meta_path,
        "labels": labels,
        "input_mode": input_mode,
        "input_shape": input_shape,
    }


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("Could not decode image bytes")
    return image_bgr


def _detect_face_region_mediapipe(image_bgr: np.ndarray) -> Optional[Dict[str, int]]:
    """Detect the first face bounding box using MediaPipe Face Detection."""
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    height, width = image_bgr.shape[:2]

    with mp.solutions.face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.5,
    ) as detector:
        result = detector.process(image_rgb)

    if not result.detections:
        return None

    bbox = result.detections[0].location_data.relative_bounding_box
    x = max(0, int(bbox.xmin * width))
    y = max(0, int(bbox.ymin * height))
    box_width = int(bbox.width * width)
    box_height = int(bbox.height * height)

    if box_width <= 0 or box_height <= 0:
        return None

    x2 = min(width, x + box_width)
    y2 = min(height, y + box_height)
    x = min(x, x2 - 1)
    y = min(y, y2 - 1)

    return {
        "x": x,
        "y": y,
        "w": max(1, x2 - x),
        "h": max(1, y2 - y),
    }


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


def _estimate_smile_score(image_bgr: np.ndarray) -> float:
    """Estimate smile likelihood from face landmarks, returned as 0-100."""
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
    ) as face_mesh:
        result = face_mesh.process(image_rgb)

    if not result.multi_face_landmarks:
        return 0.0

    landmarks = result.multi_face_landmarks[0].landmark
    left_mouth = landmarks[61]
    right_mouth = landmarks[291]
    upper_lip = landmarks[13]
    lower_lip = landmarks[14]
    left_eye = landmarks[33]
    right_eye = landmarks[263]

    mouth_width = float(np.hypot(right_mouth.x - left_mouth.x, right_mouth.y - left_mouth.y))
    mouth_open = float(np.hypot(lower_lip.x - upper_lip.x, lower_lip.y - upper_lip.y))
    eye_width = float(np.hypot(right_eye.x - left_eye.x, right_eye.y - left_eye.y))
    if eye_width <= 1e-6:
        return 0.0

    smile_ratio = mouth_width / eye_width
    openness_ratio = mouth_open / eye_width

    # Wide smile mouth with controlled openness suggests happy over sad/fear.
    width_score = np.clip((smile_ratio - 0.35) / 0.25, 0.0, 1.0)
    openness_penalty = np.clip((openness_ratio - 0.18) / 0.22, 0.0, 1.0)
    smile_score = width_score * (1.0 - 0.55 * openness_penalty)
    return round(float(np.clip(smile_score, 0.0, 1.0) * 100.0), 4)


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
    class_counts = np.bincount(y, minlength=num_classes)
    max_count = int(np.max(class_counts)) if len(class_counts) else 1
    class_weight = {
        idx: float(max_count / max(1, int(count)))
        for idx, count in enumerate(class_counts)
    }

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
        class_weight=class_weight,
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
        "class_weight": class_weight,
        "final_train_loss": float(history.history["loss"][-1]),
        "final_train_accuracy": float(history.history["accuracy"][-1]),
        "final_val_loss": float(history.history["val_loss"][-1]),
        "final_val_accuracy": float(history.history["val_accuracy"][-1]),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _load_model_artifacts.cache_clear()

    return meta


def get_fen_model_info() -> Dict[str, Any]:
    ensure_dirs()
    model_path = _resolve_existing_model_path()
    if model_path is None:
        return {
            "ready": False,
            "model_path": str(MODEL_PATH.relative_to(BASE_DIR)),
            "metadata_source": "missing",
            "message": "FEN model not trained yet",
        }

    artifacts = _load_model_artifacts()
    if artifacts is None:
        return {
            "ready": True,
            "model_path": str(model_path.relative_to(BASE_DIR)),
            "input_mode": "image",
            "labels": DEFAULT_FEN_LABELS,
            "metadata_source": "default",
            "message": "FEN model found without metadata; using default label order",
        }

    meta_path = artifacts["meta_path"]
    if meta_path is None:
        return {
            "ready": True,
            "model_path": str(model_path.relative_to(BASE_DIR)),
            "input_mode": artifacts["input_mode"],
            "labels": artifacts["labels"],
            "metadata_source": "default",
            "message": "FEN model found without metadata; using default label order",
        }

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    metadata_source = "generated" if bool(meta.get("generated")) else "training"
    return {
        "ready": True,
        **meta,
        "model_path": str(model_path.relative_to(BASE_DIR)),
        "metadata_source": metadata_source,
    }


def predict_with_fen(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    artifacts = _load_model_artifacts()
    if artifacts is None:
        return None

    model = artifacts["model"]
    labels = list(artifacts["labels"])
    input_mode = artifacts["input_mode"]
    smile_score = 0.0

    image_bgr = decode_image_bytes(image_bytes)
    face_region = _detect_face_region_mediapipe(image_bgr)
    if face_region is not None:
        height, width = image_bgr.shape[:2]
        expanded = _expand_face_region(face_region, width, height, FACE_EXPAND_RATIO)
        x, y, w, h = expanded["x"], expanded["y"], expanded["w"], expanded["h"]
        image_bgr = image_bgr[y : y + h, x : x + w]

    if input_mode == "landmark":
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

        model_input = np.expand_dims(feat, axis=0)
        face_detected = True
        probs = model.predict(model_input, verbose=0)[0]
    else:
        input_shape = tuple(model.input_shape or ())
        face_detected = True
        probs = _predict_probs_with_tta(model, image_bgr, input_shape)
    best_idx = int(np.argmax(probs))
    scores = {label: 0.0 for label in EMOTION_LABELS}
    for idx, label in enumerate(labels):
        if idx < len(probs) and label in scores:
            scores[label] = round(float(probs[idx] * 100.0), 4)

    if input_mode == "image" and FEN_SMILE_CALIBRATION:
        smile_score = _estimate_smile_score(image_bgr)
        raw_happy = float(scores.get("happy", 0.0))
        raw_sad = float(scores.get("sad", 0.0))
        raw_fear = float(scores.get("fear", 0.0))
        raw_neutral = float(scores.get("neutral", 0.0))
        raw_top_score = float(max(scores.values())) if scores else 0.0
        happy_gap = raw_top_score - raw_happy
        strong_smile = smile_score >= max(FEN_SMILE_TRIGGER_MIN, FEN_SMILE_STRONG_MIN)
        should_promote_happy = (
            smile_score >= FEN_SMILE_TRIGGER_MIN
            and raw_happy >= FEN_BASE_HAPPY_MIN
            and (raw_top_score - raw_happy) <= FEN_HAPPY_PROMOTE_MARGIN
        )
        if (
            not should_promote_happy
            and strong_smile
            and raw_happy >= max(8.0, FEN_BASE_HAPPY_MIN * 0.5)
            and happy_gap <= FEN_SMILE_MAX_HAPPY_GAP
        ):
            should_promote_happy = True

        if should_promote_happy:
            boosted_happy = max(raw_happy, smile_score * FEN_SMILE_HAPPY_BOOST_SCALE)
            scores["happy"] = round(boosted_happy, 4)
            scores["sad"] = round(raw_sad * (FEN_SMILE_SAD_SUPPRESS if strong_smile else 0.82), 4)
            scores["fear"] = round(raw_fear * (0.84 if strong_smile else 0.88), 4)
            scores["neutral"] = round(raw_neutral * (0.9 if strong_smile else 0.95), 4)

        if FEN_POST_LOGIC_ENABLED and scores:
            top_emotion = max(scores, key=scores.get)
            top_score = float(scores.get(top_emotion, 0.0))
            happy_score = float(scores.get("happy", 0.0))

            # Rescue happy when smile evidence is strong and happy is close to the top class.
            if (
                smile_score >= FEN_HAPPY_RESCUE_SMILE_MIN
                and happy_score >= FEN_HAPPY_RESCUE_HAPPY_MIN
                and top_emotion in {"sad", "fear", "neutral"}
                and (top_score - happy_score) <= FEN_HAPPY_RESCUE_GAP_MAX
            ):
                scores["happy"] = round(top_score + 0.35, 4)
                scores["sad"] = round(float(scores.get("sad", 0.0)) * 0.9, 4)
                scores["fear"] = round(float(scores.get("fear", 0.0)) * 0.92, 4)

    model_emotion = labels[best_idx] if best_idx < len(labels) else "neutral"
    emotion = max(scores, key=scores.get) if scores else model_emotion
    if input_mode == "image" and smile_score >= FEN_SMILE_TRIGGER_MIN:
        adjusted_best = max(scores, key=scores.get)
        if adjusted_best == "happy":
            emotion = "happy"

    confidence = float(scores.get(emotion, probs[best_idx] * 100.0))

    return {
        "success": True,
        "face_detected": face_detected,
        "faces_detected": 1,
        "emotion": emotion,
        "model_emotion": model_emotion,
        "smile_score": smile_score,
        "confidence": round(max(0.0, min(100.0, confidence)), 4),
        "scores": scores,
        "provider": "fen",
    }
