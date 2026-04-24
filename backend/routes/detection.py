"""
Detection Routes
Real-time sign language detection from video/images
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.facial_emotion_service import predict_emotion_pipeline

router = APIRouter()


@router.get("/health")
def detection_health() -> dict:
	return {
		"status": "ok",
		"service": "detection",
	}


@router.post("/detect-image")
async def detect_image(file: UploadFile = File(...)):
	if not file.content_type or not file.content_type.startswith("image/"):
		raise HTTPException(status_code=400, detail="Uploaded file must be an image")

	image_bytes = await file.read()
	try:
		emotion_result = predict_emotion_pipeline(image_bytes)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Detection failed: {exc}") from exc

	return {
		"success": True,
		"num_hands_detected": 0,
		"predictions": [],
		"handedness": [],
		"annotated_image": None,
		"emotion": {
			"value": emotion_result.get("emotion"),
			"confidence": emotion_result.get("confidence"),
			"provider": emotion_result.get("provider"),
			"face_detected": emotion_result.get("face_detected"),
		},
		"note": "Sign model pipeline is not wired yet; this endpoint currently returns emotion-only fallback.",
	}


@router.post("/detect-frame")
async def detect_frame(file: UploadFile = File(...)):
	result = await detect_image(file)
	emotion_value = result["emotion"]["value"]
	emotion_confidence = result["emotion"]["confidence"]
	# Smaller payload for streaming clients
	return {
		"success": result["success"],
		"prediction": None,
		"confidence": None,
		"emotion": emotion_value,
		"emotion_confidence": emotion_confidence,
		"status": "mismatch" if emotion_value in {"angry", "fear", "sad"} else "aligned",
	}


@router.get("/model-info")
def detection_model_info() -> dict:
	return {
		"task": "sign_language_detection",
		"status": "scaffold",
		"classes": [],
		"message": "Sign language model is not connected yet.",
	}