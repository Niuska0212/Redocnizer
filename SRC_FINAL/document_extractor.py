# document_extractor.py (COMPLETO Y FINAL CON LÓGICA DE CORRECCIÓN HÍBRIDA)
import random
import cv2
import os
import shutil
import pandas as pd
import re
import numpy as np
import pytesseract 
from tensorflow.keras import backend as K 
from difflib import SequenceMatcher # Necesario para calcular la similitud (Levenshtein)
from PIL import Image, ImageDraw, ImageFont
from segmentacion_dinamica import get_dynamic_rois, clean_data_by_field, clean_border_chars

# Importamos solo lo que se puede exportar fácilmente desde crnn_inference.py
from CRNN_inference import load_inference_model 
from preprocessing import prepare_roi_for_ocr 

# >>> CONFIGURACIÓN IMPORTANTE DE TESSERACT <<<
# Reemplaza esta ruta con la ruta donde instalaste tesseract.exe, ¡solo si es necesario!
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_IMAGENES = os.path.join(BASE_DIR, "..", "data", "data", "contratos", "imagenes_jpg")
RUTA_PREVIEW = os.path.join(BASE_DIR, "..", "data", "data", "contratos", "preview")
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

def split_full_name(full_name: str) -> dict:
    #Dividir el nombre completo en partes
    words =full_name.upper().strip().split()

    #Manejar el caso en el que OCR haya fallado o solo extraiga una palabra
    if len(words) < 2:
        return {'PATERNO': full_name, 'MATERNO': '', 'NOMBRE_S': ''}
    
    #Asume: paterno (primera palabra), materno (segunda palabra), nombre(s) (resto)
    paterno = words[0]
    materno = words[1]
    nombre_s = " ".join(words[2:]) 

    return {
        'PATERNO': clean_border_chars(paterno), 
        'MATERNO': clean_border_chars(materno), 
        'NOMBRE_S': clean_border_chars(nombre_s)
    }

    #return {'PATERNO': paterno, 'MATERNO': materno, 'NOMBRE_S': nombre_s}

def clean_name_contamination(name: str) -> str:

    name = name.strip()

    name = re.sub(r'\s+[A-Z0-9-]{5,15}$', '', name, flags=re.IGNORECASE).strip()

    name = re.sub(r'\s+\d{3,4}$', '', name).strip()

    name = re.sub(r'[\s\W]*[|\-,]$', '', name).strip()

    if not name:
        return ""
    
    #if len(name) < 5 and bool(re.search(r'\d', name)):
    #    return ""

    return name.strip()


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



