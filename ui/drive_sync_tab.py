# ui/drive_sync_tab.py
"""
Interfaz para la gestión de respaldo en la nube (Google Drive).
Módulo 3: Sistemas Distribuidos.

Los respaldos se realizan automáticamente en background al procesar contratos.
Esta pestaña solo muestra estado de autenticación y uso de almacenamiento.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QMessageBox,
    QFileDialog, QListView, QTreeView, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import os

class DriveSyncTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.drive_service = None
        self._init_ui()
        # Inicialización automática de Google Drive si el token existe
        try:
            from services.google_drive_service import GoogleDriveService
            import os
            if os.path.exists('token.json'):
                self.drive_service = GoogleDriveService()
                self._update_ui_logged_in()
        except Exception:
            pass

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Tarjeta de Estado de Conexión ---
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setStyleSheet("""
            #statusCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_layout = QVBoxLayout(self.status_card)
        
        self.user_label = QLabel("Estado: No conectado a la nube")
        self.user_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        
        self.email_label = QLabel("Conecta para habilitar respaldos automáticos en Google Drive")
        self.email_label.setStyleSheet("color: #666;")
        
        self.btn_login = QPushButton("🔑 Conectar Google Drive")
        self.btn_login.setMinimumHeight(40)
        self.btn_login.clicked.connect(self._handle_login)
        
        card_layout.addWidget(self.user_label)
        card_layout.addWidget(self.email_label)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.btn_login)

        # --- Sección de Almacenamiento ---
        self.storage_group = QFrame()
        self.storage_group.setVisible(False) # Se muestra solo al loguear
        storage_layout = QVBoxLayout(self.storage_group)
        
        storage_title = QLabel("Uso de Almacenamiento en Google Drive")
        storage_title.setStyleSheet("font-weight: bold; color: #1976d2;")
        
        self.progress_storage = QProgressBar()
        self.progress_storage.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
            }
        """)
        self.storage_label = QLabel("0 GB de 0 GB usados")
        # Barra de progreso para subida manual
        self.upload_progress = QProgressBar()
        self.upload_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #1976d2;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
            }
        """)
        self.upload_progress.setVisible(False)
        self.upload_status = QLabel("")
        self.upload_status.setStyleSheet("color: #1976d2; font-weight: bold;")

        self.manual_group = QFrame()
        self.manual_group.setVisible(False) # Se oculta hasta que se loguee
        manual_layout = QVBoxLayout(self.manual_group)
        
        manual_title = QLabel("Respaldo Manual")
        manual_title.setStyleSheet("font-weight: bold; color: #1976d2;")

        btn_csv = QPushButton("📄 Subir/Reemplazar CSV del Calendario")
        btn_csv.clicked.connect(self._manual_backup_csv)

        btn_contracts = QPushButton("📁 Subir Carpeta de Contratos (omitir duplicados)")
        btn_contracts.clicked.connect(self._manual_backup_contracts)

        manual_layout.addWidget(manual_title)
        manual_layout.addWidget(btn_csv)
        manual_layout.addWidget(btn_contracts)
        
        storage_layout.addWidget(storage_title)
        storage_layout.addWidget(self.progress_storage)
        storage_layout.addWidget(self.storage_label)
        storage_layout.addWidget(self.upload_progress)
        storage_layout.addWidget(self.upload_status)

        # --- Info sobre respaldos automáticos ---
        info_group = QFrame()
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel("ℹ️ Respaldos automáticos")
        info_label.setStyleSheet("font-weight: bold; color: #666;")
        desc_label = QLabel(
            "Los contratos se respaldan automáticamente en Google Drive al procesarlos.\n"
            "Estructura: backup/<CALENDARIO>/<CARPETA_PROFESOR>/...\n"
            "• PDFs: se suben sólo si no existen (se omiten duplicados)\n"
            "• CSVs: se reemplazan en cada actualización"
        )
        desc_label.setStyleSheet("color: #555; font-size: 12px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        info_layout.addWidget(desc_label)

        # Agregar al layout principal
        layout.addWidget(self.status_card)
        layout.addWidget(self.storage_group)
        layout.addWidget(self.manual_group)
        layout.addWidget(info_group)

        layout.addStretch()

    def _handle_login(self):
        """Intenta conectar con el servicio de Google Drive."""
        try:
            from services.google_drive_service import GoogleDriveService
            self.drive_service = GoogleDriveService()
            self._update_ui_logged_in()
            QMessageBox.information(self, "Éxito", "Conexión con Google Cloud establecida.\nLos respaldos automáticos están habilitados.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "No se encontró el archivo 'credentials.json'.\nPor favor, agrégalo a la carpeta raíz.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de autenticación: {str(e)}")

    def _update_ui_logged_in(self):
        """Actualiza la interfaz con la información del usuario."""
        if not self.drive_service:
            return
            
        user = self.drive_service.get_user_info()
        storage = self.drive_service.get_storage_info()
        
        self.user_label.setText(f"Bienvenido, {user['nombre']}")
        self.email_label.setText(user['email'])
        self.btn_login.setText("✅ Cuenta Vinculada")
        self.btn_login.setEnabled(False)
        
        self.progress_storage.setValue(int(storage['porcentaje']))
        self.storage_label.setText(f"{storage['usado_gb']} GB usados de {storage['total_gb']} GB")
        self.storage_group.setVisible(True)
        # habilitar controles manuales también
        self.manual_group.setVisible(True)

    def upload_backup(self, file_path):
        """Método para ser llamado desde la ventana principal tras procesar un archivo."""
        if not self.drive_service:
            return
        
        try:
            self.drive_service.upload_file(file_path)
            print(f"Respaldo en la nube completado para: {file_path}")
        except Exception as e:
            print(f"Error al subir respaldo: {e}")

    # ------------------------------------------------------------------
    # Métodos de respaldo manual invocados por los botones
    # ------------------------------------------------------------------
    def _manual_backup_csv(self):
        """Sube o reemplaza el 'contratos.csv' del calendario seleccionado."""
        if not self.drive_service:
            return
        calendar = self.main_window.calendar_combo.currentText()
        
        cal_dir = self.main_window.controller.file_service.get_calendar_dir("")
        csv_path = os.path.join(cal_dir, f"{calendar}.csv")
        
        if not os.path.exists(csv_path):
            QMessageBox.information(self, "Archivo no encontrado",
                f"No se encontró el archivo '{calendar}.csv' en la carpeta de calendarios.")
            return
        try:
            # Subir directamente a la raíz de 'Redocnizer' en Drive
            # Pasamos calendar para que el servicio de Drive sepa el nombre final
            self.drive_service.upload_to_path(
                csv_path, 
                drive_root='Redocnizer', 
                calendar=calendar, 
                subfolder_path=""
            )
            QMessageBox.information(self, "Respaldo completado",
                f"El archivo {calendar}.csv ha sido actualizado en Google Drive.")
        except Exception as e:
            QMessageBox.critical(self, "Error de subida", f"Error: {e}")

    def _manual_backup_contracts(self):
        """Permite elegir uno o varios PDFs para subir; los duplicados se omiten."""
        if not self.drive_service:
            return
        # Seleccionar una o varias carpetas locales (multi-select)
        dlg = QFileDialog(self, "Seleccionar carpeta(s) de contratos", self.main_window.root_dir or "")
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        # Habilitar selección múltiple en la vista interna
        list_view = dlg.findChild(QListView, "listView")
        tree_view = dlg.findChild(QTreeView)
        if list_view:
            list_view.setSelectionMode(QAbstractItemView.MultiSelection)
        if tree_view:
            tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if not dlg.exec():
            return
        folders = dlg.selectedFiles()
        if not folders:
            return

        calendar = self.main_window.calendar_combo.currentText()
        total_uploaded = 0
        total_skipped = 0
        total_errors = 0
        self.upload_progress.setVisible(True)
        self.upload_progress.setValue(0)
        self.upload_status.setText("Preparando subida de contratos...")
        QApplication.processEvents()
        print("[DEBUG] Ejecutando _manual_backup_contracts")
        if not self.drive_service:
            print("[DEBUG] drive_service es None")
            return
        # Seleccionar una o varias carpetas locales (multi-select)
        dlg = QFileDialog(self, "Seleccionar carpeta(s) de contratos", self.main_window.root_dir or "")
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        # Habilitar selección múltiple en la vista interna
        list_view = dlg.findChild(QListView, "listView")
        tree_view = dlg.findChild(QTreeView)
        if list_view:
            list_view.setSelectionMode(QAbstractItemView.MultiSelection)
        if tree_view:
            tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if not dlg.exec():
            print("[DEBUG] No se seleccionó ninguna carpeta")
            return
        folders = dlg.selectedFiles()
        print(f"[DEBUG] Carpetas seleccionadas: {folders}")
        if not folders:
            print("[DEBUG] Lista de carpetas vacía")
            return

        calendar = self.main_window.calendar_combo.currentText()
        print(f"[DEBUG] Calendario seleccionado: {calendar}")
        total_uploaded = 0
        total_skipped = 0
        total_errors = 0
        self.upload_progress.setVisible(True)
        self.upload_progress.setValue(0)
        self.upload_status.setText("Preparando subida de contratos...")
        QApplication.processEvents()
        total_files = 0
        for folder in folders:
            try:
                # Contar archivos a subir
                for root, dirs, files in os.walk(folder):
                    total_files += len([f for f in files if f.lower().endswith('.pdf') or f.lower().endswith('.csv')])
            except Exception:
                print(f"[DEBUG] Error al contar archivos en {folder}")
                pass
        uploaded_files = 0
        self.upload_status.setText("Subiendo contratos...")
        QApplication.processEvents()
        for folder in folders:
            print(f"[DEBUG] Subiendo carpeta: {folder}")
            try:
                summary = self.drive_service.upload_folder(folder, drive_root='Redocnizer', subfolder=calendar)
                print(f"[DEBUG] Resumen subida: {summary}")
                uploaded_files += summary.get('uploaded', 0)
                total_uploaded += summary.get('uploaded', 0)
                total_skipped += summary.get('skipped', 0)
                total_errors += summary.get('errors', 0)
                # Actualizar barra de progreso de subida
                if total_files > 0:
                    progress = int((uploaded_files / total_files) * 100)
                    self.upload_progress.setValue(progress)
                    self.upload_status.setText(f"Subiendo: {uploaded_files}/{total_files} archivos...")
                    QApplication.processEvents()
            except Exception as e:
                print(f"[DEBUG] Error al subir carpeta {folder}: {e}")
                total_errors += 1
        self.upload_progress.setValue(100)
        self.upload_status.setText(f"Se subieron: {total_uploaded} - Omisos: {total_skipped} - Errores: {total_errors}")
        QApplication.processEvents()
        self.upload_progress.setVisible(False)
        QMessageBox.information(self, "Resultado",
                                f"Se subieron: {total_uploaded} - Omisos: {total_skipped} - Errores: {total_errors}")
    def _on_auto_toggle(self, state):
        if state:
            self._start_auto_timer()
        else:
            self._stop_auto_timer()

    def _on_interval_changed(self, value):
        if self.chk_auto.isChecked():
            self._start_auto_timer()

    def _start_auto_timer(self):
        interval_min = int(self.spin_interval.value())
        self.auto_timer.stop()
        self.auto_timer.start(interval_min * 60 * 1000)

    def _stop_auto_timer(self):
        try:
            self.auto_timer.stop()
        except Exception:
            pass

    def _on_auto_timer(self):
        # Ejecuta upload_folder para cada carpeta vigilada
        for folder, calendar in list(self.watched_folders.items()):
            try:
                self.drive_service.upload_folder(folder, drive_root='backup', subfolder=calendar)
            except Exception as e:
                print(f"Error en auto-upload para {folder}: {e}")