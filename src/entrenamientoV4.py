import os
import numpy as np
import cv2
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Lambda, Input
from tensorflow.keras import backend as K
import joblib
import re
import fitz  # PyMuPDF
import logging
from collections import defaultdict

# Configuración del logging para un mejor seguimiento
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==============================================================================
# CONFIGURACIÓN Y PARÁMETROS GLOBALES
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_modelos = os.path.join(BASE_DIR, "..", "models")
os.makedirs(ruta_modelos, exist_ok=True)

img_height = 32
img_width = 256
output_sequence_length = img_width // 8

# ==============================================================================
# FUNCIONES DE AYUDA (EXTRAÍDAS DE LA VERSIÓN 3)
# ==============================================================================
def ctc_loss_lambda_func(args):
    """Función de pérdida CTC (necesaria para cargar el modelo)."""
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    """Decodifica las predicciones del modelo usando CTC."""
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    decoded_words = []
    for seq in K.get_value(results):
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def preprocess_for_ocr(image):
    """
    Preprocesa una imagen de texto para el modelo CRNN.
    
    Ajusta el tamaño y la forma de la imagen para que sea compatible
    con la entrada del modelo entrenado.
    """
    if image is None:
        return None
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image, (img_width, img_height), interpolation=cv2.INTER_AREA)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    image = np.expand_dims(image, axis=-1)
    image = np.expand_dims(image, axis=0)
    image = image.astype(np.float32) / 255.0
    return image

# ==============================================================================
# FUNCIÓN DE PROCESAMIENTO DE DOCUMENTOS
# ==============================================================================
def procesar_contrato(ruta_contrato, modelo_ocr, vocabulario):
    """
    Procesa un documento de contrato completo (PDF o JPG) y extrae datos clave.
    """
    logging.info(f"Procesando el contrato: {os.path.basename(ruta_contrato)}")
    
    # 1. Conversión de PDF/JPG a imágenes
    imagenes_paginas = []
    if ruta_contrato.lower().endswith('.pdf'):
        try:
            doc = fitz.open(ruta_contrato)
            for pagina_num in range(len(doc)):
                pagina = doc.load_page(pagina_num)
                pixmap = pagina.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                imagenes_paginas.append(img)
        except Exception as e:
            logging.error(f"Error al convertir PDF a imagen: {e}")
            return {}
    else:
        imagenes_paginas = [cv2.imread(ruta_contrato)]
    
    datos_extraidos = defaultdict(lambda: 'no_encontrado')
    
    # Expresiones regulares para la extracción de datos con patrones conocidos
    # Se usan para capturar valores que no tienen una etiqueta específica cerca
    patrones = {
        'rfc': r'\b([A-ZÑ&]{3,4}\d{6}[A-Z\d]{3})\b',
        'curp': r'\b([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2})\b',
        'n_imss': r'\b(\d{11})\b',
        'crn': r'\b(\d{5})\b',
    }

    # Definir los campos que quieres extraer con sus posibles etiquetas
    campos_a_extraer = {
        'numero_contrato': ['NÚM.', 'NUM.'],
        'apellido_paterno': ['PATERNO'],
        'apellido_materno': ['MATERNO'],
        'nombre': ['NOMBRE(S)'],
        'codigo': ['CÓDIGO', 'CÓDIGO P', 'CODIGO P'],
        'categoria': ['CATEGORIA'],
        'nombre_materia': ['NOMBRE DE LA MATERIA/CURSO'],
        'fecha_inicio': ['DESDE'],
        'fecha_fin': ['HASTA'],
        'dependencia': ['DEPENDENCIA DE ADSCRIPCIÓN'],
        'lugar_nacimiento': ['LUGAR DE NACIMIENTO'],
        'escolaridad': ['ESCOLARIDAD'],
        'domicilio': ['DOMICILIO'],
        'telefono': ['TELÉFONO'],
    }

    for i, img in enumerate(imagenes_paginas):
        if img is None:
            continue
            
        # 2. Detección y Extracción de texto
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Ordenar los contornos de arriba a abajo y de izquierda a derecha
        sorted_contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
        
        texto_de_pagina = ""
        texto_por_linea = []

        # Paso 1: Reconocer el texto en cada recorte y almacenarlo
        for contour in sorted_contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < 15 or h < 8 or w > img.shape[1] * 0.9 or h > img.shape[0] * 0.9:
                continue
            
            recorte = img[y:y+h, x:x+w]
            prepro_recorte = preprocess_for_ocr(recorte)
            if prepro_recorte is None:
                continue

            try:
                pred_probs = modelo_ocr.predict(prepro_recorte, verbose=0)
                pred_words = decode_batch_predictions(pred_probs, vocabulario['index_to_char'], vocabulario['output_sequence_length'])
                
                if pred_words:
                    texto_por_linea.append(" ".join(pred_words))
                
            except Exception as e:
                logging.error(f"Error al procesar el recorte: {e}")
        
        texto_de_pagina = "\n".join(texto_por_linea)
        
        # Paso 2: Extraer datos del texto de la página completa
        for nombre_campo, palabras_clave in campos_a_extraer.items():
            if datos_extraidos[nombre_campo] == 'no_encontrado':
                for palabra_clave in palabras_clave:
                    # Búsqueda flexible para la palabra clave y el valor en la misma línea o siguiente
                    pattern = f'{re.escape(palabra_clave)}[^\n]*\s*([^\s]+)'
                    match = re.search(pattern, texto_de_pagina, re.IGNORECASE | re.DOTALL)
                    if match:
                        datos_extraidos[nombre_campo] = match.group(1).strip()
                        logging.info(f"  {nombre_campo} extraído: {datos_extraidos[nombre_campo]}")
                        break
        
        # Buscar valores con patrones de regex sin una palabra clave
        for key, pattern in patrones.items():
            if datos_extraidos[key] == 'no_encontrado':
                match = re.search(pattern, texto_de_pagina)
                if match:
                    datos_extraidos[key] = match.group(1).strip()
                    logging.info(f"  {key} extraído por regex: {datos_extraidos[key]}")

        # Si ya se encontraron los campos principales, salimos del bucle
        campos_principales = ['numero_contrato', 'codigo', 'rfc', 'curp']
        if all(datos_extraidos[c] != 'no_encontrado' for c in campos_principales):
            break
            
    return dict(datos_extraidos)

