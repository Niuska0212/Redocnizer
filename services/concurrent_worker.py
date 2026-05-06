# services/concurrent_worker.py
"""
Worker concurrente optimizado para máximo 16GB RAM sin GPU.
Monitoreo automático en background, sin UI visible.
"""

import os
import gc
import time
from PySide6.QtCore import QThread, Signal, QRunnable, QThreadPool, QObject

from services.memory_monitor import MemoryMonitor

class WorkerSignals(QObject):
    """Señales emitidas por cada tarea OCR"""
    finished = Signal(str, dict)
    error = Signal(str)

class OCRTask(QRunnable):
    """Tarea individual de OCR que se ejecuta en el thread pool"""
    
    def __init__(self, file_path, calendar, controller, task_id: int, total_tasks: int):
        super().__init__()
        self.file_path = file_path
        self.calendar = calendar
        self.controller = controller
        self.signals = WorkerSignals()
        self.task_id = task_id
        self.total_tasks = total_tasks

    def run(self):
        nombre_archivo = os.path.basename(self.file_path)
        
        # Verificar memoria antes de empezar
        can_process, ram_msg = MemoryMonitor.can_process()
        if not can_process:
            # Esperar y reintentar
            time.sleep(2)
            can_process, ram_msg = MemoryMonitor.can_process()
            if not can_process:
                self.signals.error.emit(
                    f"⚠️ {nombre_archivo}: Memoria insuficiente. {ram_msg}"
                )
                return
        
        try:
            # Log de inicio
            mem_info = MemoryMonitor.get_system_memory_info()
            print(f"[{self.task_id}/{self.total_tasks}] Iniciando: {nombre_archivo} "
                  f"(RAM: {mem_info['percent_used']:.1f}%)")
            
            # Procesamiento OCR
            res = self.controller.process_uploaded_file(
                file_path=self.file_path, 
                calendar=self.calendar
            )
            
            if res.get("data"):
                self.signals.finished.emit(
                    f"✅ {nombre_archivo} → {res.get('final_path', 'N/A')}", 
                    {"status": "success", "file": nombre_archivo, "data": res["data"]}
                )
            else:
                raise Exception("Datos no detectados en el documento")
                
        except Exception as e:
            self.signals.error.emit(f"❌ {nombre_archivo}: {str(e)}")
        finally:
            # LIMPIEZA AGRESIVA: Liberar memoria tras cada tarea
            gc.collect()
            time.sleep(0.5)  # Pequeña pausa para estabilidad


class ConcurrentOCRWorker(QThread):
    """
    Worker que gestiona procesamiento concurrente con optimización automática de memoria.
    Funciona completamente en background sin UI visible.
    
    Signals:
        - progress(percent, message): Actualiza barra de progreso
        - file_finished(text, result): Archivo procesado
        - all_finished(successful, failed, results): Procesamiento completo
        - error(message): Error crítico
    """
    
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
        self.pool = None

    def run(self):
        """Inicia el procesamiento concurrente"""
        total = len(self.file_paths)
        if total == 0:
            self.all_finished.emit(0, 0, [])
            return

        self.pending = total
        self.pool = QThreadPool.globalInstance()
        
        # Calcular threads óptimos
        optimal_threads, reason = MemoryMonitor.calculate_optimal_threads()
        print(f"[OCR Worker] {reason}")
        
        self.pool.setMaxThreadCount(optimal_threads)
        
        # Encolar todas las tareas
        for idx, fp in enumerate(self.file_paths, 1):
            task = OCRTask(
                fp, 
                self.calendar, 
                self.controller,
                task_id=idx,
                total_tasks=total
            )
            task.signals.finished.connect(self._on_task_finished)
            task.signals.error.connect(self._on_task_error)
            self.pool.start(task)
        
        # Esperar a que se completen todas las tareas
        self.pool.waitForDone()
        
        # Emitir resumen final
        self.all_finished.emit(self.successful, self.failed, self.results_list)
        # Iniciamos el event loop del hilo para procesar señales de las tareas
        self.exec()

    def _on_task_finished(self, text, result):
        """Llamado cuando una tarea termina exitosamente"""
        self.successful += 1
        self.results_list.append(result)
        self.file_finished.emit(text, result)
        self._report_progress()
        self.pending -= 1

    def _on_task_error(self, error_msg):
        """Llamado cuando una tarea falla"""
        self.failed += 1
        self.results_list.append({"status": "error"})
        self.file_finished.emit(error_msg, {"status": "error"})
        self._report_progress()
        self.pending -= 1

    def _report_progress(self):
        """Actualiza barra de progreso"""
        self.processed_count += 1
        total = len(self.file_paths)
        percent = int((self.processed_count / total) * 100) if total > 0 else 0
        message = f"Procesado {self.processed_count} de {total}"
        self.progress.emit(percent, message)

        # Si terminamos todas las tareas, cerramos el hilo y avisamos a la UI
        if self.processed_count == len(self.file_paths):
            self.all_finished.emit(self.successful, self.failed, self.results_list)
            self.quit()