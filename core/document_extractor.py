# document_extractor.py
import random
import cv2
import os
import shutil
import pandas as pd 
import re
import numpy as np
import easyocr
from tensorflow.keras import backend as K 
from difflib import SequenceMatcher # Necesario para calcular la similitud (Levenshtein)
from PIL import Image, ImageDraw, ImageFont
from .segmentacion_dinamica import get_dynamic_rois, clean_data_by_field, clean_border_chars, validate_field_format, clean_name_specific, procesar_bloque_dependencias, EMPTY_DATA_PLACEHOLDER
from .CRNN_inference import load_inference_model
from .preprocessing import prepare_roi_for_ocr, invert_image_color, rotate_image, enhance_for_easyocr
from PySide6.QtCore import QSettings

# Respectar la preferencia de GPU del usuario (la UI guarda esta opción en QSettings)
settings = QSettings("CUCEI", "Redocnizer")
gpu_preference = settings.value("use_gpu_acceleration", False, type=bool)
reader = easyocr.Reader(['es', 'en'], gpu=gpu_preference)

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
    PARTICULAS = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'Y', 'MC', 'MAC', 'VON', 'VAN', 'SAN', 'SANTA', 'DI', 'DA', 'EL', 'LE', 'DE LA'}
    
    # PRIMERO: Limpiar caracteres problemáticos específicos para nombres
    full_name = re.sub(r'[=:!]', '', full_name)  # Eliminar caracteres problemáticos
    full_name = re.sub(r'\s+', ' ', full_name).strip()  # Normalizar espacios
    
    # SEGUNDO: Manejar casos donde hay comas en el nombre (como "N, AR, BEATRIZ ADRIANA")
    if ',' in full_name:
        parts = [part.strip() for part in full_name.split(',')]
        
        # Caso 1: Formato "PATERNO, MATERNO, NOMBRE" (3 partes)
        if len(parts) == 3:
            return {
                'PATERNO': clean_border_chars(parts[0]), 
                'MATERNO': clean_border_chars(parts[1]), 
                'NOMBRE_S': clean_border_chars(parts[2])
            }
        # Caso 2: Formato "PATERNO, MATERNO" (2 partes)
        elif len(parts) == 2:
            return {
                'PATERNO': clean_border_chars(parts[0]), 
                'MATERNO': clean_border_chars(parts[1]), 
                'NOMBRE_S': ''
            }
        # Caso 3: Más de 3 partes - unir las partes sobrantes como nombre
        elif len(parts) > 3:
            return {
                'PATERNO': clean_border_chars(parts[0]), 
                'MATERNO': clean_border_chars(parts[1]), 
                'NOMBRE_S': clean_border_chars(', '.join(parts[2:]))
            }
    
    # TERCERO: Lógica original para nombres sin comas
    words = full_name.upper().split()

    if len(words) < 2:
        return {'PATERNO': full_name, 'MATERNO': '', 'NOMBRE_S': ''}
    
    # --- LÓGICA DE MANEJO DE PREFIJOS INICIALES ---
    paterno_start_index = 0
    
    # Si la primera palabra es una partícula, el apellido compuesto REAL empieza con la segunda palabra.
    if words[0] in PARTICULAS and len(words) > 1:
        paterno_start_index = 0
    else:
        paterno_start_index = 0
        
    # Inicialización del índice de fin del Paterno
    paterno_end_index = paterno_start_index + 1

    # --- Lógica de Detección de Apellido Compuesto (PATERNO) ---
    for i in range(1, len(words) - 1): # Revisa de la 2da a la antepenúltima palabra
        if words[i] in PARTICULAS:
            paterno_end_index = i + 1
        else:
            break
            
    paterno_list = words[0:paterno_end_index]
    remaining_words = words[paterno_end_index:]

    paterno = ' '.join(paterno_list)

    if not remaining_words:
        return {'PATERNO': clean_border_chars(paterno), 'MATERNO': '', 'NOMBRE_S': ''}
    
    # --- Asignación de Materno y Nombre(s) ---
    materno = remaining_words[0]
    nombre_s = " ".join(remaining_words[1:])

    # Lógica para el materno compuesto
    if materno in PARTICULAS and len(remaining_words) > 1:
        materno = " ".join(remaining_words[0:2])
        nombre_s = " ".join(remaining_words[2:])

    return {
        'PATERNO': clean_border_chars(paterno), 
        'MATERNO': clean_border_chars(materno), 
        'NOMBRE_S': clean_border_chars(nombre_s)
    }

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

