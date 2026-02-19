# 🏗️ Arquitectura del Sistema - REDOCNIZER

## 1. Diagrama de Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  PySide6 (Qt Framework)                                │  │
│  │  ├─ main_window.py (GUI principal)                     │  │
│  │  ├─ data_tab.py (Gestión de datos)                     │  │
│  │  ├─ drive_sync_tab.py (Sincronización)                 │  │
│  │  └─ calendar_config_dialog.py (Configuración)          │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               CAPA DE LÓGICA DE NEGOCIO                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Controllers                                           │  │
│  │  └─ contract_controller.py (Orquestación)             │  │
│  │                                                        │  │
│  │  Core (Visión Artificial)                             │  │
│  │  ├─ CRNN_inference.py (Red neuronal)                  │  │
│  │  ├─ document_extractor.py (Extracción)                │  │
│  │  ├─ preprocessing.py (Normalización)                  │  │
│  │  └─ segmentacion_dinamica.py (Segmentación)           │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                 CAPA DE SERVICIOS                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Procesamiento                                         │  │
│  │  ├─ ocr_service.py (OCR Híbrido)                      │  │
│  │  ├─ pdf_service.py (PDF → Imágenes)                   │  │
│  │  └─ file_service.py (Gestión de archivos)             │  │
│  │                                                        │  │
│  │  Datos                                                │  │
│  │  ├─ csv_service.py (Lectura/Escritura CSV)            │  │
│  │  └─ data_manager.py (Gestión de datos)                │  │
│  │                                                        │  │
│  │  Nube                                                 │  │
│  │  ├─ google_drive_service.py (Google Drive API)        │  │
│  │  ├─ firebase_service.py (Firebase Realtime DB)        │  │
│  │  └─ api_server.py (Servidor REST)                     │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              CAPA DE PERSISTENCIA                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SQLite Local (calendar_db.py)                         │  │
│  │  ├─ calendarios                                        │  │
│  │  ├─ contratos                                          │  │
│  │  └─ historial_cambios                                  │  │
│  │                                                        │  │
│  │  Firebase Realtime Database                           │  │
│  │  └─ Sincronización distribuida                         │  │
│  │                                                        │  │
│  │  Almacenamiento de Archivos                            │  │
│  │  ├─ Sistema de archivos local                          │  │
│  │  ├─ Google Drive (nube)                                │  │
│  │  └─ Red compartida (SMB/CIFS)                          │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Estructura de Directorios

