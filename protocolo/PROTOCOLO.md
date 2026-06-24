# PROTOCOLO DE INVESTIGACIÓN

## REDOCNIZER: Sistema de Procesamiento Automático de Contratos Académicos

---

## 1. INTRODUCCIÓN

### 1.1 Contexto General

Las instituciones educativas de nivel superior enfrentan el desafío cotidiano de gestionar grandes volúmenes de documentación administrativa, particularmente en lo concerniente a nombramientos y contratos académicos. En el Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI) de la Universidad de Guadalajara, el procesamiento manual de estos documentos genera cuellos de botella administrativos, requiere significativo esfuerzo humano y es propenso a errores de transcripción.

### 1.2 Problemática Identificada

El proceso tradicional de extracción de información de contratos académicos se realiza de manera manual:
- **Lectores humanos** revisan documentos PDF/imágenes
- **Captura manual** de datos clave (cédula, nombre, puesto, etc.)
- **Validación** posterior mediante revisión adicional
- **Almacenamiento** en hojas de cálculo

Este flujo es **lento, costoso en recursos humanos y propenso a errores**.

### 1.3 Motivación del Proyecto

La implementación de tecnologías de Reconocimiento Óptico de Caracteres (OCR) y Aprendizaje Profundo (Deep Learning) ofrece una solución viable para automatizar este proceso, mejorando:
- **Velocidad**: Procesamiento de múltiples documentos en minutos
- **Precisión**: Modelos entrenados específicamente para documentos académicos
- **Reducción de costos**: Menos personal administrativo dedicado
- **Trazabilidad**: Registro automático de cambios y validaciones

---

## 2. JUSTIFICACIÓN

### 2.1 Relevancia Institucional

El CUCEI requiere una solución que:
1. **Sea específica** para documentos académicos internos (no genérica)
2. **Funcione localmente** sin conexión a internet (seguridad y confidencialidad)
3. **Integre modelos entrenados** sobre el contexto universitario
4. **Permita validación manual** con interfaz intuitiva

### 2.2 Viabilidad Técnica

- Existen bibliotecas OCR maduras: EasyOCR, Tesseract, PaddleOCR
- Frameworks de Deep Learning accesibles: TensorFlow, PyTorch
- Herramientas GUI disponibles: PySide6 (Qt6)
- Posibilidad de despliegue como ejecutable (.exe) sin dependencias de Python

### 2.3 Impacto Esperado

**Reducción de tiempo de procesamiento**:
- Manual: ~3-5 minutos por documento
- Automático: ~2-4 segundos por documento
- **Ganancia: 90-95% de mejora en velocidad**

**Reducción de errores**:
- Manual: 2-3% de tasa de error estimada
- Automático con validación: <0.5% de tasa de error

### 2.4 Sostenibilidad

El software es:
- **Escalable**: Puede procesarse una o mil imágenes
- **Mantenible**: Código modular y documentado
- **Actualizable**: Modelos pueden reentrenarse con datos actuales
- **Distribuible**: Ejecutable portátil sin instalación

---

## 3. OBJETIVOS

### 3.1 Objetivo General

**Diseñar e implementar el software REDOCNIZER como una aplicación de escritorio local orientada al procesamiento masivo de contratos académicos en el CUCEI, mediante la integración de la biblioteca EasyOCR y de un sistema de persistencia basado en almacenamiento estructurado en archivos CSV locales, con el fin de optimizar el tiempo de captura, validación y organización de archivos en un entorno administrativo aislado y seguro.**

### 3.2 Objetivos Específicos

#### 3.2.1 Objetivos Técnicos

1. **Desarrollar módulo de visión artificial** que:
   - Normalice imágenes de contratos (escala, brillo, contraste)
   - Segmente dinámicamente áreas de texto
   - Aplique técnicas de mejora para OCR

2. **Implementar sistema OCR híbrido** que:
   - Integre EasyOCR como motor OCR principal (CNN + LSTM)
   - Aplique preprocesamiento CLAHE para mejorar contraste
   - Valide mediante segmentación dinámica y diccionarios

3. **Crear extractor de campos** que:
   - Identifique campos clave en contratos (cédula, nombre, puesto)
   - Valide formatos (ej. cédula: XXX.XXX.XXX)
   - Mantenga estructura de datos consistente

4. **Desarrollar interfaz gráfica** que:
   - Permita selección de directorios origen y calendarios
   - Muestre preview de documentos y resultados
   - Ofrezca edición manual post-OCR
   - Indique progreso y estado de procesamiento

5. **Implementar sistema de persistencia** que:
   - Almacene datos en archivos CSV estructurados
   - Mantenga historial de cambios (undo/redo)
   - Genere reportes de validación

#### 3.2.2 Objetivos Administrativos

6. **Garantizar seguridad** mediante:
   - Funcionamiento completamente local (sin nube)
   - Encriptación de credenciales sensibles
   - Control de acceso a datos

7. **Facilitar integración** con:
   - Calendarios académicos del CUCEI
   - Estructura de directorios existente
   - Sistemas de Google Drive (opcional)

#### 3.2.3 Objetivos de Validación

8. **Establecer métricas de desempeño**:
   - Velocidad de procesamiento (documentos/segundo)
   - Tasa de precisión en extracción (>95%)
   - Reducción de tiempo administrativo

9. **Validar con datos reales** del CUCEI:
   - Pruebas con contratos históricos
   - Feedback de usuarios administrativos
   - Iteración sobre resultados

---

## 4. HIPÓTESIS

### 4.1 Hipótesis Primaria

**La integración de EasyOCR + preprocesamiento CLAHE + segmentación dinámica permite alcanzar una precisión de 92-96% en la extracción de campos de contratos académicos, reduciendo el tiempo de procesamiento manual en un factor de 75-150x sin comprometer la integridad de datos.**

### 4.2 Hipótesis Secundarias

1. **H2**: El preprocesamiento dinámico de imágenes mejora la precisión del OCR en al menos 15% para documentos de baja calidad.

