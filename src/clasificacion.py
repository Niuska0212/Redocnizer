import numpy as np
import cv2
import os
import joblib
from preprocesamiento import cargar_datos

def clasificar_imagen(ruta_imagen, modelo_knn, modelo_nn):
    """Clasifica una imagen con KNN y la Red Neuronal."""
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


if __name__ == "__main__":
    #obtener la ruta base del proyecto
    ruta_base = os.path.dirname(os.path.abspath(__file__)) #Sube un nivel desde /src
    ruta_modelos = os.path.join(ruta_base, "models")

    print("Cargando modelos...")
    knn = joblib.load(os.path.join(ruta_modelos, "knn_model.pkl"))
    nn = joblib.load(os.path.join(ruta_modelos, "nn_model.pkl"))
    #knn = joblib.load("../models/knn_model.pkl")
    #nn = joblib.load("../models/nn_model.pkl")

    # Clasificar una imagen individual
    ruta_imagen = input("Ingrese la ruta de la imagen a clasificar: ")
    knn_pred, nn_pred = clasificar_imagen(ruta_imagen, knn, nn)
    print(f"Predicción KNN: {knn_pred}")
    print(f"Predicción Red Neuronal: {nn_pred}")

    # Clasificar un conjunto de datos (opcional)
    usar_conjunto_datos = input("¿Desea clasificar un conjunto de datos? (s/n): ").lower()
    if usar_conjunto_datos == 's':
        ruta_datos = input("Ingrese la ruta del conjunto de datos: ")
        knn_preds, nn_preds, y_true = clasificar_conjunto_datos(ruta_datos, knn, nn)

        # Calcular precisión
        knn_precision = np.mean(knn_preds == y_true)
        nn_precision = np.mean(nn_preds == y_true)

        print(f"Precisión KNN: {knn_precision * 100:.2f}%")
        print(f"Precisión Red Neuronal: {nn_precision * 100:.2f}%")


    
# Compare this snippet from scr/clasificacion.py: