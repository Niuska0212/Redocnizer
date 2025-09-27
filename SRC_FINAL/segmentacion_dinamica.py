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

    TOTAL_WIDTH_NOMBRE = 700
    CELL_HEIGHT_NOMBRE = 25

    TOTAL_HEIGHT_DEP = 99
    CELL_WIDTH_DEP = 792
    CELL_HEIGHT_DEP = int(TOTAL_HEIGHT_DEP / 3)

    X_START_VAL_COL = 250
    W_FIXED_VAL_COL = 350
    H_FIXED_VAL_CELL = 57

    name_keywords = ['PATERNO', 'MATERNO', 'NOMBRE(S)', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'APELLIDOS']
    dep_keywords = ['DEPENDENCIA', 'DEPENDENCIAS']
    simple_fields_below = {
        'CRN': ['CRN'],
        'HRS_TOTALES': ['HRS. TOTALES', 'HRS TOTALES', 'HORAS TOTALES', 'HRS. TOTALES CURSO'],
        'DESDE': ['DESDE'],
        'HASTA': ['HASTA']
    }
    simple_fields_right = {
        'NUM': ['NÚM', 'NUM', 'NUM:', 'NÚM:'],
        'CODIGO': ['CÓDIGO', 'CODIGO'],
        'RFC': ['RFC'],
        'IMSS': ['IMSS', 'AFIL IMSS', 'No. AFIL IMSS'],
        'CURP': ['CURP'],
        'TELEFONO': ['TELÉFONO', 'TELEFONO', 'TEL'],
    }

    dynamic_rois = {}

    # 3. Lógica para extraer el nombre completo
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
        x_roi_start = 100
        dynamic_rois['NOMBRE_COMPLETO_RAW'] = [y_start, x_roi_start, CELL_HEIGHT_NOMBRE, TOTAL_WIDTH_NOMBRE]

    # 4. Lógica para el bloque de DEPENDENCIA
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

    # 5.1 Lógica para los campos sencillos (a la derecha y en la misma fila)
    for field_name, keywords in simple_fields_right.items():
        if field_name not in dynamic_rois:
            for keyword in keywords:
                matches = data_df[data_df['text'].str.contains(r'|'.join(keywords), case=False, regex=True)]

                if not matches.empty:
                    key_row = matches.iloc[0]
                    key_right = key_row['left'] + key_row['width']
                    y_start_label = key_row['top']
                    h_roi = 54

                    value_candidates = data_df[
                        (data_df['top'] >= y_start_label - 10) &
                        (data_df['top'] <= y_start_label + 10) &
                        (data_df['left'] >= key_right + 10)
                    ].sort_values(by='left').head(1)

                    if not value_candidates.empty:
                        x_start = int(value_candidates.iloc[0]['left'])
                        y_start = int(value_candidates.iloc[0]['top'])
                    else:
                        if field_name in ['NUM', 'CODIGO', 'TELEFONO']:
                            x_start = 800
                            w_roi = 200
                        else:
                            x_start = X_START_VAL_COL
                            w_roi = 350
                        y_start = y_start_label

                    if field_name == 'NUM':
                        w_roi = 160
                        h_roi = 40
                        if not value_candidates.empty:
                            x_start = int(value_candidates.iloc[0]['left'])
                            y_start = int(value_candidates.iloc[0]['top']) - 5
                        else:
                            x_start = 800
                            y_start = key_row['top']

                    elif field_name == 'CODIGO':
                        w_roi = 150
                        h_roi = 40
                        x_start = 830
                        y_start = key_row['top']

                    elif field_name == 'RFC':
                        if not value_candidates.empty:
                            y_start = int(value_candidates.iloc[0]['top']) - 5
                        x_start = X_START_VAL_COL - 100  # Menor posición X
                        w_roi = 250  # Menor ancho
                        h_roi = 54

                    elif field_name == 'IMSS':
                        if 'RFC' in dynamic_rois:
                            rfc_roi = dynamic_rois['RFC']
                            y_start = rfc_roi[0]  # misma altura que RFC
                            x_start = rfc_roi[1] + rfc_roi[3] + 5  # justo a la derecha de RFC
                            w_roi = 200
                            h_roi = rfc_roi[2]

                    elif field_name == 'CURP':
                        if 'IMSS' in dynamic_rois:
                            imss_roi = dynamic_rois['IMSS']
                            y_start = imss_roi[0]  # misma altura que IMSS
                            x_start = imss_roi[1] + imss_roi[3] + 5  # justo a la derecha de IMSS
                            w_roi = 480
                            h_roi = 54

                    dynamic_rois[field_name] = [y_start, x_start, h_roi, w_roi]
                    break

    # 5.2 Lógica para los campos sencillos (Debajo)
    for field_name, keywords in simple_fields_below.items():
        if field_name not in dynamic_rois:
            for keyword in keywords:
                matches = data_df[data_df['text'].str.contains('|'.join(keywords), case=False, regex=True)]
                if not matches.empty:
                    key_row = matches.iloc[0]
                    y_search_start = key_row['top'] + key_row['height'] + 5

                    x_start = X_START_VAL_COL
                    y_start = y_search_start
                    h_roi = H_FIXED_VAL_CELL
                    w_roi = W_FIXED_VAL_COL

                    value_candidates = data_df[
                        (data_df['top'] >= y_search_start) &
                        (data_df['left'] >= X_START_VAL_COL - 50) &
                        (data_df['left'] < X_START_VAL_COL + W_FIXED_VAL_COL)
                    ].sort_values(by='top').head(1)

                    if not value_candidates.empty:
                        y_start = value_candidates.iloc[0]['top']

                    if field_name == 'CRN':
                        w_roi = 170
                        h_roi = 54
                    elif field_name == 'HRS_TOTALES':
                        w_roi = W_FIXED_VAL_COL
                        h_roi = H_FIXED_VAL_CELL
                    elif field_name in ['DESDE', 'HASTA']:
                        x_start = X_START_VAL_COL + 200
                        w_roi = 240
                        h_roi = 55

                    dynamic_rois[field_name] = [y_start, x_start, h_roi, w_roi]
                
    return dynamic_rois

