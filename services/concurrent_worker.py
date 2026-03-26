# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# services/concurrent_worker.py

import os
import threading
import gc
from PySide6.QtCore import QThread, Signal

class ConcurrentOCRWorker(QThread):
    """
    TRABAJADOR DUAL (OCR + NUBE)
    Procesa el OCR de forma lineal para estabilidad y la nube en segundo plano.
    """
    progress = Signal(int, str)           
    file_finished = Signal(str, dict)      
    all_finished = Signal(int, int, list)  
    error = Signal(str)                    

    def __init__(self, file_paths, calendar, controller, drive_service=None, supabase_manager=None):
        super().__init__()
        self.file_paths = file_paths
        self.calendar = calendar
        self.controller = controller
        self.drive_service = drive_service
        self.supabase_manager = supabase_manager
        self._is_running = True

    def _cloud_task(self, data, final_path):
        """HILO 2: Gestión de red (Supabase y Drive). No detiene al Hilo 1."""
        try:
            # Sincronización Supabase
            if self.supabase_manager and self.supabase_manager.enabled:
                if data and data.get("NUM"):
                    self.supabase_manager.upsert_full_record(data)
            
            # Sincronización Google Drive
            if self.drive_service and final_path and os.path.exists(final_path):
                paterno = data.get("PATERNO", "")
                materno = data.get("MATERNO", "")
                nombre_s = data.get("NOMBRE_S", "")
                nombre_maestro = f"{paterno} {materno} {nombre_s}".strip().replace("  ", " ") or "Sin_Nombre"
                
                if final_path.lower().endswith('.csv'):
                    self.drive_service.upload_to_path(final_path, drive_root='Redocnizer', calendar=self.calendar)
                else:
                    self.drive_service.upload_to_path(final_path, drive_root='Redocnizer', subfolder_path=f"Maestros/{nombre_maestro}")
        except Exception as e:
            print(f"📡 Error de red (No detiene el proceso): {e}")

    def run(self):
        """HILO 1: Proceso principal de OCR."""
        try:
            total = len(self.file_paths)
            successful, failed = 0, 0
            results_list = [] # Aquí guardamos todo para el reporte final

            for i, fp in enumerate(self.file_paths):
                if not self._is_running: break

                nombre_archivo = os.path.basename(fp)
                self.progress.emit(int((i / total) * 100), f"Analizando: {nombre_archivo}...")

                try:
                    # 1. Ejecutar OCR y Procesamiento Local
                    res = self.controller.process_uploaded_file(file_path=fp, calendar=self.calendar)
                    
                    data_detectada = res.get("data", {})
                    final_path = res.get("final_path", "N/A")

                    if data_detectada:
                        successful += 1
                        # 2. Preparamos el resultado para la UI
                        resultado_item = {
                            "status": "success",
                            "file": nombre_archivo,
                            "path": final_path,
                            "data": data_detectada
                        }
                        results_list.append(resultado_item)
                        
                        # 3. NOTIFICAR A LA UI (Para que aparezca en la lista con el check verde)
                        texto_lista = f"✅ {nombre_archivo} -> {final_path}"
                        self.file_finished.emit(texto_lista, resultado_item)
                        
                        # 4. DISPARAR HILO DE NUBE (HILO 2)
                        # Se lanza y el bucle FOR sigue inmediatamente al siguiente archivo
                        threading.Thread(
                            target=self._cloud_task, 
                            args=(data_detectada, final_path),
                            daemon=True
                        ).start()
                    else:
                        raise Exception("No se detectaron datos válidos")

                except Exception as e:
                    failed += 1
                    error_item = {"status": "error", "file": nombre_archivo, "error": str(e)}
                    results_list.append(error_item)
                    self.file_finished.emit(f"❌ {nombre_archivo} -> Error: {str(e)}", error_item)

                # Limpieza de RAM tras cada archivo
                gc.collect()

            # Al terminar todos los archivos
            if self._is_running:
                self.progress.emit(100, "¡Todo listo!")
                self.all_finished.emit(successful, failed, results_list)

        except Exception as e:
            print(f"🔥 Error Crítico: {e}")
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False