```
redocnizer/
│
├── 📄 README.md                    # Documentación principal
├── 📄 REQUERIMIENTOS.md            # Especificaciones técnicas
├── 📄 requirements.txt             # Dependencias Python
├── 📄 app.py                       # Punto de entrada
├── 📋 .gitignore                   # Configuración Git
│
├── 📁 docs/                        # Documentación completa
│   ├── GUIA_USO.md                 # Guía de usuario
│   ├── MODULOS.md                  # Cumplimiento académico
│   ├── ARQUITECTURA.md             # Este archivo
│   └── README_DESARROLLADOR.md     # (Opcional)
│
├── 📁 ui/                          # Interfaz Gráfica
│   ├── main_window.py              # Ventana principal
│   ├── data_tab.py                 # Pestaña de datos
│   ├── drive_sync_tab.py           # Pestaña de sincronización
│   ├── calendar_config_dialog.py   # Diálogo de calendario
│   ├── calendar_db.py              # Base de datos de calendarios
│   ├── data_manager.py             # Gestor de datos
│   ├── history_manager.py          # Gestor de historial (undo/redo)
│   ├── file_watcher.py             # Observador de cambios en archivos
│   ├── edit_record_dialog.py       # Diálogo de edición (ya no en uso)
│   ├── image_preview_dialog.py     # Diálogo de vista previa
│   ├── network_credentials_dialog.py # Diálogo de credenciales de red
|   ├── splash_screen.py            # Ventana de presentacion 
│   ├── app_menu.py                 # Barra de menú
│   └── assets/                     # Imágenes y recursos
│       └── logo_redocnizer.png
│
├── 📁 controllers/                 # Lógica de Negocio
│   └── contract_controller.py      # Controlador principal
│
├── 📁 core/                        # Visión Artificial
│   ├── __init__.py
│   ├── CRNN_inference.py           # Inferencia de CRNN
│   ├── document_extractor.py       # Extracción de documentos
│   ├── preprocessing.py            # Preprocesamiento de imágenes
│   └── segmentacion_dinamica.py    # Segmentación automática
│
├── 📁 services/                    # Servicios
│   ├── ocr_service.py              # Servicio OCR Híbrido
│   ├── pdf_service.py              # Procesamiento de PDF
│   ├── csv_service.py              # Lectura/Escritura CSV
│   ├── file_service.py             # Gestión de archivos
│   ├── concurrent_worker.py        # Gestion de hilos
│   ├── data_manager.py             # Gestor de datos central
│   ├── google_drive_service.py     # Integración Google Drive
│   ├── api_server.py               # Servidor API REST
│   └── __pycache__/
│
├── 📁 models/                      # Modelos ML entrenados
│   ├── keras_cnn_lstm_v3.h5        # CRNN v3 base
│   ├── keras_cnn_lstm_v3_ctc.h5    # CRNN v3 con CTC
│   ├── keras_cnn_lstm_v4_ctc.h5    # CRNN v4 mejorado
│   ├── keras_cnn_model.h5          # CNN puro
│   └── model_best.weights.h5       # Pesos del mejor modelo
│
├── 📁 data/                        # Datos y datasets
│   ├── data/
│   │   ├── palabras.txt
│   │   ├── palabras_usadas.txt
│   │   ├── dataset/                # Dataset de entrenamiento
│   │   │   ├── 0/, 1/, 2/, ... 9/  # Imágenes de dígitos
│   │   │   ├── a_L/, A_U/, ...     # Imágenes de letras
│   │   │   └── [otros caracteres]/
│   │   ├── dataset_palabras/       # Dataset de palabras completas
│   │   ├── training_data/          # Datos de entrenamiento
│   │   └── testing_data/           # Datos de prueba
│   └── credentials.json            # Credenciales Google Drive
│
├── 📁 src/                         # Scripts adicionales
│   ├── ARQUITECTURA_MODELO_CRNN.md # Documentación de CRNN
│   ├── Documento_tecnica.md        # Documentación técnica
│   ├── entrenamiento.py            # Script de entrenamiento
│   ├── entrenamientoV2.py
│   ├── entrenamientoV3.py
│   ├── entrenamientoV4.py
│   ├── prediccion.py               # Script de predicción
│   ├── clasificador.py             # Clasificador
│   ├── preprocesamiento.py         # Preprocesamiento
│   ├── dataset_generador.py        # Generador de dataset
│   ├── reconocimiento_interfaz.py  # Interfaz de reconocimiento
│   └── config.yaml                 # Archivo de configuración
│
├── 📁 build/                       # Archivos de distribución
│   └── redocnizer/
│       ├── Analysis-00.toc
│       ├── PKG-00.pyz
│       ├── xref-redocnizer.html
│       └── localpycs/
│
├── 📁 previews/                    # Almacenamiento temporal
│   └── [imágenes de preview]
│
└── 📁 models1/                     # Evaluaciones de modelos
    ├── evaluacion_modelo_CNN_mejorado5.txt
    ├── evaluacion_modelo_CNN_mejorado6.txt
    └── evaluacion_modelo_CNN_mejorado7.txt
```

---

## 3. Flujo de Procesamiento de Contratos

### 3.1 Diagrama de Flujo

