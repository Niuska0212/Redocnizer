# core/preprocessing.py

import cv2
import numpy as np


IMG_HEIGHT = 32
IMG_WIDTH = 256

def get_adaptive_brightness(img: np.ndarray) -> np.ndarray:
    """
    Detecta si hay zonas oscuras (etiquetas sombreadas) y aplica 
    una corrección local para resaltar texto tenue.
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # Es vital para etiquetas oscuras porque mejora el contraste por secciones pequeñas.
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(img)
    
    # 2. Umbralizado suave (Denoising) para no perder trazos finos
    img_denoised = cv2.fastNlMeansDenoising(img_clahe, None, 10, 7, 21)
    
    return img_denoised

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
    Versión mejorada: Maneja etiquetas oscuras y datos claros simultáneamente.
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Paso A: Rescatar detalles en sombras (Etiquetas oscuras)
    img_rescatada = get_adaptive_brightness(img)

    # Paso B: Normalización agresiva
    # Estiramos el histograma para que lo más oscuro sea negro y lo más claro blanco puro
    img_norm = cv2.normalize(img_rescatada, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    # Paso C: Corrección Gamma dinámica
    # Si la imagen sigue siendo oscura en promedio, bajamos el gamma para iluminar
    mean_brightness = np.mean(img_norm)
    gamma = 0.6 if mean_brightness < 120 else 0.85
    
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    img_gamma = cv2.LUT(img_norm, table)

    # Paso D: Sharpening (Afilado) de bordes
    # Esto ayuda a que el OCR distinga letras pegadas
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    final_img = cv2.filter2D(img_gamma, -1, kernel)

    return final_img

def prepare_roi_for_ocr(roi_image: np.ndarray) -> np.ndarray:
    """Prepara el tensor para el modelo CRNN con el nuevo preprocesamiento."""
    if roi_image.size == 0:
        return np.zeros((1, IMG_HEIGHT, IMG_WIDTH, 1), dtype=np.float32)

    # Usamos la nueva lógica de brillo adaptativo
    roi_improved = increase_brightness_and_contrast(roi_image)

    # Redimensionar usando INTER_CUBIC para no pixelar las letras pequeñas
    img_resized = cv2.resize(roi_improved, (IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_CUBIC)

    # Normalización final
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