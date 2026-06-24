# ANEXO B: Guía de Instalación y Configuración

## 1. Requisitos del Sistema

### 1.1 Hardware Mínimo

| Componente | Mínimo | Recomendado |
|-----------|--------|------------|
| **CPU** | Intel Core i3 (2 GHz) | Intel Core i5/i7 (2.4+ GHz) |
| **RAM** | 4 GB | 8 GB |
| **Almacenamiento** | 2 GB libres | 5 GB libres |
| **Pantalla** | 1024×768 | 1920×1080 |
| **GPU** | No requerida | NVIDIA CUDA 11.0+ (opcional) |

### 1.2 Software Requerido

**Sistema Operativo**:
- Windows 7 SP1 o superior (recomendado Windows 10/11)
- Linux (Ubuntu 18.04+)
- macOS 10.14+

**Dependencias Externas**:
- Tesseract OCR 5.0+
- Python 3.8+ (para desarrollo)

---

## 2. Instalación en Windows (Usuario Final)

### 2.1 Instalación Automática (Recomendado)

#### Paso 1: Descargar Instalador
```
Descargar: redocnizer-1.0.0-setup.exe
Desde: https://github.com/CUCEI/redocnizer/releases
Tamaño: ~150 MB
```

#### Paso 2: Ejecutar Instalador
1. Doble clic en `redocnizer-1.0.0-setup.exe`
2. Aceptar licencia (GNU GPL v3)
3. Elegir carpeta destino (recomendado: `C:\Program Files\REDOCNIZER`)
4. Crear acceso directo en escritorio (opcional)
5. Esperar a que finalice (2-5 minutos)

#### Paso 3: Ejecutar la Aplicación
- Doble clic en acceso directo "REDOCNIZER"
- O: `Start → Todos los programas → REDOCNIZER`
- Splash screen aparecerá (30-60 segundos primer inicio)
- Interfaz principal se mostrará cuando esté lista

### 2.2 Instalación Manual (Para Desarrolladores)

#### Paso 1: Instalar Tesseract OCR

1. Descargar: `tesseract-ocr-w64-setup-v5.0.exe` o superior
   - Desde: https://github.com/UB-Mannheim/tesseract/wiki
   
2. Ejecutar instalador:
   ```
   tesseract-ocr-w64-setup-v5.0.exe
   ```
   - Aceptar licencia
   - Seleccionar carpeta: `C:\Program Files\Tesseract-OCR`
   - Instalar con lenguaje español (recomendado)

3. Configurar variable de entorno:
   ```
   Sistema → Variables de entorno → Nueva variable de usuario:
   Nombre: PYTESSERACT_PATH
   Valor: C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

#### Paso 2: Clonar Repositorio

```bash
# Abrir PowerShell o Command Prompt
cd %USERPROFILE%\Documents

# Clonar proyecto
git clone https://github.com/CUCEI/redocnizer.git
cd redocnizer
```

#### Paso 3: Crear Entorno Virtual

```bash
# Python venv
python -m venv venv

# Activar entorno
venv\Scripts\activate
# (Deberías ver "(venv)" en el prompt)
```

#### Paso 4: Instalar Dependencias

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar requirements
pip install -r requirements.txt
```

**Esperar 5-10 minutos** (descarga ~500 MB de librerías)

#### Paso 5: Ejecutar Aplicación

```bash
# Desde raíz del proyecto
python app.py
```

---

## 3. Configuración Inicial

### 3.1 Primer Inicio: Asistente de Configuración

Cuando REDOCNIZER se ejecuta por primera vez, aparecerá:

#### Pantalla 1: Bienvenida
```
╔════════════════════════════════════════╗
║     REDOCNIZER - Asistente Inicial    ║
║                                        ║
║  Bienvenido al sistema de OCR         ║
║  para contratos académicos CUCEI      ║
╚════════════════════════════════════════╝

[ Siguiente ]
```

#### Pantalla 2: Seleccionar Carpeta Raíz
```
Carpeta donde se guardará la información:

Buscar:  [  C:\Users\user\Documents  ]  [Examinar...]

Por defecto se usará:
C:\Users\user\Documents\REDOCNIZER_DATA
```

