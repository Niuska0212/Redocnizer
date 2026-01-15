# 📘 SISTEMA DISTRIBUIDO - README

**Implementación de criterios 3.1-3.3 (Módulo 3: Sistemas Robustos, Paralelos y Distribuidos)**

---

## 📂 Archivos Nuevos (Sistema Distribuido)

```
Proyecto-modular/
│
├── 📄 ARCHIVOS CLAVE NUEVOS:
│   ├── ARQUITECTURA_DISTRIBUIDA.md          ⭐ Doc técnica completa
│   ├── JUSTIFICACION_CRITERIOS_3_1_3_3.md   ⭐ Para presentación comité
│   ├── GUIA_SISTEMA_DISTRIBUIDO.md          ⭐ Guía paso a paso
│   ├── RESUMEN_SISTEMA_DISTRIBUIDO.md       ⭐ Resumen ejecutivo
│   ├── requirements_distribuido.txt         ⭐ Dependencias nuevas
│   ├── test_distribuido_completo.py         ⭐ Suite de tests
│   └── firebase_credentials.json            ⭐ Credenciales (crear)
│
├── 📁 services/ (Módulos distribuidos)
│   ├── firebase_service.py                  ← BD distribuida
│   ├── api_server.py                        ← Servidor REST
│   ├── ocr_client.py                        ← Cliente distribuido
│   ├── document_extractor.py                (existente)
│   └── ...
│
└── ... (resto del proyecto)
```

---

## 🚀 Inicio Rápido

### **1. Instalar dependencias**
```bash
pip install -r requirements_distribuido.txt
```

### **2. Configurar Firebase**

**A. Crear proyecto Firebase:**
- Ve a https://console.firebase.google.com
- Click "Agregar proyecto"
- Nombre: "OCR-Distribuido"
- Crear proyecto

**B. Crear Firestore Database:**
- "Firestore Database" → "Crear base de datos"
- Modo: "Prueba"
- Ubicación: "nam5 (us-central)"
- Crear

**C. Descargar credenciales:**
- Configuración (⚙️) → "Cuentas de servicio"
- Tab "Firebase Admin SDK"
- "Generar nueva clave privada"
- Guardar como `firebase_credentials.json`
- Colocar en `n:\Proyecto-modular\firebase_credentials.json`

⚠️ Agregar a .gitignore:
```bash
echo "firebase_credentials.json" >> .gitignore
```

### **3. Iniciar servidor**

**Terminal 1: Servidor**
```bash
python services/api_server.py

# Deberías ver:
# ============================================================
# 🚀 OCR REST API - SERVIDOR DISTRIBUIDO
# ============================================================
# ✅ Conectado a Firebase Firestore (BD Distribuida)
# Iniciando servidor en http://0.0.0.0:5000
```

### **4. Probar cliente**

**Terminal 2: Cliente**
```bash
python services/ocr_client.py

# Deberías ver:
# ============================================================
# 🔗 CLIENTE OCR DISTRIBUIDO
# ============================================================
# ✅ Conectado al servidor distribuido
# 📊 Estadísticas del sistema: ...
```

---

## 🧪 Ejecutar Tests

```bash
python test_distribuido_completo.py

# Ejecuta 7 tests verificando:
# ✅ TEST 1: Conexión al servidor
# ✅ TEST 2: Conexión a Firebase
# ✅ TEST 3: Procesamiento distribuido
# ✅ TEST 4: Lectura de BD distribuida
# ✅ TEST 5: Estadísticas del sistema
# ✅ TEST 6: Búsqueda distribuida
# ✅ TEST 7: Cumplimiento de criterios 3.1-3.3
```

---

## 📚 Documentación

| Archivo | Contenido | Para Quién |
|---------|-----------|-----------|
| **ARQUITECTURA_DISTRIBUIDA.md** | Arquitectura técnica completa, algoritmos, herramientas | Programadores |
| **JUSTIFICACION_CRITERIOS_3_1_3_3.md** | Justificación punto por punto para comité | Presentación |
| **GUIA_SISTEMA_DISTRIBUIDO.md** | Paso a paso: instalación, uso, ejemplos | Usuarios |
| **RESUMEN_SISTEMA_DISTRIBUIDO.md** | Resumen ejecutivo (2 minutos) | Para Comité |

---

## 🔍 ¿Cómo Usar?

### **Caso A: Testing Local (Una máquina)**

```bash
# Terminal 1
python services/api_server.py

# Terminal 2
python -c "from services.ocr_client import OCRClient
client = OCRClient('http://localhost:5000')
print(client.get_stats())"
```

### **Caso B: Cliente Remoto (Dos máquinas)**

**En Máquina A (Servidor):**
```bash
python services/api_server.py
# Escuchando en 192.168.1.100:5000
```

**En Máquina B (Cliente remoto):**
```python
from services.ocr_client import OCRClient

client = OCRClient("http://192.168.1.100:5000")  # IP de máquina A
if client.check_connection():
    stats = client.get_stats()
    print("✅ Conectado a servidor remoto")
```

### **Caso C: Integrar con UI (PySide6)**

