"""
Data Collection Script for Sign Language Training
Helps users collect training data for specific sign classes using their webcam
"""

import cv2
import os
from pathlib import Path
import mediapipe as mp

class DataCollector:
    """Collect training data for sign language using webcam"""
    
    def __init__(self, output_dir: str = "data/training_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
    
    def collect_data_for_sign(self, sign: str, num_images: int = 50):
        """
        Collect training images for a specific sign
        
        Args:
            sign: Sign letter (A-Z)
            num_images: Number of images to capture
        """
        sign = sign.upper()
        if not sign.isalpha() or len(sign) != 1:
            print("Invalid sign. Please use a single letter (A-Z)")
            return
        
        sign_dir = self.output_dir / sign
        sign_dir.mkdir(exist_ok=True)
        
        # Count existing images
        existing = len(list(sign_dir.glob("*.jpg")))
        
        print(f"\n📸 Collecting data for sign '{sign}'")
        print(f"Existing images: {existing}")
        print(f"Target images: {num_images}")
        print("Press 'c' to capture, 'q' to quit\n")
        
        cap = cv2.VideoCapture(0)
        count = 0
        
        while count < num_images:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame for selfie view
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            # Process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Draw hand landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )
                status_color = (0, 255, 0)  # Green - hand detected
            else:
                status_color = (0, 0, 255)  # Red - no hand
            
            # Display info
            cv2.putText(frame, f"Sign: {sign}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Captured: {count}/{num_images}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            cv2.putText(frame, "Press 'c' to capture, 'q' to quit", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Add ROI rectangle
            cv2.rectangle(frame, (50, 50), (w-50, h-50), status_color, 2)
            
            cv2.imshow('Data Collection - Press c to capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                # Only save if hand is detected
                if results.multi_hand_landmarks:
                    image_path = sign_dir / f"{sign}_{existing + count + 1:04d}.jpg"
                    cv2.imwrite(str(image_path), frame)
                    print(f"✓ Captured image {count + 1}/{num_images}")
                    count += 1
                else:
                    print("⚠ No hand detected. Please show your hand!")
            
            elif key == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n✅ Data collection complete!")
        print(f"Saved {count} images to {sign_dir}")
    
    def collect_all_signs(self, num_per_sign: int = 50):
        """
        Collect data for all signs (A-Z)
        
        Args:
            num_per_sign: Number of images per sign
        """
        signs = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for sign in signs:
            self.collect_data_for_sign(sign, num_per_sign)
            
            if input(f"\nContinue to next sign? (y/n): ").lower() != 'y':
                break
    
    def view_dataset(self):
        """View dataset statistics"""
        print("\n📊 Dataset Statistics")
        print("-" * 40)
        
        total = 0
        for sign_dir in sorted(self.output_dir.iterdir()):
            if sign_dir.is_dir():
                count = len(list(sign_dir.glob("*.jpg")))
                total += count
                bar = "█" * (count // 5)  # Visual bar
                print(f"{sign_dir.name}: {count:3d} images {bar}")
        
        print("-" * 40)
        print(f"Total: {total} images")

if __name__ == "__main__":
    import sys
    
    collector = DataCollector()
    
    print("🎯 Sign Language Data Collector")
    print("=" * 40)
    print("1. Collect data for a specific sign")
    print("2. Collect data for all signs")
    print("3. View dataset statistics")
    print("=" * 40)
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        sign = input("Enter sign letter (A-Z): ").strip()
        num = int(input("Number of images (default 50): ") or "50")
        collector.collect_data_for_sign(sign, num)
    
    elif choice == "2":
        num = int(input("Images per sign (default 50): ") or "50")
        collector.collect_all_signs(num)
    
    elif choice == "3":
        collector.view_dataset()
    
    else:
        print("Invalid choice")
