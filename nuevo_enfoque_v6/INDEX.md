#  Índice de Documentación - Modelo OCR Aether

## Bienvenido al Proyecto

Este es un proyecto completo de **Reconocimiento Óptico de Caracteres (OCR)** utilizando una arquitectura **CRNN (Convolutional Recurrent Neural Network)** con **CTC Loss (Connectionist Temporal Classification)**.

---

##  Guía de Lectura

### 🆕 ¿Nuevo en el proyecto?

**Empieza aquí**:
1.  [README.md](README.md) - Visión general y características
2.  [GUIA_USO.md](GUIA_USO.md) - Inicio rápido y ejemplos
3.  [RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md) - Resumen ejecutivo

**Tiempo de lectura**: ~30 minutos

###  ¿Quieres entender cómo funciona?

**Lee estos**:
1.  [ARQUITECTURA_VISUAL.md](ARQUITECTURA_VISUAL.md) - Diagramas y flujo de datos
2.  [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md) - Detalles técnicos completos
3.  [README.md](README.md) - Sección "Arquitectura del Modelo"

**Tiempo de lectura**: ~2 horas

###  ¿Quieres usar el modelo?

**Consulta**:
1.  [GUIA_USO.md](GUIA_USO.md) - Ejemplos prácticos
2.  [README.md](README.md) - Sección "Uso Rápido"
3. ️ [config.yaml](config.yaml) - Configuración

**Tiempo de setup**: ~15 minutos

###  ¿Quieres modificar o contribuir?

**Revisa**:
1.  [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md) - Implementación detallada
2.  [README.md](README.md) - Sección "Contribuciones"
3.  [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md) - Sección "Troubleshooting"

---

##  Documentos Disponibles

### 1. README.md - Documentación Principal
**Contenido**:
-  Características del proyecto
- ️ Arquitectura del modelo (CRNN + CTC)
-  Instalación y configuración
-  Uso rápido (3 comandos)
-  Estructura del proyecto
-  Pipeline de entrenamiento
-  Data augmentation
-  Evaluación y métricas
-  Optimizaciones de rendimiento
-  Resultados y benchmarks
-  Contribuciones
-  Referencias

**Ideal para**: Visión general completa del proyecto

**Secciones destacadas**:
- Arquitectura detallada con shapes
- Pipeline de entrenamiento explicado
- Data augmentation (10+ transformaciones)
- Métricas de evaluación (Word Accuracy, CER)
- Benchmarks con resultados reales

**Longitud**: ~800 líneas

---

### 2. DOCUMENTACION_TECNICA.md - Guía Técnica Profunda
**Contenido**:
1. **Introducción**
   - ¿Qué es OCR?
   - ¿Por qué CRNN + CTC?
   - Casos de uso

2. **Arquitectura del Modelo**
   - Visión general con diagramas ASCII
   - Input Layer (preprocesamiento)
   - Convolutional Blocks (4 bloques)
   - Reshape a secuencia
   - LSTM Bidireccional (2 capas)
   - Output Layer + Softmax

3. **Fundamentos Teóricos**
   - CTC: ¿Qué problema resuelve?
   - CTC: ¿Cómo funciona?
   - CTC Loss (fórmula matemática)
   - Greedy Decoding
   - Beam Search (alternativa)

4. **Implementación Detallada**
   - Clase CTCPredModel
   - Training step (forward + backward)
   - Test step (validación)
   - Construcción del modelo
   - Vocabulario y codificación

5. **Pipeline de Datos**
   - Dataloader básico
   - Dataloader optimizado (caché + prefetch)
   - Augmentation detallado

6. **Proceso de Entrenamiento**
   - Configuración
   - Learning rate warmup
   - Loop de entrenamiento
   - Validación
   - Detección de colapso

7. **Data Augmentation**
   - 10+ transformaciones explicadas
   - Código de cada transformación
   - Impacto en generalización

8. **Optimizaciones**
   - GPU (Memory Growth, XLA, CUDNN)
   - Dataloader (caché, prefetch)
   - Gradient Clipping
   - Mixed Precision (futuro)

9. **Evaluación y Métricas**
   - Word Accuracy
   - CER (Character Error Rate)
   - Edit Distance (Levenshtein)
   - Accuracy por longitud
   - Matriz de confusión

10. **Troubleshooting**
    - Modelo predice vacío
    - Loss no disminuye
    - Overfitting severo
    - GPU OOM
    - Predicciones aleatorias
    - Debugging tips

**Ideal para**: Entender el funcionamiento interno

**Longitud**: ~1200 líneas

---

### 3. GUIA_USO.md - Manual Práctico
**Contenido**:
1. **Inicio Rápido**
   - Instalación en 2 minutos
   - Entrenar en 3 comandos
   - Evaluar modelo

2. **Entrenamiento Paso a Paso**
   - Preparar fuentes
   - Generar palabras
   - Crear dataset de imágenes
   - Configurar entrenamiento
   - Entrenar modelo
   - Transfer learning

