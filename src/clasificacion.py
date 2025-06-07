import sys
import os
import numpy as np
import cv2
import joblib
from preprocesamiento import cargar_datos


# Agregar el directorio raíz del proyecto al path
ruta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ruta_proyecto not in sys.path:
    sys.path.append(ruta_proyecto)

def clasificar_imagen(ruta_imagen, modelo_knn, modelo_nn):
    #"""Clasifica una imagen con KNN y la Red Neuronal."""
    # Cargar la imagen
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        raise ValueError(f"No se pudo cargar la imagen en {ruta_imagen}")

    imagen = cv2.resize(imagen, (28, 28)).flatten()  # Redimensionar y aplanar la imagen
    imagen = imagen.astype(np.float32) / 255.0  # Normalizar la imagen

    # Hacer la predicción
    knn_pred = modelo_knn.predict([imagen])[0]
    nn_pred = modelo_nn.predict(np.array([imagen]))[0]

    return knn_pred, nn_pred


def clasificar_conjunto_datos(ruta_datos, modelo_knn, modelo_nn):
    """Clasifica un conjunto de datos completo."""
    X, y = cargar_datos(ruta_datos)
    knn_predicciones = modelo_knn.predict(X)
    nn_predicciones = modelo_nn.predict(X)

    return knn_predicciones, nn_predicciones, y

def interpretar_prediccion(valor):
    if 0 <= valor <= 9:
        return str(valor)   # Números 0-9
    elif 10 <= valor <= 35:
        return chr(valor + 55)  # Letras A-Z (A=10, B=11, ..., chr(66), etc.)
    else:
        return "No se reconoce"

if __name__ == "__main__":
    # Obtener la ruta base del proyecto
    ruta_base = os.path.dirname(os.path.abspath(__file__))  # Ruta del archivo actual
    ruta_modelos = os.path.join(ruta_base, "..", "models")  # Ruta a la carpeta de modelos

    print("Cargando modelos...")
    knn = joblib.load(os.path.join(ruta_modelos, "knn_model.pkl"))
    nn = joblib.load(os.path.join(ruta_modelos, "nn_model.pkl"))

    # Clasificar una imagen individual
    ruta_imagen = input("Ingrese la ruta de la imagen a clasificar: ")
    ruta_imagen = os.path.abspath(ruta_imagen)  # Convertir a ruta absoluta
    knn_pred, nn_pred = clasificar_imagen(ruta_imagen, knn, nn)


    
    print(f"Predicción KNN: {interpretar_prediccion(knn_pred)}")
    print(f"Predicción Red Neuronal: {interpretar_prediccion(nn_pred)}")

    # Clasificar un conjunto de datos (opcional)
    usar_conjunto_datos = input("¿Desea clasificar un conjunto de datos? (s/n): ").lower()
    if usar_conjunto_datos == 's':
        ruta_datos = input("Ingrese la ruta del conjunto de datos: ")
        ruta_datos = os.path.abspath(ruta_datos)  # Convertir a ruta absoluta
        knn_preds, nn_preds, y_true = clasificar_conjunto_datos(ruta_datos, knn, nn)

        # Calcular precisión
        knn_precision = np.mean(knn_preds == y_true)
        nn_precision = np.mean(nn_preds == y_true)

        print(f"Precisión KNN: {knn_precision * 100:.2f}%")
        print(f"Precisión Red Neuronal: {nn_precision * 100:.2f}%")