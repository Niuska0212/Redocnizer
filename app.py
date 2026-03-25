# app.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QThread, Signal

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
    """
    Hilo dedicado a cargar las librerías pesadas y la IA
    para no congelar la animación del Splash Screen.
    """
    finished_loading = Signal(object)
    error = Signal(str)

    def __init__(self, is_first_run):
        super().__init__()
        self.is_first_run = is_first_run

    def run(self):
        try:
            import tensorflow as tf
            import easyocr
            # Configuración para evitar que TF use toda la memoria al inicio
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
            
            # 1. Forzar a EasyOCR a revisar modelos
            # Al crear el Reader aquí, si no existen los modelos, los descarga.
            reader = easyocr.Reader(['es', 'en'], gpu=False) 
            
            # 2. Importar tu ventana
            from ui.main_window import MainWindow
            
            self.finished_loading.emit(MainWindow)
        except Exception as e:
            self.error.emit(str(e))

def main():
    # 1. Crear la instancia de la aplicación
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Redocnizer")
    
    # 2. Mostrar pantalla de carga inmediatamente
    splash = SplashScreen()
    splash.show()
    splash.raise_()
    
    # Aseguramos que se pinte el splash
    app.processEvents()
    
    # 3. Iniciar el trabajador de carga en segundo plano
    worker = LoadingWorker()
    
    def on_finished(MainWindowClass):
        try:
            # La instancia de la ventana DEBE crearse en el hilo principal
            if hasattr(splash, 'status_label'):
                splash.status_label.setText("Iniciando interfaz principal...")
            
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
    
    # Iniciamos el hilo de carga
    worker.start()

    # Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()