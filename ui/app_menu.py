# ui/app_menu.py
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QSettings
import os
from ui.calendar_config_dialog import CalendarConfigDialog


def create_app_menu(window):
    """Crea la barra de menú de la aplicación con atajos y ayuda.

    window: instancia de MainWindow que debe exponer `data_manager` y métodos estándar.
    """
    menubar = window.menuBar()

    # ---- MENÚ: ARCHIVO ----
    file_menu = menubar.addMenu("Archivo")

    # Abrir con atajo Ctrl+O
    act_open = QAction("Abrir CSV...", window)
    act_open.setShortcut(QKeySequence.Open)
    act_open.triggered.connect(lambda: on_open_csv(window))
    file_menu.addAction(act_open)

    # Guardar con atajo Ctrl+S (Llamando a la nueva lógica de sincronización)
    act_save = QAction("Guardar", window)
    act_save.setShortcut(QKeySequence.Save)
    act_save.triggered.connect(lambda: on_save(window))
    file_menu.addAction(act_save)

    # Guardar como con atajo Ctrl+Shift+S
    act_saveas = QAction("Guardar como...", window)
    act_saveas.setShortcut("Ctrl+Shift+S")
    act_saveas.triggered.connect(lambda: on_save_as(window))
    file_menu.addAction(act_saveas)

    file_menu.addSeparator()

    # Salir con Alt+F4
    act_exit = QAction("Salir", window)
    act_exit.setShortcut("Alt+F4")
    act_exit.triggered.connect(lambda: on_exit(window))
    file_menu.addAction(act_exit)

    # ---- MENÚ: EDITAR ----
    edit_menu = menubar.addMenu("Editar")

    # Deshacer con Ctrl+Z
    act_undo = QAction("Deshacer", window)
    act_undo.setShortcut(QKeySequence.Undo)
    act_undo.triggered.connect(lambda: on_undo(window))
    edit_menu.addAction(act_undo)

    # Rehacer con Ctrl+Y
    act_redo = QAction("Rehacer", window)
    act_redo.setShortcut(QKeySequence.Redo)
    act_redo.triggered.connect(lambda: on_redo(window))
    edit_menu.addAction(act_redo)

    # ---- MENÚ: HERRAMIENTAS ----
    tools_menu = menubar.addMenu("Herramientas")

    act_clear_cache = QAction("🧹 Vaciar carpeta de Previews", window)
    act_clear_cache.triggered.connect(lambda: on_clear_previews(window))
    tools_menu.addAction(act_clear_cache)

    # ---- MENÚ: CONFIGURACIÓN ----
    config_menu = menubar.addMenu("Configuración")
    
    settings = QSettings("CUCEI", "Redocnizer")
    gpu_enabled = settings.value("use_gpu_acceleration", False, type=bool)
    
    act_gpu = QAction("🚀 Usar Aceleración GPU (NVIDIA)", window, checkable=True)
    act_gpu.setChecked(gpu_enabled)
    act_gpu.triggered.connect(lambda checked: on_toggle_gpu(window, checked, settings))
    config_menu.addAction(act_gpu)

    act_config = QAction("Configurar Calendarios", window)
    act_config.triggered.connect(lambda: on_config_calendar(window))
    config_menu.addAction(act_config)

    # ---- MENÚ: AYUDA ----
    help_menu = menubar.addMenu("Ayuda")

    act_about = QAction("Acerca de REDOCNIZER", window)
    act_about.triggered.connect(lambda: on_about(window))
    help_menu.addAction(act_about)

    act_shortcuts = QAction("Atajos de Teclado", window)
    act_shortcuts.triggered.connect(lambda: on_show_shortcuts(window))
    help_menu.addAction(act_shortcuts)

    return menubar


# --- FUNCIONES DE SOPORTE PARA EL MENÚ ---

