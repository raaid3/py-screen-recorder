import mss
import cv2
import numpy as np
import threading
from datetime import datetime
import os
import time
import pywinctl

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.output_filename = ""
        self.video_writer = None

    def get_available_windows(self):
        """Returns a list of window titles and their corresponding objects."""
        windows = pywinctl.getAllWindows()
        # Filter out windows with no title or that are not valid for capture
        return [win for win in windows if win.title and win.isvisible]

    def start_recording(self, window=None):
        """Starts the recording on a separate thread."""
        self.is_recording = True
        output_dir = "recordings"
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.now()
        self.output_filename = os.path.join(output_dir, f"rec_{now.strftime('%Y%m%d_%H%M%S')}.mp4")

        self.recording_thread = threading.Thread(target=self.record, args=(window,))
        self.recording_thread.start()
        print("Recording Started")

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join()
            self.recording_thread = None
            print("Recording Stopped")

    def record(self, window=None):
        """Dispatches to the correct recording method."""
        if window:
            self._record_window(window)
        else:
            self._record_screen()

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print(f"Recording saved to {self.output_filename}")

    def get_frame(self, window=None):
        """Grabs a single frame from the specified window or the full screen."""
        try:
            with mss.mss() as sct:
                if window:
                    if not window.isAlive or not window.isVisible:
                        return None
                    
                    w, h = window.size
                    if w <= 0 or h <= 0:
                        return None

                    monitor = {"top": window.top, "left": window.left, "width": w, "height": h}
                    sct_img = sct.grab(monitor)
                else:
                    # Full screen
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)

                frame = np.array(sct_img)
                return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception:
            return None

    def _record_window(self, window):
        """Records a specific window."""
        try:
            # Use the window's box property for dimensions
            # Box is a named tuple: Box(left, top, width, height)
            w, h = window.size

            if w <= 0 or h <= 0:
                print("Window has invalid dimensions (e.g., minimized). Cannot record.")
                return

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, 15.0, (w, h))

            with mss.mss() as sct:
                # Define the monitor region to capture based on the window
                monitor = {"top": window.top, "left": window.left, "width": w, "height": h}
                fps_delay = 1.0 / 15.0

                while self.is_recording:
                    if not window.isAlive or not window.isVisible:
                        print("Window was closed or is no longer visible. Stopping.")
                        break

                    # Grab the data
                    sct_img = sct.grab(monitor)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    self.video_writer.write(frame)
                    time.sleep(fps_delay)

        except Exception as e:
            print(f"An error occurred during window recording: {e}")

    def _record_screen(self):
        """Records the entire screen."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, 20.0, (monitor['width'], monitor['height']))

            while self.is_recording:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                self.video_writer.write(frame)