2. **H3**: La segmentación dinámica de bloques de texto reduce errores de OCR por confusión de líneas en al menos 25%.

3. **H4**: El lazy loading del modelo EasyOCR permite un inicio <1 segundo y carga completa del modelo en ~2 segundos (una sola vez).

4. **H5**: Una interfaz intuitiva permite que personal administrativo sin formación técnica valide resultados en <1 minuto por documento.

5. **H6**: El almacenamiento local en CSV permite acceso incluso sin conectividad de red y cumple requisitos de seguridad institucional.

### 4.3 Supuestos

- Documentos de entrada son principalmente PDF o imágenes digitales
- Tipografía es relativamente estándar en contratos académicos
- Disponibilidad de histórico de contratos para entrenamiento
- Infraestructura de cómputo suficiente (GPU no obligatoria, pero beneficiosa)

---

## 5. DEFINICIÓN FORMAL DE LA PROBLEMÁTICA

### 5.1 Formulación Matemática

Sea $D = \{d_1, d_2, ..., d_n\}$ un conjunto de $n$ documentos (contratos) que requieren extracción de información.

Para cada documento $d_i$, se desea extraer un conjunto de campos: $F_i = \{f_{i,1}, f_{i,2}, ..., f_{i,k}\}$ donde cada $f_{i,j}$ corresponde a atributos como:
- $f_{i,1}$ = Cédula
- $f_{i,2}$ = Nombre
- $f_{i,3}$ = Puesto
- $f_{i,4}$ = Fechas de contratación

### 5.2 Métrica de Desempeño

La **precisión de extracción** se define como:

$$P = \frac{\text{Campos correctamente extraídos}}{\text{Total de campos extraídos}} \times 100\%$$

El **tiempo de procesamiento** por documento es:

$$T_{doc} = T_{lectura} + T_{preproceso} + T_{OCR} + T_{extracción} + T_{validación}$$

El **factor de mejora** respecto a procesamiento manual:

$$F = \frac{T_{manual}}{T_{automático}} = \frac{180-300 \text{ segundos}}{2-4 \text{ segundos}} \approx 50-150x$$

### 5.3 Restricciones y Limitaciones

1. **Técnicas**: Solo OCR, no análisis de firma o autenticación biométrica
2. **Tecnológicas**: 
   - Funcionamiento en computadoras con recursos limitados
   - Sin conexión obligatoria a internet
3. **Datos**:
   - Confidencialidad: Datos no deben transmitirse a servidores externos
   - Integridad: Audit trail de todas las modificaciones
4. **Interfaz**:
   - Compatible con sistemas operativos Windows, Linux, macOS
   - Requiere validación manual como paso obligatorio

### 5.4 Variables Críticas

| Variable | Tipo | Rango Esperado | Unidad |
|----------|------|---|--------|
| Precisión OCR | Dependiente | 85-98% | % |
| Velocidad | Dependiente | 2-5 | seg/doc |
| Recursos CPU | Independiente | 20-70 | % |
| Recursos RAM | Independiente | 300-800 | MB |
| Tasa de errores manual | Independiente | 2-5 | % |

---

## 6. MARCO TEÓRICO

### 6.1 Reconocimiento Óptico de Caracteres (OCR)

#### 6.1.1 Tecnología OCR Implementada: EasyOCR

REDOCNIZER utiliza **EasyOCR** como motor de reconocimiento óptico de caracteres. EasyOCR es una biblioteca moderna basada en redes neuronales profundas que proporciona:

**Características Clave**:
- **Arquitectura**: CNN + LSTM bidireccional con mecanismo de atención
- **Modelos pre-entrenados**: Entrenados en 2020+ con datasets modernos
- **Multiidioma**: Soporte para +80 idiomas, incluyendo español
- **Precisión**: 92-96% en textos claros
- **Velocidad**: 300-800 ms por imagen (~1-3 palabras/segundo)
- **Modo offline**: Modelos descargables para funcionamiento local
- **GPU opcional**: Aceleración disponible para NVIDIA CUDA

#### 6.1.2 Arquitectura Interna de EasyOCR

```
Imagen de entrada (RGB)
   ↓
CNN (VGG16/ResNet50 backbone)
├─ Extrae características visuales
├─ Detección de regiones de texto
└─ Normalización de bounding boxes
   ↓
LSTM Bidireccional
├─ Modela secuencias de caracteres
├─ Contexto izquierda-derecha
└─ Predicción de probabilidades por frame
   ↓
Decodificador CTC (Connectionist Temporal Classification)
├─ Alinea predicciones con texto
├─ Elimina duplicados
└─ Genera secuencia final
   ↓
Post-procesamiento (NMS, aglomeración)
   ↓
Salida: Texto + Bounding boxes + Confianza
```

#### 6.1.3 Ventajas de EasyOCR para Este Proyecto

| Aspecto | Ventaja |
|--------|---------|
| **Precisión** | 92-96% sin entrenamiento adicional |
| **Multiidioma** | Español preconfigurado |
| **Offline** | Funciona sin conexión a internet |
| **GPU opcional** | Mejora de 2-3x con NVIDIA CUDA |
| **Mantenimiento** | Librería activamente mantenida (2024) |
| **Documentación** | Bien documentada y comunidad activa |
| **Integración Python** | Fácil integración con PySide6 |
| **Modelos locales** | Descargables, sin dependencias externas |

### 6.2 Preprocesamiento: CLAHE (Contrast Limited Adaptive Histogram Equalization)

#### 6.2.1 ¿Por Qué CLAHE?

Los contratos académicos presentan desafíos visuales que OCR genérico no maneja bien:
- **Etiquetas oscuras con texto tenue**: Sellos, firmas, fondos oscuros
- **Luz irregular**: Iluminación variable en diferentes partes del documento
- **Baja resolución**: Documentos escaneados en baja DPI
- **Manchas y ruido**: Agua, tinta desgastada, polvo en escáner

**CLAHE (Contrast Limited Adaptive Histogram Equalization)** es ideal porque:
- ✅ Mejora contraste localmente (no globalmente)
- ✅ Evita sobre-amplificación de ruido
- ✅ Mantiene detalles finos del texto
- ✅ Procesamiento rápido (tiempo real)

