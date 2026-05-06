# controllers/contract_controller.py

import os
import tempfile
import traceback # Añadimos esto para ver errores detallados en consola

from services.ocr_service import OCRService
from services.file_service import FileService
from services.pdf_service import image_to_pdf
from services.csv_service import update_calendar_csv
from services.pdf_service import pdf_to_images

class ContractController:
    def __init__(self, root_dir: str, preview_dir: str):
        self.root_dir = root_dir
        self.ocr_service = OCRService()
        self.file_service = FileService(root_dir)
        self.preview_dir = preview_dir

    def process_uploaded_file(self, file_path: str, calendar: str) -> dict:
        """
        Procesa un contrato individualmente.
        """
        temp_dir = tempfile.mkdtemp()
        ext = os.path.splitext(file_path)[1].lower()
        nombre_archivo = os.path.basename(file_path)

        # 1. Determinar imagen para OCR y PDF
        if ext == ".pdf":
            images = pdf_to_images(file_path, temp_dir)
            if not images:
                raise RuntimeError("No se pudieron extraer imágenes del PDF.")
            image_for_ocr = images[0]
            pdf_for_storage = file_path
        else:
            image_for_ocr = file_path
            pdf_for_storage = image_to_pdf(file_path, os.path.join(temp_dir, "temp.pdf"))

        # 2. OCR (Aquí es donde entran tus mejoras de preprocessing.py)
        data, error = self.ocr_service.process_image(image_for_ocr, self.preview_dir)
        
        if error:
            # Si el error es por imagen oscura o vacía, lo lanzamos para el log
            raise RuntimeError(f"Error en OCR: {error}")

        # Fallbacks básicos
        data.setdefault("CODIGO", "UNKNOWN")
        data.setdefault("NUM", "UNKNOWN")
        
        # 3. CÁLCULO DINÁMICO DEL CALENDARIO
        fecha_ocr = data.get("DESDE")
        cal_calculado = self.file_service.calcular_calendario_udg(fecha_ocr)
        calendar_final = cal_calculado if cal_calculado else calendar
        data["CALENDARIO_CONTRATO"] = calendar_final

        # 4. Guardado final
        final_path = self.file_service.save_contract(
            calendar=calendar_final,
            data=data,
            source_file=pdf_for_storage
        )

        calendar_dir = self.file_service.get_calendar_dir()
        update_calendar_csv(calendar_dir, data, calendar_final)

        return {
            "status": "success", # Agregamos el estatus explícito
            "file_name": nombre_archivo,
            "data": data,
            "final_path": final_path,
            "calendario_real": calendar_final
        }

    def process_uploaded_files(self, file_paths: list, calendar: str) -> list:
        """
        Este método es el que usa el Worker. 
        Lo blindamos para que el log reciba información útil.
        """
        results = []
        for fp in file_paths:
            nombre_archivo = os.path.basename(fp)
            try:
                res = self.process_uploaded_file(file_path=fp, calendar=calendar)
                results.append(res)
            except Exception as e:
                # IMPORTANTE: Este formato es el que leerá tu generador de logs
                results.append({
                    "status": "error",
                    "file_name": nombre_archivo,
                    "error": str(e)
                })
                print(f"❌ Error procesando {nombre_archivo}: {e}")
                traceback.print_exc() # Para que tú como dev veas qué falló exactamente
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