# 📋 JUSTIFICACIÓN DEL MÓDULO 3: Sistemas Robustos, Paralelos y Distribuidos

## **Resumen Ejecutivo**

El proyecto OCR Modular implementa una **arquitectura distribuida cliente-servidor** que cumple con los requisitos del Módulo 3, particularmente:

- **3.3**: Sistema basado en nube (Google Drive), NO servidor local
- **3.4**: Protocolos HTTPS + OAuth 2.0 (Google API)
- **3.5**: Arquitectura cliente-servidor con distribución de trabajo
- **3.6**: Sincronización de recursos (datos/documentos) entre múltiples dispositivos

---

## **3.1 - Algoritmos Implementados**

### Algoritmo de Sincronización Bidireccional

```
CLIENTE (Local)                    SERVIDOR (Google Drive)
┌─────────────────┐              ┌──────────────────────┐
│ Archivo Local   │   ────────→  │ BD en Nube (Drive)   │
│ contratos.csv   │   ←────────  │ datos_sincronizados  │
└─────────────────┘              └──────────────────────┘
```

**Pseudocódigo del Algoritmo:**

```
FUNCIÓN sync_local_to_drive(carpeta_local)
    PARA CADA archivo EN carpeta_local HACER
        SI archivo NO existe EN Drive ENTONCES
            subir_archivo(archivo)
            crear_metadato(archivo)
        FIN SI
    FIN PARA
FIN FUNCIÓN

FUNCIÓN sync_drive_to_local(carpeta_local)
    PARA CADA archivo EN Drive HACER
        SI archivo NO existe LOCAL ENTONCES
            descargar_archivo(archivo)
        SINO SI timestamp_remoto > timestamp_local ENTONCES
            actualizar_archivo(archivo)
        FIN SI
    FIN PARA
FIN FUNCIÓN
```

### Algoritmo de Autenticación Distribuida (OAuth 2.0)

```
Usuario → [Navegador] → Google Auth Server → Token JWT → Cliente
                              ↓
                          Valida Credenciales
                              ↓
                          Genera Token Seguro
```

**Ventajas:**
- ✅ Seguridad: Token encriptado, no se guarda contraseña
- ✅ Distribución: Autenticación centralizada en Google
- ✅ Escalabilidad: Soporta múltiples usuarios simultáneamente
- ✅ No requiere servidor local

---

## **3.2 - Herramientas y Tecnologías**

| Herramienta | Versión | Rol | Módulo |
|-------------|---------|-----|--------|
| **Google Drive API** | v3 | BD Distribuida en nube | 3.3, 3.5, 3.6 |
| **Google OAuth 2.0** | 2.0 | Autenticación segura | 3.4 |
| **HTTPS** | TLS 1.3 | Protocolo de comunicación encriptado | 3.4 |
| **Python** | 3.9+ | Lenguaje de implementación | - |
| **google-api-python-client** | v2.100+ | Cliente de API REST | 3.5 |
| **PySide6** | 6.5+ | Interfaz gráfica distribuida | 3.5 |
| **Pandas** | 2.0+ | Manejo de datos sincronizados | 3.6 |

### Explicación del Dominio de Herramientas

#### **Google Drive API**
- **Cómo se usa**: 
  - `service.files().create()` para subir archivos
  - `service.files().list()` para listar remotos
  - `service.files().get_media()` para descargar
  - `service.about().get()` para info de usuario
  
- **Ventajas técnicas**:
  - API REST basada en estándares HTTP
  - Autenticación OAuth 2.0 integrada
  - Versionado automático de archivos
  - Disponibilidad 99.9% (Google Cloud)

#### **OAuth 2.0**
- **Protocolo de seguridad distribuido**:
  - Cliente solicita permiso
  - Usuario se autentica en servidor Google
  - Servidor retorna token JWT
  - Cliente usa token para operaciones subsecuentes
  
- **Ventaja para distribución**:
  - No requiere servidor local
  - Cada usuario autenticado independiente
  - Token válido en múltiples dispositivos
  - Revocación centralizada

---

## **3.3 - NO Servidor Local (CUMPLE REQUISITO)**

### ❌ LO QUE NO SE USA

```python
# ❌ PROHIBIDO: Servidor local
sqlite3.connect("contratos_local.db")  # ← NO se usa
server = Flask(__name__)               # ← NO se usa
socket.create_server()                 # ← NO se usa
```

### ✅ LO QUE SE USA

