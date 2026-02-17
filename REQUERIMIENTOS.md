# 📋 Especificación Técnica de Requerimientos - REDOCNIZER

## 1. Requerimientos Funcionales

### 1.1 Gestión de Documentos
- **RF-001**: El sistema debe permitir cargar uno o múltiples archivos de contrato (PDF, PNG, JPG)
- **RF-002**: El sistema debe convertir archivos PDF a imágenes procesables
- **RF-003**: El sistema debe extraer texto de documentos mediante OCR híbrido
- **RF-004**: El sistema debe segmentar dinámicamente el contenido de documentos
- **RF-005**: El sistema debe almacenar previsualizaciones de documentos procesados

### 1.2 Reconocimiento Inteligente
- **RF-006**: El sistema debe usar redes neuronales CRNN para reconocimiento de caracteres
- **RF-007**: El sistema debe implementar OCR híbrido combinando modelos entrenados y existentes
- **RF-008**: El sistema debe mantener precisión mínima del 85% en reconocimiento
- **RF-009**: El sistema debe procesar imágenes en tiempo real (< 5s por documento)

### 1.3 Gestión de Datos
- **RF-010**: El sistema debe almacenar datos extraídos en formato CSV
- **RF-011**: El sistema debe permitir edición de datos extraídos
- **RF-012**: El sistema debe guardar cambios automáticamente
- **RF-013**: El sistema debe validar integridad de datos
- **RF-014**: El sistema debe mantener historial de cambios

### 1.4 Gestión de Calendarios
- **RF-015**: El sistema debe organizar contratos por calendarios académicos
- **RF-016**: El sistema debe permitir crear/editar calendarios
- **RF-017**: El sistema debe asociar archivos con calendarios específicos

### 1.5 Sincronización en la Nube
- **RF-018**: El sistema debe integrar Google Drive
- **RF-019**: El sistema debe sincronizar datos automáticamente
- **RF-020**: El sistema debe integrar Firebase para almacenamiento distribuido
- **RF-021**: El sistema debe soportar credenciales de red compartida

### 1.6 Interfaz de Usuario
- **RF-022**: El sistema debe proporcionar interfaz intuitiva con pestañas
- **RF-023**: El sistema debe mostrar vista previa de documentos
- **RF-024**: El sistema debe mostrar progreso de procesamiento
- **RF-025**: El sistema debe proporcionar búsqueda y filtrado de datos

## 2. Requerimientos No Funcionales

### 2.1 Rendimiento
- **RNF-001**: Tiempo de procesamiento < 5 segundos por documento
- **RNF-002**: Interfaz responsiva sin bloqueos de UI
- **RNF-003**: Consumo de memoria < 1GB durante operación normal
- **RNF-004**: Soporte para lotes de hasta 50 documentos

### 2.2 Seguridad
- **RNF-005**: Autenticación con Google Drive mediante OAuth 2.0
- **RNF-006**: Encriptación de credenciales de red
- **RNF-007**: Validación de integridad de datos CSV
- **RNF-008**: Protección contra acceso no autorizado a archivos

### 2.3 Confiabilidad
- **RNF-009**: Recuperación ante fallos de procesamiento
- **RNF-010**: Tolerancia a fallos de sincronización en la nube
- **RNF-011**: Respaldo automático de datos
- **RNF-012**: Validación de integridad de base de datos

### 2.4 Mantenibilidad
- **RNF-013**: Código modular y desacoplado
- **RNF-014**: Documentación completa del código
- **RNF-015**: Logs detallados de operaciones
- **RNF-016**: Fácil actualización de modelos ML

### 2.5 Usabilidad
- **RNF-017**: Interfaz intuitiva sin necesidad de capacitación extensa
- **RNF-018**: Soporte para múltiples idiomas (ES, EN)
- **RNF-019**: Dimensionamiento automático de elementos UI
- **RNF-020**: Temas oscuro/claro

### 2.6 Compatibilidad
- **RNF-021**: Compatible con Windows 10/11, macOS, Linux
- **RNF-022**: Python 3.8+
- **RNF-023**: Compatible con sistemas de archivos NTFS, FAT32, ext4
- **RNF-024**: Soporte para rutas UNC (red compartida)

## 3. Requerimientos Técnicos

### 3.1 Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| GUI | PySide6 (Qt6) | 6.0+ |
| Backend | Python | 3.8+ |
| ML/AI | TensorFlow/Keras | 2.10+ |
| Visión Artificial | OpenCV | 4.5+ |
| OCR | Tesseract | 5.0+ / pytesseract |
| Base de Datos | SQLite (local) | 3.36+ |
| Procesamiento PDF | PyPDF2 | 3.0+ |
| Análisis de Datos | pandas | 1.3+ |
| Almacenamiento Nube | Google Drive API | v3 |
| Base de Datos Online | Firebase | Realtime Database |
| Procesamiento de Imágenes | Pillow | 8.0+ |
| Utilidades | numpy | 1.21+ |

### 3.2 Modelos de Machine Learning

