"""
Real-time Sign Language Prediction
"""


from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def training_status():
    return {"status": "training endpoint ready"}
