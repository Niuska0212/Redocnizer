#!/usr/bin/env python3
"""
Generador de Imágenes REALISTAS para Dataset OCR (OCR Synthetic Data Generator)

Combina la generación de palabras/datos realistas con la creación de imágenes PNG.
"""
import random
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import string
import argparse

# Importar Pillow para generar imágenes
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: La librería Pillow (PIL) no está instalada.")
    print("Por favor, instálala con: pip install Pillow")
    exit()

# ==================== DATOS LINGÜÍSTICOS REALES (Mismos del Script 1) ====================

# Palabras comunes en español (reducidas para concisión)
PALABRAS_ESPANOL = [
    "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "por", 
    "con", "su", "para", "como", "estar", "tener", "le", "lo", "año", "tiempo", 
    "día", "casa", "vida", "mundo", "parte", "trabajo", "persona", "problema", 
    "vez", "grupo", "forma", "mujer", "hombre", "nombre", "lugar", "nivel", 
    "mes", "hora", "mano", "momento", "agua", "sistema", "información", "código"
]

# Palabras comunes en inglés (reducidas)
PALABRAS_INGLES = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my"
]

# Nombres propios comunes y apellidos
NOMBRES_PROPIOS = [
    "Juan", "José", "Carlos", "María", "Ana", "Carmen", "Laura", "García", 
    "Rodríguez", "González", "Fernández", "López", "Smith", "Johnson", "Williams"
]

# Ciudades y países
LUGARES = [
    "Madrid", "Barcelona", "México", "Argentina", "España", "London", "Paris"
]

# Frecuencias de letras en español (simplificadas)
FRECUENCIAS_ESPANOL = {
    'e': 13.68, 'a': 12.53, 'o': 8.68, 's': 7.98, 'n': 6.71, 'r': 6.87,
    'i': 6.25, 'l': 4.97, 'd': 5.86, 't': 4.63, 'c': 4.68, 'u': 3.93,
    'm': 3.15, 'p': 2.51, 'b': 1.42, 'g': 1.01, 'v': 0.90, 'y': 0.90
}

# Bigramas comunes
BIGRAMAS_COMUNES = [
    "de", "es", "en", "el", "la", "os", "as", "ar", "er", "or", "al", "an"
]

PREFIJOS = ["des", "pre", "re", "in", "sub"]
SUFIJOS = ["ción", "dad", "mente", "ismo", "ista"]

# ==================== FUNCIONES GENERADORAS (Mismas del Script 1) ====================

def generar_fecha_realista() -> str:
    formato = random.choice(["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y", "%d/%m/%y"])
    inicio = datetime(1950, 1, 1)
    fin = datetime(2030, 12, 31)
    dias = (fin - inicio).days
    fecha_random = inicio + timedelta(days=random.randint(0, dias))
    return fecha_random.strftime(formato)

def generar_numero_realista() -> str:
    tipo = random.choice(['entero_corto', 'decimal', 'telefono', 'porcentaje', 'moneda'])
    if tipo == 'entero_corto':
        return str(random.randint(1, 9999))
    elif tipo == 'decimal':
        # Uso de coma o punto como separador decimal
        sep = random.choice(['.', ','])
        miles_sep = ',' if sep == '.' else '.'
        num = random.uniform(0, 9999)
        # Formato de miles y decimales
        return f"{num:,.2f}".replace(",", "_TEMP_").replace(".", sep).replace("_TEMP_", miles_sep)
    elif tipo == 'telefono':
        return f"+{random.randint(1,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
    elif tipo == 'porcentaje':
        return f"{random.uniform(0, 100):.1f}%"
    elif tipo == 'moneda':
        simbolo = random.choice(["$", "€", "USD", "EUR"])
        return f"{simbolo}{random.uniform(0, 9999):.2f}"
    return ""

def generar_palabra_con_ngramas(longitud: int) -> str:
    if longitud < 2: return random.choice(list(FRECUENCIAS_ESPANOL.keys()))
    palabra = random.choice(BIGRAMAS_COMUNES)
    letras = list(FRECUENCIAS_ESPANOL.keys())
    pesos = list(FRECUENCIAS_ESPANOL.values())
    while len(palabra) < longitud:
        letra = random.choices(letras, weights=pesos, k=1)[0]
        palabra += letra
    return palabra[:longitud]

def generar_palabra_con_afijos() -> str:
    base = random.choice(PALABRAS_ESPANOL[:20])
    if random.random() > 0.5:
        base = random.choice(PREFIJOS) + base
    if random.random() > 0.5:
        base = base + random.choice(SUFIJOS)
    return base

