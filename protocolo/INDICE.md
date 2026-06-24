# ÍNDICE DEL PROTOCOLO DE INVESTIGACIÓN - REDOCNIZER

## 📋 Contenidos Principales

Este protocolo de investigación está organizado en 11 secciones principales más anexos detallados.

---

## 📑 Archivos del Protocolo

### 1. **PROTOCOLO.md** (Documento Principal)
Protocolo completo de investigación con 11 secciones principales.

**Secciones**:
- [Introducción](#introducción) (1)
- [Justificación](#justificación) (2)
- [Objetivos](#objetivos) (3)
- [Hipótesis](#hipótesis) (4)
- [Definición Formal de la Problemática](#definición-formal-de-la-problemática) (5)
- [Marco Teórico](#marco-teórico) (6)
- [Metodología](#metodología) (7)
- [Pruebas y Análisis de Resultados](#pruebas-y-análisis-de-resultados) (8)
- [Conclusiones](#conclusiones) (9)
- [Bibliografía](#bibliografía) (10)
- [Anexos](#anexos) (11)

**Tamaño**: ~120 KB | **Tiempo de lectura**: 3-4 horas

---

## 📎 Anexos Detallados

### ANEXO A: ANEXO_A_ESPECIFICACION_CAMPOS.md
**Especificación técnica detallada de campos a extraer**

Contiene:
- Matriz de campos principales (cédula, nombre, puesto, fechas, calendario)
- Definiciones formales, formatos esperados, reglas de validación
- Ejemplos válidos e inválidos
- Estrategias de OCR específicas por campo
- Matriz de campos secundarios (opcionales)
- Validaciones cruzadas inter-campos
- Tabla de caracteres especiales frecuentes
- Casos de prueba mínimos

**Propósito**: Referencia técnica para programadores y validadores  
**Tamaño**: ~35 KB | **Tiempo de lectura**: 45 min

---

### ANEXO B: ANEXO_B_INSTALACION.md
**Guía completa de instalación y configuración**

Contiene:
- Requisitos del sistema (hardware y software)
- Instalación automática para usuarios finales
- Instalación manual para desarrolladores
- Configuración inicial (asistente)
- Estructura de directorios post-instalación
- Archivo de configuración explicado
- Configuración avanzada (GPU, modelos, proxy)
- Troubleshooting de problemas comunes
- Desinstalación y actualización

**Propósito**: Guía para instaladores y administradores  
**Tamaño**: ~28 KB | **Tiempo de lectura**: 1 hora

---

### ANEXO C: ANEXO_C_FORMATOS_CSV.md
**Especificación completa de formatos de datos**

Contiene:
- Estructura general de almacenamiento CSV
- Archivo principal: contratos.csv (columnas, tipos, valores permitidos)
- Archivo de validación: validacion.csv
- Archivo de historial: historial.csv
- Importación desde otros sistemas
- Exportación a Excel, JSON, SQL
- Respaldos y recuperación
- Validación de integridad de datos
- FAQ sobre manipulación de CSVs

**Propósito**: Referencia para administración de datos  
**Tamaño**: ~32 KB | **Tiempo de lectura**: 1 hora

---

### ANEXO D: ANEXO_D_RESULTADOS_PILOTO.md
(Por crear)
Resultados detallados de pruebas piloto:
- Métrica de desempeño
- Feedback de usuarios
- Curvas de aprendizaje
- Análisis de errores
- Recomendaciones post-piloto

---

### ANEXO E: ANEXO_E_CODIGO_FUENTE.md
(Por crear)
Snippets de código clave:
- Arquitectura de módulos
- Ejemplos de OCR
- Validación de campos
- Integración de servicios

---

### ANEXO F: ANEXO_F_CRONOGRAMA.md
(Por crear)
Cronograma detallado de desarrollo:
- Timeline por fase (14 semanas)
- Hitos y deliverables
- Dependencias entre tareas
- Recursos requeridos

---

### ANEXO G: ANEXO_G_PRESUPUESTO.md
(Por crear)
Presupuesto y recursos:
- Costos de desarrollo
- Costos de infraestructura
- Análisis costo-beneficio
- ROI estimado

---

### ANEXO H: ANEXO_H_RECURSOS.md
(Por crear)
Referencias y recursos adicionales:
- Links a tecnologías
- Publicaciones académicas
- Comunidades de desarrollo
- Herramientas recomendadas

---

## 🎯 Objetivo General del Protocolo

**Diseñar e implementar el software REDOCNIZER como una aplicación de escritorio local orientada al procesamiento masivo de contratos académicos en el CUCEI, mediante la integración de la biblioteca EasyOCR y de un sistema de persistencia basado en almacenamiento estructurado en archivos CSV locales, con el fin de optimizar el tiempo de captura, validación y organización de archivos en un entorno administrativo aislado y seguro.**

---

## 🎯 Objetivos Específicos Principales

### Técnicos
1. Desarrollar módulo de visión artificial (normalización, segmentación)
2. Integrar EasyOCR con preprocesamiento CLAHE y segmentación dinámica
3. Crear extractor de campos con validación automática
4. Desarrollar interfaz gráfica intuitiva (PySide6)
5. Implementar sistema de persistencia en CSV con auditoria

### Administrativos
6. Garantizar seguridad (local, encriptación, sin nube)
7. Facilitar integración con calendario y estructura CUCEI

### Validación
8. Establecer métricas de desempeño (velocidad, precisión)
9. Validar con datos reales del CUCEI

---

## 📊 Métricas de Éxito Esperadas

| Métrica | Meta |
|---------|------|
| **Precisión global** | 92-96% |
| **Velocidad** | <2 seg/documento |
| **Inicio app** | <1 segundo |
| **Mejora vs. manual** | 12-38x más rápido |
| **Usabilidad (SUS)** | ≥75/100 |
| **Tasa de adopción** | ≥80% personal administrativo |
| **Confiabilidad** | <1 crash por 1000 docs |

---

## 🔬 Hipótesis Principales

1. **H1** (Primaria): EasyOCR + CLAHE + Segmentación logra 92-96% precisión, 75-150x mejora
2. **H2**: CLAHE mejora confianza OCR ≥20% en documentos oscuros
3. **H3**: Segmentación dinámica reduce errores de layout ≥25%
4. **H4**: Lazy loading permite inicio <1 segundo
5. **H5**: Interfaz intuitiva permite validación en <1 min
6. **H6**: Almacenamiento local cumple seguridad

---

## 🏗️ Arquitectura General

```
┌─────────────────────┐
│  CAPA PRESENTACIÓN  │ PySide6 (Qt6)
├─────────────────────┤
│  CAPA LÓGICA        │ Contract Controller + Services
├─────────────────────┤
│  CAPA VISIÓN        │ CLAHE + Segmentación Dinámica
├─────────────────────┤
│  CAPA OCR           │ EasyOCR (CNN + LSTM)
├─────────────────────┤
│  CAPA SERVICIOS     │ CSV, PDF, File, GoogleDrive (opt)
├─────────────────────┤
│  CAPA PERSISTENCIA  │ CSV Local + Auditoria
└─────────────────────┘
```

---

## 📈 Timeline de Desarrollo (14 semanas)

| Fase | Semanas | Actividad | Entregables |
|------|---------|-----------|------------|
| **1: Análisis** | 1-2 | Requisitos, análisis | Documento especificación |
| **2: Datos** | 3-4 | Recolección, anotación | Dataset de 1000 docs |
| **3: Desarrollo Core** | 5-8 | EasyOCR + CLAHE + Seg | Módulos funcionales |
| **4: Integración** | 9-10 | Optimización + tuning | Parámetros finales |
| **5: Pruebas** | 11-12 | Validación completa | Reporte de pruebas |
| **6: Despliegue** | 13-14 | Empaque + docum. | .exe + manuales |

---

## 🔑 Tecnologías Principales

**Backend**:
- Python 3.8+
- TensorFlow 2.10+ (Deep Learning)
- OpenCV 4.5+ (Visión Artificial)
- Tesseract 5.0+ (OCR)
- EasyOCR 1.6+ (OCR moderno)
- EasyOCR 1.6+ (Motor OCR principal)
- OpenCV 4.5+ (Visión Artificial + CLAHE)

**Frontend**:
- PySide6 (Qt6 Python bindings)
- QSS (Qt Style Sheets)

**Datos**:
- pandas (manipulación)
- CSV local (persistencia)
- SQLite (opcional para índices)

**DevOps**:
- Git (control versiones)
- PyInstaller (empaquetación)
- GitHub (repositorio)

---

## 📋 Estructura de Directorios del Proyecto

```
redocnizer/
├── app.py                    # Punto de entrada
├── requirements.txt          # Dependencias
├── redocnizer.spec          # Especificación PyInstaller
├── LICENSE                  # GPL v3
├── README.md                # README principal
│
├── docs/                    # Documentación
│   ├── ARQUITECTURA.md
│   ├── GUIA_USO.md
│   └── protocolo/          # Este protocolo
│       ├── PROTOCOLO.md
│       ├── ANEXO_A_*.md
│       ├── ANEXO_B_*.md
│       └── ANEXO_C_*.md
│
├── ui/                      # Interfaz gráfica (PySide6)
│   ├── main_window.py
│   ├── data_tab.py
│   └── ...
│
├── core/                    # Visión artificial + ML
│   ├── CRNN_inference.py
│   ├── preprocessing.py
│   └── ...
│
├── services/                # Servicios
│   ├── ocr_service.py
│   ├── csv_service.py
│   └── ...
│
├── models/                  # Modelos entrenados
│   ├── keras_cnn_lstm_v4_ctc.h5
│   └── ...
│
└── tests/                   # Pruebas unitarias
    └── test_*.py
```

---

## 💾 Archivos de Datos

Después de instalación, se generan:

```
REDOCNIZER_DATA/
├── contratos/              # Datos principales
│   └── 2024A/
│       ├── contratos.csv   # Registros procesados
│       ├── validacion.csv  # Estados de validación
│       └── historial.csv   # Auditoria completa
├── calendarios/            # Referencias académicas
├── logs/                   # Registros de eventos
└── cache/                  # Modelos y datos temporales
```

---

## 🚀 Uso Típico

1. Usuario abre REDOCNIZER
2. Selecciona carpeta raíz y calendario (2024A)
3. Sube PDF o imágenes de contratos
4. Hace clic en "Procesar"
5. Sistema:
   - Convierte PDF → imágenes
     - Preprocesa con CLAHE + Denoising
     - Segmenta dinámicamente en bloques
     - Aplica EasyOCR a cada bloque
   - Extrae campos con validación
   - Guarda en CSV
6. Usuario valida resultados en UI
7. Sistema guarda cambios con auditoria

**Tiempo total**: ~2-4 segundos por documento
**Tiempo total**: ~1-2 segundos por documento (posterior a carga inicial)

---

## ✅ Cómo Navegar Este Protocolo

### Si eres **Directivo/Gestor**:
1. Lee: Secciones 1-3 del PROTOCOLO.md (Introducción, Justificación, Objetivos)
2. Lee: CONCLUSIONES (sección 9)
3. Referencia: Cronograma (ANEXO F)

### Si eres **Desarrollador**:
1. Lee: ARQUITECTURA.md (en docs/)
2. Lee: Secciones 5-7 del PROTOCOLO (Problemática, Marco Teórico, Metodología)
3. Referencia: ANEXO A (campos) + ANEXO C (datos)
4. Referencia: Código fuente (ANEXO E, por crear)

### Si eres **Validador/QA**:
1. Lee: Sección 8 (Pruebas y Análisis de Resultados)
2. Referencia: ANEXO A (especificación de campos)
3. Referencia: ANEXO C (formatos esperados)

### Si eres **Administrador de Sistemas**:
1. Lee: ANEXO B (Instalación)
2. Referencia: ANEXO C (Gestión de datos)
3. Referencia: ANEXO G (Presupuesto/Recursos)

### Si eres **Usuario Final**:
1. Guía rápida: GUIA_USO.md (en docs/)
2. Instalación: ANEXO B (sección 2, Windows)
3. Referencia: Ayuda en la aplicación (tecla F1)

---

## 📞 Contacto y Soporte

**Investigador Principal**: [Nombre/Institución]  
**Correo**: protocolo@cucei.edu.mx  
**Repositorio**: https://github.com/CUCEI/redocnizer  
**Licencia**: GNU General Public License v3.0

---

## 📅 Control de Versiones del Protocolo

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2024-06-23 | Versión inicial completa |
| 1.1 | (Pendiente) | Feedback post-validación |

---

## ✨ Anexos Completados

- ✅ PROTOCOLO.md (Principal)
- ✅ ANEXO_A_ESPECIFICACION_CAMPOS.md
- ✅ ANEXO_B_INSTALACION.md
- ✅ ANEXO_C_FORMATOS_CSV.md
- ⏳ ANEXO_D_RESULTADOS_PILOTO.md (Por crear)
- ⏳ ANEXO_E_CODIGO_FUENTE.md (Por crear)
- ⏳ ANEXO_F_CRONOGRAMA.md (Por crear)
- ⏳ ANEXO_G_PRESUPUESTO.md (Por crear)
- ⏳ ANEXO_H_RECURSOS.md (Por crear)

---

## 🎓 Lectura Recomendada por Rol

### 👨‍💼 Directivo
**Tiempo**: 1-2 horas
- PROTOCOLO.md: Introducción, Justificación, Objetivos (secciones 1-3)
- PROTOCOLO.md: Conclusiones (sección 9)
- Este índice

### 👨‍💻 Desarrollador
**Tiempo**: 8-10 horas
- Este índice
- PROTOCOLO.md: Completo
- ANEXO_A: Especificación de campos
- ANEXO_B: Instalación (desarrollo)
- ANEXO_C: Formatos CSV
- docs/ARQUITECTURA.md

### ✅ Validador/Tester
**Tiempo**: 5-6 horas
- PROTOCOLO.md: Hipótesis y Pruebas (secciones 4, 8)
- ANEXO_A: Campos y validaciones
- ANEXO_C: Integridad de datos

### 🔧 Administrador
**Tiempo**: 3-4 horas
- ANEXO_B: Instalación (completo)
- ANEXO_C: Gestión y respaldos
- PROTOCOLO.md: Marco teórico (sección 6)

---

*Índice generado: 23 de junio de 2024*  
*Protocolo versión: 1.0*  
*Estado: Completado para presentación inicial*

---

## 🔍 Búsqueda Rápida de Temas

Usa Ctrl+F para buscar:
- **"Precisión"** → Busca referencias a precisión OCR
- **"CSV"** → Busca referencias a formato de datos
- **"Tesseract"** → Busca referencias a OCR
- **"CRNN"** → Busca referencias a red neuronal
- **"GPU"** → Busca configuración de aceleración
- **"Error"** → Busca troubleshooting
- **"Validación"** → Busca reglas de validación
- **"Instalación"** → Busca pasos de setup

---

*Fin del Índice*
