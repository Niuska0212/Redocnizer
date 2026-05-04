# """Diálogo para configurar calendarios (nuevo/existente)."""
# # ui/calendar_config_dialog.py
# from PySide6.QtWidgets import (
#     QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
#     QComboBox, QDateEdit, QPushButton, QMessageBox, QRadioButton, QButtonGroup
# )
# from PySide6.QtCore import Qt, QDate
# from ui.calendar_db import Calendar, CalendarDB


# class CalendarConfigDialog(QDialog):
#     """Diálogo para crear o seleccionar un calendario."""
    
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Configurar Calendario")
#         self.setModal(True)
#         self.resize(500, 450)
        
#         self.db = CalendarDB()
#         self.selected_calendar = None
        
#         self.setup_ui()
    
#     def setup_ui(self):
#         layout = QVBoxLayout()
        
#         # Opción: nuevo o existente
#         option_group = QGroupBox("Seleccionar Calendario")
#         option_layout = QVBoxLayout()
        
#         self.btn_group = QButtonGroup()
        
#         self.rb_existing = QRadioButton("Usar calendario existente")
#         self.rb_new = QRadioButton("Crear nuevo calendario")
#         self.rb_existing.setChecked(True)
        
#         self.btn_group.addButton(self.rb_existing, 0)
#         self.btn_group.addButton(self.rb_new, 1)
        
#         option_layout.addWidget(self.rb_existing)
#         option_layout.addWidget(self.rb_new)
#         option_group.setLayout(option_layout)
        
#         # Panel: Calendario existente
#         existing_group = QGroupBox("Calendarios Disponibles")
#         existing_layout = QVBoxLayout()
        
#         self.combo_calendars = QComboBox()
#         self._load_calendars()
        
#         existing_layout.addWidget(self.combo_calendars)
#         existing_group.setLayout(existing_layout)
        
#         # Panel: Nuevo calendario
#         new_group = QGroupBox("Nuevo Calendario")
#         new_layout = QVBoxLayout()
        
#         # Nombre
#         name_layout = QHBoxLayout()
#         name_layout.addWidget(QLabel("Nombre:"))
#         self.input_nombre = QLineEdit()
#         self.input_nombre.setPlaceholderText("ej: 2024A")
#         name_layout.addWidget(self.input_nombre)
#         new_layout.addLayout(name_layout)
        
#         # Tipo
#         type_layout = QHBoxLayout()
#         type_layout.addWidget(QLabel("Tipo:"))
#         self.combo_tipo = QComboBox()
#         self.combo_tipo.addItems(["Actual", "Pasado"])
#         type_layout.addWidget(self.combo_tipo)
#         new_layout.addStretch()
#         new_layout.addLayout(type_layout)
        
#         # Fechas
#         dates_layout = QVBoxLayout()
        
#         start_layout = QHBoxLayout()
#         start_layout.addWidget(QLabel("Fecha Inicio (DD/MM/YYYY):"))
#         self.input_fecha_inicio = QLineEdit()
#         self.input_fecha_inicio.setPlaceholderText("01/01/2024")
#         start_layout.addWidget(self.input_fecha_inicio)
#         dates_layout.addLayout(start_layout)
        
#         end_layout = QHBoxLayout()
#         end_layout.addWidget(QLabel("Fecha Fin (DD/MM/YYYY):"))
#         self.input_fecha_fin = QLineEdit()
#         self.input_fecha_fin.setPlaceholderText("30/06/2024")
#         end_layout.addWidget(self.input_fecha_fin)
#         dates_layout.addLayout(end_layout)
        
#         new_layout.addLayout(dates_layout)
#         new_group.setLayout(new_layout)
        
#         # Conectar cambios
#         self.rb_existing.toggled.connect(self._on_option_changed)
#         self.rb_new.toggled.connect(self._on_option_changed)
        
#         # Botones de acción
#         button_layout = QHBoxLayout()
        
