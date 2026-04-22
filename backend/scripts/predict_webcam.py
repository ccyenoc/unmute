import cv2
import numpy as np
import mediapipe as mp
import joblib
from collections import deque

model = joblib.load("models/sign_model.pkl")

# ===== CONFIG =====
PHRASE_DURATION = 30   # ~1 second
CONFIDENCE_THRESHOLD = 0.7

DIRECT_PHRASES = {
    "hi": "Hi",
    "iloveyou": "I love you",
    "thankyou": "Thank you",
    "goodbye": "Goodbye"
}

# ===== MEDIAPIPE =====
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ===== STATE =====
history = deque(maxlen=12)
word_buffer = []          # temporary words (e.g. ["me"])
phrases = []              # list of [text, timer]
cooldown = 0
no_hand_frames = 0

cap = cv2.VideoCapture(0)

print("✅ Running Sign Translator")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    prediction = "..."

    # ===== HAND DETECTED =====
    if results.multi_hand_landmarks:
        no_hand_frames = 0

        for hand_landmarks in results.multi_hand_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Extract features
            row = []
            base_x = hand_landmarks.landmark[0].x
            base_y = hand_landmarks.landmark[0].y

            for lm in hand_landmarks.landmark:
                row.extend([lm.x - base_x, lm.y - base_y])

            row = np.array(row).reshape(1, -1)

            # Prediction with confidence
            probs = model.predict_proba(row)
            confidence = np.max(probs)

            if confidence < CONFIDENCE_THRESHOLD:
                pred = "..."
            else:
                pred = model.predict(row)[0]

            history.append(pred)

        # ===== STABLE PREDICTION =====
        if len(history) > 0:
            prediction = max(set(history), key=history.count)

        if cooldown > 0:
            cooldown -= 1

        # ===== ACCEPT WORD =====
        if (
            history.count(prediction) >= len(history) * 0.6
            and cooldown == 0
            and prediction != "..."
        ):

            # 🔥 DIRECT PHRASES
            if prediction in DIRECT_PHRASES:
                phrases.append([DIRECT_PHRASES[prediction], PHRASE_DURATION])
                cooldown = 30
                history.clear()
                word_buffer = []

            else:
                # ===== BUILD WORD BUFFER =====
                if len(word_buffer) == 0:
                    word_buffer.append(prediction)

                else:
                    prev = word_buffer[-1]

                    # 🔥 "me hungry" → phrase
                    if prev == "me" and prediction == "hungry":
                        phrases.append(["I am hungry", PHRASE_DURATION])
                        word_buffer = []

                    elif prev == "me" and prediction == "tired":
                        phrases.append(["I am tired", PHRASE_DURATION])
                        word_buffer = []

                    # 🔥 name detection
                    elif prev == "name":
                        phrases.append([f"My name is {prediction.upper()}", PHRASE_DURATION])
                        word_buffer = []

                    else:
                        word_buffer.append(prediction)

                cooldown = 15

    # ===== NO HAND =====
    else:
        no_hand_frames += 1

        if no_hand_frames > 15:
            history.clear()
            word_buffer = []

    # ===== UPDATE PHRASES (TIMER) =====
    for p in phrases:
        p[1] -= 1

    phrases = [p for p in phrases if p[1] > 0]

    # ===== DISPLAY =====
    display_text = " ".join([p[0] for p in phrases])

    cv2.putText(frame, f"Prediction: {prediction}",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2)

    cv2.putText(frame, f"Sentence: {display_text}",
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255,255,0),
                2)

    cv2.imshow("Sign Translator", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    if key == ord('c'):
        phrases = []
        word_buffer = []

cap.release()
cv2.destroyAllWindows()