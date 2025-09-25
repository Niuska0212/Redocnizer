# crnn_inference.py (ACTUALIZADO)

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras import backend as K
# Importamos las capas de Aumento de Datos que están en tu modelo
from tensorflow.keras.layers import RandomRotation, RandomZoom, RandomTranslation 
import joblib
import os

# --- CONSTANTES DE CONFIGURACIÓN DEL MODELO (Deben coincidir con tu entrenamiento) ---
OUTPUT_SEQUENCE_LENGTH = 32 
IMG_HEIGHT = 32
IMG_WIDTH = 256

# --- Rutas (Asegúrate de que estas rutas sean correctas) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    for seq in K.get_value(results):
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def load_inference_model():
    """Carga el modelo y el vocabulario para la inferencia."""
    try:
        # Definimos TODOS los objetos personalizados, incluyendo la función de pérdida CTC 
        # y las capas de aumento de datos que forman parte de la estructura de entrada.
        custom_objects = {
            'ctc_loss_lambda_func': ctc_loss_lambda_func,
            'RandomRotation': RandomRotation, 
            'RandomZoom': RandomZoom, 
            'RandomTranslation': RandomTranslation
        }
        
        # 1. Cargar el vocabulario
        vocab_data = joblib.load(VOCAB_PATH)
        index_to_char = vocab_data['index_to_char']
        
        # 2. Cargar el modelo de entrenamiento
        full_model = load_model(
            MODELO_PATH, 
            custom_objects=custom_objects, # <--- ¡CORRECCIÓN APLICADA AQUÍ!
            compile=False
        )
        
        # 3. Crear el modelo de INFERENCIA (solo CNN y LSTM, sin la capa CTC)
        # Tomamos la entrada del modelo completo
        input_img = full_model.get_layer('input_img').input
        # Tomamos la salida de la capa Dense, que está ANTES de la capa Lambda (ctc_loss)
        output_layer = full_model.get_layer('output').output
        
        # Creamos el nuevo modelo de inferencia
        modelo_inferencia = Model(inputs=input_img, outputs=output_layer)

        print("Modelo CRNN y vocabulario cargados exitosamente.")
        return modelo_inferencia, index_to_char, OUTPUT_SEQUENCE_LENGTH

    except Exception as e:
        # Aquí también mostramos la ruta del modelo para ayudar a la depuración
        print(f"Error al cargar el modelo o vocabulario: {e}")
        print(f"Ruta del modelo intentada: {MODELO_PATH}")
        print("Asegúrate de que el modelo y el vocabulario existan y que las capas personalizadas estén importadas.")
        return None, None, None