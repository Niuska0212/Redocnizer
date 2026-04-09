# core/preprocessing.py

import cv2
import numpy as np


IMG_HEIGHT = 32
IMG_WIDTH = 256

def enhance_for_easyocr(img: np.ndarray) -> np.ndarray:
    """
    Optimiza la imagen específicamente para EasyOCR.
    Mantiene la escala de grises pero resalta bordes sin binarizar agresivamente.
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Eliminar ruido de fondo manteniendo bordes
    img_denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    
    # 2. CLAHE moderado
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(img_denoised)
    
    return img_clahe

def increase_brightness_and_contrast(img: np.ndarray) -> np.ndarray:
    """
    Aclara imágenes y estira el contraste. 
    Ajustado para no deformar el número '1' en '4'.
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Normalización controlada (evita quemar los blancos)
    img_norm = cv2.normalize(img, None, alpha=10, beta=245, norm_type=cv2.NORM_MINMAX)

    # 2. Gamma suave (0.8 es menos agresivo que 0.7)
    gamma = 0.8 
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    img_bright = cv2.LUT(img_norm, table)

    # 3. Sharpening sutil (Kernel de 5 elementos en lugar de 9 para evitar ruido)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    final_img = cv2.filter2D(img_bright, -1, kernel)

    return final_img

def prepare_roi_for_ocr(roi_image: np.ndarray) -> np.ndarray:
    """Prepara el tensor para tu modelo CRNN actual."""
    if roi_image.size == 0:
        return np.zeros((1, IMG_HEIGHT, IMG_WIDTH, 1), dtype=np.float32)

    # Mejoramos brillo y contraste
    roi_improved = increase_brightness_and_contrast(roi_image)

    # Redimensionar con INTER_AREA para reducir aliasing (mejor para números)
    img_resized = cv2.resize(roi_improved, (IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_AREA)

    # Normalización para el modelo (0 a 1)
    X_input = img_resized.astype(np.float32) / 255.0
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