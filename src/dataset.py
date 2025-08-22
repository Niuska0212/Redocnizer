from PIL import Image, ImageDraw, ImageFont
import os
import random

# --- Configuración ---
# Ruta del archivo de texto con las palabras
text_file_path = "../data/data/palabras.txt"

# Rutas de las fuentes a usar
font_paths = [
    "../fonts/Arial.ttf",
    "../fonts/Arial_bold.ttf",
    "../fonts/Calibri.ttf",
    "../fonts/Calibri_bold.ttf",
    "../fonts/Times.ttf"
    "../fonts/Times_bold.ttf",
]

# Define el tamaño de la imagen y los tamaños de fuente posibles
img_size = (300, 60)
font_sizes = [24, 28, 32]
# Directorio de salida
output_dir = "../data/data/dataset_palabras"
# Ruta del archivo de etiquetas
labels_file_path = os.path.join(output_dir, "labels.txt")

# --- Lógica de generación ---
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Leer las palabras del archivo de texto
try:
    with open(text_file_path, "r", encoding="utf-8") as f:
        words_to_generate = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: No se encontró el archivo de texto en {text_file_path}")
    exit()

if not words_to_generate:
    print("El archivo de palabras está vacío.")
    exit()

# Abre el archivo de etiquetas para escribir
with open(labels_file_path, "w", encoding="utf-8") as labels_file:
    # Bucle para cada palabra
    for i, word in enumerate(words_to_generate):
        # Elige una fuente y un tamaño de forma aleatoria
        font_path = random.choice(font_paths)
        font_size = random.choice(font_sizes)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Error: No se pudo cargar la fuente en {font_path}")
            continue
        
        # Crea una imagen y la dibuja
        bg_color = (random.randint(200, 255),) * 3
        img = Image.new('RGB', img_size, color=bg_color)
        draw = ImageDraw.Draw(img)
        
        text_bbox = draw.textbbox((0,0), word, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        x = (img_size[0] - text_width) / 2
        y = (img_size[1] - text_height) / 2
        draw.text((x, y), word, font=font, fill=(0, 0, 0))

        # Define el nombre de archivo (usando un contador para evitar duplicados)
        filename = f"{i:05d}.png"
        save_path = os.path.join(output_dir, filename)
        img.save(save_path)
        
        # Escribe en el archivo de etiquetas
        labels_file.write(f"{filename},{word}\n")
        print(f"Imagen y etiqueta guardadas para la palabra: {word}")

print("Generación de dataset de palabras y archivo de etiquetas completada.")