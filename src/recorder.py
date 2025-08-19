import mss
import cv2
import numpy as np
import threading
from datetime import datetime
import os

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.output_filename = ""
        self.video_writer = None

    def start_recording(self):
        self.is_recording = True
        output_dir = "recordings"
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.now()
        self.output_filename = os.path.join(output_dir, f"rec_{now.strftime('%Y%m%d_%H%M%S')}.mp4")

        self.recording_thread = threading.Thread(target=self.record_screen)
        self.recording_thread.start()
        print("Recording Started")

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join()
            self.recording_thread = None
            print("Recording Stopped")

    def record_screen(self):
        with mss.mss() as sct:
            # Use the first monitor
            monitor = sct.monitors[1]
            
            # Create a VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, 20.0, (monitor['width'], monitor['height']))

            while self.is_recording:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                self.video_writer.write(frame)

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print(f"Recording saved to {self.output_filename}")
