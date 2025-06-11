import os
import numpy as np
import cv2  # Para cargar imágenes
import random 


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
    #Despues de escalar, recortar la imagen para que vuelva a ser de 28x28, asi que la re-dimensionamos y centramos
    if imagen.shape[0] > 28 or imagen.shape[1] > 28: # Si la imagen es mayor a 28x28, recort ael centro
        start_x = max(0, (imagen.shape[1] - 28) // 2)
        start_y = max(0, (imagen.shape[0] - 28) // 2)
        imagen = imagen[start_y:start_y + 28, start_x:start_x + 28]

    imagen = cv2.resize(imagen, (28, 28), interpolation= cv2.INTER_AREA)  # Asegurarse de que la imagen es de 28x28
    
    #4. Ruido aleatorio (agregar ruido gaussiano a la imagen)
    if random.random() < 0.2: #Apliucar ruido al 20% de las imagenes
        row, col = imagen.shape
        mean = 0 
        var = random.uniform(40, 80) #Variacion del ruido entre 50 y 150
        sigma = var ** 0.5
        gauss = np.random.normal(mean, sigma, (row, col))
        imagen = imagen + gauss
        imagen = np.clip(imagen, 0, 255).astype(np.uint8)  # Asegurarse de que los valores estén entre 0 y 255



    #if not hasattr(modificar_imagen, "contador"):
    #    modificar_imagen.contador = 0
    #if modificar_imagen.contador < 10 and random.random() < 0.8:  # Guardar solo el 10% de las imágenes modificadas y con probabilidad del 80% 
        #ruta_debug = os.path.join(os.path.dirname(__file__), "debug", f"debug_modificada_{modificar_imagen.contador}.png")
        #cv2.imwrite(ruta_debug, imagen)
        #modificar_imagen.contador += 1

    return imagen



def cargar_datos(directorio_base, is_training=False):
    """Carga imágenes desde un directorio y las convierte en datos numéricos."""
    X, y = [], []

    # Verifica si el directorio existe
    if not os.path.exists(directorio_base):
        raise FileNotFoundError(f"El directorio {directorio_base} no existe.")
    
    carpetas= [f for f in os.listdir(directorio_base) if os.path.isdir(os.path.join(directorio_base, f))]
    #detecta si es dataset extendido (mayusculas/minusculas)
    if any("_U" in c or "_L" in c for c in carpetas):
        print("Detectado dataset extendido (mayúsculas y minúsculas).")
        # Si es dataset extendido, filtra las carpetas que contienen "_U" o "_L"
        etiquetas = {
            **{str(i): i for i in range(10)},  # Números del 0 al 9
            **{f"{chr(65 + i )}_U": 10 + i for i in range(26)},  # Letras mayúsculas A-Z
            **{f"{chr(97 + i )}_L": 36 + i for i in range(26)}  # Letras minúsculas a-z
        }
        print("Usando mapeo extendido (mayusculas y minúsculas).")

    else:
        # Mapeo automático para dataset simple
        etiquetas = {nombre: i for i, nombre in enumerate(sorted(f for f in os.listdir(directorio_base) if os.path.isdir(os.path.join(directorio_base, f))))}
        #etiquetas = {nombre: i for i, nombre in enumerate(sorted(carpetas))}
        print("Usando mapeo automático simple.")

    max_por_carpeta = 400  # Máximo de imágenes por carpeta
    for etiqueta, indice in etiquetas.items():  # Recorre todas las carpetas A-Z, 0-9
        #if etiqueta != "B":
        #     continue
        carpeta = os.path.join(directorio_base, etiqueta)
        if os.path.isdir(carpeta):  # Verifica que es una carpeta
            contador = 0
            #print(f"Procesando carpeta: {etiqueta} ({carpeta})")
            for archivo in os.listdir(carpeta):  # Lee cada imagen
                
                
                ruta = os.path.join(carpeta, archivo)
                imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)  # Carga en escala de grises

                if imagen is None:  # Verifica si la imagen es válida
                    print(f"Error al cargar la imagen {ruta}. Se omite.")
                    continue  # Salta esta imagen y sigue con la siguiente

                if is_training and random.random() < 0.90:  # solo modifica el 70% de las imágenes si es entrenamiento
                    imagen = modificar_imagen(imagen)

                imagen = cv2.resize(imagen, (28, 28)).flatten()  # Redimensiona y aplana
                X.append(imagen)
                y.append(indice)  # Usa el nombre de la carpeta como etiqueta
                
    print(f"Se cargaron {len(X)} imágenes.")
    return np.array(X, dtype=np.float32) / 255.0, np.array(y)

if __name__ == "__main__":
    # Usa la ruta absoluta
    #directorio_training = r"N:\Proyecto modular\data\data\training_data"

    # Usa la ruta relativa
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_training = os.path.join(directorio_actual, "..", "data", "data", "training_data")

    # Verifica la ruta
    print(f"Intentando acceder a: {directorio_training}")

    # Carga los datos
    X, y = cargar_datos(directorio_training)
    print(f"Se cargaron {len(X)} imágenes de entrenamiento.")




