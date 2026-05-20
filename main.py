import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from engine import TrackingEngine

# App appearance configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class EngelsizErisimUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Engelsiz Erişim - Modern Kafa Kontrol Paneli")
        self.geometry("900x550")
        self.resizable(False, False)

        # Initialize Tracking Engine
        self.engine = TrackingEngine()

        # UI Variables
        self.sag_esik_var = ctk.DoubleVar(value=0.56)
        self.sol_esik_var = ctk.DoubleVar(value=0.44)
        self.asagi_esik_var = ctk.DoubleVar(value=0.60)

        # Update engine thresholds when sliders change
        self.sag_esik_var.trace_add("write", self.update_engine_thresholds)
        self.sol_esik_var.trace_add("write", self.update_engine_thresholds)
        self.asagi_esik_var.trace_add("write", self.update_engine_thresholds)

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT COLUMN: Camera Feed ---
        self.camera_frame = ctk.CTkFrame(self, corner_radius=15)
        self.camera_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.camera_label = ctk.CTkLabel(self.camera_frame, text="Kamera Bekleniyor...", font=("Helvetica", 16))
        self.camera_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- RIGHT COLUMN: Controls ---
        self.control_frame = ctk.CTkFrame(self, width=300, corner_radius=15)
        self.control_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.title_label = ctk.CTkLabel(self.control_frame, text="KONTROL PANELİ", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=(20, 10))

        self.status_badge = ctk.CTkLabel(self.control_frame, text="DURDURULDU", font=("Helvetica", 12, "bold"),
                                         fg_color="#e74c3c", corner_radius=8, width=200, height=30)
        self.status_badge.pack(pady=10)

        self.start_btn = ctk.CTkButton(self.control_frame, text="SİSTEMİ BAŞLAT", font=("Helvetica", 14, "bold"),
                                       fg_color="#2ecc71", hover_color="#27ae60", height=45, command=self.start_system)
        self.start_btn.pack(pady=(20, 10), padx=20, fill="x")

        self.stop_btn = ctk.CTkButton(self.control_frame, text="DURDUR", font=("Helvetica", 14, "bold"),
                                      fg_color="#e74c3c", hover_color="#c0392b", height=45, state="disabled", command=self.stop_system)
        self.stop_btn.pack(pady=10, padx=20, fill="x")

        # Sliders
        self.slider_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.slider_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(self.slider_frame, text="HASSASİYET AYARLARI", font=("Helvetica", 12, "bold")).pack(pady=(0, 10))

        self.create_slider("Sağ Eşik (TAB)", 0.50, 0.70, self.sag_esik_var)
        self.create_slider("Sol Eşik (SHIFT+TAB)", 0.30, 0.50, self.sol_esik_var)
        self.create_slider("Aşağı Eşik (ENTER)", 0.50, 0.80, self.asagi_esik_var)

        self.log_label = ctk.CTkLabel(self.control_frame, text="Hazır", font=("Helvetica", 10, "italic"), text_color="#bdc3c7")
        self.log_label.pack(side="bottom", pady=20)

    def create_slider(self, label, from_val, to_val, variable):
        ctk.CTkLabel(self.slider_frame, text=label, font=("Helvetica", 11)).pack(anchor="w")
        slider = ctk.CTkSlider(self.slider_frame, from_=from_val, to=to_val, variable=variable)
        slider.pack(fill="x", pady=(0, 10))

    def update_engine_thresholds(self, *args):
        self.engine.set_thresholds(self.sag_esik_var.get(), self.sol_esik_var.get(), self.asagi_esik_var.get())

    def update_status(self, status, color, log_text=None):
        self.after(0, lambda: self.status_badge.configure(text=status, fg_color=color))
        if log_text:
            self.after(0, lambda: self.log_label.configure(text=log_text))

    def handle_error(self, message):
        self.update_status("HATA", "#e74c3c", message)
        self.stop_system()

    def start_system(self):
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.update_status("SİSTEM AKTİF", "#2ecc71", "Kamera başlatılıyor...")
        
        self.engine.start(
            on_frame=self.update_camera_frame,
            on_status=self.update_status,
            on_error=self.handle_error
        )

    def stop_system(self):
        self.engine.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.update_status("DURDURULDU", "#e74c3c", "Sistem kapatıldı.")
        self.camera_label.configure(image="", text="Kamera Bekleniyor...")

    def update_camera_frame(self, image):
        # Convert OpenCV image to Tkinter format
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        img = img.resize((580, 435), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Update UI safely
        self.after(0, self._set_image, imgtk)

    def _set_image(self, imgtk):
        if self.engine.sistem_aktif:
            self.camera_label.configure(image=imgtk, text="")
            self.camera_label._image = imgtk

if __name__ == "__main__":
    app = EngelsizErisimUI()
    app.mainloop()
