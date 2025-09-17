import os
import numpy as np
import cv2
import tensorflow as tf
import joblib
from difflib import SequenceMatcher

# -------------------------------
# CONFIGURACIÓN Y PARÁMETROS
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_modelos = os.path.join(BASE_DIR, "..", "models")
ruta_dataset = os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")

# Define los mismos parámetros que usaste en el entrenamiento
img_height = 32
img_width = 256
output_sequence_length = img_width // 8

# -------------------------------
# FUNCIÓN DE DECODIFICACIÓN
# -------------------------------
def decode_batch_predictions(y_pred_probs, index_to_char):
    """Decodifica las predicciones del modelo usando CTC."""
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    # Se utiliza tf.keras.backend.ctc_decode
    results = tf.keras.backend.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    for seq in tf.keras.backend.get_value(results):
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def calculate_levenshtein_distance(true_word, pred_word):
    """Calcula la distancia de Levenshtein entre dos palabras."""
    return SequenceMatcher(None, true_word.lower(), pred_word.lower()).ratio()

def predict_and_print_results(model, image_path, true_word, index_to_char):
    """Carga una imagen, predice la palabra y muestra los resultados."""
    if not os.path.exists(image_path):
        print(f"\nADVERTENCIA: Archivo de imagen de prueba no encontrado en: {image_path}")
        return

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: No se pudo leer la imagen en '{image_path}'")
        return

    # Preprocesamiento de la imagen
    img = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_AREA)
    img = img.reshape(1, img_height, img_width, 1).astype(np.float32)

    # Realiza la predicción
    print(f"\nRealizando predicción para la imagen: {os.path.basename(image_path)}")
    y_pred_probs = model.predict(img)
    predicted_word = decode_batch_predictions(y_pred_probs, index_to_char)[0]
    
    # Muestra los resultados y la distancia de Levenshtein
    levenshtein_ratio = calculate_levenshtein_distance(true_word, predicted_word)
    
    print("\n--- Resultado de la Predicción ---")
    print(f"Palabra real: '{true_word}'")
    print(f"Texto predicho: '{predicted_word}'")
    print(f"Ratio de similitud (Levenshtein): {levenshtein_ratio:.2f}")
    print("-" * 30)

# -------------------------------
# FUNCIÓN PRINCIPAL DE PREDICCIÓN
# -------------------------------
def main():
    # Carga el modelo y el vocabulario
    try:
        model_path = os.path.join(ruta_modelos, "keras_cnn_lstm_v3_ctc.h5")
        model = tf.keras.models.load_model(model_path, compile=False)
        print(f"Modelo cargado correctamente desde '{model_path}'")

        vocab_path = os.path.join(ruta_modelos, "vocabulario_v3.pkl")
        data = joblib.load(vocab_path)
        index_to_char = data['index_to_char']
        print(f"Vocabulario cargado correctamente desde '{vocab_path}'")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Asegúrate de haber ejecutado el script de entrenamiento para generar los archivos.")
        return
    except KeyError as e:
        print(f"Error al cargar el vocabulario: {e}")
        print("El archivo 'vocabulario_v3.pkl' puede estar corrupto o incompleto.")
        return

    # --- LISTA DE CASOS DE PRUEBA ---
    # Puedes agregar más elementos a esta lista para probar otras imágenes.
    test_cases = [
        ("10711.png", "tornado"),
        ("10707.png", "mariposa"),
        # Añade aquí tus otras imágenes y las palabras correctas
        # Ejemplo: ("10712.png", "otra_palabra"),
    ]

    for file_name, true_word in test_cases:
        image_path = os.path.join(ruta_dataset, file_name)
        predict_and_print_results(model, image_path, true_word, index_to_char)


if __name__ == "__main__":
    main()
