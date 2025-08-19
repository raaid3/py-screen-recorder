import customtkinter as ctk
from .recorder import Recorder


class ScreenRecorderUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cross Platform Screen Recorder")
        self.geometry("800x500")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.side_panel = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.side_panel.grid(row=0, column=0, sticky='nswe')
        self.side_panel.grid_propagate(False)
        self.side_panel.grid_rowconfigure(4, weight=1)

        self.recorder = Recorder()

        self.record_button = ctk.CTkButton(
            self.side_panel,
            text="Record",
            command=self.toggle_recording
        )
        self.record_button.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.theme_switch = ctk.CTkSwitch(
            self.side_panel,
            text="Dark Mode",
            command=self.toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.grid(row=1, column=0, padx=20, pady=10)

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nswe")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.recorder.start_recording()
            self.record_button.configure(text="Stop")
        else:
            self.recorder.stop_recording()
            self.record_button.configure(text="Record")

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Light Mode")

    def on_closing(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        self.destroy()