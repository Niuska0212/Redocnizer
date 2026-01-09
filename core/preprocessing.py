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

def prepare_roi_for_ocr(roi_image: np.ndarray) -> np.ndarray:
    """
    Prepara una imagen recortada (ROI) para ser consumida por el modelo CRNN.

    Pasos:
    1. Redimensionar a IMG_WIDTH x IMG_HEIGHT.
    2. Aplicar Filtro Gaussiano (para reducir ruido, como en tu entrenamiento).
    3. Normalizar los píxeles (0 a 1).
    4. Remodelar a (1, H, W, 1) para la entrada de Keras/TensorFlow.

    Args:
        roi_image: Imagen recortada (ROI) en escala de grises (numpy array).

    Returns:
        Un tensor 4D listo para la entrada del modelo Keras.
    """
    if roi_image.ndim == 3:
        # Asegurarse de que es escala de grises
        roi_image = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)

    if roi_image.size == 0:
        # Manejo de error si el recorte fue nulo
        return np.zeros((1, IMG_HEIGHT, IMG_WIDTH, 1), dtype=np.float32)

    # 1. Redimensionar al tamaño de entrada del CRNN (32x256)
    img_resized = cv2.resize(
        roi_image, 
        (IMG_WIDTH, IMG_HEIGHT), 
        interpolation=cv2.INTER_AREA
    )

    # 2. Aplicar Filtro Gaussiano (suavizado y reducción de ruido)
    # Usamos el mismo kernel (3, 3) que especificaste en tu código original
    img_blurred = cv2.GaussianBlur(img_resized, (3, 3), 0)

    # 3. Normalizar los píxeles a un rango de 0.0 a 1.0
    X_input = img_blurred.astype(np.float32) / 255.0

    # 4. Remodelar a (Batch_size=1, Height, Width, Channels=1)
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