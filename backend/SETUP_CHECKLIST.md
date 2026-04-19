# 📋 Backend Setup Checklist

Complete checklist to get your sign language detector backend running.

## Phase 1: Installation ✅

### Prerequisites
- [ ] Python 3.8+ installed (`python --version`)
- [ ] pip installed (`pip --version`)
- [ ] Webcam connected (for data collection)
- [ ] 2GB+ free disk space

### Step-by-Step

#### 1.1 Navigate to Backend
```bash
cd backend
```
- [ ] Confirmed: in backend directory

#### 1.2 Create Virtual Environment
```bash
python -m venv venv
```
- [ ] Virtual environment created
- [ ] Folder "venv" exists

#### 1.3 Activate Virtual Environment
**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```
- [ ] Prompt shows "(venv)" at start

#### 1.4 Install Dependencies
```bash
pip install -r requirements.txt
```
- [ ] Installation completed (may take 5-10 min)
- [ ] No error messages
- [ ] All packages installed

#### 1.5 Verify Installation
```bash
python scripts/test_setup.py
```
- [ ] Test completes successfully
- [ ] All imports show ✅
- [ ] Receives message: "Backend is ready to use"

---

## Phase 2: Data Collection 📸

### Decide on Data Source

#### Option A: Webcam Collection (Recommended)
- [ ] Webcam is functional
- [ ] Good lighting available
- [ ] Quiet space

#### Option B: Pre-collected Images
- [ ] Images of sign language available
- [ ] Organized by letter (A-Z)
- [ ] At least 50-100 per letter

#### Option C: Online Dataset
- [ ] Found sign language dataset online
- [ ] Downloaded and organized
- [ ] Ready to import

### Data Collection Steps

#### 2.1 Start Collection Script
```bash
python scripts/collect_data.py
```
- [ ] Script launches
- [ ] Camera window opens

#### 2.2 Choose Collection Type
```
Select option (1-3): 1
```
- [ ] Option 1 selected: Collect single sign

#### 2.3 Enter Sign Letter
```
Enter sign letter (A-Z): A
```
- [ ] Letter entered: A
- [ ] Webcam shows live feed

#### 2.4 Capture Images
For each sign:
- [ ] Position hand in green rectangle
- [ ] Ensure good hand visibility
- [ ] Press 'c' to capture (50-100 times)
- [ ] Press 'q' when done

#### 2.5 Repeat for All Letters
- [ ] Collected data for at least 5 letters (recommended)
- [ ] Each has 30+ images
- [ ] Ideally: A-Z with 50+ images each

#### 2.6 Verify Dataset
```bash
python scripts/collect_data.py
# Select option 3: View dataset statistics
```
- [ ] Statistics shown
- [ ] Total images > 100
- [ ] Multiple letters represented

---

## Phase 3: Model Training 🧠

### Pre-Training Checklist
- [ ] Dataset created with images
- [ ] At least 100 total images
- [ ] At least 3-5 different letter classes

### Train Model

#### 3.1 Start Training
```bash
python scripts/train_model.py
```
- [ ] Training script starts
- [ ] Loading dataset message appears
- [ ] No errors in output

#### 3.2 Monitor Training
Watch for:
- [ ] Images loaded per class
- [ ] Training/validation split shown
- [ ] Epochs counting up
- [ ] Loss decreasing
- [ ] Accuracy increasing

#### 3.3 Training Completes
- [ ] Training completes without errors
- [ ] "Model saved" message appears
- [ ] No exceptions or crashes

#### 3.4 Verify Model Created
```bash
ls models/
```
- [ ] File exists: `sign_language_model.h5`
- [ ] File size > 100KB

---

## Phase 4: Backend Server 🚀

### Start Server

#### 4.1 Launch Backend
```bash
python app.py
```
- [ ] Server starts
- [ ] Message: "Uvicorn running on http://0.0.0.0:8000"
- [ ] No error messages

#### 4.2 Keep Server Running
- [ ] Leave terminal open
- [ ] Don't press Ctrl+C yet

### Access API Documentation

#### 4.3 Open API Docs (in browser)
```
http://localhost:8000/docs
```
- [ ] Swagger UI page loads
- [ ] List of endpoints visible
- [ ] All routes shown

#### 4.4 Verify Health
In another terminal:
```bash
curl http://localhost:8000/health
```
- [ ] Response: `{"status":"ok"}`
- [ ] Server is healthy

---

## Phase 5: Testing API 🧪

### Without Training Data (Skip if untrained)

#### 5.1 Test Detection Endpoint
```bash
curl "http://localhost:8000/api/detection/model-info"
```
- [ ] Response shows model info
- [ ] 26 classes listed (A-Z)
- [ ] Model path shown

### With Trained Model

#### 5.2 Test with Image
Prepare a test image with your hand sign:
```bash
curl -X POST "http://localhost:8000/api/detection/detect-image" \
  -F "file=@test_image.jpg"
