import os
import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QGridLayout, QLineEdit, QHeaderView,
    QAbstractItemView, QListWidget, QListWidgetItem, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QBrush

from services.pdf_service import pdf_to_images


class DataTab(QWidget):
    """Pestaña para visualizar y editar datos (extraída de main_window.py)."""

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

        # Conectar doble clic para editar
        self.table.cellDoubleClicked.connect(self.start_edit_cell)
        self.table.itemSelectionChanged.connect(self.table_selection_changed)

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

        # Mostrar la tabla junto con la vista previa a la derecha
        table_preview_layout = QHBoxLayout()
        table_preview_layout.addWidget(self.table, 3)

        self.preview_img_label = QLabel()
        self.preview_img_label.setObjectName("preview_label_data")
        self.preview_img_label.setFixedSize(250, 350)
        self.preview_img_label.setStyleSheet("""
            QLabel { border: 2px dashed rgba(25,118,210,0.18); border-radius: 8px; background-color: #ffffff; color: #0b2545; qproperty-alignment: AlignCenter; font-weight: 600; }
        """)
        self.preview_img_label.setText("Sin visualización")

        table_preview_layout.addWidget(self.preview_img_label, 0)
        layout.addLayout(table_preview_layout)

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

        # Reordenar columnas para visualización según preferencia del usuario
        preferred_display_order = [
            'Archivo', 'PATERNO', 'MATERNO', 'NOMBRE_S', 'CODIGO', 'NUM',
            'RFC', 'IMSS', 'CURP', 'CRN', 'TELEFONO', 'DESDE', 'HASTA',
            'DEPENDENCIA_1', 'DEPENDENCIA_2', 'DEPENDENCIA_3'
        ]

        # Mapear nombres reales de columnas respetando case-insensitive
        col_map = {c.lower(): c for c in df.columns}
        ordered_cols = []
        for pref in preferred_display_order:
            if pref.lower() in col_map:
                ordered_cols.append(col_map[pref.lower()])

        # Añadir el resto de columnas que no están en ordered_cols, preservando orden original
        remaining = [c for c in df.columns if c not in ordered_cols]
        df = df[ordered_cols + remaining]

        # Configurar tabla
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        # Llenar tabla
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                text = str(value) if not pd.isna(value) else ""
                # Formato especial para fechas
                if 'fecha' in df.columns[j].lower() and not pd.isna(value):
                    try:
                        text = str(value)[:10]
                    except:
                        pass

                item = QTableWidgetItem(text)

                # Fondo claro y contraste de texto garantizado
                bg_even = QColor(251, 251, 251)
                bg_odd = QColor(255, 255, 255)
                fg = QColor(11, 37, 69)  # #0b2545

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

        # Limpiar vista previa
        try:
            if hasattr(self, 'preview_img_label'):
                self.preview_img_label.setText("Sin visualización")
                self.preview_img_label.setPixmap(QPixmap())
        except Exception:
            pass

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

        # Asegurar que el archivo termine en .csv (guardamos CSV siempre)
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

            # Cargar visualización generada por document_extractor (Vizualizacion_<Archivo>)
            try:
                archivo_col = next((c for c in df.columns if c.lower() == 'archivo'), None)
                if archivo_col is not None:
                    archivo = row_data[archivo_col]
                    if pd.isna(archivo) or not str(archivo).strip():
                        self.preview_img_label.setText("Sin visualización")
                        self.preview_img_label.setPixmap(QPixmap())
                    else:
                        preview_name = f"Vizualizacion_{os.path.basename(str(archivo))}"
                        preview_path = os.path.join(os.getcwd(), 'previews', preview_name)
                        if os.path.exists(preview_path):
                            pix = QPixmap(preview_path)
                            if not pix.isNull():
                                pix = pix.scaled(self.preview_img_label.width(), self.preview_img_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                self.preview_img_label.setPixmap(pix)
                                self.preview_img_label.setText("")
                            else:
                                self.preview_img_label.setText("Sin visualización")
                                self.preview_img_label.setPixmap(QPixmap())
                        else:
                            self.preview_img_label.setText("Sin visualización")
                            self.preview_img_label.setPixmap(QPixmap())
                else:
                    self.preview_img_label.setText("Sin visualización")
                    self.preview_img_label.setPixmap(QPixmap())
            except Exception:
                pass