#### Pantalla 3: Configurar Tesseract
```
Detectar ubicación de Tesseract:

Sistema detectó: C:\Program Files\Tesseract-OCR
¿Es correcto?
[ Sí ]  [ Cambiar... ]
```

#### Pantalla 4: Calendarios Disponibles
```
Seleccionar calendarios académicos:

[x] 2024A
[x] 2024B
[ ] 2023A
[ ] 2023B

[ Finalizar ]
```

### 3.2 Estructura de Directorios Después de Instalación

```
C:\Users\user\Documents\REDOCNIZER_DATA/
│
├── calendarios/              # Calendarios de referencia
│   ├── 2024A.csv
│   ├── 2024B.csv
│   └── README.md
│
├── contratos/                # Datos procesados
│   ├── 2024A/
│   │   ├── contratos.csv
│   │   ├── validacion.log
│   │   └── backup_YYYYMMDD.csv
│   └── 2024B/
│
├── uploads/                  # Archivos temporales
│   └── [archivos subidos]
│
├── previews/                 # Vistas previas de OCR
│   └── [imágenes de preview]
│
├── logs/                      # Archivos de registro
│   ├── app.log
│   ├── ocr.log
│   └── errors.log
│
├── cache/                     # Modelos descargados
│   ├── crnn_model.h5
│   └── easyocr/
│
└── config.json               # Configuración de usuario
```

### 3.3 Archivo de Configuración (config.json)

```json
{
  "version": "1.0.0",
  "usuario": "admin",
  "carpeta_raiz": "C:\\Users\\user\\Documents\\REDOCNIZER_DATA",
  "idioma": "es",
  "tema": "Fusion",
  
  "tesseract": {
    "ruta": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "lenguajes": ["spa", "eng"],
    "versión": "5.0"
  },
  
  "ocr": {
    "metodo_primario": "tesseract",
    "metodo_secundario": "easyocr",
    "crnn_modelo": "keras_cnn_lstm_v4_ctc.h5",
    "usar_gpu": false,
    "confianza_minima": 0.70,
    "validacion_cruzada": true
  },
  
  "interfaz": {
    "ventana_ancho": 1200,
    "ventana_alto": 800,
    "maximizado": false,
    "preview_tamaño": 300,
    "tema_oscuro": false
  },
  
  "calendarios_activos": ["2024A", "2024B"],
  
  "seguridad": {
    "encriptar_credenciales": true,
    "log_cambios": true,
    "requerir_validacion": true
  }
}
```

---

## 4. Configuración Avanzada

### 4.1 Usar GPU NVIDIA (Opcional)

#### Requisitos
- GPU: NVIDIA con soporte CUDA 11.0+
- Drivers: NVIDIA actualizados
- RAM GPU: Mínimo 2 GB

#### Instalación CUDA/cuDNN

```bash
# 1. Instalar CUDA 11.8
# Descargar desde: https://developer.nvidia.com/cuda-11-8-0-download-archive

# 2. Instalar cuDNN
# Descargar desde: https://developer.nvidia.com/cudnn
# Seguir instrucciones de NVIDIA

# 3. Actualizar requirements
pip install tensorflow-gpu==2.10.0

# 4. Verificar
python -c "import tensorflow as tf; print(tf.test.is_built_with_cuda())"
# Debería imprimir: True
```

#### Configurar en REDOCNIZER

Editar `config.json`:
```json
{
  "ocr": {
    "usar_gpu": true,
    "gpu_device": 0,
    "gpu_memory_fraction": 0.8
  }
}
```

### 4.2 Cambiar Modelo CRNN

#### Modelos Disponibles

| Modelo | Precisión | Velocidad | Tamaño | Recomendado para |
|--------|-----------|-----------|--------|------------------|
| v3 | 92% | ⚡⚡⚡ | 45 MB | Laptop/CPU |
| v3_ctc | 93% | ⚡⚡ | 50 MB | Estándar |
| v4_ctc | 96% | ⚡ | 65 MB | Máxima precisión |
| v4_lite | 94% | ⚡⚡⚡ | 28 MB | Recursos limitados |

#### Cambiar Modelo

1. Descargar modelo:
   ```bash
   wget https://github.com/CUCEI/redocnizer/releases/download/models/keras_cnn_lstm_v4_ctc.h5
   ```

