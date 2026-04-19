# Backend Setup Guide 🚀

Complete step-by-step guide to set up the sign language detector backend.

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Data Collection](#data-collection)
4. [Model Training](#model-training)
5. [API Testing](#api-testing)
6. [Docker Deployment](#docker-deployment)

---

## Installation

### Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Webcam (for data collection)

### Step 1: Setup Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**Expected installation time: 5-10 minutes** (depending on internet speed and TensorFlow)

---

## Quick Start

### Run the Backend Server

```bash
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Access the API

**API Documentation** (Interactive Swagger UI):
```
http://localhost:8000/docs
```

**Health Check**:
```bash
curl http://localhost:8000/health
```

### Stop the Server

Press `CTRL+C` in the terminal.

---

## Data Collection

### Option 1: Collect Using Webcam Script

```bash
# Navigate to backend directory
cd backend

# Run data collection script
python scripts/collect_data.py
```

**Instructions**:
1. Select option `1` to collect single sign or `2` for all signs
2. Allow camera access when prompted
3. Position your hand in the green rectangle
4. Press `c` to capture (only saves if hand is detected)
5. Press `q` to quit

**Tips for best results**:
- Collect in well-lit environment
- Use various angles and distances
- Aim for 50-100 images per sign class
- Backgrounds can vary (more natural for model)

### Option 2: Upload Using API

```bash
# Upload images for sign 'A'
curl -X POST "http://localhost:8000/api/training/upload-training-data?sign_class=A" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

### View Dataset Progress

```bash
python scripts/collect_data.py
# Select option 3: View dataset statistics
```

Or via API:
```bash
curl "http://localhost:8000/api/training/dataset-info"
```

---

## Model Training

### Option 1: Train Using Script (Recommended)

```bash
# Train model with default settings (50 epochs)
python scripts/train_model.py

# With custom parameters
python scripts/train_model.py --epochs 100 --batch-size 16

# Evaluate trained model
python scripts/train_model.py --evaluate
```

**Expected training time**: 5-15 minutes (depends on dataset size and computer)

### Option 2: Train Using API

```bash
# Check dataset first
curl "http://localhost:8000/api/training/dataset-info"

# Train model
curl -X POST "http://localhost:8000/api/training/train-model?epochs=50&batch_size=32"
```

### View Training Progress

The script will show:
- Images loaded per class
- Training/validation split
- Real-time accuracy during training
- Final model accuracy

---

## API Testing

### Test Detection (with pre-trained model)

```bash
# Test with a local image
curl -X POST "http://localhost:8000/api/detection/detect-image" \
  -F "file=@path/to/your/image.jpg"

# Response:
{
  "success": true,
  "num_hands_detected": 1,
  "predictions": [
    {
      "prediction": "A",
      "confidence": 0.95,
      "all_predictions": {
        "A": 0.95,
        "B": 0.03,
        ...
      }
    }
  ],
  "handedness": ["Right"],
  "annotated_image": "base64_encoded..."
}
```

### Get Model Information

```bash
curl "http://localhost:8000/api/detection/model-info"

# Response:
{
  "model_loaded": true,
  "num_classes": 26,
  "classes": ["A", "B", "C", ...],
  "model_path": "models/sign_language_model.h5"
}
```

### View Translation History

```bash
# Get last 50 predictions
curl "http://localhost:8000/api/history/"

# Get statistics
curl "http://localhost:8000/api/history/stats"

# Response:
{
  "total_predictions": 150,
  "unique_signs": 15,
  "average_confidence": 0.92,
  "sign_counts": {"A": 25, "B": 18, ...},
  "most_common": "A"
}
```

---

## Docker Deployment

### Build and Run with Docker

```bash
# Build Docker image
docker build -t sign-language-backend .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  sign-language-backend
```

### Using Docker Compose (Easier)

```bash
# Start services
docker-compose up

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Troubleshooting

### Problem: "No module named 'mediapipe'"

**Solution**: Reinstall requirements
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: "No hands detected"

**Solutions**:
- Ensure good lighting
- Hand must be fully visible in frame
- Try closer to camera
- Lower `MIN_DETECTION_CONFIDENCE` in `.env`

### Problem: Poor predictions after training

**Solutions**:
- Collect more training data (100+ per class)
- Include more varied angles
- Increase training epochs: `python scripts/train_model.py --epochs 100`
- Check if hands are clearly visible in training images

### Problem: "Model not found"

**Solution**: Train a model first
```bash
python scripts/train_model.py
```

### Problem: Out of memory during training

**Solutions**:
- Reduce batch size: `python scripts/train_model.py --batch-size 8`
- Reduce number of images in dataset
- Use GPU if available

---

## Production Tips

### 1. Use Gunicorn Instead of Uvicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 2. Enable CORS for Your Frontend

Update `app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Add Authentication (Optional)

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/detect-image")
async def detect_image(file: UploadFile = File(...), credentials: HTTPAuthCredentials = Depends(security)):
    # Verify token...
```

### 4. Monitor Performance

Track:
- Average detection time
- Model accuracy on validation set
- Server memory usage

### 5. Optimize Model

- Use TensorFlow Lite for mobile: `python -m tf2onnx`
- Quantize model for faster inference
- Use GPU acceleration

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Collect training data (50-100 images per letter)
3. ✅ Train model
4. ✅ Test API endpoints
5. ✅ Connect to React Native frontend
6. ✅ Deploy to production

---

## Resources

- **MediaPipe**: https://developers.google.com/mediapipe
- **FastAPI**: https://fastapi.tiangolo.com/
- **TensorFlow**: https://www.tensorflow.org/
- **OpenCV**: https://opencv.org/

## Support

For issues, check:
1. Backend logs (server terminal)
2. API docs at `http://localhost:8000/docs`
3. README.md for detailed API documentation

---

Happy coding! 🎉
