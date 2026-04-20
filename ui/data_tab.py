#ui/data_tab.py

import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QFileDialog, QMessageBox,
    QAbstractItemView, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QFileSystemWatcher
from PySide6.QtGui import QPixmap, QColor, QBrush, QWheelEvent

from services.pdf_service import pdf_to_images
from ui.history_manager import HistoryManager 
from ui.calendar_db import CalendarDB#from ui.edit_record_dialog import EditRecordDialog
from ui.file_watcher import FileWatcher
try:
    from ui.image_preview_dialog import ImagePreviewDialog
except ImportError:
    ImagePreviewDialog = None


class ClickableLabel(QLabel):
    """Un QLabel que emite una señal cuando se hace clic en él."""
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class DataTab(QWidget):
    """Pestaña para visualizar y editar datos con búsqueda, ordenamiento y edición directa."""

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.original_df = None  # Guardar datos originales para búsqueda
        self.filtered_df = None  # Datos filtrados por búsqueda
        self.history = HistoryManager()  # Sistema de undo/redo
        self.file_watcher = FileWatcher()  # Monitor de cambios externos
        self.file_watcher.file_changed.connect(self._on_external_file_changed)
        self.current_preview_pixmap = None  # Para almacenar la imagen de vista previa actual
        self.setup_ui()

        # Ruta absoluta a la carpeta CALENDARIOS del proyecto
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.calendarios_dir = os.path.join(self.project_root, "CALENDARIOS")
        os.makedirs(self.calendarios_dir, exist_ok=True)

        # Watcher para cambios en la carpeta CALENDARIOS
        self.folder_watcher = QFileSystemWatcher()
        self.folder_watcher.addPath(self.calendarios_dir)
        self.folder_watcher.directoryChanged.connect(self.reload_calendars)

        # Configuración del calendario
        self.cal_db = CalendarDB()
        self._populate_calendar_combo()
        
        self.calendar_combo.currentIndexChanged.connect(self._on_calendar_changed)
        
        # Cargar datos iniciales del calendario
        self.current_calendar_index = self.calendar_combo.currentIndex()
        if self.calendar_combo.count() > 0:
            self._on_calendar_changed()

        # Conectar señal de actualización
        self.data_manager.data_updated.connect(self.load_data)
        
        self.data_manager.data_updated.connect(self.load_data)
        
        # Cargar datos iniciales
        QTimer.singleShot(100, self.load_data)

    def setup_ui(self):
        """Configura la interfaz de la pestaña de datos"""
        layout = QVBoxLayout()

        # -------- Controles superiores (Restaurados completamente) --------
        controls_layout = QHBoxLayout()

        # Campo de búsqueda
        search_label = QLabel("🔍 Buscar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en nombres, códigos, teléfono, etc...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.apply_filter)

        # Botones de edición
        self.btn_undo = QPushButton("↶ Deshacer")
        self.btn_undo.clicked.connect(self.undo_change)
        self.btn_undo.setMaximumWidth(100)
        self.btn_undo.setEnabled(False)

        self.btn_redo = QPushButton("↷ Rehacer")
        self.btn_redo.clicked.connect(self.redo_change)
        self.btn_redo.setMaximumWidth(100)
        self.btn_redo.setEnabled(False)

        # Botón para recargar
        #self.btn_reload = QPushButton("🔄 Recargar")
        #self.btn_reload.clicked.connect(self.load_data)
        #self.btn_reload.setMaximumWidth(100)

        # Botón Guardar
        self.btn_save_all = QPushButton("💾 Guardar Cambios")
        self.btn_save_all.clicked.connect(self.save_all_to_manager)
        self.btn_save_all.setStyleSheet("background: #2e7d32; color: white;")
        self.btn_save_all.setEnabled(False)

        # Botón para exportar
        self.btn_export = QPushButton("📥 Exportar")
        self.btn_export.clicked.connect(self.export_data)
        self.btn_export.setMaximumWidth(100)

        # Etiqueta de información
        self.info_label = QLabel("0 registros")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")

        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(self.btn_undo)
        controls_layout.addWidget(self.btn_redo)
        #controls_layout.addWidget(self.btn_reload)
        controls_layout.addWidget(self.btn_export)
        controls_layout.addWidget(self.btn_save_all)
        controls_layout.addStretch()
        controls_layout.addWidget(self.info_label)

        # -------- Tabla de datos (Restaurada configuración) --------
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        # Permitir ordenamiento
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_by_column)

        # Conexiones
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        #self.table.doubleClicked.connect(self._on_row_double_clicked)

        # -------- Vista previa (Mejorada con ClickableLabel) --------
        table_preview_layout = QHBoxLayout()
        table_preview_layout.addWidget(self.table, 3)

        # Usamos ClickableLabel con tus estilos originales y el cursor de mano
        self.preview_img_label = ClickableLabel()
        self.preview_img_label.setObjectName("preview_label_data")
        self.preview_img_label.setFixedSize(250, 350)
        self.preview_img_label.setCursor(Qt.PointingHandCursor)
        self.preview_img_label.setToolTip("Haz clic para ampliar imagen")
        self.preview_img_label.setStyleSheet("""
            QLabel { 
                border: 2px dashed rgba(25,118,210,0.18); 
                border-radius: 8px; 
                background-color: #ffffff; 
                color: #0b2545; 
                qproperty-alignment: AlignCenter; 
                font-weight: 600; 
            }
            QLabel:hover {
                border: 2px solid #1976d2;
                background-color: #f0f7ff;
            }
        """)
        self.preview_img_label.setText("Sin visualización")
        
        # Conexión para abrir el visor
        self.preview_img_label.clicked.connect(self._open_advanced_preview)
        
        table_preview_layout.addWidget(self.preview_img_label, 0)

        # -------- Ensamblar layout --------
        layout.addLayout(controls_layout)
        
        # -------- Calendario y controles --------
        calendar_layout = QHBoxLayout()
        self.calendar_combo = QComboBox()
        # Forzar estilo del popup del combo: fondo blanco y texto oscuro
        self.calendar_combo.setStyleSheet(
            "QComboBox QAbstractItemView { background-color: #ffffff; color: #0b2545; "
            "selection-background-color: #e3f2fd; selection-color: #0b2545; }"
        )
        calendar_layout.addWidget(QLabel("Calendario:"))
        calendar_layout.addWidget(self.calendar_combo)
        # Botones rápidos para abrir CSV y carpeta del calendario
        self.btn_open_calendar_excel = QPushButton("📊 Abrir Excel del calendario")
        self.btn_open_calendar_excel.setMaximumWidth(180)
        self.btn_open_calendar_excel.clicked.connect(self.open_calendar_excel)
        
        self.btn_open_calendar_folder = QPushButton("Abrir carpeta CVS")
        self.btn_open_calendar_folder.setMaximumWidth(180)
        self.btn_open_calendar_folder.clicked.connect(self.open_calendar_folder)
        
        calendar_layout.addWidget(self.btn_open_calendar_excel)
        calendar_layout.addWidget(self.btn_open_calendar_folder)
        calendar_layout.addStretch()
        layout.addLayout(calendar_layout)
        
        layout.addLayout(table_preview_layout)
        self.setLayout(layout)
        
    def _populate_calendar_combo(self):
        """Puebla el combo de calendarios con datos de DB o archivos CSV."""
        self.calendar_combo.clear()
        cals = self.cal_db.get_all_calendars()
        if cals:
            for cal in cals:
                self.calendar_combo.addItem(cal.nombre, cal)
            self.calendar_combo.setCurrentIndex(0)
        else:
            # Verificar archivos CSV existentes en la carpeta CALENDARIOS
            if os.path.exists(self.calendarios_dir):
                csv_files = [f for f in os.listdir(self.calendarios_dir) if f.endswith('.csv')]
                if csv_files:
                    for csv_file in csv_files:
                        name = os.path.splitext(csv_file)[0]
                        self.calendar_combo.addItem(name)
                    self.calendar_combo.setCurrentText("2024A")  # O el primero disponible
                else:
                    self.info_label.setText("Aún no se encuentran archivos CSV en la carpeta CALENDARIOS. No hay calendarios disponibles.")
            else:
                self.info_label.setText("No se encontró la carpeta CALENDARIOS.")
        
    def reload_calendars(self):
        """Recarga la lista de calendarios desde DB o archivos CSV."""
        previous_selection = self.calendar_combo.currentText()
        self._populate_calendar_combo()
        # Intentar mantener la selección anterior si aún existe
        if previous_selection and self.calendar_combo.findText(previous_selection) != -1:
            self.calendar_combo.setCurrentText(previous_selection)
        # Si ahora hay calendarios y antes no, cargar el primero
        if self.calendar_combo.count() > 0 and self.current_calendar_index == -1:
            self.current_calendar_index = 0
            self._on_calendar_changed()
        # Limpiar mensaje si ahora hay calendarios
        if self.calendar_combo.count() > 0:
            self.info_label.setText("0 registros")
        
    def _open_advanced_preview(self):
        """Abre la ventana con zoom y movimiento."""
        if self.current_preview_pixmap and not self.current_preview_pixmap.isNull():
            if ImagePreviewDialog:
                dialog = ImagePreviewDialog(self.current_preview_pixmap, parent=self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Error", "No se encontró image_preview_dialog.py")

    def load_data(self):
        """Carga los datos en la tabla"""
        df = self.data_manager.get_dataframe()

        if df.empty:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.info_label.setText("0 registros - No hay datos")
            self.original_df = pd.DataFrame()
            self.filtered_df = pd.DataFrame()
            self.history.clear()
            self.btn_undo.setEnabled(False)
            self.btn_redo.setEnabled(False)
            self.btn_save_all.setEnabled(False)
            return

        # Guardar datos originales
        self.original_df = df.copy()
        self.filtered_df = df.copy()
        
        # Limpiar historial al cargar nuevos datos
        self.history.clear()
        self.btn_undo.setEnabled(False)
        self.btn_redo.setEnabled(False)
        self.btn_save_all.setEnabled(False)

        # Reordenar columnas para visualización según preferencia del usuario
        preferred_display_order = [
            'Archivo', 'DESDE', 'HASTA', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'CODIGO', 'NUM',
            'CRN','HRS_TOTALES', 'MATERIA',
            'DEPENDENCIA_3', 'DEPENDENCIA_2', 'DEPENDENCIA_1',  
            'RFC', 'IMSS', 'CURP', 'TELEFONO'
        ]

        # Mapear nombres reales de columnas respetando case-insensitive
        col_map = {c.lower(): c for c in df.columns}
        ordered_cols = []
        for pref in preferred_display_order:
            if pref.lower() in col_map:
                ordered_cols.append(col_map[pref.lower()])

        # Añadir el resto de columnas que no están en ordered_cols
        remaining = [c for c in df.columns if c not in ordered_cols]
        self.original_df = self.original_df[ordered_cols + remaining]
        self.filtered_df = self.original_df.copy()

        # Si hay un CSV source establecido, iniciar el file watcher
        if self.data_manager.source_csv_file:
            self.file_watcher.set_file(self.data_manager.source_csv_file)
            self.file_watcher.start()

        # Mostrar datos
        self._populate_table(self.filtered_df)
        self.search_input.clear()

    def _populate_table(self, df):
        """Llena la tabla con los datos del dataframe"""
        self.table.blockSignals(True)  # Evitar señales mientras llenamos la tabla
        
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        # Llenar tabla
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                # Formatear valor
                text = self._format_value(value, df.columns[j])
                item = QTableWidgetItem(text)

                # Estilos
                bg_even = QColor(251, 251, 251)
                bg_odd = QColor(255, 255, 255)
                fg = QColor(11, 37, 69)

                item.setForeground(QBrush(fg))
                if i % 2 == 0:
                    item.setBackground(QBrush(bg_even))
                else:
                    item.setBackground(QBrush(bg_odd))

                self.table.setItem(i, j, item)

        # Ajustar tamaño de columnas
        self.table.resizeColumnsToContents()

        # Actualizar info
        self.info_label.setText(f"{len(df)} registros - {len(df.columns)} columnas")
        
        self.table.blockSignals(False)  # Rehabilitar señales después de llenar la tabla

        # Limpiar vista previa
        self.preview_img_label.setText("Sin visualización")
        self.preview_img_label.setPixmap(QPixmap())

    def _format_value(self, value, column_name):
        """Formatea un valor para mostrar en la tabla"""
        if pd.isna(value):
            return ""

        # Formato especial para fechas
        if 'fecha' in column_name.lower():
            try:
                return str(value)[:10]
            except Exception:
                return str(value)

        # Intentar formatear números que vienen como '1.0' a '1'
        try:
            if isinstance(value, int):
                return str(value)
            else:
                f = float(value)
                if f.is_integer():
                    return str(int(f))
                else:
                    return str(f)
        except Exception:
            return str(value)

    def apply_filter(self):
        """Aplica el filtro de búsqueda a los datos"""
        if self.original_df is None or self.original_df.empty:
            return

        search_text = self.search_input.text().lower().strip()

        if not search_text:
            # Sin búsqueda, mostrar todos los datos
            self.filtered_df = self.original_df.copy()
        else:
            # Buscar en todas las columnas
            mask = pd.Series([False] * len(self.original_df))
            for column in self.original_df.columns:
                column_mask = self.original_df[column].astype(str).str.lower().str.contains(search_text, na=False)
                mask = mask | column_mask
            self.filtered_df = self.original_df[mask].reset_index(drop=True)

        # Mostrar datos filtrados
        self._populate_table(self.filtered_df)

    def sort_by_column(self, column_index):
        """Ordena la tabla por la columna seleccionada"""
        if self.filtered_df is None or self.filtered_df.empty:
            return

        column_name = self.filtered_df.columns[column_index]

        # Alternar entre ascendente y descendente
        if not hasattr(self, 'last_sorted_column') or self.last_sorted_column != column_index:
            self.last_sorted_column = column_index
            self.sort_ascending = True
        else:
            self.sort_ascending = not self.sort_ascending

        # Ordenar
        self.filtered_df = self.filtered_df.sort_values(
            by=column_name,
            ascending=self.sort_ascending,
            na_position='last'
        ).reset_index(drop=True)

        # Mostrar datos ordenados
        self._populate_table(self.filtered_df)

    def _on_item_changed(self, item):
        """Detecta cambios en las celdas y registra en el historial"""
        if self.filtered_df is None or self.filtered_df.empty:
            return

        row = item.row()
        col = item.column()

        if row < len(self.filtered_df) and col < len(self.filtered_df.columns):
            column_name = self.filtered_df.columns[col]
            new_value = item.text()
            old_value = str(self.filtered_df.iloc[row, col])

            # Registrar en historial
            self.history.record_change(row, column_name, old_value, new_value)

            # Actualizar en datos filtrados
            self.filtered_df.iloc[row, col] = new_value

            # Actualizar en datos originales
            try:
                # Encontrar el índice en original_df
                orig_indices = self.original_df[self.original_df.index.isin(self.filtered_df.index[row:row+1])].index
                if len(orig_indices) > 0:
                    self.original_df.at[orig_indices[0], column_name] = new_value

            except Exception: pass

            # Habilitar botones de guardado y undo/redo
            self.btn_save_all.setEnabled(True)
            self.btn_undo.setEnabled(self.history.can_undo())
            self.btn_redo.setEnabled(self.history.can_redo())

    def _on_row_selected(self):
        """Cuando se selecciona una fila, mostrar la visualización"""
        selected = self.table.selectedItems()
        if selected:
            # Obtener la fila del primer ítem seleccionado
            row = selected[0].row()
            # Mostrar la visualización
            self.show_preview_for_row(row)
        else:
            # Si no hay selección, limpiar visualización
            self.preview_img_label.setText("Sin visualización")
            self.preview_img_label.setPixmap(QPixmap())

    def show_preview_for_row(self, row):
        """Muestra la miniatura y guarda el original para el visor."""
        if self.filtered_df is None or row >= len(self.filtered_df):
            return

        try:
            row_data = self.filtered_df.iloc[row]
            archivo_col = next((c for c in self.filtered_df.columns if c.lower() == 'archivo'), None)

            if archivo_col is not None:
                archivo = str(row_data[archivo_col])
                # Ajustamos la ruta según tu estructura de carpetas
                preview_name = f"Viz_{os.path.basename(archivo)}"
                preview_path = os.path.join(os.getcwd(), 'previews', preview_name)
                
                # Intentar ruta alternativa si no está en previews
                if not os.path.exists(preview_path):
                    # Ajusta esto a donde guardes las imágenes procesadas
                    preview_path = os.path.join(os.getcwd(), 'data', 'data', 'contratos', 'preview', f"Viz_{os.path.basename(archivo)}")

                if os.path.exists(preview_path):
                    pix = QPixmap(preview_path)
                    if not pix.isNull():
                        # GUARDAR ORIGINAL para que el zoom se vea bien
                        self.current_preview_pixmap = pix
                        
                        # Crear MINIATURA para el panel lateral
                        scaled = pix.scaled(
                            self.preview_img_label.width() - 5,
                            self.preview_img_label.height() - 5,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.preview_img_label.setPixmap(scaled)
                        self.preview_img_label.setText("")
                        return
            
            # Si falla algo
            self.preview_img_label.setText("Sin visualización")
            self.preview_img_label.setPixmap(QPixmap())
            self.current_preview_pixmap = None

        except Exception as e:
            print(f"Error en preview: {e}")
            self.preview_img_label.setText("Error")

    def export_data(self):
        """Exporta los datos a archivo"""
        if self.original_df is None or self.original_df.empty:
            QMessageBox.warning(self, "Sin datos", "No hay datos para exportar")
            return

        # Por defecto preferimos CSV
        file_filter = "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        default_name = f"contratos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar Datos",
            default_name,
            file_filter
        )

        if not file_path:
            return

        # Asegurar que el archivo termine en .csv
        if file_path and not file_path.lower().endswith('.csv'):
            file_path = file_path + '.csv'

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

    def save_all_to_manager(self):
        """Guarda todos los cambios realizados al data_manager y CSV del calendario"""
        try:
            # Actualizar datos del manager con el dataframe actual
            self.data_manager.data = self.original_df.copy()
            self.data_manager.save_data()
            
            if self.data_manager.source_csv_file:
                self.file_watcher.set_file(self.data_manager.source_csv_file)
            
            # Limpiar historial después de guardar
            self.history.clear()
            self.btn_save_all.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.btn_redo.setEnabled(False)
            
            self.info_label.setText("✅ Cambios guardados y monitor sincronizado")
            
            main_win = self.window() 
            if hasattr(main_win, 'sync_data_to_supabase'):
                # Llamamos a la sincronización
                main_win.sync_data_to_supabase()
            
            QTimer.singleShot(3000, lambda: self.info_label.setText(f"{len(self.original_df)} registros"))
            
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar: {e}")

    def has_unsaved_changes(self) -> bool:
        """Verifica si hay cambios sin guardar.
        
        Retorna True si hay cambios pendientes (botón 'Guardar Cambios' está habilitado)
        """
        return self.btn_save_all.isEnabled()

    def undo_change(self):
        """Deshace el último cambio."""
        changes = self.history.undo()
        if not changes:
            return
        
        # Revertir los cambios en la UI
        for change in changes:
            row = change.row_idx
            col = change.col_name
            
            if row < len(self.original_df):
                col_idx = list(self.original_df.columns).index(col)
                self.original_df.iloc[row, col_idx] = change.old_value
                
                # Si está filtrada, también actualizar
                if self.filtered_df is not None:
                    for f_row, o_idx in enumerate(self.filtered_df.index):
                        if o_idx == row:
                            self.filtered_df.iloc[f_row, col_idx] = change.old_value
                            break
        
        # Redibujar tabla
        self._populate_table(self.filtered_df)
        
        # Actualizar botones
        self.btn_save_all.setEnabled(True)
        self.btn_undo.setEnabled(self.history.can_undo())
        self.btn_redo.setEnabled(self.history.can_redo())

    def redo_change(self):
        """Rehace el último cambio deshecho."""
        changes = self.history.redo()
        if not changes:
            return
        
        # Rehacer los cambios en la UI
        for change in changes:
            row = change.row_idx
            col = change.col_name
            
            if row < len(self.original_df):
                col_idx = list(self.original_df.columns).index(col)
                self.original_df.iloc[row, col_idx] = change.new_value
                
                # Si está filtrada, también actualizar
                if self.filtered_df is not None:
                    for f_row, o_idx in enumerate(self.filtered_df.index):
                        if o_idx == row:
                            self.filtered_df.iloc[f_row, col_idx] = change.new_value
                            break
        
        # Redibujar tabla
        self._populate_table(self.filtered_df)
        
        # Actualizar botones
        self.btn_save_all.setEnabled(True)
        self.btn_undo.setEnabled(self.history.can_undo())
        self.btn_redo.setEnabled(self.history.can_redo())

    def _on_calendar_changed(self):
        """Maneja el cambio de calendario con validación de cambios pendientes."""
        
        # Verificar si hay cambios sin guardar
        if self.has_unsaved_changes():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Cambios sin guardar")
            msg_box.setText(f"Hay cambios pendientes en el calendario actual.")
            msg_box.setInformativeText("¿Deseas guardar los cambios antes de cambiar de calendario?")
            
            # Botones: Guardar, Descartar (No guardar) y Cancelar (No cambiar de pestaña)
            btn_save = msg_box.addButton("Guardar", QMessageBox.ActionRole)
            btn_discard = msg_box.addButton("Descartar", QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton("Cancelar", QMessageBox.RejectRole)
            
            msg_box.setDefaultButton(btn_save)
            msg_box.exec()
            
            clicked_button = msg_box.clickedButton()

            if clicked_button == btn_save:
                self.save_all_to_manager()
                # Después de guardar, permitimos que continúe la carga
            elif clicked_button == btn_discard:
                # No guardamos nada, simplemente permitimos que continúe la carga
                pass
            else:
                # Si eligió Cancelar, regresamos el ComboBox a su estado anterior
                self.calendar_combo.blockSignals(True)
                self.calendar_combo.setCurrentIndex(self.current_calendar_index)
                self.calendar_combo.blockSignals(False)
                return

        # Si llegamos aquí, procedemos a cargar el nuevo calendario
        self.current_calendar_index = self.calendar_combo.currentIndex()
        self.load_calendar_data()

    def load_calendar_data(self):
        """Carga los datos del calendario seleccionado."""
        calendar_name = self.calendar_combo.currentText()
        file_path = os.path.join(self.calendarios_dir, f"{calendar_name}.csv")
        if os.path.exists(file_path):
            self.data_manager.load_from_csv(file_path)
            self.load_data()
        else:
            self.info_label.setText(f"No se encuentra el archivo CSV para {calendar_name}. Verifique que el archivo exista en la carpeta CALENDARIOS.")

    def open_calendar_excel(self):
        """Abre el archivo CSV del calendario seleccionado (se abre en Excel por defecto)."""
        calendar_name = self.calendar_combo.currentText()
        file_path = os.path.join(self.calendarios_dir, f"{calendar_name}.csv")
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            self.info_label.setText(f"No se encontró el archivo CSV para {calendar_name}")

    def open_calendar_folder(self):
        """Abre la carpeta CALENDARIOS."""
        if os.path.exists(self.calendarios_dir):
            os.startfile(self.calendarios_dir)
        else:
            self.info_label.setText("No se encontró la carpeta CALENDARIOS")

    def _on_external_file_changed(self):
        """Maneja cambios externos en el CSV con validación de cambios pendientes."""
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Se detectaron cambios externos en el archivo CSV.\n\nTienes cambios sin guardar en la tabla.\n¿Deseas guardarlos antes de recargar?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if reply == QMessageBox.Save:
                self.save_all_to_manager()
            elif reply == QMessageBox.Cancel:
                return  # No recargar
            # Si Discard, continúa y recarga sin guardar
        
        # Recargar datos
        self.load_data()
        self.info_label.setText("🔄 Sincronizado con archivo externo")
        QTimer.singleShot(3000, lambda: self.info_label.setText(f"{len(self.original_df)} registros"))
        