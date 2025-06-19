import os
import numpy as np
import cv2  # Para cargar imágenes
import random 
import re # Importar re para la expresión regular


def modificar_imagen(imagen):
    #inicia aummento de datos a una imagen (rotacion, traslacion, escalado, ruido).
    #1. Rotacion +/- 15 grados
    angulo = random.uniform(-15, 15)
    M_rot = cv2.getRotationMatrix2D((14, 14), angulo, 1.0)  # Centro de rotación en (14, 14)
    imagen = cv2.warpAffine(imagen, M_rot, (28, 28), borderValue=(0,0,0))

    #2. Traslacion +/- 2 pixeles (dexplazamiento leves de la imagen)
    tx , ty = random.randint(-2, 2), random.randint(-2, 2)
    M_trans = np.float32([[1, 0, tx], [0, 1, ty]])
    imagen = cv2.warpAffine(imagen,M_trans, (28, 28), borderValue=(0,0,0))

    #3. Escalado +/- 10% (ligero cambio de tamaño de la imagen)
    escala = random.uniform(0.9, 1.1) #Escala entre 90% y 110%
    imagen = cv2.resize(imagen, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
    #Después de escalar, la imagen puede no tener el tamaño 28x28. 
    #Recortar o rellenar para que siempre sea 28x28
    h, w = imagen.shape
    new_h, new_w = 28, 28
    start_h = max(0, (h - new_h) // 2)
    start_w = max(0, (w - new_w) // 2)
    imagen = imagen[start_h:start_h+new_h, start_w:start_w+new_w]
    if imagen.shape[0] != new_h or imagen.shape[1] != new_w:
        # Si el recorte no es suficiente (ej. imagen más pequeña después del escalado),
        # rellenar con ceros.
        temp_img = np.zeros((new_h, new_w), dtype=imagen.dtype)
        temp_img[:imagen.shape[0], :imagen.shape[1]] = imagen
        imagen = temp_img


    #4. Ruido Gaussiano (pequeño ruido para simular imperfecciones de las letras)
    ruido = np.random.normal(0, 5, imagen.shape).astype(np.uint8) # Desviación estándar de 5
    imagen = cv2.add(imagen, ruido) # Suma con saturación para evitar valores fuera de 0-255

    #Asegurar que la imagen siga en el rango 0-255
    imagen = np.clip(imagen, 0, 255)

    return imagen


# Función para cargar datos desde un directorio
# Esta función es crucial para el mapeo de clases
def cargar_datos_split(directorio, test_size=0.2, random_state=42, max_por_carpeta=None):
    X = []
    y = []
    # Usar un diccionario para mapear nombres de carpetas a índices numéricos
    class_labels_map = {}
    current_label_index = 0

    # Ordenar las carpetas para asegurar un mapeo consistente entre ejecuciones
    carpetas = sorted([d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))])

    for carpeta_nombre in carpetas:
        carpeta_path = os.path.join(directorio, carpeta_nombre)
        
        # Asignar un índice numérico a la clase si no existe
        if carpeta_nombre not in class_labels_map:
            class_labels_map[carpeta_nombre] = current_label_index
            current_label_index += 1
        
        indice = class_labels_map[carpeta_nombre]
        
        archivos = [f for f in os.listdir(carpeta_path) if re.match(r'.*\.png$', f)] # Asume archivos .png
        
        # Limitar el número de archivos por carpeta si max_por_carpeta está especificado
        if max_por_carpeta:
            if len(archivos) > max_por_carpeta:
                archivos = random.sample(archivos, max_por_carpeta)
            else:
                random.shuffle(archivos) # Shuffle incluso si no se limita para aleatoriedad
        else:
            random.shuffle(archivos) # Shuffle siempre

        for archivo in archivos:
            ruta = os.path.join(carpeta_path, archivo)
            imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if imagen is None:
                continue
            imagen = cv2.resize(imagen, (28, 28)) # Mantener como 2D
            X.append(imagen) # Las imágenes se normalizarán y aplanarán en entrenamiento.py
            y.append(indice)

    X = np.array(X, dtype=np.float32) 
    y = np.array(y)

    # Mezclar y dividir
    np.random.seed(random_state)
    indices = np.arange(len(X))
    np.random.shuffle(indices)
    X, y = X[indices], y[indices]

    split = int(len(X) * (1 - test_size))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Retornar el mapeo de clases
    return X_train, X_test, y_train, y_test, class_labels_map


# cargar_datos ahora podría ser redundante si siempre se usa cargar_datos_split
# Pero la mantengo por si la usas en otro lado y para consistencia.
def cargar_datos(directorio, max_por_carpeta=None):
    X = []
    y = []
    class_labels_map = {}
    current_label_index = 0
    carpetas = sorted([d for d in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, d))])
    
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
            imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if imagen is None:
                continue
            imagen = cv2.resize(imagen, (28, 28)) # Mantener como 2D
            X.append(imagen)
            y.append(indice)
    
    X = np.array(X, dtype=np.float32)
    y = np.array(y)
    
    # Mezclar los datos una vez cargados
    indices = np.arange(len(X))
    np.random.shuffle(indices)
    X, y = X[indices], y[indices]

    return X, y, class_labels_map


if __name__ == "__main__":
    # Usa la ruta absoluta (ajusta según tu estructura de carpetas)
    # Ejemplo: si preprocesamiento.py está en 'src/', y 'data/' está en el nivel superior
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    directorio_training = os.path.join(ruta_base, "..", "data", "data", "training_data")

    print(f"Cargando datos de: {directorio_training}")
    X_train, X_test, y_train, y_test, class_labels_map = cargar_datos_split(directorio_training, max_por_carpeta=100) # Carga limitada para prueba
    
    print(f"Forma de X_train: {X_train.shape}")
    print(f"Forma de y_train: {y_train.shape}")
    print(f"Forma de X_test: {X_test.shape}")
    print(f"Forma de y_test: {y_test.shape}")
    print(f"Número de clases: {len(class_labels_map)}")
    print(f"Mapeo de clases: {class_labels_map}")

    # Demostración del aumento de datos
    if len(X_train) > 0:
        ejemplo_imagen = X_train[0]
        cv2.imshow("Original", ejemplo_imagen.astype(np.uint8))
        cv2.waitKey(0)
        
        imagen_modificada = modificar_imagen(ejemplo_imagen.astype(np.uint8))
        cv2.imshow("Modificada", imagen_modificada)
        cv2.waitKey(0)
        cv2.destroyAllWindows()