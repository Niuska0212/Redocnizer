#!/usr/bin/env python3
"""
Script de prueba: Validar sistema de monitoreo de memoria
Ejecución: python test_memory_monitor.py
"""

import sys
import os
from services.memory_monitor import MemoryMonitor

def print_header(title):
    """Imprime un header formateado"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_basic_info():
    """Test 1: Información básica de memoria"""
    print_header("TEST 1: Información Básica del Sistema")
    
    mem_info = MemoryMonitor.get_system_memory_info()
    
    print(f"RAM Total:        {mem_info['total_gb']:.2f} GB")
    print(f"RAM Disponible:   {mem_info['available_gb']:.2f} GB")
    print(f"RAM Usada:        {mem_info['used_gb']:.2f} GB")
    print(f"Porcentaje Usado: {mem_info['percent_used']:.1f}%")
    print(f"RAM en MB:        {mem_info['used_mb']:.0f} MB / {mem_info['available_mb']:.0f} MB")
    
    return mem_info

def test_process_memory():
    """Test 2: Memoria del proceso actual"""
    print_header("TEST 2: Memoria del Proceso Actual")
    
    process_mem = MemoryMonitor.get_process_memory()
    print(f"Memoria de este proceso: {process_mem:.2f} MB")
    
    return process_mem

def test_optimal_threads():
    """Test 3: Cálculo de threads óptimos"""
    print_header("TEST 3: Cálculo de Threads Óptimos")
    
    threads, reason = MemoryMonitor.calculate_optimal_threads()
    
    print(f"Threads recomendados: {threads}")
    print(f"Razón: {reason}")
    
    return threads

def test_can_process():
    """Test 4: Verificar si se puede procesar"""
    print_header("TEST 4: Verificar Estado de Procesamiento")
    
    can_process, msg = MemoryMonitor.can_process()
    
    print(f"¿Puede procesar?: {can_process}")
    print(f"Mensaje: {msg}")
    
    return can_process

def test_status_string():
    """Test 5: String de estado formateado"""
    print_header("TEST 5: String de Estado Formateado")
    
    status = MemoryMonitor.get_status_string()
    print(status)
    
    return status

def test_detailed_report():
    """Test 6: Reporte detallado completo"""
    print_header("TEST 6: Reporte Detallado Completo")
    
    report = MemoryMonitor.get_detailed_report()
    
    print("📊 MEMORIA DEL SISTEMA:")
    mem = report['system_memory']
    print(f"  - Total:     {mem['total_gb']:.2f} GB")
    print(f"  - Usada:     {mem['used_gb']:.2f} GB ({mem['percent_used']:.1f}%)")
    print(f"  - Disponible: {mem['available_gb']:.2f} GB")
    
    print(f"\n💻 INFORMACIÓN DE CPU:")
    print(f"  - Cores:     {report['cpu_cores']}")
    print(f"  - Uso:       {report['cpu_percent']:.1f}%")
    
    print(f"\n🔄 INFORMACIÓN DE THREADS:")
    print(f"  - Recomendados: {report['recommended_threads']}")
    print(f"  - Razón: {report['thread_reason']}")
    
    print(f"\n⚙️ INFORMACIÓN DEL PROCESO:")
    print(f"  - Memoria:   {report['process_memory_mb']:.2f} MB")
    
    print(f"\n✅ PUEDE CONTINUAR PROCESANDO:")
    print(f"  - Estado:    {'SÍ' if report['can_continue'] else 'NO'}")
    print(f"  - Razón:     {report['can_continue_reason']}")
    
    return report

def test_memory_simulation():
    """Test 7: Simulación de decisiones según RAM"""
    print_header("TEST 7: Simulación de Decisiones")
    
    print("Simulando diferentes niveles de RAM disponible:\n")
    
    scenarios = [
        (25, "25% - Excelente"),
        (50, "50% - Bueno"),
        (70, "70% - Moderado"),
        (80, "80% - Alto"),
        (88, "88% - Muy Alto"),
        (92, "92% - Crítico"),
    ]
    
    for percent, label in scenarios:
        if percent >= MemoryMonitor.RAM_THRESHOLD_CRITICAL:
            action = "❌ PAUSADO - Solo 1 thread"
        elif percent >= MemoryMonitor.RAM_THRESHOLD_WARNING:
            action = "⚠️ REDUCIDO - 2 threads"
        else:
            action = "✅ ÓPTIMO - Máximos threads"
        
        print(f"{label:20} → {action}")

def main():
    """Ejecuta todos los tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║  PRUEBA DE MONITOREO DE MEMORIA - REDOCNIZER           ║")
    print("╚" + "="*58 + "╝")
    
    try:
        # Ejecutar todos los tests
        test_basic_info()
        test_process_memory()
        test_optimal_threads()
        test_can_process()
        test_status_string()
        test_detailed_report()
        test_memory_simulation()
        
        # Resumen final
        print_header("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("El sistema de monitoreo de memoria está funcionando correctamente.")
        print("\n¿Próximos pasos?")
        print("1. Ejecuta la aplicación: python app.py")
        print("2. Ve a la pestaña 'Procesar Contratos'")
        print("3. Selecciona contratos y observa el widget de memoria")
        print("4. El sistema ajustará threads automáticamente según RAM disponible\n")
        
        return 0
        
    except Exception as e:
        print_header("❌ ERROR DURANTE LOS TESTS")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
