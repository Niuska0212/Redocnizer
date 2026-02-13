import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QFileDialog, QMessageBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QColor, QBrush, QWheelEvent

from services.pdf_service import pdf_to_images
from ui.history_manager import HistoryManager
from ui.edit_record_dialog import EditRecordDialog
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
        self.btn_reload = QPushButton("🔄 Recargar")
        self.btn_reload.clicked.connect(self.load_data)
        self.btn_reload.setMaximumWidth(100)

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
        controls_layout.addWidget(self.btn_reload)
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
        self.table.doubleClicked.connect(self._on_row_double_clicked)

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
        layout.addLayout(table_preview_layout)
        self.setLayout(layout)
        
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
            'Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'CODIGO', 'NUM',
            'CRN','HRS_TOTALES', 'MATERIA', 'DESDE', 'HASTA', 'TELEFONO',
            'DEPENDENCIA_3', 'DEPENDENCIA_2', 'DEPENDENCIA_1',  
            'RFC', 'IMSS', 'CURP'
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
            
            # Limpiar historial después de guardar
            self.history.clear()
            self.btn_save_all.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.btn_redo.setEnabled(False)
            
            QMessageBox.information(
                self,
                "Guardado",
                "✅ Todos los cambios han sido guardados correctamente"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al guardar",
                f"No se pudo guardar: {e}"
            )

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

    def _on_row_double_clicked(self, index):
        """Cuando se hace doble clic en una fila, abre el modal de edición."""
        row = index.row()
        if row < 0 or self.filtered_df is None:
            return
        
        # Obtener datos de la fila
        row_data = self.filtered_df.iloc[row].to_dict()
        column_names = list(self.filtered_df.columns)
        
        # Abrir modal
        accepted, edited_data = EditRecordDialog.edit_record(
            parent=self,
            row_data=row_data,
            column_names=column_names
        )
        
        if accepted:
            # Actualizar la fila con los nuevos datos
            for col_name, new_value in edited_data.items():
                old_value = row_data.get(col_name, "")
                
                if old_value != new_value:
                    # Registrar el cambio en el historial
                    self.history.record_change(row, col_name, old_value, new_value)
                    
                    # Actualizar en filtered_df
                    col_idx = list(self.filtered_df.columns).index(col_name)
                    self.filtered_df.iloc[row, col_idx] = new_value
                    
                    # Actualizar en original_df
                    orig_row = self.original_df[self.original_df.index.isin(self.filtered_df.index[row:row+1])].index
                    if len(orig_row) > 0:
                        self.original_df.at[orig_row[0], col_name] = new_value
            
            # Redibujar tabla
            self._populate_table(self.filtered_df)
            
            # Actualizar estado de botones
            self.btn_save_all.setEnabled(True)
            self.btn_undo.setEnabled(self.history.can_undo())
            self.btn_redo.setEnabled(self.history.can_redo())

    def _on_external_file_changed(self):
        """Se ejecuta cuando el CSV externo fue modificado."""
        reply = QMessageBox.question(
            self,
            "Archivo Modificado",
            "El archivo CSV ha sido modificado externamente.\n¿Desea recargar los cambios?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.load_data()
