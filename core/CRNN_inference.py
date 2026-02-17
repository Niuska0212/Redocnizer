# core/CRNN_inference.py

import os
import numpy as np

# --- 1. CONFIGURACIÓN DE PORTABILIDAD Y ESTABILIDAD ---
from PySide6.QtCore import QSettings

# Leemos la configuración ANTES de importar TensorFlow
settings = QSettings("CUCEI", "Redocnizer")
use_gpu = settings.value("use_gpu_acceleration", False, type=bool)

# Si el usuario NO activó explícitamente la GPU, la ocultamos totalmente.
# Esto evita el error de "Multiple OpKernel registrations" porque TF ni siquiera mirará la GPU.
if not use_gpu:
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1' # -1 es el estándar para "ocultar todo"
    os.environ['TF_LSTMS_USE_GPU'] = '0'
    # Esto desactiva optimizaciones de CPU que a veces causan crashes en procesadores viejos
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' 

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Solo errores críticos

import tensorflow as tf

# Silenciar logs internos
tf.get_logger().setLevel('ERROR')

# Permitir que TF elija CPU si la configuración de GPU falla
tf.config.set_soft_device_placement(True)

if use_gpu:
    try:
        # Intentamos configurar la memoria dinámica si hay GPU disponible
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            for g in gpus:
                tf.config.experimental.set_memory_growth(g, True)
            print(f"[TF] Aceleración de hardware activada.")
        else:
            print(f"[TF] GPU activada en configuración pero no detectada físicamente. Usando CPU.")
    except Exception as e:
        print(f"[TF] Error al inicializar GPU: {e}. Revirtiendo a CPU.")

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
    """Arquitectura CRNN optimizada para compatibilidad."""
    input_img = Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1), name="image", dtype="float32")

    x = Conv2D(32, (3, 3), activation="relu", padding="same", name="Conv1")(input_img)
    x = MaxPooling2D((2, 2), name="pool1")(x)
    x = BatchNormalization(name="bn1")(x)

    x = Conv2D(64, (3, 3), activation="relu", padding="same", name="Conv2")(x)
    x = MaxPooling2D((2, 2), name="pool2")(x)
    x = BatchNormalization(name="bn2")(x)

    x = Reshape(target_shape=(8, 4096), name="reshape")(x)
    x = Dense(512, activation="relu", name="dense1")(x)
    x = Dropout(0.2)(x)

    # Sigmoid es más lento que TanH pero mucho más compatible en CPUs y GPUs diversas
    x = Bidirectional(LSTM(128, return_sequences=True, recurrent_activation='sigmoid'), name="bidirectional_1")(x)
    x = Bidirectional(LSTM(64, return_sequences=True, recurrent_activation='sigmoid'), name="bidirectional_2")(x)

    y_pred = Dense(NUM_CHARS + 1, activation="softmax", name="dense_output")(x)

    model = Model(inputs=input_img, outputs=y_pred, name="crnn_inference_model")
    return model

def load_inference_model():
    """Carga los recursos del modelo asegurando estabilidad."""
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
            modelo_inf.load_weights(MODELO_PATH, by_name=True, skip_mismatch=True)
            print("✅ Inteligencia Artificial cargada correctamente.")
        except Exception as e:
            print(f"⚠️ Error cargando pesos: {e}")
    else:
        print(f"Error: Archivo de pesos no encontrado.")
    
    return modelo_inf, index_to_char, OUTPUT_SEQUENCE_LENGTH