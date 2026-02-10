# core/segmentacion_dinamica.py
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


# Inicializar el lector (puedes hacerlo global o dentro de la función)
# 'es' para español, gpu=True si tienes una tarjeta NVIDIA configurada
reader = easyocr.Reader(['es'], gpu=False)

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
    CAMPOS_CRITICOS = {'CODIGO', 'NUM', 'MATERIA', 'HRS_TOTALES', 'DEPENDENCIA_1', 'NOMBRE_COMPLETO_RAW'}
    
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
        'HRS_TOTALES':  {'keys': ['HRS. TOTALES', 'HORAS TOTALES', 'HRS TOTALES', 'HRS.'], 'w': 160, 'h_limit': 45},
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
    # 1. Campos que SÓLO deberían ser Números (o casi)
    if field_name in ['TELEFONO', 'CODIGO', 'NUM', 'HRS_TOTALES', 'CRN']:
        # --- Lógica Específica para TELEFONO ---
        if field_name == 'TELEFONO':
            # 1. Si el valor coincide con un token de 'dato vacío en el documento', estandarizar.
            if cleaned_value in PHONE_EMPTY_TOKENS:
                return EMPTY_DATA_PLACEHOLDER
        # Elimina cualquier letra (a-z) en el texto
        text = re.sub(r'[A-Z]', '', text, flags=re.IGNORECASE)
        # Elimina cualquier símbolo, manteniendo solo números y espacios
        text = re.sub(r'[^\d\s\-\.]', '', text).strip()
        # Limpia espacios extra
        text = re.sub(r'\s+', ' ', text).strip()

        if field_name == 'TELEFONO' and not text:
            return ""
    
    # 2. Campos Alfa-Numéricos (RFC, IMSS, CURP) - LIMPIEZA MÁS AGRESIVA
    elif field_name in ['RFC', 'CURP', 'IMSS']:
        # Eliminar TODOS los caracteres especiales y espacios
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Validaciones específicas por tipo de campo
        if field_name == 'RFC':
            # RFC debe tener 12-13 caracteres alfanuméricos
            if len(text) > 13:
                # Buscar el patrón RFC válido en el texto
                rfc_match = re.search(r'[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}', text)
                if rfc_match:
                    text = rfc_match.group()
                else:
                    text = text[:13]
            
        elif field_name == 'CURP':
            # CURP debe tener exactamente 18 caracteres
            # Patrón: 6 letras + 6 números + 6 letras/números
            # Primero intentar encontrar el patrón CURP válido dentro del texto
            curp_match = re.search(r'[A-Z]{6}\d{6}[A-Z0-9]{6}', text)
            if curp_match:
                text = curp_match.group()
            elif len(text) >= 18:
                # Si hay suficientes caracteres, tomar los últimos 18
                text = text[-18:]
            # Si tiene menos de 18 caracteres, mantener como está (posiblemente incompleto)
            
        elif field_name == 'IMSS':
            # IMSS generalmente son 11 dígitos, pero puede variar
            # Mantener solo números para IMSS
            text = re.sub(r'[^0-9]', '', text)
            if len(text) > 11:
                text = text[:11]
        
        elif field_name == 'MATERIA':
            # Si el OCR leyó "FISICA CREDITOS" o "FISICA 8", 
            # buscamos palabras clave de la columna de al lado para cortar.
            palabras_bloqueo = ['CREDITOS', 'CRÉDITOS', 'HORAS', 'HRS', 'CREDIT']
            for palabra in palabras_bloqueo:
                if palabra in text.upper():
                    # Cortamos el texto justo antes de la palabra prohibida
                    text = text.upper().split(palabra)[0]
            
            # Eliminar números aislados al final (que suelen ser los créditos)
            text = re.sub(r'\s+\d+\s*$', '', text)
            return text.strip()
        elif field_name == 'HRS_TOTALES':
            # 1. Dejar solo números y puntos
            text = re.sub(r'[^0-9\.]', '', text)
            # 2. Si el OCR leyó "2000" (sin punto), asumimos 2 decimales
            if '.' not in text and len(text) >= 3:
                text = text[:-2] + "." + text[-2:]
            # 3. Si leyó algo como "20..00" o "20.0.0", limpiar
            if text.count('.') > 1:
                partes = text.split('.')
                text = partes[0] + "." + "".join(partes[1:])[:2]
                
            return text
            
                
    elif "DEPENDENCIA" in field_name:
        # Primero una limpieza básica de ruido
        text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
        text = re.sub(r'^[-\s!|\/,\?=:-]+', '', text)
        
        # Aplicamos la corrección difusa
        # field_name será 'DEPENDENCIA_1', 'DEPENDENCIA_2', etc.
        text = corregir_con_catalogo(text, field_name)
        return text.strip()
    
    # 3. Campos de texto general (Dependencias, Nombres)
    else:
        # Eliminar contaminación en campos de dependencia
        text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)

        # Eliminar caracteres no alfanuméricos al inicio y final, para agregar mas limpieza debes poner aqui las reglas de la siguiete forma : text = re.sub(r'^[-\s!|\/,\?]+', '', text)
        text = re.sub(r'^[-\s!|\/,\?=:-]+', '', text)
        text = re.sub(r'[-\s!|\/,\?=:-]+$', '', text)
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        # Aplicar allowlist final para normalizar caracteres permitidos
        text = keep_allowed_chars(text, ',.- ')

    return text.strip()

