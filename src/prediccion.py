import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2
import os

# Define la ruta del modelo guardado.
# Asegúrate de que este nombre de archivo coincida con el que guardaste
model_path = "model_v3_ctc_loss.keras"

# Asegúrate de que el modelo exista antes de intentar cargarlo
if not os.path.exists(model_path):
    print(f"Error: El archivo del modelo '{model_path}' no se encontró.")
    print("Asegúrate de que el nombre del archivo es correcto y está en la misma carpeta que este script.")
    exit()

# Carga los caracteres y la configuración de longitud de etiqueta
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789áéíóúñÁÉÍÓÚÑ-!¡¿?()[]{}*.,;:" + "'\" "
num_to_char = {i: char for i, char in enumerate(CHARS)}
max_label_len = 32
max_output_len = 32

# Función para decodificar la salida del modelo
def decode_batch_predictions(pred):
    # La salida del modelo es un tensor de tamaño [lote, 32, num_clases]
    # Usamos ctc_decode para obtener la secuencia más probable
    # La configuración `greedy=True` selecciona el camino más probable
    # `beam_width` se usa para una búsqueda más exhaustiva, pero greedy es más rápido
    results = tf.keras.backend.ctc_decode(pred, input_length=np.ones(pred.shape[0]) * pred.shape[1], greedy=True)[0][0][:, :max_label_len]
    
    # Convierte los índices de vuelta a caracteres
    output_text = []
    for res in results:
        res = tf.gather(res, tf.where(tf.math.not_equal(res, -1)))
        decoded_string = tf.strings.reduce_join([num_to_char[i] for i in res.numpy()]).numpy().decode("utf-8")
        output_text.append(decoded_string)
    return output_text

# Carga y preprocesa una imagen para la predicción
def preprocess_image(image_path):
    # Carga la imagen en escala de grises
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error al cargar la imagen: {image_path}")
        return None
    
    # Cambia el tamaño de la imagen a 32x256
    # Asegúrate de que esto coincida con el tamaño de entrada de tu modelo
    img = cv2.resize(img, (256, 32))
    
    # Normaliza los píxeles (igual que en el entrenamiento)
    img = img / 255.0
    
    # Agrega las dimensiones de lote y canal que el modelo espera
    img = np.expand_dims(img, axis=-1)  # Agrega un canal
    img = np.expand_dims(img, axis=0)   # Agrega la dimensión del lote
    
    return img

# Carga el modelo guardado
model_prediction = keras.models.load_model(model_path)

# Pide al usuario que ingrese la ruta de la imagen
image_path = input("Ingresa la ruta de la imagen que quieres predecir (ej. data\\data\\dataset_palabras\\03417.png): ")

# Prepara la imagen para la predicción
input_img = preprocess_image(image_path)
if input_img is None:
    exit()

# Realiza la predicción
preds = model_prediction.predict(input_img)

# Decodifica la predicción a texto
decoded_text = decode_batch_predictions(preds)

# Imprime el resultado
print(f"Predicción del modelo: {decoded_text[0]}")
print("¡El modelo se cargó y funcionó correctamente!")
print("Recuerda que la precisión no es perfecta, pero con más entrenamiento seguirá mejorando.")
