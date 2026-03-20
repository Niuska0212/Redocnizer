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


class DirectoryWatcher(QObject):
    """Monitorea un directorio (recursivamente) y emite nuevas rutas encontradas."""

    new_files = Signal(list)  # lista de rutas absolutas nuevas

    def __init__(self, dir_path: str = None, check_interval: int = 3000):
        super().__init__()
        self.dir_path = dir_path
        self.check_interval = check_interval
        self.timer = QTimer()
        self.timer.timeout.connect(self._scan)
        self._seen = set()
        self.enabled = False

    def set_dir(self, dir_path: str):
        self.dir_path = dir_path
        self._seen = set()
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path):
                for f in files:
                    self._seen.add(os.path.join(root, f))

    def start(self):
        if self.dir_path and os.path.exists(self.dir_path):
            self.enabled = True
            self.timer.start(self.check_interval)

    def stop(self):
        self.enabled = False
        self.timer.stop()

    def _scan(self):
        if not self.enabled or not self.dir_path or not os.path.exists(self.dir_path):
            return
        new = []
        try:
            for root, dirs, files in os.walk(self.dir_path):
                for f in files:
                    path = os.path.join(root, f)
                    if path not in self._seen:
                        self._seen.add(path)
                        new.append(path)
            if new:
                self.new_files.emit(new)
        except Exception as e:
            print(f"Error en DirectoryWatcher: {e}")
