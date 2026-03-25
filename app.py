# app.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QThread, Signal, QSettings

# Importamos el Splash Screen primero por ser ligero
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

    def __init__(self, is_first_run):
        super().__init__()
        self.is_first_run = is_first_run

    def run(self):
        try:
            # 1. Configuración de entorno
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
            
            import tensorflow as tf
            import easyocr
            
            # 2. Inicializar EasyOCR
            # Si es la primera vez, esto descargará los modelos (tarda más)
            # gpu=False para ahorrar RAM en equipos modestos
            reader = easyocr.Reader(['es', 'en'], gpu=False) 
            
            # 3. Importar ventana principal
            from ui.main_window import MainWindow
            
            self.finished_loading.emit(MainWindow)
        except Exception as e:
            self.error.emit(str(e))

def main():
    # 1. Crear la instancia de la aplicación
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Redocnizer")

    # --- LÓGICA DE PRIMERA EJECUCIÓN ---
    settings = QSettings("Redocnizer", "RedocnizerApp")
    is_first_run = settings.value("first_run_completed", "false") == "false"
    
    # 2. Mostrar pantalla de carga
    splash = SplashScreen()
    
    if is_first_run:
        if hasattr(splash, 'status_label'):
            splash.status_label.setText("Configurando IA por primera vez...\n(Esto puede tardar unos minutos)")
    
    splash.show()
    splash.raise_()
    app.processEvents()
    
    # 3. Iniciar el trabajador de carga (PASANDO EL ARGUMENTO QUE FALTABA)
    worker = LoadingWorker(is_first_run)
    
    def on_finished(MainWindowClass):
        try:
            if hasattr(splash, 'status_label'):
                splash.status_label.setText("Iniciando interfaz principal...")
            
            # Guardamos que la primera configuración ya terminó
            settings.setValue("first_run_completed", "true")
            
            window = MainWindowClass()
            splash.close()
            window.show()
            window.raise_()
        except Exception as e:
            print(f"Error al instanciar ventana: {e}")
            sys.exit(1)

    def on_error(msg):
        print(f"Error crítico de carga: {msg}")
        splash.close()
        sys.exit(1)

    worker.finished_loading.connect(on_finished)
    worker.error.connect(on_error)
    
    worker.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()