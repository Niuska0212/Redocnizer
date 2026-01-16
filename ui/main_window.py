# ui/main_window.py

import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox,
    QLabel, QPushButton, QComboBox, QVBoxLayout,
    QHBoxLayout, QLineEdit, QProgressBar, QListWidget, 
    QListWidgetItem, QApplication, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QStyleFactory,
    QTextEdit, QGroupBox, QSpinBox, QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QFont, QColor, QBrush, QIcon

from controllers.contract_controller import ContractController
from services.pdf_service import pdf_to_images
from ui.app_menu import create_app_menu
from ui.calendar_db import CalendarDB
from ui.data_manager import DataManager
from ui.data_tab import DataTab
from ui.drive_sync_tab import DriveSyncTab





class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("REDOCNIZER - Gestión de Contratos CUCEI")
        self.resize(1000, 700)
        
        # --------------------------------------
        #LOGO EN LA VENTANA de la aplicacion
        # --------------------------------------
        # 1. cargar la imagen del logo
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo_redocnizer.png')
        
        # 2. verifica que el archivo exista
        if os.path.isfile(logo_path):
            pixmap = QIcon(logo_path)
            
            # 3. Establecer el icono de la ventana
            self.setWindowIcon(pixmap)
        else:
            print(f"Advertencia: No se encontró el logo en {logo_path}")
        
        # -----------------------------------------
        # ESTADO DE LA APLICACIÓN
        # -----------------------------------------
        self.root_dir = ""
        self.preview_dir = os.path.join(os.getcwd(), "previews")
        os.makedirs(self.preview_dir, exist_ok=True)

        # Manager de datos
        self.data_manager = DataManager()
        
        self.controller = None
        self.selected_files = []

        # -----------------------------------------
        # UI PRINCIPAL
        # -----------------------------------------
        self._build_ui()
        # Crear y adjuntar la barra de menú (archivo/editar)
        try:
            create_app_menu(self)
        except Exception as e:
            print(f"No se pudo crear la barra de menú: {e}")
        
        # Estilo de la aplicación (tema minimalista - azules / morados)
        # Se asegura contraste de texto oscuro sobre fondos claros para legibilidad
        self.setStyleSheet("""
            /* Colores base */
            QMainWindow { background-color: #f6f8fb; color: #0b2545; }

            /* Barra de menú */
            QMenuBar { background: transparent; color: #0b2545; }
            QMenuBar::item { background: transparent; padding: 6px 12px; }
            QMenu { background: #ffffff; color: #0b2545; }

            /* Botones: minimalistas con acento azul/índigo */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1976d2, stop:1 #6a1b9a);
                color: white;
                border: none;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { opacity: 0.95; }
            QPushButton:disabled { background: #cfd8e3; color: #7a8aa3; }
            
            QTabWidget::pane {
                border: 1px solid #e3e7ee;
                border-radius: 8px;
                background: #e6e6e6;
                margin-top: 6px;
            }

        
            QMessageBox {
                background: #e6e6e6;
                margin-top: 6px;
            }
            
            QRadioButton {
                color: black;
                background: none;
                border: none;
            }

            QDialog {
                background: #e6e6e6;
                margin-top: 6px;
            }
            
            QTabBar::tab {
                background: #eef2f8;
                color: #0b2545;
                padding: 8px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                border: 1px solid #e3e7ee;
                font-weight: 600;
            }

            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 1px solid #ffffff;
            }

            QTabBar::tab:hover {
                background: #e6ecf5;
            }               

            /* Group boxes */
            QGroupBox {
                font-weight: 700;
                border: 1px solid rgba(25,118,210,0.12);
                border-radius: 8px;
                margin-top: 10px;
                padding: 12px;
                color: #0b2545;
                background: transparent;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }

            /* Inputs y selects: fondo blanco, texto oscuro */
            QLineEdit, QComboBox, QTextEdit {
                padding: 8px;
                border: 1px solid #e3e7ee;
                border-radius: 6px;
                background-color: #ffffff;
                color: #0b2545;
            }
            QLineEdit:disabled, QComboBox:disabled { background: #f2f5fa; color: #7a8aa3; }

            /* Labels y tablas: texto oscuro */
            QLabel { color: #0b2545; }
            QTableWidget, QTableView { background: #ffffff; color: #0b2545; gridline-color: #eef2f8; }
            QTableWidget::item { color: #0b2545; }
            QHeaderView::section { background: #f3f6fb; color: #0b2545; border: none; padding: 8px; }

            /* Listas */
            QListWidget { background: #ffffff; color: #0b2545; }
            QListWidget::item:selected { background-color: rgba(25,118,210,0.08); }

            /* Preview box */
            QLabel#preview_label { border: 2px dashed rgba(25,118,210,0.18); border-radius: 8px; background-color: #ffffff; color: #0b2545; }

            /* Progress */
            QProgressBar { border: 1px solid #e6eef8; border-radius: 6px; text-align: center; background: #ffffff; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #6a1b9a); border-radius: 6px; }

            /* Texto de ayuda/pequeño */
            QLabel[style="small"] { color: #7a8aa3; font-size: 12px; }
            
            /* Forzar que el Combo Box y sus listas sean siempre blancos */
            QComboBox {
                background-color: white !important;
                color: #0b2545;
                border: 1px solid #d1d9e6;
                border-radius: 6px;
                padding: 5px;
                selection-background-color: #eef2f8;
            }

            /* El fondo de la lista desplegable */
            QComboBox QAbstractItemView {
                background-color: white;
                color: #0b2545;
                selection-background-color: #1976d2;
                selection-color: white;
                border: 1px solid #d1d9e6;
                outline: 0px;
            }

            /* Campos de entrada (incluyendo la nueva barra de búsqueda) */
            QLineEdit {
                background-color: white;
                color: #0b2545;
                border: 1px solid #d1d9e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):
        # Widget principal con pestañas
        self.tabs = QTabWidget()
        
        # Pestaña 1: Procesamiento
        self.processing_tab = self._build_processing_tab()
        self.tabs.addTab(self.processing_tab, "📄 Procesar Contratos")
        
        # Pestaña 2: Datos
        self.data_tab = DataTab(self.data_manager)
        self.tabs.addTab(self.data_tab, "📊 Ver/Editar Datos")
        
        # Pestaña 3: Google Drive (Módulo 3)
        self.drive_sync_tab = DriveSyncTab(self)
        self.tabs.addTab(self.drive_sync_tab, "☁️ Sincronización Nube")
        
        # Conectar cambio de pestaña para actualizar datos
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tabs)
    
    def _build_processing_tab(self):
        """Construye la pestaña de procesamiento"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        
        # -------- Grupo: Gestión y Búsqueda --------
        config_group = QGroupBox("Gestión y Búsqueda")
        config_layout = QVBoxLayout()
        
        # Barra de búsqueda integrada
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Buscar contratos por nombre, ID o fecha...")
        # Conectar con la lógica de filtrado
        self.search_bar.textChanged.connect(self._on_search_query_changed)
        search_layout.addWidget(self.search_bar)
        config_layout.addLayout(search_layout)
        
        # -------- Grupo: Configuración --------
        config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout()
        
        # Directorio raíz
        root_layout = QHBoxLayout()
        self.root_input = QLineEdit()
        self.root_input.setReadOnly(True)
        btn_root = QPushButton("📁 Seleccionar directorio raíz")
        btn_root.clicked.connect(self.select_root_directory)
        
        root_layout.addWidget(QLabel("Directorio raíz:"))
        root_layout.addWidget(self.root_input, 1)
        root_layout.addWidget(btn_root)
        config_layout.addLayout(root_layout)
        
        # Calendario
        calendar_layout = QHBoxLayout()
        self.calendar_combo = QComboBox()
        # Forzar estilo del popup del combo: fondo blanco y texto oscuro
        # Esto asegura legibilidad independientemente del tema del sistema
        self.calendar_combo.setStyleSheet(
            "QComboBox QAbstractItemView { background-color: #ffffff; color: #0b2545; "
            "selection-background-color: #e3f2fd; selection-color: #0b2545; }"
        )
        # Cargar calendarios desde la BD
        self.cal_db = CalendarDB()
        cals = self.cal_db.get_all_calendars()
        if cals:
            for cal in cals:
                self.calendar_combo.addItem(cal.nombre, cal)
            self.calendar_combo.setCurrentIndex(0)
        else:
            # Si no hay, cargar opciones default (legacy)
            self.calendar_combo.addItems([
                "2024A", "2024B",
                "2025A", "2025B",
                "2026A", "2026B",
                "2027A", "2027B",
                "2028A", "2028B",
                "2029A", "2029B",
            ])
            self.calendar_combo.setCurrentText("2024A")
        
        # Conectar cambio de calendario
        self.calendar_combo.currentIndexChanged.connect(self._on_calendar_changed)
        
        calendar_layout.addWidget(QLabel("Calendario:"))
        calendar_layout.addWidget(self.calendar_combo)
        # Botones rápidos para abrir CSV y carpeta del calendario
        self.btn_open_calendar_csv = QPushButton("Abrir CSV del calendario")
        self.btn_open_calendar_csv.setMaximumWidth(180)
        self.btn_open_calendar_csv.clicked.connect(self.open_calendar_csv)

        self.btn_open_calendar_folder = QPushButton("Abrir carpeta del calendario")
        self.btn_open_calendar_folder.setMaximumWidth(180)
        self.btn_open_calendar_folder.clicked.connect(self.open_calendar_folder)

        calendar_layout.addWidget(self.btn_open_calendar_csv)
        calendar_layout.addWidget(self.btn_open_calendar_folder)
        calendar_layout.addStretch()
        config_layout.addLayout(calendar_layout)
        
        config_group.setLayout(config_layout)
        
        # -------- Grupo: Archivos --------
        file_group = QGroupBox("Archivos a Procesar")
        file_layout = QHBoxLayout()
        
        # Panel izquierdo: Vista previa
        preview_panel = QVBoxLayout()
        preview_panel.setContentsMargins(0, 0, 10, 0)
        
        self.preview_label = QLabel()
        self.preview_label.setObjectName("preview_label")
        self.preview_label.setFixedSize(250, 350)
        # estilo específico para la vista previa: fondo blanco y texto oscuro
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed rgba(25,118,210,0.18);
                border-radius: 8px;
                background-color: #ffffff;
                color: #0b2545;
                qproperty-alignment: AlignCenter;
                font-weight: 600;
            }
        """)
        self.preview_label.setText("Vista previa\ndel documento")
        
        preview_panel.addWidget(self.preview_label)
        preview_panel.addStretch()
        
        # Panel derecho: Controles
        controls_panel = QVBoxLayout()
        
        # Información de archivos
        self.file_info_label = QLabel("Ningún archivo seleccionado")
        self.file_info_label.setStyleSheet("color: #666; font-size: 14px;")
        
        # Botones de archivos
        btn_layout = QHBoxLayout()
        self.btn_select_file = QPushButton("📎 Subir contrato(s)")
        self.btn_select_file.clicked.connect(self.select_file)
        self.btn_select_file.setMinimumHeight(40)
        
        self.btn_clear_files = QPushButton("🗑️ Limpiar")
        self.btn_clear_files.clicked.connect(self.clear_files)
        self.btn_clear_files.setMinimumHeight(40)
        self.btn_clear_files.setEnabled(False)

        # Botón para eliminar el archivo seleccionado individualmente
        self.btn_remove_file = QPushButton("➖ Eliminar seleccionado")
        self.btn_remove_file.clicked.connect(self.remove_selected_file)
        self.btn_remove_file.setMinimumHeight(40)
        self.btn_remove_file.setEnabled(False)
        
        btn_layout.addWidget(self.btn_select_file)
        btn_layout.addWidget(self.btn_clear_files)
        btn_layout.addWidget(self.btn_remove_file)
        
        # Lista de archivos
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: #0b2545;  /* Color del texto por defecto */
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
                color: #0b2545;  /* Color del texto del ítem */
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #0b2545;  /* Mantener texto negro cuando está seleccionado */
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
            }
        """)
        self.files_list.itemClicked.connect(self.on_file_selected)
        # Conectar cambio de selección para habilitar/deshabilitar botón eliminar
        self.files_list.itemSelectionChanged.connect(self._on_files_list_selection_changed)
        
        controls_panel.addWidget(self.file_info_label)
        controls_panel.addLayout(btn_layout)
        controls_panel.addWidget(self.files_list)
        controls_panel.addStretch()
        
        # Ensamblar layout de archivos
        file_layout.addLayout(preview_panel)
        file_layout.addLayout(controls_panel)
        file_group.setLayout(file_layout)
        
        # -------- Grupo: Progreso --------
        progress_group = QGroupBox("Progreso")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e6eef8;
                border-radius: 6px;
                text-align: center;
                background: #ffffff;
                color: #1a237e;  /* Azul oscuro */
                font-weight: 700;
                font-size: 11px;
                padding: 1px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #6a1b9a);
                border-radius: 6px;
            }
        """)
        
        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(120)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.results_list)
        progress_group.setLayout(progress_layout)
        
        # -------- Botón de procesar --------
        self.btn_process = QPushButton("🚀 Procesar Contrato(s)")
        self.btn_process.setMinimumHeight(45)
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_contract)
        
        # -------- Ensamblar layout principal --------
        main_layout.addWidget(config_group)
        main_layout.addWidget(file_group)
        main_layout.addWidget(progress_group)
        main_layout.addWidget(self.btn_process)
        
        tab.setLayout(main_layout)
        return tab
    
    def on_tab_changed(self, index):
        """Cuando cambia la pestaña activa"""
        if index == 1:  # Pestaña de datos
            self.data_tab.load_data()

    # =========================================================
    # ACCIONES
    # =========================================================

    def select_root_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar directorio raíz",
            "",
            QFileDialog.ShowDirsOnly
        )

        if not directory:
            return

        self.root_dir = directory
        self.root_input.setText(directory)

        # Inicializar controlador
        self.controller = ContractController(
            root_dir=self.root_dir,
            preview_dir=self.preview_dir
        )

        self._update_process_state()

    def select_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar contrato(s)",
            "",
            "Documentos (*.pdf *.png *.jpg *.jpeg);;Todos los archivos (*.*)"
        )

        if not files:
            return

        self.selected_files.extend(files)
        self.update_files_list()
        
        # Mostrar vista previa del primer archivo
        if self.selected_files:
            self.show_preview(self.selected_files[0])
        
        self._update_process_state()

    def clear_files(self):
        """Limpia todos los archivos seleccionados"""
        self.selected_files.clear()
        self.update_files_list()
        self.preview_label.setText("Vista previa\ndel documento")
        self._update_process_state()

    def update_files_list(self):
        """Actualiza la lista de archivos"""
        self.files_list.clear()
        for file_path in self.selected_files:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(f"📄 {file_name}")
            item.setData(Qt.UserRole, file_path)
            self.files_list.addItem(item)
        
        # Actualizar info
        count = len(self.selected_files)
        if count == 0:
            self.file_info_label.setText("Ningún archivo seleccionado")
            self.btn_clear_files.setEnabled(False)
        else:
            self.file_info_label.setText(f"{count} archivo(s) seleccionado(s)")
            self.btn_clear_files.setEnabled(True)

    def on_file_selected(self, item):
        """Cuando se selecciona un archivo en la lista"""
        file_path = item.data(Qt.UserRole)
        self.show_preview(file_path)

    def _on_files_list_selection_changed(self):
        """Habilita o deshabilita el botón de eliminar según la selección"""
        selected = self.files_list.selectedItems()
        self.btn_remove_file.setEnabled(bool(selected))
        # Mantener el botón limpiar habilitado si hay archivos
        self.btn_clear_files.setEnabled(len(self.selected_files) > 0)
        # Actualizar estado del botón de procesar
        self._update_process_state()

    def remove_selected_file(self):
        """Elimina el archivo actualmente seleccionado de la lista de archivos"""
        item = self.files_list.currentItem()
        if not item:
            return

        file_path = item.data(Qt.UserRole)

        try:
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
        except Exception:
            pass

        # Actualizar la lista y la vista previa
        self.update_files_list()
        if self.selected_files:
            # Mostrar vista previa del primero restante
            self.show_preview(self.selected_files[0])
        else:
            # Restaurar texto por defecto
            try:
                self.preview_label.setPixmap(QPixmap())
            except Exception:
                pass
            self.preview_label.setText("Vista previa\ndel documento")

        # Actualizar estado de procesamiento
        self._update_process_state()

    def show_preview(self, file_path):
        """Muestra la vista previa del archivo"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            pix = QPixmap()
            
            if ext == ".pdf":
                # Convertir primera página a imagen
                import tempfile
                tmpdir = tempfile.mkdtemp()
                imgs = pdf_to_images(file_path, tmpdir, limit=1)
                if imgs:
                    pix.load(imgs[0])
            else:
                pix.load(file_path)

            if not pix.isNull():
                pix = pix.scaled(
                    self.preview_label.width(), 
                    self.preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(pix)
            else:
                self.preview_label.setText("No se pudo cargar\nla vista previa")
        except Exception as e:
            print(f"Error en vista previa: {e}")
            self.preview_label.setText("Error en\nvista previa")

    def _update_process_state(self):
        """Habilita el botón de procesar solo si hay directorio y archivos"""
        enabled = bool(self.root_dir and self.selected_files)
        self.btn_process.setEnabled(enabled)
        
        # Actualizar texto del botón
        if enabled:
            count = len(self.selected_files)
            self.btn_process.setText(f"🚀 Procesar {count} Contrato(s)")

    def load_calendar_data(self, calendar: str = None):
        """Carga el CSV del calendario seleccionado en el DataManager y refresca la pestaña de datos."""
        if not self.controller:
            QMessageBox.warning(self, "Sin directorio raíz", "Primero seleccione el directorio raíz.")
            return

        if calendar is None:
            calendar = self.calendar_combo.currentText()

        calendar_dir = self.controller.file_service.get_calendar_dir(calendar)
        loaded = self.data_manager.load_from_calendar_dir(calendar_dir)
        if loaded:
            QMessageBox.information(self, "CSV cargado", f"CSV del calendario '{calendar}' cargado en la vista de datos.")
            if self.tabs.currentIndex() == 1:
                self.data_tab.load_data()
        else:
            QMessageBox.information(self, "Sin CSV", f"No se encontró CSV para el calendario '{calendar}'.")

    def open_calendar_folder(self):
        """Abre la carpeta del calendario en el explorador de archivos."""
        if not self.controller:
            QMessageBox.warning(self, "Sin directorio raíz", "Primero seleccione el directorio raíz.")
            return
        calendar = self.calendar_combo.currentText()
        calendar_dir = self.controller.file_service.get_calendar_dir(calendar)
        try:
            os.startfile(calendar_dir)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta: {e}")

    def open_calendar_csv(self):
        """Abre el CSV del calendario con la aplicación por defecto y lo carga en la vista."""
        if not self.controller:
            QMessageBox.warning(self, "Sin directorio raíz", "Primero seleccione el directorio raíz.")
            return
        calendar = self.calendar_combo.currentText()
        calendar_dir = self.controller.file_service.get_calendar_dir(calendar)
        csv_path = os.path.join(calendar_dir, 'contratos.csv')
        if os.path.exists(csv_path):
            try:
                os.startfile(csv_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el CSV: {e}")
            # También cargar en la pestaña de datos
            self.load_calendar_data(calendar)
        else:
            QMessageBox.information(self, "Sin CSV", f"No existe '{csv_path}'")

    # =========================================================
    # PROCESAMIENTO
    # =========================================================

    def process_contract(self):
        # Procesa los archivos seleccionados y muestra progreso
        #la barra de progreso y resultados se encuentran en self.progress_bar y self.results_list
        try:
            calendar = self.calendar_combo.currentText()
            files = list(self.selected_files)
            total = len(files)
            
            # Configurar progreso
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.results_list.clear()
            
            successful = 0
            failed = 0
            
            for i, file_path in enumerate(files):
                # Permitir que la UI responda
                QApplication.processEvents()
                
                try:
                    # Procesar archivo
                    result = self.controller.process_uploaded_file(
                        file_path=file_path, 
                        calendar=calendar
                    )
                    
                    # Mostrar en lista de resultados (no guardamos más registros automáticamente)
                    final_path = result.get('final_path', '')
                    item_text = f"✅ {os.path.basename(file_path)} -> {final_path}"
                    successful += 1
                    
                except Exception as e:
                    item_text = f"❌ {os.path.basename(file_path)} -> Error: {str(e)}"
                    failed += 1
                
                self.results_list.addItem(QListWidgetItem(item_text))
                self.progress_bar.setValue(i + 1)
            
            # Mostrar resumen
            msg = f"""
            <h3>Proceso Completado</h3>
            <p><b>Total:</b> {total} archivo(s)</p>
            <p style='color: green;'><b>Exitosos:</b> {successful}</p>
            <p style='color: red;'><b>Fallidos:</b> {failed}</p>
            """
            
            if successful > 0:
                msg += "<p>Los datos se han guardado en la pestaña 'Ver/Editar Datos'</p>"
            
            QMessageBox.information(self, "Resultado", msg)
            
            # Limpiar selección
            self.clear_files()
            self.progress_bar.setVisible(False)
            
            # Actualizar pestaña de datos si está visible
            # Cargar CSV del calendario procesado y mostrarlo
            try:
                self.load_calendar_data(calendar)
            except Exception:
                # Fallback: refrescar la vista actual del DataTab
                if self.tabs.currentIndex() == 1:
                    self.data_tab.load_data()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error en el procesamiento",
                f"Se produjo un error inesperado:\n\n{str(e)}"
            )
            self.progress_bar.setVisible(False)

    def update_stats(self):
        return
    
    def _on_calendar_changed(self):
        """Cuando se cambia el calendario seleccionado."""
        current_data = self.calendar_combo.currentData()
        if current_data and hasattr(current_data, 'nombre'):
            # Es un objeto Calendar de la BD
            cal = current_data
            print(f"Calendario seleccionado: {cal.nombre}")
            print(f"  Período: {cal.fecha_inicio} a {cal.fecha_fin}")
            print(f"  Tipo: {cal.tipo}")
        else:
            # Es un string legacy
            print(f"Calendario seleccionado: {self.calendar_combo.currentText()}")
            
    def _on_search_query_changed(self, text):
        """Lógica para filtrar los datos del DataTab desde la barra de búsqueda"""
        if hasattr(self, 'data_tab'):
            # Actualizar el campo de búsqueda en la pestaña de datos
            self.data_tab.search_input.setText(text)
            # Esto activará automáticamente apply_filter
            
    def closeEvent(self, event):
        """Se ejecuta al cerrar la ventana principal"""
        # Los cambios se guardan automáticamente en DataTab al editar
        event.accept()

    def on_tab_changed(self, index):
        """Cuando cambia la pestaña, si se sale de la de datos, preguntar si guardar"""
        # Si el usuario estaba en la pestaña de datos (index 1) y se va a otra
        # Podrías implementar una lógica similar aquí si quieres que guarde al cambiar de pestaña
        if index == 1: 
            self.data_tab.load_data()