def extract_data_from_image(image_path, modelo_inferencia, index_to_char, output_sequence_length, output_dir_preview):
    """
    Coordina la extracción de datos usando el CRNN y Tesseract con validación híbrida.
    """
    extracted_data = {'Archivo': os.path.basename(image_path)}

    img_full = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img_full is None:
        return extracted_data, f"Error: No se pudo cargar la imagen {os.path.basename(image_path)}"

    rois_dinamicas = get_dynamic_rois(img_full)
    all_extracted_data = {} # Diccionario temporal para todos los campos

    img_color = cv2.cvtColor(img_full, cv2.COLOR_GRAY2BGR) # Para debug visual si es necesario
    output_filename = "Vizualizacion_"+ os.path.basename(image_path)
    output_dir = output_dir_preview

    COLORS = {
        'NOMBRE_COMPLETO_RAW': (0, 0, 255),  # Rojo para nombre completo
        'DEPENDENCIA': (255, 0, 0),        # Azul para dependencia
        'SIMPLE_FIELD': (0, 255, 0)        # Verde para campos simples
    }

    for field_name, (y, x, h, w) in rois_dinamicas.items():
        color = COLORS.get(field_name, COLORS['SIMPLE_FIELD'])
        if field_name.startswith('DEPENDENCIA'):
            color = COLORS['DEPENDENCIA']
            
        x_end = x + w
        y_end = y + h
        cv2.rectangle(img_color, (x, y), (x_end, y_end), color, 2)

        cv2.putText(img_color, field_name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    save_path = os.path.join(output_dir, output_filename)
    cv2.imwrite(save_path, img_color)
    print(f"Visualización guardada en: {save_path}")

    for field_name, roi_data in rois_dinamicas.items():

        # Verificar que la ROI tenga 4 elementos
        if not isinstance(roi_data, (list, tuple)) or len(roi_data) != 4:
            print(f"Error: El campo  '{field_name}' tiene un valor de ROI inválido. Se esperan 4 elementos [y, x, h, w], pero se encontró: {roi_data}")
            all_extracted_data[field_name] = ""
            continue
        #Desempaquetar la ROI si la longitud es correcta
        y, x, h, w = roi_data


        img_height, img_width = img_full.shape[:2]
        
        y_end = min(y + h, img_height)
        x_end = min(x + w, img_width)
        y_start = max(y, 0)
        x_start = max(x, 0)

        roi_image = img_full[y_start : y_end, x_start : x_end]

        #Verificar si la ROI es válida
        if roi_image.size == 0 or y_end <= y_start or x_end <= x_start:
            all_extracted_data[field_name] = ""
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
        # Umbral de Similitud: Si son muy diferentes, es probable que el CRNN se haya equivocado.
        SIMILARITY_THRESHOLD = 0.70
        
        # Ambos resultados existen: Aplicamos la validación cruzada
        if ocr_result_base and ocr_result_refuerzo:
            # Calcular la similitud entre las dos predicciones
            similarity = SequenceMatcher(None, ocr_result_base, ocr_result_refuerzo).ratio()
            
            if similarity < SIMILARITY_THRESHOLD:
                # Si son muy diferentes (error de precisión), confiamos en el Plan B (Tesseract)
                final_result = ocr_result_refuerzo 
                # print(f"Corrección {field_name}: CRNN={ocr_result_base} -> Tesseract={ocr_result_refuerzo}") # Debug
        
        # Un resultado existe y el otro no: Actúa como respaldo simple (el CRNN tiene prioridad)
        elif not ocr_result_base and ocr_result_refuerzo:
            final_result = ocr_result_refuerzo

            final_result = clean_border_chars(final_result)
            
        # Fallo Total o solo el CRNN predice algo (lo cual ya está en final_result)
        
        all_extracted_data[field_name] = clean_border_chars(final_result)

    # --- POST-PROCESAMIENTO Y ESTRUCTURACIÓN DE SALIDA ---
        extracted_data = {'Archivo': os.path.basename(image_path)}

    for key, value in all_extracted_data.items():
        # Aplicamos la limpieza general Y la limpieza específica por campo
        cleaned_value = clean_data_by_field(key, clean_border_chars(value))

        if key == 'NOMBRE_COMPLETO_RAW':
            # Aplicar la funcion de division de nombre completo y añadir los 3 campos
            name_parts = split_full_name(cleaned_value)
            extracted_data.update(name_parts)
        elif key.startswith('DEPENDENCIA'):
            extracted_data[key] = cleaned_value
        # Si el campo es 'DOMICILIO', la clave no existirá aquí porque se eliminó de rois_dinamicas
        else:
            extracted_data[key] = cleaned_value

    # Asegurar que los campos PATERNO, MATERNO y NOMBRE_S existan en la salida
    if 'PATERNO' not in extracted_data: extracted_data['PATERNO'] = ''
    if 'MATERNO' not in extracted_data: extracted_data['MATERNO'] = ''
    if 'NOMBRE_S' not in extracted_data: extracted_data['NOMBRE_S'] = ''

    return extracted_data, None


def clean_and_recreate_directory(dir_path):
    """Limpia y recrea un directorio."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    os.makedirs(dir_path, exist_ok=True)

# =========================================================================
# === FUNCIÓN PRINCIPAL ===
# =========================================================================

def main():
    # Cargar el modelo CRNN (Tu base de conocimiento)
    modelo_inferencia, index_to_char, output_sequence_length = load_inference_model()
    if modelo_inferencia is None:
        print("\nEl programa no puede continuar sin el modelo de inferencia.")
        return
    
    clean_and_recreate_directory(RUTA_PREVIEW)

    # Preparar el proceso de extracción
    all_files = [f for f in os.listdir(RUTA_IMAGENES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if len(all_files) > 50:
        all_files = random.sample(all_files, 50)  # Para pruebas, limitar a 100 imágenes
    all_data = []

    print(f"\nIniciando extracción híbrida de datos de {len(all_files)} documentos...")

    for i, file_name in enumerate(all_files):
        image_path = os.path.join(RUTA_IMAGENES, file_name)
        
        data, error = extract_data_from_image(
            image_path, 
            modelo_inferencia, 
            index_to_char, 
            output_sequence_length,
            RUTA_PREVIEW
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