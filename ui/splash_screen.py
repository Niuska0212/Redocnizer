# ui/splash_screen.py

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class SplashScreen(QWidget):
    """Ventana de presentación que se muestra mientras se carga la IA y pesadeces de TensorFlow."""
    def __init__(self):
        super().__init__()
        # Sin bordes y siempre al frente
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Tamaño fijo para la presentación
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Contenedor principal con diseño redondeado
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 2px solid #1976d2;
            }
        """)
        frame_layout = QVBoxLayout(self.frame)
        
        # Logo de REDOCNIZER
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo_redocnizer.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        
        # Mensaje de estado
        self.label = QLabel("REDOCNIZER\nCargando inteligencia artificial...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0b2545; border: none;")
        
        # Barra de progreso "infinita" (indeterminada)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) 
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 5px;
                height: 10px;
                background: #eee;
            }
            QProgressBar::chunk {
                background-color: #6a1b9a;
                width: 20px;
            }
        """)
        
        frame_layout.addStretch()
        frame_layout.addWidget(self.logo_label)
        frame_layout.addWidget(self.label)
        frame_layout.addWidget(self.progress)
        frame_layout.addStretch()
        
        layout.addWidget(self.frame)
        
        # Centrar automáticamente en la pantalla del usuario
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)