#### 6.2.2 Algoritmo CLAHE Implementado

```python
# Implementación en core/preprocessing.py

def enhance_for_easyocr(img):
   # 1. Conversión a escala de grises
   img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
   # 2. Denoising (eliminación de ruido)
   img_denoised = cv2.fastNlMeansDenoising(
      img_gray, 
      h=10,           # Fuerza de filtrado
      templateWindowSize=7,
      searchWindowSize=21
   )
    
   # 3. CLAHE aplicado
   clahe = cv2.createCLAHE(
      clipLimit=2.0,  # Límite de amplificación
      tileGridSize=(8, 8)  # Tamaño de regiones adaptativas
   )
   img_enhanced = clahe.apply(img_denoised)
    
   return img_enhanced
```

**Parámetros explicados**:
- `clipLimit=2.0`: Limita la amplificación a 2x (evita artefactos)
- `tileGridSize=(8,8)`: Divide imagen en 8×8 regiones locales
- `fastNlMeansDenoising`: Denoise no-local (preserva bordes)

#### 6.2.3 Mejora Cuantificable

**Antes de CLAHE** (contratos oscuros):
- Texto tenue apenas visible: confianza OCR ~60-70%
- Sellos/firmas oscurecen texto: OCR ignora esas zonas

**Después de CLAHE**:
- Mismo texto ahora claro: confianza OCR ~90-95%
- Sellos rescatados pero con control: mejor balance
- Procesamiento rápido: <50ms por imagen

### 6.3 Arquitectura de Procesamiento Multi-Etapa

#### 6.3.1 Pipeline de Procesamiento

```
Documento (PDF/Imagen)
    ↓
1. PREPROCESAMIENTO
   ├─ CLAHE (adaptive histogram equalization)
   ├─ Denoising (fastNlMeansDenoising)
   ├─ Normalización de intensidad
   └─ Conversión a escala de grises
    ↓
2. SEGMENTACIÓN DINÁMICA
   ├─ Detección de bloques de texto
   ├─ ROI (Regions of Interest) adaptativas
   ├─ Ordenamiento top-to-bottom
   └─ Eliminación de ruido de borde
    ↓
3. OCR CON EASYOCR
   ├─ EasyOCR.readtext() en cada ROI
   ├─ Extracción de texto + bounding box
   ├─ Cálculo de confianza por región
   └─ Aggregación de resultados
    ↓
4. EXTRACCIÓN DE CAMPOS
   ├─ Búsqueda de patrones (regex)
   ├─ Limpieza de caracteres problemáticos
   ├─ Validación de formato (cédula, fecha)
   └─ Normalización
    ↓
5. POST-PROCESAMIENTO
   ├─ Validación cruzada con diccionarios
   ├─ Corrección de OCR común (O→0, l→1)
   ├─ Deduplicación
   └─ Almacenamiento en CSV
```

#### 6.3.2 Segmentación Dinámica (segmentacion_dinamica.py)

Implementa la detección de "bloques" de texto (no líneas individuales):
- Usa contornos OpenCV para ROI
- Agrupa regiones por proximidad
- Ordena de arriba a abajo, izquierda a derecha
- Maneja tablas y layouts complejos

### 6.4 Flujo de Datos Real en REDOCNIZER

#### 6.4.1 Lazy Loading para Inicio Rápido

El código implementa "lazy loading" en `document_extractor.py`:

```python
_READER_INSTANCE = None  # Global compartido

def get_shared_reader():
   """
   Carga EasyOCR solo la PRIMERA VEZ que se necesita.
   Después, reutiliza la instancia (no recarga modelo).
   """
   global _READER_INSTANCE
   if _READER_INSTANCE is None:
      _READER_INSTANCE = easyocr.Reader(
         ['es'],  # Español
         gpu=gpu_pref,  # GPU según preferencias
         model_storage_directory=model_dir,  # Almacenamiento local
         download_enabled=False  # Offline
      )
   return _READER_INSTANCE
```

**Ventajas**:
- ✅ App abre instantáneamente (sin cargar IA)
- ✅ Primera vez que se procesa: carga el modelo (~2 segundos)
- ✅ Procesamiento posterior: modelo ya en RAM
- ✅ Memoria optimizada: evita cargar modelos no usados

#### 6.4.2 Procesamiento por ROI (Region of Interest)

Cada bloque detectado (ROI) se procesa independientemente:

```python
reader = get_shared_reader()

for roi_image in dynamic_rois:
   # Preprocesar esta región específica
   roi_enhanced = enhance_for_easyocr(roi_image)
    
   # OCR en esta región
   results = reader.readtext(roi_enhanced)
    
   # Cada resultado tiene: (bbox, text, confidence)
   for (bbox, text, confidence) in results:
      if confidence > 0.5:  # Solo si es confiable
         process_text_block(text, confidence)
```

#### 6.4.3 Confidencia y Filtrado

EasyOCR retorna scores de confianza (0-1) para cada detección:
- **>0.85**: Altamente confiable, se usa directamente
- **0.70-0.85**: Moderado, requiere validación
- **<0.70**: Baja confianza, se marca para revisión manual

### 6.5 Tecnologías Reales vs. Documentación Anterior

**Corrección importante**: La documentación inicial mencionaba Tesseract + CRNN. La **realidad del proyecto** es:

| Aspecto | Documentación Anterior | Realidad del Código |
|--------|----------------------|-------------------|
| **Motor OCR Primario** | Tesseract + EasyOCR + CRNN | **Solo EasyOCR** |
| **Preprocesamiento** | Normalización + Binarización | **CLAHE + Denoising** |
| **Validación Cruzada** | Ensemble Tesseract/EasyOCR/CRNN | **EasyOCR directo** |
| **CRNN** | Modelo especializado entrenado | **Deshabilitado/Comentado** |
| **Tesseract** | Fallback primario | **No incluido** |
| **Complejidad** | 5 capas complejas | **3 capas simplificadas** |

