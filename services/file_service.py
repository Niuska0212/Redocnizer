# services/file_service.py

import os
import shutil
from datetime import datetime


class FileService:
    """
    Servicio responsable de:
    - Crear estructura de carpetas
    - Renombrar contratos
    - Mover archivos finales
    """

    def __init__(self, root_dir: str):
        """
        root_dir: directorio raíz elegido por el profesor
        """
        self.root_dir = os.path.abspath(root_dir)

    # --------------------------------------------------
    # VALIDACIONES BÁSICAS
    # --------------------------------------------------

    @staticmethod
    def _sanitize_name(value: str) -> str:
        """Limpia nombres para uso en rutas."""
        if not value:
            return "UNKNOWN"
        return "".join(c for c in value if c.isalnum() or c in ("_", "-")).strip()

    # --------------------------------------------------
    # CONSTRUCCIÓN DE RUTAS
    # --------------------------------------------------

    def get_calendar_dir(self, calendar: str) -> str:
        calendar = self._sanitize_name(calendar)
        path = os.path.join(self.root_dir, calendar)
        os.makedirs(path, exist_ok=True)
        return path

    def get_professor_dir(self, calendar: str, codigo: str) -> str:
        calendar_dir = self.get_calendar_dir(calendar)
        codigo = self._sanitize_name(codigo)
        path = os.path.join(calendar_dir, codigo)
        os.makedirs(path, exist_ok=True)
        return path

    # --------------------------------------------------
    # GUARDADO DEL CONTRATO
    # --------------------------------------------------


    def save_contract(
        self,
        calendar: str,
        codigo_profesor: str,
        num_contrato: str,
        source_file: str
    ) -> str:

        professor_dir = self.get_professor_dir(calendar, codigo_profesor)

        final_name = f"{num_contrato}.pdf"
        final_path = os.path.join(professor_dir, final_name)

        if os.path.exists(final_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_name = f"{num_contrato}_{timestamp}.pdf"
            final_path = os.path.join(professor_dir, final_name)

        shutil.move(source_file, final_path)
        return final_path