```
┌─────────────┐
│  Inicio     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ Seleccionar ruta raíz    │
│ y calendario             │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Subir archivo(s)         │
│ (PDF/PNG/JPG)            │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Click "Procesar"         │
└──────┬───────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ contract_controller.process_uploaded   │
│           _file()                      │
└──────┬─────────────────────────────────┘
       │
       ├─────────────────┬──────────────────────┐
       ▼                 ▼                      ▼
  ┌────────────┐  ┌──────────────┐  ┌──────────────┐
  │ PDF?       │  │ PNG/JPG?     │  │ Validación   │
  │ Convertir  │  │ Usar directo  │  │ de archivo   │
  │ a imágenes │  └──────────────┘  └──────────────┘
  └────┬───────┘
       │
       ▼
┌────────────────────────────────────────┐
│ core.preprocessing.preprocess_image()  │
│  - Escala: 32x128 píxeles              │
│  - Normalización: 0-1                  │
│  - Conversión a escala de grises       │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ core.segmentacion_dinamica.segment()   │
│  - Detectar líneas de texto            │
│  - Dividir en regiones                 │
│  - Paralelizar procesamiento           │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ services.ocr_service.ocr_hybrid()      │
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ 1. Tesseract OCR (Fast)          │  │
│ │    ├─ Extrae texto               │  │
│ │    └─ Calcula confianza          │  │
│ └──────────────────────────────────┘  │
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ 2. CRNN inference (Accurate)     │  │
│ │    ├─ Pasa por red neuronal      │  │
│ │    └─ Calcula confianza          │  │
│ └──────────────────────────────────┘  │
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ 3. Validación cruzada            │  │
│ │    └─ Selecciona resultado óptimo│  │
│ └──────────────────────────────────┘  │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ core.document_extractor.extract()      │
│  - Identificar campos clave            │
│  - Extraer: Código, Nombre, etc.      │
│  - Validar formato                     │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ services.csv_service.save_contract()   │
│  - Verificar integridad                │
│  - Guardar en CSV                      │
│  - Generar preview                     │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ firebase_service.sync_async()          │
│  - Subir datos a Firebase              │
│  - Mantener sincronización             │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ google_drive_service.upload()          │
│  - Subir a Google Drive                │
│  - Generar enlace compartido           │
└──────┬─────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Fin        │
└─────────────┘
```

### 3.2 Secuencia Temporal

```
Tiempo | Actividad                      | Duración
-------|--------------------------------|----------
T0     | Lectura de archivo             | 50ms
T50    | Conversión PDF → Imagen        | 120ms
T170   | Preprocesamiento               | 85ms
T255   | Segmentación                   | 75ms
T330   | OCR Tesseract                  | 150ms
T480   | OCR CRNN                       | 320ms
T800   | Extracción de campos           | 45ms
T845   | Validación                     | 30ms
T875   | Guardado CSV                   | 40ms
T915   | Sincronización Firebase        | 200ms (async)
T1115  | Upload Google Drive            | 300ms (async)
-------|--------------------------------|----------
Total  | ~1.1 segundos (procesamiento sincrónico)
       | ~1.4 segundos (con sincronización)
```

---

## 4. Componentes Clave

### 4.1 CRNN (Convolutional Recurrent Neural Network)

```python
class CRNN(Model):
    # Arquitectura detallada en core/CRNN_inference.py
    
    def __init__(self):
        # Convolutional Layers (7 capas)
        self.conv_layers = [
            Conv2D(32, (3,3)),   -> (batch, 30, 126, 32)
            MaxPool2D((2,2)),    -> (batch, 15, 63, 32)
            Conv2D(64, (3,3)),   -> (batch, 13, 61, 64)
            MaxPool2D((2,2)),    -> (batch, 6, 30, 64)
            Conv2D(128, (3,3)),  -> (batch, 4, 28, 128)
            Conv2D(128, (3,3)),  -> (batch, 2, 26, 128)
            MaxPool2D((1,2))     -> (batch, 2, 13, 128)
        ]
        
        # Reshape para RNN
        self.reshape = Reshape((26, 256))
        
        # Recurrent Layers
        self.lstm1 = Bidirectional(LSTM(256, return_sequences=True))
        self.lstm2 = Bidirectional(LSTM(256, return_sequences=True))
        
        # Output (CTC)
        self.dense = Dense(num_classes)
```

**Entrada:** Imagen 32x128x3  
**Salida:** Secuencia de caracteres (0-9, a-z, A-Z, etc.)

### 4.2 OCR Service (Híbrido)