# Función adicional para validación específica
def validate_field_format(field_name: str, text: str) -> str:
    """Valida y corrige el formato de campos específicos."""
    if not text:
        return text
    # LIMPIEZA GENERAL: conservar solo caracteres permitidos (A-Z a-z 0-9 y ', . -' y espacio)
    text = keep_allowed_chars(text, ',.- ')
    text = text.upper().strip()
    
    if field_name == 'RFC':
        # Eliminar espacios y caracteres especiales
        text = re.sub(r'[^A-Z0-9]', '', text)
        # Asegurar formato: 4 letras, 6 números, 3 alfanuméricos
        if len(text) >= 10:
            # Tomar primeros 13 caracteres máximo
            text = text[:13]
            
    elif field_name == 'CURP':
        # 1. Limpieza básica
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # 2. Nueva lógica: No ser tan estrictos con la posición de números/letras
        # Buscamos una cadena que tenga la estructura general de una CURP (18 caracteres aprox)
        if len(text) >= 10: 
            # Intentamos buscar el patrón pero permitiendo letras donde van números 
            # por si el OCR se equivoca (ej. O por 0, I por 1)
            curp_match = re.search(r'[A-Z0-9]{10,18}', text)
            
            if curp_match:
                candidate = curp_match.group()
                # Si tiene al menos algo de coherencia, lo mantenemos
                if len(candidate) > 18:
                    text = candidate[:18]
                else:
                    text = candidate
            else:
                text = "" # Solo si de plano no hay nada alfanumérico largo
        else:
            text = ""
            
    # CÓDIGO MEJORADO PARA IMSS (Línea ~279)
    elif field_name == 'IMSS':
        # IMSS generalmente son 11 dígitos, pero puede variar
        # Mantener solo números para IMSS
        text = re.sub(r'[^0-9]', '', text)
        if len(text) < 5:
            return ""
        if len(text) > 11:
            text = text[:11]
        
    elif field_name == 'TELEFONO':
        text = re.sub(r'[^0-9]', '', text)
        if len(text) > 10:
            text = text[:10]
    
    elif field_name == 'NUM':
        # NUM debe ser EXACTAMENTE 7 dígitos (obligatorio, nunca incompleto, nunca con relleno)
        text = re.sub(r'[^0-9]', '', text)
        # Si tiene exactamente 7, mantener
        if len(text) == 7:
            pass  # Válido
        elif len(text) > 7:
            # Si tiene más de 7, tomar los primeros 7
            text = text[:7]
        # Si tiene 1-6 dígitos, dejar como está (será penalizado en contador de reintentos)
        # Si está vacío, dejar vacío

    elif field_name == 'RNC':
        # asegurar que rnc sea numerico y tenga maximo 10 caracteres
        text = re.sub(r'[^0-9]', '', text)
        if len(text) < 2:
            return ""
        if len(text) > 6:
            text = text[:6]

    elif field_name == 'DESDE' or field_name == 'HASTA':
        # 1. Limpieza total: solo números y separadores básicos
        text = re.sub(r'[^0-9\/\-\.]', '', text) 
        text = text.replace('.', '/').replace('-', '/')
        
        # 2. Insertar diagonales si el OCR pegó todo (DDMMYYYY -> DD/MM/YYYY)
        if len(text) == 8 and text.isdigit():
            text = f"{text[:2]}/{text[2:4]}/{text[4:]}"
        
        # 3. Intentar extraer componentes para corregir errores de lectura (como el 46)
        match = re.match(r'(\d{1,2})[\/](\d{1,2})[\/](\d{2,4})', text)
        if match:
            day, month, year = match.groups()
            
            # --- CORRECCIÓN DE DÍGITOS (El truco del 46) ---
            # Si el día es > 31, es casi seguro que el '4' o '7' era un '1'
            if int(day) > 31:
                if day.startswith('4') or day.startswith('7'): 
                    day = '1' + day[1]
            
            # Si el mes es > 12 (ej. leyó 42 en vez de 02)
            if int(month) > 12:
                if month.startswith('4'): 
                    month = '0' + month[1]
            
            # Rellenar con ceros (ej. '4' -> '04')
            day = day.zfill(2)
            month = month.zfill(2)
            
            # Corregir año de 2 dígitos
            if len(year) == 2:
                year = '20' + year
                
            return f"{day}/{month}/{year}"
        
        # Si no tiene el formato mínimo, devolvemos lo que hay o vacío
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
    Recibe un dict con {'DEPENDENCIA_1': 'texto...', 'DEPENDENCIA_2': ...}
    y los reacomoda según su identidad real.
    Maneja casos donde los textos están vacíos o son muy cortos.
    """
    resultados_finales = {
        "DEPENDENCIA_1": "",
        "DEPENDENCIA_2": "",
        "DEPENDENCIA_3": ""
    }
    
    textos_sucios = [
        dict_textos_extraidos.get("DEPENDENCIA_1", ""),
        dict_textos_extraidos.get("DEPENDENCIA_2", ""),
        dict_textos_extraidos.get("DEPENDENCIA_3", "")
    ]

    for i, texto in enumerate(textos_sucios):
        if not texto: 
            continue
        
        # Primero una limpieza básica de basura OCR
        texto_limpio = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', texto)
        texto_limpio = re.sub(r'^[-\s!|\/,\?=:-]+', '', texto_limpio).strip()

        # Si el texto quedó muy corto después de limpieza, ignorar
        if len(texto_limpio) < 3:
            continue

        # Intentamos identificar qué es
        nivel_identificado, texto_oficial = buscador_identidad_global(texto_limpio, threshold=0.65)

        if nivel_identificado:
            # Si lo identificamos, lo ponemos en su lugar correcto (1, 2 o 3)
            resultados_finales[nivel_identificado] = texto_oficial
        else:
            # REGLA DE ESCAPE: Si no está en el diccionario, 
            # lo dejamos donde el OCR lo encontró originalmente
            # pero solo si no hay nada ahí ya
            key_original = f"DEPENDENCIA_{i+1}"
            if not resultados_finales[key_original]:  # Solo si está vacío
                resultados_finales[key_original] = texto_limpio

    return resultados_finales


def search_date_pattern():
    import re
    """Buscar fechas en formato DD/MM/YYYY, DD-MM-YYYY, etc."""
    date_pattern = r'(\d{1,2})[\/\-\.\s](\d{1,2})[\/\-\.\s](\d{2,4})'
    date_matches = data_df[data_df['text'].str.contains(date_pattern, regex=True, na=False)]
    return date_matches


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