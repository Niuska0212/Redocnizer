# app.py - Punto de entrada principal de la aplicación Redocnizer
import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal, QSettings

# Importamos el Splash Screen primero por ser muy ligero
from ui.splash_screen import SplashScreen

def resource_path(relative_path):
    """ Obtiene la ruta absoluta de los recursos, compatible con PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoadingWorker(QThread):
    finished_loading = Signal(object)
    error = Signal(str)

    def run(self):
        try:
            # 1. Silenciar logs de TensorFlow/IA para un inicio limpio
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            
            # 2. Importación de la ventana principal
            # Esto se hace aquí para que el Splash Screen se vea mientras Python carga la UI
            from ui.main_window import MainWindow
            
            # Emitimos la clase lista para usarse
            self.finished_loading.emit(MainWindow)
            
        except Exception as e:
            # Si algo falla (ej. falta una librería), avisamos
            self.error.emit(str(e))

def main():
    # Solución al error de DPI: Intentar configurar, pero ignorar si falla

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Recuperar ajustes de la aplicación
    settings = QSettings("Redocnizer", "RedocnizerApp")
    is_first_run = settings.value("first_run_completed", "false") == "false"
    
    # Mostrar Splash Screen
    splash = SplashScreen()
    if hasattr(splash, 'status_label'):
        splash.status_label.setText("Iniciando componentes...")
    
    splash.show()
    splash.raise_()
    
    # Forzar a la app a procesar el dibujo del Splash
    app.processEvents()
    
    # Crear y configurar el Worker
    worker = LoadingWorker()
    
    def on_finished(MainWindowClass):
        try:
            # Guardamos el estado del primer inicio
            settings.setValue("first_run_completed", "true")
            
            # Creamos la instancia de la ventana principal
            app.main_window = MainWindowClass()
            
            # Cerramos splash y mostramos ventana
            splash.close()
            app.main_window.show()
            app.main_window.raise_()
            print("✅ Aplicación iniciada correctamente.")
            
        except Exception as e:
            QMessageBox.critical(None, "Error de Interfaz", f"No se pudo mostrar la ventana: {e}")

    def on_error(msg):
        splash.close()
        QMessageBox.critical(None, "Error Crítico", f"Fallo al cargar la aplicación:\n{msg}")
        sys.exit(1)

    # Conectar señales
    worker.finished_loading.connect(on_finished)
    worker.error.connect(on_error)
    
    # Iniciar la carga en segundo plano
    worker.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()