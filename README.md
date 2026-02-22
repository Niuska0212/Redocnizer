# 📄 REDOCNIZER - Gestión Inteligente de Contratos

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.0%2B-green)](https://doc.qt.io/qtforpython-6/)

**REDOCNIZER** es un sistema inteligente de gestión de contratos para la Universidad de Guadalajara - CUCEI. Utiliza **Visión Artificial con OCR Híbrido** y **Redes Neuronales CRNN** para automatizar la extracción y clasificación de información de documentos contractuales.

## 🎯 Características Principales

- **📊 Procesamiento de Documentos**: Conversión automática de PDF a imágenes y extracción de texto mediante OCR híbrido
- **🧠 Reconocimiento Inteligente**: Uso de redes neuronales CRNN para reconocimiento de caracteres manuscritos e impresos
- **📁 Gestión de Calendarios**: Organización de contratos por períodos académicos (2024A, 2024B, 2025A, etc.)
- **☁️ Sincronización en la Nube**: Integración con Google Drive y Firebase para almacenamiento distribuido
- **📈 Gestión de Datos**: Vista, edición y almacenamiento de información extraída en CSV
- **🔐 Credenciales de Red**: Soporte para acceso a depósitos compartidos en red
- **🎨 Interfaz Intuitiva**: Aplicación de escritorio con PySide6 (Qt)

## 📋 Requisitos del Sistema

### Software
- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows, macOS, Linux
- **Memoria**: 4GB mínimo (recomendado 8GB)
- **Espacio en disco**: 2GB para modelos y datos

### Dependencias Principales
Ver [requirements.txt](requirements.txt) para la lista completa.

Principales:
- `PySide6`: Interfaz gráfica
- `TensorFlow/Keras`: Modelos de redes neuronales
- `OpenCV`: Procesamiento de imágenes
- `EasyOCR`: OCR
- `pandas`: Manejo de datos CSV
- `PyPDF2`: Procesamiento de PDF

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone https://github.com/Niuska0212/Redocnizer.git
cd redocnizer
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python app.py
```

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [GUIA_USO.md](docs/GUIA_USO.md) | Guía completa de uso del programa |
| [MODULOS.md](docs/MODULOS.md) | Cumplimiento de módulos requeridos |
| [ARQUITECTURA.md](docs/ARQUITECTURA.md) | Diseño y arquitectura del sistema |
| [REQUERIMIENTOS.md](REQUERIMIENTOS.md) | Especificaciones técnicas y requisitos |

## 🏗️ Estructura del Proyecto

```
redocnizer/
├── app.py                 # Punto de entrada principal
├── README.md             # Este archivo
├── REQUERIMIENTOS.md     # Especificaciones técnicas
├── requirements.txt      # Dependencias Python
├── docs/                 # Documentación
│   ├── GUIA_USO.md      # Guía de uso detallada
│   ├── MODULOS.md       # Módulos cumplidos
│   └── ARQUITECTURA.md  # Arquitectura del sistema
├── controllers/          # Controladores de lógica de negocio
│   └── contract_controller.py
├── core/                 # Núcleo de visión artificial
│   ├── CRNN_inference.py
│   ├── document_extractor.py
│   ├── preprocessing.py
│   └── segmentacion_dinamica.py
├── services/             # Servicios (OCR, PDF, Firebase, Drive)
│   ├── ocr_service.py
│   ├── pdf_service.py
│   ├── firebase_service.py
│   ├── google_drive_service.py
│   ├── api_server.py
│   └── ...
├── ui/                   # Interfaz gráfica
│   ├── main_window.py
│   ├── data_tab.py
│   ├── drive_sync_tab.py
│   ├── calendar_db.py
│   └── ...
├── models/               # Modelos entrenados
│   ├── keras_cnn_lstm_v3_ctc.h5
│   ├── keras_cnn_lstm_v4_ctc.h5
│   └── ...
├── data/                 # Datos y datasets
│   └── dataset/          # Dataset de entrenamiento
└── previews/             # Almacenamiento temporal de previsualizaciones
```

## 🎓 Módulos Académicos Cumplidos

✅ **Módulo 2**: Gestión de las Tecnologías de la Información  
✅ **Módulo 3**: Sistemas Robustos, Paralelos y Distribuidos  
✅ **Módulo 4**: Cómputo Flexible (SoftComputing)  

Ver [MODULOS.md](docs/MODULOS.md) para detalles completos.

## 📖 Guía Rápida de Uso

### Procesamiento de Contratos

1. **Seleccionar Directorio Raíz**
   - Click en "📁 Seleccionar directorio raíz"
   - Elegir la carpeta contenedora de calendarios

2. **Subir Contratos**
   - Click en "📎 Subir contrato(s)"
   - Seleccionar uno o más archivos PDF/PNG/JPG

3. **Procesar**
   - Seleccionar calendario (ej: 2024A)
   - Click en "🚀 Procesar Contrato(s)"
   - Esperar a que complete la extracción

4. **Ver Datos**
   - Ir a pestaña "📊 Ver/Editar Datos"
   - Revisar información extraída
   - Editar si es necesario

### Sincronizar con Google Drive

1. Ir a pestaña "☁️ Sincronización Nube"
2. Conectar con Google Drive
3. Sincronizar calendarios automáticamente

Ver [GUIA_USO.md](docs/GUIA_USO.md) para guía completa.

## 🔧 Configuración Avanzada

### Variables de Entorno
Crear archivo `.env` en la raíz:
```env
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
FIREBASE_URL=https://tu-firebase.firebaseio.com
FIREBASE_KEY=tu-clave-privada
```

### Modelos Personalizados
Ver [ARQUITECTURA.md](docs/ARQUITECTURA.md) para entrenar modelos propios.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 👥 Autores
- **Alumnos**: Niuska Isabel Gonzalez Rangel y Luis Diego Uribe Sandoval
- **Equipo de Desarrollo**: Proyecto Modular CUCEI 2025 - 2026 
- **Institución**: Universidad de Guadalajara - Centro Universitario de Ciencias Exactas e Ingenierías

## 📞 Soporte

Para reportar problemas o sugerencias:
- Abre un [Issue](https://github.com/Niuska0212/Redocnizer/issue)
- Contacta con el equipo de desarrollo

---

**Versión**: 1.1.1
**Última actualización**: 16 de febrero de 2026  
**Estado**: En desarrollo activo