def generar_codigo() -> str:
    tipo = random.choice(['alfanumerico', 'guiones', 'hash'])
    if tipo == 'alfanumerico':
        letras = ''.join(random.choices(string.ascii_uppercase, k=3))
        numeros = ''.join(random.choices(string.digits, k=3))
        return letras + numeros
    elif tipo == 'guiones':
        p1 = ''.join(random.choices(string.ascii_uppercase, k=3))
        p2 = ''.join(random.choices(string.digits, k=3))
        return f"{p1}-{p2}"
    elif tipo == 'hash':
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Generador Principal adaptado para devolver la lista de palabras
def generar_dataset_realista(cantidad: int = 1000, distribucion: Dict[str, float] = None, seed: int = None) -> List[str]:
    if seed is not None:
        random.seed(seed)
    
    if distribucion is None:
        distribucion = {
            'palabras_espanol': 0.35, 
            'palabras_ingles': 0.05, 
            'nombres_propios': 0.15, 
            'fechas': 0.15, 
            'numeros': 0.10, 
            'lugares': 0.05, 
            'palabras_ngramas': 0.05, 
            'palabras_afijos': 0.05, 
            'codigos': 0.05,
        }
    
    dataset = []
    
    for tipo, porcentaje in distribucion.items():
        cant_tipo = int(cantidad * porcentaje)
        
        for _ in range(cant_tipo):
            if tipo == 'palabras_espanol':
                item = random.choice(PALABRAS_ESPANOL)
            elif tipo == 'palabras_ingles':
                item = random.choice(PALABRAS_INGLES)
            elif tipo == 'nombres_propios':
                item = random.choice(NOMBRES_PROPIOS)
            elif tipo == 'fechas':
                item = generar_fecha_realista()
            elif tipo == 'numeros':
                item = generar_numero_realista()
            elif tipo == 'lugares':
                item = random.choice(LUGARES)
            elif tipo == 'palabras_ngramas':
                longitud = random.randint(4, 10)
                item = generar_palabra_con_ngramas(longitud)
            elif tipo == 'palabras_afijos':
                item = generar_palabra_con_afijos()
            elif tipo == 'codigos':
                item = generar_codigo()
            else:
                item = random.choice(PALABRAS_ESPANOL)
            
            dataset.append(item)
    
    random.shuffle(dataset)
    return dataset

# ==================== CONFIGURACIÓN DE RUTAS Y GENERACIÓN DE IMÁGENES ====================

def main():
    """Función principal para generar datos realistas e imágenes OCR."""
    
    # -------------------------------
    # Configuración de rutas (Adaptadas a tu estructura)
    # -------------------------------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Carpeta de salida para las imágenes (dataset_palabras)
    output_dir = Path(BASE_DIR).parent / "data" / "data" / "dataset_palabras"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Carpeta de fuentes (fonts)
    font_dir = Path(BASE_DIR).parent / "fonts"
    
    # Detectar automáticamente todas las fuentes .ttf
    font_paths = [str(f) for f in font_dir.glob("*.ttf")]

    # Verifica qué fuentes se encontraron
    print("="*60)
    print("📁 Configuración de Rutas:")
    print(f"   • Carpeta de Fuentes: {font_dir}")
    print(f"   • Carpeta de Salida: {output_dir}")
    print(f"   • Fuentes encontradas: {len(font_paths)}")
    print("="*60)

    if not font_paths:
        print("Error: No se encontraron fuentes .ttf en la carpeta 'fonts'.")
        print("Asegúrate de tener fuentes TrueType en la ruta especificada.")
        return

    # Tamaños de fuente y parámetros de imagen
    font_sizes = [24, 28, 32, 36]
    labels_file_path = output_dir / "labels_realistas.txt"
    NUM_TOTAL_ITEMS = 5000 # Cantidad total a generar (ajustar)
    
    # Generar el dataset de texto realista
    dataset_texto = generar_dataset_realista(cantidad=NUM_TOTAL_ITEMS, seed=42)
    print(f"✅ Dataset de texto realista generado: {len(dataset_texto)} ítems.")
    print("="*60)

    # -------------------------------
    # Generar imágenes
    # -------------------------------
    with open(labels_file_path, "w", encoding="utf-8") as labels_file: # Usamos 'w' para sobrescribir y empezar desde cero
        
        # Contador inicial
        count = 0 
        
        for item in dataset_texto:
            # 1. Seleccionar estilos aleatorios
            font_path = random.choice(font_paths)
            font_size = random.choice(font_sizes)
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                # Esto es un error recuperable, si una fuente falla, la ignoramos.
                print(f"Advertencia: No se pudo cargar la fuente en {font_path}. Saltando.")
                continue

            # 2. Calcular tamaño del texto (usando PIL.ImageDraw.Draw.textbbox)
            temp_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(temp_img)
            # Asegurar que el texto se mide correctamente
            text_bbox = draw.textbbox((0, 0), item, font=font)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

            # 3. Crear imagen
            padding = 10
            img_size = (text_width + padding * 2, text_height + padding * 2)
            
            # Color de fondo: Blanco a gris claro aleatorio
            bg_val = random.randint(230, 255)
            bg_color = (bg_val, bg_val, bg_val)
            
            # Color del texto: Negro a gris oscuro aleatorio
            text_val = random.randint(0, 50)
            text_color = (text_val, text_val, text_val)
            
            img = Image.new('RGB', img_size, color=bg_color)
            draw = ImageDraw.Draw(img)

            # 4. Dibujar texto centrado
            x = padding - text_bbox[0] # Ajuste de inicio para el padding
            y = padding - text_bbox[1]
            draw.text((x, y), item, font=font, fill=text_color)
            
            # 5. Guardar
            filename = f"{count:05d}.png"
            save_path = output_dir / filename
            img.save(save_path)
            
            # 6. Escribir etiqueta
            labels_file.write(f"{filename},{item}\n")
            
            if count % 100 == 0:
                print(f"   Generando imagen {count} de {NUM_TOTAL_ITEMS}...")
            
            count += 1
            
    print("="*60)
    print(f"🎉 Generación de dataset de {count} imágenes completada exitosamente.")
    print(f"📂 Archivos guardados en: {output_dir}")
    print(f"🏷️ Etiquetas guardadas en: {labels_file_path}")
    print("="*60)


if __name__ == "__main__":
    main()