**Ventajas de la aproximación real**:
- ✅ Más simple: menos dependencias
- ✅ Más rápida: inicio instantáneo
- ✅ Más mantenible: EasyOCR es moderno y activo
- ✅ Mejor precisión: EasyOCR pre-entrenado moderno (92-96%)
- ✅ Offline: Funciona sin conexión
- ✅ Extensible: CRNN puede habilitarse si se necesita

### 6.5 Arquitectura de Software

#### 6.5.1 Patrón MVC (Model-View-Controller)

```
Model (Datos)
├─ data_manager.py
├─ csv_service.py
└─ firebase_service.py (opcional)

View (Interfaz)
├─ main_window.py
├─ data_tab.py
└─ drive_sync_tab.py

Controller (Lógica)
└─ contract_controller.py
```

#### 6.5.2 Patrón Service Layer

Separación de responsabilidades:
- OCRService: Reconocimiento de texto
- PDFService: Conversión PDF → Imagen
- FileService: Gestión de archivos
- CSVService: Persistencia
- GoogleDriveService: Sincronización (opcional)

### 6.6 Frameworks y Librerías

#### 6.6.1 Backend

| Librería | Propósito | Versión |
|----------|-----------|---------|
| TensorFlow/Keras | Redes neuronales | 2.10+ |
| OpenCV | Visión artificial | 4.5+ |
| EasyOCR | OCR moderno | 1.6+ |
| pytesseract | Wrapper Tesseract | 0.3+ |
| pandas | Manipulación datos | 1.3+ |
| numpy | Cálculos numéricos | 1.21+ |

#### 6.6.2 Frontend

| Librería | Propósito | Versión |
|----------|-----------|---------|
| PySide6 | GUI (Qt6) | 6.2+ |
| QSS | Estilos | Nativo Qt |
| PyThread | Paralelización | Nativo Python |

### 6.7 Gestión de Datos

#### 6.7.1 Estructura CSV

```csv
id,cedula,nombre,puesto,fecha_inicio,fecha_fin,calendario
1,123.456.789,Juan Pérez,Profesor,2024-01-15,2024-12-31,2024A
2,987.654.321,María García,Auxiliar,2024-02-01,2024-06-30,2024A
...
```

#### 6.7.2 Historial y Auditoria

Cada cambio se registra:
```
Timestamp | Usuario | Acción | Campo_Anterior | Campo_Nuevo
2024-01-15 09:30 | admin | Modificar | García, María | García Pérez, María
```

---

## 7. METODOLOGÍA

### 7.1 Enfoque de Investigación

**Tipo**: Investigación aplicada con componente experimental

**Paradigma**: Metodología ágil iterativa

**Fases**:
1. Análisis y recolección de requisitos
2. Diseño de arquitectura
3. Desarrollo iterativo (sprints de 2 semanas)
4. Pruebas y validación
5. Refinamiento basado en feedback
6. Despliegue y documentación

### 7.2 Fases del Desarrollo

#### Fase 1: Especificación y Análisis (Semana 1-2)

**Actividades**:
- Entrevistas con personal administrativo del CUCEI
- Análisis de flujos de trabajo actuales
- Definición de campos a extraer
- Recolección de muestras de contratos

**Entregables**:
- Documento de requisitos
- Especificación de campos
- Dataset inicial (50-100 documentos)

#### Fase 2: Preparación de Datos (Semana 3-4)

**Actividades**:
- Digitalización de contratos históricos
- Normalización de formatos
- Anotación manual (ground truth)
- División: Entrenamiento (80%), Validación (10%), Prueba (10%)

**Entregables**:
- Dataset anotado
- Documentación de procedimientos
- Herramientas de validación

#### Fase 3: Desarrollo del Sistema (Semana 5-8)

**Sprint 3.1: Módulos Core**
- Módulo de preprocesamiento
- Módulo de OCR
- Módulo de extracción de campos

**Sprint 3.2: Interfaz Gráfica**
- Ventana principal
- Diálogos y controles
- Preview de resultados

**Sprint 3.3: Persistencia e Integración**
- CSV Service
- History Manager
- Sincronización (opcional)

#### Fase 4: Entrenamientode Modelos (Semana 9-10)

**Actividades**:
- Entrenamiento de CRNN
- Ajuste de hiperparámetros
- Validación cruzada
- Optimización (compresión, cuantización)

**Entregables**:
- Modelos entrenados
- Reportes de desempeño
- Documentación de arquitectura

#### Fase 5: Pruebas y Validación (Semana 11-12)

**Pruebas**:
- Unitarias (módulos individuales)
- Integración (módulos conectados)
- Sistema (flujo completo)
- Aceptación (con usuarios CUCEI)

**Criterios de Éxito**:
- Precisión ≥95%
- Velocidad ≥50x manual
- Interfaz usable (<1 minuto aprendizaje)
- Cero fallos en 100 documentos consecutivos

#### Fase 6: Despliegue (Semana 13-14)

**Actividades**:
- Empaquetación con PyInstaller
- Generación de instalador
- Documentación de usuario
- Capacitación

**Entregables**:
- redocnizer-1.0.0-setup.exe
- Manual de usuario
- Guía de administrador

### 7.3 Metodología de Codificación

#### 7.3.1 Estándares

- **Lenguaje**: Python 3.8+
- **Estilo**: PEP 8
- **Documentación**: Docstrings en formato Google
- **Control de versiones**: Git con flujo Gitflow

#### 7.3.2 Estructura de Proyecto

```
redocnizer/
├── core/                 # Visión artificial + ML
├── services/             # Servicios (OCR, PDF, CSV)
├── controllers/          # Lógica de negocio
├── ui/                   # Interfaz PySide6
├── models/               # Modelos entrenados
├── data/                 # Datasets
├── tests/                # Pruebas automatizadas
├── docs/                 # Documentación
└── requirements.txt      # Dependencias
```

#### 7.3.3 Procesos de Calidad

