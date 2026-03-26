# core/segmentacion_dinamica.py
import random
import cv2
import os
import shutil
import pandas as pd
import re
import numpy as np
import easyocr
#from tensorflow.keras import backend as K 
from difflib import SequenceMatcher # Necesario para calcular la similitud (Levenshtein)
from PIL import Image, ImageDraw, ImageFont


# Inicializar el lector (puedes hacerlo global o dentro de la función)

reader = easyocr.Reader(['es'], download_enabled=False)

# Constantes de estandarización
PHONE_EMPTY_TOKENS = ["-", "—", "0", "00", "000", "N/A", "NA"] 
EMPTY_DATA_PLACEHOLDER = "NO_INFO_DOC"


"constantes de DIccionario por niveles de departamentos"
CATALOGO_DEPENDENCIAS = {
    "DEPENDENCIA_1": [
        "C. U. DE CS. EXACTAS E INGENIERIAS"
    ],
    "DEPENDENCIA_2": [
        "DIV. DE CS. BÁSICAS",
        "DIV. DE INGENIERÍAS",
        "DIV. DE TECNOLOGIAS PARA LA INTEGRACION CIBER-HUMANA"
    ],
    "DEPENDENCIA_3": [
        "DEPTO. DE INGENIERÍA CIVIL Y TOPOGRAFÍA", "DEPTO. DE FÍSICA",
        "DEPTO. DE CIENCIAS COMPUTACIONALES", "DEPTO. DE INNOVACIÓN BASADA EN LA INFORMACIÓN Y EL CONOCIMIENTO",
        "DEPTO. DE BIOINGENIERÍA TRASLACIONAL", "DEPTO. DE MATEMÁTICAS",
        "DEPTO. DE QUÍMICA", "DEPTO. DE FARMACOBIOLOGÍA",
        "DEPTO. DE ELECTRÓNICA", "DEPTO. DE FOTÓNICA",
        "DEPTO. DE MÉTODOS CUANTITATIVOS", "DEPTO. DE INGENIERÍA INDUSTRIAL",
        "DEPTO. DE INGENIERÍA MECÁNICA ELÉCTRICA", "DEPTO. DE INGENIERÍA QUÍMICA",
        "DEPTO. DE MADERA, CELULOSA Y PAPEL", "DEPTO. DE PROYECTOS DE COMUNICACIÓN DE LA INGENIERÍA",
        "DEPTO. DE INGENIERÍA DE PROCESOS Y ENERGÍA", "DEPTO. DE CIENCIA DE LOS MATERIALES"
    ]
}

# =========================================================================
# === SEGMENTACION DINAMICA CON EASYOCR Y PANDAS ===
# =========================================================================

