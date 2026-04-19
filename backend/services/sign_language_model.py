"""
Sign Language Model Handler
Manages the neural network model for sign language classification
"""
import numpy as np
import tensorflow as tf
from typing import Dict, Tuple, List
import os
from pathlib import Path

class SignLanguageModel:
    """
    Neural network model for classifying hand gestures into sign language letters/words
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the sign language model
        
        Args:
            model_path: Path to saved model. If None, creates a new model.
        """
        self.model = None
        self.model_path = model_path or "models/sign_language_model.h5"
        self.classes = self._get_classes()
        
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            print(f"Model not found at {self.model_path}. Train a model first.")
            self.create_new_model()
    
    def _get_classes(self) -> List[str]:
        """Get list of sign language classes (letters A-Z)"""
        return [chr(i) for i in range(65, 91)]  # A-Z
    
    def create_new_model(self, input_dim: int = 63):
        """
        Create a new neural network model
        
        Args:
            input_dim: Input dimension (21 landmarks * 3 coordinates)
        """
        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_dim=input_dim),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.1),
            
            tf.keras.layers.Dense(26, activation='softmax')  # 26 letters
        ])
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print("New model created!")
    
    def load_model(self):
        """Load pre-trained model"""
        try:
            self.model = tf.keras.models.load_model(self.model_path)
            print(f"Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.create_new_model()
    
    def save_model(self):
        """Save trained model"""
        if self.model:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            print(f"Model saved to {self.model_path}")
    
    def predict(self, features: np.ndarray, confidence_threshold: float = 0.5) -> Dict:
        """
        Predict sign language class from hand features
        
        Args:
            features: Feature vector from hand landmarks (63D)
            confidence_threshold: Minimum confidence for prediction
            
        Returns:
            Dict with prediction, confidence, and all class probabilities
        """
        if self.model is None:
            return {
                "success": False,
                "error": "Model not loaded"
            }
        
        # Reshape for model input
        features = features.reshape(1, -1)
        
        # Get predictions
        predictions = self.model.predict(features, verbose=0)[0]
        max_confidence = np.max(predictions)
        predicted_class_idx = np.argmax(predictions)
        predicted_class = self.classes[predicted_class_idx]
        
        # Check confidence threshold
        if max_confidence < confidence_threshold:
            return {
                "success": True,
                "prediction": "UNCERTAIN",
                "confidence": float(max_confidence),
                "message": f"Confidence below threshold ({confidence_threshold})",
                "all_predictions": {
                    self.classes[i]: float(predictions[i])
                    for i in range(len(self.classes))
                }
            }
        
        return {
            "success": True,
            "prediction": predicted_class,
            "confidence": float(max_confidence),
            "all_predictions": {
                self.classes[i]: float(predictions[i])
                for i in range(len(self.classes))
            }
        }
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 50, batch_size: int = 32):
        """
        Train the model
        
        Args:
            X_train: Training features
            y_train: Training labels (one-hot encoded)
            X_val: Validation features
            y_val: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        if self.model is None:
            self.create_new_model(X_train.shape[1])
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )
        
        self.save_model()
        return history
    
    def get_model_summary(self) -> str:
        """Get model architecture summary"""
        if self.model:
            import io
            stream = io.StringIO()
            self.model.summary(print_fn=lambda x: stream.write(x + '\n'))
            return stream.getvalue()
        return "No model loaded"
