# 🎨 GUÍA VISUAL - Cómo Se Ve el Sistema Optimizado

## 📍 Ubicación en la UI

```
┌────────────────────────────────────────────────────────────────────┐
│  REDOCNIZER - Gestión de Contratos                          [_][□][X]  │
├────────────────────────────────────────────────────────────────────┤
│  📄 Procesar  │  📊 Ver/Editar Datos  │  ☁️ Cloud             │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ─────────── Configuración ───────────                            │
│  Directorio raíz: [ n:\Documentos\Contratos ]  [📁 Seleccionar]  │
│                                                                      │
│  ─────────── Archivos a Procesar ───────────                      │
│  [Vista Preview]    📎 Subir       🗑️ Limpiar   ➖ Eliminar       │
│  [250x350]          ─────────────────────────────────────────     │
│                     📄 contrato_1.pdf                             │
│                     📄 contrato_2.pdf                             │
│                     📄 contrato_3.pdf                             │
│  Vista previa       ──────────────────────────────────────────    │
│  del documento                                                     │
│                                                                      │
│  ─────────── Progreso ───────────  ◄── NUEVO                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 🔄 ESTADO DE RECURSOS: (Se actualiza cada 1 segundo)        │ │
│  │                                                              │ │
│  │ ✅ Óptimo: 50.5% RAM, 3 threads                             │ │
│  │ RAM: 8.00GB / 15.84GB (50.5%)                               │ │
│  │ Disponible: 7.84GB                                          │ │
│  │                                                              │ │
│  │ RAM:                                                         │ │
│  │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 50.5%             │ │
│  │                                                              │ │
│  │ 💻 Threads óptimos: 3 | CPU: 12.5%                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Progreso:                                                         │
│  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░ 35%                 │
│  Procesado 7 de 20                                                │
│                                                                      │
│  Resultados:                                                       │
│  ✅ contrato_1.pdf → datos/2024A/000001_SMITH_J.xlsx           │
│  ✅ contrato_2.pdf → datos/2024A/000002_JOHNSON_A.xlsx         │
│  ✅ contrato_3.pdf → datos/2024A/000003_WILLIAMS_M.xlsx        │
│  ⏳ Procesando contrato_4.pdf...                                │
│  □ contrato_5.pdf (en cola)                                    │
│                                                                      │
│                    [🚀 Procesar Contrato(s)]                      │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Estados Posibles del Widget

### 1️⃣ Estado ÓPTIMO (Verde)

```
┌──────────────────────────────────────────────────────────────┐
│ ✅ Óptimo: 45.0% RAM, 4 threads                              │
│ RAM: 7.13GB / 15.84GB (45.0%)                                │
│ Disponible: 8.71GB                                           │
│                                                              │
│ RAM:                                                         │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 45%            │
│      ▲ (Verde - Excelente)                                   │
│                                                              │
│ 💻 Threads óptimos: 4 | CPU: 8.2%                            │
└──────────────────────────────────────────────────────────────┘

ACCIÓN: Procesar a velocidad máxima con 4 threads en paralelo
VELOCIDAD: ⚡⚡⚡ Muy Rápida
```

---

### 2️⃣ Estado MODERADO (Naranja)

```
┌──────────────────────────────────────────────────────────────┐
│ ⚠️ Moderado: 68.0% RAM. 2 threads.                           │
│ RAM: 10.78GB / 15.84GB (68.0%)                               │
│ Disponible: 5.06GB                                           │
│                                                              │
│ RAM:                                                         │
│ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ 68%            │
│                ▲ (Naranja - Moderado)                        │
│                                                              │
│ 💻 Threads óptimos: 2 | CPU: 15.3%                           │
└──────────────────────────────────────────────────────────────┘

ACCIÓN: Reducir a 2 threads para mantener estabilidad
VELOCIDAD: ⚡⚡ Normal
```

---

### 3️⃣ Estado ALTO (Naranja Más Oscuro)

```
┌──────────────────────────────────────────────────────────────┐
│ ⚠️ Alto: 82.0% RAM. 2 threads.                               │
│ RAM: 13.00GB / 15.84GB (82.0%)                               │
│ Disponible: 2.84GB                                           │
│                                                              │
│ RAM:                                                         │
│ ████████████████████████░░░░░░░░░░░░░░░░░ 82%            │
│                        ▲ (Naranja oscuro - Alto)             │
│                                                              │
│ 💻 Threads óptimos: 2 | CPU: 28.5%                           │
└──────────────────────────────────────────────────────────────┘

