# controllers/contract_controller.py

import os
import tempfile

from services.ocr_service import OCRService
from services.file_service import FileService
from services.pdf_service import image_to_pdf
from services.csv_service import update_calendar_csv
from services.pdf_service import pdf_to_images


class ContractController:
    def __init__(self, root_dir: str, preview_dir: str):
        self.ocr_service = OCRService()
        self.file_service = FileService(root_dir)
        self.preview_dir = preview_dir

    def process_uploaded_file(self, file_path: str, calendar: str) -> dict:
        """Procesa un contrato (PDF o imagen) y lo guarda como PDF final.
        Retorna:
            {
                "data": datos OCR,
                "final_path": ruta del PDF final
            }
        """

        temp_dir = tempfile.mkdtemp()
        ext = os.path.splitext(file_path)[1].lower()

        # -----------------------------------
        # 1. Determinar imagen para OCR y PDF
        # -----------------------------------

        if ext == ".pdf":
            images = pdf_to_images(file_path, temp_dir)
            image_for_ocr = images[0]
            pdf_for_storage = file_path
        else:
            image_for_ocr = file_path
            pdf_for_storage = image_to_pdf(
                file_path,
                os.path.join(temp_dir, "temp.pdf")
            )

        # -----------------------------------
        # 2. OCR
        # -----------------------------------

        data, error = self.ocr_service.process_image(
            image_for_ocr,
            self.preview_dir
        )

        if error:
            raise RuntimeError(error)

        # Fallbacks básicos
        data.setdefault("CODIGO", "UNKNOWN")
        data.setdefault("NUM", "UNKNOWN")

        # -----------------------------------
        # 3. Guardado final
        # -----------------------------------

        final_path = self.file_service.save_contract(
            calendar=calendar,
            data=data,  # Pasamos todo el diccionario 'data' que tiene PATERNO, MATERNO, NOMBRES, CODIGO, NUM
            source_file=pdf_for_storage
        )

        # -----------------------------------
        # 4. Actualizar CSV
        # -----------------------------------

        calendar_dir = self.file_service.get_calendar_dir(calendar)
        update_calendar_csv(calendar_dir, data)

        return {
            "data": data,
            "final_path": final_path
        }

    def process_uploaded_files(self, file_paths: list, calendar: str) -> list:
        """
        Procesa múltiples archivos (imagenes o PDFs). Retorna lista de resultados por archivo.
        Cada resultado: {"source": ruta_original, "data": datos, "final_path": ruta_guardado} o {"source":..., "error": mensaje}
        """
        results = []
        for fp in file_paths:
            try:
                res = self.process_uploaded_file(file_path=fp, calendar=calendar)
                results.append({
                    "source": fp,
                    "data": res.get("data"),
                    "final_path": res.get("final_path")
                })
            except Exception as e:
                results.append({
                    "source": fp,
                    "error": str(e)
                })

        return results
