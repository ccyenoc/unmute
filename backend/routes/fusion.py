"""
Fusion Routes
Combines sign-language output with facial emotion to provide interaction context.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class FusionRequest(BaseModel):
    sign: str = Field(..., description="Detected sign label or translated text")
    emotion: str = Field(..., description="Dominant facial emotion")
    confidence: Optional[float] = Field(default=None, description="Emotion confidence percentage")
    expected_emotions: Optional[List[str]] = Field(
        default=None,
        description="Optional list of expected emotions for this sign/phrase",
    )
    confidence_threshold: float = Field(default=50.0, description="Minimum confidence for reliable emotion")


@router.post("/interpret")
def interpret_fusion(payload: FusionRequest):
    normalized_emotion = payload.emotion.lower().strip()

    status = "interpreted"
    message = f"User likely means: '{payload.sign}'"

    # If emotion confidence is low → warn but still follow sign
    if payload.confidence is not None and payload.confidence < payload.confidence_threshold:
        status = "low_confidence"
        message += " (emotion confidence is low)"

    # If emotion contradicts sign → add context instead of rejecting
    elif payload.expected_emotions:
        expected = [e.lower().strip() for e in payload.expected_emotions]
        if normalized_emotion not in expected:
            status = "context_adjusted"
            message += f" (emotion '{normalized_emotion}' may indicate different tone)"

    return {
        "sign": payload.sign,
        "emotion": normalized_emotion,
        "confidence": payload.confidence,
        "status": status,
        "message": message,
    }