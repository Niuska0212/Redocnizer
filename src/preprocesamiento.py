import os
import numpy as np
import cv2  # Para cargar imágenes

def cargar_datos(directorio_base):
    """Carga imágenes desde un directorio y las convierte en datos numéricos."""
    X, y = [], []

    # Verifica si el directorio existe
    if not os.path.exists(directorio_base):
        raise FileNotFoundError(f"El directorio {directorio_base} no existe.")

    # Filtra solo carpetas para evitar archivos sueltos
    etiquetas = {nombre: i for i, nombre in enumerate(sorted(f for f in os.listdir(directorio_base) if os.path.isdir(os.path.join(directorio_base, f))))}

    for etiqueta, indice in etiquetas.items():  # Recorre todas las carpetas A-Z, 0-9
        carpeta = os.path.join(directorio_base, etiqueta)
        if os.path.isdir(carpeta):  # Verifica que es una carpeta
            for archivo in os.listdir(carpeta):  # Lee cada imagen
                ruta = os.path.join(carpeta, archivo)
                imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)  # Carga en escala de grises

                if imagen is None:  # Verifica si la imagen es válida
                    print(f"Error al cargar la imagen {ruta}. Se omite.")
                    continue  # Salta esta imagen y sigue con la siguiente

                imagen = cv2.resize(imagen, (28, 28)).flatten()  # Redimensiona y aplana
                X.append(imagen)
                y.append(indice)  # Usa el nombre de la carpeta como etiqueta
    print(f"Se cargaron {len(X)} imágenes.")
    return np.array(X, dtype=np.float32) / 255.0, np.array(y)

if __name__ == "__main__":
    # Usa la ruta absoluta
    directorio_training = r"N:\Proyecto modular\data\data\training_data"

    # Verifica la ruta
    print(f"Intentando acceder a: {directorio_training}")

    # Carga los datos
    X, y = cargar_datos(directorio_training)
    print(f"Se cargaron {len(X)} imágenes de entrenamiento.")




