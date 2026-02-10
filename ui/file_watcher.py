# ui/file_watcher.py
"""Monitor de cambios de archivos para sincronización bidireccional."""

import os
import time
from PySide6.QtCore import QObject, Signal, QTimer


class FileWatcher(QObject):
    """Monitorea cambios en un archivo CSV."""
    
    file_changed = Signal()  # Se emite cuando el archivo cambió
    
    def __init__(self, file_path: str = None, check_interval: int = 2000):
        """
        file_path: Ruta del archivo a monitorear
        check_interval: Intervalo de verificación en milisegundos
        """
        super().__init__()
        self.file_path = file_path
        self.check_interval = check_interval
        self.last_modified = 0
        self.enabled = False
        
        # Timer para verificaciones periódicas
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_file)
    
    def set_file(self, file_path: str):
        """Establece el archivo a monitorear."""
        self.file_path = file_path
        if os.path.exists(file_path):
            self.last_modified = os.path.getmtime(file_path)
        else:
            self.last_modified = 0
    
    def start(self):
        """Inicia el monitoreo."""
        if self.file_path and os.path.exists(self.file_path):
            self.enabled = True
            self.last_modified = os.path.getmtime(self.file_path)
            self.timer.start(self.check_interval)
    
    def stop(self):
        """Detiene el monitoreo."""
        self.enabled = False
        self.timer.stop()
    
    def _check_file(self):
        """Verifica si el archivo ha cambiado."""
        if not self.enabled or not self.file_path or not os.path.exists(self.file_path):
            return
        
        try:
            current_modified = os.path.getmtime(self.file_path)
            
            # Si el archivo fue modificado externamente
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                self.file_changed.emit()
        
        except Exception as e:
            print(f"Error en file watcher: {e}")
