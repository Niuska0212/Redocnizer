from PIL import Image, ImageDraw, ImageFont
import os
import random


# Configuración de rutas

# Carpeta donde está este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#hola cambios
# Archivo de palabras
palabras_file = os.path.join(BASE_DIR, "..", "data", "data", "palabras.txt")
palabras_file = os.path.abspath(palabras_file)

# Carpeta de salida para las imágenes
output_dir = os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")
output_dir = os.path.abspath(output_dir)

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

# Archivo de etiquetas
labels_file_path = os.path.join(output_dir, "labels.txt")

# Preparar directorio de salida

os.makedirs(output_dir, exist_ok=True)


# Leer palabras desde el archivo
try:
    with open(palabras_file, "r", encoding="utf-8") as f:
        words_to_generate = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: No se encontró el archivo de texto en {palabras_file}")
    exit()

if not words_to_generate:
    print("El archivo de palabras está vacío.")
    exit()


# Generar imágenes
with open(labels_file_path, "w", encoding="utf-8") as labels_file:
    for i, word in enumerate(words_to_generate):
        # Elegir fuente y tamaño aleatorio
        font_path = random.choice(font_paths)
        font_size = random.choice(font_sizes)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Error: No se pudo cargar la fuente en {font_path}")
            continue
        
        # Crear imagen temporal para medir tamaño del texto
        temp_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        text_bbox = draw.textbbox((0, 0), word, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        # Crear imagen final con padding
        padding = 10
        img_size = (text_width + padding * 2, text_height + padding * 2)
        bg_color = (random.randint(200, 255),) * 3
        img = Image.new('RGB', img_size, color=bg_color)
        draw = ImageDraw.Draw(img)

        # Posicionar texto centrado
        x = (img_size[0] - text_width) / 2
        y = (img_size[1] - text_height) / 2
        draw.text((x, y), word, font=font, fill=(0, 0, 0))

        # Guardar imagen y escribir etiqueta
        filename = f"{i:05d}.png"
        save_path = os.path.join(output_dir, filename)
        img.save(save_path)
        labels_file.write(f"{filename},{word}\n")
        print(f"Imagen y etiqueta guardadas para la palabra: {word}")

print("Generación de dataset de palabras y archivo de etiquetas completada.")
