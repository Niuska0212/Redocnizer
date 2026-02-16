# core/CRNN_inference.py

import os
import numpy as np

# --- 1. CONFIGURACIÓN DE PORTABILIDAD (AMD, NVIDIA, INTEL, CPU) ---
# Forzamos el uso de la implementación estándar de LSTM para máxima compatibilidad.
# Esto evita que el programa busque librerías .dll de NVIDIA que otros usuarios podrían no tener.
os.environ['TF_LSTMS_USE_GPU'] = '0' 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from PySide6.QtCore import QSettings
settings = QSettings("CUCEI", "Redocnizer")
use_gpu = settings.value("use_gpu_acceleration", False, type=bool)

if not use_gpu:
    os.environ['CUDA_VISIBLE_DEVICES'] = ''

import tensorflow as tf

# Silenciar logs internos de Python
tf.get_logger().setLevel('ERROR')

# CRUCIAL: 'soft_device_placement' permite que si el código se ejecuta en una PC
# con hardware distinto, TensorFlow busque la mejor alternativa sin crashear.
tf.config.set_soft_device_placement(True)

if use_gpu:
    try:
        # Detectar cualquier acelerador (DirectML para AMD/Intel o CUDA para NVIDIA)
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            for g in gpus:
                tf.config.experimental.set_memory_growth(g, True)
            print(f"[TF] Aceleración de hardware detectada y configurada.")
    except Exception:
        pass

tf.random.set_seed(42)
np.random.seed(42)

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, BatchNormalization, Reshape, Dense, Bidirectional, LSTM, Dropout
import joblib

# --- CONSTANTES ---
OUTPUT_SEQUENCE_LENGTH = 32 
IMG_HEIGHT = 32
IMG_WIDTH = 256
NUM_CHARS = 84 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_MODELOS = os.path.join(BASE_DIR, "..", "models") 
MODELO_PATH = os.path.join(RUTA_MODELOS, "keras_cnn_lstm_v3_ctc.h5")
VOCAB_PATH = os.path.join(RUTA_MODELOS, "vocabulario_v3.pkl")

def build_pure_inference_model():
    """
    Construye la arquitectura CRNN.
    Usamos configuraciones estándar (sigmoid, glorot) para que el modelo
    se pueda ejecutar en cualquier tarjeta de video del mercado.
    """
    input_img = Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1), name="image", dtype="float32")

    # Bloque extractor de características (CNN)
    x = Conv2D(32, (3, 3), activation="relu", padding="same", name="Conv1")(input_img)
    x = MaxPooling2D((2, 2), name="pool1")(x)
    x = BatchNormalization(name="bn1")(x)

    x = Conv2D(64, (3, 3), activation="relu", padding="same", name="Conv2")(x)
    x = MaxPooling2D((2, 2), name="pool2")(x)
    x = BatchNormalization(name="bn2")(x)

    # Preparar secuencia para la parte Recurrente
    x = Reshape(target_shape=(8, 4096), name="reshape")(x)
    x = Dense(512, activation="relu", name="dense1")(x)
    x = Dropout(0.2)(x)

    # Bloque de lectura secuencial (RNN - LSTM)
    # recurrent_activation='sigmoid' es la clave para la compatibilidad universal.
    x = Bidirectional(LSTM(128, return_sequences=True, recurrent_activation='sigmoid'), name="bidirectional_1")(x)
    x = Bidirectional(LSTM(64, return_sequences=True, recurrent_activation='sigmoid'), name="bidirectional_2")(x)

    # Capa de clasificación de caracteres
    y_pred = Dense(NUM_CHARS + 1, activation="softmax", name="dense_output")(x)

    model = Model(inputs=input_img, outputs=y_pred, name="crnn_inference_model")
    return model

def load_inference_model():
    """Carga los recursos del modelo asegurando que el sistema esté listo."""
    if not os.path.exists(VOCAB_PATH):
        print(f"Error: No se encontró vocabulario en {VOCAB_PATH}")
        return None, None, None
    
    try:
        vocab_data = joblib.load(VOCAB_PATH)
        char_to_index = vocab_data['char_to_index']
        index_to_char = {i: c for c, i in char_to_index.items()}
    except Exception as e:
        print(f"Error cargando vocabulario: {e}")
        return None, None, None

    modelo_inf = build_pure_inference_model()

    if os.path.exists(MODELO_PATH):
        try:
            # skip_mismatch=True por si acaso hay pequeñas variaciones entre versiones de Keras
            modelo_inf.load_weights(MODELO_PATH, by_name=True, skip_mismatch=True)
            print("✅ Inteligencia Artificial cargada (Modo Universal).")
        except Exception as e:
            print(f"⚠️ Error cargando pesos del modelo: {e}")
    else:
        print(f"Error: Archivo de pesos no encontrado en {MODELO_PATH}")
    
    return modelo_inf, index_to_char, OUTPUT_SEQUENCE_LENGTH