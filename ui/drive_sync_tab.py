# ui/drive_sync_tab.py
"""
Pestaña de sincronización con Google Drive.
Permite: login, subir, descargar, sincronizar archivos.
Integración del Módulo 3 (Distribución)
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QProgressBar, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QColor
from datetime import datetime
import pandas as pd

class GoogleDriveSyncWorker(QThread):
    """Worker para operaciones de sincronización (no bloquea UI)"""
    
    progress = Signal(str)  # Mensaje de progreso
    finished = Signal(bool, str)  # (éxito, mensaje)
    files_updated = Signal(list)  # Lista de archivos actualizada
    
    def __init__(self, drive_service, operation, *args, **kwargs):
        super().__init__()
        self.drive_service = drive_service
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == "upload":
                file_id = self.drive_service.upload_contract(self.args[0], self.args[1] if len(self.args) > 1 else None)
                self.progress.emit(f"✅ Archivo subido: {file_id}")
                self.finished.emit(True, "Archivo subido exitosamente")
            
            elif self.operation == "download":
                self.drive_service.download_file(self.args[0], self.args[1])
                self.progress.emit(f"✅ Archivo descargado")
                self.finished.emit(True, "Descarga completada")
            
            elif self.operation == "list":
                files = self.drive_service.list_files(limit=self.kwargs.get('limit', 20))
                self.files_updated.emit(files)
                self.finished.emit(True, f"{len(files)} archivos encontrados")
            
            elif self.operation == "sync_local_to_drive":
                uploaded = self.drive_service.sync_local_to_drive(self.args[0])
                self.progress.emit(f"✅ {len(uploaded)} archivos sincronizados")
                self.finished.emit(True, f"{len(uploaded)} archivos subidos")
            
            elif self.operation == "sync_drive_to_local":
                count = self.drive_service.sync_drive_to_local(self.args[0])
                self.progress.emit(f"✅ {count} archivos descargados")
                self.finished.emit(True, f"{count} archivos descargados")
        
        except Exception as e:
            self.progress.emit(f"❌ Error: {str(e)}")
            self.finished.emit(False, str(e))


class DriveSyncTab(QWidget):
    """Pestaña para sincronización con Google Drive"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.drive_service = None
        self.user_info = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout()
        
        # ========== SECCIÓN 1: LOGIN ==========
        login_group = self._create_login_section()
        layout.addLayout(login_group)
        
        # ========== SECCIÓN 2: INFORMACIÓN DE USUARIO ==========
        info_layout = QHBoxLayout()
        self.label_user = QLabel("❌ No autenticado")
        self.label_storage = QLabel("---")
        info_layout.addWidget(QLabel("👤 Usuario:"))
        info_layout.addWidget(self.label_user)
        info_layout.addStretch()
        info_layout.addWidget(QLabel("💾 Almacenamiento:"))
        info_layout.addWidget(self.label_storage)
        layout.addLayout(info_layout)
        
        # ========== SECCIÓN 3: OPERACIONES ==========
        ops_group = self._create_operations_section()
        layout.addLayout(ops_group)
        
        # ========== SECCIÓN 4: TABLA DE ARCHIVOS ==========
        layout.addWidget(QLabel("📁 Archivos en OCR-Modular:"))
        self.table_files = QTableWidget()
        self.table_files.setColumnCount(5)
        self.table_files.setHorizontalHeaderLabels(
            ["Nombre", "Tamaño", "Creado", "Modificado", "ID"]
        )
        self.table_files.setColumnHidden(4, True)  # ID oculto
        layout.addWidget(self.table_files)
        
        # ========== SECCIÓN 5: PROGRESO ==========
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.label_status = QLabel("Listo")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.label_status)
        
        self.setLayout(layout)
    
    def _create_login_section(self) -> QHBoxLayout:
        """Crea sección de autenticación"""
        layout = QHBoxLayout()
        
        self.btn_login = QPushButton("🔐 Conectar con Google")
        self.btn_logout = QPushButton("🚪 Desconectar")
        self.btn_logout.setEnabled(False)
        
        self.btn_login.clicked.connect(self.login_google)
        self.btn_logout.clicked.connect(self.logout_google)
        
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_logout)
        layout.addStretch()
        
        return layout
    
    def _create_operations_section(self) -> QVBoxLayout:
        """Crea sección de operaciones"""
        layout = QVBoxLayout()
        
        # Fila 1: Subir/Descargar individual
        row1 = QHBoxLayout()
        self.btn_upload = QPushButton("📤 Subir Contrato")
        self.btn_download = QPushButton("📥 Descargar Archivo")
        self.btn_refresh = QPushButton("🔄 Actualizar Lista")
        
        self.btn_upload.clicked.connect(self.upload_file)
        self.btn_download.clicked.connect(self.download_file)
        self.btn_refresh.clicked.connect(self.refresh_file_list)
        
        self.btn_upload.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        
        row1.addWidget(self.btn_upload)
        row1.addWidget(self.btn_download)
        row1.addWidget(self.btn_refresh)
        row1.addStretch()
        layout.addLayout(row1)
        
        # Fila 2: Sincronización
        row2 = QHBoxLayout()
        self.btn_sync_up = QPushButton("⬆️ Sincronizar a Nube (Carpeta)")
        self.btn_sync_down = QPushButton("⬇️ Sincronizar desde Nube (Carpeta)")
        
        self.btn_sync_up.clicked.connect(self.sync_to_drive)
        self.btn_sync_down.clicked.connect(self.sync_from_drive)
        
        self.btn_sync_up.setEnabled(False)
        self.btn_sync_down.setEnabled(False)
        
        row2.addWidget(self.btn_sync_up)
        row2.addWidget(self.btn_sync_down)
        row2.addStretch()
        layout.addLayout(row2)
        
        return layout
    
    def login_google(self):
        """Conecta con Google Drive"""
        try:
            from services.google_drive_service import GoogleDriveService
            
            # Verificar que existe credentials.json
            if not os.path.exists("credentials.json"):
                QMessageBox.critical(
                    self,
                    "Error de Configuración",
                    "No se encontró 'credentials.json'.\n\n"
                    "Sigue los pasos en SETUP_GOOGLE_DRIVE.md para configurar Google Cloud."
                )
                return
            
            self.label_status.setText("⏳ Autenticando con Google...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(0)  # Animación indeterminada
            
            # Crear servicio (esto abrirá navegador si es primera vez)
            self.drive_service = GoogleDriveService()
            
            # Obtener información del usuario
            self.user_info = self.drive_service.get_user_info()
            storage_info = self.drive_service.get_storage_info()
            
            # Actualizar UI
            self.label_user.setText(f"{self.user_info['nombre']}")
            storage_str = f"{storage_info['usado_gb']}GB / {storage_info['total_gb']}GB"
            self.label_storage.setText(storage_str)
            
            # Habilitar botones
            self.btn_login.setEnabled(False)
            self.btn_logout.setEnabled(True)
            self.btn_upload.setEnabled(True)
            self.btn_download.setEnabled(True)
            self.btn_refresh.setEnabled(True)
            self.btn_sync_up.setEnabled(True)
            self.btn_sync_down.setEnabled(True)
            
            self.label_status.setText("✅ Conectado a Google Drive")
            self.progress_bar.setVisible(False)
            
            # Cargar lista de archivos
            self.refresh_file_list()
            
            QMessageBox.information(
                self,
                "Éxito",
                f"✅ Autenticación exitosa\n\n"
                f"Bienvenido {self.user_info['nombre']}"
            )
        
        except Exception as e:
            self.label_status.setText(f"❌ Error: {str(e)}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error de Autenticación", str(e))
    
    def logout_google(self):
        """Desconecta de Google Drive"""
        try:
            if os.path.exists("token.json"):
                os.remove("token.json")
            
            self.drive_service = None
            self.user_info = None
            
            # Deshabilitar botones
            self.btn_login.setEnabled(True)
            self.btn_logout.setEnabled(False)
            self.btn_upload.setEnabled(False)
            self.btn_download.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.btn_sync_up.setEnabled(False)
            self.btn_sync_down.setEnabled(False)
            
            # Limpiar tabla
            self.table_files.setRowCount(0)
            
            self.label_user.setText("❌ No autenticado")
            self.label_storage.setText("---")
            self.label_status.setText("✅ Desconectado")
            
            QMessageBox.information(self, "Éxito", "Sesión cerrada exitosamente")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def upload_file(self):
        """Sube un archivo a Google Drive"""
        if not self.drive_service:
            QMessageBox.warning(self, "Advertencia", "Debes autenticarte primero")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar contrato para subir",
            "",
            "Todos (*);;PDF (*.pdf);;Imágenes (*.jpg *.png);;CSV (*.csv)"
        )
        
        if file_path:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(0)
            
            worker = GoogleDriveSyncWorker(
                self.drive_service,
                "upload",
                file_path,
                os.path.basename(file_path)
            )
            worker.finished.connect(self._on_upload_finished)
            worker.progress.connect(lambda msg: self.label_status.setText(msg))
            worker.start()
    
    def _on_upload_finished(self, success, message):
        """Callback cuando termina la subida"""
        self.progress_bar.setVisible(False)
        self.label_status.setText(message)
        if success:
            self.refresh_file_list()
    
    def download_file(self):
        """Descarga un archivo de Google Drive"""
        if not self.drive_service:
            QMessageBox.warning(self, "Advertencia", "Debes autenticarte primero")
            return
        
        selected_rows = self.table_files.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "Selecciona un archivo para descargar")
            return
        
        row = selected_rows[0].row()
        file_id = self.table_files.item(row, 4).text()
        file_name = self.table_files.item(row, 0).text()
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como",
            file_name
        )
        
        if save_path:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(0)
            
            worker = GoogleDriveSyncWorker(
                self.drive_service,
                "download",
                file_id,
                save_path
            )
            worker.finished.connect(
                lambda s, m: self._on_operation_finished(s, m)
            )
            worker.progress.connect(lambda msg: self.label_status.setText(msg))
            worker.start()
    
    def refresh_file_list(self):
        """Recarga la lista de archivos"""
        if not self.drive_service:
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)
        self.label_status.setText("⏳ Cargando archivos...")
        
        worker = GoogleDriveSyncWorker(self.drive_service, "list", limit=20)
        worker.files_updated.connect(self._on_files_loaded)
        worker.finished.connect(
            lambda s, m: self._on_operation_finished(s, m)
        )
        worker.start()
    
    def _on_files_loaded(self, files):
        """Actualiza la tabla con la lista de archivos"""
        self.table_files.setRowCount(len(files))
        
        for row, file in enumerate(files):
            # Nombre
            self.table_files.setItem(row, 0, QTableWidgetItem(file['name']))
            
            # Tamaño
            size_mb = round(int(file.get('size', 0)) / (1024**2), 2)
            self.table_files.setItem(row, 1, QTableWidgetItem(f"{size_mb} MB"))
            
            # Creado
            created = file.get('createdTime', '---')[:10]
            self.table_files.setItem(row, 2, QTableWidgetItem(created))
            
            # Modificado
            modified = file.get('modifiedTime', '---')[:10]
            self.table_files.setItem(row, 3, QTableWidgetItem(modified))
            
            # ID (oculto)
            self.table_files.setItem(row, 4, QTableWidgetItem(file['id']))
    
    def sync_to_drive(self):
        """Sincroniza carpeta local a Google Drive"""
        if not self.drive_service:
            QMessageBox.warning(self, "Advertencia", "Debes autenticarte primero")
            return
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta para sincronizar a nube"
        )
        
        if folder:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(0)
            self.label_status.setText("⏳ Sincronizando...")
            
            worker = GoogleDriveSyncWorker(
                self.drive_service,
                "sync_local_to_drive",
                folder
            )
            worker.finished.connect(
                lambda s, m: self._on_operation_finished(s, m)
            )
            worker.progress.connect(lambda msg: self.label_status.setText(msg))
            worker.start()
    
    def sync_from_drive(self):
        """Sincroniza Google Drive a carpeta local"""
        if not self.drive_service:
            QMessageBox.warning(self, "Advertencia", "Debes autenticarte primero")
            return
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta para descargar archivos"
        )
        
        if folder:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(0)
            self.label_status.setText("⏳ Descargando...")
            
            worker = GoogleDriveSyncWorker(
                self.drive_service,
                "sync_drive_to_local",
                folder
            )
            worker.finished.connect(
                lambda s, m: self._on_operation_finished(s, m)
            )
            worker.progress.connect(lambda msg: self.label_status.setText(msg))
            worker.start()
    
    def _on_operation_finished(self, success, message):
        """Callback cuando termina una operación"""
        self.progress_bar.setVisible(False)
        self.label_status.setText(message)
        self.refresh_file_list()
