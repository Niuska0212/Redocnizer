import os
import fitz  # PyMuPDF

# Carpetas donde están tus PDFs
carpetas = [
    r"data\data\contratos\2024A",
    r"data\data\contratos\2024B"
]

# Carpeta de salida para todas las imágenes
carpeta_salida = r"data\data\contratos\imagenes_jpg"
os.makedirs(carpeta_salida, exist_ok=True)

for carpeta in carpetas:
    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            ruta_pdf = os.path.join(carpeta, archivo)
            nombre_base = os.path.splitext(archivo)[0]

            print(f"Convirtiendo {ruta_pdf} ...")

            pdf = fitz.open(ruta_pdf)
            if len(pdf) > 0:  # si hay al menos una página
                pagina = pdf[0]  # primera (y única) página
                zoom = 2  # 2x = mejor calidad
                mat = fitz.Matrix(zoom, zoom)
                pix = pagina.get_pixmap(matrix=mat)

                # Guardar en la carpeta de salida
                ruta_jpg = os.path.join(carpeta_salida, f"{nombre_base}.jpg")
                pix.save(ruta_jpg)

            pdf.close()

print("✅ Conversión completa. Todas las imágenes están en:", carpeta_salida)