```python
class OCRService:
    def __init__(self):
        self.tesseract = TesseractOCR()
        self.crnn = load_model('keras_cnn_lstm_v4_ctc.h5')
    
    def ocr_hybrid(self, image):
        # 1. Tesseract rápido
        text_t, conf_t = self.tesseract.extract(image)
        
        # 2. CRNN preciso
        text_c, conf_c = self.crnn.infer(image)
        
        # 3. Fusión inteligente
        if conf_t > 0.85:
            return text_t, conf_t, 'tesseract'
        elif conf_c > 0.85:
            return text_c, conf_c, 'crnn'
        else:
            # Validación cruzada
            distance = levenshtein(text_t, text_c)
            if distance / len(text_t) < 0.1:  # <10% diferencia
                scores = weight_results(conf_t, conf_c)
                return choose_best(scores), max(conf_t, conf_c), 'hybrid'
            else:
                # Conflicto: Preferir CRNN (más preciso para manual)
                return text_c, conf_c, 'crnn_priority'
```

### 4.3 Data Manager

```python
class DataManager:
    def __init__(self):
        self.data: pd.DataFrame = None
        self.csv_source: str = None
        self.history: HistoryManager = None
    
    # Operaciones
    def load_from_calendar_dir(calendar_dir: str) -> bool
    def save_to_csv(self) -> bool
    def get_dataframe(self) -> pd.DataFrame
    def add_contract(contract_data: dict) -> bool
    def update_contract(id: int, data: dict) -> bool
    def filter_by_calendar(calendar: str) -> pd.DataFrame
```

### 4.4 Firebase Service

```python
class FirebaseService:
    def __init__(self, config):
        self.db = initialize_realtime_db(config)
    
    async def sync_data_async(self, data: dict):
        """Sincronización no-bloqueante"""
        await self.db.child("contratos").set(data)
    
    def listen_updates(self, callback):
        """Escuchar cambios en tiempo real"""
        self.db.stream(callback, path="contratos")
    
    def get_sync_status(self) -> SyncStatus:
        """Estado de sincronización"""
        return {
            'connected': self.db.is_connected(),
            'last_sync': self.db.get_last_sync_time(),
            'pending': self.db.get_pending_changes()
        }
```

### 4.5 Contract Controller

```python
class ContractController:
    def __init__(self, root_dir: str, preview_dir: str):
        self.root_dir = root_dir
        self.preview_dir = preview_dir
        self.file_service = FileService(root_dir)
        self.ocr = OCRService()
        self.extractor = DocumentExtractor()
        self.firebase = FirebaseService(config)
        self.google_drive = GoogleDriveService(config)
    
    def process_uploaded_file(self, file_path: str, calendar: str) -> dict:
        """Procesar un archivo subido"""
        try:
            # 1. Convertir si es PDF
            images = self._prepare_images(file_path)
            
            # 2. Procesar cada imagen
            results = []
            for img in images:
                # Preprocesamiento
                processed = preprocess_image(img)
                
                # OCR
                text = self.ocr.ocr_hybrid(processed)
                
                # Extracción de campos
                data = self.extractor.extract(text)
                results.append(data)
            
            # 3. Guardar en CSV
            final_path = self.file_service.save_contract(calendar, results)
            
            # 4. Sincronizar
            asyncio.run(self.firebase.sync_data_async(results))
            self.google_drive.upload(final_path)
            
            return {'success': True, 'final_path': final_path}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

---

## 5. Patrones de Diseño Utilizados

### 5.1 MVC (Model-View-Controller)

```
Model (Services)
│
├─ csv_service.py (Datos)
├─ firebase_service.py (Datos distribuidos)
└─ data_manager.py (Lógica de negocio)
    │
    Controller (Business Logic)
    │
    └─ contract_controller.py
        │
        View (UI)
        │
        ├─ main_window.py
        ├─ data_tab.py
        └─ drive_sync_tab.py
