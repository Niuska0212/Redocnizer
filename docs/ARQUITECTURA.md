# Arquitectura del Sistema - REDOCNIZER

## 1. Alcance

REDOCNIZER es una aplicación de escritorio para Windows que procesa contratos académicos sin servidor de aplicación y sin sincronización obligatoria con servicios externos. Su persistencia principal se realiza mediante CSV y archivos PDF almacenados en el sistema local o en una carpeta compartida de red.

## 2. Capas del sistema

```text
Interfaz PySide6
    |
    v
MainWindow -> ContractController
    |
    +--> OCRService -> document_extractor -> preprocessing/OpenCV -> EasyOCR
    +--> PDFService -> PyMuPDF/Pillow
    +--> FileService -> expedientes locales o rutas UNC
    +--> CSVService -> CALENDARIOS/*.csv
    +--> ConcurrentOCRWorker -> QThreadPool + monitor de memoria
```

### Presentación

La carpeta `ui/` contiene la ventana principal, las pestañas de procesamiento y datos, los diálogos, el menú, la vista previa y la gestión de credenciales para recursos de red. `app.py` crea la aplicación Qt, muestra la pantalla de carga y abre `MainWindow`.

### Control

`controllers/contract_controller.py` coordina el procesamiento individual y por lotes. Valida el tipo de archivo, obtiene la imagen para OCR, calcula el calendario, guarda el expediente y actualiza el CSV correspondiente.

### Núcleo de visión

`core/document_extractor.py` y `core/preprocessing.py` preparan las regiones de interés y ejecutan el OCR activo mediante EasyOCR. `core/segmentacion_dinamica.py` contiene utilidades relacionadas con segmentación. `core/CRNN_inference.py` se conserva como componente histórico y no se carga desde `services/ocr_service.py`.

### Servicios

- `ocr_service.py`: fachada del extractor OCR.
- `pdf_service.py`: convierte la primera página de un PDF a JPG y convierte imágenes a PDF.
- `file_service.py`: crea carpetas, limpia nombres, calcula calendarios UDG y copia contratos.
- `csv_service.py`: crea o actualiza `CALENDARIOS/<calendario>.csv` y evita duplicados por `NUM`.
- `concurrent_worker.py`: procesa lotes usando `QThreadPool`.
- `memory_monitor.py`: observa el consumo de memoria para evitar saturar el equipo.

## 3. Flujo de procesamiento

1. El usuario selecciona el directorio raíz de los expedientes.
2. Selecciona uno o varios archivos PDF, PNG, JPG o JPEG.
3. El controlador convierte un PDF a imagen usando la primera página; las imágenes se usan directamente.
4. El preprocesamiento prepara la imagen y EasyOCR extrae los campos del contrato.
5. La fecha `DESDE` determina el ciclo académico: enero-junio corresponde a `A` y julio-diciembre a `B`.
6. `FileService` genera una ruta con la forma siguiente:

```text
RAIZ/
└── PATERNO MATERNO NOMBRES CODIGO/
    └── 000000 DOC BASICOS/
        └── 06 NOMBRAMIENTOS/
            └── NUM CALENDARIO.pdf
```

7. Los datos extraídos se agregan o actualizan en `CALENDARIOS/<calendario>.csv`.
8. La interfaz muestra el progreso, los errores y las vistas previas generadas.

## 4. Persistencia local

La aplicación no utiliza SQLite como almacenamiento principal. Los calendarios son archivos CSV codificados en UTF-8 con BOM para facilitar su apertura en Excel. La carpeta `CALENDARIOS/` pertenece al proyecto y contiene archivos como `2024A.csv`, `2024B.csv` y `None.csv`.

Los documentos finales se guardan en el directorio raíz seleccionado por el usuario. Las vistas previas temporales se guardan en `previews/`.

## 5. Procesamiento concurrente y memoria

Los lotes se envían a un `QThreadPool` mediante `ConcurrentOCRWorker`. Cada archivo produce un resultado exitoso o un error independiente. El monitor de memoria permite limitar el trabajo concurrente en equipos con recursos reducidos. La interfaz permanece disponible para mostrar el avance y los resultados.

## 6. Red compartida

`FileService` admite rutas locales y rutas UNC, por ejemplo `//servidor/recurso`. `NetworkCredentialsDialog` solicita credenciales cuando el acceso al recurso compartido lo requiere. Esta capacidad representa almacenamiento de archivos en una red institucional, no sincronización con la nube.

## 7. Componentes heredados

`services/google_drive_service.py`, `services/supabase_service.py`, `ui/drive_sync_tab.py` y el código CRNN se conservan por compatibilidad histórica o futura, pero sus importaciones y llamadas están deshabilitadas en la ventana principal. No deben describirse como dependencias del flujo activo.
