"""
Collect emotion-labeled face samples from webcam for Module 2 (FEN training).

Usage:
  python scripts/collect_emotion_data.py --label happy --samples 50
  python scripts/collect_emotion_data.py --label neutral --backend http://localhost:8000

Controls:
  c - capture current frame and upload as sample
  q - quit collector
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import cv2
import requests


VALID_LABELS = {"angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect emotion-labeled face samples via backend API.")
    parser.add_argument("--label", required=True, help="Emotion label (happy, angry, neutral, etc.)")
    parser.add_argument("--samples", type=int, default=50, help="Number of samples to collect")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index")
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    return parser.parse_args()


def upload_sample(base_url: str, label: str, frame_bgr: Any) -> dict:
    ok, encoded = cv2.imencode(".jpg", frame_bgr)
    if not ok:
        raise RuntimeError("Failed to encode captured frame")

    files = {
        "file": (f"{label}.jpg", encoded.tobytes(), "image/jpeg"),
    }
    params = {"label": label}

    response = requests.post(
        f"{base_url.rstrip('/')}/api/facial-emotion/collect-sample",
        params=params,
        files=files,
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f"Upload failed ({response.status_code}): {response.text}")

    return response.json()


def main() -> int:
    args = parse_args()
    label = args.label.strip().lower()
    if label not in VALID_LABELS:
        print(f"Invalid label '{args.label}'. Choose from: {sorted(VALID_LABELS)}")
        return 2

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("Could not open camera")
        print("Tip: In remote/container environments, webcam access is often unavailable.")
        print("Use /api/facial-emotion/collect-sample-frame from your mobile/frontend camera instead.")
        return 1

    print(f"Collecting up to {args.samples} samples for label='{label}'")
    print("Press 'c' to capture, 'q' to quit.")

    captured = 0
    try:
        while captured < args.samples:
            ok, frame = cap.read()
            if not ok:
                print("Camera read failed")
                continue

            display = frame.copy()
            cv2.putText(
                display,
                f"Label: {label} | Captured: {captured}/{args.samples}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                display,
                "Press c=Capture q=Quit",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Emotion Data Collector", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("c"):
                try:
                    result = upload_sample(args.backend, label, frame)
                    captured += 1
                    print(
                        f"Saved {captured}/{args.samples}: "
                        f"{result.get('sample', {}).get('file_path', 'unknown')}"
                    )
                except Exception as exc:
                    print(f"Capture failed: {exc}")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"Done. Captured {captured} sample(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