```python
# ✅ Google Cloud (Nube)
drive_service = GoogleDriveService()   # ← API REST
files = drive_service.list_files()     # ← Llamada HTTP a Google
drive_service.upload_contract(path)    # ← Almacenamiento distribuido
```

**Justificación:**
- Todos los datos residen en **Google Drive** (propiedad de Google)
- Acceso vía **API REST HTTPS**, no socket local
- Computación: Cliente (PySide6) + Servidor (Google)
- BD completamente distribuida, no local

---

## **3.4 - Protocolos de Comunicación**

### Protocolo HTTPS + OAuth 2.0

```
Cliente Local                          Google Drive API
    │                                       │
    ├─── POST /oauth2/v4/token ──────────→ │
    │    (Solicita token)                   │
    │                                       │
    │←─── JWT Token ────────────────────────┤
    │                                       │
    ├─── GET /drive/v3/files ──────────────→ │
    │    (Authorization: Bearer <token>)    │
    │                                       │
    │←─── JSON [files] ──────────────────────┤
    │                                       │
    ├─── PUT /upload/drive/v3 ─────────────→ │
    │    (Multipart: archivo + metadata)    │
    │                                       │
    │←─── File ID + Timestamp ───────────────┤
```

**Especificaciones de Red:**

| Aspecto | Detalles |
|--------|---------|
| **Puerto** | 443 (HTTPS) |
| **Protocolo** | HTTP/1.1 + TLS 1.3 |
| **Autenticación** | Bearer Token (JWT) |
| **Formato de datos** | JSON + Multipart |
| **Latencia típica** | 100-500ms |
| **Timeout** | 30 segundos |

### Justificación de Protocolos

**¿Por qué HTTPS?**
- ✅ Encriptación de datos en tránsito
- ✅ Verificación de identidad (certificado SSL)
- ✅ Estándar de facto en APIs REST

**¿Por qué OAuth 2.0?**
- ✅ Estándar de seguridad distribuida
- ✅ No expone credenciales del usuario
- ✅ Permite revocación sin cambiar contraseña
- ✅ Soporta múltiples aplicaciones

---

## **3.5 - Distribución del Trabajo**

### Arquitectura de Entidades Funcionales

```
┌──────────────────────────────────────────────────────────┐
│                      SISTEMA DISTRIBUIDO                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  CLIENTE LOCAL (PySide6 GUI)                             │
│  ├─ Interfaz usuario                                     │
│  ├─ OCR local (CPU/GPU)                                  │
│  ├─ Preprocesamiento de imágenes                         │
│  └─ Almacenamiento temporal                              │
│                                                           │
│                      ↕ HTTPS (Sync)                      │
│                                                           │
│  SERVIDOR DISTRIBUIDO (Google Drive)                     │
│  ├─ Almacenamiento de archivos                           │
│  ├─ Sincronización de datos                              │
│  ├─ Control de versiones                                 │
│  └─ Metadata de usuarios                                 │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### División de Responsabilidades

| Componente | Ubicación | Función |
|-----------|-----------|---------|
| **UI (PySide6)** | Cliente Local | Interfaz usuario, entrada/salida |
| **OCR Pipeline** | Cliente Local | Procesamiento (CRNN, Tesseract) |
| **Storage** | Google Drive | Persistencia de datos |
| **Auth Service** | Google Cloud | Validación de usuarios |
| **Sync Engine** | Cliente Local + Google | Sincronización bidireccional |

### Flujo de Trabajo Distribuido

```
ESCENARIO: Usuario procesa contrato en oficina, luego en casa

OFICINA
├─ 1. Usuario abre aplicación en Oficina-PC
├─ 2. Se autentica con Google (OAuth 2.0)
├─ 3. Descarga archivos de Drive a local
├─ 4. Procesa contrato (OCR local)
├─ 5. Sube resultado a Drive
└─ 6. Cierra aplicación

    [Datos en Google Drive]
           ↓
    
CASA
├─ 1. Usuario abre aplicación en Casa-PC
├─ 2. Se autentica con misma cuenta Google
├─ 3. Descarga últimos archivos de Drive
├─ 4. Ve cambios del día anterior
├─ 5. Continúa procesamiento
└─ 6. Sube cambios actualizados
```

---

## **3.6 - Sistema Descentralizado con Compartición de Recursos**

### Tipo Implementado: 3.1.2 - BD Distribuida

> "Dividir la base de datos entre diferentes arquitecturas de manera justificada"

### Arquitectura de BD Distribuida

```
USUARIO 1                           USUARIO 2
┌─────────────┐                   ┌─────────────┐
│ Oficina-PC  │                   │ Casa-PC     │
│ datos_local1│                   │ datos_local2│
└──────┬──────┘                   └──────┬──────┘
       │                                 │
       └─────────────┬───────────────────┘
                     │ HTTPS + OAuth2.0
                     ▼
            ┌─────────────────┐
            │  Google Drive   │
            │   (BD Nube)     │
            │ ├─ contratos/   │
            │ ├─ datos.csv    │
            │ └─ metadata.json│
            └─────────────────┘
