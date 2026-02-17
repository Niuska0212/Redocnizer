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
    QTextEdit, QGroupBox, QSpinBox, QCheckBox, QSplitter, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSettings
from PySide6.QtGui import QPixmap, QFont, QColor, QBrush, QIcon

from controllers.contract_controller import ContractController
from services.pdf_service import pdf_to_images
from ui.app_menu import create_app_menu
from ui.calendar_db import CalendarDB
from ui.data_manager import DataManager
from ui.data_tab import DataTab
from ui.drive_sync_tab import DriveSyncTab
from ui.network_credentials_dialog import NetworkCredentialsDialog

from services.concurrent_worker import ConcurrentOCRWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("REDOCNIZER - Gestión de Contratos CUCEI")
        screen = QApplication.primaryScreen().geometry()
        width = screen.width() * 0.65  
        height = screen.height() * 0.52
        self.resize(int(width), int(height))
        self.move((screen.width() - width) / 2, (screen.height() - height) / 2)
        
        # --------------------------------------
        #LOGO EN LA VENTANA de la aplicacion
        # --------------------------------------
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo_redocnizer.png')
        self.setWindowIcon(QIcon(icon_path))
        
        # 1. cargar la imagen del logo
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo_redocnizer.png')
        
        # 2. verifica que el archivo exista
        if os.path.isfile(logo_path):
            pixmap = QIcon(logo_path)
            
            # 3. Establecer el icono de la ventana
            self.setWindowIcon(pixmap)
        else:
            print(f"Advertencia: No se encontró el logo en {logo_path}")
        
        # CONFIGURACION DE MEMORIA (QSettings)
        self.settings = QSettings("Redocnizer", "RedocnizerApp")
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # -----------------------------------------
        # ESTADO DE LA APLICACIÓN
        # -----------------------------------------
        self.root_dir = "" # VALOR RAIZ POR DEFECTO
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
        
        self._load_saved_settings()
        # Crear y adjuntar la barra de menú (archivo/editar)
        try:
            create_app_menu(self)
        except Exception as e:
            print(f"No se pudo crear la barra de menú: {e}")
        
        # Estilo de la aplicación (tema minimalista - azules / morados)
        # Se asegura contraste de texto oscuro sobre fondos claros para legibilidad
        self.setStyleSheet("""
            /* Colores base */
            QMainWindow { background-color: rgba(246, 248, 251, 240);  
            color: #0b2545; }

            /* Barra de menú */
            QMenuBar { background: #f6f8fb;; color: #0b2545; }
            QMenuBar::item { background: #f6f8fb; padding: 6px 12px; }
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
            
            QTabBar {
                background: #f6f8fb;    /* Fondo claro para el área de las pestañas */
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
                background: #ffffff;
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
                "2030A", "2030B",
                "2031A", "2031B"
            ])
            self.calendar_combo.setCurrentText("2024A")
        
        # Conectar cambio de calendario
        self.calendar_combo.currentIndexChanged.connect(self._on_calendar_changed)
        
        calendar_layout.addWidget(QLabel("Calendario:"))
        calendar_layout.addWidget(self.calendar_combo)
        # Botones rápidos para abrir CSV y carpeta del calendario
        self.btn_open_calendar_excel = QPushButton("📊 Abrir Excel del calendario")
        self.btn_open_calendar_excel.setMaximumWidth(180)
        self.btn_open_calendar_excel.clicked.connect(self.open_calendar_excel)

        self.btn_load_calendar_data = QPushButton("📥 Cargar datos del calendario")
        self.btn_load_calendar_data.setMaximumWidth(180)
        self.btn_load_calendar_data.clicked.connect(self.load_calendar_file)

        self.btn_open_calendar_folder = QPushButton("Abrir carpeta del calendario")
        self.btn_open_calendar_folder.setMaximumWidth(180)
        self.btn_open_calendar_folder.clicked.connect(self.open_calendar_folder)

        calendar_layout.addWidget(self.btn_open_calendar_excel)
        calendar_layout.addWidget(self.btn_load_calendar_data)
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
            self.root_dir if self.root_dir else "", # Abrir donde se quedó la última vez
            QFileDialog.ShowDirsOnly
        )

        if not directory:
            return

        # Detectar si es una ruta UNC (red compartida)
        if directory.startswith("\\\\") or directory.startswith("//"):
            # Es una ruta de red: \\servidor\recurso
            # Solicitar credenciales
            result = self._prompt_network_credentials(directory)
            if not result:
                # Usuario canceló la autenticación
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "No se pudo acceder a la red compartida sin autenticación."
                )
                return
            # El usuario mapeó la unidad, usar la nueva ruta
            directory = result

        self.root_dir = directory
        self.root_input.setText(directory)
        
        # --- GUARDAR EN MEMORIA PERMANENTE ---
        self.settings.setValue("root_dir", directory)
        print(f"💾 Ruta guardada en configuración: {directory}")
        # ----------------------------------------

        # Inicializar controlador
        self.controller = ContractController(
            root_dir=self.root_dir,
            preview_dir=self.preview_dir
        )

        self._update_process_state()

    def _prompt_network_credentials(self, unc_path: str) -> str:
        """
        Muestra un diálogo para solicitar credenciales de red.
        
        Args:
            unc_path: Ruta UNC (\\servidor\recurso)
        
        Returns:
            Letra de unidad mapeada (Z:\\) o vacío si falló
        """
        dialog = NetworkCredentialsDialog(
            parent=self,
            network_path=unc_path,
            drive_letter="Z"
        )
        
        if dialog.exec() == QDialog.Accepted:
            mapped_drive = dialog.get_mapped_drive()
            if mapped_drive:
                print(f"✅ Red mapeada como: {mapped_drive}")
                return mapped_drive
        
        return ""

    def select_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar contrato(s)",
            "",
            "Documentos (*.pdf *.png *.jpg *.jpeg);;Todos los archivos (*.*)"
        )

        if not files:
            return

        # Solo agregar archivos que no estén ya en la lista (evitar duplicados)
        for file_path in files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
        
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

        # Verificar si hay cambios sin guardar
        if hasattr(self, 'data_tab') and self.data_tab.has_unsaved_changes():
            reply = QMessageBox.warning(
                self,
                "Cambios sin guardar",
                "⚠️ Tienes cambios sin guardar en los datos actuales.\n\n¿Deseas guardarlos antes de cargar otro calendario?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.data_tab.save_all_to_manager()
            elif reply == QMessageBox.Cancel:
                # El usuario canceló la operación, volver al calendario anterior
                return

        if calendar is None:
            calendar = self.calendar_combo.currentText()

        calendar_dir = self.controller.file_service.get_calendar_dir(calendar)
        
        # Establecer el CSV source para que se guarden cambios allí
        csv_path = os.path.join(calendar_dir, 'contratos.csv')
        self.data_manager.set_source_csv(csv_path)
        
        loaded = self.data_manager.load_from_calendar_dir(calendar_dir)
        if loaded:
            QMessageBox.information(self, "CSV cargado", f"CSV del calendario '{calendar}' cargado en la vista de datos.")
            if self.tabs.currentIndex() == 1:
                self.data_tab.load_data()
            
            # Cargar las previsualizaciones asociadas
            self._load_preview_images_from_csv()
        else:
            QMessageBox.information(self, "Sin CSV", f"No se encontró CSV para el calendario '{calendar}'.")

    def _load_preview_images_from_csv(self):
        """Carga las imágenes de preview basadas en los datos del CSV"""
        try:
            # Obtener los datos actuales del data_manager
            df = self.data_manager.get_dataframe()
            if df.empty:
                return
            
            # Buscar la columna que contenga el nombre del archivo (ej: CODIGO)
            # Intentar encontrar nombres de archivo en las primeras columnas
            preview_images = []
            
            for idx, row in df.iterrows():
                # Buscar en diferentes columnas que podrían contener nombres de archivo
                # Primero intentar con CODIGO o NUM
                filename = None
                for col in ['CODIGO', 'NUM', 'NOMBRE_S', 'PATERNO']:
                    if col in row and pd.notna(row[col]):
                        potential_file = str(row[col]).strip()
                        if potential_file and potential_file.upper() != 'UNKNOWN':
                            filename = potential_file
                            break
                
                if filename:
                    # Buscar la imagen en la carpeta de previsualizaciones
                    # Sin extensión y con extensión .jpg
                    base_name = os.path.splitext(filename)[0]
                    preview_path = os.path.join(self.preview_dir, f"{base_name}.jpg")
                    
                    if os.path.exists(preview_path):
                        preview_images.append(preview_path)
            
            # Agregar las imágenes encontradas a selected_files
            if preview_images:
                self.selected_files = preview_images
                self.update_files_list()
                
                # Mostrar vista previa del primer archivo
                if self.selected_files:
                    self.show_preview(self.selected_files[0])
                
                self._update_process_state()
        except Exception as e:
            print(f"Error cargando imágenes de preview: {e}")

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

    def open_calendar_excel(self):
        """Abre el CSV del calendario en Excel (solo abre, no carga datos)."""
        if not self.controller:
            QMessageBox.warning(self, "Sin directorio raíz", "Primero seleccione el directorio raíz.")
            return
        calendar = self.calendar_combo.currentText()
        calendar_dir = self.controller.file_service.get_calendar_dir(calendar)
        csv_path = os.path.join(calendar_dir, 'contratos.csv')
        if os.path.exists(csv_path):
            try:
                os.startfile(csv_path)
                QMessageBox.information(self, "Archivo abierto", f"Se abrió el archivo de calendario en Excel.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo en Excel: {e}")
        else:
            QMessageBox.information(self, "Sin CSV", f"No existe el archivo '{csv_path}'")

    def load_calendar_file(self):
        """Carga el CSV del calendario en la vista de datos (sin abrir Excel)."""
        if not self.controller:
            QMessageBox.warning(self, "Sin directorio raíz", "Primero seleccione el directorio raíz.")
            return
        calendar = self.calendar_combo.currentText()
        
        # Verificar si hay cambios sin guardar
        if hasattr(self, 'data_tab') and self.data_tab.has_unsaved_changes():
            reply = QMessageBox.warning(
                self,
                "Cambios sin guardar",
                "⚠️ Tienes cambios sin guardar en los datos actuales.\n\n¿Deseas guardarlos antes de cargar otro calendario?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.data_tab.save_all_to_manager()
            elif reply == QMessageBox.Cancel:
                return
        
        calendar_dir = self.controller.file_service.get_calendar_dir(calendar)
        csv_path = os.path.join(calendar_dir, 'contratos.csv')
        
        if not os.path.exists(csv_path):
            QMessageBox.warning(self, "Sin CSV", f"No existe el archivo de calendario en:\n{csv_path}")
            return
        
        # Establecer el CSV source para que se guarden cambios allí
        self.data_manager.set_source_csv(csv_path)
        
        # Cargar datos
        loaded = self.data_manager.load_from_calendar_dir(calendar_dir)
        if loaded:
            QMessageBox.information(self, "Datos cargados", f"✅ Datos del calendario '{calendar}' cargados correctamente.")
            # Cambiar a pestaña de datos para mostrar los datos cargados
            self.tabs.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos del calendario.")


    # =========================================================
    # PROCESAMIENTO
    # =========================================================

    def process_contract(self):
        """
        Lanza el procesamiento concurrente (Módulo 3).
        Sustituye el bucle for síncrono por la ejecución en un hilo secundario.
        """
        # 1. Validaciones previas
        if not self.selected_files:
            return

        calendar = self.calendar_combo.currentText()
        files = list(self.selected_files)
        
        # 2. Configuración visual inicial
        self.btn_process.setEnabled(False)
        self.progress_bar.setMaximum(len(files))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.results_list.clear()

        # 3. CREAR EL TRABAJADOR (HILO)     
        self.worker = ConcurrentOCRWorker(
            file_paths=files, 
            calendar=calendar, 
            controller=self.controller
        )

        # 4. CONECTAR LAS SEÑALES (Protocolo de comunicación interna)
        
        # Actualiza la barra y el mensaje de estado
        self.worker.progress.connect(self.update_processing_ui)
        
        # Cuando un archivo termina, se añade a la lista visual
        self.worker.file_finished.connect(self.add_result_to_list)
        
        # Cuando TODO termina, muestra el resumen y limpia
        self.worker.all_finished.connect(self.show_final_summary)
        
        # Manejo de errores críticos del hilo
        self.worker.error.connect(self.handle_worker_error)

        # 5. INICIAR EL HILO (Módulo 3.1.1)
        self.worker.start()

    # --- Funciones de soporte para el Hilo ---

    def update_processing_ui(self, value, message):
        self.progress_bar.setValue(value)
        # Si tienes un label de estado, podrías poner: self.status_label.setText(message)

    def add_result_to_list(self, item_text, result_data):
        from PySide6.QtWidgets import QListWidgetItem
        self.results_list.addItem(QListWidgetItem(item_text))
        # Hace scroll automático al final
        self.results_list.scrollToBottom()

    def show_final_summary(self, successful, failed, results):
        total = successful + failed
        msg = f"""
        <h3>Proceso Completado</h3>
        <p><b>Total:</b> {total} archivo(s)</p>
        <p style='color: green;'><b>Exitosos:</b> {successful}</p>
        <p style='color: red;'><b>Fallidos:</b> {failed}</p>
        """
        
        if successful > 0:
            msg += "<p>Los datos se han guardado en la pestaña 'Ver/Editar Datos'</p>"
        
        QMessageBox.information(self, "Resultado", msg)
        
        # Limpieza final
        self.clear_files()
        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        
        # Actualizar tabla de datos
        calendar = self.calendar_combo.currentText()
        try:
            self.load_calendar_data(calendar)
        except:
            if self.tabs.currentIndex() == 1:
                self.data_tab.load_data()

    def handle_worker_error(self, error_msg):
        QMessageBox.critical(self, "Error de Sistema Paralelo", error_msg)
        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
            
            
    # =========================================================

    def update_stats(self):
        return
    
    def _on_calendar_changed(self):
        """Cuando se cambia el calendario seleccionado."""
        current_data = self.calendar_combo.currentData()
        
        # --- LÓGICA DE LIMPIEZA CON CHECKBOX ---
        if self.controller:
            # 1. Revisar si el usuario ya marcó "No volver a mostrar" anteriormente
            # Usamos QSettings para recordar la preferencia
            settings = QSettings("MiEmpresa", "Redocnizer")
            skip_prompt = settings.value("skip_preview_cleanup_prompt", False, type=bool)
            last_answer = settings.value("last_preview_cleanup_answer", QMessageBox.No, type=int)

            if not skip_prompt:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setWindowTitle("Cambio de Calendario")
                msg_box.setText("¿Deseas eliminar las imágenes de vista previa del calendario anterior?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                # Añadir el checkbox
                cb = QCheckBox("No volver a preguntar (recordar mi elección)")
                cb.setStyleSheet("""
                    QCheckBox {
                        color: #0b2545;  /* Texto Negro/Azul muy oscuro */
                        font-weight: 500;
                        spacing: 8px;    /* Espacio entre el cuadro y el texto */
                        margin-top: 10px;
                    }
                    QCheckBox::indicator {
                        width: 18px;
                        height: 18px;
                        border-radius: 4px;
                        border: 2px solid #1976d2; /* Borde Azul */
                        background-color: white;
                    }
                    QCheckBox::indicator:unchecked:hover {
                        border: 2px solid #6a1b9a; /* Borde Morado al pasar el mouse */
                    }
                    QCheckBox::indicator:checked {
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                        stop:0 #1976d2, stop:1 #6a1b9a); /* Degradado Azul-Morado */
                        border: 2px solid #6a1b9a;
                    }
                """)
                msg_box.setCheckBox(cb)
                msg_box.setStyleSheet("QLabel{ color: #0b2545; font-size: 13px; } QPushButton{ width: 80px; }")
                
                resultado = msg_box.exec()
                
                # Guardar preferencia si el checkbox está marcado
                if cb.isChecked():
                    settings.setValue("skip_preview_cleanup_prompt", True)
                    settings.setValue("last_preview_cleanup_answer", resultado)
                
                respuesta = resultado
            else:
                # Si ya pidió no preguntar, usamos la última respuesta guardada
                respuesta = last_answer

            # Ejecutar la limpieza si la respuesta fue SI
            if respuesta == QMessageBox.Yes:
                self.controller.limpiar_previews()
                if hasattr(self, 'data_tab'):
                    self.data_tab.preview_img_label.clear()
                    self.data_tab.preview_img_label.setText("Carpeta de previews vaciada automáticamente.")
        # -----------------------------------

        if current_data and hasattr(current_data, 'nombre'):
            print(f"Calendario seleccionado: {current_data.nombre}")
        else:
            print(f"Calendario seleccionado: {self.calendar_combo.currentText()}")
            
    def _on_search_query_changed(self, text):
        """Lógica para filtrar los datos del DataTab desde la barra de búsqueda"""
        if hasattr(self, 'data_tab'):
            # Actualizar el campo de búsqueda en la pestaña de datos
            self.data_tab.search_input.setText(text)
            # Esto activará automáticamente apply_filter
            
    def closeEvent(self, event):
        """Se ejecuta al cerrar la ventana principal"""
        # Verificar si hay cambios sin guardar en la pestaña de datos
        if hasattr(self, 'data_tab') and self.data_tab.has_unsaved_changes():
            reply = QMessageBox.warning(
                self,
                "Cambios sin guardar",
                "⚠️ Tienes cambios sin guardar.\n\n¿Estás seguro de que deseas salir sin guardarlos?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                # Guardar cambios y luego cerrar
                self.data_tab.save_all_to_manager()
                event.accept()
            elif reply == QMessageBox.Discard:
                # Cerrar sin guardar
                event.accept()
            else:
                # Cancelar cierre
                event.ignore()
        else:
            # No hay cambios sin guardar, cerrar normalmente
            event.accept()

    def on_tab_changed(self, index):
        """Controla el cambio entre pestañas"""
        
        # Si el usuario intenta SALIR de la pestaña de datos (index anterior era 1)
        if hasattr(self, '_last_tab_index') and self._last_tab_index == 1:
            # Verificar si hay cambios reales usando el HistoryManager
            if self.data_tab.history.can_undo(): 
                reply = QMessageBox.question(
                    self,
                    "Cambios sin guardar",
                    "⚠️ Tienes cambios sin guardar en la pestaña de datos.\n¿Deseas guardarlos antes de cambiar?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Yes:
                    self.data_tab.save_all_to_manager()
                elif reply == QMessageBox.Cancel:
                    # Bloquear el cambio de pestaña y regresar a la de datos
                    self.tabs.setCurrentIndex(1)
                    return

        # Actualizar el índice de la pestaña actual para la próxima vez
        self._last_tab_index = index
        
        # Si entra a la pestaña de datos, cargar la información
        if index == 1:
            self.data_tab.load_data()
            
    # =========================================================
    # CONFIGURACIÓN GUARDADA
    # =========================================================      
    def _load_saved_settings(self):
        """Recupera la última ruta raíz utilizada y configura el controlador."""
        last_root = self.settings.value("root_dir", "") # Recupera valor, default ""
        
        if last_root and os.path.exists(last_root):
            print(f"📂 Configuración encontrada: {last_root}")
            
            # 1. Actualizar variable y caja de texto visual
            self.root_dir = last_root
            self.root_input.setText(last_root)
            
            # 2. IMPORTANTE: Inicializar el controlador (igual que si el usuario hubiera elegido manual)
            # Si no hacemos esto, self.controller seguirá siendo None y fallará al procesar
            self.controller = ContractController(
                root_dir=self.root_dir,
                preview_dir=self.preview_dir
            )
            
            # 3. Actualizar estado de botones
            self._update_process_state()
        else:
            print("⚠️ No hay ruta guardada o la carpeta ya no existe.")