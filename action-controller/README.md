# 🎯 Control de Mouse Avanzado con MediaPipe

Sistema de control de mouse mediante gestos de mano utilizando visión por computadora. Controla tu cursor, haz clicks, scroll y más usando solo gestos con las manos detectados por tu cámara web.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.8+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Características

### 🖱️ Funcionalidades de Control
- **Movimiento del cursor** con precisión y suavizado
- **Click izquierdo** y **click derecho**
- **Scroll vertical** bidireccional
- **Drag & Drop** (arrastrar y soltar)
- **Zoom** (zoom in/out)
- **Pausar** temporalmente el control

### 🎛️ Configuración Avanzada
- **Sensibilidad ajustable** (0.1x - 3.0x)
- **Suavizado de movimiento** configurable
- **Calibración de zona de control** personalizada
- **Toggle individual** de cada funcionalidad
- **Interfaz visual** en tiempo real con información del sistema

### 👆 Gestos Soportados
| Gesto | Función | Descripción |
|-------|---------|-------------|
| 👆 **Un dedo (índice)** | Mover cursor | Control básico del puntero |
| 🤏 **Pinza (pulgar + índice)** | Click / Drag & Drop | Click o arrastrar objetos |
| 🖖 **Gesto L** | Click derecho | Menú contextual |
| ✌️ **Dos dedos** | Scroll vertical | Desplazamiento en páginas |
| 🖖 **Tres dedos** | Zoom | Acercar/alejar contenido |
| ✊ **Puño cerrado** | Pausar | Detener movimiento del cursor |
| ✋ **Mano abierta** | Movimiento libre | Control normal del cursor |

## 🚀 Instalación

### Prerrequisitos
- Python 3.7 o superior
- Cámara web conectada
- Sistema operativo: Windows, macOS o Linux

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/control-mouse-gestos.git
cd control-mouse-gestos
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar el programa
```bash
python mouse_controller.py
```

## 🎮 Uso del Sistema

### Inicio Rápido
1. **Ejecuta el programa**
2. **Presiona ESPACIO** para activar el control
3. **Apunta con tu dedo índice** para mover el cursor
4. **Usa diferentes gestos** para diferentes acciones

### Controles de Teclado

#### Controles Básicos
| Tecla | Función |
|-------|---------|
| `ESPACIO` | Activar/pausar control del mouse |
| `Q` | Salir del programa |
| `C` | Calibrar zona de control personalizada |
| `R` | Resetear todas las configuraciones |

#### Ajustes en Tiempo Real
| Tecla | Función |
|-------|---------|
| `S` | Disminuir sensibilidad |
| `A` | Aumentar sensibilidad |
| `F` | Disminuir suavizado |
| `G` | Aumentar suavizado |

#### Toggle de Funcionalidades
| Tecla | Función |
|-------|---------|
| `1` | Activar/desactivar click básico |
| `2` | Activar/desactivar click derecho |
| `3` | Activar/desactivar scroll |
| `4` | Activar/desactivar drag & drop |
| `5` | Activar/desactivar zoom |

### Parámetros de Línea de Comandos
```bash
python mouse_controller.py --sensitivity 1.5 --smoothing 0.8 --camera 0
```

| Parámetro | Descripción | Rango | Default |
|-----------|-------------|-------|---------|
| `--sensitivity` | Sensibilidad de movimiento | 0.1 - 3.0 | 2.0 |
| `--smoothing` | Factor de suavizado | 0.1 - 1.0 | 0.7 |
| `--camera` | Índice de cámara | 0, 1, 2... | 0 |

## 🔧 Configuración Avanzada

### Calibración de Zona de Control
Para mayor precisión, puedes calibrar una zona personalizada:

1. Presiona `C` durante la ejecución
2. Posiciona tu mano en la **esquina superior izquierda** deseada
3. Presiona `ESPACIO` para marcar
4. Posiciona tu mano en la **esquina inferior derecha** deseada
5. Presiona `ESPACIO` para confirmar

### Ajuste de Sensibilidad
- **Sensibilidad baja (0.1-0.8)**: Movimientos más precisos, menor velocidad
- **Sensibilidad media (0.9-1.5)**: Balance entre precisión y velocidad
- **Sensibilidad alta (1.6-3.0)**: Movimientos rápidos, menor precisión

