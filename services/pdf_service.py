# services/pdf_service.py
"""
Servicio centralizado para conversión de PDFs a imágenes y viceversa.
"""
import fitz  # PyMuPDF
import os
from PIL import Image


def pdf_to_images(pdf_path, output_dir, limit=None):
    """
    Convierte la primera página de un PDF a imagen JPG.
    Usa PyMuPDF (fitz) para mejor calidad y eficiencia en OCR.
    
    Args:
        pdf_path: Ruta del archivo PDF
        output_dir: Directorio donde guardar la imagen
        limit: Número de páginas a convertir (por defecto solo la primera)
    
    Returns:
        Lista con las rutas de las imágenes generadas
    """
    paths = []
    
    try:
        pdf = fitz.open(pdf_path)
        if len(pdf) > 0:  # si hay al menos una página
            pagina = pdf[0]  # primera página
            zoom = 2  # 2x = mejor calidad
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat)
            
            # Usar el nombre del PDF original (sin extensión)
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            out = os.path.join(output_dir, f"{base_name}.jpg")
            pix.save(out)
            paths.append(out)
        
        pdf.close()
    except Exception as e:
        print(f"Error al convertir PDF {pdf_path}: {e}")
    
    return paths


def convert_pdfs_in_folder(source_folders, output_folder):
    """
    Convierte todos los PDFs en las carpetas especificadas.
    Reemplaza la funcionalidad del convertidor_PDF_JPG.py script.
    
    Args:
        source_folders: Lista de carpetas que contienen PDFs
        output_folder: Carpeta donde guardar todas las imágenes
    
    Returns:
        Diccionario con conteo de archivos procesados
    """
    os.makedirs(output_folder, exist_ok=True)
    
    processed = 0
    errors = 0
    
    if isinstance(source_folders, str):
        source_folders = [source_folders]
    
    for carpeta in source_folders:
        if not os.path.exists(carpeta):
            print(f"⚠️ Carpeta no encontrada: {carpeta}")
            continue
        
        for archivo in os.listdir(carpeta):
            if archivo.lower().endswith(".pdf"):
                ruta_pdf = os.path.join(carpeta, archivo)
                
                try:
                    print(f"Convirtiendo {ruta_pdf} ...")
                    
                    pdf = fitz.open(ruta_pdf)
                    if len(pdf) > 0:
                        pagina = pdf[0]
                        zoom = 2
                        mat = fitz.Matrix(zoom, zoom)
                        pix = pagina.get_pixmap(matrix=mat)
                        
                        nombre_base = os.path.splitext(archivo)[0]
                        ruta_jpg = os.path.join(output_folder, f"{nombre_base}.jpg")
                        pix.save(ruta_jpg)
                        
                        processed += 1
                    
                    pdf.close()
                except Exception as e:
                    print(f"❌ Error procesando {archivo}: {e}")
                    errors += 1
    
    print(f"\n✅ Conversión completa:")
    print(f"   Procesados: {processed}")
    print(f"   Errores: {errors}")
    print(f"   Guardados en: {output_folder}")
    
    return {"processed": processed, "errors": errors, "output_dir": output_folder}


def image_to_pdf(image_path: str, output_pdf_path: str) -> str:
    """
    Convierte una imagen a PDF (una sola página).
    
    Args:
        image_path: Ruta de la imagen
        output_pdf_path: Ruta donde guardar el PDF
    
    Returns:
        Ruta del PDF generado
    """
    img = Image.open(image_path).convert("RGB")
    img.save(output_pdf_path, "PDF", resolution=300.0)
    return output_pdf_path