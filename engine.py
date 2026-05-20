import cv2
import mediapipe as mp
import pyautogui
import threading
import time

class TrackingEngine:
    def __init__(self):
        self.sistem_aktif = False
        self.hareket_kilitli = False
        self.cap = None
        
        # Thresholds
        self.sag_esik = 0.56
        self.sol_esik = 0.44
        self.asagi_esik = 0.60
        
        # Callbacks
        self.on_frame_callback = None
        self.on_status_callback = None
        self.on_error_callback = None

    def set_thresholds(self, sag, sol, asagi):
        self.sag_esik = sag
        self.sol_esik = sol
        self.asagi_esik = asagi

    def start(self, on_frame, on_status, on_error):
        self.on_frame_callback = on_frame
        self.on_status_callback = on_status
        self.on_error_callback = on_error
        
        if not self.sistem_aktif:
            self.sistem_aktif = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.sistem_aktif = False
        if self.cap:
            self.cap.release()

    def _run(self):
        mp_face_mesh = mp.solutions.face_mesh
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]
        camera_indices = [0, 1]
        self.cap = None

        for index in camera_indices:
            for backend in backends:
                if backend is not None:
                    self.cap = cv2.VideoCapture(index, backend)
                else:
                    self.cap = cv2.VideoCapture(index)
                
                if self.cap.isOpened():
                    ret, _ = self.cap.read()
                    if ret: break
                    else: self.cap.release()
            if self.cap and self.cap.isOpened(): break

        if not self.cap or not self.cap.isOpened():
            if self.on_error_callback:
                self.on_error_callback("Kamera erişim hatası!")
            self.sistem_aktif = False
            return

        with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False, 
                                   min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
            
            while self.cap.isOpened() and self.sistem_aktif:
                success, image = self.cap.read()
                if not success: break

                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(image_rgb)

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        burun_x = face_landmarks.landmark[1].x
                        burun_y = face_landmarks.landmark[1].y

                        h, w, _ = image.shape
                        cx, cy = int(burun_x * w), int(burun_y * h)
                        cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)

                        if self.sol_esik <= burun_x <= self.sag_esik and burun_y < self.asagi_esik:
                            if self.hareket_kilitli:
                                if self.on_status_callback:
                                    self.on_status_callback("SİSTEM AKTİF", "#2ecc71", "Hareket Bekleniyor...")
                                self.hareket_kilitli = False

                        elif not self.hareket_kilitli:
                            if burun_x > self.sag_esik:
                                if self.on_status_callback:
                                    self.on_status_callback("AKSİYON: SAĞ", "#f1c40f", "İşlem: TAB")
                                pyautogui.press('tab')
                                self.hareket_kilitli = True
                            
                            elif burun_x < self.sol_esik:
                                if self.on_status_callback:
                                    self.on_status_callback("AKSİYON: SOL", "#f1c40f", "İşlem: SHIFT+TAB")
                                pyautogui.hotkey('shift', 'tab')
                                self.hareket_kilitli = True
                                
                            elif burun_y > self.asagi_esik:
                                if self.on_status_callback:
                                    self.on_status_callback("AKSİYON: AŞAĞI", "#f1c40f", "İşlem: ENTER")
                                pyautogui.press('enter')
                                self.hareket_kilitli = True

                if self.on_frame_callback:
                    self.on_frame_callback(image)

            if self.cap:
                self.cap.release()