3. **Inferencia y Predicción**
   - Script básico de predicción
   - Batch prediction
   - API REST con Flask

4. **Personalización**
   - Añadir nuevos caracteres
   - Ajustar para palabras largas
   - Modelo para manuscritos
   - Multi-idioma

5. **Ejemplos Avanzados**
   - OCR en video (frame-by-frame)
   - OCR con detección automática
   - OCR paralelo (multi-GPU)
   - Export a TensorFlow Lite

6. **FAQ**
   - ¿Cuánto tarda el entrenamiento?
   - ¿Cuánta memoria necesito?
   - ¿Puedo usar sin entrenar?
   - ¿Cómo mejoro precisión?
   - ¿Funciona con manuscrito?
   - ¿Múltiples líneas?
   - ¿Imágenes de baja calidad?
   - ¿Cómo implementar en producción?
   - ¿Cómo optimizar inferencia?
   - ¿Dónde obtener más datos?

**Ideal para**: Uso práctico y casos de uso

**Longitud**: ~1000 líneas

---

### 4. ARQUITECTURA_VISUAL.md - Diagramas y Visualizaciones
**Contenido**:
1. **Diagrama de Flujo Completo**
   - Desde imagen hasta texto
   - Con ASCII art detallado
   - Shapes en cada paso

2. **Reducción de Dimensiones**
   - Evolución de altura/ancho/canales
   - Por cada capa

3. **Flujo de CTC Loss**
   - Entrenamiento paso a paso
   - Forward pass
   - Loss calculation
   - Backpropagation

4. **Ejemplo Detallado**
   - Predicción de "HOLA"
   - CNN feature extraction
   - Reshape a secuencia
   - LSTM procesa
   - Output layer
   - CTC decoder

5. **Comparación**
   - Con LSTM vs Sin LSTM
   - Ventajas del contexto

6. **Resumen de Shapes**
   - Tabla con todas las capas
   - Input/Output shapes
   - Número de parámetros

**Ideal para**: Entender visualmente

**Longitud**: ~700 líneas

---

### 5. RESUMEN_PROYECTO.md - Executive Summary
**Contenido**:
- Información del proyecto
- Estructura verificada
- Características principales
- Resultados de rendimiento
- Inicio rápido
- Documentación completa (índice)
- Archivos de código principales
- Conceptos clave
- Casos de uso
- Mejoras futuras
- Checklist de verificación
- Conclusión

**Ideal para**: Vista rápida y completa

**Longitud**: ~500 líneas

---

### 6. INDEX.md - Este Documento
**Contenido**:
- Guía de lectura
- Índice de documentos
- Cómo navegar
- Mapas de contenido

**Ideal para**: Navegar la documentación

---

## ️ Mapa de Contenidos

### Por Tema

####  Arquitectura del Modelo
- **README.md** → Sección "Arquitectura del Modelo"
- **DOCUMENTACION_TECNICA.md** → Sección 2 "Arquitectura del Modelo"
- **ARQUITECTURA_VISUAL.md** → Todo el documento

####  Data Augmentation
- **README.md** → Sección "Generación de Dataset"
- **DOCUMENTACION_TECNICA.md** → Sección 7 "Data Augmentation"
- **dataset_creator_v2.py** → Código

####  Instalación y Uso
- **README.md** → Sección "Instalación" y "Uso Rápido"
- **GUIA_USO.md** → Secciones 1, 2, 3

####  Evaluación y Métricas
- **README.md** → Sección "Evaluación y Métricas"
- **DOCUMENTACION_TECNICA.md** → Sección 9 "Evaluación y Métricas"
- **test_generalization.py** → Código

####  Optimizaciones
- **README.md** → Sección "Optimizaciones"
- **DOCUMENTACION_TECNICA.md** → Sección 8 "Optimizaciones"
- **dataloader_optimized.py** → Código

####  Troubleshooting
- **DOCUMENTACION_TECNICA.md** → Sección 10 "Troubleshooting"
- **GUIA_USO.md** → Sección 6 "FAQ"

####  Teoría (CTC, LSTM, etc.)
- **DOCUMENTACION_TECNICA.md** → Sección 3 "Fundamentos Teóricos"
- **README.md** → Sección "Arquitectura del Modelo"

####  Ejemplos de Código
- **GUIA_USO.md** → Secciones 3, 5
- **predict.py** → (crear este archivo)

---

##  Archivos de Código

### Core del Modelo
| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `model.py` | Arquitectura CRNN + CTCPredModel | ~150 |
| `utils.py` | Funciones auxiliares (vocab, decoder) | ~50 |
| `train.py` | Script de entrenamiento optimizado | ~400 |

### Data Pipeline
| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `dataloader.py` | Dataloader básico | ~100 |
| `dataloader_optimized.py` | Dataloader con caché + prefetch | ~200 |

