# core/document_extractor.py
import cv2
import os
import sys 
import shutil
import pandas as pd 
import re
import numpy as np
import easyocr
import gc
from difflib import SequenceMatcher 
from PIL import Image, ImageDraw, ImageFont
from .segmentacion_dinamica import get_dynamic_rois, clean_data_by_field, clean_border_chars, validate_field_format, clean_name_specific, procesar_bloque_dependencias, EMPTY_DATA_PLACEHOLDER
from .preprocessing import prepare_roi_for_ocr, invert_image_color, rotate_image, enhance_for_easyocr
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication # <--- IMPORTANTE

# =========================================================
# === GESTIÓN DE RUTAS Y CARGA PEREZOSA (LAZY LOADING) ===
# =========================================================

_READER_INSTANCE = None  # Variable privada que guardará el motor una vez cargado

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_shared_reader():
    """ 
    Carga EasyOCR solo la primera vez que se solicita.
    Esto hace que la App abra instantáneamente.
    """
    global _READER_INSTANCE
    
    if _READER_INSTANCE is None:
        print("🚀 Inicializando motor de IA por primera vez...")
        
        # 1. Configurar rutas de modelos
        model_dir = get_resource_path("models")
        
        # 2. Obtener preferencias de GPU
        settings = QSettings("Redocnizer", "RedocnizerApp")
        gpu_pref = settings.value("use_gpu_acceleration", False, type=bool)
        
        # 3. Crear la instancia (Offline)
        try:
            _READER_INSTANCE = easyocr.Reader(
                ['es'], 
                gpu=gpu_pref, 
                model_storage_directory=model_dir, 
                download_enabled=False
            )
            print(f"✅ Motor IA listo (GPU={gpu_pref})")
        except Exception as e:
            print(f"⚠️ Error cargando modelos locales: {e}. Intentando carga estándar...")
            _READER_INSTANCE = easyocr.Reader(['es'], gpu=gpu_pref)
            
    return _READER_INSTANCE

# --- CONFIGURACIÓN DE RUTAS DE DATOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_IMAGENES = os.path.join(BASE_DIR, "..", "data", "data", "contratos", "imagenes_jpg")
RUTA_PREVIEW = os.path.join(BASE_DIR, "..", "data", "data", "contratos", "preview")
RUTA_SALIDA_CSV = os.path.join(BASE_DIR, "datos_extraidos_contratos.csv")

# =========================================================================
# === FUNCIÓN DE DECODIFICACIÓN (Local para evitar errores de importación) ===
# =========================================================================

# def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
#     """Decodifica las predicciones del modelo usando CTC."""
#     input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
#     # K.ctc_decode requiere la importación 'import tensorflow.keras.backend as K'
#     results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
#     decoded_words = []
#     for seq in K.get_value(results):
#         word = "".join([index_to_char[idx] for idx in seq if idx != -1])
#         decoded_words.append(word.strip())
#     return decoded_words




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
        reader = get_shared_reader()
        
        results = reader.readtext(roi_image, detail=0) # detail=0 devuelve solo el texto
        text = " ".join(results)
        return text.strip()
    except Exception as e:
        print(f"Error en EasyOCR: {e}")
        return ""




