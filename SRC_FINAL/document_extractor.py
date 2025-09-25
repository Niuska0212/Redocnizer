# document_extractor.py (COMPLETO Y FINAL CON LÓGICA DE CORRECCIÓN HÍBRIDA)
import random
import cv2
import os
import pandas as pd
import numpy as np
import pytesseract 
import tensorflow.keras.backend as K 
from difflib import SequenceMatcher # Necesario para calcular la similitud (Levenshtein)

# Importamos solo lo que se puede exportar fácilmente desde crnn_inference.py
from crnn_inference import load_inference_model 
from preprocessing import prepare_roi_for_ocr 

# >>> CONFIGURACIÓN IMPORTANTE DE TESSERACT <<<
# Reemplaza esta ruta con la ruta donde instalaste tesseract.exe, ¡solo si es necesario!
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_IMAGENES = os.path.join(BASE_DIR, "..", "data", "data", "contratos", "imagenes_jpg")
RUTA_SALIDA_CSV = os.path.join(BASE_DIR, "datos_extraidos_contratos.csv")
# Si necesitas las constantes de imagen:
# from crnn_inference import IMG_HEIGHT, IMG_WIDTH # Descomenta si las necesitas en este script

# =========================================================================
# === FUNCIÓN DE DECODIFICACIÓN (Local para evitar errores de importación) ===
# =========================================================================

def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    """Decodifica las predicciones del modelo usando CTC."""
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    # K.ctc_decode requiere la importación 'import tensorflow.keras.backend as K'
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    for seq in K.get_value(results):
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words


# =========================================================================
# === DEFINICIÓN DE LAS REGIONES DE INTERÉS (ROI) - COORDENADAS AJUSTADAS ===
# =========================================================================
ROIS_CONTRATO = {
    'PATERNO': [205, 110, 40, 205],
    'MATERNO': [205, 305, 40, 205],
    'NOMBRE_S': [205, 515, 40, 315],
    'NUM': [261, 808, 50, 252],     
    'CODIGO': [315, 872, 60, 176],  
    'RFC': [380, 132, 60, 213],     
    'IMSS': [378, 339, 61, 231],    
    'CURP': [377, 563, 55, 489],    
    'DOMICILIO': [432, 131, 63, 747],
    'TELEFONO': [429, 870, 66, 180],
    'CRN': [653, 134, 67, 178],
    'HRS_TOTALES': [651, 306, 69, 278],
    'DESDE': [650, 571, 68, 250],
    'HASTA': [649, 812, 66, 245],
    'DEPENDENCIA': [715, 134, 135, 932], 
}


# =========================================================================
# === FUNCIONES DE LECTURA OCR ===
# =========================================================================

def read_with_tesseract(roi_image: np.ndarray) -> str:
    """Intenta leer el texto usando Tesseract OCR como refuerzo."""
    # Configuración del preprocesamiento y Tesseract (PSM 7 para una sola línea)
    _, img_thresh = cv2.threshold(roi_image, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    config_tess = '--psm 7'
    try:
        text = pytesseract.image_to_string(img_thresh, config=config_tess)
        return text.strip()
    except Exception as e:
        # print(f"Error en Tesseract: {e}") # Opcional: Descomentar para debug
        return ""


def extract_data_from_image(image_path, modelo_inferencia, index_to_char, output_sequence_length):
    """
    Coordina la extracción de datos usando el CRNN y Tesseract con validación híbrida.
    """
    extracted_data = {'Archivo': os.path.basename(image_path)}
    img_full = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img_full is None:
        return extracted_data, f"Error: No se pudo cargar la imagen {os.path.basename(image_path)}"

    for field_name, (y, x, h, w) in ROIS_CONTRATO.items():
        roi_image = img_full[y : y + h, x : x + w]
        if roi_image.size == 0:
            extracted_data[field_name] = ""
            continue

        # --- ESTRATEGIA HÍBRIDA CON CORRECCIÓN DE ERRORES ---

        # 1. Lectura con el modelo BASE (CRNN)
        X_input = prepare_roi_for_ocr(roi_image)
        y_pred_probs = modelo_inferencia.predict(X_input, verbose=0)
        pred_words_crnn = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
        ocr_result_base = pred_words_crnn[0].upper().strip() if pred_words_crnn else "" # Normalizamos a mayúsculas
        
        # 2. Lectura con el modelo de REFUERZO (Tesseract)
        ocr_result_refuerzo = read_with_tesseract(roi_image).upper().strip() # Normalizamos a mayúsculas
        
        
        # 3. Lógica de SELECCIÓN Y CORRECCIÓN (Levenshtein)
        
        final_result = ocr_result_base
        
        # Ambos resultados existen: Aplicamos la validación cruzada
        if ocr_result_base and ocr_result_refuerzo:
            # Calcular la similitud entre las dos predicciones
            similarity = SequenceMatcher(None, ocr_result_base, ocr_result_refuerzo).ratio()
            
            # Umbral de Similitud: Si son muy diferentes, es probable que el CRNN se haya equivocado.
            SIMILARITY_THRESHOLD = 0.70 
            
            if similarity < SIMILARITY_THRESHOLD:
                # Si son muy diferentes (error de precisión), confiamos en el Plan B (Tesseract)
                final_result = ocr_result_refuerzo 
                # print(f"Corrección {field_name}: CRNN={ocr_result_base} -> Tesseract={ocr_result_refuerzo}") # Debug
        
        # Un resultado existe y el otro no: Actúa como respaldo simple (el CRNN tiene prioridad)
        elif not ocr_result_base and ocr_result_refuerzo:
            final_result = ocr_result_refuerzo 
            
        # Fallo Total o solo el CRNN predice algo (lo cual ya está en final_result)
        
        extracted_data[field_name] = final_result
            
    return extracted_data, None


# =========================================================================
# === FUNCIÓN PRINCIPAL ===
# =========================================================================

def main():
    # Cargar el modelo CRNN (Tu base de conocimiento)
    modelo_inferencia, index_to_char, output_sequence_length = load_inference_model()
    if modelo_inferencia is None:
        print("\nEl programa no puede continuar sin el modelo de inferencia.")
        return

    # Preparar el proceso de extracción
    all_files = [f for f in os.listdir(RUTA_IMAGENES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if len(all_files) > 100:
        all_files = random.sample(all_files, 100)  # Para pruebas, limitar a 100 imágenes
    all_data = []

    print(f"\nIniciando extracción híbrida de datos de {len(all_files)} documentos...")

    for i, file_name in enumerate(all_files):
        image_path = os.path.join(RUTA_IMAGENES, file_name)
        
        data, error = extract_data_from_image(
            image_path, 
            modelo_inferencia, 
            index_to_char, 
            output_sequence_length
        )

        if data:
            all_data.append(data)
        
        if error:
            print(f"Error procesando {file_name}: {error}")

        if (i + 1) % 50 == 0 or (i + 1) == len(all_files):
            print(f"-> {i + 1}/{len(all_files)} documentos procesados.")

    # Guardar los resultados
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(RUTA_SALIDA_CSV, index=False, encoding='utf-8')
        print(f"\n✅ Extracción híbrida completada. Datos guardados en: {RUTA_SALIDA_CSV}")
    else:
        print("\n❌ No se extrajeron datos.")


if __name__ == "__main__":
    main()