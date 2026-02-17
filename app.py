# app.py

import sys
from PySide6.QtWidgets import QApplication  #pip install PySide6
from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # mostrar pantalla de carga inmediatamente
    splash = SplashScreen()
    splash.show()
    app.processEvents()  # Asegura que la pantalla de carga se muestre antes
    
    # Aquí se cargaría la IA y TensorFlow, lo que puede tardar varios segundos
    window = MainWindow()
    
    # una vez que la ventana principal esté lista, cerramos la pantalla de carga
    splash.close()
    
    window.show()
    window.raise_()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

