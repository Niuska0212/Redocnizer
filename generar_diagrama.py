"""
DIAGRAMA DE ARQUITECTURA DISTRIBUIDA - Representación visual completa
"""

DIAGRAMA_GENERAL = """

╔═══════════════════════════════════════════════════════════════════════════════╗
║                    SISTEMA OCR DISTRIBUIDO - ARQUITECTURA                    ║
║                    (Cumple Criterios 3.1, 3.2, 3.3)                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝


                            RED/INTERNET
                    ═════════════════════════════════
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          │                       │                       │
    ┌─────┴──────┐          ┌─────┴──────┐          ┌─────┴──────┐
    │ Cliente 1  │          │ Cliente 2  │          │ Cliente N  │
    │ (Mi PC)    │          │ (Otra PC)  │          │ (Nube)     │
    └─────┬──────┘          └─────┬──────┘          └─────┬──────┘
          │                       │                       │
          │        HTTP REST      │        HTTP REST      │
          │      (Puerto 5000)    │      (Puerto 5000)    │
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                                  ↓
                    ╔═════════════════════════════╗
                    │   API REST Server (Flask)   │
                    │   • /api/process-contract  │
                    │   • /api/get-contracts     │
                    │   • /api/search-contracts  │
                    │   • /api/delete-contract   │
                    │   • /api/stats             │
                    ║════════════════════════════╝
                                  │
                    (Puede estar en Heroku/AWS/GCP)
                                  │
                                  ↓
                    ╔═════════════════════════════╗
                    │  Document Extractor (OCR)  │
                    │  • Preprocessing           │
                    │  • CRNN Inference          │
                    │  • Tesseract OCR           │
                    ║════════════════════════════╝
                                  │
                                  ↓
                    ╔═════════════════════════════╗
                    │  Firebase Service           │
                    │  • Singleton Pattern        │
                    │  • CRUD Operations         │
                    │  • Query Distribuido       │
                    ║════════════════════════════╝
                                  │
                    (Google Cloud Firestore API)
                                  │
                                  ↓
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  FIRESTORE DATABASE (BD DISTRIBUIDA)                       ║
║                        Google Cloud Platform                               ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  Colección: contratos                                              │  ║
║  │  ├─ doc_001: {RFC: "ABC123", NOMBRE: "Juan", FECHA: "..."}        │  ║
║  │  ├─ doc_002: {RFC: "DEF456", NOMBRE: "María", FECHA: "..."}       │  ║
║  │  ├─ doc_003: {RFC: "GHI789", NOMBRE: "Carlos", FECHA: "..."}      │  ║
║  │  └─ ... (más documentos)                                           │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ✅ Replicada en múltiples datacenters (us-central, eu-west, etc)        ║
║  ✅ Disponibilidad 99.9% (SLA Google)                                    ║
║  ✅ Accesible desde CUALQUIER máquina/red                                ║
║  ✅ NO ES LOCAL - Está en servidores de Google                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════════
FLUJO DE UN CONTRATO A TRAVÉS DEL SISTEMA DISTRIBUIDO
═══════════════════════════════════════════════════════════════════════════════

     ┌─────────────────────────────────────────────────────────────────┐
     │ 1. USUARIO (Cliente Local)                                      │
     │    └─ Abre interfaz PySide6                                     │
     │    └─ Selecciona archivo PDF/imagen                            │
     │    └─ Click en "Procesar"                                       │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 2. CLIENTE (ocr_client.py en máquina local)                    │
     │    └─ Lee archivo del disco                                     │
     │    └─ Codifica a base64                                         │
     │    └─ Crea JSON payload                                         │
     │    └─ HTTP POST → Servidor (puede estar en otra máquina)       │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
                         HTTP POST
                        (Puerto 5000)
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 3. SERVIDOR (api_server.py en nube)                            │
     │    └─ Recibe petición HTTP                                      │
     │    └─ Decodifica base64 → Imagen                                │
     │    └─ Invoca DocumentExtractor                                  │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 4. OCR (Document Extractor)                                     │
     │    └─ Preprocesa imagen                                         │
     │    └─ Ejecuta modelo CRNN                                       │
     │    └─ Ejecuta Tesseract OCR                                     │
     │    └─ Retorna diccionario {RFC, NOMBRE, FECHA, ...}            │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 5. SERVIDOR recibe datos del OCR                               │
     │    └─ Crea objeto para guardar                                  │
     │    └─ Invoca Firebase Service                                   │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 6. BD DISTRIBUIDA (Firebase Firestore - Google Cloud)          │
     │    └─ Crea documento en colección 'contratos'                   │
     │    └─ Asigna ID único: "doc_abc123"                            │
     │    └─ Replica en datacenters de Google                          │
     │    └─ Retorna confirmación al servidor                          │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 7. SERVIDOR responde a Cliente                                 │
     │    └─ HTTP 200 + JSON con:                                      │
     │       {                                                         │
     │         "success": true,                                        │
     │         "data": {RFC, NOMBRE, ...},                            │
     │         "document_id": "abc123",                                │
     │         "processing_time_ms": 1250                             │
     │       }                                                         │
     └──────────────────────────┬──────────────────────────────────────┘
                                │
     ┌──────────────────────────┴──────────────────────────────────────┐
     │ 8. CLIENTE recibe respuesta                                     │
     │    └─ Actualiza UI con datos extraídos                          │
     │    └─ Muestra "✅ Guardado en BD distribuida"                   │
     └─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
CUMPLIMIENTO DE CRITERIOS
═══════════════════════════════════════════════════════════════════════════════

CRITERIO 3.1 - DOMINIO DE ALGORITMOS
╔═════════════════════════════════════════════════════════════════════════════╗
║ ✅ Cliente-Servidor REST                                                   ║
║    └─ Patrón de separación: Cliente vs Servidor vs BD                      ║
║    └─ Comunicación asincrónica vía HTTP                                    ║
║    └─ Manejo de errores y reintentos                                       ║
║                                                                             ║
║ ✅ Singleton Pattern                                                       ║
║    └─ Garantiza 1 conexión a BD (no N conexiones)                          ║
║    └─ Thread-safe access a recursos                                        ║
║    └─ Eficiente en memoria                                                 ║
║                                                                             ║
║ ✅ Replicación en Cloud                                                    ║
║    └─ Firebase: Multi-región automática                                    ║
║    └─ Consistencia eventual (CAP theorem)                                  ║
║    └─ Recuperación ante fallos                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝

CRITERIO 3.2 - DOMINIO DE HERRAMIENTAS
╔═════════════════════════════════════════════════════════════════════════════╗
║ ✅ Flask - Microservicios REST                                             ║
║    └─ Lightweight, fácil de escalar                                        ║
║    └─ Endpoints RESTful bien diseñados                                     ║
║    └─ Manejo automático de threading                                       ║
║                                                                             ║
║ ✅ HTTP/REST - Protocolo de Comunicación                                   ║
║    └─ Agnóstico a SO (Windows, Linux, Mac)                                 ║
║    └─ Puertos estándar (80/443 en producción)                              ║
║    └─ Ampliamente soportado                                                ║
║                                                                             ║
║ ✅ Firebase Firestore - BD Distribuida                                     ║
║    └─ Google Cloud Platform                                                ║
║    └─ Replicación automática multi-región                                  ║
║    └─ 99.9% SLA                                                            ║
║    └─ Escalado automático                                                  ║
║                                                                             ║
║ ✅ Base64 - Transferencia de Binarios                                      ║
║    └─ Codificación segura para HTTP JSON                                   ║
║    └─ No requiere parsers especiales                                       ║
║    └─ Compatible con firewall                                              ║
╚═════════════════════════════════════════════════════════════════════════════╝

CRITERIO 3.3 - NO SERVIDOR LOCAL (CRÍTICO)
╔═════════════════════════════════════════════════════════════════════════════╗
║ ❌ PROHIBIDO (Lo que NO hacemos):                                          ║
║    • Usar SQL Server/MySQL en localhost:3306                               ║
║    • BD SQLite en C:/datos/                                                ║
║    • Servidor en 127.0.0.1                                                 ║
║    • Archivos de BD en disco local                                         ║
║                                                                             ║
║ ✅ IMPLEMENTADO (Lo que SÍ hacemos):                                       ║
║    • Firebase Firestore en Google Cloud                                    ║
║    • Servidores de Google (NO máquina local)                               ║
║    • Replicado en múltiples datacenters                                    ║
║    • Accesible desde cualquier máquina/red                                 ║
║    • Verificable en console.firebase.google.com                            ║
║                                                                             ║
║ 🧪 PRUEBA:                                                                 ║
║    1. Ve a https://console.firebase.google.com                             ║
║    2. Navega a "Firestore Database"                                        ║
║    3. Verás datos en servidores de Google (NO en tu máquina)               ║
║    4. Pueden verlos desde otra máquina también                             ║
╚═════════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════════
ESCALABILIDAD Y DISTRIBUCIÓN REAL
═══════════════════════════════════════════════════════════════════════════════

ESCENARIO 1: Testing Local (1 máquina)
┌─────────────────────────────────────────────┐
│ Mi PC                                       │
│ ├─ Cliente (ocr_client.py)                 │
│ ├─ Servidor (api_server.py)                │
│ └─ Comunicación: localhost:5000            │
│                                             │
│ BD: Firebase (Google Cloud)                │
│     ├─ Datos replicados automáticamente    │
│     └─ Accesibles desde cualquier cliente  │
└─────────────────────────────────────────────┘

ESCENARIO 2: Distribuido (2+ máquinas)
┌─────────────────────────┐        ┌──────────────────────┐
│ PC 1 (Cliente)          │        │ PC 2 (Servidor)      │
│ ├─ UI (PySide6)         │ ─HTTP─→│ ├─ Flask API         │
│ └─ ocr_client.py        │        │ └─ DocumentExtractor │
└─────────────────────────┘        └──────────────────────┘
           │                                 │
           │                                 │
           └──────────────────┬──────────────┘
                              │ API Firestore
                              ↓
                    ┌──────────────────────┐
                    │ Google Cloud         │
                    │ Firestore Database   │
                    │ (BD Distribuida)     │
                    │ - Replicada          │
                    │ - Disponible 99.9%   │
                    │ - NO local           │
                    └──────────────────────┘

ESCENARIO 3: Producción (Escalado Horizontal)
                  ┌──────────────────┐
                  │ Load Balancer    │
                  │ (Nginx/HAProxy)  │
                  └────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ↓                  ↓                  ↓
   ┌─────────┐        ┌─────────┐       ┌─────────┐
   │Server 1 │        │Server 2 │       │Server N │
   │(Heroku) │        │(AWS)    │       │(GCP)    │
   └────┬────┘        └────┬────┘       └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────┴──────┐
                    │ Firebase    │
                    │ (Google)    │
                    │ ✅ 1 BD     │
                    │ ✅ N Clientes
                    │ ✅ Escalado │
                    │ ✅ 99.9%    │
                    └─────────────┘


═══════════════════════════════════════════════════════════════════════════════
CONCLUSIÓN
═══════════════════════════════════════════════════════════════════════════════

✅ Sistema distribuido COMPLETO y funcional
✅ Cumple criterios 3.1 (algoritmos), 3.2 (herramientas), 3.3 (no local)
✅ Escalable a producción
✅ Listo para presentación al comité de titulación

"""

if __name__ == "__main__":
    print(DIAGRAMA_GENERAL)
    
    # Guardar en archivo
    with open("DIAGRAMA_ARQUITECTURA.txt", "w", encoding="utf-8") as f:
        f.write(DIAGRAMA_GENERAL)
    
    print("\n💾 Diagrama guardado en: DIAGRAMA_ARQUITECTURA.txt")
