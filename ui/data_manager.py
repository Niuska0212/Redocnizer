# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo para manejar operaciones de datos (carga, guardado, actualización)."""
import os
import pandas as pd
from datetime import datetime
from PySide6.QtCore import Signal, QObject

class DataManager(QObject):
    """
    Manejador de datos estricto. 
    Solo opera sobre el archivo 'contratos.csv' del calendario seleccionado.
    """
    data_updated = Signal()

    def __init__(self):
        super().__init__()
        self.data = pd.DataFrame()
        self.source_csv_file = None  # Ruta absoluta al contratos.csv activo

    def set_source_csv(self, csv_path: str):
        """
        Establece el archivo de trabajo principal. 
        Si el archivo existe, lo carga. Si no, limpia la vista para iniciar uno nuevo.
        """
        self.source_csv_file = csv_path
        
        if os.path.exists(csv_path):
            print(f"📁 Cargando base de datos del calendario: {csv_path}")
            self._internal_load(csv_path)
        else:
            print(f"✨ No se encontró base de datos previa en: {csv_path}. Iniciando nueva.")
            self.data = pd.DataFrame()
            self.data_updated.emit()

    def _internal_load(self, path):
        """Carga técnica de datos con limpieza de codificación."""
        try:
            # Se usa utf-8-sig para ignorar automáticamente el BOM de archivos Excel/CSV
            df = pd.read_csv(path, encoding='utf-8-sig', dtype=str)
            
            # Limpiar nombres de columnas (espacios en blanco o caracteres invisibles)
            df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
            
            # Normalización de la fecha de procesamiento si existe
            if 'Fecha_Procesamiento' in df.columns:
                df['Fecha_Procesamiento'] = pd.to_datetime(df['Fecha_Procesamiento'], errors='coerce')
            
            self.data = df
            self.data_updated.emit()
        except Exception as e:
            print(f"❌ Error al cargar el archivo CSV: {e}")
            self.data = pd.DataFrame()

    def save_data(self):
        """Guarda el estado actual del DataFrame directamente en el archivo del calendario."""
        if not self.source_csv_file:
            print("⚠️ Error: No se puede guardar porque no se ha establecido un calendario de destino.")
            return

        try:
            # Columnas requeridas según el orden del sistema
            preferred_columns = [
                'PATERNO', 'MATERNO', 'NOMBRE_S', 'CODIGO', 'NUM',
                'CRN','HRS_TOTALES', 'MATERIA', 'DESDE', 'HASTA', 'TELEFONO',
                'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3',
                'RFC', 'IMSS', 'CURP'
            ]

            # Garantizar que todas las columnas preferidas existan en el DataFrame
            for col in preferred_columns:
                if col not in self.data.columns:
                    self.data[col] = ""

            # Asegurar que existan las carpetas (ej: CALENDARIOS/2024A/)
            os.makedirs(os.path.dirname(self.source_csv_file), exist_ok=True)
            
            # Reordenar columnas para mantener consistencia: Preferidas + El resto
            other_cols = [c for c in self.data.columns if c not in preferred_columns]
            final_df = self.data[preferred_columns + other_cols]

            # Guardado final
            final_df.to_csv(self.source_csv_file, index=False, encoding='utf-8-sig')
            print(f"✅ Archivo actualizado correctamente en: {self.source_csv_file}")
            
        except Exception as e:
            print(f"❌ Error crítico al guardar datos: {e}")

    def add_record(self, record_data):
        """Añade una fila nueva y sincroniza el archivo."""
        record_data['Fecha_Procesamiento'] = datetime.now()
        new_row = pd.DataFrame([record_data])
        
        if self.data.empty:
            self.data = new_row
        else:
            self.data = pd.concat([self.data, new_row], ignore_index=True)
            
        self.save_data()
        self.data_updated.emit()

    def update_record(self, row_index, column_name, value):
        """Actualiza una celda específica y sincroniza el archivo."""
        if 0 <= row_index < len(self.data):
            self.data.at[row_index, column_name] = value
            self.save_data()
            self.data_updated.emit()

    def delete_record(self, row_index):
        """Elimina una fila y sincroniza el archivo."""
        if 0 <= row_index < len(self.data):
            self.data = self.data.drop(row_index).reset_index(drop=True)
            self.save_data()
            self.data_updated.emit()

    def get_dataframe(self):
        """Retorna una copia de los datos actuales."""
        return self.data.copy()

    def load_from_csv(self, csv_path: str):
        """
        Carga manual desde un archivo seleccionado por el usuario. 
        Esto lo convierte en el archivo activo.
        """
        self.set_source_csv(csv_path)
        return True

    def load_from_calendar_dir(self, calendar_dir: str, calendar_name: str):
        """Apunta al 'contratos.csv' dentro de la carpeta de un calendario."""
        csv_path = os.path.join(calendar_dir, f"{calendar_name}.csv")
        return self.load_from_csv(csv_path)
    
    def export_to_csv(self, filepath):
        """Exporta los datos actuales a un archivo CSV externo."""
        try:
            self.data.to_csv(filepath, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"❌ Error exportando CSV: {e}")
            return False

    def export_to_excel(self, filepath):
        """Exporta los datos actuales a un archivo Excel externo."""
        try:
            # Si termina en .xlsx usa el motor de Excel, si no, lo saca como CSV (pero con extensión cambiada)
            if filepath.lower().endswith('.xlsx'):
                self.data.to_excel(filepath, index=False)
            else:
                self.data.to_csv(filepath, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"❌ Error exportando Excel: {e}")
            return False