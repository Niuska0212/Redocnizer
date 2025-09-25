# preprocessing.py

import cv2
import numpy as np
import tensorflow as tf

# Importamos las constantes de tamaño que definiste para tu modelo CRNN
# Esto asegura que el preprocesamiento coincida con el entrenamiento.
try:
    from crnn_inference import IMG_HEIGHT, IMG_WIDTH
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