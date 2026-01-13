import os
import pandas as pd
from datetime import datetime
from PySide6.QtCore import Signal, QObject


class DataManager(QObject):
    """Manejador de datos para el sistema (extraído de main_window.py)."""
    data_updated = Signal()

    def __init__(self):
        super().__init__()
        self.data = pd.DataFrame()
        # Usar CSV en vez de XLSX según preferencia del usuario
        self.data_file = os.path.join(os.getcwd(), "contratos_data.csv")
        self._load_data()

    def _load_data(self):
        """Carga datos existentes del archivo CSV"""
        if os.path.exists(self.data_file):
            try:
                # Leer CSV si existe
                self.data = pd.read_csv(self.data_file, encoding='utf-8', dtype=str)
                # Normalizar nombres y convertir Fecha_Procesamiento si existe
                self.data.columns = [str(c).replace('\ufeff', '').strip() for c in self.data.columns]
                if 'Fecha_Procesamiento' in self.data.columns:
                    self.data['Fecha_Procesamiento'] = pd.to_datetime(self.data['Fecha_Procesamiento'], errors='coerce')
            except Exception as e:
                print(f"Error cargando datos: {e}")
                self.data = pd.DataFrame()
        else:
            self.data = pd.DataFrame()

    def add_record(self, record_data):
        """Agrega un nuevo registro"""
        record_data['Fecha_Procesamiento'] = datetime.now()

        if self.data.empty:
            self.data = pd.DataFrame([record_data])
        else:
            new_df = pd.DataFrame([record_data])
            self.data = pd.concat([self.data, new_df], ignore_index=True)

        self.save_data()
        self.data_updated.emit()

    def update_record(self, row_index, column_name, value):
        """Actualiza un registro específico"""
        if not self.data.empty and row_index < len(self.data):
            self.data.at[row_index, column_name] = value
            self.save_data()
            self.data_updated.emit()

    def delete_record(self, row_index):
        """Elimina un registro"""
        if not self.data.empty and row_index < len(self.data):
            self.data = self.data.drop(row_index).reset_index(drop=True)
            self.save_data()
            self.data_updated.emit()

    def save_data(self):
        """Guarda los datos al archivo CSV con solo columnas esenciales"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            # Columnas esenciales en el orden solicitado por el usuario
            preferred_columns = [
                'PATERNO', 'MATERNO', 'NOMBRE_S', 'NUM', 'CODIGO', 'RFC', 'IMSS', 'CURP',
                'TELEFONO', 'CRN', 'DESDE', 'HASTA', 'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3'
            ]

            # Añadir columnas faltantes con valores vacíos y mapear columnas
            # existentes de forma case-insensitive para evitar perder datos
            col_map = {c.lower(): c for c in self.data.columns}

            ordered = []
            for pref in preferred_columns:
                if pref in self.data.columns:
                    ordered.append(pref)
                elif pref.lower() in col_map:
                    # Usar el nombre real existente (p. ej. 'nombre' vs 'Nombre')
                    ordered.append(col_map[pref.lower()])
                else:
                    # Crear columna preferida si no existe
                    self.data[pref] = ""
                    ordered.append(pref)

            # Añadir el resto de columnas que no están en 'ordered', preservando nombres reales
            remaining = [c for c in self.data.columns if c not in ordered]
            final_columns = ordered + remaining

            # Guardar como CSV usando el orden final de columnas
            # Aseguramos encoding utf-8 para compatibilidad
            self.data[final_columns].to_csv(self.data_file, index=False, encoding='utf-8')

            print(f"Datos guardados en: {self.data_file}")
        except Exception as e:
            print(f"Error guardando datos: {e}")

    def get_dataframe(self):
        """Retorna el DataFrame actual"""
        return self.data.copy()

    def load_from_csv(self, csv_path: str):
        """Carga datos desde un CSV (por ejemplo el CSV de un calendario)."""
        try:
            if os.path.exists(csv_path):
                # Leer preservando todo como strings para evitar conversión errónea
                df = pd.read_csv(csv_path, encoding='utf-8', dtype=str)

                # Sanitizar nombres de columnas: eliminar BOM, trim y espacios extra
                df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]

                # Eliminar columnas inesperadas generadas por parsing erróneo (ej: sufijo _LEFT)
                drop_cols = [c for c in df.columns if c.strip().upper().endswith('_LEFT')]
                if drop_cols:
                    df = df.drop(columns=drop_cols)

                # Normalizar columna Fecha_Procesamiento si existe
                fecha_col = next((c for c in df.columns if c.lower() == 'fecha_procesamiento' or c == 'Fecha_Procesamiento'), None)
                if fecha_col is not None:
                    df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce')

                # Asegurar columnas mínimas (mismo esquema que en save_data)
                preferred_columns = [
                    'PATERNO', 'MATERNO', 'NOMBRE_S', 'NUM', 'CODIGO', 'RFC', 'IMSS', 'CURP',
                    'TELEFONO', 'CRN', 'DESDE', 'HASTA', 'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3'
                ]

                for col in preferred_columns:
                    # Añadir si no existe cualquier variante (case-insensitive)
                    if not any(c.lower() == col.lower() for c in df.columns):
                        df[col] = ""

                # Reordenar: preferidas (si existen) luego el resto
                ordered = [c for c in preferred_columns if any(dc.lower() == c.lower() for dc in df.columns)]
                # Obtener nombres reales de las columnas preferidas en el orden correcto (preservando casing existente)
                real_ordered = []
                for pref in ordered:
                    real = next((c for c in df.columns if c.lower() == pref.lower()), pref)
                    real_ordered.append(real)

                remaining = [c for c in df.columns if c not in real_ordered]
                df = df[real_ordered + remaining]

                # Fusionar con datos existentes en lugar de sobrescribir
                if self.data is None or self.data.empty:
                    combined = df.copy()
                else:
                    combined = pd.concat([self.data, df], ignore_index=True, sort=False)

                # Eliminar duplicados si existe columna 'archivo' (case-insensitive)
                archivo_col = next((c for c in combined.columns if c.lower() == 'archivo' or c.lower() == 'archivo'), None)
                if archivo_col is not None:
                    combined = combined.drop_duplicates(subset=[archivo_col], keep='first').reset_index(drop=True)

                # Guardar resultado en self.data
                self.data = combined
                self.data_updated.emit()
                return True
            return False
        except Exception as e:
            print(f"Error cargando CSV: {e}")
            return False

    def load_from_calendar_dir(self, calendar_dir: str):
        """Carga el CSV 'contratos.csv' desde un directorio de calendario."""
        csv_path = os.path.join(calendar_dir, 'contratos.csv')
        return self.load_from_csv(csv_path)

    def export_to_csv(self, filepath):
        """Exporta a CSV"""
        try:
            self.data.to_csv(filepath, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error exportando CSV: {e}")
            return False

    def export_to_excel(self, filepath):
        """Exporta a Excel (guarda CSV para compatibilidad)"""
        try:
            self.data.to_csv(filepath, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error exportando Excel: {e}")
            return False
