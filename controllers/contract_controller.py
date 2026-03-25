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
        """
        Procesa un contrato. El parámetro 'calendar' actúa como respaldo
        si el OCR no logra leer la fecha correctamente.
        """
        temp_dir = tempfile.mkdtemp()
        ext = os.path.splitext(file_path)[1].lower()

        # 1. Determinar imagen para OCR y PDF (Se mantiene igual)
        if ext == ".pdf":
            images = pdf_to_images(file_path, temp_dir)
            image_for_ocr = images[0]
            pdf_for_storage = file_path
        else:
            image_for_ocr = file_path
            pdf_for_storage = image_to_pdf(file_path, os.path.join(temp_dir, "temp.pdf"))

        # 2. OCR
        data, error = self.ocr_service.process_image(image_for_ocr, self.preview_dir)
        if error:
            raise RuntimeError(error)

        # Fallbacks básicos
        data.setdefault("CODIGO", "UNKNOWN")
        data.setdefault("NUM", "UNKNOWN")

        # ---------------------------------------------------------
        # 3. CÁLCULO DINÁMICO DEL CALENDARIO REAL
        # ---------------------------------------------------------
        fecha_ocr = data.get("DESDE")
        cal_calculado = self.file_service.calcular_calendario_udg(fecha_ocr)

        # Si el OCR leyó la fecha, usamos cal_calculado. 
        # Si falló (ej. papel borroso), usamos el 'calendar' que viene de la UI.
        calendar_final = cal_calculado if cal_calculado else calendar
        
        # Guardamos el dato calculado en el diccionario para que aparezca en el CSV
        data["CALENDARIO_CONTRATO"] = calendar_final

        # ---------------------------------------------------------
        # 4. Guardado final y actualización de CSV
        # ---------------------------------------------------------
        
        # El archivo se guardará con el nombre correcto: "NUM 2024B.pdf"
        final_path = self.file_service.save_contract(
            calendar=calendar_final,
            data=data,
            source_file=pdf_for_storage
        )

        # El CSV se guardará en el archivo correcto: "2024B.csv"
        calendar_dir = self.file_service.get_calendar_dir()
        update_calendar_csv(calendar_dir, data, calendar_final)

        return {
            "data": data,
            "final_path": final_path,
            "calendario_real": calendar_final
        }

    def process_uploaded_files(self, file_paths: list, calendar: str) -> list:
        results = []
        for fp in file_paths:
            try:
                # Aquí es donde se pasaba el argumento que daba error
                res = self.process_uploaded_file(file_path=fp, calendar=calendar)
                results.append({
                    "source": fp,
                    "data": res.get("data"),
                    "final_path": res.get("final_path")
                })
            except Exception as e:
                results.append({"source": fp, "error": str(e)})
        return results

    def limpiar_previews(self):
        if not self.preview_dir or not os.path.exists(self.preview_dir):
            return
        try:
            for archivo in os.listdir(self.preview_dir):
                ruta_archivo = os.path.join(self.preview_dir, archivo)
                if os.path.isfile(ruta_archivo):
                    os.remove(ruta_archivo)
        except Exception as e:
            print(f"⚠️ Error limpiando previews: {e}")