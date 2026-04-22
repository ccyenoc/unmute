import cv2
import os

# 🔥 choose type
data_type = input("Enter type (sign / phrase): ").strip().lower()
label = input("Enter label (e.g. hungry / iloveyou): ").strip().lower()

# validate input
if data_type not in ["sign", "phrase"]:
    print("❌ Invalid type. Use 'sign' or 'phrase'")
    exit()

folder_name = "signs" if data_type == "sign" else "phrases"

save_path = f"data/{folder_name}/{label}"
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

    cv2.putText(frame, f"{data_type.upper()}: {label} | Count: {count}",
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