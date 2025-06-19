import sys
import os
import numpy as np
import cv2
import joblib
from preprocesamiento import cargar_datos # Mantener cargar_datos por si se usa para clasificar conjuntos completos
import random # Necesario para diagnosticar_modelo

# Agregar el directorio raíz del proyecto al path
ruta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ruta_proyecto not in sys.path:
    sys.path.append(ruta_proyecto)

# Importar las clases desde entrenamiento.py para poder instanciarlas
from entrenamiento import ConvolutionalNeuralNetwork, RedNeuronal 

def interpretar_prediccion(prediccion_indice, class_labels_map):
    """Interpreta el índice de predicción a la etiqueta de clase original."""
    # Invertir el mapeo para ir de índice a nombre de clase
    idx_to_label = {v: k for k, v in class_labels_map.items()}
    return idx_to_label.get(prediccion_indice, "Desconocido")


# --- MODIFICACIÓN DE clasificar_imagen: Ahora puede recibir una imagen NumPy directamente ---
def clasificar_imagen(imagen_o_ruta, modelo_nn, modelo_cnn, class_labels_map):
    """Clasifica una imagen (desde ruta o NumPy array) con CNN y la Red Neuronal."""
    
    if isinstance(imagen_o_ruta, str): # Si es una ruta de archivo
        # Cargar la imagen
        imagen = cv2.imread(imagen_o_ruta, cv2.IMREAD_GRAYSCALE)
        if imagen is None:
            raise ValueError(f"No se pudo cargar la imagen en {imagen_o_ruta}")
    elif isinstance(imagen_o_ruta, np.ndarray): # Si ya es un array NumPy (esperamos (28,28))
        imagen = imagen_o_ruta
    else:
        raise TypeError("Input must be a file path (str) or a NumPy array (np.ndarray).")


    # Redimensionar, normalizar la imagen de la misma forma que en el entrenamiento
    # Asegúrate de que la imagen sea (28,28) si viene de la carga de datos.
    imagen_preprocesada = cv2.resize(imagen, (28, 28)).astype(np.float32) / 255.0  

    # Extraer características con la CNN
    # Reshape(1, -1) para asegurar que tiene el formato de batch de 1 muestra.
    features = modelo_cnn.extraer_caracteristicas(imagen_preprocesada).flatten().reshape(1, -1)  

    # Hacer la predicción con la Red Neuronal
    nn_pred_index = modelo_nn.predict(features)[0] # Obtiene el índice de la clase

    return nn_pred_index


def clasificar_conjunto_datos(ruta_datos_dir, modelo_nn, modelo_cnn, class_labels_map, max_por_carpeta=None):
    """Clasifica un conjunto de datos completo usando los modelos guardados."""
    # Aquí cargar_datos_split es mejor para asegurar que se use el mismo método de split si aplica
    # O usar cargar_datos si queremos el conjunto completo sin dividir.
    # Usaremos cargar_datos aquí para obtener todos los datos de la ruta.
    X_data_raw, y_true_indices_raw, _ = cargar_datos(ruta_datos_dir, max_por_carpeta=max_por_carpeta) 

    predictions = []
    true_labels = []

    for i in range(len(X_data_raw)):
        img_raw = X_data_raw[i] # La imagen ya está en 2D (28,28)
        
        # Usar la nueva función clasificar_imagen que acepta un array NumPy
        pred_index = clasificar_imagen(img_raw, modelo_nn, modelo_cnn, class_labels_map)

        predictions.append(pred_index)
        true_labels.append(y_true_indices_raw[i])
    
    return np.array(predictions), np.array(true_labels)


def diagnosticar_modelo(ruta_datos_dir, modelo_nn, modelo_cnn, class_labels_map, num_ejemplos=5):
    """
    Diagnostica el modelo mostrando algunas predicciones con las imágenes.
    """
    # Usar cargar_datos para obtener un subconjunto del directorio sin división interna
    X_data_raw, y_true_indices_raw, _ = cargar_datos(ruta_datos_dir, max_por_carpeta=num_ejemplos)

    if len(X_data_raw) == 0:
        print("No se encontraron datos para diagnóstico.")
        return

    print(f"\nRealizando diagnóstico con {len(X_data_raw)} ejemplos:")

    for i in range(len(X_data_raw)):
        img_raw = X_data_raw[i] # Imagen NumPy original (28,28)

        true_label_index = y_true_indices_raw[i]
        true_label_name = interpretar_prediccion(true_label_index, class_labels_map)

        # Clasificar la imagen usando la función actualizada
        pred_index = clasificar_imagen(img_raw, modelo_nn, modelo_cnn, class_labels_map)
        
        pred_label_name = interpretar_prediccion(pred_index, class_labels_map)

        print(f"Ejemplo {i+1}: Real: {true_label_name}, Predicción: {pred_label_name}")
        
        # Mostrar imagen
        img_display = (img_raw).astype(np.uint8) # Ya está entre 0-255, solo asegurar tipo
        cv2.imshow(f"Ejemplo {i+1} - Real: {true_label_name} - Pred: {pred_label_name}", img_display)
        cv2.waitKey(1000) # Muestra por 1 segundo
    cv2.destroyAllWindows() # Destruir todas las ventanas al final


