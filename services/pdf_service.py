# services/pdf_service.py
from pdf2image import convert_from_path
import os
from PIL import Image

def pdf_to_images(pdf_path, output_dir):
    images = convert_from_path(pdf_path, dpi=300)
    paths = []

    for i, img in enumerate(images):
        out = os.path.join(output_dir, f"page_{i+1}.jpg")
        img.save(out, "JPEG")
        paths.append(out)

    return paths


def image_to_pdf(image_path: str, output_pdf_path: str) -> str:
    """
    Convierte una imagen a PDF (una sola página).
    """
    img = Image.open(image_path).convert("RGB")
    img.save(output_pdf_path, "PDF", resolution=300.0)
    return output_pdf_path