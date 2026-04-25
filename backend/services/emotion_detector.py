import cv2
import numpy as np
from tensorflow.keras.models import load_model

# ===== LOAD MODEL (once) =====
emotion_model = load_model("models/emotion_model.hdf5", compile=False)

EMOTION_LABELS = ['angry','disgust','fear','happy','sad','surprise','neutral']

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ===== MAIN FUNCTION =====
def predict_emotion(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return {
            "emotion": "No face",
            "confidence": 0.0
        }

    # pick largest face
    (x, y, w, h) = max(faces, key=lambda f: f[2]*f[3])

    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (64, 64))
    face = face.astype("float32") / 255.0
    face = np.reshape(face, (1, 64, 64, 1))

    preds = emotion_model.predict(face, verbose=0)[0]

    return {
        "emotion": EMOTION_LABELS[np.argmax(preds)],
        "confidence": float(np.max(preds))
    }