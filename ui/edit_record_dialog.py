# ui/edit_record_dialog.py
"""Diálogo para editar registros con el estilo visual de REDOCNIZER."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QMessageBox, QFormLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import pandas as pd
import os


class EditRecordDialog(QDialog):
    """Diálogo modal estilizado para editar todos los campos de un registro."""
    
    def __init__(self, parent=None, row_data: dict = None, column_names: list = None):
        super().__init__(parent)
        self.row_data = row_data or {}
        self.column_names = column_names or []
        self.fields = {}
        
        self.setWindowTitle("REDOCNIZER - Editor de Registro")
        self.resize(650, 550)
        
        self.setup_ui()
        self.apply_styles()
        self.populate_fields()
    
    def setup_ui(self):
        """Configura la estructura de la interfaz siguiendo el estilo principal."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- CABECERA ESTILIZADA ---
        header_frame = QFrame()
        header_frame.setObjectName("header_frame")
        header_frame.setMinimumHeight(70)
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("📝 Edición de Datos de Contrato")
        title_label.setObjectName("header_title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addWidget(header_frame)

        # --- CUERPO (SCROLL AREA) ---
        container = QWidget()
        container.setObjectName("body_container")
        body_layout = QVBoxLayout(container)
        body_layout.setContentsMargins(20, 10, 20, 20)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setObjectName("scroll_area")
        
        # El widget que contiene los campos
        self.form_widget = QWidget()
        self.form_widget.setObjectName("form_inner_widget")
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setSpacing(15)
        self.form_layout.setContentsMargins(10, 10, 30, 10)
        
        # Crear campos dinámicamente
        for col in self.column_names:
            label = QLabel(col)
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Ingrese {col.lower()}...")
            
            self.form_layout.addRow(label, line_edit)
            self.fields[col] = line_edit
        
        self.scroll_area.setWidget(self.form_widget)
        body_layout.addWidget(self.scroll_area)
        
        # --- PIE (BOTONES) ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        btn_clear = QPushButton("🗑️ Limpiar Todo")
        btn_clear.setObjectName("btn_clear")
        btn_clear.clicked.connect(self.clear_all_fields)
        
        btn_cancel = QPushButton("❌ Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.accept)
        
        footer_layout.addWidget(btn_clear)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_cancel)
        footer_layout.addWidget(btn_save)
        
        body_layout.addLayout(footer_layout)
        main_layout.addWidget(container)

    def apply_styles(self):
        """Aplica el CSS basado en el estilo minimalista de MainWindow."""
        self.setStyleSheet("""
            /* Fondo General */
            QDialog {
                background-color: #f6f8fb;
            }
            
            /* Cabecera */
            QFrame#header_frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #6a1b9a);
            }
            
            QLabel#header_title {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding-left: 10px;
            }
            
            /* Contenedor del Cuerpo */
            QWidget#body_container {
                background-color: #f6f8fb;
            }
            
            /* Área de Scroll */
            QScrollArea {
                background-color: transparent;
                border: 1px solid #e3e7ee;
                border-radius: 8px;
            }
            
            QWidget#form_inner_widget {
                background-color: white;
            }

            /* Labels de los campos */
            QLabel {
                color: #0b2545;
                font-weight: 600;
                font-size: 13px;
            }

            /* Inputs (Basados en el estilo de MainWindow) */
            QLineEdit {
                padding: 10px;
                border: 1px solid #e3e7ee;
                border-radius: 6px;
                background-color: #ffffff;
                color: #0b2545;
            }
            
            QLineEdit:focus {
                border: 2px solid #1976d2;
                background-color: #f9fbfd;
            }

            /* Botones Estilo Principal */
            QPushButton#btn_primary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1976d2, stop:1 #6a1b9a);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QPushButton#btn_secondary {
                background: #cfd8e3;
                color: #0b2545;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }

            QPushButton#btn_clear {
                background: transparent;
                color: #7a8aa3;
                border: 1px solid #cfd8e3;
                padding: 8px 15px;
                border-radius: 6px;
            }
            
            QPushButton:hover {
                opacity: 0.9;
            }
            
            QPushButton#btn_clear:hover {
                background-color: #fff0f0;
                color: #d32f2f;
                border-color: #d32f2f;
            }

            /* ScrollBar estilizada */
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #cfd8e3;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #1976d2;
            }
        """)

    def populate_fields(self):
        """Rellena los campos con los datos del registro."""
        for col in self.column_names:
            value = self.row_data.get(col, "")
            if pd.isna(value):
                value = ""
            if col in self.fields:
                self.fields[col].setText(str(value))
    
    def clear_all_fields(self):
        """Limpia todos los campos con confirmación."""
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Desea limpiar todos los campos del formulario?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for field in self.fields.values():
                field.setText("")
    
    def get_edited_data(self) -> dict:
        """Retorna un diccionario con los datos limpios."""
        data = {}
        for col, field in self.fields.items():
            data[col] = field.text().strip()
        return data
    
    @staticmethod
    def edit_record(parent=None, row_data: dict = None, column_names: list = None) -> tuple:
        """
        Método estático para invocar el diálogo.
        Retorna: (True si guardó, datos_editados)
        """
        dialog = EditRecordDialog(parent, row_data, column_names)
        accepted = (dialog.exec() == QDialog.Accepted)
        edited_data = dialog.get_edited_data() if accepted else {}
        return accepted, edited_data