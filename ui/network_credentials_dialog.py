import subprocess
import os
import string
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class NetworkCredentialsDialog(QDialog):
    """
    Diálogo para solicitar credenciales de red compartida (UNC path).
    """
    
    def __init__(self, parent=None, network_path: str = ""):
        super().__init__(parent)
        self.network_path = network_path
        # En lugar de dejar Z fija, buscamos la mejor letra disponible
        self.drive_letter = self._get_first_available_drive()
        self.success = False
        
        self.setWindowTitle("Autenticación de Red")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()

    def _get_first_available_drive(self) -> str:
        """Busca letras disponibles desde la Z hacia la A."""
        # Obtener letras en uso (C:, D:, etc.)
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        
        # Revisar de Z a G (evitando las primeras letras que suelen ser locales)
        for letter in reversed(string.ascii_uppercase):
            if not (bitmask & (1 << (ord(letter) - ord('A')))):
                return letter
        return "Z" # Fallback por si acaso

        
    def _build_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Acceso a Red Compartida")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Información de la ruta
        info = QLabel(f"Se requiere autenticación para acceder a:\n\n{self.network_path}")
        info.setWordWrap(True)
        info.setStyleSheet("color: #555; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Letra de Unidad
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Mapear como unidad:"))
        self.drive_input = QLineEdit(self.drive_letter)
        self.drive_input.setMaximumWidth(40)
        self.drive_input.setAlignment(Qt.AlignCenter)
        drive_layout.addWidget(self.drive_input)
        drive_layout.addStretch()
        layout.addLayout(drive_layout)
        
        # Usuario
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario")
        layout.addWidget(self.user_input)
        
        # Contraseña
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("Contraseña")
        layout.addWidget(self.pass_input)

        # Opción de conexión persistente
        self.persistent_check = QCheckBox("Recordar esta conexión")
        self.persistent_check.setChecked(True)
        layout.addWidget(self.persistent_check)

        # Botones
        btn_layout = QHBoxLayout()
        btn_connect = QPushButton("🔗 Conectar")
        btn_connect.clicked.connect(self._connect)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_connect)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def _connect(self):
        """Intenta mapear la unidad de red con las credenciales proporcionadas."""
        user = self.user_input.text().strip()
        password = self.pass_input.text()
        drive = self.drive_input.text().strip().upper()
        persistent = "/persistent:yes" if self.persistent_check.isChecked() else "/persistent:no"
        
        if not user or not password:
            QMessageBox.warning(self, "Campos incompletos", "Ingresa usuario y contraseña.")
            return
        
        if not drive or len(drive) != 1:
            QMessageBox.warning(self, "Unidad inválida", "Especifica una sola letra (ej: Z)")
            return
        
        # Construir comando net use
        # Formato: net use Z: "\\servidor\recurso" /user:dominio\usuario contraseña /persistent:yes
        cmd = f'net use {drive}: "{self.network_path}" /user:{user} "{password}" {persistent}'
        
        try:
            # Ejecutar con shell
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.success = True
                QMessageBox.information(
                    self,
                    "Conexión exitosa",
                    f"Unidad de red mapeada como {drive}:\n\n{self.network_path}"
                )
                self.accept()
            else:
                error_msg = result.stderr if result.stderr else "Error desconocido"
                QMessageBox.critical(
                    self,
                    "Error de conexión",
                    f"No se pudo conectar a la red:\n\n{error_msg}"
                )
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Timeout", "La conexión tardó demasiado tiempo.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")
    
    def get_mapped_drive(self) -> str:
        """Retorna la letra de la unidad mapeada."""
        if self.success:
            return f"{self.drive_input.text().upper()}:\\"
        return ""