def etiqueta_a_letra(etiqueta):
    """
    Convierte etiquetas como 'A_U' o 'a_L' a la letra correspondiente 'A' o 'a'.
    Si la etiqueta no sigue el formato esperado, la retorna igual.
    """
    if etiqueta.endswith('_U'):
        return etiqueta[0].upper()
    elif etiqueta.endswith('_L'):
        return etiqueta[0].lower()
    else:
        return etiqueta


if __name__ == "__main__":
    # Obtener la ruta base del proyecto
    ruta_base = os.path.dirname(os.path.abspath(__file__)) 
    ruta_modelos = os.path.join(ruta_base, "..", "models")  
    # *** CAMBIO AQUÍ: Apuntar al directorio principal del dataset para la evaluación ***
    ruta_dataset_principal = os.path.join(ruta_base, "..", "data", "data", "dataset") 

    print("Cargando modelos...")
    try:
        # Asegúrate de cargar los modelos correctos (los generados por el entrenamiento reciente)
        nn = joblib.load(os.path.join(ruta_modelos, "nn_model.pkl"))
        cnn = joblib.load(os.path.join(ruta_modelos, "cnn_model.pkl"))
        class_labels_map = joblib.load(os.path.join(ruta_modelos, "class_labels_map.pkl"))
    except FileNotFoundError:
        print("Error: Asegúrate de haber entrenado y guardado los modelos (nn_model.pkl, cnn_model.pkl, class_labels_map.pkl) en la carpeta 'models'.")
        sys.exit(1)

    # Clasificar una imagen individual (ejemplo con ruta)
    ruta_imagen_ejemplo = os.path.join(ruta_dataset_principal, "A_U", "A_U_1.png") # Ejemplo de ruta de imagen, ajusta si es necesario
    if os.path.exists(ruta_imagen_ejemplo):
        print(f"\nClasificando imagen de ejemplo: {ruta_imagen_ejemplo}")
        try:
            pred_index = clasificar_imagen(ruta_imagen_ejemplo, nn, cnn, class_labels_map)
            print(f"Predicción Red Neuronal: {etiqueta_a_letra(interpretar_prediccion(pred_index, class_labels_map))}")
        except ValueError as e:
            print(f"Error al clasificar la imagen: {e}")
    else:
        print(f"No se encontró la imagen de ejemplo en {ruta_imagen_ejemplo}. Proporciona una ruta válida o salta.")
        
    # Preguntar al usuario por una ruta de imagen personalizada
    ruta_imagen_input = input("\nIngrese la ruta de una imagen a clasificar (deje vacío para saltar): ")
    if ruta_imagen_input:
        ruta_imagen_input = os.path.abspath(ruta_imagen_input)  # Convertir a ruta absoluta
        try:
            pred_index = clasificar_imagen(ruta_imagen_input, nn, cnn, class_labels_map)
            print(f"Predicción Red Neuronal: {etiqueta_a_letra(interpretar_prediccion(pred_index, class_labels_map))}")
        except ValueError as e:
            print(f"Error al clasificar la imagen: {e}")


    # Clasificar un conjunto de datos completo (opcional)
    usar_conjunto_datos = input("¿Desea clasificar un conjunto de datos completo (para evaluación)? (s/n): ").lower()
    if usar_conjunto_datos == 's':
        print("\nClasificando conjunto de datos para evaluación...")
        # Usamos ruta_dataset_principal para cargar un subconjunto o todo para evaluación
        predictions, true_labels = clasificar_conjunto_datos(ruta_dataset_principal, nn, cnn, class_labels_map, max_por_carpeta=100) # Limitar para prueba, quitar en producción

        if len(predictions) > 0:
            from sklearn.metrics import classification_report, confusion_matrix
            class_names = [k for k, v in sorted(class_labels_map.items(), key=lambda item: item[1])]
            print("\nReporte de Clasificación del Conjunto de Datos:")
            print(classification_report(true_labels, predictions, target_names=class_names, zero_division=0))
            print("\nMatriz de Confusión del Conjunto de Datos:")
            print(confusion_matrix(true_labels, predictions))
        else:
            print("No se pudieron cargar datos para la clasificación del conjunto.")

    # Diagnóstico visual del modelo
    usar_diagnostico = input("¿Desea realizar un diagnóstico visual del modelo? (s/n): ").lower()
    if usar_diagnostico == 's':
        # Usa ruta_dataset_principal para el diagnóstico
        diagnosticar_modelo(ruta_dataset_principal, nn, cnn, class_labels_map, num_ejemplos=5)