### Generación de Datos
| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `generador_palabras_realistas.py` | Generador de palabras lingüísticas | ~600 |
| `dataset_creator_v2.py` | Creador de imágenes con augmentation | ~800 |

### Pipeline y Testing
| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `pipe_limpio_20k.py` | Pipeline automatizado completo | ~200 |
| `test_generalization.py` | Test de generalización | ~300 |

### Configuración
| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `config.yaml` | Configuración del modelo | ~30 |
| `requirements.txt` | Dependencias Python | ~15 |

---

##  Flujo de Trabajo Recomendado

### Para Investigadores
```
1. README.md (Características y arquitectura)
   ↓
2. DOCUMENTACION_TECNICA.md (Teoría profunda)
   ↓
3. ARQUITECTURA_VISUAL.md (Visualizaciones)
   ↓
4. Código fuente (model.py, train.py)
   ↓
5. Experimentar con hyperparámetros
```

### Para Desarrolladores
```
1. README.md (Instalación y uso rápido)
   ↓
2. GUIA_USO.md (Ejemplos prácticos)
   ↓
3. Entrenar con pipeline (pipe_limpio_20k.py)
   ↓
4. Adaptar para caso de uso específico
   ↓
5. DOCUMENTACION_TECNICA.md (si necesitas modificar)
```

### Para Estudiantes
```
1. README.md (Visión general)
   ↓
2. ARQUITECTURA_VISUAL.md (Diagramas)
   ↓
3. DOCUMENTACION_TECNICA.md (Teoría)
   ↓
4. Experimentar con notebook
   ↓
5. GUIA_USO.md (Ejemplos avanzados)
```

---

##  Navegación Rápida

### Buscar por Palabra Clave

| Palabra Clave | Documento | Sección |
|---------------|-----------|---------|
| **CTC** | DOCUMENTACION_TECNICA.md | 3.1 |
| **LSTM** | DOCUMENTACION_TECNICA.md | 2.2.4 |
| **Augmentation** | DOCUMENTACION_TECNICA.md | 7 |
| **Instalación** | README.md | Instalación |
| **GPU** | DOCUMENTACION_TECNICA.md | 8.1 |
| **Overfitting** | DOCUMENTACION_TECNICA.md | 10.1.3 |
| **API** | GUIA_USO.md | 3.3 |
| **TFLite** | GUIA_USO.md | 5.4 |
| **Manuscrito** | GUIA_USO.md | 4.3 |
| **Multi-GPU** | GUIA_USO.md | 5.3 |

---

##  Enlaces Externos Útiles

### Papers
- [CRNN Paper (Shi et al. 2015)](https://arxiv.org/abs/1507.05717)
- [CTC Paper (Graves et al. 2006)](https://www.cs.toronto.edu/~graves/icml_2006.pdf)

### Documentación TensorFlow
- [tf.nn.ctc_loss](https://www.tensorflow.org/api_docs/python/tf/nn/ctc_loss)
- [tf.keras.layers.LSTM](https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM)

### Datasets
- [IIIT-5K](http://cvit.iiit.ac.in/projects/SceneTextUnderstanding/IIIT5K.html)
- [IAM Handwriting Database](https://fki.tic.heia-fr.ch/databases/iam-handwriting-database)

---

##  Checklist de Documentos

- [x] README.md - Documentación principal completa
- [x] DOCUMENTACION_TECNICA.md - Guía técnica profunda
- [x] GUIA_USO.md - Manual práctico de uso
- [x] ARQUITECTURA_VISUAL.md - Diagramas y visualizaciones
- [x] RESUMEN_PROYECTO.md - Resumen ejecutivo
- [x] INDEX.md - Este documento (índice general)

**Total**: 6 documentos de documentación  
**Líneas totales**: ~4,500 líneas  
**Cobertura**: 100% del proyecto

---

##  Notas

### Convenciones de Documentación
-  = Completado
- ️ = Advertencia/Nota importante
-  = No recomendado/No funciona
-  = Código/Implementación
-  = Teoría/Explicación
-  = Inicio rápido/Acción

### Actualización de Documentos
**Última actualización**: 6 de noviembre de 2025  
**Versión**: 1.0  
**Autor**: Aether

Para actualizar documentación:
1. Modificar el documento correspondiente
2. Actualizar INDEX.md si cambia estructura
3. Actualizar fecha y versión

---

##  ¡Feliz Lectura!

Este proyecto ha sido completamente documentado para facilitar:
-  Comprensión del funcionamiento
-  Uso práctico inmediato
-  Modificación y extensión
-  Aprendizaje de OCR/Deep Learning
-  Implementación en producción

**¿Preguntas o sugerencias?**
Abre un issue en GitHub o consulta la sección FAQ en GUIA_USO.md

---

**Autor**: Aether  
**Proyecto**: Modelo OCR Aether - CRNN con CTC Loss  
**Fecha**: Noviembre 2025  
**Licencia**: MIT