def get_dynamic_rois(img_full: np.ndarray) -> dict:
    """
    Identifica dinámicamente las regiones de interés (ROIs) basándose en etiquetas 
    detectadas por OCR, priorizando CODIGO, CRN, MATERIA, HRS_TOTALES y FECHAS.
    """
    if img_full is None: return {}
    
    H, W = img_full.shape[:2]
    
    # Campos críticos que nunca deben faltar
    CAMPOS_CRITICOS = {'CODIGO', 'NUM', 'MATERIA', 'HRS_TOTALES', 'DEPENDENCIA_3', 'NOMBRE_COMPLETO_RAW'}
    
    # --- FUNCIÓN PARA MEJORAR IMAGEN CON ACLARAMIENTO AGRESIVO ---
    def enhance_image_aggressive(gray_img):
        """Aplica CLAHE más fuerte + threshold adaptativo para fondos grises"""
        # 1. Normalizar
        normalized = cv2.normalize(gray_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        
        # 2. CLAHE más agresivo
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(6, 6))
        enhanced = clahe.apply(normalized)
        
        # 3. Threshold adaptativo para mejorar contraste de etiquetas
        enhanced = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 15, 5)
        return enhanced
    
    # --- PREPROCESAMIENTO INICIAL ---
    img_gray = cv2.cvtColor(img_full, cv2.COLOR_BGR2GRAY) if len(img_full.shape) == 3 else img_full
    avg_brightness = np.mean(img_gray)
    
    if avg_brightness < 120:
        img_gray = enhance_image_aggressive(img_gray)
    
    # Ejecución de EasyOCR
    results = reader.readtext(img_gray.astype(np.uint8))
    
    rows = []
    for (bbox, text, prob) in results:
        (tl, tr, br, bl) = bbox
        rows.append({
            'left': int(tl[0]), 
            'top': int(tl[1]),
            'width': int(tr[0] - tl[0]), 
            'height': int(bl[1] - tl[1]),
            'text': text.upper().strip(), 
            'conf': prob * 100
        })
    
    data_df = pd.DataFrame(rows)
    if data_df.empty: return {}
    
    # Filtrado inicial de ruido
    data_df = data_df[data_df['conf'] > 10].copy()
    dynamic_rois = {}

    # ==========================================================
    # 1. DEFINICIÓN DE GRUPOS DE CAMPOS (PRIORIDAD)
    # ==========================================================
    
    # Campos que mencionas como prioritarios (Valor SIEMPRE debajo)
    # Reducimos el ancho y ajustamos el comportamiento de MATERIA
    prioritarios_below = {
        'CODIGO':       {'keys': ['CÓDIGO', 'CODIGO'], 'w': 160, 'h_limit': 45},
        'MATERIA':      {'keys': ['MATERIA', 'MATERIAS', 'NOMBRE DE LA MATERIA'], 'w': 660, 'h_limit': 35},
        'CRN':          {'keys': ['CRN', 'C.R.N.', 'C R N'], 'w': 160, 'h_limit': 45},
        'HRS_TOTALES':  {'keys': ['HRS. TOTALES', 'HORAS TOTALES', 'HRS TOTALES', 'HRS.', 'HORA'], 'w': 160, 'h_limit': 45},
        'DESDE':        {'keys': ['DESDE', 'DESDE:'], 'w': 200, 'h_limit': 45},
        'HASTA':        {'keys': ['HASTA', 'HASTA:'], 'w': 200, 'h_limit': 45}
    }

    # Otros campos secundarios
    secundarios_below = {
        'CURP':     {'keys': ['CURP'], 'w': 350, 'h_limit': 45},
        'TELEFONO': {'keys': ['TELÉFONO', 'TELEFONO', 'TEL'], 'w': 200, 'h_limit': 45}
    }

    # ==========================================================
    # 2. FUNCIÓN DE BÚSQUEDA VERTICAL REFINADA
    # ==========================================================
    
    def find_value_directly_below(keywords, w_roi, h_roi=35, vertical_limit=40):
        """
        Busca el valor físico en las filas de abajo de la etiqueta encontrada.
        vertical_limit controla qué tan abajo buscamos el texto candidato.
        """
        regex_pattern = '|'.join([re.escape(kw) for kw in keywords])
        matches = data_df[data_df['text'].str.contains(regex_pattern, case=False, regex=True)]
        
        if not matches.empty:
            # Tomamos el match más probable o el primero
            anchor = matches.iloc[0]
            y_label_bottom = anchor['top'] + anchor['height']
            x_label_left = anchor['left']
            
            # Ajuste de MATERIA: Si es materia, somos más estrictos con el margen vertical
            # para evitar que baje a la fila de CRN/HRS
            candidates = data_df[
                (data_df['top'] >= y_label_bottom - 2) & 
                (data_df['top'] <= y_label_bottom + vertical_limit) &
                (data_df['left'] >= x_label_left - 80) &
                (data_df['left'] <= x_label_left + 150)
            ].sort_values(by='top')

            if not candidates.empty:
                val = candidates.iloc[0]
                # Si el candidato detectado es muy pequeño o parece otra etiqueta, ajustamos
                return [int(val['top'] - 2), int(val['left'] - 5), h_roi, w_roi]
            else:
                # Fallback: Coordenadas estimadas pegadas a la etiqueta
                return [int(y_label_bottom + 2), int(x_label_left), h_roi, w_roi]
        return None

    # ==========================================================
    # 3. PROCESAMIENTO DE ROIS
    # ==========================================================

    # --- A. Procesar Prioritarios ---
    for field, config in prioritarios_below.items():
        # Para MATERIA usamos un h_limit más corto para evitar saltar filas
        limit = config.get('h_limit', 40)
        roi = find_value_directly_below(config['keys'], config['w'], vertical_limit=limit)
        if roi:
            dynamic_rois[field] = roi

    # --- B. Procesar Secundarios ---
    for field, config in secundarios_below.items():
        if field not in dynamic_rois:
            roi = find_value_directly_below(config['keys'], config['w'])
            if roi:
                dynamic_rois[field] = roi

    # --- C. RFC, IMSS ---
    for field, keys in {'RFC': ['RFC'], 'IMSS': ['IMSS', 'AFIL']}.items():
        roi = find_value_directly_below(keys, 230)
        if roi:
            dynamic_rois[field] = roi

    # --- D. NOMBRE COMPLETO ---
    name_keywords = ['PATERNO', 'MATERNO', 'NOMBRE(S)', 'APELLIDO PATERNO']
    header_matches = data_df[data_df['text'].isin(name_keywords)]
    if not header_matches.empty:
        anchor_row = header_matches.iloc[0]
        y_start = anchor_row['top'] + anchor_row['height'] + 5
        dynamic_rois['NOMBRE_COMPLETO_RAW'] = [int(y_start), 200, 30, 600]
        
    # 2. CODIGO (Prioridad: Vertical -> Espacial a la izquierda del Nombre)
    roi_codigo = find_value_directly_below(['CÓDIGO', 'CODIGO'], 160, h_roi=35, vertical_limit=45)
    if roi_codigo:
        dynamic_rois['CODIGO'] = roi_codigo
    elif 'NOMBRE_COMPLETO_RAW' in dynamic_rois:
        # Si no lo halló debajo de la palabra "CODIGO", buscar a la izquierda del nombre
        roi_espacial = get_code_by_proximity(data_df, dynamic_rois['NOMBRE_COMPLETO_RAW'])
        if roi_espacial:
            dynamic_rois['CODIGO'] = roi_espacial

    # --- E. DEPENDENCIAS ---
    dep_keywords = ['DEPENDENCIA', 'DEPENDENCIAS']
    dep_found = False
    for kw in dep_keywords:
        matches = data_df[data_df['text'].str.contains(kw, case=False, na=False)]
        if not matches.empty:
            key_row = matches.iloc[0]
            y_start = int(key_row['top'] + key_row['height'] + 5)
            h_cell = 33
            dynamic_rois['DEPENDENCIA_1'] = [y_start, 100, h_cell, 792]
            dynamic_rois['DEPENDENCIA_2'] = [y_start + h_cell, 100, h_cell, 792]
            dynamic_rois['DEPENDENCIA_3'] = [y_start + 2*h_cell, 100, h_cell, 792]
            dep_found = True
            break
            
    if not dep_found:
        y_fallback = int(H * 0.35)
        h_cell = 33
        dynamic_rois['DEPENDENCIA_1'] = [y_fallback, 100, h_cell, 792]
        dynamic_rois['DEPENDENCIA_2'] = [y_fallback + h_cell, 100, h_cell, 792]
        dynamic_rois['DEPENDENCIA_3'] = [y_fallback + 2*h_cell, 100, h_cell, 792]

    # --- F. NUM ---
    num_keywords = ['NÚM', 'NUM', 'NUM:', 'NÚM:']
    matches = data_df[data_df['text'].str.contains('|'.join(num_keywords), case=False, regex=True)]
    if not matches.empty:
        key_row = matches.iloc[0]
        val_right = data_df[
            (data_df['top'] >= key_row['top'] - 15) & 
            (data_df['top'] <= key_row['top'] + 15) &
            (data_df['left'] >= key_row['left'] + key_row['width'])
        ].sort_values(by='left').head(1)
        
        if not val_right.empty:
            dynamic_rois['NUM'] = [int(val_right.iloc[0]['top'] - 5), int(val_right.iloc[0]['left'] - 5), 40, 160]
        else:
            dynamic_rois['NUM'] = [int(key_row['top']), int(key_row['left'] + key_row['width'] + 10), 40, 160]

    # --- G. VALIDACIÓN Y REINTENTO CON IMAGEN MEJORADA ---
    campos_encontrados = set(dynamic_rois.keys())
    campos_faltantes = CAMPOS_CRITICOS - campos_encontrados
    
    # Si faltan campos críticos, re-ejecutar OCR con imagen más aclarada
    if campos_faltantes and avg_brightness >= 100:
        print(f"⚠️ Campos críticos faltantes: {campos_faltantes}. Re-procesando con aclaramiento agresivo...")
        
        # Re-procesar imagen con aclaramiento más fuerte
        img_gray_enhanced = enhance_image_aggressive(img_gray)
        results_enhanced = reader.readtext(img_gray_enhanced.astype(np.uint8))
        
        # Reconstruir dataframe con resultados mejorados
        rows_enhanced = []
        for (bbox, text, prob) in results_enhanced:
            (tl, tr, br, bl) = bbox
            rows_enhanced.append({
                'left': int(tl[0]), 
                'top': int(tl[1]),
                'width': int(tr[0] - tl[0]), 
                'height': int(bl[1] - tl[1]),
                'text': text.upper().strip(), 
                'conf': prob * 100
            })
        
        data_df_enhanced = pd.DataFrame(rows_enhanced)
        if not data_df_enhanced.empty:
            data_df_enhanced = data_df_enhanced[data_df_enhanced['conf'] > 10].copy()
            
            # Intercambiar dataframe temporalmente
            data_df_original = data_df
            data_df = data_df_enhanced
            
            # Re-procesar solo los campos faltantes
            # CODIGO
            if 'CODIGO' in campos_faltantes:
                roi = find_value_directly_below(['CÓDIGO', 'CODIGO'], 160, h_roi=35, vertical_limit=45)
                if roi:
                    dynamic_rois['CODIGO'] = roi
            
            # MATERIA
            if 'MATERIA' in campos_faltantes:
                roi = find_value_directly_below(['MATERIA', 'MATERIAS', 'NOMBRE DE LA MATERIA'], 660, h_roi=35, vertical_limit=35)
                if roi:
                    dynamic_rois['MATERIA'] = roi
            
            # HRS_TOTALES
            if 'HRS_TOTALES' in campos_faltantes:
                roi = find_value_directly_below(['HRS. TOTALES', 'HORAS TOTALES', 'HRS TOTALES', 'HRS.'], 160, h_roi=35, vertical_limit=45)
                if roi:
                    dynamic_rois['HRS_TOTALES'] = roi
            
            # NUM
            if 'NUM' in campos_faltantes:
                num_keywords = ['NÚM', 'NUM', 'NUM:', 'NÚM:']
                matches = data_df[data_df['text'].str.contains('|'.join(num_keywords), case=False, regex=True)]
                if not matches.empty:
                    key_row = matches.iloc[0]
                    val_right = data_df[
                        (data_df['top'] >= key_row['top'] - 15) & 
                        (data_df['top'] <= key_row['top'] + 15) &
                        (data_df['left'] >= key_row['left'] + key_row['width'])
                    ].sort_values(by='left').head(1)
                    
                    if not val_right.empty:
                        dynamic_rois['NUM'] = [int(val_right.iloc[0]['top'] - 5), int(val_right.iloc[0]['left'] - 5), 40, 160]
                    else:
                        dynamic_rois['NUM'] = [int(key_row['top']), int(key_row['left'] + key_row['width'] + 10), 40, 160]
            
            # NOMBRE_COMPLETO_RAW
            if 'NOMBRE_COMPLETO_RAW' in campos_faltantes:
                name_keywords = ['PATERNO', 'MATERNO', 'NOMBRE(S)', 'APELLIDO PATERNO']
                header_matches = data_df[data_df['text'].isin(name_keywords)]
                if not header_matches.empty:
                    anchor_row = header_matches.iloc[0]
                    y_start = anchor_row['top'] + anchor_row['height'] + 5
                    dynamic_rois['NOMBRE_COMPLETO_RAW'] = [int(y_start), 200, 30, 600]
            
            # DEPENDENCIA_1
            if 'DEPENDENCIA_1' in campos_faltantes:
                dep_keywords = ['DEPENDENCIA', 'DEPENDENCIAS']
                for kw in dep_keywords:
                    matches = data_df[data_df['text'].str.contains(kw, case=False, na=False)]
                    if not matches.empty:
                        key_row = matches.iloc[0]
                        y_start = int(key_row['top'] + key_row['height'] + 5)
                        h_cell = 33
                        dynamic_rois['DEPENDENCIA_1'] = [y_start, 100, h_cell, 792]
                        dynamic_rois['DEPENDENCIA_2'] = [y_start + h_cell, 100, h_cell, 792]
                        dynamic_rois['DEPENDENCIA_3'] = [y_start + 2*h_cell, 100, h_cell, 792]
                        break
            
            # Restaurar dataframe original
            data_df = data_df_original
        
    if 'HRS_TOTALES' not in dynamic_rois or dynamic_rois['HRS_TOTALES'] is None:
        if 'CRN' in dynamic_rois and 'DESDE' in dynamic_rois:
            roi_proximidad = get_hours_by_proximity(data_df, dynamic_rois['CRN'], dynamic_rois['DESDE'])
            if roi_proximidad:
                dynamic_rois['HRS_TOTALES'] = roi_proximidad

    return dynamic_rois


