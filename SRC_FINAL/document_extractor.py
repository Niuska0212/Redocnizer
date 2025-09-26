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

# Importamos solo lo que se puede exportar fácilmente desde crnn_inference.py
from CRNN_inference import load_inference_model 
from preprocessing import prepare_roi_for_ocr 

# >>> CONFIGURACIÓN IMPORTANTE DE TESSERACT <<<
# Reemplaza esta ruta con la ruta donde instalaste tesseract.exe, ¡solo si es necesario!
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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

    return {'PATERNO': paterno, 'MATERNO': materno, 'NOMBRE_S': nombre_s}

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
# === SEGMENTACION DINAMICA CON TESSERACT Y PANDAS (PSM 3) ===
# =========================================================================

def get_dynamic_rois(img_full: np.ndarray) -> dict:
    # Definición dinámica de ROIs basada en las dimensiones de la imagen

    H, W = img_full.shape[:2]

    std_dev =np.std(img_full)
    THRESHOLD_STD = 43

    if std_dev < THRESHOLD_STD:
        print(f"Pre-procesamiento: fondo uniforme (Otsu). STD: {std_dev:.2f}")
        # Intentar el umbral de Otsu
        try:
            img_full_bin = cv2.threshold(img_full, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        except Exception:
            img_full_bin = img_full
    else:
        print(f"Pre-procesamiento: fondo complejo (Adaptative). STD: {std_dev:.2f}")
        # Intentar el umbral adaptativo
        try:
            img_full_bin = cv2.adaptiveThreshold(
                img_full, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
                )
        except Exception:
            img_full_bin = img_full

    # Converititr a PIL para pytesseract.image_to_data
    img_pil = Image.fromarray(img_full_bin)

    # 1. Obtenemos todos los datos de ubicacion de tesseract con PSM 3 (para bloques de texto)
    data_df = pytesseract.image_to_data(
        img_pil,
        output_type=pytesseract.Output.DATAFRAME,
        config='--psm 3'  # PSM 3: para bloques de texto
    )

    #Limpiamos filas sin texto
    data_df = data_df.dropna(subset=['text'])
    # Se hace copy para evitar un warning de pandas
    data_df = data_df[data_df['conf'] > 3].copy()
    data_df['text'] = data_df['text'].str.upper().str.strip() # Normalizamos para la busqueda
    
    # --- Configuración de dimensiones ---
    TOTAL_WIDTH_NOMBRE = 500 # Ancho total de la celda de nombre
    CELL_HEIGHT_NOMBRE = 30  # Altura de la celda de nombre

    TOTAL_HEIGHT_DEP =  99
    CELL_WIDTH_DEP = 792
    CELL_HEIGHT_DEP = int(TOTAL_HEIGHT_DEP / 3) # Alto de cada sub-celda
   

    # 2. Definimos las palabras claves y grupos

    #Grupo A: Nombres y Apellidos (composite fields)
    name_keywords = ['PATERNO', 'MATERNO' 'NOMBRE(S)', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'APELLIDOS']

    #Grupo B: Dependencia (multi-cell field)
    dep_keywords = ['DEPENDENCIA', 'DEPENDENCIAS']

    #Grupo C: Campos sencillos (simple fields)
    simple_fields_below = {
        'CODIGO': ['CÓDIGO', 'CODIGO'],
        'RFC': ['RFC'],
        'IMSS': ['IMSS', 'AFIL IMSS', 'No. AFIL IMSS'],
        'CURP': ['CURP'],
        'DOMICILIO': ['DOMICILIO'],
        'TELEFONO': ['TELÉFONO', 'TELEFONO', 'TEL'],
        'CRN': ['CRN'],
        'HRS_TOTALES': ['HRS. TOTALES', 'HRS TOTALES', 'HORAS TOTALES', 'HRS. TOTALES CURSO'],
        'DESDE': ['DESDE'],
        'HASTA': ['HASTA']
    }

    #Grupo C2: Campos sencillos (informacion a la derecha)
    simple_fields_right ={
        'NUM': ['NÚM', 'NUM']
    }

    dynamic_rois = {}

    # 3. Logica para extraer el nombre completo (3 campos en una sola fila)
    header_matches= data_df[data_df['text'].isin(name_keywords)]

    if not header_matches.empty:
        #Calcular limites del encabezado
        min_x_key = header_matches['left'].min()
        max_y_key_bottom = (header_matches['top'] + header_matches['height']).max()

        y_search_start = max_y_key_bottom + 2  # Un poco más abajo del encabezado

        #Buscar el bloque de texto debajo que contiene los nombres
        value_candidates = data_df[
            (data_df['top'] >= y_search_start) &
            (data_df['left'] >= min_x_key - 45)
        ].sort_values(by='top')

        if not value_candidates.empty:
            
            first_value_word = value_candidates.iloc[0]
            
            y_start = first_value_word['top']
        else:
            y_start = int(max_y_key_bottom + 5)

        X_offset = 80

        x_roi_start = int(min_x_key) - X_offset
        x_roi_start = max(0, x_roi_start)  # Asegurar que no sea negativo

        #Definir y Separar los 3 subcampos
        dynamic_rois['NOMBRE_COMPLETO_RAW'] = [y_start, x_roi_start, CELL_HEIGHT_NOMBRE, TOTAL_WIDTH_NOMBRE]

    # 4. Logica para el bloque de DEPENDENCIA (multi-line)
    for keyword in dep_keywords:
        matches = data_df[data_df['text'] == keyword]
        if not matches.empty:
            key_row = matches.iloc[0]
            x_key = key_row['left']
            h_key = key_row['height']
            y_search_start = key_row['top'] + h_key + 5

            value_candidates = data_df[
                (data_df['top'] >= y_search_start) &
                (data_df['left'] >= x_key - 10)
            ].sort_values(by='top')

            if not value_candidates.empty:
                first_value_word = value_candidates.iloc[0]
                x_start = int(first_value_word['left'])
                y_start = int(first_value_word['top'])

                h_dep = int(CELL_HEIGHT_DEP)
                w_dep = int(CELL_WIDTH_DEP)

                #Definir el área de la dependencia (3 filas)
                #ROI 1: Comienza en y_start
                dynamic_rois['DEPENDENCIA_1'] = [y_start, x_start, h_dep, w_dep]

                #ROI 2: Desplazada hacia abajo
                y2 = y_start + h_dep
                dynamic_rois['DEPENDENCIA_2'] = [y2, x_start, h_dep, w_dep]

                #ROI 3: Deplazado 2 alturas abajo
                y3 = y_start + 2 * h_dep
                dynamic_rois['DEPENDENCIA_3'] = [y3, x_start, h_dep, w_dep]
                break

    # 5.1 Logica para los campos sencillos (a la derecha)
    for field_name, keywords in simple_fields_right.items():
        if field_name not in dynamic_rois:
            for keyword in keywords:
                matches= data_df[data_df['text'] == keyword]
                if not matches.empty:
                    key_row = matches.iloc[0]
                    key_block_num = key_row['block_num']
                    key_line_num = key_row['line_num']
                    key_right = key_row['left'] + key_row['width']

                    value_candidates = data_df[
                        (data_df['block_num'] == key_block_num) &
                        (data_df['line_num'] == key_line_num) &
                        (data_df['left'] >= key_right + 5)
                    ].sort_values(by='left')

                    if not value_candidates.empty:
                        first_value_word = value_candidates.iloc[0]
                        x_start = int(first_value_word['left'])
                        y_start = int(first_value_word['top'])
                        
                        #Roi para campos sencillos (y,x,h,w)
                        dynamic_rois[field_name] = [y_start, x_start, 50, 300]
                    break

    # 5.2 Logica para los campos sencillos (Debajo)               
    for field_name, keywords in simple_fields_below.items():
        if field_name not in dynamic_rois:
            for keyword in keywords:
                matches= data_df[data_df['text'] == keyword]
                if not matches.empty:
                    key_row = matches.iloc[0]
                    x_key = key_row['left']
                    h_key = key_row['height']
                    y_search_start = key_row['top'] + h_key + 5

                    value_candidates = data_df[
                        (data_df['top'] >= y_search_start) &
                        (data_df['left'] >= x_key - 10) &
                        (data_df['left'] <= x_key + 100)
                    ].sort_values(by='top')

                    if not value_candidates.empty:
                        first_value_word = value_candidates.iloc[0]
                        x_start = first_value_word['left']
                        y_start = first_value_word['top']
                        
                        #Roi para campos sencillos (y,x,h,w)
                        dynamic_rois[field_name] = [y_start, x_start, 50, 300]
                    break
    return dynamic_rois

def clean_border_chars(text: str) -> str:
    if not text:
        return ""
    
    # Elimina caracteres no alfanuméricos al inicio y final del texto
    text = re.sub(r'[-!|\/ \-]', '', text)

    text = re.sub(r'\s+', ' ', text)  # Reemplaza múltiples espacios por uno solo
    return text.strip()

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
        
        all_extracted_data[field_name] = final_result

        # --- POST-PROCESAMIENTO ---
        extracted_data = {'Archivo': os.path.basename(image_path)}

        for key, value in all_extracted_data.items():
            if key == 'NOMBRE_COMPLETO_RAW':
                # Aplicar la funcion de division de nombre completo
                name_parts = split_full_name(value)
                extracted_data.update(name_parts)
            else:
                # Añadir todos los demás campos (incluyendo DEPENDENCIA y simples)
                extracted_data[key] = value
            
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