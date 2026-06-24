# 📚 PROTOCOLO DE INVESTIGACIÓN - REDOCNIZER

## Bienvenido

Este es el **Protocolo de Investigación Completo** para el proyecto REDOCNIZER, un sistema de procesamiento automático de contratos académicos mediante OCR e Inteligencia Artificial.

---

## 📖 Inicio Rápido

### ¿Qué debo leer primero?

**Por favor, comienza aquí según tu rol:**

1. 🎓 **Estudiante/Investigador** → Lee [PROTOCOLO.md](PROTOCOLO.md)
2. 👨‍💼 **Director/Supervisor** → Lee "Introducción", "Justificación" y "Conclusiones" en [PROTOCOLO.md](PROTOCOLO.md)
3. 👨‍💻 **Programador** → Lee [ANEXO_A_ESPECIFICACION_CAMPOS.md](ANEXO_A_ESPECIFICACION_CAMPOS.md)
4. 🔧 **Administrador del Sistema** → Lee [ANEXO_B_INSTALACION.md](ANEXO_B_INSTALACION.md)
5. 📊 **Analista de Datos** → Lee [ANEXO_C_FORMATOS_CSV.md](ANEXO_C_FORMATOS_CSV.md)

**Para obtener orientación completa**: Consulta [INDICE.md](INDICE.md)

---

## 📁 Archivos en Esta Carpeta

### Documentos Principales

| Archivo | Descripción | Tamaño | Lectura |
|---------|-------------|--------|---------|
| **[PROTOCOLO.md](PROTOCOLO.md)** | 📄 Protocolo completo de investigación (11 secciones) | 120 KB | 3-4h |
| **[INDICE.md](INDICE.md)** | 🗂️ Índice navegable y guía por roles | 25 KB | 15 min |

### Anexos Técnicos

| Archivo | Descripción | Tamaño | Lectura |
|---------|-------------|--------|---------|
| **[ANEXO_A_ESPECIFICACION_CAMPOS.md](ANEXO_A_ESPECIFICACION_CAMPOS.md)** | 🎯 Especificación detallada de campos | 35 KB | 45 min |
| **[ANEXO_B_INSTALACION.md](ANEXO_B_INSTALACION.md)** | 🔧 Guía de instalación y configuración | 28 KB | 1h |
| **[ANEXO_C_FORMATOS_CSV.md](ANEXO_C_FORMATOS_CSV.md)** | 📊 Especificación de formatos de datos | 32 KB | 1h |

### Anexos Por Crear

- ⏳ ANEXO_D_RESULTADOS_PILOTO.md (Resultados de pruebas piloto)
- ⏳ ANEXO_E_CODIGO_FUENTE.md (Snippets de código)
- ⏳ ANEXO_F_CRONOGRAMA.md (Cronograma detallado)
- ⏳ ANEXO_G_PRESUPUESTO.md (Presupuesto y recursos)
- ⏳ ANEXO_H_RECURSOS.md (Referencias y recursos)

---

## 🎯 Objetivo General

> **Diseñar e implementar el software REDOCNIZER como una aplicación de escritorio local orientada al procesamiento masivo de contratos académicos en el CUCEI, mediante la integración de la biblioteca EasyOCR y de un sistema de persistencia basado en almacenamiento estructurado en archivos CSV locales, con el fin de optimizar el tiempo de captura, validación y organización de archivos en un entorno administrativo aislado y seguro.**

---

## 🎯 Objetivos Específicos

### Técnicos
✅ Desarrollar módulo de visión artificial  
✅ Implementar sistema OCR híbrido (EasyOCR + CRNN)  
✅ Crear extractor automático de campos  
✅ Desarrollar interfaz gráfica intuitiva  
✅ Implementar persistencia en CSV con auditoria  

### Administrativos
✅ Garantizar seguridad (local, sin nube)  
✅ Facilitar integración con calendario CUCEI  

### Validación
✅ Establecer métricas de desempeño  
✅ Validar con datos reales CUCEI  

---

## 📊 Métricas de Éxito

| Métrica | Meta |
|---------|------|
| Precisión | ≥95% |
| Velocidad | <4 seg/doc |
| Mejora vs. Manual | 12-38x |
| Usabilidad | ≥75/100 |
| Adopción | ≥80% |
| Confiabilidad | <1 crash/1000 docs |

---

## 🔬 Hipótesis Principales

1. **H1**: OCR híbrido permite ≥95% precisión con 100x mejora
2. **H2**: Preprocesamiento dinámico mejora OCR ≥15%
3. **H3**: CRNN especializado supera genéricos ≥20%
4. **H4**: Segmentación inteligente reduce errores 80%
5. **H5**: Interfaz intuitiva permite validación en <1 min
6. **H6**: CSV local cumple requisitos de seguridad

---

## 🏗️ Arquitectura Simplificada

