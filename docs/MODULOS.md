# Módulos Académicos - REDOCNIZER

## Resumen

La versión actual de REDOCNIZER es una aplicación de escritorio local para la gestión de contratos académicos. Su aporte se concentra en la modularidad del software, la automatización mediante OCR, el procesamiento concurrente y la organización estructurada de información en archivos CSV.

El repositorio conserva componentes de una etapa anterior con servicios cloud y un modelo CRNN propio. Esos componentes no forman parte del flujo ejecutado por `app.py`.

## Módulo 2: Gestión de las Tecnologías de la Información

### Organización del sistema

El proyecto separa sus responsabilidades en cuatro grupos:

- `ui/`: interfaz y experiencia de usuario con PySide6.
- `controllers/`: coordinación del procesamiento de contratos.
- `core/`: preprocesamiento, segmentación y extracción OCR.
- `services/`: PDF, OCR, archivos, CSV, concurrencia y monitoreo de memoria.

Esta separación facilita el mantenimiento, las pruebas y la sustitución de componentes sin mezclar la lógica de presentación con la persistencia.

### Gestión de información

Los datos extraídos se almacenan en CSV dentro de `CALENDARIOS/`. El servicio de CSV elimina una fila anterior cuando encuentra el mismo número de contrato `NUM`, evitando duplicados durante el reprocesamiento.

Los expedientes se guardan con una estructura normalizada por profesor, código y tipo documental. Los nombres se limpian para evitar caracteres no válidos en Windows.

### Tecnologías activas

- Python
- PySide6
- EasyOCR
- OpenCV
- PyMuPDF
- Pillow
- pandas
- NumPy
- psutil

## Módulo 3: Sistemas Robustos y Paralelos

### Procesamiento concurrente

Los lotes se procesan con `QThreadPool`, `QRunnable` y `QThread`. Cada archivo se maneja de forma independiente, por lo que un error de OCR o de almacenamiento se informa sin ocultar los resultados de los demás documentos.

### Control de recursos

`MemoryMonitor` consulta el uso de RAM y CPU. `ConcurrentOCRWorker` utiliza esa información para ajustar el trabajo concurrente y evitar que el equipo se sature. La interfaz recibe el estado de los recursos mediante señales Qt y puede mostrar el avance sin bloquearse.

### Almacenamiento local y red

La aplicación puede guardar los expedientes en una carpeta local o en una ruta UNC, por ejemplo `//servidor/recurso`. La red compartida es un mecanismo de almacenamiento institucional; no constituye una arquitectura cloud ni una base de datos distribuida.

### Robustez

El flujo incluye validación de extensiones, conversión controlada de PDF, limpieza de recursos temporales, valores de respaldo para campos faltantes, captura de errores por archivo y actualización segura del CSV.

## Módulo 4: Cómputo Flexible y visión artificial

### OCR activo

El reconocimiento productivo utiliza EasyOCR. Antes del reconocimiento, el pipeline aplica operaciones de OpenCV y prepara regiones de interés para mejorar la lectura de los campos del contrato.

El módulo `core/CRNN_inference.py` y los modelos de entrenamiento se conservan como material histórico, pero no se cargan desde `OCRService` durante el funcionamiento normal.

### Extracción de información

El extractor identifica campos como:

- número de contrato (`NUM`)
- código (`CODIGO`)
- nombres y apellidos
- fecha inicial (`DESDE`)

La fecha detectada se utiliza para calcular el ciclo académico UDG: enero a junio produce un calendario `A` y julio a diciembre produce un calendario `B`.

### Límites documentados

La precisión del OCR depende de la calidad, resolución, orientación y legibilidad del documento. La aplicación permite revisar y corregir los datos extraídos antes de utilizar el CSV como registro final.

## Matriz de correspondencia

| Capacidad | Implementación actual |
|---|---|
| Interfaz gráfica | PySide6 en `ui/` |
| Control del flujo | `ContractController` |
| Reconocimiento | EasyOCR en `core/document_extractor.py` |
| Conversión PDF | PyMuPDF en `services/pdf_service.py` |
| Persistencia | CSV mediante `services/csv_service.py` |
| Expedientes | `FileService`, local o UNC |
| Paralelismo | `ConcurrentOCRWorker` y `QThreadPool` |
| Recursos | `MemoryMonitor` y widget de memoria |

## Componentes fuera del alcance activo

No deben presentarse como funcionalidades actuales:

- Google Drive
- Firebase
- Supabase
- sincronización automática
- servidor REST
- SQLite como almacenamiento principal
- CRNN como reconocedor productivo