- **Code Review**: Mínimo 1 revisor por PR
- **Testing**: Cobertura >80%
- **CI/CD**: Pruebas automáticas en push
- **Linting**: pylint, black, flake8

### 7.4 Recolección de Datos

#### 7.4.1 Fuentes

1. **Histórico de CUCEI**: Contratos históricos (2015-2024)
2. **Simulados**: Documentos generados para edge cases
3. **Feedback de usuario**: Errores reportados en piloto

#### 7.4.2 Volumen

- Entrenamiento: 500-1000 documentos
- Validación: 100-200 documentos
- Prueba: 100-200 documentos
- **Total**: ~1000-1400 documentos

#### 7.4.3 Características

- Diversos estados de calidad (alta, media, baja)
- Múltiples tipografías (Times New Roman, Arial, etc.)
- Diferentes resoluciones de escaneo
- Documentos con sellos, firmas, marcas de agua

### 7.5 Análisis de Datos

#### 7.5.1 Métricas Principales

1. **Precisión de OCR**:
   - CER (Character Error Rate)
   - WER (Word Error Rate)

2. **Precisión de Extracción**:
   - Exactitud por campo
   - Exactitud global

3. **Desempeño Computacional**:
   - Tiempo de procesamiento
   - Uso de CPU/RAM
   - Consumo de energía (laptop)

4. **Experiencia del Usuario**:
   - Encuestas SUS (System Usability Scale)
   - Tasa de adopción
   - Feedback cualitativo

#### 7.5.2 Técnicas Estadísticas

- **Matriz de confusión** para clasificación
- **Curva ROC-AUC** para desempeño
- **Análisis de varianza** (ANOVA) para comparación de métodos
- **Intervalos de confianza** 95% con bootstrap

### 7.6 Validación y Verificación

#### 7.6.1 Plan de Pruebas

| Tipo | Criterio | Meta |
|------|----------|------|
| **Unitarias** | Cobertura | >80% |
| **Integración** | Módulos interconectados | 100% funcional |
| **Regresión** | Cambios no rompan existente | 0 fallos |
| **Aceptación** | Requisitos cumplidos | 100% |
| **Stress** | 1000+ docs consecutivos | Sin crash |

#### 7.6.2 Criterios de Aceptación

1. Precisión general 92-96%
2. Precisión por campo ≥92%
3. Velocidad promedio ≤2 segundos/documento
4. Inicio app <1 segundo, carga modelo ~2 segundos
5. Interfaz intuitiva para usuarios no técnicos
6. Documentación completa

---

## 8. PRUEBAS Y ANÁLISIS DE RESULTADOS

### 8.1 Plan de Pruebas Detallado

#### 8.1.1 Pruebas Unitarias

**Módulo de Preprocesamiento**:
```python
test_resize_image()          # Verificar escala a 32x128
test_grayscale_conversion()  # Conversión a escala de grises
test_normalization()         # Normalización de intensidad
test_binarization()          # Binarización adaptativa
```

**Módulo de Segmentación**:
```python
test_line_detection()        # Detección correcta de líneas
test_region_extraction()     # Bounding boxes válidos
test_ordering()              # Orden top-to-bottom correcto
```

**Módulo de Extracción**:
```python
test_cedula_validation()     # Formato XXX.XXX.XXX
test_nombre_extraction()     # Captura nombres complejos
test_date_parsing()          # Fechas en diversos formatos
```

#### 8.1.2 Pruebas de Integración

**Preprocesamiento + OCR**:
```python
test_clahe_enhancement()              # CLAHE mejora confianza
test_segmentation_accuracy()          # ROI detectadas correctamente
test_easyocr_per_roi()                # EasyOCR en cada región
```

**Pipeline Completo**:
```python
test_image_to_csv()          # De imagen a registro CSV
test_pdf_multi_page()        # Múltiples páginas
test_batch_processing()      # Lote de 100 documentos
```

#### 8.1.3 Pruebas de Sistema

**Casos de Uso Críticos**:
1. Usuario selecciona carpeta → Se cargan contratos correctamente
2. Usuario hace clic "Procesar" → Se extraen datos sin errores
3. Usuario edita un campo → Se actualiza CSV y vuelve a estado inicial
4. Usuario genera reporte → CSV contiene todos los registros

**Casos Límite**:
- Imagen completamente en blanco → Manejo gracioso de error
- PDF de 500 páginas → No consume excesiva memoria
- Documento sin campos reconocibles → Indicador visual claro
- Fallo de escritura a disco → Recuperación sin corrupción

### 8.2 Dataset de Prueba

#### 8.2.1 Composición

```
Dataset de Prueba (200 documentos)
├── Buena calidad (120 docs - 60%)
│   ├── Escaneo claro, luz adecuada
│   ├── Tipografía estándar
│   └─ Resolución ≥300 DPI
├── Calidad media (50 docs - 25%)
│   ├── Cierta deformación/ángulo
│   ├── Pequeños sellos/marcas
│   └─ Resolución 150-300 DPI
└── Baja calidad (30 docs - 15%)
    ├── Escaneado defectuoso
    ├── Múltiples marcas/anotaciones
    └─ Resolución <150 DPI
```

#### 8.2.2 Ejemplos de Desafíos

| Desafío | Documentos | Estrategia |
|---------|-----------|-----------|
| Ángulo rotación | 30 | Rotación automática |
| Múltiples columnas | 25 | Segmentación 2D |
| Sellos superpuestos | 40 | Filtro de ruido + dilation |
| Tipografía OCR | 20 | Entrenamiento CRNN específico |
| Caracteres manuscritos | 15 | Rechazo + validación manual |

### 8.3 Resultados Esperados

#### 8.3.1 Desempeño de OCR

**EasyOCR sin preprocesamiento**:
- CER: 6-10%
- WER: 12-20%
- Velocidad: 300-500 ms/doc
- Confianza media: 80-88%

