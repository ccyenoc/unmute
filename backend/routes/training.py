"""
Training Routes
Model training and dataset management
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import numpy as np
import os
from pathlib import Path
import json

from services.hand_detector import HandDetector
from services.sign_language_model import SignLanguageModel

router = APIRouter()

hand_detector = HandDetector()
model = SignLanguageModel()

DATASET_DIR = "data/training_dataset"
Path(DATASET_DIR).mkdir(parents=True, exist_ok=True)

@router.post("/upload-training-data")
async def upload_training_data(
    sign_class: str,
    files: List[UploadFile] = File(...)
):
    """
    Upload training images for a specific sign class
    
    Args:
        sign_class: Sign letter (A-Z)
        files: List of image files
    """
    if not sign_class.isalpha() or len(sign_class) != 1:
        raise HTTPException(status_code=400, detail="Invalid sign class")
    
    sign_class = sign_class.upper()
    class_dir = Path(DATASET_DIR) / sign_class
    class_dir.mkdir(exist_ok=True)
    
    uploaded_count = 0
    
    for file in files:
        try:
            contents = await file.read()
            file_path = class_dir / file.filename
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            uploaded_count += 1
        except Exception as e:
            print(f"Error uploading {file.filename}: {e}")
    
    return {
        "success": True,
        "sign_class": sign_class,
        "uploaded_count": uploaded_count,
        "total_files": len(files)
    }

@router.get("/dataset-info")
def get_dataset_info():
    """Get information about the training dataset"""
    dataset_dir = Path(DATASET_DIR)
    
    class_info = {}
    total_images = 0
    
    if dataset_dir.exists():
        for class_dir in dataset_dir.iterdir():
            if class_dir.is_dir():
                images = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
                class_info[class_dir.name] = len(images)
                total_images += len(images)
    
    return {
        "dataset_path": str(dataset_dir),
        "total_images": total_images,
        "classes": class_info,
        "ready_to_train": total_images > 0
    }

@router.post("/train-model")
async def train_model(
    epochs: int = 50,
    batch_size: int = 32,
    validation_split: float = 0.2
):
    """
    Train the model on uploaded dataset
    
    Args:
        epochs: Number of training epochs
        batch_size: Batch size for training
        validation_split: Fraction of data for validation
    """
    try:
        # Load images and extract features
        dataset_dir = Path(DATASET_DIR)
        
        features_list = []
        labels_list = []
        
        for class_idx, class_dir in enumerate(sorted(dataset_dir.iterdir())):
            if not class_dir.is_dir():
                continue
            
            print(f"Processing class {class_dir.name}...")
            
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
            
            for image_file in image_files:
                try:
                    import cv2
                    from PIL import Image
                    
                    # Load image
                    img = cv2.imread(str(image_file))
                    if img is None:
                        continue
                    
                    # Detect hands and extract features
                    detection = hand_detector.detect_hands(img)
                    
                    if detection["success"] and len(detection["landmarks"]) > 0:
                        features = hand_detector.extract_features(detection["landmarks"][0])
                        features_list.append(features)
                        
                        # Create one-hot label
                        label = np.zeros(26)
                        label[ord(class_dir.name) - ord('A')] = 1
                        labels_list.append(label)
                        
                except Exception as e:
                    print(f"Error processing {image_file}: {e}")
                    continue
        
        if len(features_list) == 0:
            raise HTTPException(status_code=400, detail="No training data found or no hands detected")
        
        # Convert to numpy arrays
        X = np.array(features_list)
        y = np.array(labels_list)
        
        # Split data
        num_samples = len(X)
        split_idx = int(num_samples * (1 - validation_split))
        
        indices = np.random.permutation(num_samples)
        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]
        
        X_train, X_val = X[train_indices], X[val_indices]
        y_train, y_val = y[train_indices], y[val_indices]
        
        print(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        
        # Train model
        history = model.train(X_train, y_train, X_val, y_val, epochs=epochs, batch_size=batch_size)
        
        return {
            "success": True,
            "message": "Model trained successfully",
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "epochs": epochs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-incremental")
async def train_incremental(
    sign_class: str,
    files: List[UploadFile] = File(...),
    epochs: int = 10
):
    """
    Incrementally train model with new samples for a specific class
    
    Args:
        sign_class: Sign letter to train for
        files: Training images
        epochs: Number of epochs
    """
    try:
        # Save uploaded files temporarily
        temp_dir = Path(f"data/temp_{sign_class}")
        temp_dir.mkdir(exist_ok=True)
        
        for file in files:
            contents = await file.read()
            with open(temp_dir / file.filename, "wb") as f:
                f.write(contents)
        
        # Extract features
        features_list = []
        labels_list = []
        
        import cv2
        
        for image_file in temp_dir.glob("*.jpg"):
            img = cv2.imread(str(image_file))
            if img is not None:
                detection = hand_detector.detect_hands(img)
                if detection["success"]:
                    features = hand_detector.extract_features(detection["landmarks"][0])
                    features_list.append(features)
                    
                    label = np.zeros(26)
                    label[ord(sign_class.upper()) - ord('A')] = 1
                    labels_list.append(label)
        
        if len(features_list) == 0:
            raise HTTPException(status_code=400, detail="No hands detected in images")
        
        X = np.array(features_list)
        y = np.array(labels_list)
        
        # Train with small learning rate for incremental learning
        model.model.fit(X, y, epochs=epochs, batch_size=8, verbose=1)
        model.save_model()
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        return {
            "success": True,
            "message": f"Model updated with {len(X)} new samples for class {sign_class}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-summary")
def get_model_summary():
    """Get model architecture summary"""
    return {
        "summary": model.get_model_summary()
    }
