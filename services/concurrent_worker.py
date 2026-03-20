# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo 3.1: Implementación de concurrencia para procesamiento masivo de OCR."""

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
    progress = Signal(int, str)           # (valor_barra, mensaje_estado)
    file_finished = Signal(str, dict)      # (texto_para_lista, resultados_completos)
    all_finished = Signal(int, int, list)  # (exitosos, fallidos, lista_total)
    error = Signal(str)                    # Mensaje de error crítico

    def __init__(self, file_paths, calendar, controller, drive_service=None):
        """
        Inicializa el trabajador con la carga de archivos.
        
        file_paths: Lista de rutas de archivos a procesar.
        calendar: Nombre del calendario activo (ej. 2024A).
        controller: Instancia de ContractController (Entidad de Control).
        drive_service: (Opcional) Instancia de GoogleDriveService para subida en background.
        """
        super().__init__()
        self.file_paths = file_paths
        self.calendar = calendar
        self.controller = controller
        self.drive_service = drive_service
        self._is_running = True
        
        # Punto 3.1.4: Gestión de recursos de hardware
        # Limitamos a 4 hilos para no saturar la memoria VRAM/RAM con modelos de IA
        self.max_workers = 4 
        self._semaphore = threading.Semaphore(self.max_workers)

    def process_single_file(self, fp):
        """
        Ejecuta el proceso pesado de un solo archivo.
        Este método es ejecutado por el ThreadPoolExecutor.
        """
        if not self._is_running:
            return None

        nombre_archivo = os.path.basename(fp)

        # El semáforo limita cuántas instancias de la IA corren simultáneamente
        with self._semaphore:
            try:
                # Invocación de la lógica de negocio (Entidad de Control)
                # Este es el punto de mayor carga computacional del sistema
                res = self.controller.process_uploaded_file(
                    file_path=fp, 
                    calendar=self.calendar
                )
                
                final_path = res.get("final_path", "N/A")
                
                # Subida en background a Drive (si está disponible)
                if self.drive_service and final_path and final_path != "N/A":
                    try:
                        # Obtener nombre completo del maestro
                        data = res.get("data", {})
                        paterno = data.get("PATERNO", "")
                        materno = data.get("MATERNO", "")
                        nombre_s = data.get("NOMBRE_S", "")
                        nombre_maestro = f"{paterno} {materno} {nombre_s}".strip().replace("  ", " ")
                        if not nombre_maestro.strip():
                            nombre_maestro = self.calendar
                        # Subir contratos a /Redocnizer/nombre_maestro y CSV a /Redocnizer/calendario
                        nombre_archivo = os.path.basename(final_path).lower()

                        if nombre_archivo == "contratos.csv":
                            # Subir CSV a /Redocnizer/calendario/nombre_calendario/contratos.csv
                            self.drive_service.upload_to_path(
                                final_path, 
                                drive_root='Redocnizer', 
                                calendar=self.calendar, 
                                subfolder_path=""
                                )
                        else:
                            # Subir contratos a /Redocnizer/maestros/nombre_maestro/[subcarpetas]
                            subfolder = nombre_maestro
                            self.drive_service.upload_to_path(
                                final_path,
                                drive_root='Redocnizer',
                                calendar='',
                                subfolder_path=subfolder
                                )
                    except Exception as e:
                        print(f"Advertencia: no se pudo subir a Drive {final_path}: {e}")
                
                return {
                    "status": "success",
                    "file": nombre_archivo,
                    "path": final_path,
                    "data": res.get("data")
                }
            except Exception as e:
                return {
                    "status": "error",
                    "file": nombre_archivo,
                    "error": str(e)
                }

    def run(self):
        """
        Punto 3.5: Distribución de carga en entidades funcionales.
        Ejecución principal del hilo del Sistema Operativo.
        """
        try:
            total = len(self.file_paths)
            successful = 0
            failed = 0
            results = []

            # ThreadPoolExecutor permite que el SO gestione los hilos disponibles
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Lanzamos las tareas al pool de forma no bloqueante
                futures = [executor.submit(self.process_single_file, fp) for fp in self.file_paths]
                
                for i, future in enumerate(futures):
                    if not self._is_running:
                        break
                    
                    # Esperamos el resultado de cada futuro
                    result_item = future.result()
                    
                    if result_item:
                        if result_item["status"] == "success":
                            successful += 1
                            # Texto con ruta de guardado (formato preferido del usuario)
                            item_text = f"✅ {result_item['file']} -> {result_item['path']}"
                        else:
                            failed += 1
                            item_text = f"❌ {result_item['file']} -> Error: {result_item.get('error')}"
                        
                        # Notificar a la UI el fin de este archivo específico
                        self.file_finished.emit(item_text, result_item)
                        results.append(result_item)
                    
                    # Punto 3.1.2: Actualización asíncrona de progreso
                    progreso_val = int(((i + 1) / total) * 100)
                    self.progress.emit(progreso_val, f"Procesado {i+1} de {total} documentos...")

            # Notificar finalización total al sistema principal
            if self._is_running:
                self.progress.emit(100, "Proceso completado exitosamente")
                self.all_finished.emit(successful, failed, results)
            
        except Exception as e:
            # Robustez 3.1.5: Captura de errores en hilos secundarios
            self.error.emit(f"Error en procesamiento paralelo: {str(e)}")

    def stop(self):
        """
        Permite detener el hilo de manera segura (Robustez 3.1.5).
        Corta el bucle de procesamiento y detiene el envío de señales.
        """
        self._is_running = False
        print("🛑 Deteniendo trabajador concurrente...")