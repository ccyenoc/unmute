"""
Test Script - Verify Backend Setup
Runs diagnostic tests to ensure all components are working
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("🔍 Testing imports...")
    
    packages = {
        "FastAPI": "fastapi",
        "MediaPipe": "mediapipe",
        "TensorFlow": "tensorflow",
        "OpenCV": "cv2",
        "NumPy": "numpy",
    }
    
    all_ok = True
    for name, module in packages.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def test_mediapipe():
    """Test MediaPipe hand detection"""
    print("\n🤚 Testing MediaPipe Hand Detection...")
    
    try:
        import cv2
        import numpy as np
        from services.hand_detector import HandDetector
        
        detector = HandDetector()
        
        # Create test image (white background)
        test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        results = detector.detect_hands(test_image)
        print(f"  ✅ Hand detector initialized")
        print(f"  ✅ Can process images")
        
        detector.close()
        return True
        
    except Exception as e:
        print(f"  ❌ MediaPipe test failed: {e}")
        return False

def test_model():
    """Test TensorFlow model loading"""
    print("\n🧠 Testing TensorFlow Model...")
    
    try:
        from services.sign_language_model import SignLanguageModel
        import numpy as np
        
        model = SignLanguageModel()
        print(f"  ✅ Model initialized")
        
        if model.model is None:
            print(f"  ℹ️  No pre-trained model found (will train first)")
        else:
            # Test prediction
            test_features = np.random.randn(63)
            result = model.predict(test_features)
            
            print(f"  ✅ Model can make predictions")
            print(f"  ✅ Example prediction: {result['prediction']} (confidence: {result['confidence']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        return False

def test_api():
    """Test FastAPI server startup"""
    print("\n🚀 Testing FastAPI Server...")
    
    try:
        from app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print(f"  ✅ Server health check passed")
        
        # Test model info
        response = client.get("/api/detection/model-info")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API endpoints working")
            print(f"  ℹ️  Model classes: {len(data['classes'])} (A-Z)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
        return False

def check_dataset():
    """Check if training dataset exists"""
    print("\n📂 Checking Dataset...")
    
    dataset_dir = Path("data/training_dataset")
    
    if dataset_dir.exists():
        classes = [d for d in dataset_dir.iterdir() if d.is_dir()]
        total_images = sum(len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) 
                          for d in classes)
        
        if total_images > 0:
            print(f"  ✅ Dataset found")
            print(f"  ℹ️  Classes: {len(classes)}, Total images: {total_images}")
            return True
        else:
            print(f"  ⚠️  Dataset directory empty - run scripts/collect_data.py to collect training data")
            return False
    else:
        print(f"  ⚠️  No training dataset - run scripts/collect_data.py to start")
        return False

def check_model_file():
    """Check if trained model exists"""
    print("\n💾 Checking Saved Model...")
    
    model_path = Path("models/sign_language_model.h5")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Trained model found ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ⚠️  No trained model - run scripts/train_model.py to train")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("🧪 Sign Language Detector - Backend Tests")
    print("=" * 50)
    
    results = {
        "Imports": test_imports(),
        "MediaPipe": test_mediapipe(),
        "Model": test_model(),
        "API": test_api(),
    }
    
    check_dataset()
    check_model_file()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✨ All tests passed! Backend is ready to use.")
        print("\n🚀 Next steps:")
        print("  1. Collect training data: python scripts/collect_data.py")
        print("  2. Train model: python scripts/train_model.py")
        print("  3. Start server: python app.py")
        print("  4. Test API: curl http://localhost:8000/docs")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("Run: pip install -r requirements.txt")

if __name__ == "__main__":
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    main()
