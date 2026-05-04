# Optimización de Procesamiento y Monitoreo de Memoria

## 📋 Resumen

La aplicación Redocnizer ahora incluye un **sistema inteligente de monitoreo de memoria** que:

✅ **Evita que se trabe** durante el procesamiento de múltiples contratos  
✅ **Calcula dinámicamente** cuántos procesos OCR pueden ejecutarse en paralelo  
✅ **Muestra en tiempo real** el uso de RAM, CPU y threads recomendados  
✅ **Pausa automáticamente** si la memoria alcanza niveles críticos  
✅ **Ajusta threads sobre la marcha** según cambios de disponibilidad de RAM  

---

## 🔧 Componentes Principales

### 1. `services/memory_monitor.py`
Módulo que monitorea recursos del sistema:

```python
from services.memory_monitor import MemoryMonitor

# Obtener información de memoria
info = MemoryMonitor.get_system_memory_info()
# {'total_gb': 16.0, 'available_gb': 8.5, 'used_gb': 7.5, 'percent_used': 47.0, ...}

# Calcular threads óptimos
threads, reason = MemoryMonitor.calculate_optimal_threads()
# (3, "✅ Óptimo: 47.0% RAM, 3 threads recomendados")

# Verificar si se puede continuar
can_process, msg = MemoryMonitor.can_process()
# (True, "✅ Procesando: 47.0% RAM")

# Obtener reporte detallado
report = MemoryMonitor.get_detailed_report()
# Devuelve: system_memory, recommended_threads, process_memory_mb, can_continue, cpu_cores, cpu_percent
```

**Umbrales de decisión:**
- **90% RAM**: ❌ Crítico - Solo 1 thread, procesa lentamente
- **85% RAM**: ⚠️ Alto - 2 threads
- **70% RAM**: ✅ Óptimo - Calcula threads según CPU cores

---

### 2. `services/concurrent_worker.py` (Mejorado)
Worker concurrente con monitoreo en tiempo real:

```python
worker = ConcurrentOCRWorker(file_paths, calendar, controller)

# Nuevas señales disponibles:
worker.progress           # Actualiza barra de progreso
worker.file_finished      # Archivo terminado
worker.memory_status      # 🆕 Estado de memoria actualizado
worker.all_finished       # Procesamiento completo
worker.error             # Error crítico
```

**Características:**
- Verifica memoria antes de empezar cada tarea
- Reintenta si hay baja memoria temporal
- Limpia memoria agresivamente después de cada OCR (`gc.collect()`)
- Monitorea cada 1 segundo (configurable)
- Ajusta threads dinámicamente durante ejecución

---

### 3. `ui/memory_status_widget.py` (Nuevo)
Widget visual que muestra en tiempo real:

- 📊 **Barra de RAM**: Verde (bueno) → Naranja → Rojo (crítico)
- 💻 **Threads recomendados**: Cantidad óptima según RAM
- 🔌 **CPU actual**: Porcentaje de uso de CPU
- ⚠️ **Estado detallado**: Información completa de recursos

---

## 🎯 Cómo Funciona

### Flujo de Ejecución:

1. **Usuario hace clic en "Procesar Contrato(s)"**
2. **Sistema verifica memoria disponible**
3. **MemoryMonitor calcula threads óptimos**
   - Si 16GB y 50% RAM usado → 3 threads
   - Si 16GB y 80% RAM usado → 2 threads
   - Si 16GB y 90% RAM usado → 1 thread
4. **ConcurrentOCRWorker inicia con ese número de threads**
5. **Cada 1 segundo actualiza memoria_status**
6. **Si OCR tarda mucho, puede ajustar threads sobre la marcha**
7. **Limpia memoria agresivamente después de cada archivo**

### Ejemplo con 16GB RAM:

```
ESCENARIO A: RAM libre (40% usado)
├─ Threads recomendados: 4-6
├─ Velocidad: Rápida ⚡
└─ Consumo: ~1.4GB por proceso

ESCENARIO B: RAM moderada (65% usado)
├─ Threads recomendados: 2-3
├─ Velocidad: Normal
└─ Consumo: ~1.4GB por proceso

ESCENARIO C: RAM baja (85% usado)
├─ Threads recomendados: 2
├─ Velocidad: Lenta 🐌
└─ Consumo: Monitoreo constante

ESCENARIO D: RAM crítica (92% usado)
├─ Threads recomendados: 1
├─ Velocidad: Muy lenta ⏸️
└─ Consumo: Pausa y reinicia cuando se libera RAM
```

