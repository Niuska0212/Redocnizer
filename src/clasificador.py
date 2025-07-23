import sys
import os
import numpy as np
import cv2
import joblib
# Importar la versión actualizada de cargar_datos
from preprocesamiento import cargar_datos 
import random 

# Agregar el directorio raíz del proyecto al path
ruta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ruta_proyecto not in sys.path:
    sys.path.append(ruta_proyecto)

# Importar las clases desde entrenamiento.py para poder instanciarlas
from entrenamiento import ConvolutionalNeuralNetwork, RedNeuronal 

def interpretar_prediccion(prediccion_indice, class_labels_map):
    """Interpreta el índice de predicción a la etiqueta de clase original."""
    idx_to_label = {v: k for k, v in class_labels_map.items()}
    return idx_to_label.get(prediccion_indice, "Desconocido")

def clasificar_imagen(imagen_o_ruta, modelo_nn, modelo_cnn, class_labels_map):
    """Clasifica una imagen (desde ruta o NumPy array) con CNN y la Red Neuronal."""
    
    if isinstance(imagen_o_ruta, str): # Si es una ruta de archivo
        imagen = cv2.imread(imagen_o_ruta, cv2.IMREAD_GRAYSCALE)
        if imagen is None:
            raise ValueError(f"No se pudo cargar la imagen en {imagen_o_ruta}")
    elif isinstance(imagen_o_ruta, np.ndarray): # Si ya es un array NumPy (esperamos (28,28))
        imagen = imagen_o_ruta
    else:
        raise TypeError("Input must be a file path (str) or a NumPy array (np.ndarray).")

    # La imagen ya debe estar redimensionada a (28,28) desde la carga,
    # solo se normaliza si no lo estaba ya.
    imagen_preprocesada = imagen.astype(np.float32) / 255.0  

    # Extraer características con la CNN
    features = modelo_cnn.extraer_caracteristicas(imagen_preprocesada).flatten().reshape(1, -1)  

    # Hacer la predicción con la Red Neuronal
    nn_pred_index = modelo_nn.predict(features)[0] 

    return nn_pred_index

def clasificar_conjunto_datos(ruta_datos_dir, modelo_nn, modelo_cnn, class_labels_map, max_por_carpeta=None, num_workers=os.cpu_count()):
    """Clasifica un conjunto de datos completo usando los modelos guardados, ahora paralelizado."""
    X_data_raw, y_true_indices_raw, _ = cargar_datos(ruta_datos_dir, max_por_carpeta=max_por_carpeta, num_workers=num_workers) 

    predictions = []
    true_labels = []

    # La extracción de características y predicción con tus clases personalizadas
    # no se puede paralelizar directamente en este bucle sin reestructurar
    # tus clases ConvolutionalNeuralNetwork y RedNeuronal para aceptar batches.
    # Por ahora, se mantiene secuencial, pero la carga de datos es paralela.
    for i in range(len(X_data_raw)):
        img_raw = X_data_raw[i] 
        pred_index = clasificar_imagen(img_raw, modelo_nn, modelo_cnn, class_labels_map)
        predictions.append(pred_index)
        true_labels.append(y_true_indices_raw[i])
    
    return np.array(predictions), np.array(true_labels)