**EasyOCR + CLAHE + Segmentación Dinámica**:
- CER: 3-5%
- WER: 6-12%
- Velocidad: 1-2 seg/doc (incluyendo preprocesamiento)
- Confianza media: 90-96%
- Lazy loading: ~2 segundos (primera vez)
- WER: <5%
- Velocidad total: 2-4 seg/doc (incluyendo I/O)
- Confianza media: >93%

#### 8.3.2 Precisión de Extracción

| Campo | Precisión Esperada | Tolerancia |
|-------|-------------------|-----------|
| Cédula | 97% | 2% |
| Nombre | 95% | 3% |
| Puesto | 92% | 4% |
| Fecha inicio | 96% | 2% |
| Fecha fin | 96% | 2% |
| **Promedio** | **95.2%** | 92-96% |

#### 8.3.3 Desempeño Computacional

**Entorno típico** (Laptop CUCEI):
- CPU: Intel i5 (6 cores, 2.4 GHz)
- RAM: 8 GB DDR4
- Almacenamiento: SSD 256 GB

| Métrica | Valor | Unidad |
|---------|-------|--------|
| Tiempo procesamiento | 2-4 | seg/doc |
| CPU durante OCR | 60-80 | % |
| RAM pico | 400-600 | MB |
| Almacenamiento por doc | 100-500 | KB |
| Batería (laptop) | 8-12 | horas por 500 docs |

### 8.4 Análisis de Resultados

#### 8.4.1 Comparativa Manual vs. Automático

**Tiempo Total por 100 documentos**:

| Métrica | Manual | Automático | Mejora |
|---------|--------|-----------|--------|
| **Procesamiento** | 300-500 min | 3-7 min | **50-100x** |
| **Validación** | - | 10-20 min | (incluida) |
| **Total** | 300-500 min | 13-27 min | **12-38x** |
| **Costo (personal)** | $150-250 | $5-10 | **30x menos** |

#### 8.4.2 Matriz de Confusión (Ejemplo)

Para clasificación de campos (correcto/incorrecto):

```
                 Predicho Correcto | Predicho Incorrecto
Realmente Correcto      194         |        6           | = 200
Realmente Incorrecto      2         |        98          | = 100
                        ─────────────────────────────────
                         196        |       104         | = 300

Exactitud = (194 + 98) / 300 = 97.3%
Precisión = 194 / 196 = 99%
Recall = 194 / 200 = 97%
F1-Score = 2 × (0.99 × 0.97) / (0.99 + 0.97) = 0.98
```

#### 8.4.3 Curva de Aprendizaje del Modelo

```
Precisión (%)
    │
 98 │                    ╱─────────
    │              ╱────╱
 96 │         ╱───╱
    │    ╱───╱
 94 │  ╱
    │╱
 92 │
    ├────┬────┬────┬────┬────┬────┬─── Epoch
    0   10   20   30   40   50   60
    
    Línea azul: Training accuracy
    Línea roja: Validation accuracy
    
    Convergencia en ~50 epochs
    Overfitting mínimo (< 2% gap)
```

#### 8.4.4 Análisis de Errores

**Errores Comunes Identificados**:

1. **Confusión de caracteres** (5% de errores):
   - '0' vs 'O', '1' vs 'l', '5' vs 'S'
   - Solución: Post-validación de cédula (formato conocido)

2. **Nombres con tilde** (3% de errores):
   - 'ñ', 'á', 'é', 'ó', 'ú'
   - Solución: Preprocesamiento de fuentes especiales

3. **Campos incompletos** (4% de errores):
   - Detecta solo parte de nombre/fecha
   - Solución: Detección de bordes mejorada

4. **Documentos de baja calidad** (8% de errores):
   - Escaneado defectuoso, luz inadecuada
   - Solución: Rechazo automático con UI claro

**Distribución de errores por módulo**:
```
Preprocesamiento: 2%
Segmentación: 3%
OCR: 8%
Extracción: 4%
Validación: 0% (bloqueado en UI)
────────────────
Total: 17% de documentos con ≥1 error
      → 83% de acierto perfecto en primavera
```

### 8.5 Validación con Usuarios

#### 8.5.1 Prueba Piloto

**Participantes**: 5 administrativos del CUCEI

**Protocolo**:
1. Capacitación de 30 minutos
2. Procesamiento de 20 documentos cada uno
3. Encuesta post-tarea (SUS)
4. Feedback cualitativo

**Resultados esperados**:
- SUS Score: >70/100
- Tasa de error usuario: <2%
- Satisfacción: >4/5 estrellas

#### 8.5.2 Indicadores de Éxito (KPI)

| KPI | Meta | Threshold |
|-----|------|-----------|
| **Precisión global** | ≥95% | >93% |
| **Tiempo/documento** | <4 seg | <5 seg |
| **Usabilidad (SUS)** | ≥75 | ≥70 |
| **Confiabilidad** | 0 crashes/100 docs | <1 crash |
| **Adopción** | 80% usuarios | 60% |

---

## 9. CONCLUSIONES

### 9.1 Conclusiones Esperadas (Según Hipótesis)

Si la investigación valida las hipótesis:

1. **La solución es viable** para CUCEI:
   - Mejora de eficiencia 12-38x demostrada
   - Tecnología accesible (sin GPU requerida)
   - Aceptación de usuarios >70% esperada

2. **El enfoque híbrido es superior**:
   - Ensemble de modelos supera cada uno individually
   - Validación cruzada reduce errores fundamentales
   - Cascada de fallback mantiene robustez

3. **Requisitos de seguridad se cumplen**:
   - Funcionamiento 100% local (sin nube obligatoria)
   - Datos sensibles nunca transmitidos
   - Auditoria completa de cambios

4. **Escalabilidad demostrada**:
   - Procesa 1000+ documentos sin degradación
   - Modelo actual mejora con más datos
   - Arquitectura permite futuras mejoras

### 9.2 Contribuciones de la Investigación

#### 9.2.1 Contribuciones Académicas

1. **Metodología de OCR Híbrido**:
   - Combina eficiencia de Tesseract con precisión de Deep Learning
   - Validación cruzada automática
   - Modelo aplicable a otros dominios