---

## 📊 Interpretando el Widget de Memoria

### Barra de RAM

```
████░░░░░░░░░░░░░░░░ 45% - ✅ Excelente
████████░░░░░░░░░░░░ 65% - ⚠️ Moderado  
████████████░░░░░░░░ 80% - ⚠️ Alto
████████████████░░░░ 92% - ❌ Crítico
```

### Mensajes de Estado

| Mensaje | Significado | Acción |
|---------|------------|--------|
| `✅ Óptimo: 45.0% RAM, 4 threads` | Todo perfecto | Procesar |
| `⚠️ Moderado: 68.0% RAM. 2 threads` | RAM moderada | Procesar lento |
| `⚠️ Alto: 82.0% RAM. 2 threads` | RAM alta | Procesar muy lento |
| `❌ PAUSADO: 92.0% RAM. Limpiando` | RAM crítica | Esperar liberación |

---

## ⚙️ Configuración Avanzada

### Ajustar Umbrales (En `memory_monitor.py`)

```python
class MemoryMonitor:
    RAM_THRESHOLD_CRITICAL = 90      # % donde se pausa
    RAM_THRESHOLD_WARNING = 85       # % donde se reduce a 2 threads
    RAM_THRESHOLD_OPTIMAL = 70       # % donde se calcula máximo
    
    RAM_PER_OCR_PROCESS = 350  # MB estimados por OCR
```

### Cambiar Intervalo de Monitoreo

```python
# En main_window.py
self.worker = ConcurrentOCRWorker(
    file_paths=files,
    calendar=calendar,
    controller=self.controller,
    check_memory_interval=2000  # 2 segundos en lugar de 1
)
```

---

## 🚀 Mejoras Implementadas

### Antes (Versión Anterior)

```
❌ Se trabaaba todo si había muchos archivos
❌ Siempre usaba 2 threads fijos
❌ No mostraba estado de RAM
❌ Podía alcanzar 100% de RAM → crash
❌ Sin retroalimentación visual
```

### Ahora (Versión Optimizada)

```
✅ Calcula dinámicamente threads según RAM
✅ Ajusta sobre la marcha sin reiniciar
✅ Widget de memoria en tiempo real
✅ Pausa antes de crashear
✅ Limpia memoria agresivamente
✅ Retroalimentación visual clara
```

---

## 📱 Ejemplo de Uso en UI

```python
# En main_window.py - El widget se muestra automáticamente en la pestaña "Procesar"

# Estado inicial (antes de procesar):
memory_widget.update_memory_status("✅ Óptimo: 50.5% RAM, 3 threads\n...")

# Durante procesamiento (actualiza cada 1 segundo):
# El widget muestra:
# - Barra de RAM en tiempo real
# - Threads recomendados actualizados
# - CPU usage actual
```

---

## 🔍 Debugging

### Ver logs en consola:

```
[OCR Worker] ✅ Óptimo: 50.5% RAM, 3 threads recomendados
[1/5] Iniciando: contrato_1.pdf (RAM: 50.1%)
[Memory Monitor] Ajustando a 2 threads: ⚠️ ALTO: 82.5% RAM
[2/5] Iniciando: contrato_2.pdf (RAM: 82.3%)
```

### Verificar consumo de memoria en tu equipo:

```python
from services.memory_monitor import MemoryMonitor

# Terminal Python
report = MemoryMonitor.get_detailed_report()
print(report)

# Output:
# {
#   'system_memory': {'total_gb': 16.0, 'available_gb': 8.5, ...},
#   'recommended_threads': 3,
#   'thread_reason': '✅ Óptimo: 50.5% RAM, 3 threads',
#   'process_memory_mb': 342.5,
#   'can_continue': True,
#   'cpu_cores': 8,
#   'cpu_percent': 23.5
# }
```

---

## 📦 Requisitos

Asegúrate de tener `psutil` instalado:

```bash
pip install psutil
```

Ya está incluido en `requirements.txt`.

---

## 🎓 Conclusión

El sistema de optimización de memoria:
- **Previene trabas** durante procesamiento
- **Maximiza velocidad** sin arriesgar estabilidad
- **Proporciona transparencia** con widget en tiempo real
- **Se adapta dinámicamente** a cambios de recursos

¡Ahora puedes procesar contratos masivamente sin preocuparte por crashes! 🎉
