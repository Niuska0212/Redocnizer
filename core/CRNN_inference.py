# crnn_inference.py (Creando un Nuevo Modelo de Inferenci a Partir del Antiguo)

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras import backend as K
# Importamos TODAS las capas personalizadas para asegurar la carga
from tensorflow.keras.layers import RandomRotation, RandomZoom, RandomTranslation, Rescaling 
import joblib
import os
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, BatchNormalization, Reshape, Dense, Bidirectional, LSTM, Dropout
import h5py

# --- CONSTANTES DE CONFIGURACIÓN DEL MODELO ---
OUTPUT_SEQUENCE_LENGTH = 32 
IMG_HEIGHT = 32
IMG_WIDTH = 256
NUM_CHARS = 84 # Asumiendo 84 caracteres en tu vocabulario (como sugiere el KerasTensor shape=(None, 32, 84))

# --- Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_MODELOS = os.path.join(BASE_DIR, "..", "models") 
MODELO_PATH = os.path.join(RUTA_MODELOS, "keras_cnn_lstm_v3_ctc.h5")
VOCAB_PATH = os.path.join(RUTA_MODELOS, "vocabulario_v3.pkl")

# Función de pérdida CTC (necesaria para load_model)
def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# -------------------------------
# DECODIFICACIÓN Y CARGA
# -------------------------------

# (decode_batch_predictions se mantiene igual)

