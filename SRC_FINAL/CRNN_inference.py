# crnn_inference.py

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras import backend as K
import joblib
import os

# --- CONSTANTES DE CONFIGURACIÓN DEL MODELO (Deben coincidir con tu entrenamiento) ---
# Longitud de la secuencia de salida (256 // 8 = 32)
OUTPUT_SEQUENCE_LENGTH = 32 
# Altura y ancho que espera el modelo (32x256)
IMG_HEIGHT = 32
IMG_WIDTH = 256

# --- Rutas (Asegúrate de que estas rutas sean correctas en tu entorno) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Asume que 'models' está al mismo nivel que tu directorio de scripts (../models)
RUTA_MODELOS = os.path.join(BASE_DIR, "..", "models") 
MODELO_PATH = os.path.join(RUTA_MODELOS, "keras_cnn_lstm_v3_ctc.h5")
VOCAB_PATH = os.path.join(RUTA_MODELOS, "vocabulario_v3.pkl")

# La función de pérdida CTC es necesaria solo para que Keras pueda cargar el modelo
def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# -------------------------------
# DECODIFICACIÓN Y CARGA
# -------------------------------

def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    """Decodifica las predicciones del modelo usando CTC."""
    # input_len debe coincidir con la longitud de la secuencia de salida (OUTPUT_SEQUENCE_LENGTH)
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    
    # Decodificación 'greedy'
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    # Usamos K.get_value() para obtener el numpy array del tensor
    for seq in K.get_value(results):
        # Filtramos el índice -1 (el padding)
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def load_inference_model():
    """Carga el modelo y el vocabulario para la inferencia."""
    try:
        # 1. Cargar el vocabulario
        vocab_data = joblib.load(VOCAB_PATH)
        index_to_char = vocab_data['index_to_char']
        
        # 2. Cargar el modelo de entrenamiento
        full_model = load_model(
            MODELO_PATH, 
            custom_objects={'ctc_loss_lambda_func': ctc_loss_lambda_func}, 
            compile=False
        )
        
        # 3. Crear el modelo de INFERENCIA (solo CNN y LSTM, sin la capa CTC)
        input_img = full_model.get_layer('input_img').input
        output_layer = full_model.get_layer('output').output
        modelo_inferencia = Model(inputs=input_img, outputs=output_layer)

        print("Modelo CRNN y vocabulario cargados exitosamente.")
        return modelo_inferencia, index_to_char, OUTPUT_SEQUENCE_LENGTH

    except Exception as e:
        print(f"Error al cargar el modelo o vocabulario: {e}")
        print("Asegúrate de que los archivos 'keras_cnn_lstm_v3_ctc.h5' y 'vocabulario_v3.pkl' existan en la ruta correcta.")
        return None, None, None