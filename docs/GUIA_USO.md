# Guía de Uso - REDOCNIZER

## 1. Instalación

REDOCNIZER está orientado a Windows y requiere Python 3.10 o una versión compatible con las dependencias del proyecto.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La primera instalación de EasyOCR puede requerir conexión para descargar sus modelos. El procesamiento normal de contratos es local.

## 2. Preparación de carpetas

Selecciona una carpeta raíz donde la aplicación pueda crear los expedientes. El sistema genera automáticamente la siguiente estructura:

```text
Raiz de expedientes/
└── APELLIDO PATERNO APELLIDO MATERNO NOMBRES CODIGO/
    └── 000000 DOC BASICOS/
        └── 06 NOMBRAMIENTOS/
```

Los CSV de calendarios se guardan en la carpeta `CALENDARIOS/` del proyecto, no dentro de la raíz de expedientes.

## 3. Procesamiento de contratos

1. Abre REDOCNIZER con `python app.py`.
2. Selecciona el directorio raíz mediante **Seleccionar directorio raíz**.
3. Elige el calendario disponible.
4. Pulsa **Subir contrato(s)** y selecciona archivos PDF, PNG, JPG o JPEG.
5. Revisa la vista previa del archivo seleccionado.
6. Pulsa **Procesar Contrato(s)**.
7. Espera a que finalice la barra de progreso.
8. Revisa los resultados en la pestaña de datos.

Para los PDF se procesa la primera página. Las imágenes se convierten a PDF antes de guardarse como expediente.

## 4. Datos y CSV

La pestaña de datos permite cargar el CSV del calendario, buscar información, editar celdas y guardar cambios. Al procesar un contrato, el sistema reemplaza la fila anterior cuando encuentra el mismo valor en `NUM`.

Los campos dependen de la información identificada por el OCR. Entre los campos utilizados por el flujo se encuentran `NUM`, `CODIGO`, `PATERNO`, `MATERNO`, `NOMBRES`, `DESDE` y `CALENDARIO_CONTRATO`.

## 5. Cálculo del calendario

La fecha `DESDE` se interpreta con el formato `DD/MM/AAAA`:

- enero a junio: `AAAA` + `A`, por ejemplo `2024A`
- julio a diciembre: `AAAA` + `B`, por ejemplo `2024B`

Si la fecha no puede interpretarse, se utiliza el calendario seleccionado manualmente.

## 6. Rutas de red compartida

También se puede seleccionar una ruta UNC, como `//servidor/recurso/expedientes`. El equipo debe tener conectividad y permisos de escritura. Si Windows solicita autenticación, utiliza el diálogo de credenciales de red.

La red compartida solo se utiliza para guardar archivos. Los datos CSV continúan almacenándose en `CALENDARIOS/` dentro del proyecto.

## 7. Vistas previas y limpieza

Las imágenes temporales de OCR se guardan en `previews/`. Desde el menú de la aplicación se pueden eliminar las vistas previas para liberar espacio. Los expedientes PDF y los CSV no se eliminan mediante esa opción.

## 8. Errores frecuentes

### No se puede acceder a la carpeta

Comprueba que la ruta exista, que el recurso de red esté conectado y que la cuenta tenga permisos de lectura y escritura.

### El OCR no reconoce correctamente el contrato

Usa una imagen nítida, con buena iluminación y texto legible. Revisa y corrige los campos en la pestaña de datos después del procesamiento.

### No se genera el calendario esperado

Verifica que el campo `DESDE` tenga el formato `DD/MM/AAAA`. Si no se puede interpretar, selecciona manualmente el calendario correcto.

### El procesamiento consume demasiada memoria

Procesa lotes más pequeños, cierra otras aplicaciones y deja activo el monitor de memoria. El número de trabajadores se controla para evitar saturar el equipo.

## 9. Alcance actual

La aplicación funciona de forma local. Google Drive, Firebase y Supabase no se conectan durante el flujo actual, aunque existen archivos heredados relacionados con esas integraciones.