```
┌────────────────────────┐
│   UI (PySide6/Qt6)     │  ← Interfaz gráfica
├────────────────────────┤
│  Lógica + Controlador  │  ← Orquestación
├────────────────────────┤
│  OCR Híbrido + CRNN    │  ← Procesamiento IA
├────────────────────────┤
│  Servicios CSV, PDF    │  ← Utilidades
├────────────────────────┤
│  Almacenamiento Local  │  ← Datos en CSV
└────────────────────────┘
```

---

## 🚀 Timeline de Desarrollo

| Fase | Semanas | Resultado |
|------|---------|-----------|
| Análisis & Requisitos | 1-2 | Especificación completa |
| Preparación de Datos | 3-4 | Dataset de 1000 documentos |
| Desarrollo Core | 5-8 | Módulos funcionales |
| ML & Entrenamiento | 9-10 | Modelos optimizados |
| Pruebas | 11-12 | Validación de aceptación |
| Despliegue | 13-14 | Producto final |

**Total**: 14 semanas ≈ 3.5 meses

---

## 💡 ¿Cómo Navegar Este Protocolo?

### Opción 1: Por Estructura Lineal
```
PROTOCOLO.md
├─ Sección 1: Introducción
├─ Sección 2: Justificación
├─ Sección 3: Objetivos
├─ Sección 4: Hipótesis
├─ Sección 5: Definición de Problemática
├─ Sección 6: Marco Teórico
├─ Sección 7: Metodología
├─ Sección 8: Pruebas y Resultados
├─ Sección 9: Conclusiones
├─ Sección 10: Bibliografía
└─ Sección 11: Anexos (referencias)
```

### Opción 2: Por Rol Profesional
Ver tabla en [INDICE.md](INDICE.md) para rutas de lectura recomendadas

### Opción 3: Por Tema Específico
Usa **Ctrl+F** para buscar:
- "OCR" → Tecnología de reconocimiento
- "CRNN" → Red neuronal
- "CSV" → Formato de datos
- "Validación" → Criterios de éxito
- "GPU" → Aceleración
- "Error" → Troubleshooting

---

## 🔑 Conceptos Clave

### OCR (Reconocimiento Óptico de Caracteres)
Tecnología que convierte imágenes de texto en texto editable.

REDOCNIZER usa **OCR Híbrido**:
- **Tesseract**: Rápido, baseline
- **EasyOCR**: Moderno, preciso
- **CRNN**: Especializado, máxima precisión
- **Validación cruzada**: Selecciona mejor resultado

### CRNN (Convolutional Recurrent Neural Network)
Red neuronal que combina:
- **Convoluciones**: Extrae características visuales
- **LSTM**: Modela dependencias secuenciales
- **CTC Loss**: Maneja secuencias de longitud variable

### CSV Local
Almacenamiento seguro de contratos en archivos de texto:
```
id,cedula,nombre,puesto,fecha_inicio,fecha_fin,calendario,estado
1,123.456.789,García López,Profesor Titular,2024-01-15,2024-12-31,2024A,validado
```

---

## 📋 Campos Extraídos

REDOCNIZER extrae automáticamente:

| Campo | Formato | Validación |
|-------|---------|-----------|
| **Cédula** | XXX.XXX.XXX | Patrón + checksum |
| **Nombre** | Texto completo | >20 caracteres |
| **Puesto** | Enum (Diccionario) | Fuzzy matching |
| **Fecha Inicio** | YYYY-MM-DD | Rango válido |
| **Fecha Fin** | YYYY-MM-DD | > Inicio, <2 años |
| **Calendario** | YYYYX (X=A/B) | Patrón + año |

Ver [ANEXO_A_ESPECIFICACION_CAMPOS.md](ANEXO_A_ESPECIFICACION_CAMPOS.md) para especificación completa.

---

## 🛠️ Tecnologías

**Backend**:
- Python 3.8+
- TensorFlow 2.10+ (Deep Learning)
- OpenCV 4.5+ (Visión)
- EasyOCR 1.6+, Tesseract 5.0+

**Frontend**:
- PySide6 (Qt6)

**Datos**:
- pandas, numpy
- CSV local

**DevOps**:
- Git, PyInstaller, GitHub

---

## 📖 Lectura Recomendada por Nivel

### ⏱️ Lectura Rápida (15 minutos)
- Este README
- "Introducción" en PROTOCOLO.md
- "Objetivo General" arriba

### ⏱️ Lectura Estándar (2-3 horas)
- Este README
- PROTOCOLO.md (secciones 1-9)
- INDICE.md

### ⏱️ Lectura Completa (8-10 horas)
- Todo el protocolo
- Todos los anexos
- Documentación técnica en docs/

### ⏱️ Lectura para Implementación (20+ horas)
- Lectura completa
- ANEXO_A, B, C
- docs/ARQUITECTURA.md
- Código fuente en GitHub

---

## ❓ Preguntas Frecuentes

### P: ¿Cuál es la diferencia entre este protocolo y la documentación en docs/?

