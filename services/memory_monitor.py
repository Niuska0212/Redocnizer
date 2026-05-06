# services/memory_monitor.py
"""
Monitor de memoria y gestor de recursos.
Calcula dinámicamente cuántos procesos OCR pueden ejecutarse en paralelo.
"""

import psutil
import os
from typing import Dict, Tuple

class MemoryMonitor:
    """
    Monitorea RAM y CPU del sistema para optimizar paralelismo.
    Optimizado para máximo 16GB RAM sin GPU.
    """
    
    # Inicializar el contador de CPU para lecturas no bloqueantes
    _ = psutil.cpu_percent(interval=None)

    # Umbrales optimizados para 16GB max
    RAM_THRESHOLD_CRITICAL = 88      # % - Detener procesamiento (evitar OOM)
    RAM_THRESHOLD_WARNING = 80       # % - Reducir threads
    RAM_THRESHOLD_OPTIMAL = 65       # % - Zona segura para más threads
    
    # Estimaciones de RAM por proceso OCR (en MB)
    # Calibrado para CPU sin GPU: CRNN + EasyOCR en CPU
    RAM_PER_OCR_PROCESS = 400  # CPU-only OCR consume más RAM
    
    @staticmethod
    def get_system_memory_info() -> Dict[str, float]:
        """
        Obtiene información de memoria del sistema
        
        Returns:
            Dict con: total_gb, available_gb, used_gb, percent_used
        """
        virtual_memory = psutil.virtual_memory()
        return {
            'total_gb': virtual_memory.total / (1024**3),
            'available_gb': virtual_memory.available / (1024**3),
            'used_gb': virtual_memory.used / (1024**3),
            'percent_used': virtual_memory.percent,
            'used_mb': virtual_memory.used / (1024**2),
            'available_mb': virtual_memory.available / (1024**2),
        }
    
    @staticmethod
    def get_process_memory() -> float:
        """Obtiene memoria usada por el proceso actual en MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024**2)
    
    @staticmethod
    def calculate_optimal_threads(reserved_ram_percent: float = 20) -> Tuple[int, str]:
        """
        Calcula dinámicamente cuántos threads OCR son óptimos basándose en RAM y CPU.
        """
        mem_info = MemoryMonitor.get_system_memory_info()
        ram_percent = mem_info['percent_used']
        
        # 1. Obtener uso actual de la CPU (promedio de los últimos 500ms)
        cpu_percent = psutil.cpu_percent(interval=0.5)
        # Usamos interval=None para que no bloquee el hilo de la interfaz
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # 2. Obtener núcleos FÍSICOS (no los hilos lógicos/Hyper-threading)
        # Esto es vital para el OCR porque usar hilos lógicos en tareas pesadas 
        # suele calentar la CPU sin ganar velocidad real.
        physical_cores = psutil.cpu_count(logical=False) or 1
        
        # --- Lógica de decisión ---

        # CASO 1: RAM Crítica (Peligro de cierre de la app)
        if ram_percent >= MemoryMonitor.RAM_THRESHOLD_CRITICAL:
            return 1, f"⚠️ CRÍTICO: {ram_percent:.1f}% RAM. Forzando 1 hilo."

        # CASO 2: CPU Saturada (La computadora se está trabando)
        # Si la CPU está arriba del 85%, bajamos el ritmo aunque haya RAM.
        if cpu_percent > 85:
            # Usamos la mitad de los núcleos o al menos 1
            low_threads = max(1, physical_cores // 2)
            return low_threads, f"⚠️ CPU Saturada ({cpu_percent}%). Reduciendo a {low_threads} hilos."

        # CASO 3: Cálculo Balanceado (Zona segura)
        # Calculamos cuántos hilos caben en la RAM disponible
        reserved_mb = mem_info['total_gb'] * 1024 * (reserved_ram_percent / 100)
        usable_ram_mb = max(0, mem_info['available_mb'] - reserved_mb)
        max_threads_by_ram = max(1, int(usable_ram_mb / MemoryMonitor.RAM_PER_OCR_PROCESS))

        # El número ideal será el menor entre la RAM disponible y los núcleos físicos libres.
        # Dejamos siempre 1 núcleo libre para que el sistema operativo y tu UI respondan.
        optimal_threads = min(max_threads_by_ram, max(1, physical_cores - 1))

        # Mensaje de estado detallado
        if ram_percent <= MemoryMonitor.RAM_THRESHOLD_OPTIMAL:
            status = "✅ Óptimo"
        else:
            status = "⚠️ Moderado"

        return optimal_threads, f"{status}: {ram_percent:.1f}% RAM, {cpu_percent}% CPU. Recomendado: {optimal_threads} hilos."
    
    @staticmethod
    def can_process() -> Tuple[bool, str]:
        """
        Determina si se puede seguir procesando
        
        Returns:
            Tuple(can_process: bool, message: str)
        """
        mem_info = MemoryMonitor.get_system_memory_info()
        percent = mem_info['percent_used']
        
        if percent >= MemoryMonitor.RAM_THRESHOLD_CRITICAL:
            return False, f"❌ PAUSADO: {percent:.1f}% RAM. Limpiando memoria..."
        
        return True, f"✅ Procesando: {percent:.1f}% RAM"
    
    @staticmethod
    def get_status_string() -> str:
        """Obtiene string formateado del estado del sistema"""
        mem_info = MemoryMonitor.get_system_memory_info()
        threads, reason = MemoryMonitor.calculate_optimal_threads()
        
        return (
            f"{reason}\n"
            f"RAM: {mem_info['used_gb']:.2f}GB / {mem_info['total_gb']:.2f}GB "
            f"({mem_info['percent_used']:.1f}%)\n"
            f"Disponible: {mem_info['available_gb']:.2f}GB"
        )
    
    @staticmethod
    def get_detailed_report() -> Dict:
        """Obtiene reporte detallado para debugging"""
        mem_info = MemoryMonitor.get_system_memory_info()
        threads, reason = MemoryMonitor.calculate_optimal_threads()
        process_mem = MemoryMonitor.get_process_memory()
        can_process, msg = MemoryMonitor.can_process()
        
        return {
            'system_memory': mem_info,
            'recommended_threads': threads,
            'thread_reason': reason,
            'process_memory_mb': process_mem,
            'can_continue': can_process,
            'can_continue_reason': msg,
            'cpu_cores': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
        }