def clean_border_chars(text: str) -> str:
    if not text:
        return ""
    #eliminar contaminacion en los campos de dependencia.
    text = re.sub(r'^((\d\.)+\d?\s*|22\s*|\d+)\s+', '', text)
    
    # Elimina caracteres no alfanuméricos al inicio y final del texto
    text = re.sub(r'^[-\s!|\/,\?]+', '', text)
    text = re.sub(r'[-\s!|\/,\?]+$', '', text)

    text = re.sub(r'\s+', ' ', text)  # Reemplaza múltiples espacios por uno solo
    return text.strip()


def clean_data_by_field(field_name: str, text: str) -> str:
    """Aplica limpieza específica basada en el tipo de campo."""
    if not text:
        return ""
    
    # 1. Campos que SÓLO deberían ser Números (o casi)
    if field_name in ['TELEFONO', 'CODIGO', 'NUM']:
        # Elimina cualquier letra (a-z) en el texto
        text = re.sub(r'[A-Z]', '', text, flags=re.IGNORECASE)
        # Elimina cualquier símbolo, manteniendo solo números y espacios
        text = re.sub(r'[^\d\s\-\.]', '', text).strip()
        # Limpia espacios extra
        text = re.sub(r'\s+', ' ', text).strip()
    
    # 2. Campos Alfa-Numéricos (RFC, IMSS, CURP)
    elif field_name in ['RFC', 'CURP', 'IMSS']:
        # Elimina caracteres de ruido comunes al inicio y final
        text = re.sub(r'^[-\s!|\/,\?]+', '', text)
        text = re.sub(r'[-\s!|\/,\?]+$', '', text)
        # Elimina subcadenas comunes de ruido: "6VGVP", "AE", "IJ", "ZÑZÓ", etc.
        text = re.sub(r'(6VGVP|AE|IJ|CUO09 TS|ZÑZÓ|SES\s*R\s*TES)', '', text, flags=re.IGNORECASE) 
        # Limpia múltiples espacios
        text = re.sub(r'\s+', ' ', text).strip()
    
    # Los demás campos (Dependencias, Nombres) seguirán con clean_border_chars
    return text.strip()
