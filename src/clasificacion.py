import numpy as np
import cv2
import joblib
from preprocesamiento import cargar_datos

def clasificar_imagen(ruta_imagen, modelo_knn, modelo_nn):
    """Clasifica una imagen con KNN y la Red Neuronal."""
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    imagen = cv2.resize(imagen, (28, 28)).flatten().astype(np.float32) / 255.0

    knn_pred = modelo_knn.predict([imagen])[0]
    nn_pred = np.argmax(modelo_nn.predict(np.array([imagen])))

    return imagen, knn_pred, nn_pred

def actualizar_datos(ruta_imagen, imagen, label_correcto, archivo_datos):
    """Guarda la imagen y la etiqueta correguida en un archivo de datos para mejorar el modelo"""
    try:
        #Cargar datos existentes
        datos = np.load(archivo_datos, allow_pickle=True)
        X, y = datos["X"], datos["y"]
    except FileNotFoundError:
        #Si no existe crear un nuevo dataset
        X, y = np.array([]).reshape(0, 784), np.array([])

    #Agregar nueva imagen y etiqueta corregida
    X= np.vstack([X, imagen])
    y= np.append(y, label_correcto)

    #Guardar los datos corregidos
    np.savez(archivo_datos, X=X, y=y)
    print("Datos actualizados con la corrección")

if __name__ == "__main__":
    print("Cargando modelos...")
    knn = joblib.load("../models/knn_model.pkl")
    nn = joblib.load("../models/nn_model.pkl")

    ruta_imagen = input("Ingrese la ruta de la imagen a clasificar: ")
    imagen, knn_pred, nn_pred = clasificar_imagen(ruta_imagen, knn, nn)

    print(f"Predicción KNN: {knn_pred}")
    print(f"Predicción Red Neuronal: {nn_pred}")

    es_correcto = input("¿Es correcta la prediccion? (s/n): ").strip().lower()

    if es_correcto == "n":
        label_correcto = int(input("Ingrese la categoria correcta: "))
        actualizar_datos(ruta_imagen, imagen, label_correcto, "datos_corregidos.npz")
        print("La informacion se ha guardado")