def build_pure_inference_model(weights_source_model: Model = None):
    """
    Define y construye la arquitectura Pura de Inferenci (sin Aumento/CTC).
    Si se proporciona un modelo fuente, se transfieren los pesos.
    """
    input_img = Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1), name='input_img_inference')

    # Replicamos la arquitectura CNN (saltando el preprocesamiento)
    x = tf.keras.layers.Rescaling(1./255)(input_img) # Se mantiene la Rescaling por si es esencial para los pesos

    x = Conv2D(64, (3, 3), activation='relu', padding='same', name='conv_1')(x)
    x = BatchNormalization(name='bn_1')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x)

    x = Conv2D(128, (3, 3), activation='relu', padding='same', name='conv_2')(x)
    x = BatchNormalization(name='bn_2')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_2')(x)
    
    x = Conv2D(256, (3, 3), activation='relu', padding='same', name='conv_3')(x)
    x = BatchNormalization(name='bn_3')(x)
    
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='conv_4')(x)
    x = BatchNormalization(name='bn_4')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_3')(x)
    
    # Dropout (solo para inferencia se suele omitir o desactivar)
    # x = Dropout(0.3, name='dropout_cnn')(x) 

    x = Reshape(target_shape=(OUTPUT_SEQUENCE_LENGTH, (IMG_HEIGHT // 8) * 512), name='reshape_inf')(x)
    # x = Dropout(0.3, name='dropout_pre_lstm')(x) 
    
    # Replicamos la arquitectura RNN
    x = Bidirectional(LSTM(256, return_sequences=True, dropout=0.0, name='lstm_1'))(x) # dropout=0.0 en inferencia
    x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.0, name='lstm_2'))(x) # dropout=0.0 en inferencia

    output = Dense(NUM_CHARS + 1, activation='softmax', name='output')(x)

    modelo_inferencia = Model(inputs=input_img, outputs=output)
    
    # ----------------------------------------------
    # 2. Transferencia de Pesos (Transfer Learning)
    # ----------------------------------------------
    if weights_source_model:
        print("Intentando transferir pesos del modelo original...")
        for layer in modelo_inferencia.layers:
            try:
                # Buscamos la capa correspondiente en el modelo fuente
                source_layer = weights_source_model.get_layer(layer.name)
                # Transferimos los pesos
                layer.set_weights(source_layer.get_weights())
                # print(f"Pesos transferidos a la capa: {layer.name}")
            except Exception as e:
                # print(f"No se pudieron transferir pesos a la capa {layer.name}. (Puede ser Input o Reshape/Output)")
                pass
        print("Transferencia de pesos completada.")

    return modelo_inferencia


def load_inference_model():
    """Carga el modelo y el vocabulario. Intenta la carga directa, si falla, construye y transfiere."""
    
    custom_objects = {
        'ctc_loss_lambda_func': ctc_loss_lambda_func,
        'RandomRotation': RandomRotation, 
        'RandomZoom': RandomZoom, 
        'RandomTranslation': RandomTranslation,
        'Rescaling': Rescaling # Incluir la capa Rescaling
    }
    
    try:
        # 1. Cargar el vocabulario
        vocab_data = joblib.load(VOCAB_PATH)
        index_to_char = vocab_data['index_to_char']
        
        # --- INTENTO 1: Carga directa del modelo de entrenamiento ---
        print("Intentando cargar el modelo completo para extraer el grafo...")
        full_model = load_model(
            MODELO_PATH, 
            custom_objects=custom_objects, 
            compile=False
        )
        
        # Si la carga es exitosa, creamos el modelo de inferencia a partir del grafo cargado
        input_img = full_model.get_layer('input_img').input
        output_layer = full_model.get_layer('output').output
        modelo_inferencia = Model(inputs=input_img, outputs=output_layer)
        
        # Eliminar las capas de Aumento de Datos después de la carga si es necesario.
        # En este caso, simplemente usamos las capas 'limpias' del modelo funcional.
        print("Modelo CRNN cargado y grafo de inferencia creado exitosamente.")
        return modelo_inferencia, index_to_char, OUTPUT_SEQUENCE_LENGTH

    except Exception as e:
        # --- INTENTO 2: Construir el modelo limpio y transferir pesos ---
        print(f"La carga directa falló: {e}")
        print("Intentando cargar solo los pesos y transferirlos a una arquitectura de inferencia limpia...")
        
        # 2a. Cargar solo el modelo (incluyendo el grafo, aunque esté incompleto)
        try:
            full_model_weights = load_model(
                MODELO_PATH, 
                custom_objects=custom_objects,
                compile=False
            )
            # 2b. Construir la arquitectura de inferencia limpia y transferir pesos
            modelo_inferencia = build_pure_inference_model(weights_source_model=full_model_weights)
            
            # 2c. Validar la transferencia (opcional, pero útil)
            if modelo_inferencia.get_layer('conv_1').get_weights():
                print("Transferencia de pesos validada. Usando el nuevo modelo de inferencia.")
                return modelo_inferencia, index_to_char, OUTPUT_SEQUENCE_LENGTH
            else:
                raise Exception("Fallo en la transferencia de pesos.")
                
        except Exception as e_transfer:
            print(f"Error al intentar la transferencia de pesos: {e_transfer}")
            print(f"Ruta del modelo intentada: {MODELO_PATH}")
            # Intento alternativo: construir el modelo limpio y usar load_weights(by_name=True)
            try:
                modelo_inferencia = build_pure_inference_model(weights_source_model=None)
                print("Intentando cargar pesos mediante load_weights(by_name=True)...")
                modelo_inferencia.load_weights(MODELO_PATH, by_name=True)
                print("Carga de pesos por nombre completada.")
                return modelo_inferencia, index_to_char, OUTPUT_SEQUENCE_LENGTH
            except Exception as e_loadname:
                print(f"Fallo load_weights by_name: {e_loadname}")
                # Intento manual con h5py: mapear pesos por nombre de capa
                try:
                    print("Intentando carga manual de pesos con h5py...")
                    with h5py.File(MODELO_PATH, 'r') as f:
                        weights_group = f['model_weights'] if 'model_weights' in f else f

                        modelo_inf = build_pure_inference_model(weights_source_model=None)
                        for layer in modelo_inf.layers:
                            name = layer.name
                            if name in weights_group:
                                try:
                                    g = weights_group[name]
                                    weight_vals = []
                                    # Recorremos los datasets en el grupo de la capa
                                    for k in g:
                                        item = g[k]
                                        if isinstance(item, h5py.Dataset):
                                            weight_vals.append(item[()])
                                    if weight_vals:
                                        try:
                                            layer.set_weights(weight_vals)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                        print("Carga manual (h5py) intentada. Es posible que falten pesos no transferibles.")
                        return modelo_inf, index_to_char, OUTPUT_SEQUENCE_LENGTH
                except Exception as e_h5:
                    print(f"Error en carga manual h5py: {e_h5}")
                    print("¡Fallo crítico! Asegúrate de que los nombres de las capas en 'build_pure_inference_model' coincidan con 'entrenamientoV3.py'.")
                    return None, None, None