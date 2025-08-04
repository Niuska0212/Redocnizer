import os
from src.clasificacion import clasificar_imagen
import joblib

if __name__ == "__main__":
    print("Cargando modelos entrenados...")
    knn = joblib.load("models/knn_model.pkl")
    nn = joblib.load("models/nn_model.pkl")

    ruta_imagen = input("Ingrese la ruta de la imagen: ")
    if not os.path.exists(ruta_imagen):
        print("La imagen no existe.")
    else:
        knn_pred, nn_pred = clasificar_imagen(ruta_imagen, knn, nn)
        print(f"Predicción con KNN: {knn_pred}")
        print(f"Predicción con Red Neuronal: {nn_pred}")





#Resumen
#preprocesamiento.py  Carga imágenes en un formato numérico.
#entrenamiento.py  Entrena KNN + Red Neuronal con TODAS las imágenes a la vez.
#clasificacion.py  Usa los modelos entrenados para predecir letras/números en nuevas imágenes.
#main.py  Ejecuta todo el proceso automáticamente.
