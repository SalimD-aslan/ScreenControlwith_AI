import cv2
import mediapipe as mp
import pyautogui
import time
import threading
import tkinter as tk
from tkinter import ttk

# Güvenlik önlemi
pyautogui.FAILSAFE = False

class EngelsizErisimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Engelsiz Erişim - Kafa Kontrol Paneli")
        self.root.geometry("450x300")
        self.root.configure(bg="#2c3e50")
        self.root.resizable(False, False)

        # Kontrol Değişkenleri
        self.sistem_aktif = False
        self.hareket_kilitli = False
        self.tracking_thread = None

        # Varsayılan Hassasiyet Ayarları
        self.SAG_ESIK = 0.56
        self.SOL_ESIK = 0.44
        self.ASAGI_ESIK = 0.60

        # Arayüz Elemanlarını Oluştur
        self.arayuz_tasarla()

    def arayuz_tasarla(self):
        # Başlık
        title_label = tk.Label(self.root, text="ENGELSİZ ERİŞİM SİSTEMİ", font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="#ecf0f1")
        title_label.pack(pady=20)

        # Durum Göstergesi
        self.status_label = tk.Label(self.root, text="Sistem: KAPALI", font=("Helvetica", 12, "bold"), bg="#2c3e50", fg="#e74c3c")
        self.status_label.pack(pady=10)

        # Bilgilendirme Notu
        info_label = tk.Label(self.root, text="Sistemi başlattıktan sonra bu pencereyi simge durumuna\nalıp masaüstünde kafa hareketlerinizle gezinebilirsiniz.", 
                             font=("Helvetica", 10, "italic"), bg="#2c3e50", fg="#bdc3c7")
        info_label.pack(pady=10)

        # Butonlar İçin Çerçeve
        btn_frame = tk.Frame(self.root, bg="#2c3e50")
        btn_frame.pack(pady=20)

        # Başlat Butonu
        self.start_btn = tk.Button(btn_frame, text="SİSTEMİ BAŞLAT", font=("Helvetica", 11, "bold"), bg="#2ecc71", fg="white", 
                                   width=15, height=2, command=self.sistemi_baslat)
        self.start_btn.grid(row=0, column=0, padx=10)

        # Durdur Butonu
        self.stop_btn = tk.Button(btn_frame, text="DURDUR", font=("Helvetica", 11, "bold"), bg="#e74c3c", fg="white", 
                                  width=15, height=2, command=self.sistemi_durdur, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10)

    def sistemi_baslat(self):
        if not self.sistem_aktif:
            self.sistem_aktif = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Sistem: AKTİF (Hareket Bekleniyor)", fg="#2ecc71")
            
            # Arka planda kamerayı kilitlemeden çalışması için Thread başlatıyoruz
            self.tracking_thread = threading.Thread(target=self.kafa_takip_dongusu, daemon=True)
            self.tracking_thread.start()

    def sistemi_durdur(self):
        if self.sistem_aktif:
            self.sistem_aktif = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Sistem: KAPALI", fg="#e74c3c")

    def kafa_takip_dongusu(self):
        mp_face_mesh = mp.solutions.face_mesh
        cap = cv2.VideoCapture(0)

        with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
                                   min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
            
            # Kullanıcı uygulamayı durdurana kadar döngü çalışır
            while cap.isOpened() and self.sistem_aktif:
                success, image = cap.read()
                if not success:
                    break

                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(image_rgb)

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        burun_x = face_landmarks.landmark[1].x
                        burun_y = face_landmarks.landmark[1].y

                        # --- KİLİT MEKANİZMASI ---
                        if self.SOL_ESIK <= burun_x <= self.SAG_ESIK and burun_y < self.ASAGI_ESIK:
                            if self.hareket_kilitli:
                                self.status_label.config(text="Sistem: HAZIR (Hareket Bekleniyor)", fg="#2ecc71")
                                self.hareket_kilitli = False

                        elif not self.hareket_kilitli:
                            # Sağa Dönüş -> TAB
                            if burun_x > self.SAG_ESIK:
                                self.status_label.config(text="Son İşlem: SAĞ (TAB)", fg="#f1c40f")
                                pyautogui.press('tab')
                                self.hareket_kilitli = True
                            
                            # Sola Dönüş -> SHIFT+TAB
                            elif burun_x < self.SOL_ESIK:
                                self.status_label.config(text="Son İşlem: SOL (SHIFT+TAB)", fg="#f1c40f")
                                pyautogui.hotkey('shift', 'tab')
                                self.hareket_kilitli = True
                                
                            # Aşağı Eğilme -> ENTER
                            elif burun_y > self.ASAGI_ESIK:
                                self.status_label.config(text="Son İşlem: AŞAĞI (ENTER)", fg="#f1c40f")
                                pyautogui.press('enter')
                                self.hareket_kilitli = True

                # Görsel pencereyi artık gizliyoruz veya test için açık tutabilirsin. 
                # Jüri sunumunda kamerayı görmek isterlerse alttaki iki satırı aktif bırakabilirsin.
                cv2.imshow('Kamera Arkaplan Akisi', image)
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()

# Uygulamayı çalıştır
if __name__ == "__main__":
    root = tk.Tk()
    app = EngelsizErisimApp(root)
    root.mainloop()