# Backend Quick Reference Guide 📋

Quick copy-paste examples for common tasks.

## Installation & Setup

### 1. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Run Server

```bash
python app.py
# Open http://localhost:8000/docs
```

### 3. Test Setup

```bash
python scripts/test_setup.py
```

---

## Data Collection

### Collect Data via Webcam

```bash
python scripts/collect_data.py
# Select option 1 for single sign or 2 for all signs
# Press 'c' to capture, 'q' to quit
```

### Upload Data via API

```bash
# Upload images for sign 'A'
curl -X POST "http://localhost:8000/api/training/upload-training-data?sign_class=A" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"

# Check dataset
curl "http://localhost:8000/api/training/dataset-info"
```

---

## Model Training

### Train Model (Script - Recommended)

```bash
# Basic training (50 epochs)
python scripts/train_model.py

# Custom parameters
python scripts/train_model.py --epochs 100 --batch-size 16

# Evaluate only
python scripts/train_model.py --evaluate
```

### Train Model (API)

```bash
# Start training
curl -X POST "http://localhost:8000/api/training/train-model?epochs=50&batch_size=32"

# Train with incremental learning
curl -X POST "http://localhost:8000/api/training/train-incremental?sign_class=A&epochs=10" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"
```

---

## Real-Time Detection

### Emotion Predict API (Base64 or File)

```bash
# Base64 frame payload
curl -X POST "http://localhost:8000/api/emotion/predict" \
  -H "Content-Type: application/json" \
  -d '{"image":"data:image/jpeg;base64,/9j/..."}'
```

```bash
# Uploaded image file
curl -X POST "http://localhost:8000/api/emotion/predict" \
  -F "file=@face.jpg"
```

Response fields: `emotion`, `confidence` (0-1), `face_detected`.

### Test Detection (Image)

```bash
# Upload image for detection
curl -X POST "http://localhost:8000/api/detection/detect-image" \
  -F "file=@test_image.jpg" \
  -o result.json

# View result
cat result.json | jq
```

### Test Detection (Frame)

```bash
# Optimized for streaming
curl -X POST "http://localhost:8000/api/detection/detect-frame" \
  -F "file=@frame.jpg"
```

### Get Model Info

```bash
curl "http://localhost:8000/api/detection/model-info"
```

---

## History & Stats

### Get Detection History

```bash
# Get last 50 predictions
curl "http://localhost:8000/api/history/"

# Get last 100
curl "http://localhost:8000/api/history/?limit=100"
```

### Get Statistics

```bash
curl "http://localhost:8000/api/history/stats" | jq
```

### Add to History

```bash
curl -X POST "http://localhost:8000/api/history/add" \
  -H "Content-Type: application/json" \
  -d '{
    "prediction": "A",
    "confidence": 0.95,
    "image_path": "/path/to/image.jpg"
  }'
```

### Export History

```bash
# Export as JSON
curl "http://localhost:8000/api/history/export?format=json" > history.json

# Export as CSV
curl "http://localhost:8000/api/history/export?format=csv" > history.csv
```

---

## Python Usage (Direct)

### Use Hand Detector

```python
from services.hand_detector import HandDetector
import cv2

# Initialize
detector = HandDetector(max_hands=2, min_confidence=0.5)

# Load image
img = cv2.imread("path/to/image.jpg")

# Detect hands
results = detector.detect_hands(img)

if results["success"]:
    print(f"Hands detected: {results['num_hands_detected']}")
    print(f"Handedness: {results['handedness']}")
    
    for i, landmarks in enumerate(results["landmarks"]):
        features = detector.extract_features(landmarks)
        print(f"Hand {i} features shape: {features.shape}")
    
    # Get annotated image
    annotated = results["image"]
    cv2.imshow("Result", annotated)
    cv2.waitKey(0)

detector.close()
```

### Use Sign Language Model

