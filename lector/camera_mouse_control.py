import cv2
import numpy as np
import pyautogui
import time
import threading
from collections import deque
import argparse

class CameraMouseController:
    def __init__(self, sensitivity=20, smoothing_factor=0.3, detection_method='motion'):
        """
        Controlador de mouse usando cámara web
        
        Args:
            sensitivity: Sensibilidad para detección de movimiento (menor = más sensible)
            smoothing_factor: Factor de suavizado del movimiento (0-1)
            detection_method: 'motion' para detección de movimiento, 'hand' para detección de manos
        """
        self.sensitivity = sensitivity
        self.smoothing_factor = smoothing_factor
        self.detection_method = detection_method
        
        # Variables de estado
        self.is_running = False
        self.is_calibrated = False
        self.mouse_enabled = False
        
        # Variables para detección de movimiento
        self.background = None
        self.motion_history = deque(maxlen=5)
        
        # Variables para suavizado
        self.current_x = 0
        self.current_y = 0
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Variables para click por gesto
        self.click_threshold = 1000  # Área mínima para detectar click
        self.click_cooldown = 0.5    # Segundos entre clicks
        self.last_click_time = 0
        
        print("🎯 Controlador de Mouse con Cámara iniciado")
        print(f"📺 Resolución de pantalla: {self.screen_width}x{self.screen_height}")
        print("🎮 Controles:")
        print("  - Espacio: Alternar control del mouse")
        print("  - 'c': Calibrar")
        print("  - 'q': Salir")
        print("  - 's': Ajustar sensibilidad")

    def initialize_camera(self, camera_index=0, width=640, height=480):
        """Inicializar la cámara"""
        try:
            self.cap = cv2.VideoCapture(camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not self.cap.isOpened():
                raise Exception("No se puede abrir la cámara")
            
            # Obtener dimensiones reales
            self.cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"📹 Cámara inicializada: {self.cam_width}x{self.cam_height}")
            return True
            
        except Exception as e:
            print(f"❌ Error al inicializar cámara: {e}")
            return False

    def calibrate_background(self, frames_to_average=30):
        """Calibrar el fondo para detección de movimiento"""
        print("🎯 Calibrando fondo... Mantente fuera del campo de visión")
        
        background_frames = []
        for i in range(frames_to_average):
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                background_frames.append(gray)
                
                # Mostrar progreso
                cv2.putText(frame, f"Calibrando... {i+1}/{frames_to_average}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('Camera Mouse Control', frame)
                cv2.waitKey(100)
        
        if background_frames:
            self.background = np.mean(background_frames, axis=0).astype(np.uint8)
            self.is_calibrated = True
            print("✅ Calibración completada")
        else:
            print("❌ Error en calibración")

    def detect_motion(self, frame):
        """Detectar movimiento en el frame"""
        if self.background is None:
            return None, None
        
        # Preprocesar frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Calcular diferencia con el fondo
        frame_delta = cv2.absdiff(self.background, gray)
        thresh = cv2.threshold(frame_delta, self.sensitivity, 255, cv2.THRESH_BINARY)[1]
        
        # Morfología para limpiar la imagen
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Encontrar el contorno más grande
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > 500:  # Filtrar movimientos muy pequeños
                # Calcular centro del movimiento
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy), area
        
        return None, None

    def detect_hand_landmarks(self, frame):
        """Detectar landmarks de la mano (requiere mediapipe)"""
        try:
            import mediapipe as mp
            
            if not hasattr(self, 'hands'):
                mp_hands = mp.solutions.hands
                self.hands = mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5
                )
                self.mp_drawing = mp.solutions.drawing_utils
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Obtener posición del dedo índice (landmark 8)
                    landmark = hand_landmarks.landmark[8]
                    x = int(landmark.x * self.cam_width)
                    y = int(landmark.y * self.cam_height)
                    
                    # Dibujar landmarks
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    
                    return (x, y), 1000  # Área fija para manos
            
            return None, None
            
        except ImportError:
            print("⚠️  MediaPipe no instalado. Usando detección de movimiento.")
            return self.detect_motion(frame)

    def map_to_screen_coordinates(self, x, y):
        """Mapear coordenadas de cámara a coordenadas de pantalla"""
        # Invertir X para efecto espejo más natural
        screen_x = self.screen_width - (x * self.screen_width // self.cam_width)
        screen_y = y * self.screen_height // self.cam_height
        
        # Aplicar suavizado
        self.current_x += (screen_x - self.current_x) * self.smoothing_factor
        self.current_y += (screen_y - self.current_y) * self.smoothing_factor
        
        return int(self.current_x), int(self.current_y)

    def move_mouse(self, x, y):
        """Mover el mouse a las coordenadas especificadas"""
        try:
            pyautogui.moveTo(x, y)
        except pyautogui.FailSafeException:
            print("🛑 FailSafe activado - mouse movido a esquina")
            self.mouse_enabled = False

    def detect_click_gesture(self, area):
        """Detectar gesto de click basado en área de movimiento"""
        current_time = time.time()
        
        # Click cuando el área es muy grande (mano muy cerca de la cámara)
        if (area > self.click_threshold and 
            current_time - self.last_click_time > self.click_cooldown):
            
            self.last_click_time = current_time
            return True
        
        return False

    def adjust_sensitivity(self, delta):
        """Ajustar sensibilidad de detección"""
        self.sensitivity = max(5, min(50, self.sensitivity + delta))
        print(f"🎛️  Sensibilidad ajustada a: {self.sensitivity}")

    def draw_interface(self, frame, motion_center, area):
        """Dibujar interfaz de usuario en el frame"""
        height, width = frame.shape[:2]
        
        # Panel de estado
        panel_height = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Información de estado
        status_color = (0, 255, 0) if self.mouse_enabled else (0, 0, 255)
        status_text = "ACTIVO" if self.mouse_enabled else "PAUSADO"
        
        cv2.putText(frame, f"Estado: {status_text}", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        cv2.putText(frame, f"Sensibilidad: {self.sensitivity}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(frame, f"Suavizado: {self.smoothing_factor:.1f}", (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if motion_center:
            cv2.putText(frame, f"Pos: ({motion_center[0]}, {motion_center[1]})", (10, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Controles
        controls_y = height - 60
        cv2.putText(frame, "ESPACIO: Toggle | C: Calibrar | S/A: Sensibilidad | Q: Salir", 
                   (10, controls_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Dibujar centro de detección
        if motion_center:
            x, y = motion_center
            cv2.circle(frame, (x, y), 20, (0, 255, 0), 2)
            cv2.line(frame, (x-15, y), (x+15, y), (0, 255, 0), 2)
            cv2.line(frame, (x, y-15), (x, y+15), (0, 255, 0), 2)
            
            # Indicador de click
            if area and area > self.click_threshold:
                cv2.circle(frame, (x, y), 30, (0, 0, 255), 3)
                cv2.putText(frame, "CLICK!", (x-30, y-40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    def run(self):
        """Ejecutar el controlador principal"""
        if not self.initialize_camera():
            return
        
        self.is_running = True
        print("\n🚀 Sistema iniciado. Presiona 'c' para calibrar.")
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Error al leer frame de la cámara")
                    break
                
                # Voltear frame para efecto espejo
                frame = cv2.flip(frame, 1)
                
                motion_center = None
                area = None
                
                # Detectar movimiento o mano según el método seleccionado
                if self.is_calibrated:
                    if self.detection_method == 'hand':
                        motion_center, area = self.detect_hand_landmarks(frame)
                    else:
                        motion_center, area = self.detect_motion(frame)
                    
                    # Mover mouse si está habilitado y hay detección
                    if self.mouse_enabled and motion_center:
                        screen_x, screen_y = self.map_to_screen_coordinates(*motion_center)
                        self.move_mouse(screen_x, screen_y)
                        
                        # Detectar click por gesto
                        if area and self.detect_click_gesture(area):
                            pyautogui.click()
                            print("🖱️  Click!")
                
                # Dibujar interfaz
                self.draw_interface(frame, motion_center, area)
                
                # Mostrar frame
                cv2.imshow('Camera Mouse Control', frame)
                
                # Procesar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    if self.is_calibrated:
                        self.mouse_enabled = not self.mouse_enabled
                        status = "activado" if self.mouse_enabled else "pausado"
                        print(f"🖱️  Control de mouse {status}")
                    else:
                        print("⚠️  Calibra primero presionando 'c'")
                elif key == ord('c'):
                    self.calibrate_background()
                elif key == ord('s'):
                    self.adjust_sensitivity(-5)
                elif key == ord('a'):
                    self.adjust_sensitivity(5)
                elif key == ord('r'):
                    print("🔄 Recalibrando...")
                    self.is_calibrated = False
                    self.mouse_enabled = False
                    
        except KeyboardInterrupt:
            print("\n🛑 Interrupción del usuario")
        
        finally:
            self.cleanup()

    def cleanup(self):
        """Limpiar recursos"""
        self.is_running = False
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()
        print("🧹 Recursos liberados")

def main():
    parser = argparse.ArgumentParser(description='Control de Mouse con Cámara')
    parser.add_argument('--sensitivity', type=int, default=20, 
                       help='Sensibilidad de detección (5-50)')
    parser.add_argument('--smoothing', type=float, default=0.3, 
                       help='Factor de suavizado (0.1-1.0)')
    parser.add_argument('--method', choices=['motion', 'hand'], default='motion',
                       help='Método de detección: motion o hand')
    parser.add_argument('--camera', type=int, default=0, 
                       help='Índice de la cámara')
    
    args = parser.parse_args()
    
    # Validar argumentos
    args.sensitivity = max(5, min(50, args.sensitivity))
    args.smoothing = max(0.1, min(1.0, args.smoothing))
    
    # Crear y ejecutar controlador
    controller = CameraMouseController(
        sensitivity=args.sensitivity,
        smoothing_factor=args.smoothing,
        detection_method=args.method
    )
    
    controller.run()

if __name__ == "__main__":
    main()