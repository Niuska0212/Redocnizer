# document_extractor.py

import cv2
import os
import pandas as pd
import numpy as np
from crnn_inference import load_inference_model, decode_batch_predictions
from preprocessing import prepare_roi_for_ocr # Importamos la función de preprocesamiento

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ruta a tu carpeta con los 4000 archivos JPG (ajusta si es necesario)
RUTA_IMAGENES = os.path.join(BASE_DIR, "..", "data", "contratos", "imagenes_jpg")
RUTA_SALIDA_CSV = os.path.join(BASE_DIR, "datos_extraidos_contratos.csv")

# =========================================================================
# === DEFINICIÓN DE LAS REGIONES DE INTERÉS (ROI) - ¡ACTUALIZA ESTO! ======
# =========================================================================
# Formato: 'nombre_campo': [Y_INICIO, X_INICIO, ALTURA, ANCHO] (Coordenadas en píxeles)
# Las coordenadas son relativas a la esquina superior izquierda (0,0).

ROIS_CONTRATO = {
    # Estos son placeholders basados en la imagen, DEBES AJUSTARLOS
    'PATERNO': [210, 115, 30, 195], 
    'MATERNO': [210, 315, 30, 195],
    'NOMBRE_S': [210, 520, 30, 305],
    'NUM': [180, 700, 30, 150],
    'CODIGO': [180, 850, 30, 150],
    'RFC': [260, 115, 30, 195],
    'CURP': [260, 520, 30, 305],
    'DOMICILIO': [295, 320, 30, 400],
    'TELEFONO': [295, 800, 30, 200],
    'DEPENDENCIA': [470, 160, 30, 500],
    'CRN': [440, 130, 30, 150],
    'HRS_TOTALES': [440, 290, 30, 170],
    'DESDE': [440, 470, 30, 150],
    'HASTA': [440, 620, 30, 150],
}

# =========================================================================

def extract_data_from_image(image_path, modelo_inferencia, index_to_char, output_sequence_length):
    """
    Carga la imagen, aplica la lógica de ROI, recorta, preprocesa y ejecuta el CRNN.
    """
    extracted_data = {'Archivo': os.path.basename(image_path)}
    
    # Cargar la imagen completa en escala de grises
    img_full = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img_full is None:
        return extracted_data, f"Error: No se pudo cargar la imagen {os.path.basename(image_path)}"

    try:
        # 1. Iterar sobre las ROI
        for field_name, (y, x, h, w) in ROIS_CONTRATO.items():
            
            # 2. Recortar la región de interés: [Y_inicio:Y_fin, X_inicio:X_fin]
            roi_image = img_full[y : y + h, x : x + w]
            
            if roi_image.size == 0:
                extracted_data[field_name] = ""
                continue

            # 3. Preprocesar la imagen recortada (usa la función de preprocessing.py)
            X_input = prepare_roi_for_ocr(roi_image)

            # 4. Predicción del CRNN
            # El input ya está en la forma (1, H, W, 1)
            y_pred_probs = modelo_inferencia.predict(X_input, verbose=0)
            
            # 5. Decodificación
            pred_words = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
            
            # Guardar el resultado
            extracted_data[field_name] = pred_words[0] if pred_words else ""
            
        return extracted_data, None

    except Exception as e:
        return extracted_data, f"Error inesperado en {os.path.basename(image_path)}: {e}"


def main():
    # Cargar el modelo CRNN
    modelo_inferencia, index_to_char, output_sequence_length = load_inference_model()
    if modelo_inferencia is None:
        return

    # Preparar el proceso de extracción
    all_files = [f for f in os.listdir(RUTA_IMAGENES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    all_data = []

    print(f"\nIniciando extracción de datos de {len(all_files)} documentos en: {RUTA_IMAGENES}")

    for i, file_name in enumerate(all_files):
        image_path = os.path.join(RUTA_IMAGENES, file_name)
        
        data, error = extract_data_from_image(
            image_path, 
            modelo_inferencia, 
            index_to_char, 
            output_sequence_length
        )

        if data:
            all_data.append(data)
        
        if error:
            print(f"Error o advertencia en {file_name}: {error}")

        if (i + 1) % 100 == 0 or (i + 1) == len(all_files):
            print(f"-> {i + 1}/{len(all_files)} documentos procesados.")

    # Guardar los resultados
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(RUTA_SALIDA_CSV, index=False, encoding='utf-8')
        print(f"\n✅ Extracción completada. Datos guardados en: {RUTA_SALIDA_CSV}")
    else:
        print("\n❌ No se extrajeron datos. Revisa las rutas, el modelo CRNN y las ROIs.")


if __name__ == "__main__":
    main()