def on_open_csv(window):
    path, _ = QFileDialog.getOpenFileName(window, "Abrir CSV", "", "CSV Files (*.csv);;All Files (*)")
    if not path:
        return
    try:
        if window.data_manager.load_from_csv(path):
            QMessageBox.information(window, "CSV cargado", f"CSV cargado: {os.path.basename(path)}")
            if hasattr(window, 'data_tab'):
                window.data_tab.load_data()
        else:
            QMessageBox.warning(window, "Error", "No se pudo cargar el CSV.")
    except Exception as e:
        QMessageBox.critical(window, "Error al abrir CSV", str(e))

def on_save(window):
    """Llama a la lógica de guardado de la pestaña de datos para asegurar sincronización."""
    try:
        if hasattr(window, 'data_tab'):
            # Usamos el método de data_tab porque actualiza el watcher y el historial
            window.data_tab.save_all_to_manager()
        else:
            # Fallback si por alguna razón no existe la pestaña
            window.data_manager.save_data()
            QMessageBox.information(window, "Guardado", "Datos guardados correctamente.")
    except Exception as e:
        QMessageBox.critical(window, "Error al guardar", f"No se pudo guardar: {e}")

def on_save_as(window):
    path, _ = QFileDialog.getSaveFileName(window, "Guardar como", "contratos_export.csv", "CSV Files (*.csv);;Excel Files (*.xlsx)")
    if not path:
        return
    try:
        ok = window.data_manager.export_to_excel(path) if path.lower().endswith('.xlsx') else window.data_manager.export_to_csv(path)
        if ok:
            QMessageBox.information(window, "Guardado", f"Archivo guardado en:\n{path}")
        else:
            QMessageBox.critical(window, "Error", "No se pudo guardar el archivo.")
    except Exception as e:
        QMessageBox.critical(window, "Error al guardar", str(e))

def on_exit(window):
    reply = QMessageBox.question(window, "Salir", "¿Desea salir de la aplicación?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
        window.close()

def on_undo(window):
    if hasattr(window, 'data_tab'):
        window.data_tab.undo_change()

def on_redo(window):
    if hasattr(window, 'data_tab'):
        window.data_tab.redo_change()

def on_clear_previews(window):
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

def on_toggle_gpu(window, checked, settings):
    settings.setValue("use_gpu_acceleration", checked)
    msg = "GPU activada. Reinicia la app." if checked else "Se usará CPU."
    QMessageBox.information(window, "Aceleración GPU", msg)

def on_config_calendar(window):
    """Abre el diálogo de configuración de calendarios."""
    dialog = CalendarConfigDialog(window)
    if dialog.exec() == QDialog.Accepted:
        calendar = dialog.get_selected_calendar()
        if calendar:
            # Actualizar combo de calendarios en la ventana principal
            if hasattr(window, 'calendar_combo'):
                window.calendar_combo.setCurrentText(calendar.nombre)
            QMessageBox.information(window, "Calendario", f"Calendario '{calendar.nombre}' seleccionado.")

def on_about(window):
    QMessageBox.about(
        window, 
        "Acerca de REDOCNIZER",
        "<h3>REDOCNIZER v1.1.1</h3>"
        "<p>Herramienta avanzada para la gestión y OCR de documentos PDF.</p>"
        "<p><b>Características:</b><br>"
        "- Edición directa en tabla (doble clic).<br>"
        "- Sincronización automática de archivos.<br>"
        "- Historial de cambios (Deshacer/Rehacer).</p>"
        "<p>Hecho por:<br>"
        "<b>NIUSKA ISABEL GONZALEZ RANGEL Y LUIS DIEGO URIBE SANDOVAL</b>.</p>"
        "<p>Desarrollado para <b>CUCEI</b>.</p>"
    )

def on_show_shortcuts(window):
    QMessageBox.information(
        window,
        "Atajos de Teclado",
        "<b>Archivo:</b><br>"
        "• Ctrl + O : Abrir archivo<br>"
        "• Ctrl + S : Guardar cambios<br>"
        "• Alt + F4 : Salir<br><br>"
        "<b>Edición:</b><br>"
        "• Ctrl + Z : Deshacer<br>"
        "• Ctrl + Y : Rehacer<br>"
        "• Doble Clic : Editar celda"
    )