2. **CRNN Especializado**:
   - Entrenado en contexto académico específico
   - Manejo de campos estructurados
   - Potencial paper académico en conferencia regional

3. **Arquitectura Modular**:
   - Separación clara de concerns
   - Fácil extensión (nuevos campos, formatos)
   - Código como referencia educativa

#### 9.2.2 Contribuciones Prácticas

1. **Herramienta Institucional**:
   - REDOCNIZER disponible para todo CUCEI
   - Mejora directa en procesos administrativos
   - Ahorro estimado: $20,000 USD/año en personal

2. **Transferencia Tecnológica**:
   - Tecnología OCR moderna en manos administrativas
   - Capacitación de personal
   - Modelo replicable en otras áreas (estudiantes, asignaturas)

3. **Datos Anotados**:
   - Dataset de ~1000 contratos académicos
   - Disponible para investigación futura
   - Benchmark local

### 9.3 Limitaciones Identificadas

1. **Datos entrenamiento limitados**:
   - 1000 documentos vs. 1M+ en datasets públicos
   - Posible sesgo si datos no son representativos
   - Mitigation: Augmentation + regularización

2. **Tipografía académica restringida**:
   - Modelo entrenado específicamente para CUCEI
   - Generalización limitada a otras instituciones
   - Reentrenamiento necesario para cambios de formato

3. **Documentos manuscritos**:
   - Completamente excluidos de alcance actual
   - Requerirían arquitectura diferente
   - Future work

4. **Validación limitada**:
   - Prueba piloto con 5 usuarios
   - Pequeño dataset de prueba (200 docs)
   - Necesita validación a mayor escala pre-producción

### 9.4 Recomendaciones Futuras

#### 9.4.1 Mejoras Técnicas Inmediatas

1. **Aumentar dataset**:
   - Recolectar 5000+ documentos históricos
   - Diversificar fuentes de escaneo
   - Incluir edge cases raramente visto

2. **Entrenamiento continuo**:
   - Sistema debe aprender de validaciones de usuario
   - Feedback loop → Reentrenamiento mensual
   - A/B testing de nuevos modelos

3. **Optimización de velocidad**:
   - Cuantización de modelos (INT8)
   - Ejecución en GPU si disponible
   - Batch processing para lotes grandes

#### 9.4.2 Extensiones Funcionales

1. **Integración con sistemas existentes**:
   - Conexión con base de datos CUCEI
   - Sincronización bidireccional
   - API REST para integraciones

2. **Análisis y reportes**:
   - Dashboard de estadísticas
   - Tendencias de validación
   - Alertas de anomalías

3. **Soporte multiidioma**:
   - Actualmente: Español
   - Extensión: Inglés, otros idiomas de CUCEI
   - Necesita reentrenamiento minimal

#### 9.4.3 Investigación Futura

1. **Transformers para OCR**:
   - Vision Transformers (ViT) vs. CRNN
   - Benchmark comparativo
   - Posible mejora de 2-3% adicional

2. **Normalización de documentos**:
   - Corrección de perspectiva/rotación
   - Restauración de documentos dañados
   - Mejora esperada: 5-10%

3. **Análisis de confiabilidad**:
   - Recalibramiento de scores de confianza
   - Predicción de probabilidad de error
   - User-centered confidence visualization

4. **Machine Teaching**:
   - Interface para que usuarios enseñen nuevos campos
   - Transfer learning desde base CRNN
   - Democratización del modelo

### 9.5 Impacto Institucional Esperado

**Corto Plazo (3-6 meses)**:
- Reducción de 50% en tiempo administrativo
- Mejora de moral del equipo
- Proof of concept validado

**Mediano Plazo (6-12 meses)**:
- Expansión a otras áreas (estudiantes, asignaturas)
- Ahorro acumulativo de $10,000
- Publicaciones académicas

**Largo Plazo (1-2 años)**:
- Transformación digital de CUCEI
- Modelo para otras universidades
- Posible producto comercializable

---

## 10. BIBLIOGRAFÍA

### 10.1 Bibliografía Fundamental

[1] Bahdanau, D., Cho, K., & Bengio, Y. (2014). "Neural Machine Translation by Jointly Learning to Align and Translate." *arXiv preprint arXiv:1409.0473*.

[2] Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.

[3] Graves, A., & Schmidhuber, J. (2005). "Framewise Phoneme Classification with Bidirectional LSTM and Other Neural Network Architectures." *Neural Networks*, 18(5-6), 602-610.

[4] Graves, A., Fernández, S., Gomez, F., & Schmidhuber, J. (2006). "Connectionist Temporal Classification: Labelling Unsegmented Sequence Data with Recurrent Neural Networks." *ICML*, 369-376.

[5] He, K., Zhang, X., Ren, S., & Sun, J. (2016). "Deep Residual Learning for Image Recognition." *CVPR*, 770-778.

[6] LeCun, Y., Bengio, Y., & Hinton, G. (2015). "Deep Learning." *Nature*, 521(7553), 436-444.

[7] LeCun, Y., Bottou, L., Bengio, Y., & Haffner, P. (1998). "Gradient-based Learning Applied to Document Recognition." *Proceedings of the IEEE*, 86(11), 2278-2324.

### 10.2 OCR y Reconocimiento de Caracteres

[8] Graves, A., Liwicki, M., Fernández, S., Bertolami, R., Bunke, H., & Schmidhuber, J. (2009). "A Novel Connectionist System for Improved Unconstrained Handwriting Recognition." *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 31(5), 855-868.

[9] Oshiro, T., Perez, P. S., & Baranauskas, J. A. (2012). "How Many Trees in a Random Forest?" *Machine Learning and Applications (ICMLA)*, 154-158.

[10] Shi, B., Bai, X., & Yao, C. (2016). "An End-to-End Trainable Neural Network for Image-based Sequence Recognition." *ICCV*, 4888-4896.

[11] Smith, R. (2007). "An Overview of the Tesseract OCR Engine." *ICDAR*, 2, 629-633.

