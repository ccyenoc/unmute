# Sign Language Translator Backend 🔥

Python FastAPI backend with MediaPipe for real-time sign language detection.

## Tech Stack

- **Framework**: FastAPI
- **Hand Detection**: MediaPipe (21 landmarks per hand)
- **ML Model**: TensorFlow/Keras
- **Facial Emotion Detection**: DeepFace with FER fallback
- **Video Processing**: OpenCV
- **API**: RESTful with CORS support

## Quick Start

### Run Backend (Copy/Paste)

From the project root:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Alternative run command:

```bash
cd backend
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

### 1. Prerequisites

- Python 3.8+
- pip or conda

### 2. Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Server

```bash
# Development mode with auto-reload
python app.py

# Or using uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs** (Swagger UI)

## Project Structure

```
backend/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── services/
│   ├── hand_detector.py   # MediaPipe hand detection
│   └── sign_language_model.py  # TensorFlow model for classification
├── routes/
│   ├── detection.py       # Real-time detection endpoints
│   ├── history.py         # Translation history management
│   └── training.py        # Model training endpoints
├── models/
│   └── sign_language_model.h5  # Trained model (auto-created)
└── data/
    ├── training_dataset/  # Training images by class (A-Z)
    └── translation_history.json
```

## API Endpoints

### Detection

#### POST `/api/detection/detect-image`
Detect sign language from uploaded image.

```bash
curl -X POST "http://localhost:8000/api/detection/detect-image" \
  -F "file=@image.jpg"
```

**Response:**
```json
{
  "success": true,
  "num_hands_detected": 1,
  "predictions": [
    {
      "prediction": "A",
      "confidence": 0.95,
      "all_predictions": {...}
    }
  ],
  "handedness": ["Right"],
  "annotated_image": "base64_encoded_image"
}
```

#### POST `/api/detection/detect-frame`
Optimize for real-time mobile/streaming usage (returns smaller response).

```bash
curl -X POST "http://localhost:8000/api/detection/detect-frame" \
  -F "file=@frame.jpg"
```

#### GET `/api/detection/model-info`
Get model configuration and available classes.

### Training

#### POST `/api/training/upload-training-data`
Upload training images for a specific sign class.

```bash
curl -X POST "http://localhost:8000/api/training/upload-training-data?sign_class=A" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"
```

#### POST `/api/training/train-model`
Train model on all uploaded dataset.

```bash
curl -X POST "http://localhost:8000/api/training/train-model?epochs=50&batch_size=32"
```

#### GET `/api/training/dataset-info`
View dataset statistics.

### Facial Emotion

#### POST `/api/emotion/predict`
Unified facial emotion prediction endpoint.

Accepts either:
- JSON body with base64 frame: `{"image":"<base64_string>"}`
- Multipart image upload: `file=@face.jpg`

```bash
# JSON base64 input
curl -X POST "http://localhost:8000/api/emotion/predict" \
  -H "Content-Type: application/json" \
  -d '{"image":"data:image/jpeg;base64,/9j/..."}'
```

```bash
# Multipart file input
curl -X POST "http://localhost:8000/api/emotion/predict" \
  -F "file=@face.jpg"
```

**Response:**
```json
{
  "emotion": "happy",
  "confidence": 0.92,
  "face_detected": true
}
```

#### GET `/api/facial-emotion/health`
Check whether the emotion service is ready.

#### POST `/api/facial-emotion/analyze-image`
Detect facial emotion from an uploaded image.

```bash
curl -X POST "http://localhost:8000/api/facial-emotion/analyze-image" \
  -F "file=@face.jpg"
```

#### POST `/api/facial-emotion/analyze-frame`
Detect facial emotion from a base64-encoded mobile camera frame.

```bash
curl -X POST "http://localhost:8000/api/facial-emotion/analyze-frame" \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"data:image/jpeg;base64,/9j/..."}'
```

**Response:**
```json
{
  "success": true,
  "face_detected": true,
  "faces_detected": 1,
  "provider": "deepface",
  "emotion": "happy",
  "confidence": 98.42,
  "scores": {
    "angry": 0,
    "disgust": 0,
    "fear": 0,
    "happy": 98.42,
    "sad": 0,
    "surprise": 1.58,
    "neutral": 0
  },
  "results": []
}
```

#### GET `/api/facial-emotion/model-info`
Returns available providers and supported emotion labels.

#### POST `/api/facial-emotion/collect-sample`
Collect and store labeled emotion samples for optional custom training.

```bash
curl -X POST "http://localhost:8000/api/facial-emotion/collect-sample?label=happy" \
  -F "file=@face_happy.jpg"
```

#### GET `/api/facial-emotion/dataset-info`
View emotion dataset size per class.

```bash
curl "http://localhost:8000/api/facial-emotion/dataset-info"
```

#### POST `/api/facial-emotion/train`
Start a background emotion training job scaffold.

```bash
curl -X POST "http://localhost:8000/api/facial-emotion/train?epochs=20&batch_size=32"
```

#### GET `/api/facial-emotion/training-status`
Check current or previous training job status.

```bash
curl "http://localhost:8000/api/facial-emotion/training-status"
```

```bash
curl "http://localhost:8000/api/facial-emotion/training-status?job_id=<job_id>"
```

### Fusion

#### POST `/api/fusion/interpret`
Combines sign output and facial emotion to detect alignment/mismatch context.

