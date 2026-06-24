#!/usr/bin/env python3
"""
Migra contenido de carpetas NOMBRAMIENTOS a 06 NOMBRAMIENTOS con Interfaz Gráfica.
"""

import os
import shutil
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)


def normalize_path(value: str) -> str:
    if not value:
        return value
    return os.path.normpath(value.strip())


def find_nombramientos_dirs(root_dir: str):
    for current_dir, dirnames, _ in os.walk(root_dir):
        if os.path.basename(current_dir).strip().upper() == "NOMBRAMIENTOS":
            yield current_dir


def move_contents(old_dir: str, new_dir: str):
    moved = 0
    overwritten = 0

    os.makedirs(new_dir, exist_ok=True)

    for root, _, files in os.walk(old_dir):
        rel_path = os.path.relpath(root, old_dir)
        destination_root = (
            new_dir if rel_path == "." else os.path.join(new_dir, rel_path)
        )
        os.makedirs(destination_root, exist_ok=True)

        for filename in files:
            source_path = os.path.join(root, filename)
            destination_path = os.path.join(destination_root, filename)

            if os.path.exists(destination_path):
                os.remove(destination_path)
                overwritten += 1

            shutil.move(source_path, destination_path)
            moved += 1

    return moved, overwritten


def cleanup_empty_dirs(start_dir: str):
    removed = 0
    for root, dirs, files in os.walk(start_dir, topdown=False):
        if not dirs and not files:
            try:
                os.rmdir(root)
                removed += 1
            except OSError:
                pass
    return removed


class MigrationWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Migrador de Carpetas de Contratos")
        self.setMinimumSize(650, 450)
        self.init_ui()

    def init_ui(self):
        # Widget Central y Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        # Instrucciones
        instruction_label = QLabel(
            "Selecciona la carpeta raíz donde están los expedientes de los profesores.\n"
            "El script buscará las carpetas llamadas 'NOMBRAMIENTOS' para mover su contenido a '06 NOMBRAMIENTOS'."
        )
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        # Selector de Ruta (Layout Horizontal)
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(
            "Ruta de la carpeta raíz (ej. Z:\\000_Archivo\\000_expedientes_cper)"
        )

        browse_button = QPushButton("Buscar...")
        browse_button.clicked.connect(self.browse_folder)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        main_layout.addLayout(path_layout)

        # Botón de Acción Principal
        self.run_button = QPushButton("Iniciar Migración")
        self.run_button.setStyleSheet(
            "font-weight: bold; background-color: #2b579a; color: white; padding: 8px;"
        )
        self.run_button.clicked.connect(self.start_migration)
        main_layout.addWidget(self.run_button)

        # Consola de Estado / Logs
        log_label = QLabel("Progreso del proceso:")
        main_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, Monaco, monospace;"
        )
        main_layout.addWidget(self.log_output)

    def browse_folder(self):
        selected_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta Raíz de Expedientes"
        )
        if selected_dir:
            self.path_input.setText(os.path.normpath(selected_dir))

    def log(self, text: str):
        self.log_output.append(text)
        # Auto-scroll hacia abajo
        self.log_output.ensureCursorVisible()

    def start_migration(self):
        root_dir = normalize_path(self.path_input.text())

        if not root_dir or not os.path.isdir(root_dir):
            QMessageBox.critical(
                self,
                "Error de Ruta",
                "Por favor, selecciona una ruta de carpeta válida antes de continuar.",
            )
            return

        self.log_output.clear()
        self.log(f"[*] Iniciando búsqueda en: {root_dir}")
        self.run_button.setEnabled(False)
        QApplication.processEvents()  # Forzar actualización de la UI

        try:
            summary = []
            for old_dir in find_nombramientos_dirs(root_dir):
                parent_path = os.path.dirname(old_dir)
                new_dir = os.path.join(parent_path, "06 NOMBRAMIENTOS")

                self.log(f"\n[->] Procesando: {old_dir}")

                moved, overwritten = move_contents(old_dir, new_dir)
                removed_dirs = cleanup_empty_dirs(old_dir)

                self.log(f"    - Movidos: {moved} archivos.")
                if overwritten > 0:
                    self.log(f"    - Sobrescritos: {overwritten} archivos.")
                if removed_dirs > 0:
                    self.log(
                        f"    - Removida carpeta antigua (quedó vacía)."
                    )

                summary.append(
                    {
                        "old_dir": old_dir,
                        "new_dir": new_dir,
                        "moved": moved,
                        "overwritten": overwritten,
                        "removed_empty_dirs": removed_dirs,
                    }
                )

            self.log("\n" + "=" * 40)
            if not summary:
                self.log("\n[!] No se encontró ninguna carpeta 'NOMBRAMIENTOS'.")
                QMessageBox.information(
                    self,
                    "Proceso Terminado",
                    "No se encontraron carpetas para migrar.",
                )
            else:
                self.log(
                    f"\n[+] Migración finalizada con éxito. Se procesaron {len(summary)} carpetas."
                )
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"¡Migración completada!\nSe actualizaron {len(summary)} rutas.",
                )

        except Exception as e:
            self.log(f"\n[ERROR] Ocurrió un fallo: {str(e)}")
            QMessageBox.critical(
                self,
                "Error en Ejecución",
                f"Ocurrió un error inesperado durante la migración:\n{str(e)}",
            )

        finally:
            self.run_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MigrationWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()