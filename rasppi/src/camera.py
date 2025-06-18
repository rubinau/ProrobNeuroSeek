# camera.py
# Module to handle camera access and YOLO detection.
# This version displays a local video feed window for debugging purposes.

import cv2
import time
import threading
import logging
from ultralytics import YOLO

class Camera:
    """
    A self-contained class to manage camera access and run YOLO object detection.
    It provides a method to get the latest list of detected object labels and
    shows a local debug window using cv2.imshow().
    """
    def __init__(self):
        logging.info("Initializing Camera and loading YOLO model...")
        
        # --- YOLO Model Initialization ---
        self.model = YOLO('yolo11n_ncnn_model', task='detect')
        
        # --- Camera Initialization ---
        self.video = cv2.VideoCapture(0) # For live camera
        # self.video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) # WSL2 only
        # self.video = cv2.VideoCapture('test_video.mp4') # For testing with a video file
        if not self.video.isOpened():
            raise RuntimeError("Could not start camera or video file.")
        
        # --- State for Detected Objects ---
        self.detected_objects = []
        self.last_frame_with_overlay = None
        self.lock = threading.Lock()

        # Start a thread to continuously process frames for detection
        self.detection_thread = threading.Thread(target=self._update_detections_loop, daemon=True)
        self.detection_thread.start()
        logging.info("Camera detection thread started.")

    def _update_detections_loop(self):
        """
        [Internal Method] This runs in a separate thread to continuously
        read frames, perform object detection, and show the local debug view.
        """
        while True:
            success, frame = self.video.read()
            if not success:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(1)
                continue

            # --- YOLO DETECTION LOGIC ---
            results = self.model(frame, device='cpu', verbose=False) 
            result = results[0] 
            detected_labels = [result.names[int(c)] for c in result.boxes.cls]

            # --- LOCAL DEBUG VIEW ---
            # Draw the overlay on the frame
            frame_with_overlay = self._draw_overlay(frame.copy(), result)
            
            with self.lock:
                self.detected_objects = list(set(detected_labels))
                self.last_frame_with_overlay = frame_with_overlay

            # Display the resulting frame in a window named 'Robot Debug Feed'
            cv2.imshow('Robot Debug Feed', frame_with_overlay)
            
            # This is crucial for the window to update. It waits for 1ms for a key press.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break # Allow closing the window with 'q'

            time.sleep(0.1) # Control loop speed slightly

        # Clean up the window when the loop breaks
        self.video.release()
        cv2.destroyAllWindows()

    def _draw_overlay(self, frame, result):
        """Draws bounding boxes and labels on the frame."""
        for box in result.boxes:
            x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0]]
            label = result.names[int(box.cls[0])]
            conf = float(box.conf[0])
            label_text = f"{label} {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame


    def get_detected_objects(self):
        """
        Returns the latest list of unique detected object labels.
        """
        with self.lock:
            return self.detected_objects

    def get_confirmation_frame(self):
        with self.lock:
            return self.last_frame_with_overlay

    def __del__(self):
        """Releases the camera resource and closes windows."""
        if self.video:
            self.video.release()
        cv2.destroyAllWindows()

