# Guía: Acceso a Redes Compartidas (UNC Path)

## 📋 Resumen

El programa ahora soporta **dos formas** de acceder a carpetas compartidas en red que requieren credenciales:

---

## **Opción 1: MAPEO PREVIO (Recomendado) ✅**

### ¿Cuándo usarla?
- Máxima seguridad
- Mejor rendimiento
- Compatible con cualquier tipo de autenticación

### ¿Cómo hacerlo?

#### **Windows Explorer:**
1. Click derecho en "Este equipo" → "Conectar a unidad de red"
2. Ingresa: `\\192.168.1.100\compartido` (o el servidor de tu red)
3. Marca "Conectarse con credenciales diferentes"
4. Ingresa usuario y contraseña
5. Marca "Recordar credenciales"
6. Selecciona letra (ej: Z:)

#### **PowerShell (Administrador):**
```powershell
net use Z: "\\192.168.1.100\compartido" /user:dominio\usuario miContraseña /persistent:yes
```

#### **Ejemplo completo:**
```powershell
# Conectar sin persistencia (temporal)
net use Z: "\\servidor-interno\datos-contratos" /user:DOMINIO\carlos "miPassword123" 

# Conectar y recordar para futuros inicios
net use Z: "\\servidor-interno\datos-contratos" /user:DOMINIO\carlos "miPassword123" /persistent:yes

# Desconectar una unidad mapeada
net use Z: /delete
```

### **Luego en REDOCNIZER:**
- Selecciona el directorio raíz normalmente
- El programa reconocerá `Z:\carpeta` como ruta local
- ✅ Sin dialogs adicionales

---

## **Opción 2: AUTENTICACIÓN INTEGRADA (Nuevo) 🔐**

### ¿Cuándo usarla?
- Cuando el usuario no quiere pre-configurar unidades
- Para redes ocasionales o diferentes durante la sesión

### ¿Cómo funciona?

1. **Selecciona un directorio raíz:**
   - Navega a `\\192.168.1.100\compartido` en el diálogo de carpetas

2. **Se abre automáticamente un diálogo de autenticación:**
   - Te pide usuario (ej: `DOMINIO\usuario` o `usuario@empresa.com`)
   - Te pide contraseña

3. **El programa mapea la unidad automáticamente:**
   - Unidad: `Z:` (o la que especifiques)
   - Persistencia: Por defecto "recordada"

4. **Continúa normalmente:**
   - La ruta se guarda en configuración
   - Próximo inicio cargará la misma ruta

### **Pantalla del Diálogo:**
```
┌─────────────────────────────────────┐
│  Acceso a Red Compartida             │
├─────────────────────────────────────┤
│  Se requiere autenticación para:     │
│  \\192.168.1.100\compartido          │
│                                      │
│  Mapear como: [Z ▼]                  │
│                                      │
│  Usuario: [dominio\usuario       ]  │
│                                      │
│  Contraseña: [•••••••••••]          │
│                                      │
│  ☑ Recordar esta conexión            │
│                                      │
│           [Conectar] [Cancelar]      │
└─────────────────────────────────────┘
```

---

## 🔴 **Solución de Problemas**

### "No se puede acceder a la ruta"
**Causa:** La carpeta no existe o no hay conexión a la red  
**Solución:** Verifica que la red esté disponible:
```powershell
# Probar conexión
Test-Path "\\192.168.1.100\compartido"

# Si usa FQDN:
Test-Path "\\servidor.dominio.local\compartido"
```

### "Error de autenticación"
**Causa:** Usuario/contraseña incorrectos  
**Soluciones:**
- Verifica mayúsculas/minúsculas en contraseña
- Intenta formato con dominio: `DOMINIO\usuario`
- Si es AD: `usuario@empresa.com`
- Pide credenciales al administrador de red

### "Conexión temporal, desaparece al reiniciar"
**Causa:** No marcaste "Recordar conexión"  
**Solución:** Usa `/persistent:yes` en PowerShell o marca checkbox en el diálogo

### "Unidad Z está ocupada"
**Solución:** Usa otra letra (X, Y, etc.) en el selector del diálogo

---

## 💡 RECOMENDACIÓN FINAL

Para **entornos corporativos/profesionales**:
- ✅ Usa **Opción 1** (mapeo previo) 
- Más seguro (credenciales no pasan por dialogs)
- Mejor control administrativo
- El IT puede pre-configurarlo

Para **uso ocasional/desarrollo**:
- ✅ Usa **Opción 2** (autenticación integrada)
- Más cómodo
- No requiere pre-configuración
- Ideal para testing

---

## 📌 Formato de Usuario (Según tu Red)

| Tipo de Red | Formato | Ejemplo |
|---|---|---|
| Dominio Active Directory | `DOMINIO\usuario` | `CUCEI\jgarcia` |
| Azure AD / O365 | `usuario@empresa.com` | `juan.garcia@universidad.edu.co` |
| Servidor SMB local | `usuario` | `admin` |
| NAS Synology | `usuario` | `backup` |

---

## 🔧 Script Helper: Automatizar Mapeo

Si tu admin quiere pre-configurar todo, crea este script en el servidor:

```powershell
# script_mapear_red.ps1
param(
    [string]$Usuario = "DOMINIO\usuario",
    [string]$Contrasena,
    [string]$Ruta = "\\servidor\compartido",
    [string]$Letra = "Z"
)

Write-Host "Mapeando $Ruta como $Letra`:"
net use $Letra`: "$Ruta" /user:$Usuario $Contrasena /persistent:yes

if ($?) {
    Write-Host "✅ Éxito" -ForegroundColor Green
} else {
    Write-Host "❌ Error" -ForegroundColor Red
}
```

**Ejecutar:**
```powershell
.\script_mapear_red.ps1 -Usuario "DOMINIO\usuario" -Contrasena "pass123" -Ruta "\\servidor\datos" -Letra "Z"
```

---

## 📞 Soporte

Si tienes problemas:
1. Verifica conectividad con `ping servidor` o `Test-Path`
2. Confirma permisos con el administrador de red
3. Intenta primero mapear manualmente en Explorer
4. Si funciona en Explorer pero no en el programa, reporta el error