def read_with_easyocr(roi_image: np.ndarray) -> str:
    """Lee el texto usando EasyOCR """
    try:
        # EasyOCR funciona mejor con imágenes en color o gris sin tanto threshold agresivo
        results = reader.readtext(roi_image, detail=0) # detail=0 devuelve solo el texto
        text = " ".join(results)
        return text.strip()
    except Exception as e:
        print(f"Error en EasyOCR: {e}")
        return ""


def extract_data_from_image(image_path, modelo_inferencia, index_to_char, output_sequence_length, output_dir_preview):
    """
    Coordina la extracción de datos usando el CRNN y EasyOCR con validación híbrida.
    Implementa lógica de reintento: 0. Original -> 1. Invertida -> 2. Rotada
    """
    
    img_full_original = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_full_original is None:
        return {'Archivo': os.path.basename(image_path)}, f"Error: No se pudo cargar la imagen {os.path.basename(image_path)}"

    extracted_data_list = []
    
    # Parámetros de la lógica de reintento
    MIN_REQUIRED_FIELDS = 10 
    
    current_img = img_full_original
    
    # Bucle de 3 intentos: 0: Original, 1: Invertida, 2: Rotada
    for attempt in range(3): 
        
        # Lógica de pre-procesamiento por intento
        if attempt == 1:
            if extracted_data_list and len([v for v in extracted_data_list[0].values() if v and str(v) != EMPTY_DATA_PLACEHOLDER]) >= MIN_REQUIRED_FIELDS:
                break
            print(f"  [REINTENTO 1] Imagen invertida para {os.path.basename(image_path)}")
            current_img = invert_image_color(img_full_original)
        
        elif attempt == 2:
            if extracted_data_list and len([v for v in extracted_data_list[0].values() if v and str(v) != EMPTY_DATA_PLACEHOLDER]) >= MIN_REQUIRED_FIELDS:
                break
            print(f"  [REINTENTO 2] Imagen rotada 2 grados para {os.path.basename(image_path)}")
            current_img = rotate_image(img_full_original, 2.0) 

        # --- PRE-PROCESAMIENTO DE REGIONES DE INTERÉS (ROIS) ---
        rois_dinamicas = get_dynamic_rois(current_img)
        img_height, img_width = current_img.shape[:2]
        
        # --- VISUALIZACIÓN (Solo con el primer intento exitoso de ROI) ---
        if attempt == 0 and output_dir_preview:
            img_color = cv2.cvtColor(current_img, cv2.COLOR_GRAY2BGR)
            COLORS = {'NOMBRE_COMPLETO_RAW': (0, 0, 255), 'DEPENDENCIA': (255, 0, 0), 'SIMPLE_FIELD': (0, 255, 0)}
            
            for field_name, (y, x, h, w) in rois_dinamicas.items():
                color = COLORS.get(field_name, COLORS['SIMPLE_FIELD'])
                if 'DEPENDENCIA' in field_name: color = COLORS['DEPENDENCIA']
                cv2.rectangle(img_color, (int(x), int(y)), (int(x + w), int(y + h)), color, 2)
                cv2.putText(img_color, field_name, (int(x), max(0, int(y) - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

            save_path = os.path.join(output_dir_preview, "Viz_" + os.path.basename(image_path))
            cv2.imwrite(save_path, img_color)
        
        # --- EXTRACCIÓN OCR POR ROI ---
        all_extracted_data = {}
        for field_name, roi_data in rois_dinamicas.items():
            if not isinstance(roi_data, (list, tuple)) or len(roi_data) != 4:
                all_extracted_data[field_name] = ""
                continue

            y, x, h, w = roi_data
            y_start, x_start = max(0, int(y)), max(0, int(x))
            y_end, x_end = min(img_height, int(y + h)), min(img_width, int(x + w))

            # Ajuste de márgenes para campos específicos
            if 'DEPENDENCIA' in field_name or field_name in ['CURP', 'RFC', 'IMSS']:
                min_w, min_h = 150, 25
            else:
                min_w, min_h = 12, 12
                
            if (x_end - x_start) < min_w:
                extra = (min_w - (x_end - x_start)) // 2 + 5
                x_start, x_end = max(0, x_start - extra), min(img_width, x_end + extra)
            if (y_end - y_start) < min_h:
                extra = (min_h - (y_end - y_start)) // 2 + 5
                y_start, y_end = max(0, y_start - extra), min(img_height, y_end + extra)

            roi_image = current_img[y_start:y_end, x_start:x_end]
            if roi_image.size == 0:
                all_extracted_data[field_name] = ""
                continue
            
            # --- Lógica de Lectura ---
            if 'DEPENDENCIA' in field_name or field_name in ['CURP', 'RFC', 'IMSS']:
                try:
                    roi_for_easy = enhance_for_easyocr(roi_image)
                    final_result = read_with_easyocr(roi_for_easy).upper().strip()
                except: final_result = ""
            else:
                # Híbrido CRNN + EasyOCR
                ocr_result_base = ""
                try:
                    X_input = prepare_roi_for_ocr(roi_image)
                    y_pred_probs = modelo_inferencia.predict(X_input, verbose=0)
                    pred_words_crnn = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
                    ocr_result_base = pred_words_crnn[0].upper().strip() if pred_words_crnn else ""
                except: ocr_result_base = ""

                try:
                    roi_for_easy = enhance_for_easyocr(roi_image) 
                    ocr_result_refuerzo = read_with_easyocr(roi_for_easy).upper().strip()
                except: ocr_result_refuerzo = ""

                # Selección
                final_result = ocr_result_base or ocr_result_refuerzo
                if ocr_result_base and ocr_result_refuerzo:
                    if SequenceMatcher(None, ocr_result_base, ocr_result_refuerzo).ratio() < 0.60:
                        final_result = ocr_result_refuerzo

            # Limpieza y Validación individual
            final_result = clean_border_chars(final_result)
            cleaned_value = clean_data_by_field(field_name, final_result)
            all_extracted_data[field_name] = validate_field_format(field_name, cleaned_value)

        # --- POSTPROCESAMIENTO DE RESULTADOS ---
        extracted_data = {'Archivo': os.path.basename(image_path)}
        
        # 1. Bloque de dependencias
        solo_deps_raw = {k: all_extracted_data.get(k, "") for k in ["DEPENDENCIA_1", "DEPENDENCIA_2", "DEPENDENCIA_3"]}
        deps_corregidas = procesar_bloque_dependencias(solo_deps_raw)
        
        # 2. Mapeo final
        for key, value in all_extracted_data.items():
            if key.startswith('DEPENDENCIA'):
                extracted_data[key] = deps_corregidas.get(key, value)
            elif key == 'NOMBRE_COMPLETO_RAW':
                name_parts = split_full_name(value)
                for nk in name_parts: name_parts[nk] = clean_name_specific(name_parts[nk])
                extracted_data.update(name_parts)
            else:
                extracted_data[key] = value

        # Asegurar campos básicos de nombre
        for k in ['PATERNO', 'MATERNO', 'NOMBRE_S']:
            if k not in extracted_data: extracted_data[k] = ''
        
        extracted_data_list.append(extracted_data)

        # --- EVALUACIÓN DEL INTENTO ---
        score = 0
        for k, v in extracted_data.items():
            if k in ['Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'NOMBRE_COMPLETO_RAW']: continue
            if v and str(v).strip() and str(v) != EMPTY_DATA_PLACEHOLDER:
                if k == 'NUM':
                    if len(re.sub(r'[^0-9]', '', str(v))) == 7: score += 1
                else: score += 1

        print(f"  Intento {attempt + 1}: {score} campos válidos.")
        if score >= MIN_REQUIRED_FIELDS:
            return extracted_data, None
            
    # Si no se llegó al mínimo, elegir el mejor intento
    if extracted_data_list:
        best_idx = 0
        max_score = -1
        for idx, data in enumerate(extracted_data_list):
            current_score = sum(1 for k, v in data.items() if v and str(v).strip() and str(v) != EMPTY_DATA_PLACEHOLDER)
            if current_score > max_score:
                max_score = current_score
                best_idx = idx
        return extracted_data_list[best_idx], None
    
    return {'Archivo': os.path.basename(image_path)}, "No se detectaron datos."



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

        # Orden Exacto de las columnas en el CSV
        columnas_ordenadas = ['Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'NUM', 'CODIGO', 'RFC', 'IMSS', 'CURP', 'TELEFONO', 'CRN', 'HORAS', 'MATERIA' , 'DESDE', 'HASTA', 'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3']
        # 2. Reorganizamos el DataFrame, asegurando las columas que puedan faltar en 'all_data'
        existing_columns = [col for col in columnas_ordenadas if col in df.columns]
        df = df[existing_columns]

        # 3. Guardamos el archivo CSV con encoding UTF-8-sig para compatibilidad Excel
        df.to_csv(RUTA_SALIDA_CSV, index=False, encoding='utf-8-sig')
        print(f"\n✅ Extracción híbrida completada. Datos guardados en: {RUTA_SALIDA_CSV}")
    else:
        print("\n❌ No se extrajeron datos.")

if __name__ == "__main__":
    main()