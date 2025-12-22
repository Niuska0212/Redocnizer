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
    QTextEdit, QGridLayout, QGroupBox, QSpinBox, QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QFont, QColor, QBrush

from controllers.contract_controller import ContractController
from services.pdf_service import pdf_to_images


class DataManager(QObject):
    """Manejador de datos para el sistema"""
    data_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.data = pd.DataFrame()
        self.data_file = os.path.join(os.getcwd(), "contratos_data.xlsx")
        self._load_data()
    
    def _load_data(self):
        """Carga datos existentes del archivo Excel"""
        if os.path.exists(self.data_file):
            try:
                self.data = pd.read_excel(self.data_file)
                self.data['Fecha_Procesamiento'] = pd.to_datetime(self.data['Fecha_Procesamiento'], errors='coerce')
            except Exception as e:
                print(f"Error cargando datos: {e}")
                self.data = pd.DataFrame()
        else:
            self.data = pd.DataFrame()
    
    def add_record(self, record_data):
        """Agrega un nuevo registro"""
        record_data['Fecha_Procesamiento'] = datetime.now()
        
        if self.data.empty:
            self.data = pd.DataFrame([record_data])
        else:
            new_df = pd.DataFrame([record_data])
            self.data = pd.concat([self.data, new_df], ignore_index=True)
        
        self.save_data()
        self.data_updated.emit()
    
    def update_record(self, row_index, column_name, value):
        """Actualiza un registro específico"""
        if not self.data.empty and row_index < len(self.data):
            self.data.at[row_index, column_name] = value
            self.save_data()
            self.data_updated.emit()
    
    def delete_record(self, row_index):
        """Elimina un registro"""
        if not self.data.empty and row_index < len(self.data):
            self.data = self.data.drop(row_index).reset_index(drop=True)
            self.save_data()
            self.data_updated.emit()
    
    def save_data(self):
        """Guarda los datos al archivo Excel"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            # Guardar con formato Excel
            with pd.ExcelWriter(self.data_file, engine='openpyxl') as writer:
                self.data.to_excel(writer, index=False, sheet_name='Contratos')
            
            print(f"Datos guardados en: {self.data_file}")
        except Exception as e:
            print(f"Error guardando datos: {e}")
    
    def get_dataframe(self):
        """Retorna el DataFrame actual"""
        return self.data.copy()
    
    def export_to_csv(self, filepath):
        """Exporta a CSV"""
        try:
            self.data.to_csv(filepath, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error exportando CSV: {e}")
            return False
    
    def export_to_excel(self, filepath):
        """Exporta a Excel"""
        try:
            self.data.to_excel(filepath, index=False)
            return True
        except Exception as e:
            print(f"Error exportando Excel: {e}")
            return False


class DataTab(QWidget):
    """Pestaña para visualizar y editar datos"""
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.current_edit_row = -1
        self.setup_ui()
        
        # Conectar señal de actualización
        self.data_manager.data_updated.connect(self.load_data)
        
        # Cargar datos iniciales
        QTimer.singleShot(100, self.load_data)
    
    def setup_ui(self):
        """Configura la interfaz de la pestaña de datos"""
        layout = QVBoxLayout()
        
        # -------- Controles superiores --------
        controls_layout = QHBoxLayout()
        
        # Botón para recargar
        self.btn_reload = QPushButton("🔄 Recargar")
        self.btn_reload.clicked.connect(self.load_data)
        self.btn_reload.setMaximumWidth(100)
        
        # Botón para exportar
        self.btn_export = QPushButton("📥 Exportar Datos")
        self.btn_export.clicked.connect(self.export_data)
        self.btn_export.setMaximumWidth(150)
        
        # Etiqueta de información
        self.info_label = QLabel("0 registros")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        
        controls_layout.addWidget(self.btn_reload)
        controls_layout.addWidget(self.btn_export)
        controls_layout.addStretch()
        controls_layout.addWidget(self.info_label)
        
        # -------- Tabla de datos --------
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 2px solid #1976d2;
                font-weight: bold;
            }
        """)
        
        # Conectar doble clic para editar
        self.table.cellDoubleClicked.connect(self.start_edit_cell)
        
        # -------- Panel de edición --------
        edit_group = QGroupBox("Editar Registro")
        edit_group.setMaximumHeight(200)
        edit_layout = QGridLayout()
        
        self.edit_fields = {}
        fields_config = [
            ("ID", "id", QLineEdit),
            ("Nombre", "nombre", QLineEdit),
            ("Contrato", "contrato", QLineEdit),
            ("Fecha", "fecha", QLineEdit),
            ("Calendario", "calendario", QLineEdit),
            ("Archivo", "archivo", QLineEdit),
        ]
        
        for i, (label, field_name, field_type) in enumerate(fields_config):
            row = i // 3
            col = (i % 3) * 2
            
            # Etiqueta
            lbl = QLabel(label + ":")
            lbl.setMinimumWidth(80)
            
            # Campo de entrada
            if field_type == QLineEdit:
                field = QLineEdit()
                field.setReadOnly(True)
            else:
                field = field_type()
            
            field.setMinimumWidth(150)
            
            edit_layout.addWidget(lbl, row, col)
            edit_layout.addWidget(field, row, col + 1)
            
            self.edit_fields[field_name] = field
        
        # Botones de edición
        btn_layout = QHBoxLayout()
        
        self.btn_save_edit = QPushButton("💾 Guardar Cambios")
        self.btn_save_edit.clicked.connect(self.save_edits)
        self.btn_save_edit.setEnabled(False)
        
        self.btn_cancel_edit = QPushButton("❌ Cancelar")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit)
        self.btn_cancel_edit.setEnabled(False)
        
        self.btn_delete = QPushButton("🗑️ Eliminar Registro")
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_delete.setEnabled(False)
        
        btn_layout.addWidget(self.btn_save_edit)
        btn_layout.addWidget(self.btn_cancel_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        
        edit_layout.addLayout(btn_layout, len(fields_config)//3 + 1, 0, 1, 6)
        edit_group.setLayout(edit_layout)
        
        # -------- Ensamblar layout --------
        layout.addLayout(controls_layout)
        layout.addWidget(self.table)
        layout.addWidget(edit_group)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Carga los datos en la tabla"""
        df = self.data_manager.get_dataframe()
        
        if df.empty:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.info_label.setText("0 registros - No hay datos")
            return
        
        # Configurar tabla
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        
        # Llenar tabla
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if not pd.isna(value) else "")
                
                # Colores alternados
                if i % 2 == 0:
                    item.setBackground(QBrush(QColor(250, 250, 250)))
                
                # Formato especial para fechas
                if 'fecha' in df.columns[j].lower() and not pd.isna(value):
                    try:
                        item.setText(str(value)[:10])
                    except:
                        pass
                
                self.table.setItem(i, j, item)
        
        # Ajustar tamaño de columnas
        self.table.resizeColumnsToContents()
        
        # Actualizar info
        self.info_label.setText(f"{len(df)} registros - {len(df.columns)} columnas")
        
        # Deshabilitar edición
        self.cancel_edit()
    
    def start_edit_cell(self, row, column):
        """Inicia la edición de una celda"""
        self.current_edit_row = row
        self.table.editItem(self.table.item(row, column))
    
    def save_edits(self):
        """Guarda los cambios realizados en el formulario de edición"""
        if self.current_edit_row < 0:
            return
        
        df = self.data_manager.get_dataframe()
        if self.current_edit_row >= len(df):
            return
        
        # Obtener valores de los campos
        updates = {}
        for field_name, field_widget in self.edit_fields.items():
            if field_name in df.columns:
                updates[field_name] = field_widget.text()
        
        # Actualizar cada campo
        for field_name, value in updates.items():
            self.data_manager.update_record(self.current_edit_row, field_name, value)
        
        # Recargar datos
        self.load_data()
        QMessageBox.information(self, "Guardado", "Cambios guardados correctamente")
    
    def cancel_edit(self):
        """Cancela la edición actual"""
        self.current_edit_row = -1
        
        # Limpiar campos de edición
        for field_widget in self.edit_fields.values():
            field_widget.clear()
            if isinstance(field_widget, QLineEdit):
                field_widget.setReadOnly(True)
        
        # Deshabilitar botones
        self.btn_save_edit.setEnabled(False)
        self.btn_cancel_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        
        # Deseleccionar fila
        self.table.clearSelection()
    
    def delete_record(self):
        """Elimina el registro seleccionado"""
        if self.current_edit_row < 0:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación",
            "¿Está seguro de eliminar este registro?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_manager.delete_record(self.current_edit_row)
            self.cancel_edit()
    
    def export_data(self):
        """Exporta los datos a archivo"""
        if self.data_manager.data.empty:
            QMessageBox.warning(self, "Sin datos", "No hay datos para exportar")
            return
        
        file_filter = "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar Datos",
            f"contratos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            file_filter
        )
        
        if not file_path:
            return
        
        success = False
        if selected_filter.startswith("Excel"):
            success = self.data_manager.export_to_excel(file_path)
        elif selected_filter.startswith("CSV"):
            success = self.data_manager.export_to_csv(file_path)
        
        if success:
            QMessageBox.information(
                self, 
                "Exportación exitosa",
                f"Datos exportados a:\n{file_path}"
            )
        else:
            QMessageBox.critical(
                self, 
                "Error", 
                "No se pudo exportar los datos"
            )
    
    def table_selection_changed(self):
        """Cuando se selecciona una fila en la tabla"""
        selected = self.table.selectedItems()
        if not selected:
            self.cancel_edit()
            return
        
        row = selected[0].row()
        df = self.data_manager.get_dataframe()
        
        if row < len(df):
            self.current_edit_row = row
            row_data = df.iloc[row]
            
            # Llenar campos de edición
            for field_name, field_widget in self.edit_fields.items():
                if field_name in df.columns:
                    value = row_data[field_name]
                    if pd.isna(value):
                        field_widget.setText("")
                    else:
                        field_widget.setText(str(value))
                    
                    if isinstance(field_widget, QLineEdit):
                        field_widget.setReadOnly(False)
            
            # Habilitar botones
            self.btn_save_edit.setEnabled(True)
            self.btn_cancel_edit.setEnabled(True)
            self.btn_delete.setEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de OCR de Contratos - Procesamiento y Gestión")
        self.resize(1000, 700)

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
        
        # Estilo de la aplicación
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 4px;
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
        
        # Pestaña 3: Estadísticas
        self.stats_tab = self._build_stats_tab()
        self.tabs.addTab(self.stats_tab, "📈 Estadísticas")
        
        # Conectar cambio de pestaña para actualizar datos
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tabs)
    
    def _build_processing_tab(self):
        """Construye la pestaña de procesamiento"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        
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
        self.calendar_combo.addItems([
            "2024A", "2024B",
            "2025A", "2025B",
            "2026A", "2026B",
            "2027A", "2027B",
            "2028A", "2028B",
            "2029A", "2029B",
        ])
        self.calendar_combo.setCurrentText("2024A")
        
        calendar_layout.addWidget(QLabel("Calendario:"))
        calendar_layout.addWidget(self.calendar_combo)
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
        self.preview_label.setFixedSize(250, 350)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: white;
                qproperty-alignment: AlignCenter;
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
        
        btn_layout.addWidget(self.btn_select_file)
        btn_layout.addWidget(self.btn_clear_files)
        
        # Lista de archivos
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.files_list.itemClicked.connect(self.on_file_selected)
        
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
    
    def _build_stats_tab(self):
        """Construye la pestaña de estadísticas"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("📊 Estadísticas del Sistema")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Widget de estadísticas
        stats_widget = QWidget()
        stats_layout = QGridLayout()
        
        # Definir estadísticas
        stats_info = [
            ("Total Contratos", "0", "#4caf50"),
            ("Procesados Hoy", "0", "#2196f3"),
            ("Con Errores", "0", "#f44336"),
            ("Por Calendario", "Cargando...", "#ff9800"),
            ("Último Proceso", "Nunca", "#9c27b0"),
            ("Tasa de Éxito", "0%", "#00bcd4"),
        ]
        
        for i, (title, value, color) in enumerate(stats_info):
            group = QGroupBox(title)
            group_layout = QVBoxLayout()
            
            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                font-size: 24px;
                font-weight: bold;
                color: {color};
                qproperty-alignment: AlignCenter;
            """)
            
            group_layout.addWidget(value_label)
            group.setLayout(group_layout)
            
            row = i // 3
            col = i % 3
            stats_layout.addWidget(group, row, col)
        
        stats_widget.setLayout(stats_layout)
        
        # Botón para actualizar estadísticas
        btn_refresh_stats = QPushButton("🔄 Actualizar Estadísticas")
        btn_refresh_stats.clicked.connect(self.update_stats)
        
        layout.addWidget(title_label)
        layout.addWidget(stats_widget)
        layout.addWidget(btn_refresh_stats, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def on_tab_changed(self, index):
        """Cuando cambia la pestaña activa"""
        if index == 1:  # Pestaña de datos
            self.data_tab.load_data()
        elif index == 2:  # Pestaña de estadísticas
            self.update_stats()

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

    # =========================================================
    # PROCESAMIENTO
    # =========================================================

    def process_contract(self):
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
                    
                    # Extraer datos para guardar
                    record_data = {
                        'id': f"CT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                        'nombre': result.get('nombre', ''),
                        'contrato': result.get('contrato', ''),
                        'fecha': result.get('fecha', ''),
                        'calendario': calendar,
                        'archivo': os.path.basename(file_path),
                        'ruta_final': result.get('final_path', ''),
                        'estado': 'COMPLETADO',
                    }
                    
                    # Agregar al manager de datos
                    self.data_manager.add_record(record_data)
                    
                    # Mostrar en lista de resultados
                    item_text = f"✅ {os.path.basename(file_path)} -> {record_data['ruta_final']}"
                    successful += 1
                    
                except Exception as e:
                    item_text = f"❌ {os.path.basename(file_path)} -> Error: {str(e)}"
                    failed += 1
                    
                    # Guardar registro de error
                    error_record = {
                        'id': f"ERR_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                        'nombre': '',
                        'contrato': '',
                        'fecha': '',
                        'calendario': calendar,
                        'archivo': os.path.basename(file_path),
                        'ruta_final': '',
                        'estado': f'ERROR: {str(e)}',
                    }
                    self.data_manager.add_record(error_record)
                
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
        """Actualiza las estadísticas en la pestaña correspondiente"""
        df = self.data_manager.get_dataframe()
        
        if df.empty:
            return
        
        # Calcular estadísticas
        total = len(df)
        today = datetime.now().date()
        today_count = len(df[pd.to_datetime(df['Fecha_Procesamiento']).dt.date == today])
        errors = len(df[df['estado'].astype(str).str.contains('ERROR', case=False)])
        
        # Tasa de éxito
        success_rate = ((total - errors) / total * 100) if total > 0 else 0
        
        # Último procesamiento
        if 'Fecha_Procesamiento' in df.columns:
            last_date = pd.to_datetime(df['Fecha_Procesamiento']).max()
            last_str = last_date.strftime('%Y-%m-%d %H:%M')
        else:
            last_str = "N/A"
        
        # Por calendario
        if 'calendario' in df.columns:
            calendar_stats = df['calendario'].value_counts().to_dict()
            calendar_str = ", ".join([f"{k}: {v}" for k, v in calendar_stats.items()][:3])
            if len(calendar_stats) > 3:
                calendar_str += "..."
        else:
            calendar_str = "N/A"
        
        # Actualizar widgets (necesitarías agregar referencias a los labels)
        # Para simplificar, aquí solo se muestra cómo calcular las estadísticas
        print(f"Estadísticas: Total={total}, Hoy={today_count}, Errores={errors}")