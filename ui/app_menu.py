# ui/app_menu.py
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from PySide6.QtGui import QAction
from PySide6.QtCore import QSettings
import os
from ui.calendar_config_dialog import CalendarConfigDialog


def create_app_menu(window):
    """Crea la barra de menú de la aplicación y conecta acciones básicas.

    window: instancia de MainWindow que debe exponer `data_manager` y métodos estándar.
    """
    menubar = window.menuBar()

    # ---- Archivo ----
    file_menu = menubar.addMenu("Archivo")

    def on_open_csv():
        path, _ = QFileDialog.getOpenFileName(window, "Abrir CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            loaded = window.data_manager.load_from_csv(path)
            if loaded:
                QMessageBox.information(window, "CSV cargado", f"CSV cargado: {os.path.basename(path)}")
                # refrescar vista
                if hasattr(window, 'data_tab'):
                    window.data_tab.load_data()
            else:
                QMessageBox.warning(window, "Error", "No se pudo cargar el CSV seleccionado.")
        except Exception as e:
            QMessageBox.critical(window, "Error al abrir CSV", str(e))

    def on_save():
        try:
            window.data_manager.save_data()
            QMessageBox.information(window, "Guardado", "Datos guardados correctamente.")
        except Exception as e:
            QMessageBox.critical(window, "Error al guardar", f"No se pudo guardar: {e}")

    def on_save_as():
        path, filter_sel = QFileDialog.getSaveFileName(window, "Guardar como", "contratos_export.csv", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if not path:
            return
        try:
            if path.lower().endswith('.xlsx'):
                ok = window.data_manager.export_to_excel(path)
            else:
                ok = window.data_manager.export_to_csv(path)
            if ok:
                QMessageBox.information(window, "Guardado", f"Archivo guardado en:\n{path}")
            else:
                QMessageBox.critical(window, "Error", "No se pudo guardar el archivo.")
        except Exception as e:
            QMessageBox.critical(window, "Error al guardar", str(e))

    def on_exit():
        # Confirmar salida
        reply = QMessageBox.question(window, "Salir", "¿Desea salir de la aplicación?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            window.close()

    act_open = QAction("Abrir CSV...", window)
    act_open.triggered.connect(on_open_csv)
    file_menu.addAction(act_open)

    act_save = QAction("Guardar", window)
    act_save.triggered.connect(on_save)
    file_menu.addAction(act_save)

    act_saveas = QAction("Guardar como...", window)
    act_saveas.triggered.connect(on_save_as)
    file_menu.addAction(act_saveas)

    file_menu.addSeparator()

    act_exit = QAction("Salir", window)
    act_exit.triggered.connect(on_exit)
    file_menu.addAction(act_exit)

    # ---- Edit (Undo/Redo) ----
    edit_menu = menubar.addMenu("Editar")

    act_undo = QAction("Deshacer", window)
    act_undo.setShortcut("Ctrl+Z")
    
    def on_undo():
        if hasattr(window, 'data_tab') and hasattr(window.data_tab, 'undo_change'):
            window.data_tab.undo_change()
    
    act_undo.triggered.connect(on_undo)
    edit_menu.addAction(act_undo)

    act_redo = QAction("Rehacer", window)
    act_redo.setShortcut("Ctrl+Y")
    
    def on_redo():
        if hasattr(window, 'data_tab') and hasattr(window.data_tab, 'redo_change'):
            window.data_tab.redo_change()
    
    act_redo.triggered.connect(on_redo)
    edit_menu.addAction(act_redo)
    
    # ---- NUEVO MENÚ: Herramientas (Limpieza de emergencia) ----
    tools_menu = menubar.addMenu("Herramientas")

    def on_clear_previews():
        """Acción de emergencia para borrar imágenes de preview."""
        reply = QMessageBox.warning(
            window, 
            "Limpieza de Emergencia", 
            "¿Estás seguro de que deseas eliminar TODAS las imágenes de vista previa?\n\n"
            "Esto liberará espacio en disco, pero no podrás ver las imágenes en la tabla hasta procesar de nuevo.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if hasattr(window, 'controller') and window.controller:
                window.controller.limpiar_previews()
                # Limpiar el visualizador actual para que no intente mostrar algo borrado
                if hasattr(window, 'data_tab'):
                    window.data_tab.preview_img_label.clear()
                    window.data_tab.preview_img_label.setText("Vistas previas eliminadas.")
                QMessageBox.information(window, "Limpieza Completa", "Se han eliminado los archivos de vista previa correctamente.")
            else:
                QMessageBox.critical(window, "Error", "El controlador no está inicializado.")

    act_clear_cache = QAction("🧹 Vaciar carpeta de Previews", window)
    act_clear_cache.triggered.connect(on_clear_previews)
    tools_menu.addAction(act_clear_cache)

    # ---- Configuración ----
    config_menu = menubar.addMenu("Configuración")
    
    #ACcion para activar o desactivar aceleracion GPU
    settings = QSettings("CUCEI", "Redocnizer")
    # Leemos el estado actual (por defecto False)
    gpu_enabled = settings.value("use_gpu_acceleration", False, type=bool)
    
    act_gpu = QAction("🚀 Usar Aceleración GPU (NVIDIA)", window, checkable=True)
    act_gpu.setChecked(gpu_enabled)
    
    def on_toggle_gpu(checked):
        settings.setValue("use_gpu_acceleration", checked)
        if checked:
            QMessageBox.information(window, "Aceleración GPU", 
                "Has activado la GPU. Reicia la aplicación para aplicar los cambios.\n\n"
                "Nota: Requiere tarjeta NVIDIA y drivers CUDA instalados.")
        else:
            QMessageBox.information(window, "Aceleración GPU", 
                "Se usará el Procesador (CPU) para el próximo procesamiento.")

    act_gpu.triggered.connect(on_toggle_gpu)
    config_menu.addAction(act_gpu)

    def on_config_calendar():
        dialog = CalendarConfigDialog(window)
        if dialog.exec() == QDialog.Accepted:
            calendar = dialog.get_selected_calendar()
            if calendar:
                # Actualizar combo de calendarios en la ventana
                if hasattr(window, 'calendar_combo'):
                    window.calendar_combo.setCurrentText(calendar.nombre)
                QMessageBox.information(window, "Calendario", f"Calendario '{calendar.nombre}' seleccionado.\nPeríodo: {calendar.fecha_inicio} a {calendar.fecha_fin}")

    act_config = QAction("Configurar Calendarios", window)
    act_config.triggered.connect(on_config_calendar)
    config_menu.addAction(act_config)

    return menubar