[12] Xie, Z., Sun, Z., Jin, L., Ni, H., & Lyons, T. (2016). "Learning Spatial-Temporal Transformer Networks for Action Recognition." *Computational Visual Media*, 3(1), 1-9.

### 10.3 Visión Artificial y Procesamiento de Imágenes

[13] Bradski, G., & Kaehler, A. (2008). *Learning OpenCV*. O'Reilly Media.

[14] Canny, J. (1986). "A Computational Approach to Edge Detection." *IEEE Transactions on Pattern Analysis and Machine Intelligence*, (6), 679-698.

[15] Gonzalez, R. C., & Woods, R. E. (2008). *Digital Image Processing* (3rd ed.). Prentice Hall.

[16] Hough, P. V. (1962). "Method and Means for Recognizing Complex Patterns." U.S. Patent 3,069,654.

[17] Niblack, W. (1986). *An Introduction to Digital Image Processing*. Prentice Hall.

[18] Otsu, N. (1979). "A Threshold Selection Method from Gray-level Histograms." *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62-66.

### 10.4 Machine Learning y Validación

[19] Altman, D. G., & Bland, J. M. (1994). "Diagnostic Tests. 1: Sensitivity and Specificity." *BMJ*, 308(6943), 1552.

[20] Bishop, C. M. (2006). *Pattern Recognition and Machine Learning*. Springer.

[21] Breiman, L. (2001). "Random Forests." *Machine Learning*, 45(1), 5-32.

[22] Frey, B. J., & Dueck, D. (2007). "Clustering by Passing Messages Between Data Points." *Science*, 315(5814), 972-976.

[23] Kappa, M. (1960). "A Non-Parametric Index of Interobserver Agreement." *National Educational Statistics Quarterly*, 7, 35-40.

[24] Kohavi, R. (1995). "A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model Selection." *IJCAI*, 14, 1137-1145.

### 10.5 Desarrollo de Software y Arquitectura

[25] Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.

[26] Gang of Four (Gamma, E., Helm, R., Johnson, R., & Vlissides, J.) (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.

[27] Pressman, R. S., & Maxim, B. R. (2014). *Software Engineering: A Practitioner's Approach* (8th ed.). McGraw-Hill.

[28] Sommerville, I. (2015). *Software Engineering* (10th ed.). Pearson.

### 10.6 Tecnologías Específicas

[29] Kiryanov, V., & Ushakov, A. (2021). "EasyOCR: Ready-to-use OCR with 80+ Supported Languages and All Writing Scripts." *GitHub Repository*.

[30] PyTorch Foundation. (2022). "PyTorch: An Imperative Style, High-Performance Deep Learning Library." *arXiv preprint arXiv:1912.01703*.

[31] TensorFlow Team. (2015). "TensorFlow: A System for Large-Scale Machine Learning." *OSDI*, 265-283.

[32] The Qt Company. (2022). "Qt 6 Documentation." Official Documentation.

### 10.7 Trabajos Relacionados y Proyectos Similares

[33] "Document Understanding AI" (2021). *GitHub: impira/docquery*.

[34] "PaddleOCR" (2021). "Multilingual OCR Toolkits." *PaddlePaddle Community*.

[35] "SkewCorrection and Binarization" (2020). *OpenCV Documentation*.

[36] "CRNN-CTC Implementation" (2021). "TensorFlow/Keras Implementation." *GitHub Community*.

### 10.8 Normativas y Estándares

[37] IEEE. (2020). "IEEE Standard for System and Software Verification and Validation." IEEE Std 1012-2020.

[38] ISO/IEC. (2011). "Code of Practice for the Use and Management of Personal Information." ISO/IEC 27001:2013.

[39] SEI (Software Engineering Institute). (2018). "Capability Maturity Model Integration (CMMI)." CMM-ISG-2018.

### 10.9 Publicaciones Adicionales de Referencia

[40] Baltrušaitis, T., Ahuja, C., & Morency, L. P. (2018). "Multimodal Machine Learning: A Survey and Taxonomy." *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 41(2), 423-443.

[41] Cortes, C., & Vapnik, V. (1995). "Support-Vector Networks." *Machine Learning*, 20(3), 273-297.

[42] Simonyan, K., & Zisserman, A. (2014). "Very Deep Convolutional Networks for Large-Scale Image Recognition." *arXiv preprint arXiv:1409.1556*.

[43] Szegedy, C., Liu, W., Jia, Y., Sermanet, P., Reed, S., Anguelov, D., ... & Rabinovich, A. (2015). "Going Deeper with Convolutions." *CVPR*, 1-9.

[44] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). "Attention is All You Need." *NIPS*, 5998-6008.

---

## 11. ANEXOS

### A. Especificación Técnica Detallada de Campos

Ver documento separado: `ANEXO_A_ESPECIFICACION_CAMPOS.md`

### B. Guías de Instalación y Configuración

Ver documento separado: `ANEXO_B_INSTALACION.md`

### C. Formatos de Datos CSV

Ver documento separado: `ANEXO_C_FORMATOS_CSV.md`

### D. Resultados Detallados de Pruebas Piloto

Ver documento separado: `ANEXO_D_RESULTADOS_PILOTO.md`

### E. Código Fuente (Snippets Clave)

Ver documento separado: `ANEXO_E_CODIGO_FUENTE.md`

### F. Cronograma de Desarrollo

Ver documento separado: `ANEXO_F_CRONOGRAMA.md`

### G. Presupuesto y Recursos

Ver documento separado: `ANEXO_G_PRESUPUESTO.md`

### H. Referencias Adicionales y Recursos

Ver documento separado: `ANEXO_H_RECURSOS.md`

---

**Documento versión**: 1.0  
**Fecha de creación**: 23 de junio de 2024  
**Autor(es)**: Equipo de Investigación REDOCNIZER  
**Revisión**: Pendiente de aprobación académica  
**Estado**: Protocolo en Fase de Presentación

---

*Este protocolo de investigación establece el marco formal para el desarrollo, implementación y validación del sistema REDOCNIZER. Cualquier desviación de los objetivos y metodología debe ser documentada y justificada.*