```

### 5.2 Service Layer

```
UI
│
├─ OCRService
├─ PDFService
├─ GoogleDriveService
├─ FirebaseService
│
Core (Business Logic)
```

### 5.3 Repository Pattern

```
DataManager (Repository)
│
├─ load() -> DataFrame
├─ save() -> CSV
├─ get() -> Record
└─ filter() -> List[Record]
```

### 5.4 Factory Pattern

```
class ModelFactory:
    @staticmethod
    def create_model(version='v4'):
        if version == 'v3':
            return load_model('keras_cnn_lstm_v3_ctc.h5')
        elif version == 'v4':
            return load_model('keras_cnn_lstm_v4_ctc.h5')
```

### 5.5 Observer Pattern

```
DocumentChangedSignal
│
├─ Observador 1: Actualizar CSV
├─ Observador 2: Sincronizar Firebase
└─ Observador 3: Actualizar UI
```

---

## 6. Comunicación entre Componentes

```
┌─────────────────────┐
│   UI (PySide6)      │
└────────┬────────────┘
         │ Signals
         │ Slots
         ▼
┌─────────────────────┐      ┌──────────────┐
│ Main Window         │◄────►│ Data Manager │
├─────────────────────┤      └──────┬───────┘
│ - File Selection    │             │
│ - Preview           │             │ CSV
│ - Progress          │             │ Data
└────────┬────────────┘             ▼
         │                   ┌──────────────┐
         │                   │ CSV Service  │
         │                   └──────────────┘
         │
         ▼
┌─────────────────────┐
│ Contract Controller │
└────────┬────────────┘
         │
    ┌────┴────┬─────────┬──────────────┐
    │          │         │              │
    ▼          ▼         ▼              ▼
 ┌────────┐ ┌──────┐ ┌────────┐  ┌──────────┐
 │ OCR    │ │ PDF  │ │ Document│ │ File    │
 │Service │ │Svc   │ │Extract  │ │Service  │
 └────────┘ └──────┘ └────────┘  └──────────┘
    │
    └────┬──────────┬─────────┐
         │          │         │
    ┌────▼──┐  ┌─────▼──┐ ┌──▼──────┐
    │Tesseract│ │ CRNN  │ │ Validation
    └────────┘  └───────┘ └─────────┘
```

---

## 7. Tecnologías y Stack

### Backend
- **Lenguaje:** Python 3.8+
- **Framework Web:** FastAPI (opcional para API)
- **Async:** asyncio, concurrent.futures

### Frontend
- **Framework GUI:** PySide6 (Qt6 Python bindings)
- **Styling:** QSS (Qt Style Sheets)

### Machine Learning
- **Framework:** TensorFlow 2.10+
- **Modelos:** Keras Sequential
- **OCR:** Tesseract 5.0+, pytesseract

### Visión Artificial
- **OpenCV:** 4.5+
- **PIL/Pillow:** 8.0+
- **numpy:** 1.21+

### Base de Datos
- **Local:** SQLite 3.36+
- **Distribuida:** Firebase Realtime Database
- **Queries:** pandas, sqlalchemy (optional)

### Almacenamiento Nube
- **Google Drive:** google-cloud-storage, google-drive-api
- **Firebase:** firebase-admin

### Utilidades
- **CSV:** pandas 1.3+
- **PDF:** PyPDF2 3.0+
- **Versionado:** Semántico (X.Y.Z)
- **Empaquetado:** PyInstaller

---

## 8. Despliegue

### Desarrollo
```bash
python app.py
```

### Producción
```bash
pyinstaller redocnizer.spec
# Genera: redocnizer.exe (Windows)
```

### Distribución
```
redocnizer-1.0.0-setup.exe
├─ Instalador automático
├─ Configuración inicial
└─ Lanzador de escritorio
```

---

## 9. Consideraciones de Seguridad

### Autenticación
- OAuth 2.0 para Google Drive
- Tokens guardados encriptados
- Refresh automático

### Comunicación
- TLS 1.2+ para HTTPS
- WebSocket Secure (WSS)
- Validación de certificados

### Datos
- Encriptación de credenciales en `.env`
- Sanitización de entrada
- Validación de integridad (checksums)

---

**Arquitectura versión**: 5.0  
**Última actualización**: 16 de febrero de 2026

