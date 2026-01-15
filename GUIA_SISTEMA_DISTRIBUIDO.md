# 🚀 GUÍA DE USO: SISTEMA DISTRIBUIDO

## Introducción

Este documento guía paso a paso cómo usar el sistema OCR distribuido para cumplir con los criterios 3.1-3.3.

---

## 📋 Requisitos Previos

1. **Python 3.9+** instalado
2. **Git** para versión control
3. **Cuenta de Firebase** (gratuita en https://console.firebase.google.com)
4. **Tesseract OCR** instalado en el sistema

---

## 🔧 Instalación

### **1. Instalar dependencias**

```bash
cd n:\Proyecto-modular

# Instalar paquetes necesarios
pip install -r requirements_distribuido.txt
```

### **2. Configurar Firebase**

**Paso A: Crear proyecto en Firebase**
```
1. Ve a https://console.firebase.google.com
2. Click en "Agregar proyecto"
3. Nombre: "OCR-Distribuido"
4. Acepta términos
5. Click en "Crear proyecto"
```

**Paso B: Crear base de datos Firestore**
```
1. En el panel, ve a "Firestore Database"
2. Click "Crear base de datos"
3. Modo: "Modo prueba" (para desarrollo)
4. Ubicación: "nam5 (us-central)"
5. Click "Crear"
```

**Paso C: Obtener credenciales**
```
1. Ve a Configuración (⚙️) → Cuentas de servicio
2. Tab "Firebase Admin SDK"
3. Language: Python
4. Click "Generar nueva clave privada"
5. Guarda el JSON con nombre: firebase_credentials.json
6. Coloca en: n:\Proyecto-modular\firebase_credentials.json
```

⚠️ **Importante:** NUNCA publiques firebase_credentials.json en Git. Agregar a .gitignore:
```
echo "firebase_credentials.json" >> .gitignore
```

---

## 🎮 Uso del Sistema

### **Opción 1: Modo Testing (Local)**

Perfecto para pruebas sin desplegar a nube:

```bash
# Terminal 1: Inicia el servidor localmente
python services/api_server.py

# Deberías ver:
# ============================================================
# 🚀 OCR REST API - SERVIDOR DISTRIBUIDO
# ============================================================
# ✅ Conectado a Firebase Firestore (BD Distribuida)
# Iniciando servidor en http://0.0.0.0:5000
```

```bash
# Terminal 2: Usa el cliente
python services/ocr_client.py

# Deberías ver:
# ============================================================
# 🔗 CLIENTE OCR DISTRIBUIDO
# ============================================================
# ✅ Conectado al servidor distribuido
# 
# 📊 Estadísticas del sistema:
# {"total_contracts": 0, ...}
```

### **Opción 2: Procesar un Contrato (Python Script)**

Crea un archivo `test_distribuido.py`:

```python
from services.ocr_client import OCRClient
import os

# 1. Conectar al servidor
client = OCRClient(server_url="http://localhost:5000")

# 2. Verificar conexión
if not client.check_connection():
    print("❌ No hay conexión al servidor")
    print("Inicia: python services/api_server.py")
    exit(1)

# 3. Procesar contrato
resultado = client.process_contract_from_image(
    image_path="ruta/a/contrato.jpg",
    metadata={
        "departamento": "Recursos Humanos",
        "año": 2024,
        "tipo": "laboral"
    }
)

# 4. Ver resultado
if resultado['success']:
    print("✅ Procesado exitosamente")
    print(f"ID documento: {resultado['document_id']}")
    print(f"Datos extraídos: {resultado['data']}")
else:
    print(f"❌ Error: {resultado['error']}")

# 5. Obtener todos los contratos
todos = client.get_all_contracts()
print(f"Total en BD: {todos['count']} contratos")

# 6. Buscar contrato
busqueda = client.search_contracts("RFC", "ABC123456")
print(f"Encontrados: {busqueda['count']} registros")
```

Ejecutar:
```bash
python test_distribuido.py
```

### **Opción 3: Integrar con UI (PySide6)**

Modificar `ui/main_window.py` para usar cliente distribuido:

```python
from services.ocr_client import OCRClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Cliente distribuido
        self.ocr_client = OCRClient(server_url="http://localhost:5000")
    
    def process_contract(self):
        """Procesa contrato usando servidor distribuido"""
        if not self.ocr_client.check_connection():
            QMessageBox.warning(self, "Error", "Servidor no disponible")
            return
        
        # Enviar imagen al servidor
        resultado = self.ocr_client.process_contract_from_image(
            image_path=self.file_path,
            metadata={"usuario": "admin"}
        )
        
        if resultado['success']:
            # Mostrar datos
            self.show_results(resultado['data'])
            QMessageBox.information(
                self, "Éxito", 
                f"Guardado en BD distribuida: {resultado['document_id']}"
            )
```

---

## 📊 Ejemplos de Uso Completo

### **Ejemplo 1: Procesar Lote de Contratos**

```python
from services.ocr_client import OCRClient
import os
from pathlib import Path

client = OCRClient("http://localhost:5000")

# Procesar todos los JPG en una carpeta
carpeta = "data/contratos/2024A"
for archivo in Path(carpeta).glob("*.jpg"):
    print(f"Procesando {archivo.name}...")
    
    resultado = client.process_contract_from_image(
        str(archivo),
        metadata={"batch": "2024A"}
    )
    
    if resultado['success']:
        print(f"  ✅ {resultado['document_id']}")
    else:
        print(f"  ❌ {resultado['error']}")
```

### **Ejemplo 2: Búsqueda y Actualización**

```python
# Buscar contrato por RFC
resultado = client.search_contracts("RFC", "ABC123456")

if resultado['success'] and resultado['count'] > 0:
    # Obtener ID del documento
    doc_id = resultado['data'][0]['id']
    
    # Mostrar datos
    print(f"Encontrado: {resultado['data'][0]['extracted_data']}")
    
    # Eliminar si no es necesario
    client.delete_contract(doc_id)
```

### **Ejemplo 3: Sincronizar Entre Máquinas**

**En máquina A (servidor):**
```bash
python services/api_server.py
```

**En máquina B (cliente remoto):**
```python
from services.ocr_client import OCRClient

# Conectar a máquina A usando su IP
client = OCRClient(server_url="http://192.168.1.100:5000")

# Procesar contrato (se ejecuta en máquina A)
resultado = client.process_contract_from_image("local_contract.jpg")

# Datos se guardan en Firebase (accesible desde cualquier máquina)
print(f"Guardado en nube: {resultado['document_id']}")
```

---

## 🚢 Despliegue en Producción

### **Opción A: Heroku (Gratuito para pruebas)**

```bash
# 1. Instalar Heroku CLI
# Descargar desde https://devcenter.heroku.com/articles/heroku-cli

# 2. Loguearse
heroku login

# 3. Crear app
heroku create mi-ocr-app

# 4. Agregar archivo Procfile en raíz:
echo "web: python services/api_server.py" > Procfile

# 5. Configurar variables de entorno
heroku config:set FLASK_ENV=production

# 6. Deploying
git add .
git commit -m "Deploy OCR distribuido a Heroku"
git push heroku main

# 7. Ver logs
heroku logs --tail

# 8. Usar desde cliente:
client = OCRClient("https://mi-ocr-app.herokuapp.com")
```

### **Opción B: AWS Lambda + API Gateway**

```bash
# Usar SAM (Serverless Application Model)
sam init
# Seleccionar plantilla de Flask
# Deploying: sam deploy --guided
```

### **Opción C: Google Cloud Run**

```bash
# 1. Crear Dockerfile
cat > Dockerfile << EOF
FROM python:3.9-slim
WORKDIR /app
COPY requirements_distribuido.txt .
RUN pip install -r requirements_distribuido.txt
COPY . .
CMD ["python", "services/api_server.py"]
EOF

# 2. Deploy
gcloud run deploy ocr-api --source .

# 3. Obtener URL y usar:
# client = OCRClient("https://ocr-api-xxxxx.run.app")
```

---

## 🔍 Monitoreo y Debugging

### **Ver estadísticas del sistema**

```python
stats = client.get_stats()
print(stats['stats'])
# {
#   "total_contracts": 42,
#   "contracts_today": 5,
#   "total_size_estimates": "210 KB aprox"
# }
```

### **Ver logs del servidor**

```bash
# En terminal donde corre api_server.py:
# [2024-01-14 10:23:45] POST /api/process-contract - 200 - 1250ms
# ✅ Contrato guardado en Firestore
```

### **Verificar conexión Firebase**

```python
from services.firebase_service import firebase_service

try:
    contracts = firebase_service.get_all_contracts()
    print(f"✅ Firebase conectado: {len(contracts)} contratos")
except Exception as e:
    print(f"❌ Error Firebase: {e}")
```

---

## ⚠️ Solución de Problemas

| Problema | Solución |
|----------|----------|
| "ConnectionError: No se pudo conectar" | Verificar que `python services/api_server.py` está corriendo |
| "Firebase no está configurado" | Verificar que `firebase_credentials.json` existe y es válido |
| "ModuleNotFoundError: No module named 'flask'" | Ejecutar `pip install -r requirements_distribuido.txt` |
| "Port 5000 already in use" | Cambiar puerto: `api_server.py` línea 132: `port=5001` |
| "Timeout esperando servidor" | Verificar firewall/antivirus, aumentar timeout |

---

## 📚 Archivos Clave

```
Proyecto-modular/
├── services/
│   ├── api_server.py              ← Servidor REST (ejecutar aquí)
│   ├── ocr_client.py              ← Cliente distribuido
│   ├── firebase_service.py        ← BD distribuida
│   └── document_extractor.py      ← OCR (CRNN + Tesseract)
├── ARQUITECTURA_DISTRIBUIDA.md    ← Documentación técnica
├── requirements_distribuido.txt   ← Dependencias
└── firebase_credentials.json      ← Credenciales (NO en Git)
```

---

## ✅ Checklist de Implementación

- [ ] Firebase configurado
- [ ] Credenciales guardadas en `firebase_credentials.json`
- [ ] Dependencias instaladas: `pip install -r requirements_distribuido.txt`
- [ ] Tesseract OCR instalado
- [ ] Servidor ejecutándose: `python services/api_server.py`
- [ ] Cliente conectado: `python services/ocr_client.py` → "✅ Conectado"
- [ ] Test de procesamiento exitoso
- [ ] Datos visibles en Firebase Console
- [ ] Documentación completa

---

**Versión:** 1.0  
**Última actualización:** 14 de enero de 2026
