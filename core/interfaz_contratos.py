import sys
import os
import shutil
import tempfile
import pandas as pd
from pathlib import Path

# Importar PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QComboBox, QPushButton, QLabel, 
    QFileDialog, QLineEdit, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal

# Importar el backend de OCR (asumiendo que están en la misma carpeta)
try:
    # Estas son las funciones que tienes en tus scripts originales
    from CRNN_inference import load_inference_model
    from document_extractor import extract_data_from_image
    BACKEND_OK = True
except ImportError as e:
    BACKEND_OK = False
    print(f"Error de importación crítica del backend: {e}")
    # Nota: El error se mostrará en la interfaz de usuario.


# Importar las funciones de utilidad para la conversión de archivos
# Se asume que convert_to_image_if_needed está definida aquí o en un módulo de utilidad
def convert_to_image_if_needed(temp_file_path):
    """Convierte PDF o asegura que la imagen sea compatible (retorna la ruta JPG)."""
    # Mantenemos esta función simple, si necesitas la implementación
    # completa (incluyendo cv2) revisa el script de Streamlit anterior.
    
    # Este es el placeholder para la lógica real que usa cv2 y pdf2image
    import cv2
    import numpy as np
    
    temp_path = Path(temp_file_path)
    output_image_path = temp_path.with_suffix(".jpg")

    if temp_path.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(temp_file_path, first_page=1, last_page=1)
            images[0].save(output_image_path, "JPEG") 
            return output_image_path
        except ImportError:
            QMessageBox.critical(None, "Error PDF", "Para procesar PDFs, necesitas instalar 'pdf2image' y Poppler.")
            return None
        except Exception as e:
            QMessageBox.critical(None, "Error PDF", f"Error al convertir PDF: {e}")
            return None

    elif temp_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
        img_cv = cv2.imread(str(temp_file_path), cv2.IMREAD_COLOR)
        if img_cv is None:
             QMessageBox.critical(None, "Error de Imagen", "No se pudo leer el archivo de imagen.")
             return None
        cv2.imwrite(str(output_image_path), img_cv)
        return output_image_path
        
    return None

# =========================================================================
# CLASE DE THREAD PARA EJECUTAR EL PROCESO DE OCR EN SEGUNDO PLANO
# =========================================================================

