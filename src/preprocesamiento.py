import os
import numpy as np
import cv2  # Para cargar imágenes


def cargar_datos(directorio_base):
    """Carga imágenes desde un directorio y las convierte en datos numéricos."""
    X, y = [], []
    etiquetas = {nombre: i for i, nombre in enumerate(sorted(os.listdir(directorio_base)))}

    for etiqueta, indice in etiquetas.items():
        carpeta = os.path.join(directorio_base, etiqueta)
        if os.path.isdir(carpeta):
            for archivo in os.listdir(carpeta):
                ruta = os.path.join(carpeta, archivo)
                imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)  # Carga en escala de grises
                imagen = cv2.resize(imagen, (28, 28)).flatten()  # Redimensiona y aplana
                X.append(imagen)
                y.append(indice)

    return np.array(X, dtype=np.float32) / 255.0, np.array(y)

if __name__ == "__main__":
    directorio_training = os.path.join("..", "data", "data", "training_data")
    X, y = cargar_datos(directorio_training)
    print(f"Se cargaron {len(X)} imágenes de entrenamiento.")
