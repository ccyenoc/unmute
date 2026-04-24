"""
History Routes
Manage translation history
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_history():
    return {"history": []}