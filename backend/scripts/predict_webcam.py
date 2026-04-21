import cv2
import numpy as np
import mediapipe as mp
import joblib
from collections import deque

model = joblib.load("models/phrase_model.pkl")

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

history = deque(maxlen=10)

cap = cv2.VideoCapture(0)

print("✅ Running phrase detection")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    prediction = "..."

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            row = []

            base_x = hand_landmarks.landmark[0].x
            base_y = hand_landmarks.landmark[0].y

            for lm in hand_landmarks.landmark:
                row.extend([lm.x - base_x, lm.y - base_y])

            row = np.array(row).reshape(1, -1)

            pred = model.predict(row)[0]
            history.append(pred)

            prediction = max(set(history), key=history.count)

    cv2.putText(frame, f"Prediction: {prediction}",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2)

    cv2.imshow("Sign Translator", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()