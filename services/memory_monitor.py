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
        Calcula dinámicamente cuántos threads OCR son óptimos
        
        Args:
            reserved_ram_percent: % de RAM a reservar para SO y otras apps
            
        Returns:
            Tuple(num_threads: int, reason: str)
        """
        mem_info = MemoryMonitor.get_system_memory_info()
        percent = mem_info['percent_used']
        available_gb = mem_info['available_gb']
        total_gb = mem_info['total_gb']
        
        # --- Lógica de decisión basada en disponibilidad ---
        
        # CRÍTICO: RAM muy baja
        if percent >= MemoryMonitor.RAM_THRESHOLD_CRITICAL:
            return 1, f"⚠️ CRÍTICO: {percent:.1f}% RAM usada. Solo 1 thread."
        
        # ALERTA: RAM alta
        if percent >= MemoryMonitor.RAM_THRESHOLD_WARNING:
            return 2, f"⚠️ ALTO: {percent:.1f}% RAM. Reducido a 2 threads."
        
        # ÓPTIMO: Calcular procesos por disponibilidad
        if percent <= MemoryMonitor.RAM_THRESHOLD_OPTIMAL:
            reserved_mb = total_gb * 1024 * (reserved_ram_percent / 100)
            usable_ram_mb = max(0, mem_info['available_mb'] - reserved_mb)
            max_threads_by_ram = max(1, int(usable_ram_mb / MemoryMonitor.RAM_PER_OCR_PROCESS))

            # Para CPU-bound, usar núcleos reales (o lógicos si no hay físicos)
            cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
            max_threads = min(max_threads_by_ram, max(1, cpu_cores))

            return max_threads, f"✅ Óptimo: {percent:.1f}% RAM, {max_threads} procesos recomendados"
        
        # INTERMEDIO
        return 2, f"⚠️ Moderado: {percent:.1f}% RAM. 2 threads."
    
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