def clean_border_chars(text: str) -> str:
    if not text:
        return ""
    #eliminar contaminacion en los campos de dependencia.
    text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
    
    # Elimina caracteres no alfanuméricos al inicio y final del texto
    text = re.sub(r'^[-\s!|\/,\?=:._-]+', '', text)
    text = re.sub(r'[-\s!|\/,\?=:._-]+$', '', text)


    # text = re, sub(r'^=,', '', text)  # Elimina '=' al inicio

    text = re.sub(r'\s+', ' ', text)  # Reemplaza múltiples espacios por uno solo
    # Aplicar allowlist: conservar letras, dígitos, coma, punto, espacio y guión
    text = keep_allowed_chars(text, ',.- ')
    return text.strip()


def keep_allowed_chars(text: str, extra_allowed: str = ',.- ') -> str:
    """Conserva únicamente caracteres A-Z a-z 0-9 y los símbolos permitidos.

    extra_allowed: string con caracteres adicionales permitidos (por defecto ",.- ")
    """
    if not text:
        return ""
    # Usar \w para incluir letras Unicode (acentos), dígitos y guión bajo.
    # Luego eliminar guiones bajos si aparecen.
    pattern = rf"[^\w{re.escape(extra_allowed)}]"
    cleaned = re.sub(pattern, '', str(text), flags=re.UNICODE)
    # Quitar guiones bajos introducidos por \w
    cleaned = cleaned.replace('_', '')
    return cleaned



