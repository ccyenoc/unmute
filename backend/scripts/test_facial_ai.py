"""
Live Facial AI Webcam Demo
Simple real-time demonstration of facial emotion and linguistic expression detection.
"""

import cv2
import sys
import os
import time
import logging

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.emotion_detector import FacialAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_live_demo(duration_seconds: int = 60):
    """
    Run a live demo of facial AI analysis.
    
    Args:
        duration_seconds: How long to run the demo (0 = unlimited)
    """
    logger.info("Initializing FacialAI...")
    ai = FacialAI(enable_smoothing=True)
    
    logger.info("Opening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Cannot open webcam!")
        return
    
    logger.info("Webcam opened. Press 'q' to quit.")
    logger.info(f"Running for {duration_seconds}s (0 = unlimited)")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame")
                break
            
            # Resize for faster processing
            frame = cv2.resize(frame, (640, 480))
            frame_count += 1
            
            # Run analysis
            start_analyze = time.time()
            result = ai.analyze_frame(frame)
            analyze_time = time.time() - start_analyze
            
            # Extract results
            emotion = result['emotion']
            emotion_conf = result['emotion_confidence']
            expression = result['linguistic_expression']
            expr_conf = result['linguistic_confidence']
            faces = result['faces_detected']
            
            # Display information
            y_offset = 30
            info_texts = [
                f"Emotion: {emotion} ({emotion_conf:.2f})",
                f"Expression: {expression} ({expr_conf:.2f})",
                f"Faces detected: {faces}",
                f"Processing time: {analyze_time*1000:.1f}ms",
                f"Frame: {frame_count}",
            ]
            
            # Show all emotions if no face detected
            if not result['success']:
                info_texts.append("❌ No face detected")
            
            # Draw text
            for i, text in enumerate(info_texts):
                color = (0, 255, 0) if result['success'] else (0, 0, 255)
                cv2.putText(
                    frame,
                    text,
                    (10, y_offset + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )
            
            # Display frame
            cv2.imshow('FacialAI Live Demo', frame)
            
            # Check for quit or timeout
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("Quit requested")
                break
            
            if duration_seconds > 0 and time.time() - start_time > duration_seconds:
                logger.info(f"Duration limit ({duration_seconds}s) reached")
                break
    
    except Exception as e:
        logger.error(f"Error during demo: {str(e)}", exc_info=True)
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Print statistics
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        stats = ai.get_statistics()
        
        logger.info("\n" + "="*60)
        logger.info("DEMO STATISTICS")
        logger.info("="*60)
        logger.info(f"Total frames: {frame_count}")
        logger.info(f"Elapsed time: {elapsed:.1f}s")
        logger.info(f"Average FPS: {fps:.1f}")
        logger.info(f"Face detection rate: {stats['detection_rate']*100:.1f}%")
        logger.info("="*60)


if __name__ == "__main__":
    # Run demo for 60 seconds (or until 'q' is pressed)
    run_live_demo(duration_seconds=60)