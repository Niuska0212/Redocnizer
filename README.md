<p align="center">
  <img src="ui/assets/logo_redocnizer.png" alt="REDOCNIZER Logo" width="200">
</p>

# 📄 REDOCNIZER - Gestión Inteligente de Contratos

[![GitHub release](https://img.shields.io/github/v/release/Niuska0212/Redocnizer?style=flat-square)](https://github.com/Niuska0212/Redocnizer/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.0%2B-green)](https://doc.qt.io/qtforpython-6/)

**REDOCNIZER** es una aplicación de escritorio para la Universidad de Guadalajara - CUCEI que automatiza la extracción y clasificación de datos de contratos académicos mediante Visión Artificial y OCR, con procesamiento y almacenamiento completamente locales.

## 📥 Descargar Aplicación

Si deseas utilizar la herramienta sin configurar el entorno de desarrollo, puedes descargar la última versión estable del ejecutable para Windows aquí:

[**➔ Descargar la ultima version de REDOCNIZER(.exe)**](https://github.com/Niuska0212/Redocnizer/releases/latest)

---

## 🎯 Características Principales

- **📊 Procesamiento de Documentos**: Conversión automática de PDF a imágenes y extracción de texto mediante OCR
- **🧠 Reconocimiento de Texto**: Motor OCR EasyOCR ejecutado localmente (modelos descargados una sola vez, sin conexión requerida en tiempo de uso), con un pipeline de preprocesamiento propio en OpenCV para localizar y limpiar las regiones de interés antes de leerlas
- **📁 Gestión de Calendarios**: Organización de contratos por períodos académicos (2024A, 2024B, 2025A, etc.), calculados automáticamente a partir de la fecha extraída del contrato
- **⚡ Procesamiento Concurrente**: Lotes de contratos procesados en paralelo mediante un pool de hilos (`QThreadPool`), con monitoreo de memoria RAM en tiempo real para evitar saturar el equipo
- **💾 Almacenamiento 100% Local**: Los datos extraídos se guardan en archivos CSV locales por calendario; no hay sincronización ni dependencia de servicios en la nube
- **🗄️ Organización de Archivos en Red Local**: Soporta guardar los expedientes en una unidad de red compartida de la institución (rutas UNC tipo `//servidor/recurso`), con un diálogo de autenticación para credenciales de red — esto es una carpeta compartida local, no un servicio en la nube
- **🎨 Interfaz Intuitiva**: Aplicación de escritorio con PySide6 (Qt)

## 📋 Requisitos del Sistema (Para Desarrolladores)

### Software
- **Python**: 3.10 o inferior
- **Sistema Operativo**: Windows
- **Memoria**: 8GB mínimo (recomendado 12GB)
- **Espacio en disco**: 10GB para modelos y datos

### Dependencias Principales
Ver [requirements.txt](requirements.txt) para la lista completa.

Principales:
- `PySide6`: Interfaz gráfica
- `EasyOCR`: motor de reconocimiento óptico de caracteres
- `OpenCV`: preprocesamiento y segmentación de imágenes
- `pandas`: manejo de datos y exportación a CSV
- `PyPDF2` / `pdf2image` / `PyMuPDF`: conversión y procesamiento de PDF
- `psutil`: monitoreo de memoria durante el procesamiento por lotes
- `TensorFlow/Keras`: incluidas como dependencia porque el repositorio conserva el pipeline de entrenamiento de un modelo CRNN propio (ver [Notas de alcance](#-notas-de-alcance-y-componentes-no-activos)), aunque **no se usan en el flujo de reconocimiento activo**

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
| [REQUERIMIENTOS.md](docs/REQUERIMIENTOS.md) | Especificaciones técnicas y requisitos |

> ⚠️ Estos documentos describen una versión anterior del sistema, con sincronización en la nube (Google Drive/Firebase) y un motor OCR híbrido con red neuronal CRNN propia. La versión actual del código (documentada en este README) es una versión local simplificada. Estos documentos están pendientes de actualizarse para reflejar el estado actual.

## 🏗️ Estructura del Proyecto

```
redocnizer/
├── app.py                 # Punto de entrada principal
├── README.md              # Este archivo
├── requirements.txt       # Dependencias Python (versión activa)
├── requirements_distribuido.txt  # Dependencias de una variante distribuida no activa (ver Notas de alcance)
├── docs/                  # Documentación (pendiente de actualizar, ver aviso arriba)
│   ├── GUIA_USO.md
│   ├── MODULOS.md
│   ├── ARQUITECTURA.md
│   └── REQUERIMIENTOS.md
├── controllers/           # Controladores de lógica de negocio
│   └── contract_controller.py
├── core/                  # Núcleo de visión artificial
│   ├── document_extractor.py   # Orquesta preprocesamiento + EasyOCR
│   ├── preprocessing.py        # Preprocesamiento de imagen (OpenCV)
│   ├── segmentacion_dinamica.py # Localización de regiones de interés (ROIs)
│   └── CRNN_inference.py       # Módulo de inferencia CRNN (no activo, ver Notas de alcance)
├── services/               # Servicios de la aplicación
│   ├── ocr_service.py          # Envuelve el pipeline de OCR activo (EasyOCR)
│   ├── pdf_service.py          # Conversión PDF ↔ imagen
│   ├── file_service.py         # Organización de expedientes (local o red compartida)
│   ├── csv_service.py          # Persistencia en CSV local
│   ├── concurrent_worker.py    # Pool de hilos para procesamiento por lotes
│   ├── memory_monitor.py       # Monitoreo de RAM durante el procesamiento
│   ├── google_drive_service.py # No activo, ver Notas de alcance
│   └── supabase_service.py     # No activo, ver Notas de alcance
├── ui/                     # Interfaz gráfica
│   ├── main_window.py
│   ├── data_tab.py
│   ├── network_credentials_dialog.py  # Autenticación para unidades de red compartidas
│   ├── drive_sync_tab.py       # No activo, ver Notas de alcance
│   └── ...
├── src/                    # Scripts de entrenamiento y datasets del modelo CRNN (no activo)
├── models/, models1/       # Pesos de modelos entrenados (CRNN, no activo)
├── data/                   # Datasets usados para entrenar el CRNN (no activo)
└── previews/                # Almacenamiento temporal de previsualizaciones OCR
```

## ⚠️ Notas de alcance y componentes no activos

Este repositorio conserva código de una etapa previa del proyecto que ya no forma parte del flujo activo de la aplicación. Se documenta aquí para que quede claro qué corre realmente al ejecutar `python app.py`:

- **Sincronización en la nube (Google Drive / Firebase / Supabase)**: el código existe (`services/google_drive_service.py`, `services/supabase_service.py`, `ui/drive_sync_tab.py`), pero está deshabilitado — las importaciones que lo activarían en `ui/main_window.py` están comentadas, y las dependencias correspondientes están comentadas en `requirements.txt`. La aplicación no se conecta a ningún servicio externo en su configuración actual.
- **Red neuronal CRNN propia**: `core/CRNN_inference.py` y todo `src/` (entrenamiento, dataset, modelos `.h5`) implementan un reconocedor de caracteres entrenado desde cero. Sin embargo, `services/ocr_service.py` tiene la carga de este modelo comentada; el reconocimiento de texto en producción usa **únicamente EasyOCR**, un motor preentrenado.
- **`requirements_distribuido.txt`**: describe las dependencias (Flask, Firebase) de una variante distribuida del sistema que tampoco está activa en el código actual.

## 🎓 Módulos Académicos

Ver [MODULOS.md](docs/MODULOS.md) — este documento aún describe la arquitectura distribuida con CRNN y necesita revisarse contra el alcance real listado arriba antes de usarse como evidencia final ante el comité.

## 📖 Guía Rápida de Uso

### Procesamiento de Contratos

1. **Seleccionar Directorio Raíz**
   - Click en "📁 Seleccionar directorio raíz"
   - Elegir la carpeta contenedora de calendarios (local o unidad de red compartida)

2. **Subir Contratos**
   - Click en "📎 Subir contrato(s)"
   - Seleccionar uno o más archivos PDF/PNG/JPG

3. **Procesar**
   - Seleccionar calendario (ej: 2024A)
   - Click en "🚀 Procesar Contrato(s)"
   - Los contratos se procesan en paralelo (varios hilos) hasta el límite de memoria disponible

4. **Ver Datos**
   - Ir a pestaña "📊 Ver/Editar Datos"
   - Revisar información extraída
   - Editar si es necesario

Ver [GUIA_USO.md](docs/GUIA_USO.md) para guía completa (nota: puede incluir pasos de sincronización con la nube que ya no aplican, ver aviso arriba).

## 🤝 Contribuciones

Este es un proyecto académico de titulación y, por el momento, 
no se aceptan contribuciones externas ni cambios en el código base 
por parte de terceros para mantener la integridad de la entrega institucional.
 Agradecemos su comprensión.

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 👥 Autores
- **Alumnos**: Niuska Isabel Gonzalez Rangel y Luis Diego Uribe Sandoval
- **Equipo de Desarrollo**: Proyecto Modular CUCEI 2025 - 2026 
- **Institución**: Universidad de Guadalajara - Centro Universitario de Ciencias Exactas e Ingenierías

## 📞 Soporte

Para reportar problemas o sugerencias:
- Abre un [Issue](https://github.com/Niuska0212/Redocnizer/issues)
- Contacta con el equipo de desarrollo

---

**Última actualización**: 21 de septiembre de 2026  
**Estado**: En desarrollo activo — versión local simplificada
