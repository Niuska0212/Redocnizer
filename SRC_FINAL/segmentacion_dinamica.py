# segmentacion_dinamica.py
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

# =========================================================================
# === SEGMENTACION DINAMICA CON TESSERACT Y PANDAS (PSM 3) ===
# =========================================================================

def get_dynamic_rois(img_full: np.ndarray) -> dict:
    H, W = img_full.shape[:2]

    std_dev = np.std(img_full)
    THRESHOLD_STD = 43

    if std_dev < THRESHOLD_STD:
        print(f"Pre-procesamiento: fondo uniforme (Otsu). STD: {std_dev:.2f}")
        try:
            img_full_bin = cv2.threshold(img_full, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        except Exception:
            img_full_bin = img_full
    else:
        print(f"Pre-procesamiento: fondo complejo (Adaptative). STD: {std_dev:.2f}")
        try:
            img_full_bin = cv2.adaptiveThreshold(
                img_full, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
            )
        except Exception:
            img_full_bin = img_full

    img_pil = Image.fromarray(img_full_bin)

    data_df = pytesseract.image_to_data(
        img_pil,
        output_type=pytesseract.Output.DATAFRAME,
        config='--psm 3'
    )

    data_df = data_df.dropna(subset=['text'])
    data_df = data_df[data_df['conf'] > 3].copy()
    data_df['text'] = data_df['text'].str.upper().str.strip()

    TOTAL_WIDTH_NOMBRE = 600
    CELL_HEIGHT_NOMBRE = 25

    TOTAL_HEIGHT_DEP = 99
    CELL_WIDTH_DEP = 792
    CELL_HEIGHT_DEP = int(TOTAL_HEIGHT_DEP / 3)

    X_START_VAL_COL = 250
    W_FIXED_VAL_COL = 350
    H_FIXED_VAL_CELL = 57

    # POSICIONES FIJAS PARA FALLBACK
    NUM_FALLBACK_X = 930
    NUM_FALLBACK_Y = 230

    # ANCHOS ESPECÍFICOS Y POSICIONES FIJAS PARA RFC, IMSS, CURP
    RFC_WIDTH = 230
    IMSS_WIDTH = 230
    CURP_WIDTH = 350

    #la altura de IMSS se encuentra 
    # POSICIONES FIJAS ABSOLUTAS (más a la izquierda)
    RFC_X = 100
    IMSS_X = RFC_X + RFC_WIDTH + 20   # 100 + 230 + 10 = 340
    CURP_X = IMSS_X + IMSS_WIDTH + 10 # 340 + 230 + 10 = 580

    name_keywords = ['PATERNO', 'MATERNO', 'NOMBRE(S)', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'APELLIDOS']
    dep_keywords = ['DEPENDENCIA', 'DEPENDENCIAS']
    
    simple_fields_right = {
        'NUM': ['NÚM', 'NUM', 'NUM:', 'NÚM:']
    }
    
    # CÓDIGO y TELÉFONO están DEBAJO de sus etiquetas
    simple_fields_below = {
        'CODIGO': ['CÓDIGO', 'CODIGO'],
        'TELEFONO': ['TELÉFONO', 'TELEFONO', 'TEL'],
        'CRN': ['CRN'],
        'HRS_TOTALES': ['HRS. TOTALES', 'HRS TOTALES', 'HORAS TOTALES', 'HRS. TOTALES CURSO'],
        'DESDE': ['DESDE'],
        'HASTA': ['HASTA'],
    }

    dynamic_rois = {}

    # 1. Lógica para extraer el nombre completo
    header_matches = data_df[data_df['text'].isin(name_keywords)]
    if not header_matches.empty:
        anchor_row = header_matches.iloc[0]
        y_start_base = anchor_row['top'] + anchor_row['height'] + 10
        value_candidates = data_df[
            (data_df['top'] >= y_start_base) &
            (data_df['top'] < y_start_base + 50)
        ].sort_values(by='top')
        if not value_candidates.empty:
            y_start = value_candidates.iloc[0]['top'] - 5
        else:
            y_start = y_start_base
        x_roi_start = 200
        dynamic_rois['NOMBRE_COMPLETO_RAW'] = [y_start, x_roi_start, CELL_HEIGHT_NOMBRE, TOTAL_WIDTH_NOMBRE]

    # 2. Lógica para el bloque de DEPENDENCIA
    for keyword in dep_keywords:
        matches = data_df[data_df['text'] == keyword]
        if not matches.empty:
            key_row = matches.iloc[0]
            x_key = key_row['left']
            h_key = key_row['height']
            y_search_start = key_row['top'] + h_key + 5
            x_start = 130
            value_candidates = data_df[
                (data_df['top'] >= y_search_start) &
                (data_df['left'] >= x_start - 5) &
                (data_df['left'] <= x_start + 100)
            ].sort_values(by='top')
            if not value_candidates.empty:
                y_start = int(value_candidates.iloc[0]['top']) - 5
            else:
                y_start = 710
            h_dep = int(CELL_HEIGHT_DEP)
            w_dep = int(CELL_WIDTH_DEP)
            dynamic_rois['DEPENDENCIA_1'] = [y_start, x_start, h_dep, w_dep]
            dynamic_rois['DEPENDENCIA_2'] = [y_start + h_dep, x_start, h_dep, w_dep]
            dynamic_rois['DEPENDENCIA_3'] = [y_start + 2 * h_dep, x_start, h_dep, w_dep]
            break

    # 3. Lógica SOLO para NUM (a la derecha)
    for field_name, keywords in simple_fields_right.items():
        if field_name not in dynamic_rois:
            for keyword in keywords:
                matches = data_df[data_df['text'].str.contains(r'|'.join(keywords), case=False, regex=True)]
                if not matches.empty:
                    key_row = matches.iloc[0]
                    key_right = key_row['left'] + key_row['width']
                    y_start_label = key_row['top']
                    
                    w_roi, h_roi = 160, 40
                    
                    value_candidates = data_df[
                        (data_df['top'] >= y_start_label - 15) &
                        (data_df['top'] <= y_start_label + 15) &
                        (data_df['left'] >= key_right + 5)
                    ].sort_values(by='left').head(1)

                    if value_candidates.empty:
                        x_start, y_start = NUM_FALLBACK_X, NUM_FALLBACK_Y
                    else:
                        x_start = int(value_candidates.iloc[0]['left']) - 15
                        y_start = int(value_candidates.iloc[0]['top']) - 15

                    dynamic_rois[field_name] = [y_start, x_start, h_roi, w_roi]
                    break

    # 4. Lógica para RFC, IMSS, CURP (POSICIONES FIJAS INDEPENDIENTES)
    base_row_y = None
    
    # Primero buscar todos para establecer la fila base común
    rfc_matches = data_df[data_df['text'].str.contains(r'R\.?F\.?C\.?\s*$', case=False, regex=True)]
    #codigo mejorado para RFC
    #rfc_matches = data_df[data_df['text'].str.contains(r'R\.?F\.?C\.c*RFC', case=False, regex=True)]
    # CÓDIGO MEJORADO PARA IMSS
    imss_matches = data_df[data_df['text'].str.contains(r'I\.?M\.?S\.?S|AFIL\.?\s*IMSS|NO\.?\s*AFIL\.?\s*IMSS', case=False, regex=True)]
    curp_matches = data_df[data_df['text'].str.contains(r'CURP\.?\s*$', case=False, regex=True)]
    
    # Establecer base_row_y con el primer campo que se encuentre
    for matches in [rfc_matches, imss_matches, curp_matches]:
        if not matches.empty:
            key_row = matches.iloc[0]
            y_search_start = key_row['top'] + key_row['height'] + 5
            value_candidates = data_df[
                (data_df['top'] >= y_search_start) &
                (data_df['top'] <= y_search_start + 50) &
                (data_df['left'] >= key_row['left'] - 50) &
                (data_df['left'] <= key_row['left'] + 400)
            ].sort_values(by='top').head(1)
            
            if not value_candidates.empty:
                base_row_y = value_candidates.iloc[0]['top'] - 10
                break
    
    # Si no se encontró ningún valor, usar posición por defecto
    if base_row_y is None:
        base_row_y = 400  # Posición Y por defecto
    # Procesar RFC (si existe)
    if not rfc_matches.empty:
        dynamic_rois['RFC'] = [base_row_y, RFC_X, 45, RFC_WIDTH]

    # Procesar IMSS (si existe) - INDEPENDIENTE DE RFC
    if not imss_matches.empty:
        dynamic_rois['IMSS'] = [base_row_y - 2 , IMSS_X, 40, IMSS_WIDTH]

    # Procesar CURP (si existe) - INDEPENDIENTE DE LOS OTROS
    if not curp_matches.empty:
        dynamic_rois['CURP'] = [base_row_y, CURP_X, 45, CURP_WIDTH]

    # 5. Lógica para campos DEBAJO (CÓDIGO, TELÉFONO, CRN, etc.)
    for field_name, keywords in simple_fields_below.items():
        if field_name not in dynamic_rois:
            for keyword in keywords:
                matches = data_df[data_df['text'].str.contains('|'.join(keywords), case=False, regex=True)]
                if not matches.empty:
                    key_row = matches.iloc[0]
                    y_search_start = key_row['top'] + key_row['height'] + 5

                    value_candidates = data_df[
                        (data_df['top'] >= y_search_start) &
                        (data_df['top'] <= y_search_start + 80) &
                        (data_df['left'] >= key_row['left'] - 50) &
                        (data_df['left'] <= key_row['left'] + 400)
                    ].sort_values(by='top').head(1)

                    # Valores por defecto
                    x_start = key_row['left']
                    y_start = y_search_start
                    h_roi = 54
                    w_roi = 200

                    if not value_candidates.empty:
                        y_start = value_candidates.iloc[0]['top'] - 10
                        x_start = value_candidates.iloc[0]['left'] - 10

                    # Ajustes específicos
                    if field_name == 'CODIGO':
                        w_roi = 150
                        x_start = 700 if value_candidates.empty else value_candidates.iloc[0]['left'] - 10
                    
                    elif field_name == 'TELEFONO':
                        w_roi = 200
                        x_start = 700 if value_candidates.empty else value_candidates.iloc[0]['left'] - 10
                    
                    elif field_name == 'CRN':
                        w_roi = 170
                        x_start = 150
                    elif field_name == 'HRS_TOTALES':
                        w_roi = 120
                        x_start = 330
                    elif field_name == 'DESDE':
                        w_roi = 240
                        x_start = 550
                    elif field_name == 'HASTA':
                        w_roi = 240
                        x_start = 800

                    dynamic_rois[field_name] = [y_start, x_start, h_roi, w_roi]
                    break
                
    return dynamic_rois


def clean_border_chars(text: str) -> str:
    if not text:
        return ""
    #eliminar contaminacion en los campos de dependencia.
    text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
    
    # Elimina caracteres no alfanuméricos al inicio y final del texto
    text = re.sub(r'^[-\s!|\/,\?.]+', '', text)
    text = re.sub(r'[-\s!|\/,\?.]+$', '', text)

    text = re.sub(r'\s+', ' ', text)  # Reemplaza múltiples espacios por uno solo
    return text.strip()


def clean_data_by_field(field_name: str, text: str) -> str:
    """Aplica limpieza específica basada en el tipo de campo."""
    if not text:
        return ""
    
    # 1. Campos que SÓLO deberían ser Números (o casi)
    if field_name in ['TELEFONO', 'CODIGO', 'NUM', 'HRS_TOTALES', 'CRN']:
        # Elimina cualquier letra (a-z) en el texto
        text = re.sub(r'[A-Z]', '', text, flags=re.IGNORECASE)
        # Elimina cualquier símbolo, manteniendo solo números y espacios
        text = re.sub(r'[^\d\s\-\.]', '', text).strip()
        # Limpia espacios extra
        text = re.sub(r'\s+', ' ', text).strip()
    
    # 2. Campos Alfa-Numéricos (RFC, IMSS, CURP) - LIMPIEZA MÁS AGRESIVA
    elif field_name in ['RFC', 'CURP', 'IMSS']:
        # Eliminar TODOS los caracteres especiales y espacios
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Validaciones específicas por tipo de campo
        if field_name == 'RFC':
            # RFC debe tener 12-13 caracteres alfanuméricos
            if len(text) > 13:
                text = text[:13]
            # Eliminar dígitos extra al final si tiene más de 13
            text = re.sub(r'^([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}).*', r'\1', text)
            
        elif field_name == 'CURP':
            # CURP debe tener 18 caracteres exactos
            if len(text) > 18:
                text = text[:18]
            # Patrón básico de CURP: 4 letras, 6 números, 1 letra, 1 sexo, 2 letras, 3 números
            text = re.sub(r'^([A-Z]{4}\d{6}[A-Z]{6}\d{2}).*', r'\1', text)
            
        # En la función clean_data_by_field (Línea ~280)

        elif field_name == 'IMSS':
            # IMSS generalmente son 11 dígitos, pero puede variar
            # Mantener solo números para IMSS
            text = re.sub(r'[^0-9]', '', text)
            if len(text) > 11:
                text = text[:11]
    
    # 3. Campos de texto general (Dependencias, Nombres)
    else:
        # Eliminar contaminación en campos de dependencia
        text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
        
        # Eliminar caracteres no alfanuméricos al inicio y final
        text = re.sub(r'^[-\s!|\/,\?]+', '', text)
        text = re.sub(r'[-\s!|\/,\?]+$', '', text)
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()

    return text.strip()

# Función adicional para validación específica
def validate_field_format(field_name: str, text: str) -> str:
    """Valida y corrige el formato de campos específicos."""
    if not text:
        return text
        
    text = text.upper().strip()
    
    if field_name == 'RFC':
        # Eliminar espacios y caracteres especiales
        text = re.sub(r'[^A-Z0-9]', '', text)
        # Asegurar formato: 4 letras, 6 números, 3 alfanuméricos
        if len(text) >= 10:
            # Tomar primeros 13 caracteres máximo
            text = text[:13]
            
    elif field_name == 'CURP':
        text = re.sub(r'[^A-Z0-9]', '', text)
        if len(text) >= 16:
            text = text[:18]
            
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
        # asegurar que num sea numerico y tenga maximo 7 caracteres
        text = re.sub(r'[^0-9]', '', text)
        if len(text) >= 7:
            text = text[:7]

    elif field_name == 'RNC':
        # asegurar que rnc sea numerico y tenga maximo 10 caracteres
        text = re.sub(r'[^0-9]', '', text)
        if len(text) < 2:
            return ""

        if len(text) > 6:
            text = text[:6]

    elif field_name == 'DESDE' or field_name == 'HASTA':
        # Asegurar formato de fecha DD/MM/YYYY o DD-MM-YYYY
        match = re.match(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})', text)
        if match:
            day, month, year = match.groups()
            day = day.zfill(2)
            month = month.zfill(2)
            if len(year) == 2:
                year = '20' + year  # Asumir siglo 21 para años de 2 dígitos
            text = f"{day}/{month}/{year}"
        else:
            text = ""

            
    return text