class OCRWorker(QThread):
    """Ejecuta el pesado proceso de OCR y manipulación de archivos en un thread separado."""
    
    # Señales para comunicar el resultado a la GUI
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, file_path, selected_period, base_root_dir, modelo, index_to_char, out_len):
        super().__init__()
        self.file_path = file_path
        self.selected_period = selected_period
        self.base_root_dir = base_root_dir
        self.modelo = modelo
        self.index_to_char = index_to_char
        self.out_len = out_len
        self.COLUMNAS_CSV = ['Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'NUM', 'CODIGO', 'RFC', 'IMSS', 'CURP', 'TELEFONO', 'CRN', 'DESDE', 'HASTA', 'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3']
        
    def update_csv(self, periodo, new_data):
        """Carga el CSV del periodo, añade los nuevos datos y lo guarda."""
        # Se asume que los CSV se guardan en una subcarpeta 'datos_csv' dentro de la carpeta raíz.
        csv_path = self.base_root_dir / "datos_csv" / f"{periodo}_datos_extraidos.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        if csv_path.exists():
            df_existente = pd.read_csv(csv_path)
        else:
            df_existente = pd.DataFrame(columns=self.COLUMNAS_CSV)

        df_nuevo = pd.DataFrame([new_data], columns=self.COLUMNAS_CSV)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_final.to_csv(csv_path, index=False)
        return csv_path

    def run(self):
        try:
            # 1. Copiar y Estandarizar a imagen JPG en una carpeta temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                raw_temp_path = temp_dir_path / Path(self.file_path).name
                shutil.copy(self.file_path, raw_temp_path)
                
                image_to_process_path = convert_to_image_if_needed(str(raw_temp_path))

                if image_to_process_path is None:
                    self.error_occurred.emit("Fallo en la conversión del archivo a imagen procesable.")
                    return

                # 2. Extracción de datos (OCR)
                # Crear una carpeta temporal para el preview del OCR
                preview_temp_dir = temp_dir_path / "preview"
                preview_temp_dir.mkdir()
                
                extracted_data, error = extract_data_from_image(
                    str(image_to_process_path), 
                    self.modelo, 
                    self.index_to_char, 
                    self.out_len,
                    str(preview_temp_dir)
                )

                if error or not extracted_data:
                    self.error_occurred.emit(f"Fallo en la extracción de datos: {error}. Revise el archivo.")
                    return
                
                # 3. Validar datos críticos (NUM y CODIGO)
                num_contrato = extracted_data.get('NUM', '').strip()
                codigo_profesor = extracted_data.get('CODIGO', '').strip()

                if not num_contrato.isdigit():
                    self.error_occurred.emit(f"El OCR no pudo obtener un 'NUM' de contrato válido. Valor: '{num_contrato}'. Proceso detenido.")
                    return
                
                if not codigo_profesor.strip():
                    self.error_occurred.emit(f"El OCR no pudo obtener el 'CODIGO' del profesor. Valor: '{codigo_profesor}'. Proceso detenido.")
                    return
                
                # 4. Organización del archivo
                # Directorio de destino: BASE_ROOT_DIR / contratos_periodos / CODIGO / PERIODO
                contracts_dir = self.base_root_dir / "contratos_periodos"
                target_dir = contracts_dir / codigo_profesor / self.selected_period
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Nombre final del archivo (NUM_CONTRATO.jpg)
                new_file_name = f"{num_contrato}{Path(image_to_process_path).suffix}"
                final_file_path = target_dir / new_file_name
                
                # Mover el archivo procesado (JPG) a su destino final
                shutil.move(image_to_process_path, final_file_path)

                # 5. Actualizar CSV
                extracted_data['Archivo'] = new_file_name
                new_row = {col: extracted_data.get(col, '') for col in self.COLUMNAS_CSV}
                csv_path = self.update_csv(self.selected_period, new_row)
                
                # 6. Emitir resultado exitoso
                self.result_ready.emit({
                    "success": True,
                    "file_name": new_file_name,
                    "target_folder": str(target_dir),
                    "csv_path": str(csv_path),
                    "data": new_row
                })

        except Exception as e:
            self.error_occurred.emit(f"Error inesperado durante el proceso de OCR/Archivo: {e}")

# =========================================================================
# CLASE DE VENTANA PRINCIPAL (GUI)
# =========================================================================

class ContratosApp(QMainWindow):
    """Ventana principal de la aplicación de escritorio PySide6."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clasificación de Contratos con OCR")
        self.setGeometry(100, 100, 800, 600)
        self.root_dir = None
        self.current_file_path = None
        self.PERIODOS_VALIDOS = ["2024A", "2024B", "2025A", "2025B", "2026A", "2026B"]
        
        if BACKEND_OK:
            self._load_ocr_model()
        
        self._setup_ui()
        self._check_backend()

    def _load_ocr_model(self):
        """Carga el modelo de OCR una sola vez y lo almacena."""
        try:
            self.modelo_inferencia, self.index_to_char, self.output_sequence_length = load_inference_model()
            self.status_label.setText("Estado: ✅ Modelo OCR cargado correctamente.")
        except Exception as e:
            self.modelo_inferencia, self.index_to_char, self.output_sequence_length = None, None, None
            self.status_label.setText(f"Estado: ❌ Error crítico al cargar el modelo OCR. {e}")
            self.process_button.setEnabled(False)

    def _check_backend(self):
        """Verifica si el backend está listo para funcionar."""
        if not BACKEND_OK:
            QMessageBox.critical(self, "Error de Sistema", 
                "No se pudieron importar los scripts de OCR (document_extractor.py, CRNN_inference.py). "
                "Asegúrate de que todos los archivos estén en la misma carpeta y las dependencias instaladas."
            )
            self.process_button.setEnabled(False)
            self.status_label.setText("Estado: ❌ Falla en la importación de scripts.")
            
        elif self.modelo_inferencia is None:
             self.process_button.setEnabled(False)
        else:
             self.process_button.setEnabled(True)


    def _setup_ui(self):
        """Configura todos los widgets y el layout de la ventana."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Configuración de Carpeta Raíz
        root_group = QWidget()
        root_layout = QHBoxLayout(root_group)
        root_layout.addWidget(QLabel("Carpeta Raíz:"))
        
        self.root_dir_edit = QLineEdit("Selecciona la Carpeta Raíz para organizar archivos...")
        self.root_dir_edit.setReadOnly(True)
        root_layout.addWidget(self.root_dir_edit)
        
        self.root_button = QPushButton("Seleccionar Carpeta")
        self.root_button.clicked.connect(self._select_root_directory)
        root_layout.addWidget(self.root_button)
        main_layout.addWidget(root_group)
        
        # 2. Selección de Periodo y Archivo
        control_group = QWidget()
        control_layout = QHBoxLayout(control_group)
        
        control_layout.addWidget(QLabel("Periodo:"))
        self.period_selector = QComboBox()
        self.period_selector.addItems(self.PERIODOS_VALIDOS)
        control_layout.addWidget(self.period_selector)
        
        control_layout.addWidget(QLabel("Archivo:"))
        self.file_path_edit = QLineEdit("Ningún archivo seleccionado...")
        self.file_path_edit.setReadOnly(True)
        control_layout.addWidget(self.file_path_edit)
        
        self.file_button = QPushButton("Subir Contrato")
        self.file_button.clicked.connect(self._select_contract_file)
        control_layout.addWidget(self.file_button)
        
        main_layout.addWidget(control_group)

        # 3. Botón de Procesamiento
        self.process_button = QPushButton("▶️ Iniciar Procesamiento OCR y Clasificación")
        self.process_button.setStyleSheet("padding: 10px; font-size: 16px; background-color: #4CAF50; color: white;")
        self.process_button.setEnabled(False) # Deshabilitado hasta que se seleccionen archivos y se cargue el modelo
        self.process_button.clicked.connect(self._start_ocr_process)
        main_layout.addWidget(self.process_button)

        # 4. Área de Estado y Resultados
        self.status_label = QLabel("Estado: Esperando carga del modelo OCR...")
        self.status_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(self.status_label)

        main_layout.addWidget(QLabel("\nResultados del Procesamiento:"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        main_layout.addWidget(self.result_text)

    # --- Slots y Métodos de la GUI ---
    
    def _select_root_directory(self):
        """Permite al usuario seleccionar la carpeta raíz del proyecto."""
        dir_name = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta Raíz")
        if dir_name:
            self.root_dir = Path(dir_name)
            self.root_dir_edit.setText(str(self.root_dir))
            self._check_ready_to_process()

    def _select_contract_file(self):
        """Permite al usuario seleccionar el archivo de contrato."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Contrato", "", "Archivos de Contrato (*.pdf *.jpg *.jpeg *.png)"
        )
        if file_path:
            self.current_file_path = file_path
            self.file_path_edit.setText(self.current_file_path)
            self._check_ready_to_process()

    def _check_ready_to_process(self):
        """Habilita el botón de procesamiento si la configuración es correcta."""
        is_ready = (self.root_dir is not None and 
                    self.current_file_path is not None and 
                    self.modelo_inferencia is not None)
        self.process_button.setEnabled(is_ready)
        
        if is_ready:
             self.status_label.setText("Estado: ✅ Listo para procesar.")

    def _start_ocr_process(self):
        """Inicia el thread de OCR Worker."""
        if not self.process_button.isEnabled():
            return
            
        self.result_text.clear()
        self.status_label.setText("Estado: ⏳ Procesando archivo... Por favor espere.")
        self.process_button.setEnabled(False) # Deshabilitar durante el proceso

        self.worker = OCRWorker(
            file_path=self.current_file_path,
            selected_period=self.period_selector.currentText(),
            base_root_dir=self.root_dir,
            modelo=self.modelo_inferencia,
            index_to_char=self.index_to_char,
            out_len=self.output_sequence_length
        )
        
        # Conectar las señales del worker a los slots de la ventana
        self.worker.result_ready.connect(self._handle_success)
        self.worker.error_occurred.connect(self._handle_error)
        self.worker.finished.connect(self._worker_finished) # Se ejecuta al terminar (éxito o error)
        
        self.worker.start()

    def _handle_success(self, result):
        """Maneja el resultado exitoso del worker."""
        msg = f"--- Proceso Completado Exitosamente ---\n\n"
        msg += f"Archivo Renombrado: {result['file_name']}\n"
        msg += f"Ubicación del Contrato: {result['target_folder']}\n"
        msg += f"CSV Actualizado: {result['csv_path']}\n\n"
        msg += f"--- Datos Extraídos y Guardados ---\n"
        
        # Formatear datos para el QTextEdit
        data_lines = [f"{k}: {v}" for k, v in result['data'].items()]
        msg += "\n".join(data_lines)
        
        self.result_text.setText(msg)
        self.status_label.setText("Estado: ✅ Procesado y Clasificado Correctamente.")
        QMessageBox.information(self, "Éxito", "Contrato procesado y clasificado con éxito.")


    def _handle_error(self, error_msg):
        """Maneja cualquier error reportado por el worker."""
        self.result_text.setText(f"ERROR: {error_msg}")
        self.status_label.setText("Estado: ❌ Error en el procesamiento.")
        QMessageBox.critical(self, "Error de Procesamiento", error_msg)

    def _worker_finished(self):
        """Señal emitida cuando el thread worker ha terminado."""
        # Se re-habilita el botón de proceso
        self.process_button.setEnabled(True)
        # Limpiar la ruta del archivo para evitar reprocesar accidentalmente
        self.current_file_path = None
        self.file_path_edit.setText("Ningún archivo seleccionado. Suba un nuevo contrato...")


# =========================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =========================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContratosApp()
    window.show()
    sys.exit(app.exec())