#         btn_ok = QPushButton("Aceptar")
#         btn_cancel = QPushButton("Cancelar")
        
#         btn_ok.clicked.connect(self.accept)
#         btn_cancel.clicked.connect(self.reject)
        
#         button_layout.addWidget(btn_ok)
#         button_layout.addWidget(btn_cancel)
        
#         # Ensamblar
#         layout.addWidget(option_group)
#         layout.addWidget(existing_group)
#         layout.addWidget(new_group)
#         layout.addLayout(button_layout)
        
#         self.setLayout(layout)
        
#         # Actualizar estado inicial
#         self._on_option_changed()
    
#     def _load_calendars(self):
#         """Carga los calendarios disponibles en el combo."""
#         self.combo_calendars.clear()
#         calendars = self.db.get_all_calendars()
#         for cal in calendars:
#             self.combo_calendars.addItem(cal.nombre, cal)
    
#     def _on_option_changed(self):
#         """Habilita/deshabilita campos según la opción seleccionada."""
#         is_existing = self.rb_existing.isChecked()
        
#         self.combo_calendars.setEnabled(is_existing)
#         self.input_nombre.setEnabled(not is_existing)
#         self.combo_tipo.setEnabled(not is_existing)
#         self.input_fecha_inicio.setEnabled(not is_existing)
#         self.input_fecha_fin.setEnabled(not is_existing)
    
#     def accept(self):
#         """Procesa la selección/creación del calendario."""
#         if self.rb_existing.isChecked():
#             # Usar calendario existente
#             if self.combo_calendars.count() == 0:
#                 QMessageBox.warning(self, "Error", "No hay calendarios disponibles.")
#                 return
#             self.selected_calendar = self.combo_calendars.currentData()
#         else:
#             # Crear nuevo calendario
#             nombre = self.input_nombre.text().strip()
#             tipo = self.combo_tipo.currentText().lower()
#             fecha_inicio = self.input_fecha_inicio.text().strip()
#             fecha_fin = self.input_fecha_fin.text().strip()
            
#             # Validar
#             if not nombre:
#                 QMessageBox.warning(self, "Error", "Ingrese el nombre del calendario.")
#                 return
#             if not fecha_inicio or not fecha_fin:
#                 QMessageBox.warning(self, "Error", "Ingrese ambas fechas (DD/MM/YYYY).")
#                 return
#             if not self._validate_date_format(fecha_inicio) or not self._validate_date_format(fecha_fin):
#                 QMessageBox.warning(self, "Error", "Formato de fecha inválido. Use DD/MM/YYYY.")
#                 return
            
#             # Verificar que no exista
#             if self.db.calendar_exists(nombre):
#                 QMessageBox.warning(self, "Error", f"El calendario '{nombre}' ya existe.")
#                 return
            
#             # Crear
#             cal = Calendar(
#                 nombre=nombre,
#                 tipo=tipo,
#                 fecha_inicio=fecha_inicio,
#                 fecha_fin=fecha_fin,
#                 ruta_base=""  # Se establecerá después
#             )
#             cal_id = self.db.add_calendar(cal)
#             if cal_id > 0:
#                 self.selected_calendar = self.db.get_calendar(nombre)
#                 QMessageBox.information(self, "Éxito", f"Calendario '{nombre}' creado correctamente.")
#             else:
#                 QMessageBox.critical(self, "Error", "No se pudo crear el calendario.")
#                 return
        
#         super().accept()
    
#     def _validate_date_format(self, date_str: str) -> bool:
#         """Valida que la fecha esté en formato DD/MM/YYYY."""
#         try:
#             parts = date_str.split("/")
#             if len(parts) != 3:
#                 return False
#             day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
#             return 1 <= day <= 31 and 1 <= month <= 12 and year >= 2000
#         except ValueError:
#             return False
    
#     def get_selected_calendar(self) -> Calendar:
#         """Retorna el calendario seleccionado/creado."""
#         return self.selected_calendar
