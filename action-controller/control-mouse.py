import cv2
import numpy as np
import pyautogui
import time
import threading
from collections import deque
import argparse
import mediapipe as mp
import warnings
import os

# Suprimir warnings molestos
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

class CameraMouseControllerAdvanzado:
    def __init__(self, sensitivity=2.0, smoothing_factor=0.7):
        """
        Controlador de mouse avanzado usando MediaPipe para detección de manos
        
        Args:
            sensitivity: Sensibilidad del movimiento (0.1-2.0)
            smoothing_factor: Factor de suavizado del movimiento (0.1-1.0)
        """
        self.sensitivity = sensitivity
        self.smoothing_factor = smoothing_factor
        
        # Inicializar MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # Solo una mano para control más estable
            min_detection_confidence=0.8,
            min_tracking_confidence=0.7
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Variables de estado
        self.is_running = False
        self.mouse_enabled = False
        self.click_mode_enabled = False
        
        # Sistema de seguimiento avanzado
        self.historial_posiciones = deque(maxlen=20)
        self.historial_velocidades = deque(maxlen=10)
        self.tiempo_ultimo_frame = time.time()
        
        # Variables para suavizado de mouse
        self.current_x = 0
        self.current_y = 0
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Variables para detección de clicks y gestos avanzados
        self.ultimo_click_tiempo = 0
        self.click_cooldown = 0.5
        self.umbral_pinza = 0.03  # Distancia para detectar gesto de pinza
        
        # Variables para funcionalidades avanzadas
        self.scroll_enabled = True
        self.drag_drop_enabled = True
        self.zoom_enabled = True
        self.right_click_enabled = True
        
        # Estado de arrastrar y soltar
        self.is_dragging = False
        self.drag_start_pos = None
        
        # Variables para scroll
        self.scroll_cooldown = 0.1
        self.ultimo_scroll_tiempo = 0
        self.scroll_sensitivity = 3
        
        # Variables para zoom
        self.zoom_reference_distance = None
        self.zoom_sensitivity = 50
        
        # Historial para detectar movimientos de scroll
        self.scroll_history = deque(maxlen=5)
        
        # Variables para calibración
        self.zona_calibracion = None
        self.es_calibrado = False
        
        # Configuración de zona de control
        self.margen_zona = 0.1  # 10% de margen en los bordes
        self.zona_control = {
            'x_min': self.margen_zona,
            'x_max': 1.0 - self.margen_zona,
            'y_min': self.margen_zona,
            'y_max': 1.0 - self.margen_zona
        }
        
        print(f"📺 Resolución de pantalla: {self.screen_width}x{self.screen_height}")
        print("")
        print("🎮 Controles básicos:")
        print("  - ESPACIO: Activar/pausar control del mouse")
        print("  - 'c': Calibrar zona de control")
        print("  - 's/a': Ajustar sensibilidad")
        print("  - 'f/g': Ajustar suavizado")
        print("  - 'r': Resetear calibración")
        print("  - 'q': Salir")
        print("")
        print("🎮 Controles de funcionalidades:")
        print("  - '1': Toggle Click básico (pinza)")
        print("  - '2': Toggle Click derecho (gesto L)")
        print("  - '3': Toggle Scroll (2 dedos)")
        print("  - '4': Toggle Drag & Drop (pinza + mover)")
        print("  - '5': Toggle Zoom (3 dedos)")
        print("")
        print("📋 Gestos de control:")
        print("  - 👆 Apuntar (1 dedo): Mover cursor")
        print("  - 🤏 Pinza (pulgar + índice): Click / Drag & Drop")
        print("  - 🖖 Gesto L (pulgar + índice separados): Click derecho")
        print("  - ✌️  Dos dedos (índice + medio): Scroll vertical")
        print("  - 🖖 Tres dedos (índice + medio + anular): Zoom")
        print("  - ✊ Puño cerrado: Pausar movimiento")
        print("  - ✋ Mano abierta: Movimiento libre")

    def initialize_camera(self, camera_index=0, width=1280, height=720):
        """Inicializar la cámara con alta resolución"""
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

    def extraer_puntos_clave_mano(self, hand_landmarks):
        """Extrae puntos clave importantes de la mano"""
        puntos = hand_landmarks.landmark
        
        puntos_clave = {
            'muñeca': [puntos[0].x, puntos[0].y, puntos[0].z],
            'pulgar_tip': [puntos[4].x, puntos[4].y, puntos[4].z],
            'pulgar_ip': [puntos[3].x, puntos[3].y, puntos[3].z],
            'indice_tip': [puntos[8].x, puntos[8].y, puntos[8].z],
            'indice_pip': [puntos[6].x, puntos[6].y, puntos[6].z],
            'medio_tip': [puntos[12].x, puntos[12].y, puntos[12].z],
            'anular_tip': [puntos[16].x, puntos[16].y, puntos[16].z],
            'meñique_tip': [puntos[20].x, puntos[20].y, puntos[20].z],
            'centro_palma': [puntos[9].x, puntos[9].y, puntos[9].z]
        }
        
        return puntos_clave

    def analizar_gesto_mano(self, puntos_clave):
        """Analiza el gesto de la mano para determinar la acción - VERSIÓN AVANZADA"""
        # Calcular si los dedos están extendidos
        dedos_extendidos = self.detectar_dedos_extendidos(puntos_clave)
        
        # Contar dedos extendidos
        num_dedos = sum(dedos_extendidos.values())
        
        # Detectar gestos específicos
        
        # 1. PINZA para click o drag (pulgar + índice juntos)
        if self.detectar_gesto_pinza(puntos_clave):
            return 'pinza'
        
        # 2. GESTO L para click derecho (pulgar + índice en L)
        if self.detectar_gesto_L(puntos_clave):
            return 'click_derecho'
        
        # 3. DOS DEDOS para scroll (índice + medio)
        if dedos_extendidos['indice'] and dedos_extendidos['medio'] and num_dedos == 2:
            return 'scroll'
        
        # 4. TRES DEDOS para zoom (índice + medio + anular)
        if (dedos_extendidos['indice'] and dedos_extendidos['medio'] and 
            dedos_extendidos['anular'] and num_dedos == 3):
            return 'zoom'
        
        # 5. SOLO ÍNDICE para mover cursor
        if dedos_extendidos['indice'] and num_dedos == 1:
            return 'apuntar'
        
        # 6. PUÑO CERRADO para pausar
        if num_dedos <= 1:
            return 'puño'
        
        # 7. MANO ABIERTA para movimiento libre
        if num_dedos >= 4:
            return 'abierta'
        
        # Default
        return 'desconocido'

    def detectar_dedos_extendidos(self, puntos_clave):
        """Detecta qué dedos están extendidos"""
        dedos = {
            'pulgar': False,
            'indice': False,
            'medio': False,
            'anular': False,
            'meñique': False
        }
        
        # Pulgar (comparar X porque se mueve lateralmente)
        if puntos_clave['pulgar_tip'][0] > puntos_clave['pulgar_ip'][0]:
            dedos['pulgar'] = True
        
        # Otros dedos (comparar Y)
        if puntos_clave['indice_tip'][1] < puntos_clave['indice_pip'][1]:
            dedos['indice'] = True
        
        if puntos_clave['medio_tip'][1] < puntos_clave['centro_palma'][1]:
            dedos['medio'] = True
        
        if puntos_clave['anular_tip'][1] < puntos_clave['centro_palma'][1]:
            dedos['anular'] = True
        
        if puntos_clave['meñique_tip'][1] < puntos_clave['centro_palma'][1]:
            dedos['meñique'] = True
        
        return dedos

    def detectar_gesto_pinza(self, puntos_clave):
        """Detecta si se está haciendo gesto de pinza (pulgar e índice juntos)"""
        pulgar = np.array(puntos_clave['pulgar_tip'][:2])
        indice = np.array(puntos_clave['indice_tip'][:2])
        
        distancia = np.linalg.norm(pulgar - indice)
        return distancia < self.umbral_pinza

    def detectar_gesto_L(self, puntos_clave):
        """Detecta gesto en L para click derecho (pulgar e índice perpendiculares)"""
        dedos = self.detectar_dedos_extendidos(puntos_clave)
        
        # Solo pulgar e índice extendidos
        if not (dedos['pulgar'] and dedos['indice'] and 
                sum(dedos.values()) == 2):
            return False
        
        # Verificar que estén separados (no en pinza)
        pulgar = np.array(puntos_clave['pulgar_tip'][:2])
        indice = np.array(puntos_clave['indice_tip'][:2])
        distancia = np.linalg.norm(pulgar - indice)
        
        return distancia > self.umbral_pinza * 2  # Más separados que una pinza

    def detectar_movimiento_scroll(self, puntos_clave):
        """Detecta movimiento vertical para scroll"""
        if len(self.scroll_history) < 3:
            return None
        
        # Usar posición del dedo medio para scroll
        pos_actual = puntos_clave['medio_tip'][1]
        
        # Obtener posiciones previas de forma segura
        posiciones_previas = []
        for i in range(max(0, len(self.scroll_history) - 3), len(self.scroll_history)):
            try:
                if isinstance(self.scroll_history[i], dict) and 'medio_tip' in self.scroll_history[i]:
                    posiciones_previas.append(self.scroll_history[i]['medio_tip'][1])
            except (IndexError, TypeError, KeyError):
                continue
        
        if len(posiciones_previas) < 2:
            return None
        
        # Calcular dirección promedio
        diferencias = []
        for i in range(1, len(posiciones_previas)):
            diferencias.append(posiciones_previas[i] - posiciones_previas[i-1])
        
        if not diferencias:
            return None
        
        movimiento_promedio = np.mean(diferencias)
        
        # Determinar dirección si el movimiento es significativo
        if abs(movimiento_promedio) > 0.005:  # Umbral de sensibilidad
            return 'arriba' if movimiento_promedio < 0 else 'abajo'
        
        return None

    def detectar_zoom_gesture(self, puntos_clave):
        """Detecta gesto de zoom usando separación de dedos"""
        # Usar distancia entre índice y anular como referencia de zoom
        indice = np.array(puntos_clave['indice_tip'][:2])
        anular = np.array(puntos_clave['anular_tip'][:2])
        distancia_actual = np.linalg.norm(indice - anular)
        
        if self.zoom_reference_distance is None:
            self.zoom_reference_distance = distancia_actual
            return None
        
        # Calcular cambio en la distancia
        cambio = distancia_actual - self.zoom_reference_distance
        self.zoom_reference_distance = distancia_actual
        
        # Determinar dirección del zoom
        if abs(cambio) > 0.01:  # Umbral de sensibilidad
            return 'zoom_in' if cambio > 0 else 'zoom_out'
        
        return None

    def calcular_velocidades(self, puntos_actuales):
        """Calcula velocidades de movimiento"""
        if len(self.historial_posiciones) == 0:
            return {'velocidad': 0, 'direccion': [0, 0]}
        
        tiempo_actual = time.time()
        dt = tiempo_actual - self.tiempo_ultimo_frame
        self.tiempo_ultimo_frame = tiempo_actual
        
        if dt == 0:
            return {'velocidad': 0, 'direccion': [0, 0]}
        
        pos_anterior = self.historial_posiciones[-1]['indice_tip'][:2]
        pos_actual = puntos_actuales['indice_tip'][:2]
        
        velocidad_vector = np.array(pos_actual) - np.array(pos_anterior)
        velocidad_magnitud = np.linalg.norm(velocidad_vector) / dt
        
        return {
            'velocidad': velocidad_magnitud,
            'direccion': velocidad_vector.tolist()
        }

    def calibrar_zona_control(self):
        """Calibra la zona de control del mouse"""
        print("\n🎯 CALIBRACIÓN DE ZONA DE CONTROL")
        print("Instrucciones:")
        print("1. Posiciona tu mano en la ESQUINA SUPERIOR IZQUIERDA de tu zona de control")
        print("2. Presiona ESPACIO para marcar")
        print("3. Posiciona tu mano en la ESQUINA INFERIOR DERECHA")
        print("4. Presiona ESPACIO para confirmar")
        print("5. ESC para cancelar")
        
        puntos_calibracion = []
        
        while len(puntos_calibracion) < 2:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    puntos_clave = self.extraer_puntos_clave_mano(hand_landmarks)
                    indice_pos = puntos_clave['indice_tip'][:2]
                    
                    # Dibujar punto de referencia
                    x_pixel = int(indice_pos[0] * frame.shape[1])
                    y_pixel = int(indice_pos[1] * frame.shape[0])
                    cv2.circle(frame, (x_pixel, y_pixel), 10, (0, 255, 0), -1)
            
            # Mostrar instrucciones en pantalla
            instruccion = "Esquina SUPERIOR IZQUIERDA" if len(puntos_calibracion) == 0 else "Esquina INFERIOR DERECHA"
            cv2.putText(frame, f"Posiciona: {instruccion}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Punto {len(puntos_calibracion) + 1}/2 - ESPACIO para marcar", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('Calibración - Control de Mouse', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # Espacio
                if results.multi_hand_landmarks:
                    puntos_clave = self.extraer_puntos_clave_mano(results.multi_hand_landmarks[0])
                    puntos_calibracion.append(puntos_clave['indice_tip'][:2])
                    print(f"✅ Punto {len(puntos_calibracion)} marcado")
                else:
                    print("❌ No se detecta mano")
            elif key == 27:  # ESC
                print("Calibración cancelada")
                cv2.destroyWindow('Calibración - Control de Mouse')
                return
        
        # Procesar calibración
        if len(puntos_calibracion) == 2:
            p1, p2 = puntos_calibracion
            
            self.zona_control = {
                'x_min': min(p1[0], p2[0]),
                'x_max': max(p1[0], p2[0]),
                'y_min': min(p1[1], p2[1]),
                'y_max': max(p1[1], p2[1])
            }
            
            self.es_calibrado = True
            print("✅ Calibración completada!")
            print(f"Zona de control: X({self.zona_control['x_min']:.2f}-{self.zona_control['x_max']:.2f}), "
                  f"Y({self.zona_control['y_min']:.2f}-{self.zona_control['y_max']:.2f})")
        
        cv2.destroyWindow('Calibración - Control de Mouse')

    def mapear_a_coordenadas_pantalla(self, pos_mano):
        """Mapea posición de mano a coordenadas de pantalla - VERSIÓN SIMPLIFICADA"""
        x_mano, y_mano = pos_mano
        
        # Mapeo directo y simple (sin calibración compleja)
        # Movimiento natural: derecha = derecha, izquierda = izquierda
        screen_x = x_mano * self.screen_width
        screen_y = y_mano * self.screen_height
        
        # Aplicar sensibilidad de forma más directa
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Calcular offset desde el centro
        offset_x = (screen_x - center_x) * self.sensitivity
        offset_y = (screen_y - center_y) * self.sensitivity
        
        # Aplicar offset al centro
        final_x = center_x + offset_x
        final_y = center_y + offset_y
        
        # Clampear a los límites de pantalla
        final_x = max(0, min(self.screen_width - 1, final_x))
        final_y = max(0, min(self.screen_height - 1, final_y))
        
        # Aplicar suavizado más agresivo
        self.current_x += (final_x - self.current_x) * self.smoothing_factor
        self.current_y += (final_y - self.current_y) * self.smoothing_factor
        
        # Debug: imprimir valores
        if hasattr(self, 'debug_counter'):
            self.debug_counter += 1
        else:
            self.debug_counter = 0
            
        # Imprimir debug cada 30 frames para no spamear
        if self.debug_counter % 30 == 0:
            print(f"DEBUG: Mano({x_mano:.2f}, {y_mano:.2f}) -> Screen({int(self.current_x)}, {int(self.current_y)})")
        
        return int(self.current_x), int(self.current_y)

    def mover_mouse(self, x, y):
        """Mueve el mouse a las coordenadas especificadas"""
        try:
            pyautogui.moveTo(x, y)
        except pyautogui.FailSafeException:
            print("🛑 FailSafe activado - mouse movido a esquina")
            self.mouse_enabled = False

    def realizar_click(self):
        """Realiza un click izquierdo con cooldown"""
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_click_tiempo > self.click_cooldown:
            pyautogui.click()
            self.ultimo_click_tiempo = tiempo_actual
            print("🖱️ Click izquierdo!")

    def realizar_click_derecho(self):
        """Realiza un click derecho con cooldown"""
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_click_tiempo > self.click_cooldown:
            pyautogui.rightClick()
            self.ultimo_click_tiempo = tiempo_actual
            print("🖱️ Click derecho!")

    def realizar_scroll(self, direccion):
        """Realiza scroll en la dirección especificada"""
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_scroll_tiempo > self.scroll_cooldown:
            if direccion == 'arriba':
                pyautogui.scroll(self.scroll_sensitivity)
                print("📜 Scroll arriba")
            elif direccion == 'abajo':
                pyautogui.scroll(-self.scroll_sensitivity)
                print("📜 Scroll abajo")
            
            self.ultimo_scroll_tiempo = tiempo_actual

    def iniciar_drag(self, posicion):
        """Inicia operación de arrastrar"""
        if not self.is_dragging:
            self.is_dragging = True
            self.drag_start_pos = posicion
            pyautogui.mouseDown()
            print("🤏 Iniciando arrastre...")

    def terminar_drag(self):
        """Termina operación de arrastrar"""
        if self.is_dragging:
            self.is_dragging = False
            self.drag_start_pos = None
            pyautogui.mouseUp()
            print("🤏 Arrastre terminado!")

    def realizar_zoom(self, tipo_zoom):
        """Realiza zoom usando combinaciones de teclas"""
        if tipo_zoom == 'zoom_in':
            pyautogui.hotkey('ctrl', '+')
            print("🔍 Zoom in")
        elif tipo_zoom == 'zoom_out':
            pyautogui.hotkey('ctrl', '-')
            print("🔍 Zoom out")

    def ajustar_sensibilidad(self, delta):
        """Ajusta la sensibilidad"""
        self.sensitivity = max(0.1, min(3.0, self.sensitivity + delta))
        print(f"🎛️ Sensibilidad: {self.sensitivity:.1f}")

    def ajustar_suavizado(self, delta):
        """Ajusta el factor de suavizado"""
        self.smoothing_factor = max(0.1, min(1.0, self.smoothing_factor + delta))
        print(f"🎛️ Suavizado: {self.smoothing_factor:.1f}")

    def dibujar_zona_control(self, frame):
        """Dibuja la zona de control en el frame"""
        if not self.es_calibrado:
            return
        
        altura, ancho = frame.shape[:2]
        
        x1 = int(self.zona_control['x_min'] * ancho)
        y1 = int(self.zona_control['y_min'] * altura)
        x2 = int(self.zona_control['x_max'] * ancho)
        y2 = int(self.zona_control['y_max'] * altura)
        
        # Dibujar rectángulo de zona de control
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(frame, "ZONA DE CONTROL", (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    def dibujar_interfaz(self, frame, results=None, gesto=None, posicion_mouse=None):
        """Dibuja la interfaz de usuario"""
        altura, ancho = frame.shape[:2]
        
        # Panel de estado con fondo más grande
        panel_height = 200
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (ancho, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Estado del sistema
        estado_color = (0, 255, 0) if self.mouse_enabled else (0, 0, 255)
        estado_texto = "🟢 ACTIVO - Moviendo cursor" if self.mouse_enabled else "🔴 PAUSADO - Presiona ESPACIO"
        cv2.putText(frame, estado_texto, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, estado_color, 2)
        
        # Configuración actual
        cv2.putText(frame, f"Sensibilidad: {self.sensitivity:.1f}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Suavizado: {self.smoothing_factor:.1f}", (200, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Estado de funcionalidades - Línea 1
        funciones_y = 75
        cv2.putText(frame, "Funciones:", (10, funciones_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Click básico
        click_color = (0, 255, 0) if self.click_mode_enabled else (100, 100, 100)
        cv2.putText(frame, f"Click:{self.click_mode_enabled}", (100, funciones_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, click_color, 1)
        
        # Click derecho
        right_color = (0, 255, 0) if self.right_click_enabled else (100, 100, 100)
        cv2.putText(frame, f"R-Click:{self.right_click_enabled}", (200, funciones_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, right_color, 1)
        
        # Scroll
        scroll_color = (0, 255, 0) if self.scroll_enabled else (100, 100, 100)
        cv2.putText(frame, f"Scroll:{self.scroll_enabled}", (320, funciones_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, scroll_color, 1)
        
        # Línea 2 de funciones
        funciones_y2 = 95
        # Drag & Drop
        drag_color = (0, 255, 0) if self.drag_drop_enabled else (100, 100, 100)
        cv2.putText(frame, f"Drag&Drop:{self.drag_drop_enabled}", (100, funciones_y2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, drag_color, 1)
        
        # Zoom
        zoom_color = (0, 255, 0) if self.zoom_enabled else (100, 100, 100)
        cv2.putText(frame, f"Zoom:{self.zoom_enabled}", (250, funciones_y2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, zoom_color, 1)
        
        # Estado de arrastre
        if self.is_dragging:
            cv2.putText(frame, "🤏 ARRASTRANDO", (350, funciones_y2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Estado de calibración
        calibracion_estado = "✅ Calibrado" if self.es_calibrado else "⚠️ Sin calibrar"
        cv2.putText(frame, calibracion_estado, (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if self.es_calibrado else (0, 255, 255), 1)
        
        # Gesto actual con colores específicos
        if gesto:
            gesto_colors = {
                'apuntar': (0, 255, 0),
                'pinza': (255, 0, 0),
                'click_derecho': (255, 100, 0),
                'scroll': (0, 255, 255),
                'zoom': (255, 0, 255),
                'puño': (255, 255, 0),
                'abierta': (255, 255, 255),
                'desconocido': (100, 100, 100)
            }
            
            gesto_color = gesto_colors.get(gesto, (255, 255, 255))
            gesto_texto = {
                'apuntar': '👆 APUNTAR',
                'pinza': '🤏 PINZA',
                'click_derecho': '🖖 CLICK DERECHO',
                'scroll': '✌️ SCROLL',
                'zoom': '🖖 ZOOM',
                'puño': '✊ PUÑO',
                'abierta': '✋ ABIERTA',
                'desconocido': '❓ DESCONOCIDO'
            }.get(gesto, gesto.upper())
            
            cv2.putText(frame, f"Gesto: {gesto_texto}", (10, 145), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, gesto_color, 2)
        
        # Posición del mouse
        if posicion_mouse:
            cv2.putText(frame, f"Mouse: ({posicion_mouse[0]}, {posicion_mouse[1]})", 
                       (200, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostrar posición de mano también
            if results and results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                puntos_clave = self.extraer_puntos_clave_mano(hand_landmarks)
                pos_indice = puntos_clave['indice_tip'][:2]
                cv2.putText(frame, f"Mano: ({pos_indice[0]:.2f}, {pos_indice[1]:.2f})", 
                           (200, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Controles en la parte inferior - Línea 1
        controles_y1 = altura - 60
        cv2.putText(frame, "ESPACIO:Toggle | C:Calibrar | S/A:Sens | F/G:Suav | R:Reset | Q:Salir", 
                   (10, controles_y1), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Controles en la parte inferior - Línea 2  
        controles_y2 = altura - 40
        cv2.putText(frame, "1:Click | 2:R-Click | 3:Scroll | 4:Drag&Drop | 5:Zoom", 
                   (10, controles_y2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        # Controles en la parte inferior - Línea 3
        controles_y3 = altura - 20
        cv2.putText(frame, "Gestos: 👆=Mover | 🤏=Click/Drag | 🖖=R-Click | ✌️=Scroll | 🖖=Zoom | ✊=Pausa", 
                   (10, controles_y3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        
        # Dibujar zona de control
        self.dibujar_zona_control(frame)

    def procesar_deteccion_mano(self, results, frame):
        """Procesa la detección de manos y ejecuta acciones"""
        if not results.multi_hand_landmarks:
            return None, None
        
        # Usar solo la primera mano detectada
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Dibujar landmarks
        self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        # Extraer puntos clave
        puntos_clave = self.extraer_puntos_clave_mano(hand_landmarks)
        
        # Analizar gesto
        gesto = self.analizar_gesto_mano(puntos_clave)
        
        # Actualizar historial
        self.historial_posiciones.append(puntos_clave)
        
        # Calcular velocidades
        velocidades = self.calcular_velocidades(puntos_clave)
        
        # Procesar según el gesto - VERSIÓN AVANZADA CON TODAS LAS FUNCIONALIDADES
        posicion_mouse = None
        
        if self.mouse_enabled:
            # Siempre mover el mouse usando posición del índice
            pos_indice = puntos_clave['indice_tip'][:2]
            posicion_mouse = self.mapear_a_coordenadas_pantalla(pos_indice)
            
            # Procesar según el gesto detectado
            if gesto == 'pinza':
                # DRAG AND DROP: Iniciar/continuar arrastre
                if self.drag_drop_enabled:
                    if not self.is_dragging:
                        self.iniciar_drag(posicion_mouse)
                    # Continuar moviendo mientras se arrastra
                    self.mover_mouse(*posicion_mouse)
                else:
                    # Si drag&drop está deshabilitado, hacer click normal
                    if self.click_mode_enabled:
                        self.realizar_click()
                        
            elif gesto == 'click_derecho':
                # CLICK DERECHO
                if self.right_click_enabled:
                    self.realizar_click_derecho()
                    
            elif gesto == 'scroll':
                # SCROLL: Detectar movimiento vertical
                if self.scroll_enabled:
                    self.scroll_history.append(puntos_clave)
                    direccion_scroll = self.detectar_movimiento_scroll(puntos_clave)
                    if direccion_scroll:
                        self.realizar_scroll(direccion_scroll)
                # Mover cursor también durante scroll
                self.mover_mouse(*posicion_mouse)
                
            elif gesto == 'zoom':
                # ZOOM: Detectar cambio en separación de dedos
                if self.zoom_enabled:
                    tipo_zoom = self.detectar_zoom_gesture(puntos_clave)
                    if tipo_zoom:
                        self.realizar_zoom(tipo_zoom)
                # Mover cursor también durante zoom
                self.mover_mouse(*posicion_mouse)
                
            elif gesto in ['apuntar', 'abierta']:
                # MOVIMIENTO NORMAL: Solo mover cursor
                # Terminar drag si estaba activo
                if self.is_dragging:
                    self.terminar_drag()
                self.mover_mouse(*posicion_mouse)
                
            elif gesto == 'puño':
                # PUÑO: Pausar movimiento pero terminar drag si está activo
                if self.is_dragging:
                    self.terminar_drag()
                # No mover el cursor cuando es puño
                
            else:  # gesto desconocido
                # Mover cursor por defecto
                if self.is_dragging:
                    self.terminar_drag()
                self.mover_mouse(*posicion_mouse)
        
        return gesto, posicion_mouse

    def run(self):
        """Ejecuta el controlador principal"""
        if not self.initialize_camera():
            return
        
        self.is_running = True
        print("👆 PARA EMPEZAR:")
        print("   1. Presiona ESPACIO para ACTIVAR el control")
        print("   2. Usa gestos con tu mano:")
        print("      👆 UN DEDO (índice) = Mover cursor")
        print("      🤏 PINZA (pulgar + índice juntos) = Click / Arrastrar")
        print("      🖖 GESTO L (pulgar + índice separados) = Click derecho")
        print("      ✌️  DOS DEDOS (índice + medio) = Scroll vertical")
        print("      🖖 TRES DEDOS (índice + medio + anular) = Zoom")
        print("      ✊ PUÑO CERRADO = Pausar movimiento")
        print()
        print("🎛️ CONTROLES RÁPIDOS:")
        print("   Teclas 1-5 para activar/desactivar funciones")
        print("   S/A para sensibilidad, F/G para suavizado")
        print("   C para calibrar zona personalizada")
        print()
        if not self.es_calibrado:
            print("💡 OPCIONAL: Presiona 'c' para calibrar zona de control personalizada")
        print("🐛 DEBUG: Verás mensajes en consola con cada acción")
        print()
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Error al leer frame de la cámara")
                    break
                
                # Voltear frame para efecto espejo
                frame = cv2.flip(frame, 1)
                
                # Procesar con MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                # Procesar detección de manos
                gesto, posicion_mouse = self.procesar_deteccion_mano(results, frame)
                
                # Dibujar interfaz
                self.dibujar_interfaz(frame, results, gesto, posicion_mouse)
                
                # Mostrar frame
                cv2.imshow('Control de Mouse Avanzado - MediaPipe', frame)
                
                # Procesar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == 32:  # Espacio
                    self.mouse_enabled = not self.mouse_enabled
                    estado = "activado" if self.mouse_enabled else "pausado"
                    print(f"🖱️ Control de mouse {estado}")
                elif key == ord('c'):
                    self.calibrar_zona_control()
                    
                # Funcionalidades (teclas numéricas)
                elif key == ord('1'):
                    self.click_mode_enabled = not self.click_mode_enabled
                    estado = "activado" if self.click_mode_enabled else "desactivado"
                    print(f"🖱️ Click básico {estado}")
                elif key == ord('2'):
                    self.right_click_enabled = not self.right_click_enabled
                    estado = "activado" if self.right_click_enabled else "desactivado"
                    print(f"🖱️ Click derecho {estado}")
                elif key == ord('3'):
                    self.scroll_enabled = not self.scroll_enabled
                    estado = "activado" if self.scroll_enabled else "desactivado"
                    print(f"📜 Scroll {estado}")
                elif key == ord('4'):
                    self.drag_drop_enabled = not self.drag_drop_enabled
                    estado = "activado" if self.drag_drop_enabled else "desactivado"
                    print(f"🤏 Drag & Drop {estado}")
                elif key == ord('5'):
                    self.zoom_enabled = not self.zoom_enabled
                    estado = "activado" if self.zoom_enabled else "desactivado"
                    print(f"🔍 Zoom {estado}")
                    
                # Ajustes
                elif key == ord('s'):
                    self.ajustar_sensibilidad(-0.1)
                elif key == ord('a'):
                    self.ajustar_sensibilidad(0.1)
                elif key == ord('f'):
                    self.ajustar_suavizado(-0.1)
                elif key == ord('g'):
                    self.ajustar_suavizado(0.1)
                elif key == ord('r'):
                    self.es_calibrado = False
                    self.zoom_reference_distance = None
                    self.is_dragging = False
                    self.zona_control = {
                        'x_min': self.margen_zona,
                        'x_max': 1.0 - self.margen_zona,
                        'y_min': self.margen_zona,
                        'y_max': 1.0 - self.margen_zona
                    }
                    print("🔄 Sistema reseteado completamente")
        
        except KeyboardInterrupt:
            print("\n🛑 Interrupción del usuario")
        
        finally:
            self.cleanup()

    def cleanup(self):
        """Limpia recursos y estados"""
        self.is_running = False
        
        # Terminar cualquier operación de drag pendiente
        if self.is_dragging:
            try:
                pyautogui.mouseUp()
                print("🤏 Terminando arrastre pendiente...")
            except:
                pass
        
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()
        print("🧹 Recursos liberados")


def main():
    parser = argparse.ArgumentParser(description='Control de Mouse Avanzado con MediaPipe')
    parser.add_argument('--sensitivity', type=float, default=2.0, 
                       help='Sensibilidad de movimiento (0.1-3.0)')
    parser.add_argument('--smoothing', type=float, default=0.7, 
                       help='Factor de suavizado (0.1-1.0)')
    parser.add_argument('--camera', type=int, default=0, 
                       help='Índice de la cámara')
    
    args = parser.parse_args()
    
    # Validar argumentos
    args.sensitivity = max(0.1, min(3.0, args.sensitivity))
    args.smoothing = max(0.1, min(1.0, args.smoothing))
    
    print("=" * 50)
    print("Dependencias requeridas:")
    print("pip install opencv-python mediapipe pyautogui numpy")
    print("=" * 50)
    
    try:
        controller = CameraMouseControllerAdvanzado(
            sensitivity=args.sensitivity,
            smoothing_factor=args.smoothing
        )
        
        controller.run()
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Instala las dependencias con:")
        print("pip install opencv-python mediapipe pyautogui numpy")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()