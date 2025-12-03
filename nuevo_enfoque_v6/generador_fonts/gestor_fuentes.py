#!/usr/bin/env python3
"""
Gestor de Fuentes para Modelo OCR
=================================
Descarga fuentes Open Source y verifica fuentes propietarias.
"""

import os
import sys
import zipfile
import io
import shutil
import urllib.request
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
FONTS_DIR = BASE_DIR / 'fonts'

# Fuentes propietarias a verificar (no se pueden descargar legalmente por script)
PROPIETARY_FONTS = {
    'Arial': ['Arial.ttf', 'Arial_bold.ttf', 'Arial_Italic.ttf', 'Arial_Bold_Italic.ttf'],
    'Times New Roman': ['Times.ttf', 'Times_bold.ttf', 'Times_Italic.ttf', 'Times_Bold_Italic.ttf'],
    'Calibri': ['Calibri.ttf', 'Calibri_bold.ttf', 'Calibri_Italic.ttf', 'Calibri_Bold_Italic.ttf']
}

# Fuentes Open Source a descargar (Google Webfonts Helper API - Más estable)
OPEN_SOURCE_FONTS = {
    'Courier Prime': 'https://gwfh.mranftl.com/api/fonts/courier-prime?download=zip&subsets=latin&variants=regular,700,italic,700italic',
    'Roboto Mono': 'https://gwfh.mranftl.com/api/fonts/roboto-mono?download=zip&subsets=latin&variants=regular,700,italic,700italic',
    'Tinos': 'https://gwfh.mranftl.com/api/fonts/tinos?download=zip&subsets=latin&variants=regular,700,italic,700italic',
    'EB Garamond': 'https://gwfh.mranftl.com/api/fonts/eb-garamond?download=zip&subsets=latin&variants=regular,700,italic,700italic',
    'Arimo': 'https://gwfh.mranftl.com/api/fonts/arimo?download=zip&subsets=latin&variants=regular,700,italic,700italic',
    'Open Sans': 'https://gwfh.mranftl.com/api/fonts/open-sans?download=zip&subsets=latin&variants=regular,700,italic,700italic'
}

def verificar_fuentes_propietarias():
    """Verifica si existen las fuentes propietarias y advierte sobre las faltantes."""
    print(f"\n{'='*60}")
    print("AUDITORÍA DE FUENTES PROPIETARIAS")
    print(f"{'='*60}")
    
    faltantes_total = 0
    
    for familia, archivos in PROPIETARY_FONTS.items():
        print(f"\nVerificando familia: {familia}")
        for archivo in archivos:
            ruta = FONTS_DIR / archivo
            # Intentar buscar insensible a mayúsculas/minúsculas
            existe = False
            if ruta.exists():
                existe = True
            else:
                # Búsqueda manual en el directorio para ignorar case
                for f in os.listdir(FONTS_DIR):
                    if f.lower() == archivo.lower():
                        existe = True
                        break
            
            if existe:
                print(f"  [OK] {archivo}")
            else:
                print(f"  [FALTA] {archivo}")
                faltantes_total += 1
    
    if faltantes_total > 0:
        print(f"\n[ADVERTENCIA] Faltan {faltantes_total} archivos de fuentes propietarias.")
        print("   Se recomienda copiarlas manualmente desde C:\\Windows\\Fonts o /usr/share/fonts")
        print("   especialmente las variantes 'Italic' para mejorar el entrenamiento.")
    else:
        print("\n[OK] Todas las fuentes propietarias base están presentes.")

def descargar_fuentes_opensource():
    """Descarga e instala fuentes desde Google Fonts."""
    print(f"\n{'='*60}")
    print("DESCARGA DE FUENTES OPEN SOURCE")
    print(f"{'='*60}")
    
    if not FONTS_DIR.exists():
        FONTS_DIR.mkdir(parents=True)
        print(f"Creado directorio: {FONTS_DIR}")

    for familia, url in OPEN_SOURCE_FONTS.items():
        print(f"\nProcesando: {familia}...")
        try:
            # Descargar ZIP
            print(f"  Descargando desde GWFH API...")
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
            
            # Procesar ZIP en memoria
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                # Filtrar solo archivos .ttf (y static/ si existen)
                # GWFH suele devolver archivos como 'courier-prime-v11-latin-regular.ttf'
                archivos_ttf = [f for f in z.namelist() if f.lower().endswith('.ttf')]
                
                count = 0
                for archivo in archivos_ttf:
                    filename = os.path.basename(archivo)
                    
                    # Extraer
                    source = z.open(archivo)
                    target_path = FONTS_DIR / filename
                    
                    with open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    
                    print(f"  [INSTALADA] {filename}")
                    count += 1
                
                if count == 0:
                    print("  [AVISO] No se encontraron archivos .ttf en el ZIP descargado.")
                    
        except Exception as e:
            print(f"  [ERROR] Error descargando {familia}: {e}")

def main():
    print(f"Directorio de fuentes: {FONTS_DIR}")
    verificar_fuentes_propietarias()
    descargar_fuentes_opensource()
    
    print(f"\n{'='*60}")
    print("PROCESO COMPLETADO")
    print(f"Total de fuentes en {FONTS_DIR}: {len(list(FONTS_DIR.glob('*.ttf')))}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