def extract_data_from_image(image_path, output_dir_preview):
    """
    Versión Ágil y Optimizada para poca RAM: 
    Extrae datos usando exclusivamente EasyOCR con control de memoria.
    """
    
    img_full_original = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_full_original is None:
        return {'Archivo': os.path.basename(image_path)}, f"Error: No se pudo cargar la imagen"

    # --- OPTIMIZACIÓN 1: Redimensionar imágenes gigantes ---
    h_orig, w_orig = img_full_original.shape[:2]
    if w_orig > 2200:
        scale = 2000 / w_orig
        img_full_original = cv2.resize(img_full_original, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    # Parámetros de control
    MIN_REQUIRED_FIELDS = 10 
    best_attempt_data = None
    max_score = -1
    
    # Bucle de intentos: 0: Original, 1: Invertida, 2: Rotada
    for attempt in range(3):
        # --- OPTIMIZACIÓN 2: Evitar copias innecesarias si el intento 0 es suficiente ---
        if attempt == 0:
            current_img = img_full_original
        elif attempt == 1:
            current_img = cv2.bitwise_not(img_full_original)
        elif attempt == 2:
            current_img = rotate_image(img_full_original, 2.0) 

        # --- LOCALIZACIÓN DE REGIONES (ROIs) ---
        rois_dinamicas = get_dynamic_rois(current_img)
        img_height, img_width = current_img.shape[:2]
        # >>> BLOQUE AQUÍ PARA LAS PREVIEWS <<<
        if attempt == 0 and output_dir_preview:
            # Crear una copia a color para dibujar los rectángulos
            img_color = cv2.cvtColor(current_img, cv2.COLOR_GRAY2BGR)
            COLORS = {'NOMBRE_COMPLETO_RAW': (0, 0, 255), 'DEPENDENCIA': (255, 0, 0), 'SIMPLE_FIELD': (0, 255, 0)}
            
            for field_name, roi_data in rois_dinamicas.items():
                if not isinstance(roi_data, (list, tuple)) or len(roi_data) != 4: continue
                y, x, h, w = roi_data
                color = COLORS.get(field_name, COLORS['SIMPLE_FIELD'])
                if 'DEPENDENCIA' in field_name: color = COLORS['DEPENDENCIA']
                
                cv2.rectangle(img_color, (int(x), int(y)), (int(x + w), int(y + h)), color, 2)
                cv2.putText(img_color, field_name, (int(x), max(0, int(y) - 5)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

            save_path = os.path.join(output_dir_preview, "Viz_" + os.path.basename(image_path))
            cv2.imwrite(save_path, img_color)
        # >>> FIN DEL BLOQUE DE PREVIEWS <<<
        all_extracted_data = {}
        
        # --- EXTRACCIÓN CON EASYOCR ---
        for field_name, roi_data in rois_dinamicas.items():
            y, x, h, w = roi_data
            y_s, x_s = max(0, int(y)), max(0, int(x))
            y_e, x_e = min(img_height, int(y + h)), min(img_width, int(x + w))

            roi_image = current_img[y_s:y_e, x_s:x_e]
            if roi_image.size == 0:
                all_extracted_data[field_name] = ""
                continue
            
            roi_prepared = enhance_for_easyocr(roi_image)
            
            try:
                # Usamos el reader global para no reiniciarlo
                raw_text = read_with_easyocr(roi_prepared).upper().strip()
            except:
                raw_text = ""

            cleaned_value = clean_data_by_field(field_name, clean_border_chars(raw_text))
            all_extracted_data[field_name] = validate_field_format(field_name, cleaned_value)

        # --- CONSOLIDACIÓN DE RESULTADOS ---
        extracted_data = {'Archivo': os.path.basename(image_path)}
        
        solo_deps = {k: all_extracted_data.get(k, "") for k in ["DEPENDENCIA_1", "DEPENDENCIA_2", "DEPENDENCIA_3"]}
        deps_corregidas = procesar_bloque_dependencias(solo_deps)
        
        for key, value in all_extracted_data.items():
            if key.startswith('DEPENDENCIA'):
                extracted_data[key] = deps_corregidas.get(key, value)
            elif key == 'NOMBRE_COMPLETO_RAW':
                name_parts = split_full_name(value)
                extracted_data.update({nk: clean_name_specific(nv) for nk, nv in name_parts.items()})
            else:
                extracted_data[key] = value

        # --- EVALUACIÓN RÁPIDA ---
        score = sum(1 for k, v in extracted_data.items() 
                if v and str(v).strip() and str(v) != EMPTY_DATA_PLACEHOLDER 
                and k not in ['Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'NOMBRE_COMPLETO_RAW'])

        if score >= MIN_REQUIRED_FIELDS:
            # --- OPTIMIZACIÓN 3: Limpieza profunda antes de salir ---
            del img_full_original
            if attempt > 0: del current_img
            gc.collect() 
            return extracted_data, None
        
        if score > max_score:
            max_score = score
            best_attempt_data = extracted_data

    # --- OPTIMIZACIÓN 4: Limpieza final si agotó los intentos ---
    del img_full_original
    gc.collect()

    return best_attempt_data if best_attempt_data else ({'Archivo': os.path.basename(image_path)}, "No se detectaron datos.")



def clean_and_recreate_directory(dir_path):
    """Limpia y recrea un directorio."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    os.makedirs(dir_path, exist_ok=True)

# =========================================================================
# === FUNCIÓN PRINCIPAL ===
# =========================================================================

# def main():
#     # Cargar el modelo CRNN (Tu base de conocimiento)
#     modelo_inferencia, index_to_char, output_sequence_length = load_inference_model()
#     if modelo_inferencia is None:
#         print("\nEl programa no puede continuar sin el modelo de inferencia.")
#         return
    
#     clean_and_recreate_directory(RUTA_PREVIEW)

#     # Preparar el proceso de extracción
#     all_files = [f for f in os.listdir(RUTA_IMAGENES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

#     if len(all_files) > 50:
#         all_files = random.sample(all_files, 50)  # Para pruebas, limitar a 100 imágenes
#     all_data = []

#     print(f"\nIniciando extracción híbrida de datos de {len(all_files)} documentos...")

#     for i, file_name in enumerate(all_files):
#         image_path = os.path.join(RUTA_IMAGENES, file_name)
        
#         data, error = extract_data_from_image(
#             image_path, 
#             modelo_inferencia, 
#             index_to_char, 
#             output_sequence_length,
#             RUTA_PREVIEW
#         )

#         if data:
#             all_data.append(data)
        
#         if error:
#             print(f"Error procesando {file_name}: {error}")

#         if (i + 1) % 50 == 0 or (i + 1) == len(all_files):
#             print(f"-> {i + 1}/{len(all_files)} documentos procesados.")

#     # Guardar los resultados
#     if all_data:
#         df = pd.DataFrame(all_data)

#         # Orden Exacto de las columnas en el CSV
#         columnas_ordenadas = ['Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'NUM', 'CODIGO', 'RFC', 'IMSS', 'CURP', 'TELEFONO', 'CRN', 'HORAS', 'MATERIA' , 'DESDE', 'HASTA', 'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3']
#         # 2. Reorganizamos el DataFrame, asegurando las columas que puedan faltar en 'all_data'
#         existing_columns = [col for col in columnas_ordenadas if col in df.columns]
#         df = df[existing_columns]

#         # 3. Guardamos el archivo CSV con encoding UTF-8-sig para compatibilidad Excel
#         df.to_csv(RUTA_SALIDA_CSV, index=False, encoding='utf-8-sig')
#         print(f"\n✅ Extracción híbrida completada. Datos guardados en: {RUTA_SALIDA_CSV}")
#     else:
#         print("\n❌ No se extrajeron datos.")

# if __name__ == "__main__":
#     main()