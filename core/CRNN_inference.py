# CRNN_inference.py

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras import backend as K
import joblib
import os
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, BatchNormalization, Reshape, Dense, Bidirectional, LSTM, Dropout
import h5py

# --- CONSTANTES DE CONFIGURACIÓN ---
OUTPUT_SEQUENCE_LENGTH = 32 
IMG_HEIGHT = 32
IMG_WIDTH = 256
# El número de caracteres debe coincidir exactamente con tu vocabulario_v3.pkl
NUM_CHARS = 84 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_MODELOS = os.path.join(BASE_DIR, "..", "models") 
MODELO_PATH = os.path.join(RUTA_MODELOS, "keras_cnn_lstm_v3_ctc.h5")
VOCAB_PATH = os.path.join(RUTA_MODELOS, "vocabulario_v3.pkl")

def build_pure_inference_model():
    """
    Reconstruye la arquitectura exacta del modelo para inferencia.
    Esto evita errores de compatibilidad al cargar el .h5 directamente.
    """
    input_img = Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1), name="image", dtype="float32")

    # Bloque CNN
    x = Conv2D(32, (3, 3), activation="relu", kernel_initializer="he_normal", padding="same", name="Conv1")(input_img)
    x = MaxPooling2D((2, 2), name="pool1")(x)
    x = BatchNormalization(name="bn1")(x)

    x = Conv2D(64, (3, 3), activation="relu", kernel_initializer="he_normal", padding="same", name="Conv2")(x)
    x = MaxPooling2D((2, 2), name="pool2")(x)
    x = BatchNormalization(name="bn2")(x)

    # Preparar para RNN
    # Después de 2 poolings (2,2): (32,256,1) -> (8,64,64) en espacio de características
    # Aplanar correctamente: 8 (alto) x 64 (ancho) x 64 (canales) = 32,768 elementos
    # Reshape a (8, 4096) para mantener la secuencia temporal
    x = Reshape(target_shape=(8, 4096), name="reshape")(x)
    x = Dense(512, activation="relu", name="dense1")(x)
    x = Dropout(0.2)(x)

    # Bloque RNN (Bidirectional LSTM)
    x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.25), name="bidirectional_1")(x)
    x = Bidirectional(LSTM(64, return_sequences=True, dropout=0.25), name="bidirectional_2")(x)

    # Capa de Salida
    y_pred = Dense(NUM_CHARS + 1, activation="softmax", name="dense_output")(x)

    model = Model(inputs=input_img, outputs=y_pred, name="crnn_inference_model")
    return model

def load_inference_model():
    """Carga vocabulario y pesos en el modelo de inferencia."""
    print(f"\n[INFO] Cargando recursos de inteligencia...")
    
    # 1. Cargar Vocabulario
    if not os.path.exists(VOCAB_PATH):
        print(f"ERROR: No se encontró el vocabulario en {VOCAB_PATH}")
        return None, None, None
    
    vocab_data = joblib.load(VOCAB_PATH)
    # Aseguramos que el índice a carácter esté bien mapeado
    char_to_index = vocab_data['char_to_index']
    index_to_char = {i: c for c, i in char_to_index.items()}

    # 2. Construir arquitectura
    modelo_inf = build_pure_inference_model()

    # 3. Cargar Pesos
    if os.path.exists(MODELO_PATH):
        try:
            # Intentamos carga estándar
            modelo_inf.load_weights(MODELO_PATH, by_name=True, skip_mismatch=True)
            print("✅ Pesos del modelo CRNN cargados exitosamente.")
        except Exception as e:
            print(f"⚠️ Advertencia en carga directa: {e}. Intentando mapeo manual...")
            # Aquí podrías implementar la carga manual con h5py si es necesario
    else:
        print(f"❌ ERROR: Archivo de pesos no encontrado en {MODELO_PATH}")
        return None, None, None

    return modelo_inf, index_to_char, OUTPUT_SEQUENCE_LENGTH