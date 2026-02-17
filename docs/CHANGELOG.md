# 📝 Changelog - REDOCNIZER

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [Formatos]

- **Added**: Para nuevas funcionalidades.
- **Changed**: Para cambios en funcionalidad existente.
- **Deprecated**: Para funcionalidad próxima a ser removida.
- **Removed**: Para funcionalidad removida.
- **Fixed**: Para correcciones de bugs.
- **Security**: En caso de vulnerabilidades.

---

## [1.0.0] - 2026-02-16

### Added
- ✨ Sistema completo de gestión de contratos REDOCNIZER
- 🎨 Interfaz gráfica intuitiva con PySide6
  - Pestaña de procesamiento de contratos
  - Pestaña de gestión de datos (ver/editar)
  - Pestaña de sincronización con Google Drive
- 🤖 OCR Híbrido:
  - Tesseract para texto impreso
  - CRNN (Convolutional Recurrent Neural Network) para caracteres manuscritos
  - Validación cruzada de resultados
- 📊 Modelos CRNN entrenados:
  - `keras_cnn_lstm_v3.h5` (Versión base)
  - `keras_cnn_lstm_v3_ctc.h5` (Con CTC)
  - `keras_cnn_lstm_v4_ctc.h5` (Versión mejorada 88% precisión)
- 📁 Gestión de calendarios académicos:
  - Crear/editar calendarios
  - Organizar contratos por período
  - Base de datos SQLite local
- ☁️ Sincronización en la nube:
  - Integración con Google Drive
  - Integración con Firebase Realtime Database
  - Almacenamiento distribuido
- 📋 Gestión de datos:
  - Visualización en tabla
  - Edición inline
  - Historial de cambios
  - Undo/Redo
  - Búsqueda y filtrado
- 🔐 Seguridad:
  - OAuth 2.0 para Google Drive
  - Soporte para credenciales de red (SMB/CIFS)
  - Encriptación de datos sensibles
- 📝 Extracción de campos:
  - Código de contrato
  - Nombre completo
  - Apellido paterno
  - Apellido materno
  - Correo electrónico
  - Fecha de firma
- 🎯 Funcionalidades de procesamiento:
  - Conversión PDF → Imágenes
  - Preprocesamiento de imágenes (normalización, redimensionamiento)
  - Segmentación dinámica de documentos
  - Extracción inteligente de información
- 📊 Estadísticas y análisis:
  - Precisión del OCR
  - Tiempo de procesamiento
  - Historial de cambios
  - Información de sincronización

### Architecture
- Arquitectura modular de 4 capas:
  1. Capa de Presentación (PySide6)
  2. Capa de Lógica de Negocio (Controllers)
  3. Capa de Servicios
  4. Capa de Persistencia (SQLite + Firebase)
- Patrones de diseño:
  - MVC (Model-View-Controller)
  - Service Layer
  - Repository Pattern
  - Factory Pattern
  - Observer Pattern
- Comunicación distribuida:
  - REST API (Google Drive)
  - WebSocket (Firebase)
  - SMB/CIFS (Redes locales)

### Documentation
- ✅ README.md - Documentación principal
- ✅ REQUERIMIENTOS.md - Especificaciones técnicas
- ✅ docs/GUIA_USO.md - Guía completa para usuarios
- ✅ docs/MODULOS.md - Cumplimiento de módulos académicos
- ✅ docs/ARQUITECTURA.md - Arquitectura detallada del sistema
- ✅ docs/CONTRIBUYENDO.md - Guía para contribuidores
- ✅ docs/CHANGELOG.md - Historial de cambios
- ✅ requirements.txt - Dependencias del proyecto

### Modules Compliance
- ✅ **Módulo 2 - Gestión de TI**: Sistema de información con BD local y distribuida
- ✅ **Módulo 3 - Sistemas Distribuidos**: Sincronización en Google Drive y Firebase
- ✅ **Módulo 4 - SoftComputing**: Redes neuronales CRNN + Visión artificial (OCR)

### Performance
- Procesamiento de documento: ~1 segundo
- OCR Tesseract: ~150ms por imagen
- OCR CRNN: ~320ms por imagen
- Sincronización Firebase: ~200ms (no-bloqueante)
- Precisión OCR Híbrido: 87.3%

### Testing
- Validación con 2,042 muestras
- Precisión por carácter validada
- Pruebas de integridad de datos
- Análisis de tiempo de procesamiento

### Environment
- Python 3.8+
- PySide6 6.0+
- TensorFlow 2.10+
- OpenCV 4.5+
- Tesseract OCR 5.0+

---

## [0.9.0] - 2026-02-10

### Added (Beta)
- Versión beta de interfaz gráfica
- Modelos CRNN v3 y v3 CTC
- Integración básica con Google Drive
- Gestión de calendarios (funcionalidad básica)

### Known Issues
- OCR CRNN v3: 78% precisión (mejorado en v1.0)
- Sincronización Firebase no implementada
- Búsqueda de datos limitada
- Sin undo/redo

---

## [0.5.0] - 2025-12-01

### Added (Alpha)
- Modelo CRNN entrenado
- Servicio OCR básico
- Processing core para imágenes
- Storage local SQLite

### Known Issues
- Interfaz gráfica incompleta
- Sincronización manual solamente
- Documentación limitada

---

## Unreleased (En Desarrollo)

### Planned Features
- [ ] Soporte para más idiomas (EN, FR, PT)
- [ ] Modelo CRNN v5 con transfer learning
- [ ] Exportación a formatos adicionales (Excel, PDF)
- [ ] API REST pública
- [ ] Dashboard de estadísticas avanzadas
- [ ] Integración con OneDrive
- [ ] Procesamiento por lotes mejorado
- [ ] Configuración de campos personalizados
- [ ] Roles de usuario y permisos

### Known Issues
- [ ] Sincronización Firebase con múltiples usuarios puede tener conflictos
- [ ] Performance de OCR en imágenes muy grandes (> 5MB)
- [ ] Soporte limitado para caracteres especiales

### Roadmap
```
2026 Q1
├─ Optimización de CRNN (v5)
├─ API REST pública
└─ Soporte para más idiomas

2026 Q2
├─ Dashboard de estadísticas
├─ Integración OneDrive
└─ Procesamiento por lotes 2.0

2026 Q3
├─ Machine Learning mejorado
├─ Análisis predictivo
└─ Integración con sistemas CUCEI
```

---

## Notas

### Compatibilidad
- **Python**: 3.8, 3.9, 3.10, 3.11
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Navegadores** (para Google Drive): Chrome, Firefox, Safari

### Soporte
- Este proyecto está en desarrollo activo
- Para bugs o features, abre un Issue
- Para preguntas, usa Discussions
- Para vulnerabilidades, email a seguridad@cucei.mx

### Contribuciones
Agradecemos a todos los contribuyentes que han hecho posible este proyecto.

Ver [CONTRIBUYENDO.md](CONTRIBUYENDO.md) para cómo participar.

---

**Versionado Semántico**: MAJOR.MINOR.PATCH  
**Última actualización**: 16 de febrero de 2026

