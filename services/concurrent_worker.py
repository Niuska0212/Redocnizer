# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# services/concurrent_worker.py
"""Módulo 3.1: Implementación de concurrencia para procesamiento masivo de OCR."""

import os
import threading
from PySide6.QtCore import QThread, Signal
from concurrent.futures import ThreadPoolExecutor
import psutil 
import gc


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
        # --- OPTIMIZACIÓN DINÁMICA DE HILOS ---
        # Detectamos la RAM total en GB
        ram_total = psutil.virtual_memory().total / (1024**3)
        
        # Si la RAM es menor a 9GB, usamos solo 1 hilo (Procesamiento secuencial seguro)
        # Si tiene 16GB o más, usamos 3 para ir rápido sin saturar.
        if ram_total < 9:
            self.max_workers = 1
            print("⚠️ Máquina de 8GB detectada: Procesando de 1 en 1 para evitar cierres.")
        else:
            self.max_workers = 4
            print(f"🚀 Máquina con {ram_total:.1f}GB: Usando {self.max_workers} hilos.")
            
        self._semaphore = threading.Semaphore(self.max_workers)

    def process_single_file(self, fp):
        """
        Ejecuta el proceso pesado de un solo archivo.
        Actualizado para manejar nombres de CSV dinámicos (Ej: 2024A.csv).
        """
        if not self._is_running:
            return None

        # Nombre del archivo original que se está procesando (el PDF)
        nombre_original = os.path.basename(fp)

        with self._semaphore:
            try:
                # Invocación de la lógica de negocio
                res = self.controller.process_uploaded_file(
                    file_path=fp, 
                    calendar=self.calendar
                )
                
                final_path = res.get("final_path", "N/A")
                
                # Subida en background a Drive
                if self.drive_service and final_path and final_path != "N/A":
                    try:
                        data = res.get("data", {})
                        paterno = data.get("PATERNO", "")
                        materno = data.get("MATERNO", "")
                        nombre_s = data.get("NOMBRE_S", "")
                        nombre_maestro = f"{paterno} {materno} {nombre_s}".strip().replace("  ", " ")
                        
                        if not nombre_maestro.strip():
                            nombre_maestro = "Sin_Nombre"

                        # --- CORRECCIÓN AQUÍ ---
                        # Obtenemos el nombre real del archivo generado (ej: '2024A.csv')
                        nombre_generado = os.path.basename(final_path).lower()

                        # En lugar de comparar contra "contratos.csv", revisamos si es el CSV del calendario
                        if nombre_generado.endswith('.csv'):
                            # Subir la base de datos a la raíz del proyecto en Drive
                            self.drive_service.upload_to_path(
                                final_path, 
                                drive_root='Redocnizer', 
                                calendar=self.calendar, # Esto asegura que use el nombre del ciclo
                                subfolder_path=""
                            )
                        else:
                            # Subir el contrato PDF a la carpeta del maestro
                            self.drive_service.upload_to_path(
                                final_path,
                                drive_root='Redocnizer',
                                calendar='',
                                subfolder_path=f"Maestros/{nombre_maestro}"
                            )
                    except Exception as e:
                        print(f"Advertencia: no se pudo subir a Drive {final_path}: {e}")
                gc.collect()  # Liberar memoria después de cada archivo procesado
                return {
                    "status": "success",
                    "file": nombre_original,
                    "path": final_path,
                    "data": res.get("data")
                }
            except Exception as e:
                return {
                    "status": "error",
                    "file": nombre_original,
                    "error": str(e)
                }

    def run(self):
        try:
            total = len(self.file_paths)
            successful = 0
            failed = 0
            results = []

            # Recomendación: Aunque tengas 16GB, no pases de 4 workers si usas OCR
            # para evitar que TensorFlow choque con los hilos de red.
            num_workers = min(self.max_workers, 4) 

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # 1. Lanzamos las tareas
                futures = {executor.submit(self.process_single_file, fp): fp for fp in self.file_paths}
                
                for i, future in enumerate(futures):
                    if not self._is_running:
                        break
                    
                    file_path = futures[future]
                    try:
                        # 2. Timeout de 60s por archivo. Si Drive/Supa se traban, 
                        # este hilo "suelta" el proceso para que la app no muera.
                        result_item = future.result(timeout=60) 
                        
                        if result_item:
                            if result_item.get("status") == "success":
                                successful += 1
                                item_text = f"✅ {result_item['file']} -> {result_item['path']}"
                            else:
                                failed += 1
                                item_text = f"❌ {result_item['file']} -> Error: {result_item.get('error')}"
                            
                            # Enviamos señal a la UI
                            self.file_finished.emit(item_text, result_item)
                            results.append(result_item)

                    except Exception as e:
                        # Este bloque atrapa el "Timeout" o errores de red
                        failed += 1
                        print(f"⚠️ Error procesando {file_path}: {e}")
                        self.file_finished.emit(f"❌ Error en archivo: {os.path.basename(file_path)}", {})
                    
                    # 3. Limpieza de memoria tras cada archivo (Vital para estabilidad)
                    import gc
                    gc.collect()

                    # 4. Actualizar barra de progreso
                    progreso_val = int(((i + 1) / total) * 100)
                    self.progress.emit(progreso_val, f"Procesado {i+1} de {total} documentos...")

            # Al finalizar el bucle
            if self._is_running:
                self.progress.emit(100, "Proceso completado")
                self.all_finished.emit(successful, failed, results)
            
        except Exception as e:
            # Si algo explota a nivel general, lo mandamos a la barra de estado
            # pero no cerramos la app.
            print(f"🔥 Error Crítico en Worker: {e}")
            self.error.emit(f"Error en hilos: {str(e)}")

    def stop(self):
        """
        Permite detener el hilo de manera segura (Robustez 3.1.5).
        Corta el bucle de procesamiento y detiene el envío de señales.
        """
        self._is_running = False
        print("🛑 Deteniendo trabajador concurrente...")