ACCIÓN: Mantener 2 threads, vigilar atentamente
VELOCIDAD: ⚡ Lenta
RIESGO: ⚠️ Alto
```

---

### 4️⃣ Estado CRÍTICO (Rojo)

```
┌──────────────────────────────────────────────────────────────┐
│ ❌ PAUSADO: 92.0% RAM. Limpiando memoria...                  │
│ RAM: 14.58GB / 15.84GB (92.0%)                               │
│ Disponible: 1.26GB                                           │
│                                                              │
│ RAM:                                                         │
│ ████████████████████████████░░░░░░░░░░░░░ 92%            │
│                            ▲ (Rojo - CRÍTICO)                │
│                                                              │
│ 💻 Threads óptimos: 1 | CPU: 85.2%                           │
└──────────────────────────────────────────────────────────────┘

ACCIÓN: PAUSAR procesamiento, esperar liberación de RAM
VELOCIDAD: ⏸️ PAUSADO
RIESGO: 🚨 CRÍTICO - Evitar crash
RECOMENDACIÓN: Cierra otras aplicaciones
```

---

## 📊 Evolución Durante Procesamiento

### Escenario: Procesar 20 contratos con 16GB RAM

```
SEGUNDO 0 (Inicio)
─────────────────────────────────────────────────────────
RAM Usada: 50% | Threads: 4 | Velocidad: ⚡⚡⚡ Máxima
[████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 50%
✅ contrato_1.pdf procesado
⏳ 19 en cola...

SEGUNDO 10 (Mediados)
─────────────────────────────────────────────────────────
RAM Usada: 68% | Threads: 2 | Velocidad: ⚡⚡ Normal
[████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░] 68%
✅ contrato_1.pdf procesado
✅ contrato_2.pdf procesado
✅ contrato_3.pdf procesado
⏳ 17 en cola...
(Sistema ajustó threads automáticamente)

SEGUNDO 20 (Tres cuartos)
─────────────────────────────────────────────────────────
RAM Usada: 80% | Threads: 2 | Velocidad: ⚡ Lenta
[████████████████████░░░░░░░░░░░░░░░░░░░░░░] 80%
✅ contrato_1-7.pdf procesados
⏳ 13 en cola...

SEGUNDO 30 (Casi final)
─────────────────────────────────────────────────────────
RAM Usada: 50% | Threads: 3 | Velocidad: ⚡⚡⚡ Rápida
[████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 50%
✅ contrato_1-15.pdf procesados
(GC liberó memoria después de contrato 14)
(Sistema aumentó threads automáticamente)
⏳ 5 en cola...

SEGUNDO 45 (Completado)
─────────────────────────────────────────────────────────
RAM Usada: 55% | Threads: 3 | Velocidad: ✅ Completado
[█████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 100%
✅ contrato_1-20.pdf procesados
Tiempo total: 45 segundos
Éxito: 20/20
```

---

## 🔄 Flujo de Interacción del Usuario

```
PASO 1: Usuario abre Redocnizer
└─ Widget muestra estado actual de RAM del sistema
   ✅ Óptimo: 50% RAM, 3 threads


PASO 2: Usuario selecciona 20 contratos
└─ Widget sigue mostrando estado en tiempo real
   ⚠️ Moderado: 65% RAM, 2 threads


PASO 3: Usuario hace clic en "Procesar"
└─ Sistema verifica RAM
   └─ Inicia OCR con threads óptimos (3)
   └─ Widget comienza actualizaciones cada 1 segundo
       ACTUALIZACIÓN 1: ✅ Óptimo: 50% RAM, 3 threads
       ACTUALIZACIÓN 2: ✅ Óptimo: 52% RAM, 3 threads
       ACTUALIZACIÓN 3: ⚠️ Moderado: 68% RAM, 2 threads ← AJUSTÓ THREADS
       ACTUALIZACIÓN 4: ⚠️ Moderado: 70% RAM, 2 threads
       ...


PASO 4: Durante procesamiento
└─ Usuario VE en tiempo real:
   ├─ Barra de RAM (color dinámico)
   ├─ Threads recomendados actual
   ├─ CPU usage actual
   ├─ Barra de progreso de OCR
   └─ Lista de archivos procesados/en cola
   
   EJEMPLO:
   ├─ ✅ contrato_1.pdf → datos/001_SMITH.xlsx
   ├─ ✅ contrato_2.pdf → datos/002_JOHNSON.xlsx
   ├─ ⏳ Procesando contrato_3.pdf...
   └─ □ contrato_4.pdf (en cola)


PASO 5: Si RAM sube demasiado
└─ Sistema PAUSA automáticamente (>90%)
   └─ Widget muestra: ❌ PAUSADO: 92% RAM. Limpiando...
   └─ Usuario NO VE congelación
   └─ Sistema reintenta cuando RAM baja


PASO 6: Procesamiento completo
└─ Widget muestra resumen final:
   ✅ Procesados: 20 archivos
   ✅ Exitosos: 20
   ❌ Errores: 0
   ⏱️ Tiempo: 45 segundos
   📊 RAM final: 55%
```

---

## 🎨 Esquema de Colores del Widget

### Barra de RAM

```
 0% ──────────────────────────────── 100%
 │
 ├─ 0-50%    ████ VERDE      ✅ Excelente
 ├─ 50-70%   ████ VERDE CLR  ✅ Bueno
 ├─ 70-80%   ████ NARANJA    ⚠️ Moderado
 ├─ 80-90%   ████ NARANJA SC ⚠️ Alto
 └─ 90-100%  ████ ROJO       ❌ Crítico
```

### Mensajes de Estado

```
Color     Mensaje                      Acción
──────────────────────────────────────────────────────
Verde     ✅ Óptimo: XX% RAM, N threads → Procesar máxima velocidad
Naranja   ⚠️ Moderado: XX% RAM, 2 threads → Procesar moderado
Naranja   ⚠️ Alto: XX% RAM, 2 threads → Procesar lentamente
Rojo      ❌ PAUSADO: XX% RAM → Esperar liberación RAM
```

---

## 💡 Ejemplos de Situaciones Reales

### Situación 1: Usuario con 8GB RAM, 70% usada

```
Sistema detecta: 2.4GB disponible
Calcula: 2400MB / 350MB = 6.8 threads máx
Pero limita a: min(6, 8 cores × 1.5) = min(6, 12) = 6
DECISIÓN: 6 threads? NO, para seguridad → 2 threads
RESULTADO: Procesamiento estable sin crashes
```

### Situación 2: Usuario abre 5 pestañas Chrome mientras procesa

```
ANTES: RAM 50% → 4 threads
CHROME ABRE: RAM sube a 78%
MONITOR DETECTA: 78% > 70%
AJUSTE AUTOMÁTICO: 4 threads → 2 threads (sin reiniciar)
USUARIO VE: Widget actualiza de 4 a 2 threads
RESULTADO: Sigue procesando sin congelación
```

### Situación 3: Usuario cierra aplicación pesada durante OCR

```
ANTES: RAM 82% → 2 threads
CIERRA EXPLORER: RAM baja a 55%
MONITOR DETECTA: 55% < 70%
AJUSTE AUTOMÁTICO: 2 threads → 4 threads
USUARIO VE: Widget actualiza, velocidad aumenta
RESULTADO: Procesamiento se acelera automáticamente
```

---

## 📱 Vista Responsive

El widget se adapta al tamaño de ventana:

```
VENTANA GRANDE (1600x900)
┌───────────────────────────────────────────┐
│ ✅ Óptimo: 50.5% RAM, 3 threads          │
│ RAM: 8.00GB / 15.84GB (50.5%)             │
│ Disponible: 7.84GB                        │
│                                            │
│ RAM:                                       │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░ 50.5% │
│                                            │
│ 💻 Threads óptimos: 3 | CPU: 12.5%        │
└───────────────────────────────────────────┘


VENTANA PEQUEÑA (800x600)
┌─────────────────────────────────┐
│ ✅ Óptimo: 50.5% RAM, 3 threads │
│ RAM: 8.00GB / 15.84GB (50.5%)   │
│                                  │
│ ████████░░░░░░░░░░░░░░░░░░░  50% │
│                                  │
│ Threads: 3 | CPU: 12.5%          │
└─────────────────────────────────┘
```

---

## 🎓 Interpretación Rápida

| Symbol | Significa | Acción |
|--------|-----------|--------|
| ✅ | Todo bien | Continúa usando la app normalmente |
| ⚠️ | Atención | Procesa, pero más lentamente |
| ❌ | Crítico | Sistema pausó, espera a que libere RAM |
| 🟩 | Barra verde | RAM < 70%, excelente |
| 🟨 | Barra naranja | RAM 70-90%, moderado a alto |
| 🟥 | Barra roja | RAM > 90%, crítico |

---

**Resumen**: El usuario verá cómo la aplicación maneja inteligentemente la memoria, con actualización visual cada segundo, sin que la UI se congele, y con procesamiento óptimo basado en recursos disponibles. ✨