```

### Características de Descentralización

#### **1. Sincronización Bidireccional**

```python
# Cliente 1 (Oficina)
drive.upload_contract("contrato1.pdf")
drive.upload_csv_data(df_procesada)

    ↓ [Google Drive sincroniza]

# Cliente 2 (Casa)
archivos = drive.list_files()  # Ve contrato1.pdf
df = drive.download_csv_data() # Ve datos procesados
```

#### **2. Versionado Distribuido**

- Google Drive mantiene historial automático
- Cada usuario ve versión sincronizada
- Sin conflictos de escritura (timestamps)
- Rollback disponible

#### **3. Autenticación Distribuida**

```python
# Usuario X se autentica en dispositivo A
creds = flow.run_local_server()  # Login único

# Usuario X usa mismo token en dispositivo B
creds = Credentials.from_authorized_user_file("token.json")
```

#### **4. Compartición de Datos**

```
Disponibilidad: Usuario X puede acceder desde:
├─ Oficina (Windows)
├─ Casa (Windows)
├─ Laptop (cualquier OS con Python)
└─ Teléfono (Google Drive app)

Sincronización automática:
├─ Cambios en Oficina → Drive → Casa (en tiempo real)
├─ Sin duplicación de datos
└─ Versión única de verdad (Google Drive)
```

---

## **Comparación: Cumplimiento de Requisitos**

| Requisito | Estado | Evidencia |
|-----------|--------|-----------|
| **3.1 Algoritmos** | ✅ | Sync bidireccional, OAuth |
| **3.2 Herramientas** | ✅ | Google Drive API, OAuth 2.0 |
| **3.3 NO servidor local** | ✅ | Datos en nube, NO local |
| **3.4 Protocolos** | ✅ | HTTPS + OAuth 2.0 |
| **3.5 Distribución** | ✅ | Cliente-servidor, múltiples ubicaciones |
| **3.6 Descentralizado** | ✅ | BD distribuida, multi-dispositivo |

---

## **Demostración Técnica**

### Instalación Rápida

```bash
# 1. Seguir SETUP_GOOGLE_DRIVE.md

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar app
python app.py

# 4. Ir a pestaña "☁️ Sincronización Nube"
# 5. Hacer click en "🔐 Conectar con Google"
# 6. Autorizar aplicación en navegador
# 7. Ver UI de sincronización
```

### Casos de Uso

**Caso 1: Trabajar desde múltiples ubicaciones**
```
1. Usuario abre app en Oficina
2. Procesa contrato, sube a nube
3. Cierra sesión
4. Se va a casa, abre app
5. Ve archivos sincronizados
6. Descarga y continúa trabajo
```

**Caso 2: Respaldo automático**
```
1. Usuario sube contrato vía UI
2. Google Drive lo almacena indefinidamente
3. Si PC local falla, datos persisten en nube
4. Recuperación en otro dispositivo
```

**Caso 3: Sincronización en tiempo real**
```
1. Usuario A procesa datos en Oficina
2. Usuario A sube CSV actualizado
3. Usuario B en Casa ve actualización al refrescar
4. Sin servidor local, todo en Google Drive
```

---

## **Conclusión**

El proyecto OCR Modular implementa una **arquitectura distribuida completa** que:

✅ **Cumple 3.3**: No usa servidor local, datos en Google Cloud  
✅ **Cumple 3.4**: Comunicación HTTPS + OAuth 2.0  
✅ **Cumple 3.5**: Cliente-servidor distribuido, múltiples dispositivos  
✅ **Cumple 3.6**: BD distribuida con sincronización de recursos  

**Justificación de Diseño:**
- Google Drive como BD descentralizada
- OAuth 2.0 como protocolo de autenticación
- Sincronización bidireccional de archivos
- Sin dependencia de servidor local
- Escalable a múltiples usuarios y dispositivos

---

**Documento preparado para evaluación del Comité de Titulación**  
*Carrera: Ingeniería Informática*  
*Proyecto: OCR Modular - Detección y Automatización de Contratos*
