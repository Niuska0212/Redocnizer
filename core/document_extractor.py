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
from .segmentacion_dinamica import get_dynamic_rois, clean_data_by_field, clean_border_chars, validate_field_format, clean_name_specific, procesar_bloque_dependencias
from .CRNN_inference import load_inference_model
from .preprocessing import prepare_roi_for_ocr, invert_image_color, rotate_image


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
    PARTICULAS = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'Y', 'MC', 'MAC', 'VON', 'VAN', 'SAN', 'SANTA', 'DI', 'DA', 'EL', 'LE'}
    
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
            # Revisa si el intento 0 fue suficiente. Si sí, termina.
            if extracted_data_list and len([v for v in extracted_data_list[0].values() if v and len(str(v).strip()) > 1]) >= MIN_REQUIRED_FIELDS:
                break
            print("  [REINTENTO 1] Intentando con imagen invertida.")
            current_img = invert_image_color(img_full_original)
        
        elif attempt == 2:
            # Revisa si el intento 0 o 1 fue suficiente. Si sí, termina.
            # Nota: Si el intento 1 fue el mejor, se habría roto en el chequeo anterior,
            # pero este chequeo es de seguridad.
            if extracted_data_list and len([v for v in extracted_data_list[0].values() if v and len(str(v).strip()) > 1]) >= MIN_REQUIRED_FIELDS:
                break
            
            print("  [REINTENTO 2] Intentando con imagen ligeramente rotada (2 grados).")
            # Usamos la imagen original para rotar y evitar rotar la ya invertida.
            current_img = rotate_image(img_full_original, 2.0) 

        # --- PRE-PROCESAMIENTO DE REGIONES DE INTERÉS (ROIS) ---
        rois_dinamicas = get_dynamic_rois(current_img)
        img_height, img_width = current_img.shape[:2]
        
        # --- VISUALIZACIÓN (Solo con el primer intento) ---
        if attempt == 0:
            img_color = cv2.cvtColor(current_img, cv2.COLOR_GRAY2BGR)
            # ... (CÓDIGO DE VISUALIZACIÓN DE ROIS, IGUAL AL ORIGINAL) ...
            COLORS = {
                'NOMBRE_COMPLETO_RAW': (0, 0, 255),
                'DEPENDENCIA': (255, 0, 0),
                'SIMPLE_FIELD': (0, 255, 0)
            }
            output_filename = "Vizualizacion_"+ os.path.basename(image_path)
            output_dir = output_dir_preview
            
            for field_name, (y, x, h, w) in rois_dinamicas.items():
                color = COLORS.get(field_name, COLORS['SIMPLE_FIELD'])
                if field_name.startswith('DEPENDENCIA'):
                    color = COLORS['DEPENDENCIA']
                x_end = x + w
                y_end = y + h
                cv2.rectangle(img_color, (x, y), (x_end, y_end), color, 2)
                cv2.putText(img_color, field_name, (x, max(0, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            save_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(save_path, img_color)
            print(f"Visualización guardada en: {save_path}")
        
        # --- EXTRACCIÓN OCR POR ROI ---
        all_extracted_data = {}
        for field_name, roi_data in rois_dinamicas.items():
            # ... (CÓDIGO DE CLAMPING, EXTRACCIÓN CRNN/TESSERACT) ...
            if not isinstance(roi_data, (list, tuple)) or len(roi_data) != 4:
                all_extracted_data[field_name] = ""
                continue

            y, x, h, w = roi_data
            y_start = max(0, int(y))
            x_start = max(0, int(x))
            y_end = min(img_height, int(y + h))
            x_end = min(img_width, int(x + w))

            min_w, min_h = 12, 12
            if (x_end - x_start) < min_w:
                extra = (min_w - (x_end - x_start)) // 2 + 2
                x_start = max(0, x_start - extra)
                x_end = min(img_width, x_end + extra)
            if (y_end - y_start) < min_h:
                extra = (min_h - (y_end - y_start)) // 2 + 2
                y_start = max(0, y_start - extra)
                y_end = min(img_height, y_end + extra)

            roi_image = current_img[y_start:y_end, x_start:x_end]
            if roi_image.size == 0 or y_end <= y_start or x_end <= x_start:
                all_extracted_data[field_name] = ""
                continue
            
            # 1) lectura CRNN (proteger con try)
            ocr_result_base = ""
            try:
                X_input = prepare_roi_for_ocr(roi_image)
                y_pred_probs = modelo_inferencia.predict(X_input, verbose=0)
                pred_words_crnn = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
                ocr_result_base = pred_words_crnn[0].upper().strip() if pred_words_crnn else ""
            except Exception:
                ocr_result_base = ""

            # 2) lectura Tesseract (refuerzo)
            try:
                ocr_result_refuerzo = read_with_tesseract(roi_image).upper().strip()
            except Exception:
                ocr_result_refuerzo = ""

            # 3) selección / corrección
            final_result = ocr_result_base or ocr_result_refuerzo
            if ocr_result_base and ocr_result_refuerzo:
                similarity = SequenceMatcher(None, ocr_result_base, ocr_result_refuerzo).ratio()
                if similarity < 0.70:
                    final_result = ocr_result_refuerzo

            final_result = clean_border_chars(final_result)
            all_extracted_data[field_name] = final_result

        # --- POSTPROCESAMIENTO Y VALIDACIÓN ---
        extracted_data = {'Archivo': os.path.basename(image_path)}
        
        # 1. Preparar bloque de dependencias para reordenamiento semántico
        solo_deps_raw = {
            "DEPENDENCIA_1": all_extracted_data.get("DEPENDENCIA_1", ""),
            "DEPENDENCIA_2": all_extracted_data.get("DEPENDENCIA_2", ""),
            "DEPENDENCIA_3": all_extracted_data.get("DEPENDENCIA_3", "")
        }
        
        deps_corregidas = procesar_bloque_dependencias(solo_deps_raw)
        
        # 2. Procesar todos los campos
        for key, value in all_extracted_data.items():
            if key.startswith('DEPENDENCIA'):
                # Usamos el valor ya reordenado y limpio
                final_validate_value = deps_corregidas.get(key, "")
            else:
                # Procesamiento normal para los demás campos
                if key == 'NOMBRE_COMPLETO_RAW':
                    value = clean_name_specific(value)
                
                cleaned_value = clean_data_by_field(key, clean_border_chars(value))
                final_validate_value = validate_field_format(key, cleaned_value)

            # Asignación a la estructura final
            if key == 'NOMBRE_COMPLETO_RAW':
                name_parts = split_full_name(final_validate_value)
                for name_key in name_parts:
                    name_parts[name_key] = clean_name_specific(name_parts[name_key])
                extracted_data.update(name_parts)
            else:
                extracted_data[key] = final_validate_value

        # asegurar campos obligatorios
        if 'PATERNO' not in extracted_data: extracted_data['PATERNO'] = ''
        if 'MATERNO' not in extracted_data: extracted_data['MATERNO'] = ''
        if 'NOMBRE_S' not in extracted_data: extracted_data['NOMBRE_S'] = ''
        
        # Almacenar el resultado del intento actual
        extracted_data_list.append(extracted_data)

        # --- LÓGICA DE REINTENTO: Contar campos no vacíos ---
        relevant_fields = {k: v for k, v in extracted_data.items() if k not in ['NOMBRE_COMPLETO_RAW', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'Archivo']}
        
        # Contador especial: NUM incompleto (< 7 dígitos) NO cuenta como exitoso
        successful_fields_count = 0
        for field_key, field_val in relevant_fields.items():
            if field_val and len(str(field_val).strip()) > 1:
                # Si es NUM, validar que tenga exactamente 7 dígitos
                if field_key == 'NUM':
                    num_digits = re.sub(r'[^0-9]', '', str(field_val))
                    if len(num_digits) == 7:
                        successful_fields_count += 1
                else:
                    successful_fields_count += 1

        print(f"  Intento {attempt + 1}: {successful_fields_count} campos extraídos.")
        
        if successful_fields_count >= MIN_REQUIRED_FIELDS:
            # Éxito: Usar este resultado y terminar
            return extracted_data, None
            
    # Si el bucle termina sin éxito, comparamos los resultados para ver cuál fue el mejor
    if extracted_data_list:
        # Contar campos exitosos para cada intento (NUM debe tener exactamente 7 dígitos)
        scores = []
        for data in extracted_data_list:
            relevant_fields = {k: v for k, v in data.items() if k not in ['NOMBRE_COMPLETO_RAW', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'Archivo']}
            score = 0
            for field_key, field_val in relevant_fields.items():
                if field_val and len(str(field_val).strip()) > 1:
                    if field_key == 'NUM':
                        num_digits = re.sub(r'[^0-9]', '', str(field_val))
                        if len(num_digits) == 7:
                            score += 1
                    else:
                        score += 1
            scores.append(score)
        
        # Retorna el resultado con el puntaje más alto
        best_attempt_index = np.argmax(scores)
        return extracted_data_list[best_attempt_index], None
    
    return {'Archivo': os.path.basename(image_path)}, "No se pudo extraer ningún dato en los intentos."



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
        # document_extractor.py (CORREGIDO)
        columnas_ordenadas = ['Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'NUM', 'CODIGO', 'RFC', 'IMSS', 'CURP', 'TELEFONO', 'CRN', 'DESDE', 'HASTA', 'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3']
        # 2. Reorganizamos el DataFrame, asegurando las columas que puedan faltar en 'all_data'
        existing_columns = [col for col in columnas_ordenadas if col in df.columns]
        df = df[existing_columns]

        # 3. Guardamos el archivo CSV
        df.to_csv(RUTA_SALIDA_CSV, index=False, encoding='utf-8')
        print(f"\n✅ Extracción híbrida completada. Datos guardados en: {RUTA_SALIDA_CSV}")
    else:
        print("\n❌ No se extrajeron datos.")

if __name__ == "__main__":
    main()