```
- [ ] Response received
- [ ] Prediction shown (letter)
- [ ] Confidence score > 0
- [ ] JSON response valid

#### 5.3 Check History
```bash
curl "http://localhost:8000/api/history/"
```
- [ ] Predictions listed
- [ ] Timestamps shown
- [ ] No errors

#### 5.4 View Statistics
```bash
curl "http://localhost:8000/api/history/stats"
```
- [ ] Statistics displayed
- [ ] Confidence average shown
- [ ] Most common letter shown

---

## Phase 6: Documentation Review 📚

### Read Documentation
- [ ] README.md - Full API reference
- [ ] QUICKSTART.md - Quick start guide
- [ ] ARCHITECTURE.md - System design
- [ ] QUICK_REFERENCE.md - Copy-paste examples
- [ ] SETUP_SUMMARY.md - Complete summary

### Key Concepts Understood
- [ ] What MediaPipe does (hand detection)
- [ ] What TensorFlow model does (classification)
- [ ] How features are extracted (63 dimensions)
- [ ] What API endpoints do
- [ ] How frontend connects

---

## Phase 7: Frontend Integration 🔗

### Prepare Frontend Connection

#### 7.1 Review Frontend Guide
```
Read: FRONTEND_INTEGRATION.md
```
- [ ] Understood integration approach
- [ ] Reviewed example code
- [ ] Know API endpoints to use

#### 7.2 Update Frontend API URL
In frontend code (if needed):
```javascript
const API_URL = 'http://localhost:8000';
```
- [ ] API_URL correct for your setup
- [ ] Backend IP/port matches

#### 7.3 Test Frontend Connection
In frontend project:
```bash
# Try to fetch from backend
curl http://localhost:8000/health
```
- [ ] Response received
- [ ] Connection works

---

## Phase 8: Production Readiness 🏭

### Optional: Docker Setup

#### 8.1 Build Docker Image
```bash
docker build -t sign-language-backend .
```
- [ ] Image built successfully
- [ ] No errors
- [ ] Image size reasonable

#### 8.2 Run Docker Container
```bash
docker run -p 8000:8000 sign-language-backend
```
- [ ] Container starts
- [ ] Server accessible at http://localhost:8000
- [ ] Works like native Python

### Optional: Production Deployment

#### 8.3 Choose Deployment Platform
- [ ] Decision made (Heroku, AWS, Google Cloud, etc.)
- [ ] Platform account created
- [ ] Deployment credentials prepared

#### 8.4 Prepare for Deployment
- [ ] .env configured for production
- [ ] Database setup (if using)
- [ ] Secrets/keys secured
- [ ] Error handling tested

---

## Phase 9: Final Verification ✓

### System Test

#### 9.1 Full End-to-End Test
```
1. Start backend: python app.py
2. Open: http://localhost:8000/docs
3. Upload test image
4. Verify prediction received
5. Check history updated
6. View statistics
```
- [ ] All steps completed successfully
- [ ] No errors encountered
- [ ] System working end-to-end

#### 9.2 Performance Verification
```bash
time curl -X POST "http://localhost:8000/api/detection/detect-image" \
  -F "file=@test_image.jpg"
```
- [ ] Response time < 2 seconds
- [ ] Confidence > 0.5 (if well-trained)
- [ ] No timeouts

#### 9.3 Stress Test (Optional)
```bash
# Send multiple requests
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/detection/detect-image" \
    -F "file=@test_image.jpg"
done
```
- [ ] All requests successful
- [ ] No crashes
- [ ] Server stable

### Cleanup

#### 9.4 Organize Files
```bash
# Create .gitignore to exclude data
git init  # if not already git project
```
- [ ] .gitignore in place
- [ ] Large files not tracked
- [ ] Repository clean

---

## Issues & Solutions

### If Something Doesn't Work

#### ModuleNotFoundError
```bash
pip install -r requirements.txt --upgrade
```
- [ ] Try reinstalling all packages

#### Port 8000 Already in Use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```
- [ ] Port freed up
- [ ] Server can start

#### No Hands Detected
- [ ] Better lighting needed
- [ ] Hand fully visible in frame
- [ ] Adjust MIN_DETECTION_CONFIDENCE in .env

#### Poor Predictions
- [ ] Collect more training data
- [ ] More diverse angles and backgrounds
- [ ] Retrain model

---

## Success Criteria ✅

You're successful when you can:

- ✅ Run backend without errors
- ✅ Access API documentation at /docs
- ✅ Upload and detect images
- ✅ View prediction history
- ✅ Retrain model with new data
- ✅ Connect from frontend (when ready)
- ✅ Deploy to production (when ready)

---

## Next Steps After Setup

1. **Integrate with Frontend**
   - Connect React Native app to backend
   - Test real-time detection
   - Add UI improvements

2. **Improve Accuracy**
   - Collect more training data
   - Train with more epochs
   - Try different architectures

3. **Add Features**
   - Add more sign classes
   - Support for words/phrases
   - Real-time video streaming

4. **Deploy**
   - Setup production server
   - Configure domain/SSL
   - Monitor performance

---

## Help & Support

### Documentation Files
- `README.md` - API reference
- `QUICKSTART.md` - Quick start
- `ARCHITECTURE.md` - System design  
- `QUICK_REFERENCE.md` - Command reference
- `SETUP_SUMMARY.md` - Complete overview

### Resources
- FastAPI: https://fastapi.tiangolo.com/
- MediaPipe: https://developers.google.com/mediapipe
- TensorFlow: https://www.tensorflow.org/
- OpenCV: https://opencv.org/

### Debugging
```bash
# Verify everything
python scripts/test_setup.py

# Check server logs
# Look in the terminal running 'python app.py'
```

---

**Congratulations! 🎉 Your backend is set up and ready!**

Next: Connect your React Native frontend and start detecting sign language!

---

*Last Updated: 2024*
*For questions or issues, refer to documentation or GitHub discussions*
