"""
Training Routes
Model training and dataset management
"""

from __future__ import annotations

from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data" / "training_dataset"


@router.post("/upload-training-data")
async def upload_training_data(
	sign_class: str = Query(..., min_length=1, max_length=32),
	files: List[UploadFile] = File(...),
):
	label = sign_class.strip().upper()
	if not label.isalnum():
		raise HTTPException(status_code=422, detail="sign_class must be alphanumeric")

	class_dir = DATASET_DIR / label
	class_dir.mkdir(parents=True, exist_ok=True)

	saved = []
	for file in files:
		if not file.content_type or not file.content_type.startswith("image/"):
			continue
		content = await file.read()
		filename = f"{label}_{uuid4().hex[:8]}.jpg"
		path = class_dir / filename
		path.write_bytes(content)
		saved.append(str(path.relative_to(BASE_DIR)))

	if not saved:
		raise HTTPException(status_code=400, detail="No valid image files uploaded")

	return {
		"success": True,
		"sign_class": label,
		"saved_count": len(saved),
		"files": saved,
	}


@router.get("/dataset-info")
def dataset_info():
	DATASET_DIR.mkdir(parents=True, exist_ok=True)
	stats = {}
	total = 0

	for entry in sorted(DATASET_DIR.iterdir()):
		if not entry.is_dir():
			continue
		count = len([item for item in entry.glob("*.jpg") if item.is_file()])
		stats[entry.name] = count
		total += count

	return {
		"success": True,
		"dataset_dir": str(DATASET_DIR.relative_to(BASE_DIR)),
		"total_images": total,
		"classes": stats,
	}


@router.post("/train-model")
def train_model(
	epochs: int = Query(20, ge=1, le=1000),
	batch_size: int = Query(32, ge=1, le=2048),
):
	info = dataset_info()
	if info["total_images"] == 0:
		raise HTTPException(status_code=400, detail="Dataset is empty. Upload training data first.")

	return {
		"success": True,
		"status": "queued",
		"epochs": epochs,
		"batch_size": batch_size,
		"message": "Training pipeline scaffold ready. Connect your TensorFlow training logic here.",
		"dataset": info,
	}
