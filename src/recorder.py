import mss
import cv2
import numpy as np
import threading
from datetime import datetime
import os
import time
import pywinctl
import platform

# Attempt to import the Windows-specific library
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        from windows_capture import WindowsCapture, Frame, InternalCaptureControl
    except ImportError:
        print("Windows-specific capture library not found. Falling back to MSS.")
        WindowsCapture = None
else:
    WindowsCapture = None

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.output_filename = ""
        self.video_writer = None
        self.target_fps = 30.0

    def get_available_windows(self):
        """Returns a list of window titles and their corresponding objects."""
        windows = pywinctl.getAllWindows()
        return [win for win in windows if win.title and win.isVisible]

    def start_recording(self, window=None):
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
        if window:
            if IS_WINDOWS and WindowsCapture:
                self._record_window_api(window)
            else:
                self._record_window_mss(window)
        else:
            self._record_screen_mss()

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print(f"Recording saved to {self.output_filename}")

    def get_frame(self, window=None):
        """Grabs a single frame. Prefers screen-region capture for previews for simplicity."""
        try:
            with mss.mss() as sct:
                if window:
                    if not window.isAlive or not window.isVisible:
                        return None
                    w, h = window.size
                    if w <= 0 or h <= 0: return None
                    monitor = {"top": window.top, "left": window.left, "width": w, "height": h}
                    sct_img = sct.grab(monitor)
                else:
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception:
            return None

    def _record_window_api(self, window):
        """Records a specific window using the event-driven Windows Graphics Capture API."""
        print("Using modern Windows Graphics Capture API.")
        try:
            capture = WindowsCapture(window_name=window.title)
            w, h = capture.get_width(), capture.get_height()

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, self.target_fps, (w, h))

            @capture.event
            def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
                if not self.is_recording:
                    capture_control.stop()
                    return
                self.video_writer.write(frame.frame_buffer)

            @capture.event
            def on_closed():
                print("Capture session closed.")

            capture.start()
            while self.is_recording:
                time.sleep(0.1)

        except Exception as e:
            print(f"Windows Graphics Capture failed: {e}")
            print("Falling back to screen-region capture method.")
            self._record_window_mss(window)

    def _record_window_mss(self, window):
        """Records a specific window using the MSS screen-region capture method."""
        print("Using cross-platform screen-region capture (MSS).")
        try:
            w, h = window.size
            if w <= 0 or h <= 0: return

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, self.target_fps, (w, h))
            frame_time = 1.0 / self.target_fps

            with mss.mss() as sct:
                monitor = {"top": window.top, "left": window.left, "width": w, "height": h}
                while self.is_recording:
                    frame_start_time = time.time()
                    if not window.isAlive or not window.isVisible: break
                    sct_img = sct.grab(monitor)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    self.video_writer.write(frame)
                    elapsed_time = time.time() - frame_start_time
                    sleep_time = frame_time - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except Exception as e:
            print(f"An error occurred during MSS window recording: {e}")

    def _record_screen_mss(self):
        """Records the entire screen using MSS."""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, self.target_fps, (monitor['width'], monitor['height']))
                frame_time = 1.0 / self.target_fps
                while self.is_recording:
                    frame_start_time = time.time()
                    sct_img = sct.grab(monitor)
                    frame = np.array(sct_img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    self.video_writer.write(frame)
                    elapsed_time = time.time() - frame_start_time
                    sleep_time = frame_time - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except Exception as e:
            print(f"An error occurred during screen recording: {e}")