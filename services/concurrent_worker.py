# services/concurrent_worker.py

import os
import gc
import psutil # Opcional: para monitoreo real
from PySide6.QtCore import QThread, Signal, QRunnable, QThreadPool, QObject

class WorkerSignals(QObject):
    finished = Signal(str, dict)
    error = Signal(str)

class OCRTask(QRunnable):
    def __init__(self, file_path, calendar, controller):
        super().__init__()
        self.file_path = file_path
        self.calendar = calendar
        self.controller = controller
        self.signals = WorkerSignals()

    def run(self):
        nombre_archivo = os.path.basename(self.file_path)
        try:
            # Procesamiento
            res = self.controller.process_uploaded_file(file_path=self.file_path, calendar=self.calendar)
            
            if res.get("data"):
                self.signals.finished.emit(
                    f"✅ {nombre_archivo} -> {res.get('final_path', 'N/A')}", 
                    {"status": "success", "file": nombre_archivo, "data": res["data"]}
                )
            else:
                raise Exception("Datos no detectados")
        except Exception as e:
            self.signals.error.emit(f"❌ {nombre_archivo}: {str(e)}")
        finally:
            # LIMPIEZA AGRESIVA: Forzamos liberación de memoria tras cada tarea
            gc.collect()

class ConcurrentOCRWorker(QThread):
    progress = Signal(int, str)           
    file_finished = Signal(str, dict)      
    all_finished = Signal(int, int, list)  
    error = Signal(str)                    

    def __init__(self, file_paths, calendar, controller):
        super().__init__()
        self.file_paths = file_paths
        self.calendar = calendar
        self.controller = controller
        self.results_list = []
        self.successful = 0
        self.failed = 0
        self.processed_count = 0
        self.pending = 0

    def run(self):
        total = len(self.file_paths)
        if total == 0: return

        self.pending = total
        pool = QThreadPool.globalInstance()
        
        # AJUSTE SEGURO: 2 hilos para mantener estabilidad en 16GB RAM
        # Puedes probar con 3 si ves que la RAM no llega al 85%
        pool.setMaxThreadCount(2) 

        for fp in self.file_paths:
            task = OCRTask(fp, self.calendar, self.controller)
            task.signals.finished.connect(self._on_task_finished)
            task.signals.error.connect(self._on_task_error)
            pool.start(task)

        # No esperamos aquí, las señales manejarán el final

    def _on_task_finished(self, text, result):
        self.successful += 1
        self.results_list.append(result)
        self.file_finished.emit(text, result)
        self._report_progress()
        self.pending -= 1
        if self.pending == 0:
            self.all_finished.emit(self.successful, self.failed, self.results_list)

    def _on_task_error(self, error_msg):
        self.failed += 1
        self.results_list.append({"status": "error"})
        self.file_finished.emit(error_msg, {"status": "error"})
        self._report_progress()
        self.pending -= 1
        if self.pending == 0:
            self.all_finished.emit(self.successful, self.failed, self.results_list)

    def _report_progress(self):
        self.processed_count += 1
        percent = int((self.processed_count / len(self.file_paths)) * 100)
        self.progress.emit(percent, f"Procesado {self.processed_count} de {len(self.file_paths)}")