# ==============================================================================
# FUNCIÓN PRINCIPAL DE EJECUCIÓN
# ==============================================================================
def main():
    # 1. Cargar el modelo de OCR ya entrenado
    ruta_modelo = os.path.join(ruta_modelos, "keras_cnn_lstm_v3_ctc.h5")
    ruta_vocabulario = os.path.join(ruta_modelos, "vocabulario_v3.pkl")
    
    if not os.path.exists(ruta_modelo) or not os.path.exists(ruta_vocabulario):
        logging.error("No se encontró el modelo o el vocabulario. Por favor, asegúrate de haber entrenado el modelo V3 y guardado los archivos 'keras_cnn_lstm_v3_ctc.h5' y 'vocabulario_v3.pkl' en la carpeta 'models'.")
        return

    try:
        modelo_ocr = load_model(ruta_modelo, custom_objects={'ctc_loss': ctc_loss_lambda_func})
        vocabulario = joblib.load(ruta_vocabulario)
        logging.info("Modelo de OCR V4 cargado exitosamente.")
    except Exception as e:
        logging.error(f"Error al cargar el modelo o el vocabulario: {e}")
        return

    # 2. Procesar los documentos de contrato
    ruta_base_contratos = 'N:\\Proyecto-modular\\data\\data\\contratos'
    carpetas_contratos = ['2024A', '2024B']
    
    todos_los_datos = []
    
    for carpeta in carpetas_contratos:
        ruta_completa_carpeta = os.path.join(ruta_base_contratos, carpeta)
        if not os.path.exists(ruta_completa_carpeta):
            logging.warning(f"La carpeta '{ruta_completa_carpeta}' no existe. Saltando.")
            continue

        logging.info(f"--- Procesando carpeta: {carpeta} ---")
        for nombre_archivo in os.listdir(ruta_completa_carpeta):
            ruta_archivo = os.path.join(ruta_completa_carpeta, nombre_archivo)
            
            datos_extraidos = procesar_contrato(ruta_archivo, modelo_ocr, vocabulario)
            
            # Usar los datos para el nombre del archivo final
            numero_contrato = datos_extraidos.get('numero_contrato', 'sin_num')
            codigo = datos_extraidos.get('codigo', 'sin_cod')
            
            datos_extraidos['nombre_archivo'] = nombre_archivo
            datos_extraidos['nuevo_nombre_sugerido'] = f"{numero_contrato}_{codigo}_{nombre_archivo}"
            todos_los_datos.append(datos_extraidos)
            
            logging.info(f"  Archivo procesado. Datos extraídos: {datos_extraidos}")

    # 3. Guardar los resultados en un Excel
    df_resultados = pd.DataFrame(todos_los_datos)
    ruta_excel_salida = os.path.join(ruta_modelos, 'resumen_contratos_V4.xlsx')
    df_resultados.to_excel(ruta_excel_salida, index=False)
    
    logging.info(f"\nProceso completado. Los datos se han guardado en: {ruta_excel_salida}")

if __name__ == "__main__":
    main()