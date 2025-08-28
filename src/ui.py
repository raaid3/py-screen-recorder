import customtkinter as ctk
from .recorder import Recorder
from PIL import Image, ImageTk
import cv2

class ScreenRecorderUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cross-Platform Screen Recorder")
        self.geometry("1200x800")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State variables
        self.recorder = Recorder()
        self.windows = []
        self.title_to_window = {}
        self.selected_target = ctk.StringVar(value="Full Screen")
        self.is_preview_active = True

        # Layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Side Panel ---
        self.side_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.side_panel.grid(row=0, column=0, sticky='nswe')
        self.side_panel.grid_propagate(False)

        ctk.CTkLabel(self.side_panel, text="Recording Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(20, 10))

        self.record_button = ctk.CTkButton(self.side_panel, text="Record", command=self.toggle_recording)
        self.record_button.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(self.side_panel, text="Recording Target").pack(padx=20, pady=(20, 5), anchor="w")
        self.window_menu = ctk.CTkOptionMenu(self.side_panel, variable=self.selected_target, values=["Full Screen"])
        self.window_menu.pack(padx=20, pady=5, fill="x")

        self.refresh_btn = ctk.CTkButton(self.side_panel, text="Refresh Windows", command=self.refresh_windows_list)
        self.refresh_btn.pack(padx=20, pady=(5, 20), fill="x")

        self.theme_switch = ctk.CTkSwitch(self.side_panel, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.select()
        self.theme_switch.pack(padx=20, pady=20, anchor="w")

        # --- Main Area ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(self.main_area, text="Live Preview will appear here", corner_radius=10, fg_color=("gray85", "gray17"))
        self.preview_label.grid(row=0, column=0, sticky="nswe")

        # Initial setup
        self.refresh_windows_list()
        self.update_preview_loop()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def refresh_windows_list(self):
        self.windows = self.recorder.get_available_windows()
        self.title_to_window = {win.title: win for win in self.windows}
        
        titles = ["Full Screen"] + [win.title for win in self.windows]
        self.window_menu.configure(values=titles)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.is_preview_active = False
            self.preview_label.configure(image=None, text="Preview paused during recording...")
            
            target_title = self.selected_target.get()
            print(f"[DEBUG] UI: Selected target title: '{target_title}'")
            window_to_record = self.title_to_window.get(target_title)
            print(f"[DEBUG] UI: Found window object: {window_to_record}")
            
            self.recorder.start_recording(window=window_to_record)
            self.record_button.configure(text="Stop", fg_color="#DB4437", hover_color="#C53929")
        else:
            self.recorder.stop_recording()
            self.record_button.configure(text="Record", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])
            
            self.is_preview_active = True
            self.update_preview_loop()

    def update_preview_loop(self):
        if not self.is_preview_active:
            self.after(250, self.update_preview_loop)
            return

        target_title = self.selected_target.get()
        window_to_preview = self.title_to_window.get(target_title)

        frame = self.recorder.get_frame(window=window_to_preview)

        if frame is not None:
            label_w, label_h = self.preview_label.winfo_width(), self.preview_label.winfo_height()
            if label_w < 2 or label_h < 2:
                self.after(250, self.update_preview_loop)
                return

            h, w, _ = frame.shape
            scale = min(label_w / w, label_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            resized_frame = cv2.resize(frame, (new_w, new_h))
            
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.preview_label.configure(image=imgtk, text="")
            self.preview_label.image = imgtk
        else:
            self.preview_label.configure(image=None, text="Could not get preview for the selected target.")

        self.after(250, self.update_preview_loop)

    def toggle_theme(self):
        mode = "light" if self.theme_switch.get() == 0 else "dark"
        ctk.set_appearance_mode(mode)

    def on_closing(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        self.destroy()