"""Debug script para ver exactamente qué texto detecta Tesseract"""
import cv2
import pytesseract
import pandas as pd
import numpy as np
import os
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Tomar la primera imagen como ejemplo
RUTA_IMAGENES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "data", "contratos", "imagenes_jpg")
image_path = os.path.join(RUTA_IMAGENES, os.listdir(RUTA_IMAGENES)[0])

# Cargar imagen
img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
H, W = img.shape[:2]

# Pre-procesamiento
std_dev = np.std(img)
THRESHOLD_STD = 43

if std_dev < THRESHOLD_STD:
    img_bin = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
else:
    img_bin = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )

# Detectar todo con PSM 3
img_pil = Image.fromarray(img_bin)
data_df = pytesseract.image_to_data(
    img_pil,
    output_type=pytesseract.Output.DATAFRAME,
    config='--psm 3'
)

# Mostrar TODOS los textos detectados
print(f"\n{'='*80}")
print(f"IMAGEN: {os.path.basename(image_path)}")
print(f"{'='*80}\n")
print("Todas las palabras detectadas por Tesseract (PSM 3):\n")
print(data_df[['left', 'top', 'width', 'height', 'text', 'conf']].to_string())

# Buscar específicamente DESDE/HASTA
print(f"\n{'='*80}")
print("BÚSQUEDA DE CAMPOS DE INTERÉS:")
print(f"{'='*80}\n")

for keyword in ['DESDE', 'HASTA', 'NOMBRE', 'RFC', 'CURP', 'IMSS', 'CÓDIGO', 'TELÉFONO', 'CRN', 'NOMBRE DE LA MATERIA / CURSO', 'HRS. TOTALES CURSO', 'DEPTO. DE MATEMATICAS']:
    matches = data_df[data_df['text'].str.contains(keyword, case=False, na=False)]
    if not matches.empty:
        print(f"\n✓ '{keyword}' encontrado:")
        print(matches[['left', 'top', 'text']].to_string())
    else:
        print(f"\n✗ '{keyword}' NO encontrado")

print(f"\n{'='*80}\n")
