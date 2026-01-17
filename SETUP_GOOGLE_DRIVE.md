# 🔧 Configuración de Google Drive API para Sincronización

## 1. Crear Proyecto en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Click en **"Crear Proyecto"**
3. Nombre: `Redocnizer-Drive`
4. Click **Crear**

## 2. Habilitar Google Drive API

1. En la barra de búsqueda, buscar: `Google Drive API`
2. Click en el resultado
3. Click en **"HABILITAR"**

## 3. Crear Credenciales OAuth 2.0

1. Click en **"+ CREAR CREDENCIALES"**
2. Tipo: **OAuth 2.0 - ID de cliente**
3. Tipo de aplicación: **Aplicación de escritorio**
4. Nombre: `OCR-App-Desktop`
5. Click **Crear**
6. Descargar el JSON (será `credentials.json`)
7. **Guardar en la raíz del proyecto** como `credentials.json`

## 4. Configurar Pantalla de consentimiento OAuth

1. En el menú lateral, ir a **"Pantalla de consentimiento OAuth"**
2. Tipo de usuario: **Externo**
3. Click **Crear**
4. Rellenar:
   - **Nombre de la aplicación**: OCR Modular
   - **Email de soporte**: tu@email.com
5. Click **Guardar y continuar**
6. En Permisos, agregar:
   - `https://www.googleapis.com/auth/drive.file`
7. Click **Guardar y continuar**
8. Agregar tu email como usuario de prueba

## 5. Instalar Dependencias

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## ⚠️ IMPORTANTE

- `credentials.json` NO debe compartirse (agregar a `.gitignore`)
- El token almacenado será `token.json` (generado automáticamente)
- Cada usuario necesita hacer login la primera vez
