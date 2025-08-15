import os
import numpy as np
import cv2  # Para cargar imágenes
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def cargar_imagen_individual(ruta):
    """Carga y redimensiona una imagen individual."""
    imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        return None
    imagen_suavizada = cv2.GaussianBlur(imagen, (3,3),0) # Metodo de Gauss para reducion de ruido
    imagen_binarizada = cv2.daptivethreshold(imagen_suavizada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 5,2) #Ajustar el threshold adaptativo para mejora de contraste
    kernel = np.ones((2,2), np.uint8)
    imagen_dilatada = cv2.dilate(imagen_binarizada, kernel, iterations=1) # Dilatacion para eliminar ruido
    imagen = cv2.resize(imagen_dilatada, (28, 28)) 
    return imagen

def cargar_datos_split(directorio, test_size=0.2, random_state=42, max_por_carpeta=None, num_workers=os.cpu_count()):
    X = []
    y = []
    class_labels_map = {}
    current_label_index = 0

    carpetas = sorted([d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))])

    print(f"Cargando datos con {num_workers} workers...")
    
    # Usar ThreadPoolExecutor para cargar imágenes en paralelo
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures_to_label = {} # Para mapear futuros a sus etiquetas

        for carpeta_nombre in carpetas:
            carpeta_path = os.path.join(directorio, carpeta_nombre)
            
            if carpeta_nombre not in class_labels_map:
                class_labels_map[carpeta_nombre] = current_label_index
                current_label_index += 1
            
            indice = class_labels_map[carpeta_nombre]
            
            archivos = [f for f in os.listdir(carpeta_path) if re.match(r'.*\.png$', f)]
            
            if max_por_carpeta:
                if len(archivos) > max_por_carpeta:
                    archivos = random.sample(archivos, max_por_carpeta)
                else:
                    random.shuffle(archivos)
            else:
                random.shuffle(archivos) # Shuffle siempre para aleatoriedad

            for archivo in archivos:
                ruta = os.path.join(carpeta_path, archivo)
                # Enviar la tarea de carga al pool de hilos
                future = executor.submit(cargar_imagen_individual, ruta)
                futures_to_label[future] = indice
        
        # Recolectar resultados a medida que se completan
        for future in as_completed(futures_to_label):
            imagen = future.result()
            if imagen is not None:
                X.append(imagen)
                y.append(futures_to_label[future])

    X = np.array(X, dtype=np.float32) 
    y = np.array(y)

    np.random.seed(random_state)
    indices = np.arange(len(X))
    np.random.shuffle(indices)
    X, y = X[indices], y[indices]

    split = int(len(X) * (1 - test_size))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    return X_train, X_test, y_train, y_test, class_labels_map


def cargar_datos(directorio, max_por_carpeta=None, num_workers=os.cpu_count()):
    """
    Carga todos los datos de un directorio de forma similar a cargar_datos_split
    pero sin dividir en train/test. Usa paralelización.
    """
    X = []
    y = []
    class_labels_map = {}
    current_label_index = 0
    carpetas = sorted([d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))])
    
    print(f"Cargando datos (full set) con {num_workers} workers...")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures_to_label = {}

        for carpeta_nombre in carpetas:
            carpeta_path = os.path.join(directorio, carpeta_nombre)
            
            if carpeta_nombre not in class_labels_map:
                class_labels_map[carpeta_nombre] = current_label_index
                current_label_index += 1
            
            indice = class_labels_map[carpeta_nombre]
            
            archivos = [f for f in os.listdir(carpeta_path) if re.match(r'.*\.png$', f)]
            
            if max_por_carpeta:
                if len(archivos) > max_por_carpeta:
                    archivos = random.sample(archivos, max_por_carpeta)
                else:
                    random.shuffle(archivos)
            else:
                random.shuffle(archivos)

            for archivo in archivos:
                ruta = os.path.join(carpeta_path, archivo)
                future = executor.submit(cargar_imagen_individual, ruta)
                futures_to_label[future] = indice
        
        for future in as_completed(futures_to_label):
            imagen = future.result()
            if imagen is not None:
                X.append(imagen)
                y.append(futures_to_label[future])
    
    X = np.array(X, dtype=np.float32)
    y = np.array(y)
    
    indices = np.arange(len(X))
    np.random.shuffle(indices)
    X, y = X[indices], y[indices]

    return X, y, class_labels_map


if __name__ == "__main__":
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    # Ajusta esta ruta a tu directorio de datos principal
    directorio_dataset = os.path.join(ruta_base, "..", "data", "data", "dataset") 

    print(f"Probando cargar_datos_split de: {directorio_dataset}")
    # Puedes ajustar max_por_carpeta o quitarlo si quieres cargar todo
    X_train, X_test, y_train, y_test, class_labels_map = cargar_datos_split(directorio_dataset, max_por_carpeta=100) 
    
    print(f"Forma de X_train: {X_train.shape}")
    print(f"Forma de y_train: {y_train.shape}")
    print(f"Forma de X_test: {X_test.shape}")
    print(f"Forma de y_test: {y_test.shape}")
    print(f"Número de clases: {len(class_labels_map)}")
    print(f"Mapeo de clases: {class_labels_map}")

    # # El diagnóstico visual de 'modificar_imagen' ya no es relevante si lo quitamos
    # if len(X_train) > 0:
    #     ejemplo_imagen = X_train[0]
    #     cv2.imshow("Original (desde cargar_datos_split)", ejemplo_imagen.astype(np.uint8))
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()