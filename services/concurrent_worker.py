# services/concurrent_worker.py

import os
import threading
from PySide6.QtCore import QThread, Signal
from concurrent.futures import ThreadPoolExecutor

class ConcurrentOCRWorker(QThread):
    """
    TRABAJADOR CONCURRENTE (Módulo 3.1.1 y 3.1.4)
    Esta clase implementa la ejecución asíncrona para evitar el bloqueo de la UI
    y permitir la distribución de carga en hilos de hardware.
    """
    # Señales para comunicación entre hilos (Protocolo de comunicación interna)
    # Reemplazan la necesidad de actualizar la UI directamente desde el bucle
    progress = Signal(int, str)  # Envia (valor_barra, mensaje_estado)
    file_finished = Signal(str, dict) # Envia (texto_para_lista, resultados_completos)
    all_finished = Signal(int, int, list) # Envia (exitosos, fallidos, lista_total)
    error = Signal(str) # Envia mensaje de error crítico

    def __init__(self, file_paths, calendar, controller):
        super().__init__()
        self.file_paths = file_paths
        self.calendar = calendar
        self.controller = controller
        self._is_running = True
        
        self.max_workers = 4 
        self._semaphore = threading.Semaphore(self.max_workers)
        

    def process_single_file(self, fp):
        """Ejecuta el proceso pesado de un solo archivo."""
        if not self._is_running:
            return None

        # El semáforo limita cuántos archivos entran a la IA al mismo tiempo
        with self._semaphore:
            try:
                # El controlador gestiona la IA (OCR + CRNN)
                res = self.controller.process_uploaded_file(file_path=fp, calendar=self.calendar)
                return {
                    "status": "success",
                    "file": os.path.basename(fp),
                    "path": res.get("final_path"),
                    "data": res.get("data")
                }
            except Exception as e:
                return {
                    "status": "error",
                    "file": os.path.basename(fp),
                    "error": str(e)
                }

    def run(self):
        try:
            total = len(self.file_paths)
            successful = 0
            failed = 0
            results = []

            # ThreadPoolExecutor permite que el SO gestione los 24 hilos disponibles
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Lanzamos todas las tareas al pool
                futures = [executor.submit(self.process_single_file, fp) for fp in self.file_paths]
                
                for i, future in enumerate(futures):
                    if not self._is_running:
                        break
                    
                    result_item = future.result()
                    if result_item:
                        if result_item["status"] == "success":
                            successful += 1
                            item_text = f"✅ {result_item['file']} -> Terminado"
                        else:
                            failed += 1
                            item_text = f"❌ {result_item['file']} -> Error"
                        
                        # Actualizar la UI inmediatamente
                        self.file_finished.emit(item_text, result_item)
                        results.append(result_item)
                    
                    # Cálculo de progreso
                    self.progress.emit(int(((i + 1) / total) * 100), f"Procesando {i+1}/{total}")

            self.all_finished.emit(successful, failed, results)
            
        except Exception as e:
            self.error.emit(f"Error en procesamiento paralelo: {str(e)}")

    def stop(self):
        """Permite detener el hilo de manera segura (Robustez 3.1.5)"""
        self._is_running = False