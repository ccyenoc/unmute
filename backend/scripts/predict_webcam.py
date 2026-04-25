import cv2
import numpy as np
import mediapipe as mp
import joblib
from collections import deque
import os

from tensorflow.keras.models import load_model

emotion_model = load_model("models/emotion_model.hdf5", compile=False)

emotion_labels = ['angry','disgust','fear','happy','sad','surprise','neutral']

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ===== TEXT INPUT STATE =====
typed_text = ""
text_mode = False
play_queue = []
current_word_idx = 0

SIGN_VIDEO_PATH = "data/videos"

# ===== VIDEO PLAYER =====
def play_video(word):
    path = os.path.join(SIGN_VIDEO_PATH, f"{word}.mp4")

    if not os.path.exists(path):
        print(f"❌ No video for: {word}")
        return

    cap_v = cv2.VideoCapture(path)

    while cap_v.isOpened():
        ret, frame = cap_v.read()
        if not ret:
            break

        cv2.imshow("Sign Playback", frame)

        if cv2.waitKey(25) & 0xFF == 27:  # ESC to skip
            break

    cap_v.release()
    cv2.destroyWindow("Sign Playback")

# ===== LOAD MODEL =====
model = joblib.load("models/sign_model.pkl")

# ===== CONFIG =====
PHRASE_DURATION = 30
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
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ===== STATE =====
history = deque(maxlen=12)
word_buffer = []
phrases = []
cooldown = 0
no_hand_frames = 0

# ===== CAMERA =====
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

   # ===== EMOTION DETECTION =====
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    emotion_text = "No face"

    if len(faces) > 0:
        (x, y, w, h) = max(faces, key=lambda f: f[2]*f[3])

        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (64, 64))
        face = face.astype("float32") / 255.0
        face = np.reshape(face, (1, 64, 64, 1))

        preds = emotion_model.predict(face, verbose=0)[0]
        emotion_text = emotion_labels[np.argmax(preds)]

        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)
    # ===== HAND DETECTION (UNCHANGED) =====
    if results.multi_hand_landmarks:
        no_hand_frames = 0

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
            print("WEBCAM ROW:", row[0][:10])

            probs = model.predict_proba(row)
            confidence = np.max(probs)

            if confidence < CONFIDENCE_THRESHOLD:
                pred = "..."
            else:
                pred = model.predict(row)[0]

            history.append(pred)

        if len(history) > 0:
            prediction = max(set(history), key=history.count)

        if cooldown > 0:
            cooldown -= 1

        if (
            history.count(prediction) >= len(history) * 0.6
            and cooldown == 0
            and prediction != "..."
        ):

            if prediction in DIRECT_PHRASES:
                phrases.append([DIRECT_PHRASES[prediction], PHRASE_DURATION])
                cooldown = 30
                history.clear()
                word_buffer = []

            else:
                if len(word_buffer) == 0:
                    word_buffer.append(prediction)

                else:
                    prev = word_buffer[-1]

                    if prev == "me" and prediction == "hungry":
                        phrases.append(["I am hungry", PHRASE_DURATION])
                        word_buffer = []

                    elif prev == "me" and prediction == "tired":
                        phrases.append(["I am tired", PHRASE_DURATION])
                        word_buffer = []

                    else:
                        word_buffer.append(prediction)

                cooldown = 15

    else:
        no_hand_frames += 1
        if no_hand_frames > 15:
            history.clear()
            word_buffer = []

    # ===== UPDATE PHRASES =====
    for p in phrases:
        p[1] -= 1

    phrases = [p for p in phrases if p[1] > 0]

    display_text = " ".join([p[0] for p in phrases])

    # ===== DISPLAY =====
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
    
    cv2.putText(frame, f"Emotion: {emotion_text}",
            (10, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255,100,100),
            2)

    # ===== TEXT INPUT DISPLAY =====
    if text_mode:
        cv2.putText(frame, f"Typing: {typed_text}",
                    (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0,200,255),
                    2)
    else:
        cv2.putText(frame, "Press 't' to type",
                    (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (200,200,200),
                    2)

    cv2.imshow("Sign Translator", frame)

    key = cv2.waitKey(1) & 0xFF

    # ===== KEY HANDLING =====
    if key == ord('t'):
        text_mode = True
        typed_text = ""

    elif text_mode:
        if key == 13:  # ENTER
            print("Typed:", typed_text)
            text_mode = False
            text = typed_text.lower().replace(" ", "_")

            text = typed_text.lower().replace("i am", "me")
            play_queue = text.split()
            current_word_idx = 0

        elif key == 8:
            typed_text = typed_text[:-1]

        elif 32 <= key <= 126:
            typed_text += chr(key)

    if key == ord('c'):
        phrases = []
        word_buffer = []
        play_queue = []

    if key == ord('q'):
        break

    # ===== VIDEO PLAYBACK =====
    if play_queue:
        word = play_queue[current_word_idx]
        play_video(word)

        current_word_idx += 1
        if current_word_idx >= len(play_queue):
            play_queue = []

cap.release()
cv2.destroyAllWindows()