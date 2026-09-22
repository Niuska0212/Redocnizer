# Requerimientos Técnicos - REDOCNIZER

## 1. Requerimientos funcionales

### Documentos y OCR

- **RF-001**: cargar uno o varios archivos PDF, PNG, JPG o JPEG.
- **RF-002**: convertir la primera página de un PDF en una imagen para OCR.
- **RF-003**: extraer campos de contratos mediante EasyOCR local.
- **RF-004**: aplicar preprocesamiento y segmentación de imágenes antes del reconocimiento.
- **RF-005**: generar vistas previas temporales del procesamiento.

### Datos y calendarios

- **RF-006**: guardar la información extraída en CSV por calendario.
- **RF-007**: actualizar una fila existente cuando coincida el número `NUM`.
- **RF-008**: permitir revisar, buscar y editar los datos desde la interfaz.
- **RF-009**: calcular el calendario UDG a partir de la fecha `DESDE`.
- **RF-010**: conservar el calendario seleccionado cuando la fecha no pueda interpretarse.

### Expedientes

- **RF-011**: crear carpetas de expediente a partir del nombre, apellidos y código.
- **RF-012**: guardar el contrato final con el formato `NUM CALENDARIO.pdf`.
- **RF-013**: trabajar con almacenamiento local o rutas UNC de red compartida.

### Interfaz y lotes

- **RF-014**: mostrar una interfaz de escritorio mediante PySide6.
- **RF-015**: procesar varios documentos con una cola de trabajo concurrente.
- **RF-016**: mostrar progreso y errores individuales por archivo.
- **RF-017**: permitir limpiar las vistas previas temporales.

## 2. Requerimientos no funcionales

- **RNF-001**: el procesamiento normal debe ejecutarse localmente.
- **RNF-002**: la interfaz no debe bloquearse mientras se procesa un lote.
- **RNF-003**: el sistema debe controlar el uso de memoria durante el OCR.
- **RNF-004**: los errores de un archivo no deben impedir informar el resultado de los demás archivos.
- **RNF-005**: los CSV deben guardarse con codificación compatible con Excel.
- **RNF-006**: los nombres de archivos y carpetas deben limpiarse para evitar caracteres no válidos en Windows.
- **RNF-007**: la aplicación debe funcionar en Windows con almacenamiento NTFS o recursos compartidos accesibles.
- **RNF-008**: el sistema debe operar sin una cuenta de Google, Firebase o Supabase.

## 3. Stack tecnológico activo

| Área | Tecnología |
|---|---|
| Lenguaje | Python 3.10 o superior compatible |
| Interfaz | PySide6 |
| OCR | EasyOCR |
| Imágenes | OpenCV, Pillow, NumPy |
| PDF | PyMuPDF, PyPDF2 y pdf2image disponibles |
| Datos | pandas y CSV |
| Concurrencia | QThreadPool, QRunnable y QThread |
| Recursos | psutil |
| Distribución | PyInstaller |

## 4. Formatos de entrada y salida

### Entrada

- PDF
- PNG
- JPG
- JPEG

### Salida

- `CALENDARIOS/<calendario>.csv`
- expedientes PDF en la raíz seleccionada
- imágenes temporales en `previews/`

## 5. Seguridad y datos

La aplicación no envía contratos ni CSV a servicios externos en su configuración actual. La protección de los datos depende de los permisos del sistema de archivos y de la red compartida utilizada. Las credenciales de red deben manejarse de acuerdo con las políticas institucionales y no deben incluirse en el repositorio.

## 6. Componentes no activos

El repositorio conserva componentes de versiones anteriores, pero no son requisitos del flujo productivo actual:

- Google Drive
- Firebase
- Supabase
- sincronización automática en la nube
- servidor REST
- modelo CRNN propio como reconocedor activo

Estos componentes solo deben documentarse como legado o como posibles líneas futuras, no como funcionalidades disponibles en la ejecución normal de `app.py`.

## 7. Verificación recomendada

La validación del sistema debe cubrir:

1. procesamiento de un PDF válido;
2. procesamiento de una imagen PNG o JPG;
3. creación y actualización de un CSV;
4. cálculo de calendarios `A` y `B`;
5. guardado en una ruta local;
6. guardado en una ruta UNC accesible;
7. manejo de archivos inválidos o errores de OCR;
8. procesamiento de un lote sin bloquear la interfaz.
