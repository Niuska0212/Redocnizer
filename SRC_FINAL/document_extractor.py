# document_extractor.py (ACTUALIZADO CON REFUERZO OCR HÍBRIDO)

import cv2
import os
import pandas as pd
import numpy as np
# Importamos la librería para el OCR de refuerzo
import pytesseract 
from crnn_inference import load_inference_model, decode_batch_predictions, IMG_HEIGHT, IMG_WIDTH
from preprocessing import prepare_roi_for_ocr 

# --- CONFIGURACIÓN DE RUTAS ---
# ... (Rutas iguales) ...
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_IMAGENES = os.path.join(BASE_DIR, "..", "data", "data", "contratos", "imagenes_jpg")
RUTA_SALIDA_CSV = os.path.join(BASE_DIR, "datos_extraidos_contratos.csv")

# =========================================================================
# === DEFINICIÓN DE LAS REGIONES DE INTERÉS (ROI) - USANDO COORDENADAS AJUSTADAS ======
# (Se mantienen los ROIs ajustados de la respuesta anterior)
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

def read_with_tesseract(roi_image: np.ndarray) -> str:
    """Intenta leer el texto usando Tesseract OCR como refuerzo."""
    # Tesseract funciona mejor con imágenes en escala de grises o binarias
    # Aplicamos un umbral simple para mejorar la lectura de Tesseract
    _, img_thresh = cv2.threshold(roi_image, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Configuración de Tesseract: solo alfanumérico, sin diccionario, forzar reconocimiento
    config_tess = '--psm 7' # PSM 7: Imagen de una sola línea
    
    try:
        text = pytesseract.image_to_string(img_thresh, config=config_tess)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract no encontrado. ¿Está instalado en su sistema?")
        return ""
    except Exception as e:
        # print(f"Error en Tesseract: {e}")
        return ""


def extract_data_from_image(image_path, modelo_inferencia, index_to_char, output_sequence_length):
    """
    Coordina la extracción de datos usando el CRNN y Tesseract como modelo de refuerzo.
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

        # --- ESTRATEGIA HÍBRIDA (Transfer Learning) ---

        # 1. Lectura con el modelo BASE (Tu CRNN entrenado)
        X_input = prepare_roi_for_ocr(roi_image)
        y_pred_probs = modelo_inferencia.predict(X_input, verbose=0)
        pred_words_crnn = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
        ocr_result_base = pred_words_crnn[0] if pred_words_crnn else ""

        # 2. Lectura con el modelo de REFUERZO (Tesseract - OCR generalista)
        ocr_result_refuerzo = read_with_tesseract(roi_image)
        
        # 3. Lógica de SELECCIÓN Y COMBINACIÓN (Ej. Preferir CRNN si no está vacío, sino usar Tesseract)
        if ocr_result_base:
            # Usar tu modelo entrenado por defecto, ya que es especializado
            extracted_data[field_name] = ocr_result_base
        elif ocr_result_refuerzo:
            # Si tu modelo falla, usar el OCR generalista como respaldo
            extracted_data[field_name] = ocr_result_refuerzo
        else:
            extracted_data[field_name] = ""
            
    return extracted_data, None


def main():
    # Cargar el modelo CRNN (Tu base de conocimiento)
    modelo_inferencia, index_to_char, output_sequence_length = load_inference_model()
    if modelo_inferencia is None:
        return

    # Preparar el proceso de extracción
    all_files = [f for f in os.listdir(RUTA_IMAGENES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    all_data = []

    print(f"\nIniciando extracción híbrida de datos de {len(all_files)} documentos...")

    for i, file_name in enumerate(all_files):
        # ... (Bucle de procesamiento y guardado) ...
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

        if (i + 1) % 100 == 0 or (i + 1) == len(all_files):
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