"""
Model Training Utility Script
Train the sign language model locally
"""
import os
import cv2
import numpy as np
import mediapipe as mp
from sklearn.ensemble import RandomForestClassifier
import joblib
from collections import Counter

dataset_path = "data"   # 👈 IMPORTANT

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5
)

X = []
y = []

# 🔥 LOOP THROUGH signs + phrases
for category in ["signs", "phrases"]:
    category_path = os.path.join(dataset_path, category)

    for label in os.listdir(category_path):
        folder = os.path.join(category_path, label)

        print(f"Processing {category}/{label}...")

        for img_name in os.listdir(folder):
            img_path = os.path.join(folder, img_name)
            img = cv2.imread(img_path)

            if img is None:
                continue

            img = cv2.resize(img, (256, 256))
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:

                    row = []

                    base_x = hand_landmarks.landmark[0].x
                    base_y = hand_landmarks.landmark[0].y

                    for lm in hand_landmarks.landmark:
                        row.extend([lm.x - base_x, lm.y - base_y])

                    X.append(row)
                    y.append(label)

print("Data distribution:", Counter(y))

X = np.array(X)
y = np.array(y)

print("Training model...")

model = RandomForestClassifier(n_estimators=200)
model.fit(X, y)

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/sign_model.pkl")  # 👈 renamed

print("✅ Model trained and saved!")