#### CRNN (Convolutional Recurrent Neural Network)
- **Propósito**: Reconocimiento de secuencias de caracteres
- **Arquitectura**: 
  - Capas Convolucionales para extracción de características
  - RNN (LSTM) para secuenciación
  - CTC (Connectionist Temporal Classification) para alineación
- **Entrada**: Imágenes de 32x128 píxeles
- **Salida**: Texto reconocido
- **Versiones disponibles**:
  - `keras_cnn_lstm_v3.h5`: Modelo base
  - `keras_cnn_lstm_v3_ctc.h5`: Con CTC
  - `keras_cnn_lstm_v4_ctc.h5`: Versión mejorada

#### OCR Híbrido
- **Componente 1**: Tesseract OCR (modelo preentrenado)
- **Componente 2**: CRNN personalizado (entrenado con dataset de CUCEI)
- **Estrategia**: Combinación de resultados con validación cruzada

### 3.3 Base de Datos

#### Estructura Local (SQLite)
```
calendarios
├── id (INTEGER PRIMARY KEY)
├── nombre (TEXT, UNIQUE)
├── fecha_inicio (DATE)
└── fecha_fin (DATE)

contratos
├── id (INTEGER PRIMARY KEY)
├── id_calendario (FK)
├── codigo (TEXT)
├── nombre (TEXT)
├── paterno (TEXT)
├── materno (TEXT)
├── path_original (TEXT)
├── path_procesado (TEXT)
└── fecha_procesamiento (TIMESTAMP)
```

#### Almacenamiento Distribuido (Firebase)
- Base de datos en tiempo real
- Sincronización automática
- Backups diarios

### 3.4 Protocolo de Comunicación
- **Google Drive API**: REST con OAuth 2.0
- **Firebase**: WebSocket para tiempo real
- Protocolo SMB/CIFS para redes compartidas (Windows)

## 4. Requerimientos de Datos

### 4.1 Entrada
- Formatos: PDF, PNG, JPG, JPEG
- Tamaño máximo: 50MB por archivo
- Resolución mínima: 300 DPI (para OCR)
- Volumen mínimo para validación: 35 documentos

### 4.2 Procesamiento
- Dataset de entrenamiento: 10,000+ imágenes de caracteres
- Dataset de prueba: 2,000+ imágenes
- Proporción entrenamiento:validación:prueba = 70:15:15

### 4.3 Salida
- Formato CSV con campos: Código, Nombre, Paterno, Materno, Fecha
- Validación: Unicidad de códigos, formato de nombres
- Archivos de preview: JPEG 72 DPI

## 5. Requerimientos de Calidad

### 5.1 Pruebas
- **Unitarias**: Mínimo 80% de cobertura
- **Integración**: Validar flujos completos
- **Sistema**: Pruebas end-to-end
- **Rendimiento**: Benchmarking en diferentes configuraciones
- **Usabilidad**: Pruebas con usuarios finales

### 5.2 Estándares de Código
- Adherencia a PEP 8
- Type hints en funciones críticas
- Documentación en docstrings (Google style)
- Máximo de líneas por función: 50

### 5.3 Documentación
- README con guía rápida
- Guía de usuario detallada
- Documentación técnica de arquitectura
- Comentarios en código complejo
- Changelog versionado

## 6. Requerimientos de Seguridad

### 6.1 Autenticación
- OAuth 2.0 para Google Drive
- Credenciales de red con encriptación
- API Keys protegidas en variables de entorno

### 6.2 Autorización
- Roles: Admin, Usuario estándar
- Control de acceso por calendario
- Auditoría de cambios

### 6.3 Protección de Datos
- Datos en tránsito: HTTPS/TLS
- Datos en reposo: Encriptación opcional
- Eliminación segura de temporales

## 7. Requerimientos de Despliegue

### 7.1 Desarrollo
- Git para control de versiones
- Virtual environment para dependencias
- Testing automatizado

### 7.2 Producción
- Empaquetado con PyInstaller
- Instalador ejecutable (.exe para Windows)
- Archivo de configuración centralizado
- Logging y monitoreo

### 7.3 Mantenimiento
- Actualizaciones de modelos
- Patches de seguridad
- Respaldos automáticos
- Recuperación ante desastres

## 8. Restricciones y Limitaciones

- No utilizar servidores locales (según requerimientos de Módulo 3)
- Sincronización distribuida obligatoria
- Validación de integridad de datos en cada operación
- Acceso concurrente limitado a 5 usuarios simultáneos (Firebase plan free)

## 9. Matriz de Trazabilidad

| Módulo | Requerimiento | Funcional | No Funcional | Validación |
|--------|--------------|-----------|--------------|-----------|
| 2 | Gestión TI | RF-010,011,012,013,014 | RNF-012,013,014 | Test BD |
| 3 | Distribuido | RF-018,019,020,021 | RNF-009,010,011 | Integración |
| 4 | SoftComputing | RF-006,007,008,009 | RNF-001,002,003 | Benchmark |