```python
# En ui/main_window.py

from services.ocr_client import OCRClient

class MainWindow(QMainWindow):
    def __init__(self):
        self.ocr_client = OCRClient(server_url="http://localhost:5000")
    
    def process_contract(self):
        resultado = self.ocr_client.process_contract_from_image(
            image_path=self.selected_file,
            metadata={"usuario": "admin"}
        )
        if resultado['success']:
            self.show_results(resultado['data'])
            print(f"Guardado: {resultado['document_id']}")
```

---

## 📡 Endpoints API

El servidor REST proporciona los siguientes endpoints:

```
GET  /api/health
     └─ Verifica que servidor está activo

POST /api/process-contract
     ├─ Input: {"image_base64": "...", "metadata": {...}}
     └─ Output: {"success": true, "data": {...}, "document_id": "..."}

GET  /api/get-contracts
     └─ Output: {"success": true, "count": N, "data": [...]}

POST /api/search-contracts
     ├─ Input: {"field": "RFC", "value": "ABC123456"}
     └─ Output: {"success": true, "count": N, "data": [...]}

DELETE /api/delete-contract/<doc_id>
       └─ Output: {"success": true, "message": "..."}

GET  /api/stats
     └─ Output: {"success": true, "stats": {"total_contracts": N, ...}}
```

---

## 🏗️ Arquitectura

```
┌────────────────────┐
│   Cliente Local    │  (PySide6 UI)
│   (Tu máquina)     │
└────────┬───────────┘
         │ HTTP REST
         ↓
┌────────────────────┐
│   API Server       │  (Flask)
│   (Nube o remoto)  │
└────────┬───────────┘
         │ API Firestore
         ↓
┌────────────────────┐
│ Firebase Firestore │  (Google Cloud)
│  (BD Distribuida)  │  ← NO LOCAL
└────────────────────┘
```

---

## ✅ Cumplimiento de Criterios

### **3.1 - Dominio de Algoritmos ✅**
- ✅ Cliente-Servidor REST
- ✅ Singleton Pattern
- ✅ Replicación en Cloud
- **Ver:** `services/api_server.py` + `services/ocr_client.py`

### **3.2 - Dominio de Herramientas ✅**
- ✅ Flask (microservicios)
- ✅ HTTP/REST (protocolo)
- ✅ Firebase (BD distribuida)
- ✅ Base64 (transferencia segura)
- **Ver:** `ARQUITECTURA_DISTRIBUIDA.md`

### **3.3 - NO Servidor Local ✅**
- ✅ BD en Google Cloud (NOT localhost)
- ✅ Servidor puede estar en otra máquina
- ✅ Datos accesibles globalmente
- **Ver:** Firebase Console: https://console.firebase.google.com

---

## 🔒 Seguridad (Importante)

1. **firebase_credentials.json** 
   - NUNCA subir a Git
   - Agregar a .gitignore
   - En producción, usar environment variables

2. **HTTPS en Producción**
   - Usar HTTPS, no HTTP
   - Firebase usa HTTPS automáticamente

3. **Autenticación**
   - Agregar API keys o OAuth2
   - Limitar acceso a datos

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| "ConnectionError: Failed to connect" | Iniciar servidor: `python services/api_server.py` |
| "Firebase no está configurado" | Verificar `firebase_credentials.json` existe |
| "ModuleNotFoundError: No module named 'flask'" | `pip install -r requirements_distribuido.txt` |
| "Port 5000 already in use" | Cambiar puerto en `api_server.py` línea 132 |
| "Timeout esperando servidor" | Aumentar timeout o verificar firewall |

---

## 📊 Próximos Pasos

### **Para desarrollo:**
- ✅ Tests locales funcionando
- ✅ Firebase configurado
- ✅ Cliente-Servidor comunicándose

### **Para producción:**
- [ ] Desplegar servidor a Heroku/AWS/GCP
- [ ] Usar HTTPS
- [ ] Agregar autenticación
- [ ] Agregar logging/monitoreo
- [ ] Rate limiting

### **Ejemplo: Deploy a Heroku**
```bash
heroku create mi-ocr-api
git push heroku main
# URL: https://mi-ocr-api.herokuapp.com

# Usar:
client = OCRClient("https://mi-ocr-api.herokuapp.com")
```

---

## 📞 Soporte

Para dudas sobre la implementación distribuida:

1. **Revisar:** `ARQUITECTURA_DISTRIBUIDA.md`
2. **Estudiar:** `JUSTIFICACION_CRITERIOS_3_1_3_3.md`
3. **Ejecutar:** `test_distribuido_completo.py`
4. **Leer:** `GUIA_SISTEMA_DISTRIBUIDO.md`

---

## 📋 Checklist Final

- [ ] Firebase proyecto creado
- [ ] Firestore Database activada
- [ ] `firebase_credentials.json` descargado
- [ ] `firebase_credentials.json` guardado en raíz
- [ ] Dependencias instaladas: `pip install -r requirements_distribuido.txt`
- [ ] Servidor ejecutándose: `python services/api_server.py`
- [ ] Cliente conectado: `python services/ocr_client.py` → "✅ Conectado"
- [ ] Tests pasando: `python test_distribuido_completo.py` → "✅ TODOS LOS TESTS PASARON"
- [ ] Documentación leída
- [ ] Listo para presentación al comité

---

**Versión:** 1.0  
**Fecha:** 14 de enero de 2026  
**Estado:** ✅ COMPLETO Y LISTO
