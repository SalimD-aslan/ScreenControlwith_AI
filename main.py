import cv2
import mediapipe as mp
import pyautogui
import time
import threading
import customtkinter as ctk
from PIL import Image, ImageTk

# Security measure
pyautogui.FAILSAFE = False

# App appearance configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class EngelsizErisimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Engelsiz Erişim - Modern Kafa Kontrol Paneli")
        self.geometry("900x550")
        self.resizable(False, False)

        # Control Variables
        self.sistem_aktif = False
        self.hareket_kilitli = False
        self.tracking_thread = None
        self.cap = None

        # Threshold Variables (Controlled by Sliders)
        self.sag_esik_var = ctk.DoubleVar(value=0.56)
        self.sol_esik_var = ctk.DoubleVar(value=0.44)
        self.asagi_esik_var = ctk.DoubleVar(value=0.60)

        self.setup_ui()

    def setup_ui(self):
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1) # Camera Column
        self.grid_columnconfigure(1, weight=0) # Control Column
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT COLUMN: Camera Feed ---
        self.camera_frame = ctk.CTkFrame(self, corner_radius=15)
        self.camera_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.camera_label = ctk.CTkLabel(self.camera_frame, text="Kamera Bekleniyor...", font=("Helvetica", 16))
        self.camera_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- RIGHT COLUMN: Controls ---
        self.control_frame = ctk.CTkFrame(self, width=300, corner_radius=15)
        self.control_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Title
        self.title_label = ctk.CTkLabel(self.control_frame, text="KONTROL PANELİ", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=(20, 10))

        # Status Badge
        self.status_badge = ctk.CTkLabel(self.control_frame, text="DURDURULDU", font=("Helvetica", 12, "bold"),
                                         fg_color="#e74c3c", corner_radius=8, width=200, height=30)
        self.status_badge.pack(pady=10)

        # Buttons
        self.start_btn = ctk.CTkButton(self.control_frame, text="SİSTEMİ BAŞLAT", font=("Helvetica", 14, "bold"),
                                       fg_color="#2ecc71", hover_color="#27ae60", height=45, command=self.sistemi_baslat)
        self.start_btn.pack(pady=(20, 10), padx=20, fill="x")

        self.stop_btn = ctk.CTkButton(self.control_frame, text="DURDUR", font=("Helvetica", 14, "bold"),
                                      fg_color="#e74c3c", hover_color="#c0392b", height=45, state="disabled", command=self.sistemi_durdur)
        self.stop_btn.pack(pady=10, padx=20, fill="x")

        # Sliders Section
        self.slider_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.slider_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.slider_frame, text="HASSASİYET AYARLARI", font=("Helvetica", 12, "bold")).pack(pady=(0, 10))

        # Right Threshold
        ctk.CTkLabel(self.slider_frame, text="Sağ Eşik (TAB)", font=("Helvetica", 11)).pack(anchor="w")
        self.sag_slider = ctk.CTkSlider(self.slider_frame, from_=0.50, to=0.70, variable=self.sag_esik_var)
        self.sag_slider.pack(fill="x", pady=(0, 10))

        # Left Threshold
        ctk.CTkLabel(self.slider_frame, text="Sol Eşik (SHIFT+TAB)", font=("Helvetica", 11)).pack(anchor="w")
        self.sol_slider = ctk.CTkSlider(self.slider_frame, from_=0.30, to=0.50, variable=self.sol_esik_var)
        self.sol_slider.pack(fill="x", pady=(0, 10))

        # Down Threshold
        ctk.CTkLabel(self.slider_frame, text="Aşağı Eşik (ENTER)", font=("Helvetica", 11)).pack(anchor="w")
        self.asagi_slider = ctk.CTkSlider(self.slider_frame, from_=0.50, to=0.80, variable=self.asagi_esik_var)
        self.asagi_slider.pack(fill="x", pady=(0, 10))

        # Activity Log
        self.log_label = ctk.CTkLabel(self.control_frame, text="Hazır", font=("Helvetica", 10, "italic"), text_color="#bdc3c7")
        self.log_label.pack(side="bottom", pady=20)

    def update_status(self, status, color, log_text=None):
        self.status_badge.configure(text=status, fg_color=color)
        if log_text:
            self.log_label.configure(text=log_text)

    def sistemi_baslat(self):
        if not self.sistem_aktif:
            self.sistem_aktif = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.update_status("SİSTEM AKTİF", "#2ecc71", "Kamera başlatılıyor...")
            
            self.tracking_thread = threading.Thread(target=self.kafa_takip_dongusu, daemon=True)
            self.tracking_thread.start()

    def sistemi_durdur(self):
        if self.sistem_aktif:
            self.sistem_aktif = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.update_status("DURDURULDU", "#e74c3c", "Sistem kapatıldı.")
            if self.cap:
                self.cap.release()
            self.camera_label.configure(image="", text="Kamera Bekleniyor...")

    def kafa_takip_dongusu(self):
        print("[DEBUG] Thread started")
        mp_face_mesh = mp.solutions.face_mesh
        
        # Try different camera indices and backends
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]
        camera_indices = [0, 1]
        self.cap = None

        print("[DEBUG] Attempting to open camera...")
        for index in camera_indices:
            for backend in backends:
                print(f"[DEBUG] Trying Index: {index}, Backend: {backend}")
                if backend is not None:
                    self.cap = cv2.VideoCapture(index, backend)
                else:
                    self.cap = cv2.VideoCapture(index)
                
                if self.cap.isOpened():
                    # Check if we can actually read a frame
                    ret, _ = self.cap.read()
                    if ret:
                        print(f"[DEBUG] Success with Index: {index}, Backend: {backend}")
                        break
                    else:
                        print(f"[DEBUG] Opened but could not read frame")
                        self.cap.release()
                else:
                    print(f"[DEBUG] Failed to open")
            
            if self.cap and self.cap.isOpened():
                break

        if not self.cap or not self.cap.isOpened():
            print("[DEBUG] ALL CAMERA ATTEMPTS FAILED")
            self.after(0, lambda: self.update_status("HATA", "#e74c3c", "Kamera erişim hatası!"))
            self.sistem_aktif = False
            return

        with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
                                   min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
            
            while self.cap.isOpened() and self.sistem_aktif:
                success, image = self.cap.read()
                if not success:
                    print("[DEBUG] Failed to read frame")
                    break

                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(image_rgb)

                # Get dynamic thresholds
                sag_esik = self.sag_esik_var.get()
                sol_esik = self.sol_esik_var.get()
                asagi_esik = self.asagi_esik_var.get()

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        burun_x = face_landmarks.landmark[1].x
                        burun_y = face_landmarks.landmark[1].y

                        # Draw indicator on the burun point for visual feedback
                        h, w, c = image.shape
                        cx, cy = int(burun_x * w), int(burun_y * h)
                        cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)

                        # Logic
                        if sol_esik <= burun_x <= sag_esik and burun_y < asagi_esik:
                            if self.hareket_kilitli:
                                self.after(0, lambda: self.update_status("SİSTEM AKTİF", "#2ecc71", "Hareket Bekleniyor..."))
                                self.hareket_kilitli = False

                        elif not self.hareket_kilitli:
                            if burun_x > sag_esik:
                                self.after(0, lambda: self.update_status("AKSİYON: SAĞ", "#f1c40f", "İşlem: TAB"))
                                pyautogui.press('tab')
                                self.hareket_kilitli = True
                            
                            elif burun_x < sol_esik:
                                self.after(0, lambda: self.update_status("AKSİYON: SOL", "#f1c40f", "İşlem: SHIFT+TAB"))
                                pyautogui.hotkey('shift', 'tab')
                                self.hareket_kilitli = True
                                
                            elif burun_y > asagi_esik:
                                self.after(0, lambda: self.update_status("AKSİYON: AŞAĞI", "#f1c40f", "İşlem: ENTER"))
                                pyautogui.press('enter')
                                self.hareket_kilitli = True

                # Convert image for Tkinter
                img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                # Resize to fit the label roughly while keeping aspect ratio
                img = img.resize((580, 435), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update UI safely
                self.after(0, self.update_camera_frame, imgtk)

            if self.cap:
                self.cap.release()

    def update_camera_frame(self, imgtk):
        if self.sistem_aktif:
            self.camera_label.configure(image=imgtk, text="")
            self.camera_label._image = imgtk # Keep a reference

if __name__ == "__main__":
    app = EngelsizErisimApp()
    app.mainloop()