def diagnosticar_modelo(ruta_datos_dir, modelo_nn, modelo_cnn, class_labels_map, num_ejemplos=5, num_workers=os.cpu_count()):
    """
    Diagnostica el modelo mostrando algunas predicciones con las imágenes.
    Ahora carga los datos en paralelo.
    """
    X_data_raw, y_true_indices_raw, _ = cargar_datos(ruta_datos_dir, max_por_carpeta=num_ejemplos, num_workers=num_workers)

    if len(X_data_raw) == 0:
        print("No se encontraron datos para diagnóstico.")
        return

    print(f"\nRealizando diagnóstico con {len(X_data_raw)} ejemplos:")

    for i in range(len(X_data_raw)):
        img_raw = X_data_raw[i] 

        true_label_index = y_true_indices_raw[i]
        true_label_name = interpretar_prediccion(true_label_index, class_labels_map)

        pred_index = clasificar_imagen(img_raw, modelo_nn, modelo_cnn, class_labels_map)
        
        pred_label_name = interpretar_prediccion(pred_index, class_labels_map)

        print(f"Ejemplo {i+1}: Real: {true_label_name}, Predicción: {pred_label_name}")
        
        img_display = (img_raw).astype(np.uint8) 
        cv2.imshow(f"Ejemplo {i+1} - Real: {true_label_name} - Pred: {pred_label_name}", img_display)
        cv2.waitKey(1000) 
    cv2.destroyAllWindows()


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
    ruta_base = os.path.dirname(os.path.abspath(__file__)) 
    ruta_modelos = os.path.join(ruta_base, "..", "models") 
    ruta_dataset_principal = os.path.join(ruta_base, "..", "data", "data", "dataset") 

    print("Cargando modelos...")
    try:
        # Asegúrate de cargar los modelos correctos (los generados por el entrenamiento reciente)
        nn = joblib.load(os.path.join(ruta_modelos, "nn_model_mejorado.pkl")) # Ajusta si el nombre del archivo es diferente
        cnn = joblib.load(os.path.join(ruta_modelos, "cnn_model.pkl"))
        class_labels_map = joblib.load(os.path.join(ruta_modelos, "class_labels_map.pkl"))
    except FileNotFoundError:
        print("Error: Asegúrate de haber entrenado y guardado los modelos (nn_model_mejorado.pkl, cnn_model.pkl, class_labels_map.pkl) en la carpeta 'models'.")
        sys.exit(1)

    ruta_imagen_ejemplo = os.path.join(ruta_dataset_principal, "A_U", "A_U_1.png") 
    if os.path.exists(ruta_imagen_ejemplo):
        print(f"\nClasificando imagen de ejemplo: {ruta_imagen_ejemplo}")
        try:
            pred_index = clasificar_imagen(ruta_imagen_ejemplo, nn, cnn, class_labels_map)
            print(f"Predicción Red Neuronal: {etiqueta_a_letra(interpretar_prediccion(pred_index, class_labels_map))}")
        except ValueError as e:
            print(f"Error al clasificar la imagen: {e}")
    else:
        print(f"No se encontró la imagen de ejemplo en {ruta_imagen_ejemplo}. Proporciona una ruta válida o salta.")
        
    ruta_imagen_input = input("\nIngrese la ruta de una imagen a clasificar (deje vacío para saltar): ")
    if ruta_imagen_input:
        ruta_imagen_input = os.path.abspath(ruta_imagen_input) 
        try:
            pred_index = clasificar_imagen(ruta_imagen_input, nn, cnn, class_labels_map)
            print(f"Predicción Red Neuronal: {etiqueta_a_letra(interpretar_prediccion(pred_index, class_labels_map))}")
        except ValueError as e:
            print(f"Error al clasificar la imagen: {e}")

    usar_conjunto_datos = input("¿Desea clasificar un conjunto de datos completo (para evaluación)? (s/n): ").lower()
    if usar_conjunto_datos == 's':
        print("\nClasificando conjunto de datos para evaluación...")
        # Limitar num_workers para no sobrecargar el sistema si no hay suficiente RAM
        predictions, true_labels = clasificar_conjunto_datos(ruta_dataset_principal, nn, cnn, class_labels_map, max_por_carpeta=100, num_workers=os.cpu_count()) 

        if len(predictions) > 0:
            from sklearn.metrics import classification_report, confusion_matrix
            class_names = [k for k, v in sorted(class_labels_map.items(), key=lambda item: item[1])]
            print("\nReporte de Clasificación del Conjunto de Datos:")
            print(classification_report(true_labels, predictions, target_names=class_names, zero_division=0))
            print("\nMatriz de Confusión del Conjunto de Datos:")
            print(confusion_matrix(true_labels, predictions))
        else:
            print("No se pudieron cargar datos para la clasificación del conjunto.")

    usar_diagnostico = input("¿Desea realizar un diagnóstico visual del modelo? (s/n): ").lower()
    if usar_diagnostico == 's':
        diagnosticar_modelo(ruta_dataset_principal, nn, cnn, class_labels_map, num_ejemplos=5, num_workers=os.cpu_count())