```bash
curl -X POST "http://localhost:8000/api/fusion/interpret" \
  -H "Content-Type: application/json" \
  -d '{
    "sign":"HELLO",
    "emotion":"angry",
    "confidence":87,
    "expected_emotions":["happy","neutral"]
  }'
```

**Fusion Response:**
```json
{
  "sign": "HELLO",
  "emotion": "angry",
  "confidence": 87,
  "status": "mismatch",
  "message": "Emotion may not match expected context. Consider clarifying intent.",
  "expected_emotions": ["happy", "neutral"]
}
```

## API Checklist (Implemented vs Later)

Implemented now:
- `GET /api/facial-emotion/health`
- `GET /api/facial-emotion/model-info`
- `POST /api/facial-emotion/analyze-image`
- `POST /api/facial-emotion/analyze-frame`
- `POST /api/facial-emotion/collect-sample`
- `GET /api/facial-emotion/dataset-info`
- `POST /api/facial-emotion/train`
- `GET /api/facial-emotion/training-status`
- `POST /api/fusion/interpret`

You can fill later:
- Custom model persistence (e.g., save `.h5`/`.keras` weights)
- Real FER/FEN training loop + validation metrics endpoint
- `POST /api/fusion/rules` (custom sign-emotion rule management)

### History

#### GET `/api/history/`
Get translation history (last 50 by default).

```bash
curl "http://localhost:8000/api/history/?limit=100"
```

#### GET `/api/history/stats`
Get statistics about translations.

#### POST `/api/history/add`
Add translation to history.

```bash
curl -X POST "http://localhost:8000/api/history/add" \
  -H "Content-Type: application/json" \
  -d '{"prediction":"A","confidence":0.95}'
```

## How MediaPipe Works 🔥

MediaPipe detects **21 landmarks (keypoints)** per hand:

```
0:  Wrist
1-4:  Thumb (CMC, MCP, IP, TIP)
5-8:  Index (MCP, PIP, DIP, TIP)
9-12: Middle (MCP, PIP, DIP, TIP)
13-16: Ring (MCP, PIP, DIP, TIP)
17-20: Pinky (MCP, PIP, DIP, TIP)
```

Each landmark has:
- **X**: Normalized horizontal position (0-1)
- **Y**: Normalized vertical position (0-1)
- **Z**: Depth (relative to wrist)
- **Visibility**: Confidence that landmark is visible

**Total feature vector**: 21 landmarks × 3 coordinates = **63 dimensions**

## Model Architecture

```
Input Layer (63 features)
    ↓
Dense(128, relu) + Dropout(0.2)
    ↓
Dense(64, relu) + Dropout(0.2)
    ↓
Dense(32, relu) + Dropout(0.1)
    ↓
Output Layer (26 classes: A-Z)
```

## Training Your Model

### Step 1: Prepare Dataset

Create folder structure:
```
data/training_dataset/
├── A/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── B/
│   ├── image1.jpg
│   └── ...
└── ... (A-Z)
```

**Best practices for training data:**
- 50-100+ images per sign class
- Various angles, lighting conditions, backgrounds
- Clear hand visibility
- High quality images

### Step 2: Train the Model

Upload images:
```bash
# Upload images for class 'A'
curl -X POST "http://localhost:8000/api/training/upload-training-data?sign_class=A" \
  -F "files=@A_image1.jpg" \
  -F "files=@A_image2.jpg"

# Repeat for other classes...
```

Train model:
```bash
curl -X POST "http://localhost:8000/api/training/train-model?epochs=50"
```

### Step 3: Use for Detection

Once trained, use the detection endpoints for predictions.

## Real-Time Detection Workflow

```
Mobile App (React Native)
      ↓
   Capture frame
      ↓
POST to /api/detection/detect-frame
      ↓
Server: MediaPipe detects hands
      ↓
Server: ML model classifies gesture
      ↓
Return prediction + confidence
      ↓
Display on mobile app
```

## Performance Tips

1. **Detection Speed**: MediaPipe runs at ~30 FPS on CPU
2. **Model Inference**: ~10ms per prediction on CPU
3. **Optimization**: Use `detect-frame` for real-time (smaller response)
4. **Batch Processing**: Use `detect-image` for accuracy

## Troubleshooting

### Model not found
- Train a model first using `/api/training/train-model`
- Or download a pre-trained model

### No hands detected
- Ensure good lighting
- Hand must be fully visible
- Try adjusting `MIN_DETECTION_CONFIDENCE` in `.env`

### Poor predictions
- More training data needed (aim for 100+ images per class)
- More diverse angles and backgrounds in training set
- Increase training epochs

## Environment Variables

```
PORT=8000                    # Server port
DEBUG=True                   # Debug mode
MODEL_PATH=models/...        # Path to trained model
MAX_HANDS=2                  # Max hands to detect
MIN_DETECTION_CONFIDENCE=0.5 # Detection threshold
```

## Next Steps

1. **Data Collection**: Use app to collect sign language images
2. **Model Training**: Train on collected dataset
3. **Fine-tuning**: Incrementally add more classes
4. **Deployment**: Use gunicorn for production

## Resources

- [MediaPipe Hand Documentation](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TensorFlow Guide](https://www.tensorflow.org/guide)

---

Happy coding! 🚀
