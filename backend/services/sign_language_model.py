"""
Sign Language Model Handler
Manages the neural network model for sign language classification
"""

import cv2
import numpy as np
import mediapipe as mp
import joblib
from collections import deque
import os

# ===== LOAD MODEL =====
# Handle both relative and absolute paths
model_path = "models/sign_model.pkl"
if not os.path.exists(model_path):
    # Try absolute path from backend directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(current_dir, "models", "sign_model.pkl")

model = joblib.load(model_path)
print(f"✅ Model loaded from: {model_path}")

# ===== MEDIAPIPE SETUP =====
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,  # Match predict_webcam.py for stability
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ===== CONFIG =====
CONFIDENCE_THRESHOLD = 0.7
SINGLE_HAND_THRESHOLD = 0.5  # Lower threshold for single-hand signs
history = deque(maxlen=12)  # Match predict_webcam.py for better smoothing

# ===== MAIN FUNCTION =====
def predict_sign(frame):
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    frame = frame[:, int(w * 0.2):int(w * 0.8)]


    # 🔥 FIX 2: resize like webcam (NOT square)
    frame = cv2.resize(frame, (640, 480))

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Extract landmarks for frontend visualization
    landmarks_data = []
    predictions = []
    confidences = []

    # ❌ No hand detected
    if not results.multi_hand_landmarks:
        return {
            "prediction": "No hand",
            "confidence": 0.0,
            "landmarks": []
        }

    # ✅ Process ALL detected hands (match predict_webcam.py)
    for hand_landmarks in results.multi_hand_landmarks:
        # Extract features for prediction
        row = []
        base_x = hand_landmarks.landmark[0].x
        base_y = hand_landmarks.landmark[0].y

        for lm in hand_landmarks.landmark:
            row.extend([lm.x - base_x, lm.y - base_y])

        row = np.array(row).reshape(1, -1)
        print("DEBUG ROW:", row[0][:10])
        print("MOBILE ROW:", row[0][:10])

        # ===== PREDICTION =====
        probs = model.predict_proba(row)
        confidence = float(np.max(probs))

        # Use different thresholds for single vs multiple hands
        threshold = SINGLE_HAND_THRESHOLD if len(results.multi_hand_landmarks) == 1 else CONFIDENCE_THRESHOLD
        
        if confidence < threshold:
            pred = "Uncertain"
        else:
            pred = model.predict(row)[0]

        predictions.append(pred)
        confidences.append(confidence)

        # Store landmarks for frontend
        hand_lms = []
        for lm in hand_landmarks.landmark:
            hand_lms.append({
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z)
            })
        landmarks_data.append(hand_lms)

    # Use first hand prediction (best confidence)
    if predictions:
        best_idx = confidences.index(max(confidences))
        pred = predictions[best_idx]
        confidence = confidences[best_idx]
    else:
        return {
            "prediction": "No hand",
            "confidence": 0.0,
            "landmarks": []
        }

    # ===== SMOOTHING =====
    history.append(pred)
    final_pred = max(set(history), key=history.count)

    return {
        "prediction": final_pred,
        "confidence": confidence,
        "landmarks": landmarks_data
    }
