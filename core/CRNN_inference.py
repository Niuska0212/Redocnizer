# core/CRNN_inference.py

import os
import numpy as np

# --- 1. CONFIGURACIÓN DE PORTABILIDAD Y ESTABILIDAD ---
from PySide6.QtCore import QSettings

# Leemos la configuración ANTES de importar TensorFlow para tener control total
settings = QSettings("CUCEI", "Redocnizer")
use_gpu = settings.value("use_gpu_acceleration", False, type=bool)

# Si el usuario NO activó explícitamente la GPU, forzamos el modo CPU.
# Usamos '-1' y una cadena vacía para asegurar que ninguna capa de abstracción vea la GPU.
if not use_gpu:
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 
    os.environ['TF_LSTMS_USE_GPU'] = '0'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' 
else:
    # Si se usa GPU, forzamos que no reserve toda la memoria de golpe,
    # lo cual a veces causa el error de registro duplicado.
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

# Nivel 3 silencia casi todo excepto errores que detengan el programa
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# IMPORTANTE: Importar tensorflow DESPUÉS de configurar las variables de entorno anteriores
import tensorflow as tf

# Silenciar logs internos de la biblioteca para una terminal limpia
tf.get_logger().setLevel('ERROR')

# 'soft_device_placement' permite que TF elija CPU si la GPU falla o no es compatible
tf.config.set_soft_device_placement(True)

if use_gpu:
    try:
        # Intentamos detectar dispositivos de aceleración (NVIDIA CUDA o DirectML)
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            for g in gpus:
                try:
                    tf.config.experimental.set_memory_growth(g, True)
                except:
                    pass
            print(f"[TF] Aceleración de hardware activada (GPU detectada).")
        else:
            print(f"[TF] GPU solicitada pero no detectada. Usando CPU de forma segura.")
    except Exception as e:
        print(f"[TF] Error al inicializar aceleración: {e}. Revirtiendo a modo CPU.")

# Fijar semillas para que los resultados del OCR sean consistentes
tf.random.set_seed(42)
np.random.seed(42)

from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D, BatchNormalization, 
    Reshape, Dense, Bidirectional, LSTM, Dropout
)
import joblib

# --- CONSTANTES DEL MODELO ---
OUTPUT_SEQUENCE_LENGTH = 32 
IMG_HEIGHT = 32
IMG_WIDTH = 256
NUM_CHARS = 84 

# Localización de archivos de inteligencia artificial
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_MODELOS = os.path.join(BASE_DIR, "..", "models") 
MODELO_PATH = os.path.join(RUTA_MODELOS, "keras_cnn_lstm_v3_ctc.h5")
VOCAB_PATH = os.path.join(RUTA_MODELOS, "vocabulario_v3.pkl")

def build_pure_inference_model():
    """
    Construye la arquitectura CRNN (CNN + RNN).
    Diseñada con capas estándar para funcionar en cualquier procesador o tarjeta.
    """
    # Definimos el input explícitamente como float32 para evitar conversiones automáticas de GPU
    input_img = Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1), name="image", dtype="float32")

    # Bloque 1: Extracción de formas (CNN)
    x = Conv2D(32, (3, 3), activation="relu", padding="same", name="Conv1")(input_img)
    x = MaxPooling2D((2, 2), name="pool1")(x)
    x = BatchNormalization(name="bn1")(x)

    # Bloque 2: Profundización de características
    x = Conv2D(64, (3, 3), activation="relu", padding="same", name="Conv2")(x)
    x = MaxPooling2D((2, 2), name="pool2")(x)
    x = BatchNormalization(name="bn2")(x)

    # Preparación: Convertir mapa de bits a secuencia para la red neuronal recurrente
    x = Reshape(target_shape=(8, 4096), name="reshape")(x)
    x = Dense(512, activation="relu", name="dense1")(x)
    x = Dropout(0.2)(x)

    # Bloque 3: Análisis secuencial (LSTM Bidireccional)
    # recurrent_activation='sigmoid' es vital para compatibilidad entre CPU y distintas GPUs
    x = Bidirectional(LSTM(128, return_sequences=True, recurrent_activation='sigmoid'), name="bidirectional_1")(x)
    x = Bidirectional(LSTM(64, return_sequences=True, recurrent_activation='sigmoid'), name="bidirectional_2")(x)

    # Capa de salida: Clasificador por cada posición de la secuencia
    y_pred = Dense(NUM_CHARS + 1, activation="softmax", name="dense_output")(x)

    model = Model(inputs=input_img, outputs=y_pred, name="crnn_inference_model")
    return model

def load_inference_model():
    """Carga los recursos de IA asegurando que el sistema no crashee por hardware."""
    if not os.path.exists(VOCAB_PATH):
        print(f"Error crítico: No se encontró vocabulario en {VOCAB_PATH}")
        return None, None, None
    
    try:
        vocab_data = joblib.load(VOCAB_PATH)
        char_to_index = vocab_data['char_to_index']
        index_to_char = {i: c for c, i in char_to_index.items()}
    except Exception as e:
        print(f"Error al procesar vocabulario: {e}")
        return None, None, None

    # Construir estructura en memoria
    # El error ocurría aquí porque build_pure_inference_model() gatilla el registro de kernels
    modelo_inf = build_pure_inference_model()

    if os.path.exists(MODELO_PATH):
        try:
            # skip_mismatch=True permite cargar el modelo aunque haya ligeras diferencias de versión
            modelo_inf.load_weights(MODELO_PATH, by_name=True, skip_mismatch=True)
            print("✅ Inteligencia Artificial lista (Modo de compatibilidad total).")
        except Exception as e:
            print(f"⚠️ Error al inyectar pesos al modelo: {e}")
    else:
        print(f"Error crítico: Archivo de pesos .h5 no encontrado.")
    
    return modelo_inf, index_to_char, OUTPUT_SEQUENCE_LENGTH