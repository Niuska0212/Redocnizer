from PIL import Image, ImageDraw, ImageFont
import os
import random
from datetime import datetime, timedelta

#scrip completo para generar imagenes segun palabras.txt y generar 500 imagenes con fechas random.

# -------------------------------
# Configuración de rutas
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Archivo de palabras
palabras_file = os.path.join(BASE_DIR, "..", "data", "data", "palabras.txt")
palabras_file = os.path.abspath(palabras_file)

# Carpeta de salida para las imágenes
output_dir = os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")
output_dir = os.path.abspath(output_dir)
os.makedirs(output_dir, exist_ok=True)

# Carpeta de fuentes
font_dir = os.path.join(BASE_DIR, "..", "fonts")
font_dir = os.path.abspath(font_dir)

# Detectar automáticamente todas las fuentes .ttf
font_paths = [os.path.join(font_dir, f) for f in os.listdir(font_dir) if f.lower().endswith(".ttf")]

# Verifica qué fuentes se encontraron
print("Fuentes encontradas:")
for f in font_paths:
    print(f, os.path.exists(f))

# Tamaños de fuente posibles
font_sizes = [24, 28, 32]

# Archivo de etiquetas (existente o nuevo)
labels_file_path = os.path.join(output_dir, "labels.txt")

# -------------------------------
# Leer palabras desde el archivo
# -------------------------------
try:
    with open(palabras_file, "r", encoding="utf-8") as f:
        words_to_generate = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: No se encontró el archivo de texto en {palabras_file}")
    exit()

if not words_to_generate:
    print("El archivo de palabras está vacío.")
    exit()

# -------------------------------
# Función para generar fechas aleatorias
# -------------------------------
def generar_fecha():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2030, 12, 31)
    delta_days = (end_date - start_date).days
    random_days = random.randint(0, delta_days)
    fecha = start_date + timedelta(days=random_days)
    return fecha.strftime("%d/%m/%y")

# Número de fechas a generar
num_fechas = 500   #modificar al gusto
fechas_a_generar = [generar_fecha() for _ in range(num_fechas)]

# -------------------------------
# Generar imágenes de palabras y fechas
# -------------------------------
# Abrimos el archivo en modo 'append' para no sobrescribir etiquetas existentes
with open(labels_file_path, "a", encoding="utf-8") as labels_file:
    # Contador inicial basado en archivos existentes en la carpeta
    existing_files = [f for f in os.listdir(output_dir) if f.endswith(".png")]
    count = len(existing_files)

    # --- Primero las palabras ---
    for word in words_to_generate:
        font_path = random.choice(font_paths)
        font_size = random.choice(font_sizes)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Error: No se pudo cargar la fuente en {font_path}")
            continue

        temp_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        text_bbox = draw.textbbox((0, 0), word, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        padding = 10
        img_size = (text_width + padding * 2, text_height + padding * 2)
        bg_color = (random.randint(200, 255),) * 3
        img = Image.new('RGB', img_size, color=bg_color)
        draw = ImageDraw.Draw(img)

        x = (img_size[0] - text_width) / 2
        y = (img_size[1] - text_height) / 2
        draw.text((x, y), word, font=font, fill=(0, 0, 0))

        filename = f"{count:05d}.png"
        save_path = os.path.join(output_dir, filename)
        img.save(save_path)
        labels_file.write(f"{filename},{word}\n")
        print(f"Imagen y etiqueta guardadas para la palabra: {word}")
        count += 1

    # --- Luego las fechas ---
    for fecha in fechas_a_generar:
        font_path = random.choice(font_paths)
        font_size = random.choice(font_sizes)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Error: No se pudo cargar la fuente en {font_path}")
            continue

        temp_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        text_bbox = draw.textbbox((0, 0), fecha, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        padding = 10
        img_size = (text_width + padding * 2, text_height + padding * 2)
        bg_color = (random.randint(200, 255),) * 3
        img = Image.new('RGB', img_size, color=bg_color)
        draw = ImageDraw.Draw(img)

        x = (img_size[0] - text_width) / 2
        y = (img_size[1] - text_height) / 2
        draw.text((x, y), fecha, font=font, fill=(0, 0, 0))

        filename = f"{count:05d}.png"
        save_path = os.path.join(output_dir, filename)
        img.save(save_path)
        labels_file.write(f"{filename},{fecha}\n")
        print(f"Imagen de fecha guardada: {fecha}")
        count += 1

print("Generación de dataset de palabras y fechas completada.")
