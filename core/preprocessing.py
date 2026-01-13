# preprocessing.py

import cv2
import numpy as np
import tensorflow as tf

# Importamos las constantes de tamaño que definiste para tu modelo CRNN
# Esto asegura que el preprocesamiento coincida con el entrenamiento.
try:
    from .CRNN_inference import IMG_HEIGHT, IMG_WIDTH
except ImportError:
    # Si lo ejecutas solo, definimos los valores por defecto
    IMG_HEIGHT = 32
    IMG_WIDTH = 256
    print("Advertencia: No se pudo importar IMG_HEIGHT/IMG_WIDTH. Usando valores por defecto (32x256).")

def enhance_image_contrast(img: np.ndarray) -> np.ndarray:
    """Mejora la nitidez y el contraste de imagenes oscuras usando CLAHE."""
    #1. Aseguirar que esta en escalas de grises
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #2. Acplicar CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    img_enhanced = clahe.apply(img)
    
    # 3 Opcional un filtro de enfoque (sharpening para definir mejor los bordes de las letras)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    img_sharpened = cv2.filter2D(img_enhanced, -1, kernel)
    
    return img_sharpened

def increase_brightness_and_contrast(img: np.ndarray) -> np.ndarray:
    """
    Aclara imágenes muy oscuras y estira el contraste al máximo.
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Normalización Min-Max: Estira los píxeles para que el más claro sea 255 y el más oscuro 0
    img_norm = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    # 2. Corrección Gamma (gamma < 1 aclara las zonas oscuras)
    # 0.5 a 0.8 es un buen rango para imágenes oscuras
    gamma = 0.7 
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    img_bright = cv2.LUT(img_norm, table)

    # 3. CLAHE para rematar el contraste de las letras
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    final_img = clahe.apply(img_bright)

    return final_img

def prepare_roi_for_ocr(roi_image: np.ndarray) -> np.ndarray:
    if roi_image.size == 0:
        return np.zeros((1, IMG_HEIGHT, IMG_WIDTH, 1), dtype=np.float32)

    # --- USAR LA NUEVA FUNCIÓN DE BRILLO ---
    roi_improved = increase_brightness_and_contrast(roi_image)

    # Redimensionar
    img_resized = cv2.resize(roi_improved, (IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_CUBIC)

    # Filtro Gaussiano suave para limpiar el ruido del brillo
    img_blurred = cv2.GaussianBlur(img_resized, (3, 3), 0)

    # Normalización para el modelo (0 a 1)
    X_input = img_blurred.astype(np.float32) / 255.0
    X_input = X_input.reshape(1, IMG_HEIGHT, IMG_WIDTH, 1)

    return X_input

def invert_image_color(img_full: np.ndarray) -> np.ndarray:
    """Invierte los colores de una imagen en escala de grises."""
    if len(img_full.shape) == 3: # Si es color, convertir a gris primero
        img_gray = cv2.cvtColor(img_full, cv2.COLOR_BGR2GRAY)
    else:
        img_gray = img_full
        
    # Inversión simple de la imagen
    img_inverted = cv2.bitwise_not(img_gray)
    
    # Opcional: Ecualización de histograma para aumentar el contraste en la imagen invertida
    img_inverted = cv2.equalizeHist(img_inverted) 
    
    return img_inverted


def rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rota la imagen alrededor de su centro sin recortar el contenido."""
    # Asegurar que la imagen sea gris, aunque cv2.getRotationMatrix2D funciona con gris.
    (h, w) = img.shape[:2]
    (cX, cY) = (w // 2, h // 2)

    # Obtener la matriz de rotación
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    
    # Calcular el nuevo tamaño de la imagen para evitar el recorte
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    # Nuevas dimensiones
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    
    # Ajustar la matriz para que la rotación se realice sobre el centro
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY

    # Aplicar la transformación (interpolación cúbica para mejor calidad)
    return cv2.warpAffine(img, M, (nW, nH), flags=cv2.INTER_CUBIC, borderValue=(255))

# Ejemplo de uso (solo para pruebas internas)
if __name__ == '__main__':
    # Crear una imagen simulada (blanca) de 100x40 píxeles
    dummy_img = np.ones((40, 100), dtype=np.uint8) * 200 
    
    print(f"Imagen original simulada: {dummy_img.shape}")
    
    # Preparar para el modelo
    prepared_tensor = prepare_roi_for_ocr(dummy_img)
    
    print(f"Tensor de salida listo para Keras: {prepared_tensor.shape}")
    print(f"Tipo de dato: {prepared_tensor.dtype}")
    
    # Debe ser (1, 32, 256, 1)
    if prepared_tensor.shape == (1, IMG_HEIGHT, IMG_WIDTH, 1):
        print("¡El tensor está en la forma correcta para el CRNN!")
    else:
        print("Error: El tensor no tiene la forma esperada.")