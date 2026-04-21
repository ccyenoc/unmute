"""
Data Collection Script for Sign Language Training
Helps users collect training data for specific sign classes using their webcam
"""
import cv2
import os

label = input("Enter phrase label (e.g. hi): ")

save_path = f"data/phrases/{label}"
os.makedirs(save_path, exist_ok=True)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera not opened")
    exit()

count = 0

print("Press SPACE to capture, Q to quit")

while True:
    ret, frame = cap.read()

    if not ret or frame is None:
       print("⚠️ Failed to grab frame")
       continue

    frame = cv2.flip(frame, 1)

    cv2.putText(frame, f"Label: {label} | Count: {count}",
                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Collect Data", frame)

    key = cv2.waitKey(1)

    if key == ord(' '):
        img_path = f"{save_path}/{count}.jpg"
        cv2.imwrite(img_path, frame)
        count += 1
        print(f"Saved {img_path}")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()