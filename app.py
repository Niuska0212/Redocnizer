# app.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
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
            # gpu=False para evitar crasheos por falta de memoria VRAM
            reader = easyocr.Reader(['es', 'en'], gpu=False) 
            
            # 3. Importar ventana principal
            from ui.main_window import MainWindow
            
            self.finished_loading.emit(MainWindow)
        except Exception as e:
            # Enviamos el error pero NO cerramos aquí
            self.error.emit(str(e))

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Redocnizer")

    settings = QSettings("Redocnizer", "RedocnizerApp")
    is_first_run = settings.value("first_run_completed", "false") == "false"
    
    splash = SplashScreen()
    
    if is_first_run:
        if hasattr(splash, 'status_label'):
            splash.status_label.setText("Configurando IA por primera vez...\n(Esto puede tardar unos minutos)")
    
    splash.show()
    splash.raise_()
    app.processEvents()
    
    worker = LoadingWorker(is_first_run)
    
    def on_finished(MainWindowClass):
        try:
            if hasattr(splash, 'status_label'):
                splash.status_label.setText("Iniciando interfaz principal...")
            
            settings.setValue("first_run_completed", "true")
            
            # Guardamos la ventana en una variable global o de app para que no desaparezca
            app.main_window = MainWindowClass()
            splash.close()
            app.main_window.show()
            app.main_window.raise_()
        except Exception as e:
            # Si falla la ventana, avisamos pero no matamos el proceso de golpe
            QMessageBox.critical(None, "Error de Interfaz", f"No se pudo abrir la ventana principal: {e}")

    def on_error(msg):
        # QUITAMOS sys.exit(1). Ahora solo avisa.
        print(f"⚠️ Advertencia de carga: {msg}")
        
        # Opcional: Mostrar un mensaje al usuario sin cerrar la app
        # Esto permite que si el error fue por algo no vital (como un log de TF), la app siga.
        if "MainWindow" not in msg: # Si el error no es que falte la ventana principal
            splash.status_label.setText("Iniciando con advertencias...")
            # Intentamos forzar la carga de la ventana de todos modos
            try:
                from ui.main_window import MainWindow
                on_finished(MainWindow)
            except:
                QMessageBox.warning(None, "Advertencia de IA", f"La IA podría no funcionar correctamente: {msg}")

    worker.finished_loading.connect(on_finished)
    worker.error.connect(on_error)
    
    worker.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()