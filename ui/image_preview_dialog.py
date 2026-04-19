import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QFileDialog, QMessageBox,
    QAbstractItemView, QDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize
from PySide6.QtGui import QPixmap, QColor, QBrush, QWheelEvent, QMouseEvent

from ui.history_manager import HistoryManager
# from ui.edit_record_dialog import EditRecordDialog
from ui.file_watcher import FileWatcher

class ImagePreviewDialog(QDialog):
    """Visor de imágenes con soporte para Zoom y Desplazamiento."""
    def __init__(self, pixmap, title="Vista Previa del Documento", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.original_pixmap = pixmap
        self.zoom_factor = 1.0
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Instrucciones
        info_label = QLabel("💡 Usa la rueda del ratón para Zoom | Arrastra para mover")
        info_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(info_label)

        # Área de desplazamiento
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #2.2.3b; border: 1px solid #333;")

        # Label contenedor de la imagen
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(self.original_pixmap)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        # Botones de control
        btn_layout = QHBoxLayout()
        btn_reset = QPushButton("Restablecer Vista")
        btn_reset.clicked.connect(self.reset_zoom)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        # Variables para el arrastre
        self.last_mouse_pos = QPoint()

    def wheelEvent(self, event: QWheelEvent):
        """Maneja el zoom con la rueda del ratón."""
        if event.angleDelta().y() > 0:
            self.zoom_factor *= 1.15
        else:
            self.zoom_factor /= 1.15
            
        self.update_view()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.last_mouse_pos.isNull():
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            
            # Mover las barras de scroll
            h_bar = self.scroll_area.horizontalScrollBar()
            v_bar = self.scroll_area.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.last_mouse_pos = QPoint()
        self.setCursor(Qt.ArrowCursor)

    def update_view(self):
        """Actualiza el tamaño del label según el factor de zoom."""
        new_size = self.original_pixmap.size() * self.zoom_factor
        scaled_pixmap = self.original_pixmap.scaled(
            new_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.adjustSize()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_view()

