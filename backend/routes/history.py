"""
History Routes
Manage translation history
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "translation_history.json"


class HistoryRecord(BaseModel):
	prediction: str = Field(..., min_length=1)
	confidence: float = Field(..., ge=0)
	timestamp: str | None = None


def _read_history() -> List[dict]:
	DATA_DIR.mkdir(parents=True, exist_ok=True)
	if not HISTORY_FILE.exists():
		return []

	try:
		payload = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
		return payload if isinstance(payload, list) else []
	except json.JSONDecodeError:
		return []


def _write_history(records: List[dict]) -> None:
	DATA_DIR.mkdir(parents=True, exist_ok=True)
	HISTORY_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")


@router.get("/")
def get_history(limit: int = Query(50, ge=1, le=500)):
	records = _read_history()
	return {
		"success": True,
		"count": min(len(records), limit),
		"records": records[:limit],
	}


@router.post("/add")
def add_history(item: HistoryRecord):
	records = _read_history()
	record = item.model_dump()
	if not record.get("timestamp"):
		record["timestamp"] = datetime.now(timezone.utc).isoformat()

	records.insert(0, record)
	_write_history(records[:500])

	return {
		"success": True,
		"record": record,
	}


@router.get("/stats")
def history_stats():
	records = _read_history()
	return {
		"success": True,
		"total_records": len(records),
		"last_prediction": records[0]["prediction"] if records else None,
	}


@router.delete("/")
def clear_history():
	try:
		_write_history([])
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Failed to clear history: {exc}") from exc

	return {
		"success": True,
		"message": "History cleared",
	}