def clean_data_by_field(field_name: str, text: str) -> str:
    """Aplica limpieza específica basada en el tipo de campo."""
    if not text:
        return ""
    
    cleaned_value = text.upper().strip()
    
    # --- 1. HORAS TOTALES ---
    if field_name == 'HRS_TOTALES':
        cleaned_value = re.sub(r'[^\d\.]', '', str(text))
        if not cleaned_value or cleaned_value == ".":
            return "0.00"

        if cleaned_value.count('.') > 1:
            parts = cleaned_value.split('.')
            cleaned_value = parts[0] + '.' + ''.join(parts[1:])
        
        try:
            val = float(cleaned_value)
            if val >= 100 and '.' not in str(text):
                val = val / 100
            if val == 0: 
                return "0.00"
            return "{:.2f}".format(val)
        except ValueError:
            return "0.00"

    # --- 2. CAMPOS NUMÉRICOS ---
    if field_name in ['TELEFONO', 'CODIGO', 'NUM', 'CRN']:
        if field_name == 'TELEFONO' and cleaned_value in PHONE_EMPTY_TOKENS:
            return EMPTY_DATA_PLACEHOLDER
        
        text = re.sub(r'[A-Z]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[^\d\s\-\.]', '', text).strip()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # --- 3. CAMPOS ALFA-NUMÉRICOS (RFC, CURP, IMSS) ---
    elif field_name in ['RFC', 'CURP', 'IMSS']:
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        if field_name == 'RFC' and len(text) > 13:
            rfc_match = re.search(r'[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}', text)
            text = rfc_match.group() if rfc_match else text[:13]
        elif field_name == 'CURP':
            curp_match = re.search(r'[A-Z]{6}\d{6}[A-Z0-9]{6}', text)
            if curp_match: text = curp_match.group()
            elif len(text) >= 18: text = text[-18:]
        elif field_name == 'IMSS':
            text = re.sub(r'[^0-9]', '', text)
            if len(text) > 11: text = text[:11]
        return text

    # --- 4. MATERIA (CON SOPORTE MEJORADO PARA T/P) ---
    elif field_name == 'MATERIA':
        text_up = text.upper().strip()
        
        # A. Rescatar indicador (T) o (P) con o sin paréntesis, incluso con espacios
        # Detecta: "(T)", "( P )", " T", " P" al final del texto pero antes de basura numérica
        tipo_rescatado = ""
        # Buscamos una T o P que esté sola al final o rodeada de paréntesis
        match_tipo = re.search(r'[\s\(]([TP])[\s\)]?$', text_up)
        if not match_tipo:
            # Reintento: si hay números de créditos al final, buscamos la T/P antes de ellos
            match_tipo = re.search(r'[\s\(]([TP])[\s\)]?(?=\s+\d+)', text_up)
        
        if match_tipo:
            tipo_rescatado = f"({match_tipo.group(1)})"

        # B. Cortar por palabras de bloqueo (columna contigua)
        palabras_bloqueo = ['CREDITOS', 'CRÉDITOS', 'HORAS', 'HRS', 'CREDIT']
        for palabra in palabras_bloqueo:
            if palabra in text_up:
                text_up = text_up.split(palabra)[0]
        
        # C. Limpieza de números de créditos al final (ej. "MATERIA 8")
        # Pero nos aseguramos de no borrar la T o P si ya la identificamos
        text_up = re.sub(r'\s+\d+\s*$', '', text_up).strip()
        
        # D. Si rescatamos un tipo y ya no está en el texto limpio, lo re-anexamos
        if tipo_rescatado:
            # Evitar duplicados como "MATERIA (T) (T)"
            base_sin_tipo = re.sub(r'[\s\(]+[TP][\s\)]*$', '', text_up).strip()
            return f"{base_sin_tipo} {tipo_rescatado}".strip()
            
        return text_up.strip()
            
    # --- 5. DEPENDENCIAS ---
    elif "DEPENDENCIA" in field_name:
        text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
        text = re.sub(r'^[-\s!|\/,\?=:-]+', '', text)
        if 'corregir_con_catalogo' in globals():
            text = corregir_con_catalogo(text, field_name)
        return text.strip()
    
    # --- 6. TEXTO GENERAL ---
    else:
        text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
        text = re.sub(r'^[-\s!|\/,\?=:-]+', '', text)
        text = re.sub(r'[-\s!|\/,\?=:-]+$', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = keep_allowed_chars(text, ',.- ')
        return text

def validate_field_format(field_name: str, text: str) -> str:
    """Valida y corrige el formato de campos específicos después de la limpieza inicial."""
    if not text:
        return text
    
    text = keep_allowed_chars(text, ',.- ')
    text = text.upper().strip()
    
    if field_name == 'RFC':
        text = re.sub(r'[^A-Z0-9]', '', text)
        if len(text) >= 10: text = text[:13]
            
    elif field_name == 'CURP':
        text = re.sub(r'[^A-Z0-9]', '', text)
        if len(text) >= 10: 
            curp_match = re.search(r'[A-Z0-9]{10,18}', text)
            if curp_match:
                text = curp_match.group()[:18]
            else: text = ""
        else: text = ""
            
    elif field_name == 'IMSS':
        text = re.sub(r'[^0-9]', '', text)
        if len(text) < 5: return ""
        if len(text) > 11: text = text[:11]
        
    elif field_name == 'TELEFONO':
        text = re.sub(r'[^0-9]', '', text)
        if len(text) > 10: text = text[:10]
    
    elif field_name == 'NUM':
        text = re.sub(r'[^0-9]', '', text)
        if len(text) > 7: text = text[:7]

    elif field_name == 'RNC':
        text = re.sub(r'[^0-9]', '', text)
        if len(text) < 2: return ""
        if len(text) > 6: text = text[:6]

    elif field_name in ['DESDE', 'HASTA']:
        text = re.sub(r'[^0-9\/\-\.]', '', text) 
        text = text.replace('.', '/').replace('-', '/')
        if len(text) == 8 and text.isdigit():
            text = f"{text[:2]}/{text[2:4]}/{text[4:]}"
        
        match = re.match(r'(\d{1,2})[\/](\d{1,2})[\/](\d{2,4})', text)
        if match:
            day, month, year = match.groups()
            if int(day) > 31 and (day.startswith('4') or day.startswith('7')): 
                day = '1' + day[1:]
            if int(month) > 12 and month.startswith('4'): 
                month = '0' + month[1:]
            day, month = day.zfill(2), month.zfill(2)
            if len(year) == 2: year = '20' + year
            return f"{day}/{month}/{year}"
        return text if len(text) >= 8 else ""
            
    return text


def clean_name_specific(text: str) -> str:
    """Limpieza específica para campos de nombre"""
    if not text:
        return ""
    #para poner que no haya A solitaria antes del apellido
    text = re.sub(r'^\bA\s+', '', text)  # Elimina 'A' solitaria
    #elimina SZ al inicio 
    text = re.sub(r'^ZS', '', text)  # Elimina 'SZ' al inicio
    text = re.sub(r'^[AZ]\s+', '', text)  # Elimina 'A' o 'Z' solitaria al inicio
    #elimina AE en el apellido materno
    text = re.sub(r'AE$', '', text)  # Elimina 'AE' al final
    #Elimina y separa nombres pegados por un punto o guion o coma ejemplo RAMIREZ.EDUARDO
    text = re.sub(r'([A-Z])[\.,\-]([A-Z])', r'\1 \2', text)  # Separa nombres pegados por '.', ',', '-'
    # Eliminar casos específicos problemáticos
    text = re.sub(r'^=,', '', text)  # Caso: "=,MARISCAL"
    text = re.sub(r':\s*$', '', text)  # Caso: "JOSE CARLOS:"
    text = re.sub(r'!\s*', ' ', text)  # Caso: "NAYELI! ARELI"
    text = re.sub(r'\s+7$', '', text)  # Caso: "HECTOR GUILLERMO 7"
    
    # Eliminar caracteres problemáticos en general
    text = re.sub(r'[=:!]', '', text)
    
    return text.strip()

def corregir_con_catalogo(texto_ocr, nivel_dependencia, threshold=0.6):
    """
    Compara el texto del OCR con el catálogo y devuelve la opción más parecida.
    """
    if not texto_ocr or nivel_dependencia not in CATALOGO_DEPENDENCIAS:
        return texto_ocr

    opciones = CATALOGO_DEPENDENCIAS[nivel_dependencia]
    mejor_coincidencia = texto_ocr
    max_prob = 0
    
    texto_ocr = texto_ocr.upper().strip()

    for opcion in opciones:
        # Calculamos la similitud (0.0 a 1.0)
        prob = SequenceMatcher(None, texto_ocr, opcion.upper()).ratio()
        if prob > max_prob:
            max_prob = prob
            mejor_coincidencia = opcion

    # Si la similitud es alta, devolvemos el valor oficial del catálogo
    if max_prob >= threshold:
        return mejor_coincidencia
    
    return texto_ocr # Si es muy diferente, dejamos lo que el OCR leyó

def buscador_identidad_global(texto_ocr, threshold=0.65):
    """
    Busca en TODO el catálogo para identificar a qué nivel pertenece el texto
    y devuelve (Nivel_Detectado, Texto_Oficial).
    Usa un threshold más bajos (0.65) para aceptar coincidencias parciales.
    """
    if not texto_ocr or len(texto_ocr) < 3:
        return None, texto_ocr

    mejor_coincidencia = texto_ocr
    mejor_nivel = None
    max_prob = 0
    
    texto_ocr_norm = texto_ocr.upper().strip()

    # Buscamos en todas las llaves del catálogo
    for nivel, opciones in CATALOGO_DEPENDENCIAS.items():
        for opcion in opciones:
            prob = SequenceMatcher(None, texto_ocr_norm, opcion.upper()).ratio()
            if prob > max_prob:
                max_prob = prob
                mejor_coincidencia = opcion
                mejor_nivel = nivel

    # Si la coincidencia es buena, devolvemos el veredicto
    if max_prob >= threshold:
        return mejor_nivel, mejor_coincidencia
    
    # Si no se parece a nada, devolvemos None para que el sistema 
    # sepa que es un dato "desconocido" o nuevo
    return None, texto_ocr

def procesar_bloque_dependencias(dict_textos_extraidos):
    """
    Procesa dependencias priorizando la Dependencia 3 y buscando patrones dinámicos.
    """
    resultados_finales = {
        "DEPENDENCIA_1": EMPTY_DATA_PLACEHOLDER,
        "DEPENDENCIA_2": EMPTY_DATA_PLACEHOLDER,
        "DEPENDENCIA_3": EMPTY_DATA_PLACEHOLDER
    }
    
    # Unificamos todos los textos encontrados en el área de dependencias para analizarlos
    textos_area = [str(v).upper() for v in dict_textos_extraidos.values() if v]
    texto_completo = "\n".join(textos_area)
    lineas = [l.strip() for l in texto_completo.split('\n') if len(l.strip()) > 3]

    # 1. Prioridad: Identificar Dependencia 3 (Departamentos)
    for linea in lineas:
        # Intentar coincidencia con catálogo
        match_cat = corregir_con_catalogo(linea, "DEPENDENCIA_3", threshold=0.75)
        if match_cat in CATALOGO_DEPENDENCIAS["DEPENDENCIA_3"]:
            resultados_finales["DEPENDENCIA_3"] = match_cat
            break
        
        # BÚSQUEDA DINÁMICA: Si contiene "DEPTO. DE" y no se halló en catálogo
        regex_depto = re.search(r'(DEPTO\.\s+DE\s+.*)', linea)
        if regex_depto:
            resultados_finales["DEPENDENCIA_3"] = regex_depto.group(1).strip()
            break

    # 2. Identificar Dependencia 2 (Divisiones)
    for linea in lineas:
        match_cat = corregir_con_catalogo(linea, "DEPENDENCIA_2", threshold=0.75)
        if match_cat in CATALOGO_DEPENDENCIAS["DEPENDENCIA_2"]:
            resultados_finales["DEPENDENCIA_2"] = match_cat
            break

    # 3. Identificar Dependencia 1 (Centro)
    for linea in lineas:
        match_cat = corregir_con_catalogo(linea, "DEPENDENCIA_1", threshold=0.75)
        if match_cat in CATALOGO_DEPENDENCIAS["DEPENDENCIA_1"]:
            resultados_finales["DEPENDENCIA_1"] = match_cat
            break
    
    return resultados_finales


def get_code_by_proximity(df, anchor_roi, horizontal_threshold=35):
    """
    Busca un candidato a código a la izquierda de una ROI (usualmente NOMBRE_COMPLETO_RAW).
    """
    if not anchor_roi or df.empty:
        return None
    
    # anchor_roi = [y, x, h, w]
    y_top_anchor, x_left_anchor = anchor_roi[0], anchor_roi[1]
    y_bottom_anchor = y_top_anchor + anchor_roi[2]
    y_center_anchor = y_top_anchor + (anchor_roi[2] / 2)

    # Buscar candidatos que estén en la misma franja horizontal pero a la izquierda
    candidates = df[
        (df['top'] + (df['height']/2) >= y_center_anchor - horizontal_threshold) &
        (df['top'] + (df['height']/2) <= y_center_anchor + horizontal_threshold) &
        (df['left'] + df['width'] < x_left_anchor + 50) # Que terminen antes de que empiece el nombre (con margen)
    ].copy()

    if not candidates.empty:
        # Limpiar texto y validar que parezca un código (alfanumérico, sin mucha basura)
        candidates['clean_text'] = candidates['text'].apply(lambda x: re.sub(r'[^A-Z0-9]', '', x))
        # Filtrar por longitud típica de código (ej. >= 5 caracteres)
        real_candidates = candidates[candidates['clean_text'].str.len() >= 5].copy()
        
        if not real_candidates.empty:
            # Calcular distancia horizontal al nombre
            real_candidates['dist'] = x_left_anchor - (real_candidates['left'] + real_candidates['width'])
            # Retornar el más cercano
            best = real_candidates.sort_values(by='dist').iloc[0]
            return [int(best['top'] - 5), int(best['left'] - 5), 40, int(best['width'] + 10)]
    
    return None



def get_hours_by_proximity(df, crn_roi, desde_roi):
    """
    Busca el dato de horas que se encuentra físicamente entre CRN y DESDE.
    """
    if df.empty or not crn_roi or not desde_roi:
        return None

    # Coordenadas de las anclas: [y, x, h, w]
    x_limit_left = crn_roi[1] + crn_roi[3]  # Donde termina CRN
    x_limit_right = desde_roi[1]             # Donde empieza DESDE
    y_center_reference = crn_roi[0] + (crn_roi[2] / 2)
    
    # Margen de tolerancia vertical (píxeles)
    v_tolerance = 20 

    # Buscar candidatos en esa "caja" virtual entre ambas etiquetas
    candidates = df[
        (df['left'] >= x_limit_left - 10) & 
        (df['left'] + df['width'] <= x_limit_right + 50) &
        (df['top'] + (df['height']/2) >= y_center_reference - v_tolerance) &
        (df['top'] + (df['height']/2) <= y_center_reference + v_tolerance)
    ].copy()

    if not candidates.empty:
        # Limpiar y verificar si el texto parece un número (horas)
        candidates['clean'] = candidates['text'].apply(lambda x: re.sub(r'[^\d\.]', '', str(x)))
        valid = candidates[candidates['clean'].str.len() > 0]
        
        if not valid.empty:
            # Tomar el que esté más al centro o el primero detectado
            best = valid.iloc[0]
            return [int(best['top'] - 5), int(best['left'] - 5), 40, int(best['width'] + 10)]
            
    return None