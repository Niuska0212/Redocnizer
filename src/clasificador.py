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

def clasificar_imagen(ruta_imagen, modelo_nn):
    #"""Clasifica una imagen con CNN y la Red Neuronal."""
    # Cargar la imagen
    from entrenamiento import ConvolutionalNeuralNetwork
    cnn = ConvolutionalNeuralNetwork()
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        raise ValueError(f"No se pudo cargar la imagen en {ruta_imagen}")

    imagen = cv2.resize(imagen, (28, 28)).astype(np.float32) / 255.0  # Redimensionar, aplanar y normalizar la imagen
    features = cnn.extraer_caracteristicas(imagen).flatten().reshape(1, -1)  # Extraer características con la CNN
    # Hacer la predicción
    nn_pred = modelo_nn.predict(features)[0]

    return nn_pred


def clasificar_conjunto_datos(ruta_datos, modelo_nn):
    """Clasifica un conjunto de datos completo."""
    from entrenamiento import ConvolutionalNeuralNetwork
    cnn= ConvolutionalNeuralNetwork()
    X, y = cargar_datos(ruta_datos, is_training=False)  # Cargar datos sin modificaciones
    X_features = np.array([cnn.extraer_caracteristicas(x.reshape(28, 28)).flatten() for x in X])  # Extraer características de cada imagen
    nn_predicciones = modelo_nn.predict(X_features)

    return nn_predicciones, y

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
    nn = joblib.load(os.path.join(ruta_modelos, "nn_model.pkl"))

    # Clasificar una imagen individual
    ruta_imagen = input("Ingrese la ruta de la imagen a clasificar: ")
    ruta_imagen = os.path.abspath(ruta_imagen)  # Convertir a ruta absoluta
    pred = clasificar_imagen(ruta_imagen, nn)

    print(f"Predicción Red Neuronal: {interpretar_prediccion(pred)}")

    # Clasificar un conjunto de datos (opcional)
    usar_conjunto_datos = input("¿Desea clasificar un conjunto de datos? (s/n): ").lower()
    if usar_conjunto_datos == 's':
        ruta_datos = input("Ingrese la ruta del conjunto de datos: ")
        ruta_datos = os.path.abspath(ruta_datos)  # Convertir a ruta absoluta
        nn_preds, y_true = clasificar_conjunto_datos(ruta_datos, nn)

        # Calcular precisión
        precision = np.mean(nn_preds == y_true)

        print(f"Precisión Red Neuronal: {precision * 100:.2f}%")