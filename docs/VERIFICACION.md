# Verificación del Proyecto - REDOCNIZER

## 1. Estado de componentes activos

| Componente | Estado | Evidencia |
|---|---|---|
| Aplicación de escritorio | Activo | `app.py` y `ui/main_window.py` |
| Interfaz PySide6 | Activo | Widgets, pestañas y diálogos en `ui/` |
| OCR local | Activo | EasyOCR en `core/document_extractor.py` |
| Procesamiento PDF | Activo | PyMuPDF en `services/pdf_service.py` |
| Persistencia CSV | Activo | `services/csv_service.py` y `CALENDARIOS/` |
| Procesamiento concurrente | Activo | `services/concurrent_worker.py` |
| Monitor de memoria | Activo | `services/memory_monitor.py` |
| Rutas UNC | Activo | `services/file_service.py` y `ui/network_credentials_dialog.py` |
| Google Drive/Firebase/Supabase | No activo | Importaciones y llamadas deshabilitadas |
| CRNN propio | No activo en producción | Código conservado como legado |

## 2. Verificación automática disponible

Ejecuta desde la raíz del proyecto:

```powershell
python test_memory_monitor.py
```

Este script valida el monitor de memoria, la información del proceso, el cálculo de trabajadores recomendados, los estados de recursos y las decisiones de procesamiento.

También se puede comprobar la sintaxis de los módulos con:

```powershell
python -m compileall app.py controllers core services ui
```

## 3. Pruebas funcionales recomendadas

### Inicio

1. Ejecutar `python app.py`.
2. Confirmar que aparece la pantalla de carga.
3. Confirmar que abre la ventana principal.

### OCR y documentos

1. Seleccionar un PDF válido.
2. Procesar una imagen PNG o JPG.
3. Confirmar que el PDF se convierte a imagen para OCR.
4. Revisar los campos extraídos y la vista previa.

### Calendarios y CSV

1. Procesar un contrato con `DESDE` entre enero y junio.
2. Confirmar que se asigna un calendario `AAAAA`.
3. Procesar un contrato con `DESDE` entre julio y diciembre.
4. Confirmar que se asigna un calendario `AAAAB`.
5. Abrir el CSV creado en `CALENDARIOS/`.
6. Reprocesar el mismo `NUM` y confirmar que no se duplica la fila.

### Expedientes

1. Usar una ruta local con permisos de escritura.
2. Confirmar la creación de `000000 DOC BASICOS/06 NOMBRAMIENTOS`.
3. Confirmar el nombre final `NUM CALENDARIO.pdf`.
4. Repetir con una ruta UNC accesible si la infraestructura está disponible.

### Concurrencia y memoria

1. Seleccionar varios contratos.
2. Iniciar el procesamiento por lote.
3. Confirmar que la interfaz sigue respondiendo.
4. Confirmar que la barra de progreso se actualiza.
5. Confirmar que los errores individuales se informan sin detener todo el lote.
6. Ejecutar `python test_memory_monitor.py` y registrar el resultado.

## 4. Criterios de aceptación

- La aplicación inicia sin requerir servicios cloud.
- Los formatos PDF, PNG, JPG y JPEG se aceptan correctamente.
- EasyOCR produce resultados o informa un error legible.
- Los datos se guardan en el CSV del calendario correspondiente.
- Los archivos se organizan en la ruta seleccionada.
- El procesamiento de lotes no bloquea la interfaz.
- El consumo de memoria se muestra o controla durante el procesamiento.

## 5. Nota sobre resultados

Los resultados de precisión, tiempos y consumo deben medirse con documentos reales representativos. No deben presentarse cifras históricas de CRNN, Tesseract, Firebase o Google Drive como resultados de la versión local actual.
