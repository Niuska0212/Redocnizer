# ui/main_window.py

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox,
    QLabel, QPushButton, QComboBox, QVBoxLayout,
    QHBoxLayout, QLineEdit
)
from PySide6.QtCore import Qt

from controllers.contract_controller import ContractController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de OCR de Contratos")
        self.resize(700, 400)

        # -----------------------------------------
        # ESTADO DE LA APLICACIÓN
        # -----------------------------------------
        self.root_dir = ""
        self.preview_dir = os.path.join(os.getcwd(), "previews")

        os.makedirs(self.preview_dir, exist_ok=True)

        self.controller = None
        self.selected_file = None

        # -----------------------------------------
        # UI
        # -----------------------------------------
        self._build_ui()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
 
        # -------- Directorio raíz --------
        root_layout = QHBoxLayout()

        self.root_input = QLineEdit()
        self.root_input.setReadOnly(True)

        btn_root = QPushButton("Seleccionar directorio raíz")
        btn_root.clicked.connect(self.select_root_directory)

        root_layout.addWidget(QLabel("Directorio raíz:"))
        root_layout.addWidget(self.root_input)
        root_layout.addWidget(btn_root)

        # -------- Calendario --------
        calendar_layout = QHBoxLayout()

        self.calendar_combo = QComboBox()
        self.calendar_combo.addItems([
            "2024A", "2024B",
            "2025A", "2025B",
            "2026A", "2026B",
            "2027A", "2027B",
            "2028A", "2028B",
            "2029A", "2029B",
        ])

        calendar_layout.addWidget(QLabel("Calendario:"))
        calendar_layout.addWidget(self.calendar_combo)

        # -------- Archivo --------
        file_layout = QHBoxLayout()

        self.file_label = QLabel("Ningún archivo seleccionado")
        self.file_label.setStyleSheet("color: gray")

        btn_file = QPushButton("Subir contrato")
        btn_file.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(btn_file)

        # -------- Procesar --------
        self.btn_process = QPushButton("Procesar contrato")
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_contract)

        # -------- Ensamblar --------
        layout.addLayout(root_layout)
        layout.addLayout(calendar_layout)
        layout.addLayout(file_layout)
        layout.addStretch()
        layout.addWidget(self.btn_process, alignment=Qt.AlignRight)

        central.setLayout(layout)
        self.setCentralWidget(central)

    # =========================================================
    # ACCIONES
    # =========================================================

    def select_root_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar directorio raíz"
        )

        if not directory:
            return

        self.root_dir = directory
        self.root_input.setText(directory)

        # Inicializar controlador SOLO cuando hay raíz
        self.controller = ContractController(
            root_dir=self.root_dir,
            preview_dir=self.preview_dir
        )

        self._update_process_state()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar contrato",
            "",
            "Documentos (*.pdf *.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        self.selected_file = file_path
        self.file_label.setText(os.path.basename(file_path))
        self.file_label.setStyleSheet("color: black")

        self._update_process_state()

    def _update_process_state(self):
        """
        Habilita el botón de procesar solo si:
        - Hay directorio raíz
        - Hay archivo seleccionado
        """
        self.btn_process.setEnabled(
            bool(self.root_dir and self.selected_file)
        )

    # =========================================================
    # PROCESAMIENTO
    # =========================================================

    def process_contract(self):
        try:
            calendar = self.calendar_combo.currentText()

            result = self.controller.process_uploaded_file(
                file_path=self.selected_file,
                calendar=calendar
            )

            data = result["data"]
            final_path = result["final_path"]

            QMessageBox.information(
                self,
                "Proceso completado",
                (
                    "Contrato procesado correctamente.\n\n"
                    f"CÓDIGO: {data.get('CODIGO')}\n"
                    f"NÚMERO: {data.get('NUM')}\n\n"
                    f"Guardado en:\n{final_path}"
                )
            )

            # Reset
            self.selected_file = None
            self.file_label.setText("Ningún archivo seleccionado")
            self.file_label.setStyleSheet("color: gray")
            self.btn_process.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )
