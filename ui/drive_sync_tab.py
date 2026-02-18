# ui/drive_sync_tab.py
"""
Interfaz para la gestión de respaldo en la nube (Google Drive).
Módulo 3: Sistemas Distribuidos.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os

class DriveSyncTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.drive_service = None
        self._init_ui()

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
        
        self.email_label = QLabel("Inicia sesión para respaldar tus contratos")
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
        
        storage_title = QLabel("Uso de Almacenamiento Distribuido")
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
        
        storage_layout.addWidget(storage_title)
        storage_layout.addWidget(self.progress_storage)
        storage_layout.addWidget(self.storage_label)

        # Agregar al layout principal
        layout.addWidget(self.status_card)
        layout.addWidget(self.storage_group)
        layout.addStretch()

    def _handle_login(self):
        """Intenta conectar con el servicio de Google Drive."""
        try:
            from services.google_drive_service import GoogleDriveService
            self.drive_service = GoogleDriveService()
            self._update_ui_logged_in()
            QMessageBox.information(self, "Éxito", "Conexión con Google Cloud establecida.")
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

    def upload_backup(self, file_path):
        """Método para ser llamado desde la ventana principal tras procesar un archivo."""
        if not self.drive_service:
            return
        
        try:
            self.drive_service.upload_file(file_path)
            print(f"Respaldo en la nube completado para: {file_path}")
        except Exception as e:
            print(f"Error al subir respaldo: {e}")