### Ajuste de Suavizado
- **Suavizado bajo (0.1-0.4)**: Respuesta rápida, puede ser irregular
- **Suavizado medio (0.5-0.8)**: Balance recomendado
- **Suavizado alto (0.9-1.0)**: Movimientos muy suaves, respuesta lenta

## 🎯 Consejos de Uso

### Para Mejor Rendimiento
1. **Iluminación**: Usa buena iluminación, evita contraluces
2. **Fondo**: Usa un fondo uniforme y contrastante
3. **Distancia**: Mantén tu mano a 50-80cm de la cámara
4. **Cámara**: Posiciona la cámara a la altura de tu mano
5. **Estabilidad**: Evita movimientos bruscos para mejor detección

### Gestos Efectivos
- **Pinza**: Junta pulgar e índice claramente
- **Gesto L**: Mantén pulgar e índice perpendiculares
- **Scroll**: Usa índice y medio juntos, mueve verticalmente
- **Zoom**: Extiende tres dedos claramente
- **Pausar**: Cierra el puño completamente

### Solución de Problemas Comunes

#### El cursor se mueve demasiado rápido/lento
- Ajusta la sensibilidad con `S` (menos) o `A` (más)

#### Movimientos irregulares del cursor
- Aumenta el suavizado con `G`
- Mejora la iluminación
- Calibra una zona de control con `C`

#### Gestos no se detectan
- Asegúrate de que tu mano esté bien iluminada
- Haz los gestos más pronunciados
- Verifica que las funciones estén activadas (teclas 1-5)

#### FailSafe activado
- El cursor se movió a una esquina de la pantalla
- Presiona `ESPACIO` para reactivar

## 🛠️ Desarrollo

### Estructura del Código
```
mouse_controller.py          # Archivo principal
├── CameraMouseControllerAdvanzado
│   ├── __init__()          # Inicialización y configuración
│   ├── initialize_camera() # Configuración de cámara
│   ├── extraer_puntos_clave_mano() # Extracción de landmarks
│   ├── analizar_gesto_mano() # Análisis de gestos
│   ├── detectar_*()        # Funciones de detección específicas
│   ├── mapear_a_coordenadas_pantalla() # Mapeo de coordenadas
│   ├── realizar_*()        # Funciones de acción del mouse
│   ├── dibujar_interfaz()  # UI visual
│   └── run()               # Loop principal
```

## 📋 Requisitos del Sistema

### Hardware Mínimo
- **Procesador**: Intel i3 o equivalente
- **RAM**: 4 GB
- **Cámara**: Webcam 720p (1080p recomendado)

### Hardware Recomendado
- **Procesador**: Intel i5 o superior
- **RAM**: 8 GB o más
- **Cámara**: Webcam 1080p con buen autoenfoque

## 🤖 Desarrollo Asistido por IA

Este proyecto fue desarrollado con la **asistencia de Inteligencia Artificial** para acelerar el proceso de desarrollo y mejorar la calidad del código:

### 🔧 Áreas donde se utilizó IA:
- **📝 Optimización de algoritmos** de detección de gestos
- **🎯 Mejora de la precisión** en el mapeo de coordenadas
- **⚡ Optimización de rendimiento** y suavizado de movimientos

### 🚧 Estado del Proyecto:
> **Nota**: Este proyecto está en **desarrollo activo** y no está completado al 100%. Se siguen implementando mejoras y nuevas funcionalidades con asistencia de IA para lograr un producto final robusto y profesional.

### 🎭 Transparencia en el Desarrollo:
- **Desarrollo híbrido**: Combinación de conocimiento humano y asistencia de IA
- **Código revisado**: Todo el código ha sido analizado y optimizado
- **Metodología moderna**: Aprovechando herramientas actuales para desarrollo eficiente

## 🙏 Agradecimientos

- **MediaPipe** por el framework de detección de manos
- **OpenCV** por las herramientas de visión por computadora
- **PyAutoGUI** por el control del sistema operativo

⭐ **¡Si te gusta este proyecto, no olvides darle una estrella!** ⭐