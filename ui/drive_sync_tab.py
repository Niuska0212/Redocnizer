"""
Interfaz para la gestión de respaldo en la nube (Google Drive).
Módulo 3: Sistemas Distribuidos.
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QMessageBox,
    QFileDialog, QListView, QTreeView, QAbstractItemView,
    QApplication, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QColor

class DriveSyncTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.drive_service = None
        
        # Forzar fondo gris claro para toda la pestaña
        self.setObjectName("driveSyncTab")
        self.setStyleSheet("""
            #driveSyncTab {
                background-color: #f5f5f5;
            }
        """)
        
        self._init_ui()
        
        # Inicialización automática si existe el token
        try:
            from services.google_drive_service import GoogleDriveService
            if os.path.exists('token.json'):
                self.drive_service = GoogleDriveService()
                self._update_ui_logged_in()
        except Exception:
            pass

    def _init_ui(self):
        # Layout principal con scroll por si la ventana es pequeña
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- ESTILOS COMPARTIDOS ---
        card_style = """
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """
        
        button_primary = """
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1557b0; }
            QPushButton:pressed { background-color: #0d47a1; }
            QPushButton:disabled { background-color: #bdc1c6; }
        """

        button_secondary = """
            QPushButton {
                background-color: white;
                color: #5f6368;
                border: 1px solid #dadce0;
                border-radius: 8px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #f8f9fa; border-color: #bdc1c6; }
        """

        # --- SECCIÓN 1: ESTADO DE CUENTA ---
        self.status_card = QFrame()
        self.status_card.setStyleSheet(card_style)
        status_layout = QHBoxLayout(self.status_card)
        status_layout.setContentsMargins(20, 20, 20, 20)

        # Icono de Drive (Placeholder visual con texto)
        self.icon_label = QLabel("☁️")
        self.icon_label.setStyleSheet("font-size: 40px; margin-right: 10px; border: none;")
        status_layout.addWidget(self.icon_label)

        info_user_layout = QVBoxLayout()
        self.user_label = QLabel("Estado: Desconectado")
        self.user_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #202124; border: none;")
        
        self.email_label = QLabel("Inicia sesión para respaldar tus contratos automáticamente.")
        self.email_label.setStyleSheet("color: #5f6368; font-size: 13px; border: none;")
        
        info_user_layout.addWidget(self.user_label)
        info_user_layout.addWidget(self.email_label)
        status_layout.addLayout(info_user_layout)
        status_layout.addStretch()

        self.btn_login = QPushButton("🔑 Conectar Google Drive")
        self.btn_login.setStyleSheet(button_primary)
        self.btn_login.clicked.connect(self._handle_login)
        
        self.btn_logout = QPushButton("🚪 Cerrar Sesión")
        self.btn_logout.setStyleSheet(button_secondary)
        self.btn_logout.clicked.connect(self._handle_logout)
        self.btn_logout.setVisible(False)

        status_layout.addWidget(self.btn_login)
        status_layout.addWidget(self.btn_logout)

        # --- SECCIÓN 2: ALMACENAMIENTO ---
        self.storage_group = QFrame()
        self.storage_group.setStyleSheet(card_style)
        self.storage_group.setVisible(False)
        storage_layout = QVBoxLayout(self.storage_group)
        storage_layout.setContentsMargins(20, 20, 20, 20)

        storage_header = QLabel("📊 Uso de Almacenamiento")
        storage_header.setStyleSheet("font-weight: bold; color: #1a73e8; font-size: 15px; border: none;")
        
        self.progress_storage = QProgressBar()
        self.progress_storage.setFixedHeight(12)
        self.progress_storage.setStyleSheet("""
            QProgressBar {
                background-color: #e8eaed;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #34a853;
                border-radius: 6px;
            }
        """)
        
        self.storage_label = QLabel("Calculando espacio disponible...")
        self.storage_label.setStyleSheet("color: #5f6368; font-size: 12px; border: none;")

        storage_layout.addWidget(storage_header)
        storage_layout.addWidget(self.progress_storage)
        storage_layout.addWidget(self.storage_label)

        # --- SECCIÓN 3: ACCIONES MANUALES ---
        self.manual_group = QFrame()
        self.manual_group.setStyleSheet(card_style)
        self.manual_group.setVisible(False)
        manual_layout = QVBoxLayout(self.manual_group)
        manual_layout.setContentsMargins(20, 20, 20, 20)

        manual_title = QLabel("🛠️ Acciones de Respaldo Manual")
        manual_title.setStyleSheet("font-weight: bold; color: #1a73e8; font-size: 15px; border: none;")
        
        btn_layout = QHBoxLayout()
        self.btn_csv = QPushButton("📄 Sincronizar CSV")
        self.btn_csv.setToolTip("Sube el archivo de datos del calendario actual")
        self.btn_csv.setStyleSheet(button_secondary)
        self.btn_csv.clicked.connect(self._manual_backup_csv)

        self.btn_contracts = QPushButton("📁 Subir Carpeta de Contratos")
        self.btn_contracts.setToolTip("Selecciona una carpeta para subir PDFs faltantes")
        self.btn_contracts.setStyleSheet(button_secondary)
        self.btn_contracts.clicked.connect(self._manual_backup_contracts)
        
        btn_layout.addWidget(self.btn_csv)
        btn_layout.addWidget(self.btn_contracts)

        # Barra de progreso para subidas largas
        self.upload_progress = QProgressBar()
        self.upload_progress.setVisible(False)
        self.upload_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #1a73e8; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #1a73e8; }
        """)
        self.upload_status = QLabel("")
        self.upload_status.setStyleSheet("color: #1a73e8; font-size: 11px; border: none;")

        manual_layout.addWidget(manual_title)
        manual_layout.addLayout(btn_layout)
        manual_layout.addWidget(self.upload_progress)
        manual_layout.addWidget(self.upload_status)

        # --- SECCIÓN 4: RECUPERACIÓN (CRÍTICA) ---
        self.recovery_card = QFrame()
        self.recovery_card.setStyleSheet("""
            QFrame {
                background-color: #fdf2f2;
                border-radius: 15px;
                border: 1px solid #f8b4b4;
            }
        """)
        recovery_layout = QHBoxLayout(self.recovery_card)
        recovery_layout.setContentsMargins(20, 15, 20, 15)
        
        rec_text_layout = QVBoxLayout()
        rec_title = QLabel("⚡ Recuperación de Emergencia")
        rec_title.setStyleSheet("font-weight: bold; color: #9b1c1c; border: none;")
        rec_desc = QLabel("Descarga la última base de datos desde Supabase.")
        rec_desc.setStyleSheet("color: #c81e1e; font-size: 11px; border: none;")
        rec_text_layout.addWidget(rec_title)
        rec_text_layout.addWidget(rec_desc)
        
        self.btn_restore_cloud = QPushButton("Restaurar Datos")
        self.btn_restore_cloud.setCursor(Qt.PointingHandCursor)
        self.btn_restore_cloud.clicked.connect(self.restore_from_supabase)
        self.btn_restore_cloud.setStyleSheet("""
            QPushButton {
                background-color: #e02424;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c81e1e; }
        """)
        
        recovery_layout.addLayout(rec_text_layout)
        recovery_layout.addStretch()
        recovery_layout.addWidget(self.btn_restore_cloud)

        # --- INFO FOOTER ---
        info_label = QLabel(
            "ℹ️ <b>Información:</b> Los contratos procesados se suben automáticamente a Google Drive "
            "en la carpeta 'Redocnizer'. Los archivos PDF duplicados se omiten para ahorrar espacio."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #70757a; font-size: 12px; margin-top: 10px;")

        # Ensamblar
        layout.addWidget(self.status_card)
        layout.addWidget(self.storage_group)
        layout.addWidget(self.manual_group)
        layout.addWidget(self.recovery_card)
        layout.addWidget(info_label)
        layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    # --- LÓGICA DE FUNCIONES (SIN CAMBIOS EN FUNCIONALIDAD) ---

    def _handle_login(self):
        self.btn_login.setText("⌛ Conectando...")
        self.btn_login.setEnabled(False)
        QApplication.processEvents()
        
        try:
            from services.google_drive_service import GoogleDriveService
            self.drive_service = GoogleDriveService()
            if self.drive_service.service:
                self._update_ui_logged_in()
                QMessageBox.information(self, "Conexión Exitosa", "Se ha vinculado la cuenta de Google Drive correctamente.")
            else:
                raise Exception("El servicio no se inició correctamente.")
        except Exception as e:
            self.btn_login.setText("🔑 Conectar Google Drive")
            self.btn_login.setEnabled(True)
            QMessageBox.critical(self, "Error de Conexión", f"No se pudo conectar: {str(e)}")

    def _update_ui_logged_in(self):
        if not self.drive_service or not self.drive_service.service:
            return
            
        try:
            user = self.drive_service.get_user_info()
            storage = self.drive_service.get_storage_info()
            
            self.user_label.setText(f"Usuario: {user['nombre']}")
            self.email_label.setText(f"Conectado como: {user['email']}")
            
            self.progress_storage.setValue(int(storage['porcentaje']))
            self.storage_label.setText(f"Uso: {storage['usado_gb']} GB de {storage['total_gb']} GB disponibles")
            
            self.storage_group.setVisible(True)
            self.manual_group.setVisible(True)
            self.btn_login.setVisible(False)
            self.btn_logout.setVisible(True)
            self.icon_label.setText("☁️✅")
            
        except Exception as e:
            print(f"Error actualizando UI: {e}")

    def _handle_logout(self):
        confirm = QMessageBox.question(
            self, "Cerrar Sesión",
            "¿Estás seguro de que deseas desvincular Google Drive de esta aplicación?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if os.path.exists('token.json'):
                    os.remove('token.json')
                self.drive_service = None
                
                # Reset UI
                self.user_label.setText("Estado: Desconectado")
                self.email_label.setText("Inicia sesión para respaldar tus contratos automáticamente.")
                self.btn_login.setVisible(True)
                self.btn_login.setEnabled(True)
                self.btn_login.setText("🔑 Conectar Google Drive")
                self.btn_logout.setVisible(False)
                self.storage_group.setVisible(False)
                self.manual_group.setVisible(False)
                self.icon_label.setText("☁️")
                
                QMessageBox.information(self, "Sesión Finalizada", "La cuenta ha sido desvinculada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cerrar sesión: {e}")

    def _manual_backup_csv(self):
        if not self.drive_service: return
        calendar = self.main_window.calendar_combo.currentText()
        cal_dir = self.main_window.controller.file_service.get_calendar_dir("")
        csv_path = os.path.join(cal_dir, f"{calendar}.csv")
        
        if not os.path.exists(csv_path):
            QMessageBox.warning(self, "No encontrado", f"No existe el archivo local: {calendar}.csv")
            return
            
        try:
            self.drive_service.upload_to_path(csv_path, drive_root='Redocnizer', calendar=calendar, subfolder_path="")
            QMessageBox.information(self, "Éxito", "El archivo CSV ha sido actualizado en la nube.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _manual_backup_contracts(self):
        if not self.drive_service: return
        
        dlg = QFileDialog(self, "Seleccionar carpetas de contratos", self.main_window.root_dir or "")
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        
        list_view = dlg.findChild(QListView, "listView")
        if list_view: list_view.setSelectionMode(QAbstractItemView.MultiSelection)
        tree_view = dlg.findChild(QTreeView)
        if tree_view: tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if not dlg.exec(): return
        folders = dlg.selectedFiles()
        if not folders: return

        calendar = self.main_window.calendar_combo.currentText()
        self.upload_progress.setVisible(True)
        self.upload_progress.setValue(0)
        self.upload_status.setText("Escaneando archivos...")
        QApplication.processEvents()

        total_uploaded = 0
        total_skipped = 0
        
        for folder in folders:
            try:
                summary = self.drive_service.upload_folder(folder, drive_root='Redocnizer', subfolder=calendar)
                total_uploaded += summary.get('uploaded', 0)
                total_skipped += summary.get('skipped', 0)
            except Exception as e:
                print(f"Error en carpeta {folder}: {e}")

        self.upload_progress.setValue(100)
        self.upload_status.setText(f"Finalizado: {total_uploaded} subidos, {total_skipped} omitidos.")
        QMessageBox.information(self, "Respaldo Manual", f"Proceso terminado.\nSubidos: {total_uploaded}\nOmitidos (duplicados): {total_skipped}")
        self.upload_progress.setVisible(False)

    def restore_from_supabase(self):
        import pandas as pd
        confirm = QMessageBox.question(
            self, "Confirmar Restauración",
            "ADVERTENCIA: Esto reemplazará tu base de datos local con la información de Supabase.\n\n¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                data = self.main_window.supabase_manager.fetch_all_data()
                if data:
                    df_cloud = pd.DataFrame(data)
                    self.main_window.data_manager.set_dataframe(df_cloud)
                    self.main_window.data_manager.save_to_csv()
                    QMessageBox.information(self, "Recuperación Exitosa", f"Se han restaurado {len(df_cloud)} registros.")
                else:
                    QMessageBox.warning(self, "Sin Datos", "No se encontraron registros en la nube para restaurar.")
            except Exception as e:
                QMessageBox.critical(self, "Error de Restauración", f"Error: {e}")