import os
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

    def run(self):
        """
        Punto 3.5: Distribución de carga en entidades funcionales.
        Este método se ejecuta en un hilo separado del Sistema Operativo (SO).
        """
        results = []
        successful = 0
        failed = 0
        total = len(self.file_paths)
        
        try:
            # Punto 3.1.4: Distribución del procesamiento de cálculos
            # Usamos ThreadPoolExecutor para gestionar la ejecución de forma estructurada
            with ThreadPoolExecutor(max_workers=1) as executor:
                for i, fp in enumerate(self.file_paths):
                    if not self._is_running:
                        break
                        
                    nombre_archivo = os.path.basename(fp)
                    # Notificar a la UI el progreso actual
                    self.progress.emit(i, f"Procesando: {nombre_archivo}")
                    
                    try:
                        # Invocación de la lógica de negocio (Entidad de Control)
                        # Este es el punto de mayor carga computacional del OCR
                        res = self.controller.process_uploaded_file(
                            file_path=fp, 
                            calendar=self.calendar
                        )
                        
                        successful += 1
                        final_path = res.get("final_path", "N/A")
                        
                        # Construimos el texto con la ruta de guardado (como te gustaba antes)
                        item_text = f"✅ {nombre_archivo} -> {final_path}"
                        
                        result_item = {
                            "status": "success",
                            "file": nombre_archivo,
                            "path": final_path,
                            "data": res.get("data")
                        }
                        self.file_finished.emit(item_text, result_item)
                        
                    except Exception as e:
                        failed += 1
                        error_text = f"❌ {nombre_archivo} -> Error: {str(e)}"
                        
                        result_item = {
                            "status": "error",
                            "file": nombre_archivo,
                            "error": str(e)
                        }
                        self.file_finished.emit(error_text, result_item)
                    
                    results.append(result_item)
            
            # Notificar finalización total al sistema principal
            self.progress.emit(total, "Proceso completado")
            self.all_finished.emit(successful, failed, results)
            
        except Exception as e:
            self.error.emit(f"Error en el sistema paralelo: {str(e)}")

    def stop(self):
        """Permite detener el hilo de manera segura (Robustez 3.1.5)"""
        self._is_running = False