```python
from services.sign_language_model import SignLanguageModel
import numpy as np

# Initialize
model = SignLanguageModel()

# Predict
features = np.random.randn(63)  # Or from hand detector
result = model.predict(features, confidence_threshold=0.6)

print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.2f}")
```

### Train Model Programmatically

```python
from services.sign_language_model import SignLanguageModel
import numpy as np

model = SignLanguageModel()

# Create dummy data
X_train = np.random.randn(100, 63)  # 100 samples, 63 features
y_train = np.eye(26)[np.random.randint(0, 26, 100)]  # One-hot encoded

X_val = np.random.randn(20, 63)
y_val = np.eye(26)[np.random.randint(0, 26, 20)]

# Train
history = model.train(X_train, y_train, X_val, y_val, epochs=50)
```

---

## Docker

### Build & Run

```bash
# Build image
docker build -t sign-language-backend .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  sign-language-backend
```

### Using Docker Compose

```bash
# Start
docker-compose up

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

---

## Troubleshooting Commands

### Check Dependencies

```bash
python scripts/test_setup.py
```

### View API Docs

Open in browser:
```
http://localhost:8000/docs
```

### Clear History

```bash
curl -X DELETE "http://localhost:8000/api/history/clear"
```

### View Available Endpoints

```bash
curl http://localhost:8000/docs -s | grep '"url"'
```

### Check Model Summary

```bash
curl "http://localhost:8000/api/training/model-summary"
```

---

## Development Tips

### Using Python Interactive Shell

```bash
python

>>> from services.hand_detector import HandDetector
>>> detector = HandDetector()
>>> # Test code here
```

### Debug Prints

```python
# In your code:
print(f"DEBUG: variable = {variable}")  # F-string
print("DEBUG:", variable)                # Comma separator
import pdb; pdb.set_trace()             # Debugger
```

### Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Connection refused` | Server not running: `python app.py` |
| `No hands detected` | Better lighting, show hand fully |
| `Out of memory` | Reduce batch size or dataset |
| `Port already in use` | Kill existing: `lsof -ti:8000 \| xargs kill -9` |

---

## Performance Optimization

### Reduce Model Size

```python
# Quantization (in training script)
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model("models/")
tflite_model = converter.convert()

# Save smaller model
with open("models/model_lite.tflite", "wb") as f:
    f.write(tflite_model)
```

### Speed Up Training

```bash
# Use smaller dataset
python scripts/train_model.py --batch-size 64 --epochs 10

# Or use GPU (if available)
# TensorFlow will auto-detect GPU
```

### Optimize Inference

```python
# Use batch predictions instead of single
model.predict(batch_features)  # Instead of looping
```

---

## Environment Variables

```bash
# .env file
PORT=8000
DEBUG=True
ENV=development
MODEL_PATH=models/sign_language_model.h5
MAX_HANDS=2
MIN_DETECTION_CONFIDENCE=0.5
```

---

## Useful Commands

```bash
# List all routes
grep -r "@router" routes/

# Count images in dataset
find data/training_dataset -name "*.jpg" | wc -l

# Check API response times
time curl http://localhost:8000/api/detection/model-info

# Monitor server resource usage
top -p $(pgrep -f "uvicorn")

# Kill server
lsof -ti:8000 | xargs kill -9
```

---

## Production Checklist

- [ ] Train model with sufficient data
- [ ] Test all API endpoints
- [ ] Update `.env` for production
- [ ] Enable HTTPS
- [ ] Add authentication
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Test error handling
- [ ] Document API changes
- [ ] Set up backups

---

## Resources

- **MediaPipe Docs**: https://developers.google.com/mediapipe
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **TensorFlow Guide**: https://www.tensorflow.org/guide
- **OpenCV Docs**: https://docs.opencv.org/

---

**Pro Tips:**
- 🔍 Use `/docs` for interactive API testing
- 📊 Check stats to monitor model performance  
- 💾 Regularly backup trained models
- 🧪 Use `test_setup.py` before troubleshooting
- 📈 Collect more diverse data for better accuracy

Happy hacking! 🚀
