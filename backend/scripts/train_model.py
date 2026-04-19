"""
Model Training Utility Script
Train the sign language model locally
"""

import sys
from pathlib import Path
import numpy as np
import cv2

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.hand_detector import HandDetector
from services.sign_language_model import SignLanguageModel

class ModelTrainer:
    """Train sign language model on collected dataset"""
    
    def __init__(self, dataset_dir: str = "data/training_dataset"):
        self.dataset_dir = Path(dataset_dir)
        self.hand_detector = HandDetector()
        self.model = SignLanguageModel()
    
    def load_dataset(self, validation_split: float = 0.2) -> tuple:
        """
        Load training dataset from files
        
        Returns:
            Tuple of (X_train, y_train, X_val, y_val)
        """
        print("📂 Loading dataset...")
        
        features_list = []
        labels_list = []
        class_distribution = {}
        
        for class_dir in sorted(self.dataset_dir.iterdir()):
            if not class_dir.is_dir():
                continue
            
            class_name = class_dir.name
            class_idx = ord(class_name) - ord('A')
            
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
            loaded_count = 0
            
            print(f"Processing class '{class_name}': ", end="", flush=True)
            
            for image_file in image_files:
                try:
                    # Load image
                    img = cv2.imread(str(image_file))
                    if img is None:
                        continue
                    
                    # Detect hands
                    detection = self.hand_detector.detect_hands(img)
                    
                    if detection["success"] and len(detection["landmarks"]) > 0:
                        # Extract features
                        features = self.hand_detector.extract_features(detection["landmarks"][0])
                        features_list.append(features)
                        
                        # Create one-hot label
                        label = np.zeros(26)
                        label[class_idx] = 1
                        labels_list.append(label)
                        
                        loaded_count += 1
                        
                except Exception as e:
                    print(f".", end="", flush=True)
                    continue
            
            class_distribution[class_name] = loaded_count
            print(f" ✓ {loaded_count} samples")
        
        if len(features_list) == 0:
            raise ValueError("No valid training data found!")
        
        # Convert to numpy arrays
        X = np.array(features_list)
        y = np.array(labels_list)
        
        # Shuffle
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        # Split into train/validation
        split_idx = int(len(X) * (1 - validation_split))
        X_train = X[:split_idx]
        y_train = y[:split_idx]
        X_val = X[split_idx:]
        y_val = y[split_idx:]
        
        print("\n📊 Dataset Statistics:")
        print("-" * 40)
        for class_name, count in sorted(class_distribution.items()):
            bar = "█" * (count // 5)
            print(f"{class_name}: {count:3d} {bar}")
        print("-" * 40)
        print(f"Total samples: {len(X)}")
        print(f"Training set: {len(X_train)} ({validation_split*100:.0f}%)")
        print(f"Validation set: {len(X_val)} ({(1-validation_split)*100:.0f}%)")
        
        return X_train, y_train, X_val, y_val
    
    def train(self, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.2):
        """
        Train the model
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size
            validation_split: Validation data fraction
        """
        try:
            # Load dataset
            X_train, y_train, X_val, y_val = self.load_dataset(validation_split)
            
            print(f"\n🚀 Starting training...")
            print(f"Epochs: {epochs}, Batch size: {batch_size}")
            print("-" * 40)
            
            # Train model
            history = self.model.train(
                X_train, y_train,
                X_val, y_val,
                epochs=epochs,
                batch_size=batch_size
            )
            
            print("\n✅ Training complete!")
            print(f"Model saved to: {self.model.model_path}")
            
            return history
            
        except Exception as e:
            print(f"❌ Error during training: {e}")
            return None
    
    def evaluate_model(self) -> dict:
        """
        Evaluate model on validation set
        
        Returns:
            Evaluation metrics
        """
        print("📈 Evaluating model...")
        
        try:
            _, _, X_val, y_val = self.load_dataset()
            
            # Evaluate
            loss, accuracy = self.model.model.evaluate(X_val, y_val, verbose=0)
            
            metrics = {
                "loss": float(loss),
                "accuracy": float(accuracy)
            }
            
            print(f"Validation Loss: {loss:.4f}")
            print(f"Validation Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error during evaluation: {e}")
            return None

def main():
    """Main training script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train sign language model")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--validation-split", type=float, default=0.2, help="Validation split")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate trained model")
    parser.add_argument("--dataset-dir", type=str, default="data/training_dataset", help="Dataset directory")
    
    args = parser.parse_args()
    
    print("🎯 Sign Language Model Trainer")
    print("=" * 50)
    
    trainer = ModelTrainer(args.dataset_dir)
    
    if args.evaluate:
        trainer.evaluate_model()
    else:
        trainer.train(
            epochs=args.epochs,
            batch_size=args.batch_size,
            validation_split=args.validation_split
        )

if __name__ == "__main__":
    main()