**R**: 
- **Este protocolo** (protocolo/): Investigación académica formal, teoría, resultados
- **Documentación en docs/**: Guías prácticas, arquitectura, guías de uso

### P: ¿Puedo imprimier todo?

**R**: Sí, pero:
- PROTOCOLO.md + ANEXOS_A-C = ~200 páginas
- Mejor: lectura digital (clickeable, con búsqueda)
- O exportar a PDF individualmente

### P: ¿Qué hacer si encuentro errores en el protocolo?

**R**: 
- Reporta en: protocolo@cucei.edu.mx
- O en GitHub issues: https://github.com/CUCEI/redocnizer/issues

### P: ¿Este protocolo está completo?

**R**: 
- ✅ 3 anexos completados (A, B, C)
- ⏳ 5 anexos por crear (D, E, F, G, H)
- ✅ Protocolo principal completo
- ✅ Estructura lista para presentación

### P: ¿Cuál es la siguiente versión?

**R**: 
- v1.1 (Esperada): Post-validación de protocolo
- v1.2 (Proyectada): Anexos D-H completados
- v2.0 (Futuro): Post-piloto con resultados reales

---

## 📞 Contacto

**Investigador Principal**: [Nombre/Institución]  
**Correo Protocolo**: protocolo@cucei.edu.mx  
**Repositorio**: https://github.com/CUCEI/redocnizer  
**Licencia**: GNU General Public License v3.0

---

## 📅 Versión y Historial

**Versión Actual**: 1.0  
**Fecha**: 23 de junio de 2024  
**Estado**: ✅ Completado para presentación inicial  

**Historial**:
- v1.0 (2024-06-23): Versión inicial completa con 4 documentos

---

## ✨ Características de Este Protocolo

✅ **Académicamente riguroso**: Sigue estructura formal de protocolo de investigación  
✅ **Técnicamente detallado**: Especificaciones completas para desarrolladores  
✅ **Prácticamente útil**: Guías de instalación y uso  
✅ **Bien estructurado**: Fácil navegación por roles  
✅ **Autoexplicativo**: Matemáticas y conceptos desarrollados  
✅ **Citado**: ~60 referencias académicas  
✅ **Reproducible**: Especificación completa de metodología  

---

## 🎓 Para Presentación Académica

Si presentas este protocolo en tu universidad:

**Extensión mínima**: Protocolo.md (120 KB)  
**Extensión estándar**: PROTOCOLO.md + ANEXO_A, B, C (~200 KB)  
**Extensión máxima**: Protocolo completo + todos anexos (cuando completados)

**Tiempo de presentación**: 20-30 minutos (resumen ejecutivo)

---

## 🚀 Próximos Pasos

1. ✅ Leer este README
2. ⏳ Seleccionar y leer documento apropiado según rol
3. ⏳ Revisar especificaciones técnicas (ANEXO_A, B, C)
4. ⏳ Validar protocolo con supervisor
5. ⏳ Proceder a fase de implementación

---

## 📚 Estructura de Carpeta Completa

```
n:/Proyecto-modular/
│
├── protocolo/              ← ¡Estás aquí!
│   ├── README.md           ← Este archivo
│   ├── PROTOCOLO.md        ← Documento principal
│   ├── INDICE.md           ← Índice navegable
│   ├── ANEXO_A_*.md        ← Especificación campos
│   ├── ANEXO_B_*.md        ← Instalación
│   ├── ANEXO_C_*.md        ← Formatos CSV
│   ├── ANEXO_D_*.md        ← (Por crear)
│   ├── ANEXO_E_*.md        ← (Por crear)
│   ├── ANEXO_F_*.md        ← (Por crear)
│   ├── ANEXO_G_*.md        ← (Por crear)
│   └── ANEXO_H_*.md        ← (Por crear)
│
├── docs/                   ← Documentación técnica
│   ├── ARQUITECTURA.md
│   ├── GUIA_USO.md
│   └── ...
│
├── app.py
├── requirements.txt
├── ...
```

---

## 🏁 Conclusión

Este protocolo es una **guía completa y académicamente rigorosa** para el desarrollo de REDOCNIZER.

**Comienza ahora**:
1. Abre [PROTOCOLO.md](PROTOCOLO.md) o [INDICE.md](INDICE.md)
2. Elige tu rol y sigue la ruta recomendada
3. ¡Bienvenido a la investigación!

---

**¡Gracias por leer este protocolo!**

*Última actualización: 23 de junio de 2024*  
*Generado automáticamente por sistema de documentación*

---

### 🎯 **¿Dónde Empiezo?**

| Si... | Entonces... |
|--------|-----------|
| Necesito resumen ejecutivo | Lee "Introducción" (5 min) |
| Soy estudiante | Lee PROTOCOLO.md completo (3h) |
| Soy desarrollador | Lee ANEXO_A + código (2h) |
| Soy administrador | Lee ANEXO_B + ANEXO_C (2h) |
| Tengo 30 minutos | Lee este README + INDICE.md |
| Tengo 1 hora | Lee PROTOCOLO.md + este README |
| Tengo 8 horas | Lee todo |

---

*Fin del README*
