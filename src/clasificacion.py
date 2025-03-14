import numpy as np
import cv2
import joblib
from preprocesamiento import cargar_datos

def clasificar_imagen(ruta_imagen, modelo_knn, modelo_nn):
    """Clasifica una imagen con KNN y la Red Neuronal."""
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    imagen = cv2.resize(imagen, (28, 28)).flatten().astype(np.float32) / 255.0

    knn_pred = modelo_knn.predict([imagen])[0]
    nn_pred = modelo_nn.predict(np.array([imagen]))[0]

    return knn_pred, nn_pred

if __name__ == "__main__":
    print("Cargando modelos...")
    knn = joblib.load("../models/knn_model.pkl")
    nn = joblib.load("../models/nn_model.pkl")

    ruta_imagen = input("Ingrese la ruta de la imagen a clasificar: ")
    knn_pred, nn_pred = clasificar_imagen(ruta_imagen, knn, nn)

    print(f"Predicción KNN: {knn_pred}")
    print(f"Predicción Red Neuronal: {nn_pred}")


    
# Compare this snippet from scr/clasificacion.py: