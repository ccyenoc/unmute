import cv2
import numpy as np
from tensorflow.keras.models import load_model

model = load_model("models/emotion_model.hdf5", compile=False)

emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

cap = cv2.VideoCapture(0)

print("✅ Emotion detection running...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    emotion_text = "No face"
    confidence = 0.0

    if len(faces) > 0:
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])

        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (64, 64))
        face = face.astype("float32") / 255.0
        face = np.reshape(face, (1, 64, 64, 1))

        preds = model.predict(face, verbose=0)[0]
        emotion_text = emotion_labels[np.argmax(preds)]
        confidence = np.max(preds)

        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.putText(frame, f"{emotion_text} ({confidence:.2f})",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2)

    cv2.imshow("Emotion Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()