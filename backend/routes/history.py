"""
History Routes
Manage translation history
"""
from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

router = APIRouter()

HISTORY_FILE = "data/translation_history.json"

def load_history() -> List[dict]:
    """Load translation history from file"""
    Path(HISTORY_FILE).parent.mkdir(exist_ok=True)
    if Path(HISTORY_FILE).exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history: List[dict]):
    """Save translation history to file"""
    Path(HISTORY_FILE).parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@router.get("/")
def get_history(limit: int = 50):
    """
    Get recent translation history
    
    Args:
        limit: Maximum number of entries to return
    """
    history = load_history()
    return {
        "total": len(history),
        "entries": history[-limit:]
    }

@router.post("/add")
def add_to_history(
    prediction: str,
    confidence: float,
    image_path: Optional[str] = None
):
    """
    Add a translation to history
    
    Args:
        prediction: The detected sign (e.g., 'A', 'B', etc.)
        confidence: Confidence score of the prediction
        image_path: Optional path to the original image
    """
    history = load_history()
    
    entry = {
        "id": len(history) + 1,
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction,
        "confidence": confidence,
        "image_path": image_path
    }
    
    history.append(entry)
    save_history(history)
    
    return {
        "success": True,
        "entry": entry
    }

@router.delete("/clear")
def clear_history():
    """Clear all translation history"""
    save_history([])
    return {
        "success": True,
        "message": "History cleared"
    }

@router.get("/stats")
def get_stats():
    """Get statistics about translation history"""
    history = load_history()
    
    if not history:
        return {
            "total_predictions": 0,
            "unique_signs": 0,
            "average_confidence": 0
        }
    
    # Count occurrences
    predictions = [entry["prediction"] for entry in history]
    unique_signs = set(predictions)
    avg_confidence = sum(entry["confidence"] for entry in history) / len(history)
    
    # Count by sign
    sign_counts = {}
    for prediction in predictions:
        sign_counts[prediction] = sign_counts.get(prediction, 0) + 1
    
    return {
        "total_predictions": len(history),
        "unique_signs": len(unique_signs),
        "average_confidence": round(avg_confidence, 3),
        "sign_counts": sign_counts,
        "most_common": max(sign_counts, key=sign_counts.get) if sign_counts else None
    }

@router.get("/export")
def export_history(format: str = "json"):
    """
    Export history in various formats
    
    Args:
        format: Export format (json, csv)
    """
    history = load_history()
    
    if format == "json":
        return history
    elif format == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        if history:
            writer = csv.DictWriter(output, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
        
        return {"csv": output.getvalue()}
    else:
        return {"error": "Unsupported format"}
