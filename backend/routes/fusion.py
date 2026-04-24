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
    expected = [item.lower().strip() for item in (payload.expected_emotions or []) if item]

    status = "aligned"
    message = "Emotion context is aligned with sign interpretation."

    if payload.confidence is not None and payload.confidence < payload.confidence_threshold:
        status = "low_confidence"
        message = "Emotion confidence is low. Ask user to retry or improve camera angle."
    elif expected and normalized_emotion not in expected:
        status = "mismatch"
        message = "Emotion may not match expected context. Consider clarifying intent."

    return {
        "sign": payload.sign,
        "emotion": normalized_emotion,
        "confidence": payload.confidence,
        "status": status,
        "message": message,
        "expected_emotions": expected,
    }
