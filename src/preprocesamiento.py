import os
import numpy as np
import cv2  # Para cargar imágenes


def cargar_datos(directorio_base):
    """Carga imágenes desde un directorio y las convierte en datos numéricos."""
    X, y = [], []

    # Filtra solo carpetas para evitar archivos sueltos
    etiquetas = {nombre: i for i, nombre in enumerate(sorted(f for f in os.listdir(directorio_base) if os.path.isdir(os.path.join(directorio_base, f))))}

    for etiqueta, indice in etiquetas.items(): #Recorre todas las carpetas A-Z, 0-9
        carpeta = os.path.join(directorio_base, etiqueta)
        if os.path.isdir(carpeta): #Verifica que es una carpeta
            for archivo in os.listdir(carpeta): #Lee cada imagen
                ruta = os.path.join(carpeta, archivo)
                imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)  # Carga en escala de grises

                if imagen is None: #Verifica si la imagen es valida
                    print(f"Error al cargar la imagen {ruta}")
                    continue #Salta esta imagen y sigue con la siguiente

                imagen = cv2.resize(imagen, (28, 28)).flatten()  # Redimensiona y aplana
                X.append(imagen)
                y.append(indice) #USa el nombr ede la carpeta como etiqueta

    return np.array(X, dtype=np.float32) / 255.0, np.array(y)

if __name__ == "__main__":
    directorio_training = os.path.join("..", "data", "data", "training_data")
    X, y = cargar_datos(directorio_training)
    print(f"Se cargaron {len(X)} imágenes de entrenamiento.")





