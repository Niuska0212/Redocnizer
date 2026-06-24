# services/file_service.py

import os
import shutil
from datetime import datetime

class FileService:
    """
    Servicio responsable de:
    - Crear estructura de carpetas jerárquica (Expedientes/Nombre Código/Subcarpetas)
    - Renombrar contratos según: NUM_CONTRATO CALENDARIO.pdf
    - gestión de archivos en almacenamiento local o de red.
    Soporta rutas UNC (//servidor/recurso) para evitar depender de letras de unidad (Z:/).
    """

    def __init__(self, root_dir: str):
        """
        root_dir: Puede ser 'Z:/...' o '//192.168.1.100/compartido/...'
        """
        # Convertimos a ruta absoluta y normalizamos barras según el SO
        self.root_dir = os.path.normpath(root_dir)
        self._check_connection()

    def _check_connection(self):
        """Verifica si el recurso de red está accesible."""
        if not os.path.exists(self.root_dir):
            print(f"⚠️ ADVERTENCIA: No se puede acceder a la ruta: {self.root_dir}")
            print("Asegúrate de tener permisos de red y conexión activa.")

    @staticmethod
    def _sanitize_name(value: str) -> str:
        """Limpia nombres para evitar caracteres prohibidos en carpetas."""
        if not value:
            return ""
        # Permitimos espacios para los nombres de carpetas de profesores
        return "".join(c for c in value if c.isalnum() or c in (" ", "_", "-")).strip().upper()
    
    def calcular_calendario_udg(self, fecha_desde_str: str) -> str:
        """
        Analiza la fecha 'DESDE' extraída por el OCR y determina el ciclo.
        Ejemplo: 16/01/2024 -> 2024A | 16/07/2024 -> 2024B
        """
        try:
            if not fecha_desde_str or "/" not in str(fecha_desde_str):
                return None
            
            # Limpiar posibles espacios y convertir a objeto fecha
            fecha_dt = datetime.strptime(fecha_desde_str.strip(), "%d/%m/%Y")
            anio = fecha_dt.year
            mes = fecha_dt.month

            # Lógica UDG: Enero a Junio es 'A', Julio en adelante es 'B'
            ciclo = "A" if mes <= 6 else "B"
            
            return f"{anio}{ciclo}"
        except Exception as e:
            print(f"⚠️ No se pudo procesar la fecha '{fecha_desde_str}': {e}")
            return None

    def get_calendar_dir(self, calendar: str = None) -> str:
        """
        Retorna SIEMPRE la carpeta CALENDARIOS dentro de la carpeta del software.
        Ignora el root_dir de los expedientes para la base de datos.
        """
        # Esto obtiene la ruta de 'n:/Proyecto-modular' independientemente de N:/000_Archivo
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        calendar_path = os.path.normpath(os.path.join(project_root, "CALENDARIOS"))
        
        if not os.path.exists(calendar_path):
            os.makedirs(calendar_path, exist_ok=True)
            
        return calendar_path

    def get_full_professor_path(self, data: dict) -> str:
        """
        Construye la ruta completa siguiendo el ejemplo:
        RAIZ / APELLIDO PATERNO MATERNO NOMBRES CODIGO / 000000 DOC BASICOS / 06 NOMBRAMIENTOS
        """
        # 1. Extraer y limpiar partes del nombre (Asumiendo que vienen del OCR/DataTab)
        paterno = self._sanitize_name(data.get("PATERNO", ""))
        materno = self._sanitize_name(data.get("MATERNO", ""))
        nombres = self._sanitize_name(data.get("NOMBRE_S", data.get("NOMBRES", "")))
        codigo  = self._sanitize_name(str(data.get("CODIGO", "SINCÓDIGO")))

        # 2. Formatear la carpeta del profesor: "FRANCO LOPEZ VELARDE EMMANUEL 2324725"
        professor_folder_name = f"{paterno} {materno} {nombres} {codigo}".strip()
        
        # 3. Definir subcarpetas fijas
        sub_path = os.path.join(
            professor_folder_name, 
            "000000 DOC BASICOS", 
            "06 NOMBRAMIENTOS"
        )

        # 4. Ruta absoluta final
        final_dir = os.path.join(self.root_dir, sub_path)
        
        # Crear la estructura si no existe
        os.makedirs(final_dir, exist_ok=True)
        return final_dir

    def save_contract(
        self,
        calendar: str, # Este será el calendario calculado que le mande el Controller
        data: dict,
        source_file: str
    ) -> str:
        dest_dir = self.get_full_professor_path(data)

        # El nombre ahora usará el calendario real del contrato (ej. 2024B)
        num_contrato = self._sanitize_name(str(data.get("NUM", "SIN_NUM")))
        calendar_str = self._sanitize_name(calendar)
        
        final_name = f"{num_contrato} {calendar_str}.pdf"
        final_path = os.path.join(dest_dir, final_name)

        try:
            shutil.copy2(source_file, final_path)
            return final_path
        except Exception as e:
            print(f"Error al guardar archivo: {e}")
            return f"ERROR: {str(e)}"

