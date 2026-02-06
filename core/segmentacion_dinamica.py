# segmentacion_dinamica.py
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
    if img_full is None: return {}
    
    H, W = img_full.shape[:2]
    
    # ==========================================================
    # ACLARAR IMAGEN (CORREGIDO)
    # ==========================================================
    # Error previo: Usabas img_gray antes de definirlo.
    img_gray = cv2.cvtColor(img_full, cv2.COLOR_BGR2GRAY) if len(img_full.shape) == 3 else img_full
    
    avg_brightness = np.mean(img_gray)
    if avg_brightness < 120:
        # Normalizamos y aplicamos CLAHE para que EasyOCR vea mejor las letras
        img_gray = cv2.normalize(img_gray, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img_gray = clahe.apply(img_gray)
        
    # Usamos la imagen en escala de grises procesada (uint8)
    # EasyOCR prefiere 3 canales, pero con uint8 gris suele bastar.
    results = reader.readtext(img_gray.astype(np.uint8))
    
    # ==========================================================
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
    
    # Si el OCR no detectó nada, evitamos que truene el DataFrame
    if data_df.empty:
        return {}

    data_df = data_df.dropna(subset=['text'])
    # Bajamos un poco el filtro de confianza a 10 para no perder datos reales
    data_df = data_df[data_df['conf'] > 10].copy() 
    data_df['text'] = data_df['text'].str.upper().str.strip()

    TOTAL_WIDTH_NOMBRE = 600
    CELL_HEIGHT_NOMBRE = 25

    TOTAL_HEIGHT_DEP = 99
    CELL_WIDTH_DEP = 792
    CELL_HEIGHT_DEP = int(TOTAL_HEIGHT_DEP / 3)

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
    dep_keywords = ['DEPENDENCIA', 'DEPENDENCIAS',]
    simple_fields_right = {
        'NUM': ['NÚM', 'NUM', 'NUM:', 'NÚM:', 'NUM.', 'NÚM.']
    }
    

    simple_fields_below = {
        'CODIGO': ['CÓDIGO', 'CODIGO'],
        'CURP': ['CURP','cuRP'],
        'TELEFONO': ['TELÉFONO', 'TELEFONO', 'TEL'],
        'CRN': ['CRN', 'C.R.N.', 'C R N'],
        'MATERIA': ['MATERIA', 'MATERIAS', 'NOMBRE DE LA MATERIA / CURSO', 'NOMBRE DE LA MATERIA'],
        'HRS_TOTALES': ['HRS. TOTALES', 'HRS TOTALES', 'HORAS TOTALES', 'HRS. TOTALES CURSO', 'HRS TOTALES CURSO', 'HRS.'],
        'DESDE': ['DESDE', 'DESDE:'],
        'HASTA': ['HASTA', 'HASTA:'],
    }

    dynamic_rois = {}

    # ============ BÚSQUEDA DE DESDE/HASTA AL FINAL (DESPUÉS DE TODO) ============
    # Si DESDE/HASTA no se encuentran por etiqueta, buscar por patrón de fecha
    def search_date_pattern():
        import re
        """Buscar fechas en formato DD/MM/YYYY, DD-MM-YYYY, etc."""
        date_pattern = r'(\d{1,2})[\/\-\.\s](\d{1,2})[\/\-\.\s](\d{2,4})'
        date_matches = data_df[data_df['text'].str.contains(date_pattern, regex=True, na=False)]
        return date_matches

    # 1. Lógica para extraer el nombre completo
    header_matches = data_df[data_df['text'].isin(name_keywords)]
    if not header_matches.empty:
        anchor_row = header_matches.iloc[0]
        y_start_base = anchor_row['top'] + anchor_row['height'] + 10
        value_candidates = data_df[
            (data_df['top'] >= y_start_base) &
            (data_df['top'] < y_start_base )
        ].sort_values(by='top')
        if not value_candidates.empty:
            y_start = value_candidates.iloc[0]['top'] - 5
        else:
            y_start = y_start_base
        x_roi_start = 200
        dynamic_rois['NOMBRE_COMPLETO_RAW'] = [y_start, x_roi_start, CELL_HEIGHT_NOMBRE, TOTAL_WIDTH_NOMBRE]

    # 2. Búsqueda mejorada de DEPENDENCIA con flexibilidad
    dep_found = False
    for keyword in dep_keywords:
        # Primero intentar coincidencia exacta (lo original)
        matches = data_df[data_df['text'] == keyword]
        
        # Si no se encuentra exacto, buscar por contenencia de substring
        if matches.empty:
            matches = data_df[data_df['text'].str.upper().str.contains(keyword, regex=False, na=False)]
        
        # Si aún no se encuentra, buscar cualquier cosa que EMPIECE con "DEP"
        if matches.empty:
            matches = data_df[data_df['text'].str.upper().str.contains('^DEP', regex=True, na=False)]
        
        if not matches.empty:
            key_row = matches.iloc[0]
            x_key = key_row['left']
            h_key = key_row['height']
            
            # Búsqueda más inteligente: valores DEBAJO de la etiqueta
            y_search_start = key_row['top'] + h_key + 2
            x_start = 100  # Posición X más a la izquierda para captar valores
            
            # Buscar cualquier texto en las líneas siguientes
            value_candidates = data_df[
                (data_df['top'] >= y_search_start) &
                (data_df['top'] < y_search_start + TOTAL_HEIGHT_DEP + 20) &
                (data_df['left'] >= x_start - 50) &
                (data_df['left'] <= x_start + 200)
            ].sort_values(by='top')

            if not value_candidates.empty:
                y_start = int(value_candidates.iloc[0]['top']) - 8
            else:
                # Fallback: comenzar justo bajo la etiqueta
                y_start = int(key_row['top'] + h_key + 5)

            h_dep = int(CELL_HEIGHT_DEP)
            w_dep = int(CELL_WIDTH_DEP)
            
            # ROIs verticales por defecto (líneas debajo de la etiqueta)
            dynamic_rois['DEPENDENCIA_1'] = [y_start, x_start, h_dep, w_dep]
            dynamic_rois['DEPENDENCIA_2'] = [y_start + h_dep, x_start, h_dep, w_dep]
            dynamic_rois['DEPENDENCIA_3'] = [y_start + 2 * h_dep, x_start, h_dep, w_dep]
            dep_found = True
            break
    
    # Si DEPENDENCIA no se encontró, usar posiciones por defecto basadas en documento típico
    if not dep_found:
        # Posiciones fallback típicas para documentos estándar
        # Buscar cualquier texto que se parezca a un departamento (contiene palabras clave)
        dept_keywords = ['DEPTO', 'DIV', 'DIVISION', 'DEPARTAMENTO', 'C.U', 'NSTITUTO']
        dept_matches = data_df[
            data_df['text'].str.upper().str.contains('|'.join(dept_keywords), regex=True, na=False)
        ]
        
        if not dept_matches.empty:
            # Encontramos algo que se parece un departamento
            first_dept = dept_matches.iloc[0]
            y_start = int(first_dept['top']) - 15
            x_start = 100
        else:
            # Usar posiciones completamente por defecto (35% desde la parte superior)
            y_start = int(H * 0.35)
            x_start = 100
        
        h_dep = int(CELL_HEIGHT_DEP)
        w_dep = int(CELL_WIDTH_DEP)
        
        dynamic_rois['DEPENDENCIA_1'] = [y_start, x_start, h_dep, w_dep]
        dynamic_rois['DEPENDENCIA_2'] = [y_start + h_dep, x_start, h_dep, w_dep]
        dynamic_rois['DEPENDENCIA_3'] = [y_start + 2 * h_dep, x_start, h_dep, w_dep]

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
    # Hacer búsqueda más flexible sin el $ (fin de línea)
    rfc_matches = data_df[data_df['text'].str.contains(r'R\.?F\.?C', case=False, regex=True)]
    imss_matches = data_df[data_df['text'].str.contains(r'I\.?M\.?S\.?S|AFIL|NO\.?\s*AFIL', case=False, regex=True)]
    # Búsqueda mejorada para CURP: no requiere fin de línea
    curp_matches = data_df[data_df['text'].str.contains(r'CURP', case=False, regex=True)]
    
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
    
    # Si no se encontró ningún valor, usar posición por defecto más inteligente
    if base_row_y is None:
        # Buscar la primera fila de valores alfanuméricos largos (probablemente documentos)
        long_text = data_df[data_df['text'].str.len() > 10].sort_values(by='top')
        if not long_text.empty:
            base_row_y = int(long_text.iloc[0]['top']) - 10
        else:
            base_row_y = 400  # Posición Y por defecto si nada funciona
    
    # Procesar RFC (si existe)
    if not rfc_matches.empty:
        dynamic_rois['RFC'] = [base_row_y, RFC_X, 45, RFC_WIDTH]
    else:
        # Fallback: posición por defecto para RFC
        dynamic_rois['RFC'] = [base_row_y, RFC_X, 45, RFC_WIDTH]

    # Procesar IMSS (si existe) - INDEPENDIENTE DE RFC
    if not imss_matches.empty:
        dynamic_rois['IMSS'] = [base_row_y + 3, IMSS_X, 33, IMSS_WIDTH]
    else:
        # Fallback: posición por defecto para IMSS
        dynamic_rois['IMSS'] = [base_row_y + 3, IMSS_X, 33, IMSS_WIDTH]
        
    # Procesar CURP (si existe) - INDEPENDIENTE DE LOS OTROS
    if not curp_matches.empty:
        key_row = curp_matches.iloc[0]
        # En lugar de usar base_row_y, usamos la posición exacta de su etiqueta
        y_curp = key_row['top'] + key_row['height'] + 2 
        # Intentar encontrar el valor de CURP a la derecha o debajo de la etiqueta
        y_search_start = key_row['top'] + key_row['height'] + 2
        value_candidates = data_df[
            (data_df['top'] >= y_search_start - 6) &
            (data_df['top'] <= y_search_start + 40) &
            (data_df['left'] >= key_row['left']) &
            (data_df['left'] <= key_row['left'] + 600)
        ].sort_values(by='left').head(1)

        if not value_candidates.empty:
            x_curp = int(value_candidates.iloc[0]['left']) - 5
            y_curp = int(value_candidates.iloc[0]['top']) - 6
        else:
            # Si no se encuentra a la derecha, colocar ROI justo a la derecha de la etiqueta
            x_curp = int(key_row['left'] + key_row['width'] + 5)

        # Bajamos el alto de 33 a 28 para que NO toque el recuadro de abajo
        dynamic_rois['CURP'] = [y_curp, x_curp, 28, CURP_WIDTH]
    else:
        # Fallback: posición por defecto para CURP
        dynamic_rois['CURP'] = [base_row_y, CURP_X, 33, CURP_WIDTH]

    # 5. Lógica para campos DEBAJO (CÓDIGO, TELÉFONO, CRN, DESDE, HASTA, etc.)
    for field_name, keywords in simple_fields_below.items():
        if field_name not in dynamic_rois:
            regex_pattern = '|'.join([re.escape(kw) for kw in keywords])
            matches = data_df[data_df['text'].str.contains(regex_pattern, case=False, regex=True)]
            
            if not matches.empty:
                key_row = matches.iloc[0]
                
                # --- AJUSTE DE PRECISIÓN ---
                # Buscamos valores que empiecen casi en la misma X que la etiqueta
                # y que estén inmediatamente abajo (máximo 40 pixeles de distancia)
                y_search_start = key_row['top'] + key_row['height']
                
                value_candidates = data_df[
                    (data_df['top'] >= y_search_start - 2) & 
                    (data_df['top'] <= y_search_start + 40) &
                    (data_df['left'] >= key_row['left'] - 15) & # Margen pequeño a la izquierda
                    (data_df['left'] <= key_row['left'] + 60)   # Margen pequeño a la derecha
                ].sort_values(by='top').head(1)

                # Valores por defecto (si no encuentra candidato claro)
                x_start = key_row['left']
                y_start = y_search_start + 2
                h_roi = 35 # Altura estándar para una línea de texto
                w_roi = 200

                if not value_candidates.empty:
                    # Si encontramos el texto real, nos pegamos a su posición exacta
                    y_start = value_candidates.iloc[0]['top'] - 5
                    x_start = value_candidates.iloc[0]['left'] - 5

                # Ajustes específicos
                if field_name == 'CODIGO':
                    w_roi = 150
                    h_roi = 40
                    x_start = 700 if value_candidates.empty else value_candidates.iloc[0]['left'] - 10
                    
                    # 🚨 Fallback extra si no lo encuentra directamente
                    if value_candidates.empty:
                        # Buscar si tenemos el ROI de NOMBRE o NUM para apoyarnos
                        if 'NOMBRE_COMPLETO_RAW' in dynamic_rois:
                            nombre_y, nombre_x, nombre_h, nombre_w = dynamic_rois['NOMBRE_COMPLETO_RAW']
                            y_start = nombre_y
                            x_start = nombre_x + nombre_w + 130  # 130px a la derecha de nombre
                        
                        elif 'NUM' in dynamic_rois:
                            num_y, num_x, num_h, num_w = dynamic_rois['NUM']
                            y_start = num_y + 5   # misma altura aprox
                            x_start = num_x + 30  # 30px a la derecha de num
                
                elif field_name == 'TELEFONO':
                    w_roi = 200
                    x_start = 700 if value_candidates.empty else value_candidates.iloc[0]['left'] - 10
                    
                elif field_name == 'MATERIA':
                    w_roi = 660
                    h_roi = 35
                    if value_candidates.empty:
                        y_start = key_row['top'] + key_row['height'] + 2 # Pegado a la etiqueta
                    
                
                elif field_name == 'CRN':
                    w_roi = 170
                    h_roi = 35
                    x_start = 150
                    if value_candidates.empty:
                        # Busca cerca de DESDE/HASTA si existen 
                        if 'DESDE' in dynamic_rois:
                            desde_y, desde_x, desde_h, desde_w = dynamic_rois['DESDE']
                            y_start = desde_y
                            x_start = desde_x - 300  # 300px a la izquierda de DESDE
                    
                elif field_name == 'HRS_TOTALES':
                    w_roi = 150
                    h_roi = 35
                    x_start = 330
                    if value_candidates.empty:
                        #busca cerca de Desde/Hasta si existen
                        if 'DESDE' in dynamic_rois:
                            desde_y, desde_x, desde_h, desde_w = dynamic_rois['DESDE']
                            y_start = desde_y
                            x_start = desde_x - 250  # 150px a la izquierda de DESDE
                
                elif field_name == 'DESDE' or field_name == 'HASTA':
                    w_roi = 200  # Un poco más ancho por si la fecha es larga
                    h_roi = 40

                dynamic_rois[field_name] = [y_start, x_start, h_roi, w_roi]
                print(f"    >> ROI final para {field_name}: y={int(y_start)}, x={int(x_start)}, h={h_roi}, w={w_roi}")
                
    # ============ BÚSQUEDA ALTERNATIVA: Si DESDE/HASTA NO se encontraron, buscar por patrón de fecha ============
    if 'DESDE' not in dynamic_rois or 'HASTA' not in dynamic_rois:
        # Patrones más flexibles para detectar fechas
        # Permite espacios, múltiples separadores, formatos variados
        date_patterns = [
            r'\d{1,2}\s*[/\-\.]\s*\d{1,2}\s*[/\-\.]\s*\d{2,4}',  # Flexible: 01 / 12 / 2023 o 1-1-2023
            r'\d{4}[/\-]\d{1,2}[/\-]\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}/\d{1,2}/\d{1,2}',  # 01/12/23
        ]
        
        date_matches = None
        for pattern in date_patterns:
            date_matches = data_df[data_df['text'].str.contains(pattern, regex=True, na=False)]
            if not date_matches.empty:
                print(f"  [DEBUG] Detectadas {len(date_matches)} fechas potenciales con patrón: {pattern}")
                break
        
        # Si aún no se encuentran fechas por patrón, buscar por proximidad a la etiqueta "DESDE"
        if date_matches is None or date_matches.empty:
            print(f"  [DEBUG] No se encontraron fechas por patrón de OCR, buscando por etiqueta flexible...")
            # Buscar "DESDE" en cualquier formato (D, DESDE, DESDE:, etc.)
            desde_etiqueta = data_df[data_df['text'].str.upper().str.contains(r'^D[ESDE]*|DESDE', regex=True, na=False)]
            
            if not desde_etiqueta.empty:
                print(f"  [DEBUG] Etiqueta DESDE encontrada como fallback")
                first_desde = desde_etiqueta.iloc[0]
                y_date = int(first_desde['top']) + int(first_desde['height']) + 5
                x_date = int(first_desde['left'])
                
                # Crear ROIs relativos a la etiqueta encontrada
                if 'DESDE' not in dynamic_rois:
                    dynamic_rois['DESDE'] = [y_date, x_date, 45, 150]
                    print(f"  [DEBUG] DESDE asignado por etiqueta flexible")
                
                if 'HASTA' not in dynamic_rois:
                    # HASTA está debajo o a la derecha de DESDE
                    dynamic_rois['HASTA'] = [y_date + 50, x_date, 45, 150]
                    print(f"  [DEBUG] HASTA asignado por etiqueta flexible")
        else:
            print(f"  [DEBUG] Detectadas {len(date_matches)} fechas potenciales:")
            for idx, row in date_matches.iterrows():
                print(f"    - Fecha en ({int(row['left'])}, {int(row['top'])}): '{row['text']}'")
            
            # Asignar las dos primeras fechas encontradas a DESDE y HASTA
            if 'DESDE' not in dynamic_rois and len(date_matches) >= 1:
                first_date_row = date_matches.iloc[0]
                y_date = int(first_date_row['top']) - 5
                x_date = int(first_date_row['left']) - 10
                dynamic_rois['DESDE'] = [y_date, x_date, 45, 150]
                print(f"  [DEBUG] DESDE asignado automáticamente por patrón de fecha")
            
            if 'HASTA' not in dynamic_rois and len(date_matches) >= 2:
                second_date_row = date_matches.iloc[1]
                y_date = int(second_date_row['top']) - 5
                x_date = int(second_date_row['left']) - 10
                dynamic_rois['HASTA'] = [y_date, x_date, 45, 150]
                print(f"  [DEBUG] HASTA asignado automáticamente por patrón de fecha")
                
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