2. Guardar en: `%APPDATA%\REDOCNIZER\models\`

3. Editar `config.json`:
   ```json
   {
     "ocr": {
       "crnn_modelo": "keras_cnn_lstm_v4_ctc.h5"
     }
   }
   ```

4. Reiniciar REDOCNIZER

### 4.3 Configurar Proxy (Entorno Corporativo)

```bash
# Si está detrás de proxy corporativo

# 1. En Python:
pip install --proxy [user:passwd@]proxy.server:port -r requirements.txt

# 2. En Git:
git config --global http.proxy http://user:passwd@proxy.server:port

# 3. En REDOCNIZER (config.json):
{
  "red": {
    "usar_proxy": true,
    "proxy_url": "http://proxy.server:port",
    "proxy_usuario": "usuario",
    "proxy_password": "contraseña"
  }
}
```

---

## 5. Troubleshooting

### 5.1 Problema: Tesseract No Se Encuentra

**Error**:
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**Solución**:
```bash
# 1. Verificar instalación
where tesseract

# 2. Si no está en PATH, agregar variable de entorno:
setx PYTESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"

# 3. Reiniciar Python/REDOCNIZER
```

### 5.2 Problema: Modelo CRNN No Carga

**Error**:
```
FileNotFoundError: Could not find model file: keras_cnn_lstm_v4_ctc.h5
```

**Solución**:
```bash
# 1. Descargar modelo manualmente
wget https://github.com/CUCEI/redocnizer/releases/download/models/keras_cnn_lstm_v4_ctc.h5

# 2. Guardar en carpeta correcta
# Windows: C:\Users\[usuario]\AppData\Local\REDOCNIZER\models\
# Linux: ~/.local/share/redocnizer/models/
# macOS: ~/Library/Application Support/REDOCNIZER/models/

# 3. Reiniciar aplicación
```

### 5.3 Problema: Memoria Insuficiente

**Error**:
```
MemoryError: Unable to allocate 500 MiB for an array
```

**Soluciones**:

a) Usar modelo más ligero:
```json
{
  "ocr": {
    "crnn_modelo": "keras_cnn_lstm_v4_lite.h5"
  }
}
```

b) Reducir batch size:
```json
{
  "ocr": {
    "batch_size": 4
  }
}
```

c) Procesamiento serial:
```json
{
  "procesamiento": {
    "modo_paralelo": false,
    "workers": 1
  }
}
```

### 5.4 Problema: Aplicación Lenta

**Síntomas**: Interfaz se congela al procesar

**Causas y Soluciones**:

| Causa | Síntoma | Solución |
|-------|--------|----------|
| CPU alta | Todas operaciones lentas | Reducir workers, usar GPU |
| RAM alta | Crash al procesar lotes | Reducir batch_size |
| Disco lento | Guardado lento | Usar SSD, reducir preview_tamaño |
| EasyOCR lento | OCR específicamente lento | Usar solo Tesseract + CRNN |

---

## 6. Desinstalación

### 6.1 Windows

1. **Desinstalar desde Panel de Control**:
   - `Configuración → Aplicaciones → REDOCNIZER`
   - Clic en desinstalar

2. **Limpiar datos (opcional)**:
   ```
   Si deseas eliminar datos guardados:
   Eliminar: C:\Users\[usuario]\Documents\REDOCNIZER_DATA
   ```

3. **Desinstalar Tesseract (si no lo usa otro programa)**:
   - `Configuración → Aplicaciones → Tesseract OCR`
   - Clic en desinstalar

### 6.2 Linux/macOS

```bash
# Desinstalar (si se instaló con pip)
pip uninstall redocnizer

# Limpiar datos
rm -rf ~/.local/share/redocnizer/
# o
rm -rf ~/Library/Application\ Support/REDOCNIZER/
```

---

## 7. Actualización

### 7.1 Verificar Versión Actual

Dentro de REDOCNIZER: `Ayuda → Acerca de`

### 7.2 Actualizar a Nueva Versión

```bash
# Opción 1: Descargar nuevo instalador y ejecutar
redocnizer-1.1.0-setup.exe
# (Mantiene datos anteriores)

# Opción 2: Desde línea de comandos (desarrollo)
cd redocnizer/
git pull origin main
pip install -r requirements.txt
python app.py
```

---

*Última actualización: 23 de junio de 2024*
