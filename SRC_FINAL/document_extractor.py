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
from segmentacion_dinamica import get_dynamic_rois, clean_data_by_field, clean_border_chars, validate_field_format

#la parte del orden de las columnas del archivo csv se maneja en pandas al momento de crear el dataframe en la linea 377

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
    PARTICULAS = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'Y', 'MC', 'MAC', 'VON', 'VAN', 'SAN', 'SANTA', 'DI', 'DA', 'EL', 'LE'}
    words = full_name.upper().strip().split()

    if len(words) < 2:
        return {'PATERNO': full_name, 'MATERNO': '', 'NOMBRE_S': ''}
    
    # --- LÓGICA DE MANEJO DE PREFIJOS INICIALES ---
    paterno_start_index = 0
    
    # Si la primera palabra es una partícula, el apellido compuesto REAL empieza con la segunda palabra.
    # Ej: DE LA ROSA -> (paterno_start_index = 0, luego se une con la siguiente)
    # Ej: ALMEIDA CUNHA -> (paterno_start_index = 0)
    
    # Si la PRIMERA palabra es una partícula, la incluimos y buscamos la siguiente palabra para que sea el núcleo del apellido.
    if words[0] in PARTICULAS and len(words) > 1:
        # El apellido paterno comienza con la partícula y el núcleo del apellido.
        paterno_start_index = 0
    else:
        # El apellido paterno comienza con el núcleo (primera palabra).
        paterno_start_index = 0
        
    # Inicialización del índice de fin del Paterno
    paterno_end_index = paterno_start_index + 1

    # --- Lógica de Detección de Apellido Compuesto (PATERNO) ---
    # Caso 1: Buscar partículas que sigan al primer núcleo
    # El bucle debe comenzar *después* de la primera o segunda palabra ya absorbida.
    
    # Si ya manejamos una partícula inicial (paterno_start_index = 0), el bucle debe buscar a partir del índice 1.
    # Si la primera palabra NO era partícula, el bucle busca a partir del índice 1.

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
    
    # --- Asignación de Materno y Nombre(s) (sin cambios significativos) ---
    materno = remaining_words[0]
    nombre_s = " ".join(remaining_words[1:])

    # Lógica simplificada para el materno compuesto (la conservamos, asume que el materno es la primera palabra restante)
    # Si el "materno" es una partícula, es probable que deba ir junto a la siguiente palabra (segundo apellido compuesto).
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
    """
    extracted_data = {'Archivo': os.path.basename(image_path)}

    img_full = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img_full is None:
        return extracted_data, f"Error: No se pudo cargar la imagen {os.path.basename(image_path)}"

    rois_dinamicas = get_dynamic_rois(img_full)
    all_extracted_data = {} # Diccionario temporal para todos los campos

    img_color = cv2.cvtColor(img_full, cv2.COLOR_GRAY2BGR)
    output_filename = "Vizualizacion_"+ os.path.basename(image_path)
    output_dir = output_dir_preview

    COLORS = {
        'NOMBRE_COMPLETO_RAW': (0, 0, 255),
        'DEPENDENCIA': (255, 0, 0),
        'SIMPLE_FIELD': (0, 255, 0)
    }

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

    # ---------------- extracción OCR por ROI ----------------
    all_extracted_data = {}
    img_height, img_width = img_full.shape[:2]

    for field_name, roi_data in rois_dinamicas.items():
        # validación ROI
        if not isinstance(roi_data, (list, tuple)) or len(roi_data) != 4:
            print(f"[WARN] ROI inválida para {field_name}: {roi_data}")
            all_extracted_data[field_name] = ""
            continue

        y, x, h, w = roi_data
        # clamp local (por si acaso)
        y_start = max(0, int(y))
        x_start = max(0, int(x))
        y_end = min(img_height, int(y + h))
        x_end = min(img_width, int(x + w))

        # si ROI es muy pequeña, intentar expandir un poco
        min_w, min_h = 12, 12
        if (x_end - x_start) < min_w:
            extra = (min_w - (x_end - x_start)) // 2 + 2
            x_start = max(0, x_start - extra)
            x_end = min(img_width, x_end + extra)
        if (y_end - y_start) < min_h:
            extra = (min_h - (y_end - y_start)) // 2 + 2
            y_start = max(0, y_start - extra)
            y_end = min(img_height, y_end + extra)

        roi_image = img_full[y_start:y_end, x_start:x_end]
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
        except Exception as e:
            # si CRNN falla, lo anotamos y seguimos con tesseract
            print(f"[WARN] CRNN fallo para {field_name} en {os.path.basename(image_path)}: {e}")
            ocr_result_base = ""

        # 2) lectura Tesseract (refuerzo)
        try:
            ocr_result_refuerzo = read_with_tesseract(roi_image).upper().strip()
        except Exception as e:
            print(f"[WARN] Tesseract fallo para {field_name}: {e}")
            ocr_result_refuerzo = ""

        # 3) selección / corrección
        final_result = ocr_result_base or ocr_result_refuerzo
        if ocr_result_base and ocr_result_refuerzo:
            similarity = SequenceMatcher(None, ocr_result_base, ocr_result_refuerzo).ratio()
            if similarity < 0.70:
                # si son muy diferentes, preferimos tesseract como fallback
                final_result = ocr_result_refuerzo

        final_result = clean_border_chars(final_result)
        all_extracted_data[field_name] = final_result

    # ---------------- postprocesamiento (AHORA FUERA DEL for) ----------------
    extracted_data = {'Archivo': os.path.basename(image_path)}

    for key, value in all_extracted_data.items():
        cleaned_value = clean_data_by_field(key, clean_border_chars(value))
        final_validate_value = validate_field_format(key, cleaned_value)

        if key == 'NOMBRE_COMPLETO_RAW':
            name_parts = split_full_name(final_validate_value)
            extracted_data.update(name_parts)
        elif key.startswith('DEPENDENCIA'):
            extracted_data[key] = final_validate_value
        else:
            # Usamos claves sin tildes en todo el flujo (recomiendo 'NUM' no 'NÚM')
            extracted_data[key] = final_validate_value

    # asegurar campos obligatorios
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