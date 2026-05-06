# 📖 Guía de Uso - REDOCNIZER

## 1. Configuración Inicial

### 1.1 Instalación de Dependencias

Después de clonar el repositorio:

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.2 Configuración de Google Drive (Opcional)

Para sincronizar con Google Drive:

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un nuevo proyecto
3. Habilitar Google Drive API
4. Crear credenciales (OAuth 2.0 - Desktop)
5. Descargar JSON y guardar como `credentials.json` en la carpeta raíz

### 1.3 Configuración de Firebase (Opcional)

Para sincronización en tiempo real:

1. Crear proyecto en [Firebase Console](https://console.firebase.google.com/)
2. Copiar datos de conexión
3. Guardar en `.env`:

```env
FIREBASE_URL=https://tu-proyecto.firebaseio.com
FIREBASE_KEY=tu-clave-secreta
```

---

## 2. Interfaz Principal

### 2.1 Descripción de Elementos

```
┌─────────────────────────────────────────────────────────────────┐
│ REDOCNIZER - Gestión de Contratos CUCEI                        │
├─────────────────────────────────────────────────────────────────┤
│ [📄 Procesar Contratos] [📊 Ver/Editar Datos] [☁️ Nube]        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Gestión y Búsqueda                                              │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ 🔍 Buscar contratos por nombre, ID o fecha...            │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ Configuración                                                   │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Directorio raíz: [________________] [📁 Seleccionar]     │  │
│ │ Calendario: [2024A ▼] [Abrir Excel] [Cargar] [Carpeta]  │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ Archivos a Procesar                                             │
│ ┌─────────────────┬───────────────────────────────────────┐    │
│ │ Vista previa    │ [📎 Subir] [🗑️ Limpiar] [➖ Eliminar] │   │
│ │ del documento   │                                       │    │
│ │                 │ 📄 archivo1.pdf                      │   │
│ │                 │ 📄 archivo2.pdf                      │   │
│ └─────────────────┴───────────────────────────────────────┘    │
│                                                                 │
│ Progreso                                                        │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ ████████░░░░░░░░░░ 50% [Resultados]                      │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│             [🚀 Procesar Contratos]                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Flujo de Procesamiento Paso a Paso

### Paso 1: Seleccionar Directorio Raíz

1. Click en botón **"📁 Seleccionar directorio raíz"**
2. Se abre un explorador de archivos
3. Navega a la carpeta principal que contiene tus calendarios

**Estructura esperada:**
```
Mi Carpeta Raíz/
├── 2024A/
│   ├── contratos.csv
│   └── documentos/
├── 2024B/
│   ├── contratos.csv
│   └── documentos/
└── 2025A/
    ├── contratos.csv
    └── documentos/
```

**Nota**: Si es una ruta de red (\\servidor\compartido), se solicitarán credenciales.

### Paso 2: Seleccionar Calendario

1. En el dropdown **"Calendario"**, elige el período (ej: 2024A)
2. Las opciones disponibles se cargan desde la BD local
3. Si no ves tu calendario, puede ser que:
   - No existe el archivo `contratos.csv` en esa carpeta
   - La carpeta no está dentro del directorio raíz seleccionado

**Botones asociados:**
- **📊 Abrir Excel**: Abre el CSV del calendario en Excel sin cargar datos
- **📥 Cargar datos**: Carga el CSV en la vista de edición de datos
- **Abrir carpeta**: Abre la carpeta del calendario en el explorador

### Paso 3: Cargar Documentos

1. Click en **"📎 Subir contrato(s)"**
2. Selecciona uno o múltiples archivos (Ctrl+Click para múltiples)
3. Formatos soportados: `.pdf`, `.png`, `.jpg`, `.jpeg`
4. Se mostrarán en la lista "Archivos a Procesar"

**Operaciones:**
- Selecciona un archivo para ver su preview en la izquierda
- Click en **"➖ Eliminar seleccionado"** para quitar un archivo individual
- Click en **"🗑️ Limpiar"** para eliminar todos

### Paso 4: Procesamiento

1. Asegúrate de que:
   - ✓ Hay directorio raíz seleccionado
   - ✓ Hay archivos subidos
   - ✓ Hay calendario elegido

2. Click en **"🚀 Procesar Contratos"**

3. Se mostrarán en tiempo real:
   - Barra de progreso
   - Estado de cada archivo (✅ exitoso / ❌ error)

4. **Importante**: Mientras se procesa, el botón estará **bloqueado** para evitar procesamiento duplicado

### Paso 5: Revisar Resultados

1. Los datos se cargan automáticamente en la pestaña **"📊 Ver/Editar Datos"**
2. Se muestra un resumen del procesamiento:
   - Total de archivos
   - Archivos exitosos
   - Archivos fallidos

3. Si todos fueron exitosos, podés ir a ver/editar los datos

---

## 4. Pestaña: Ver/Editar Datos

### 4.1 Estructura

```
┌─────────────────────────────────────────────┐
│ 📊 Ver/Editar Datos                         │
├─────────────────────────────────────────────┤
│ 🔍 [Buscar por nombre, código...] [🔄 Recargar] │
│ ┌─────────────────────────────────────────┐ │
│ │ CODIGO │ NOMBRE │ PATERNO │ MATERNO │ .. │ │
│ ├─────────────────────────────────────────┤ │
│ │ 001    │ Juan  │ Pérez  │ López   │ 📷 │ │
│ │ 002    │ María │ García │ Martín  │ 📷 │ │
│ └─────────────────────────────────────────┘ │
│ [📥 Guardar Todo]                           │
└─────────────────────────────────────────────┘
```

### 4.2 Operaciones

#### Edición Inline
1. Haz double-click en una celda para editar
2. Escribe el nuevo valor
3. Presiona **Enter** para guardar o **Esc** para cancelar

#### Búsqueda y Filtrado
1. Escribe en la barra de búsqueda (🔍)
2. Filtra por: Código, Nombre, Paterno, Materno
3. La tabla se actualiza en tiempo real

#### Vista Previa de Imagen
1. Click en el ícono 📷 en la columna "Preview"
2. Se abre un diálogo con la imagen del documento
3. Puedes guardarla con botón derecho del ratón

#### Guardado
1. Los cambios se marcan con asterisco (*)
2. El historial de cambios se mantiene automáticamente
3. Click en **"📥 Guardar Todo"** para guardar al CSV
4. O cambia a otra pestaña y selecciona "Guardar"

#### Deshacer/Rehacer
- **Ctrl+Z**: Deshacer último cambio
- **Ctrl+Y**: Rehacer cambio deshecho

---

## 5. Pestaña: Sincronización Nube

### 5.1 Google Drive

#### Conexión Inicial
1. Click en **"Conectar con Google Drive"**
2. Se abre navegador con login de Google
3. Autoriza acceso a tu Google Drive
4. Token se guardarán automáticamente

#### Sincronización Manual
1. Click en **"Sincronizar Ahora"**
2. Sube los datos al Google Drive
3. Se sincroniza en carpeta: `/REDOCNIZER/`

#### Sincronización Automática
1. Marca checkbox **"Sincronizar automáticamente"**
2. Configura intervalo (cada 5/10/30 minutos)
3. Los cambios se suben automáticamente

### 5.2 Firebase

#### Conectar (si está configurado)
1. Proporciona URL y clave en `.env`
2. Sistema se conecta automáticamente
3. Ver estado de conexión en indicador

#### Base de Datos en Tiempo Real
- Cambios se replican automáticamente
- Múltiples usuarios pueden trabajar simultáneamente
- Resolución de conflictos automática

---

## 6. Buscar y Filtrar

### 6.1 Barra de Búsqueda Global

Ubicada en **"Gestión y Búsqueda"** (pestaña Procesar):

```
🔍 Buscar contratos por nombre, ID o fecha...
```

Busca en:
- Nombre de archivo
- Código de contrato
- Fecha de procesamiento

### 6.2 Filtrado en Tabla de Datos

Busca en cualquier columna visible en tiempo real.

---

## 7. Resolución de Problemas

### Problema: "Tesseract no encontrado"

**Solución:**
```python
# Editar: services/ocr_service.py
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Problema: "No se puede acceder a la red compartida"

**Solución:**
1. Usa ruta UNC: `\\servidor\compartido`
2. Proporciona credenciales cuando se pida
3. Asegúrate de tener permisos de lectura/escritura

### Problema: "Error al procesar PDF"

**Causas posibles:**
- PDF protegido con contraseña
- Formato PDF corrupto
- Resolución muy baja (< 300 DPI)

**Solución:**
- Intenta con otro PDF
- Convierte a imagen primera con herramienta externa
- Verifica integridad del archivo

### Problema: "Modelo ML no encontrado"

**Solución:**
1. Verifica que exista carpeta `models/`
2. Descarga modelos desde: [enlace a repositorio]
3. Coloca archivos `.h5` en `models/`

### Problema: "Google Drive no sincroniza"

**Solución:**
1. Verifica que exista `credentials.json`
2. Revoca permisos e intenta nuevamente
3. Verifica conexión a internet
4. Ver logs en carpeta `logs/`

---

## 8. Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| **Ctrl+O** | Seleccionar directorio raíz |
| **Ctrl+U** | Subir archivos |
| **Ctrl+P** | Procesar contratos |
| **Ctrl+S** | Guardar cambios en datos |
| **Ctrl+Z** | Deshacer |
| **Ctrl+Y** | Rehacer |
| **Ctrl+F** | Buscar |
| **Ctrl+Q** | Salir de la aplicación |
| **F5** | Recargar datos |

---

## 9. Configuración Avanzada

### 9.1 Variables de Entorno

Crear archivo `.env` en raíz del proyecto:

```env
# Google Drive
GOOGLE_DRIVE_CREDENTIALS=credentials.json

# Firebase
FIREBASE_URL=https://tu-proyecto.firebaseio.com
FIREBASE_KEY=tu-clave-secreta

# Tesseract (si no está en path)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# OCR
OCR_MIN_CONFIDENCE=0.8
OCR_LANG=spa+eng

# Procesamiento
MAX_WORKERS=4
BATCH_SIZE=16
PREVIEW_DPI=72
```

### 9.2 Agregar Calendarios

Manualmente en bases de datos:

```bash
# Abrir la interfaz de calendario
python -m ui.calendar_config_dialog
```

O crear carpetas directamente:
```
Directorio Raíz/
└── 2026A/
    ├── contratos.csv
    └── documentos/
```

---

## 10. Mejor Práctica y Consejos

### ✅ Mejores Prácticas

1. **Antes de procesar:**
   - Verifica que los PDFs tengan buena calidad
   - Usa 300 DPI mínimo
   - Nombres de archivo claros

2. **Procesamiento:**
   - Procesa pocos archivos primero (< 10)
   - Verifica que la extracción sea buena
   - Luego procesa lotes grandes

3. **Datos:**
   - Revisa manualmente los primeros registros
   - Corrige valores inconsistentes
   - Mantén formato consistent (mayúsculas, acentos)

4. **Sincronización:**
   - Habilita auto-sync si trabajas en equipo
   - Revisa conflictos regularmente
   - Haz backup semanal

### ⏱️ Rendimiento

- Procesa máximo 50 documentos por lote
- Espera 1 minuto entre lotes
- Verifica disponibilidad de memoria (mínimo 500MB libre)

### 🔒 Seguridad

- Nunca compartas `credentials.json`
- Revoca accesos periódicamente
- Usa VPN para redes no seguras
- Cambios sensibles guardan en log

---

## 11. Obtener Ayuda

### Logs

Ver archivo de logs:
```bash
# Windows
type logs/redocnizer.log

# Linux/macOS
cat logs/redocnizer.log
```

### Contacto

- **Email**: niuska.gonzalez5462@alumnos.udg.mx o luis.uribe0840@alumnos.udg.mx
- **Issues**: https://github.com/Niuska0212/Redocnizer/issues


---

**Versión**: 2.3.2
**Última actualización**: 24 de febrero de 2026

