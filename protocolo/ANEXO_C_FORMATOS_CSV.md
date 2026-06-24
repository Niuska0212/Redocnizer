# ANEXO C: Formatos de Datos CSV

## 1. Estructura General de Datos

REDOCNIZER almacena todos los contratos en archivos CSV (Comma-Separated Values) con la siguiente estructura:

```
REDOCNIZER_DATA/
└── contratos/
    ├── 2024A/
    │   ├── contratos.csv          # Datos principales
    │   ├── validacion.csv         # Estado de validación
    │   ├── historial.csv          # Historial de cambios
    │   └── backup_20240623.csv    # Backup automático
    └── 2024B/
        ├── contratos.csv
        ├── validacion.csv
        └── historial.csv
```

---

## 2. Archivo Principal: contratos.csv

### 2.1 Estructura de Columnas

```csv
id,cedula,nombre,puesto,fecha_inicio,fecha_fin,calendario,dedicacion,departamento,nivel_salarial,estado,fecha_procesamiento,confianza_ocr,error_ocr
1,123.456.789,García López Juan Carlos,Profesor Titular,2024-01-15,2024-12-31,2024A,Tiempo Completo,Ciencias Exactas,Nivel A,validado,2024-06-23 09:30:45,0.98,
2,987.654.321,Pérez Rodríguez María,Auxiliar de Docencia,2024-02-01,2024-06-30,2024A,Por Horas,Ingeniería,Nivel B,validado,2024-06-23 10:15:22,0.95,
3,555.666.777,López Martín José,Técnico Académico,2024-03-10,2024-12-31,2024A,Medio Tiempo,Ciencias Exactas,Nivel C,pendiente_revision,2024-06-23 11:02:33,0.87,"Campo 'puesto' con baja confianza"
```

### 2.2 Descripción de Columnas

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id` | Integer | Identificador único, auto-incrementado | `1, 2, 3...` |
| `cedula` | String | Cédula del académico | `123.456.789` |
| `nombre` | String | Nombre completo | `García López Juan Carlos` |
| `puesto` | String | Puesto académico | `Profesor Titular` |
| `fecha_inicio` | Date | Inicio de contratación | `2024-01-15` |
| `fecha_fin` | Date | Fin de contratación | `2024-12-31` |
| `calendario` | String | Calendario académico | `2024A` |
| `dedicacion` | String | Tipo de dedicación | `Tiempo Completo` |
| `departamento` | String | Departamento CUCEI | `Ciencias Exactas` |
| `nivel_salarial` | String | Nivel salarial asignado | `Nivel A` |
| `estado` | String | Estado de validación | `validado` |
| `fecha_procesamiento` | DateTime | Cuándo se procesó | `2024-06-23 09:30:45` |
| `confianza_ocr` | Float | Confianza del OCR (0-1) | `0.98` |
| `error_ocr` | String | Descripción de errores | `Campo 'puesto' con baja confianza` |

### 2.3 Codificación y Formato

```
Codificación: UTF-8 with BOM (para compatibilidad Excel)
Separador: Coma (,)
Delimitador de texto: Comillas dobles (")
Saltos de línea: CRLF (\r\n) en Windows, LF (\n) en Unix
Decimales: Punto (.) no coma (,)
Fechas: ISO 8601 (YYYY-MM-DD)
Booleanos: 0 = False, 1 = True (o "true"/"false")
```

### 2.4 Valores Permitidos para Enumeraciones

#### Puesto
```
Profesor Titular
Profesor Asociado
Profesor Asistente
Auxiliar de Docencia
Técnico Académico
Coordinador
Jefe de Departamento
Investigador
Otro
```

#### Dedicación
```
Tiempo Completo
Medio Tiempo
Por Horas
Tiempo Parcial
```

#### Departamento
```
Ciencias Exactas
Ingeniería Civil
Ingeniería Electrónica
Ingeniería Industrial
Ingeniería Mecánica
Otro
```

#### Nivel Salarial
```
Nivel A
Nivel B
Nivel C
Nivel D
Nivel E
Nivel F
```

#### Estado de Validación
```
sin_validar       # Recién procesado, sin revisión
pendiente_revision # Errores OCR que requieren validación
validado          # Revisado y aprobado por usuario
rechazado         # Datos incorrectos, rechazado
archivado         # Contrato finalizado/archivado
```

---

## 3. Archivo de Validación: validacion.csv

Registra el estado de validación de cada registro:

```csv
id_contrato,usuario_validacion,fecha_validacion,cambios_realizados,estado_anterior,estado_nuevo,notas
1,admin,2024-06-23 10:00:00,none,sin_validar,validado,"Revisado sin cambios"
2,admin,2024-06-23 10:05:30,"nombre: 'Péres' → 'Pérez'",sin_validar,validado,"Corregida tilde"
3,maria_rh,2024-06-23 11:30:00,"puesto: 'Teccnico' → 'Técnico Académico'",pendiente_revision,validado,"Corregido OCR"
4,maria_rh,2024-06-23 12:15:00,none,pendiente_revision,rechazado,"Fecha inicio > fin, contactar"
```

### 3.1 Columnas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id_contrato` | Integer | Referencia a contratos.csv |
| `usuario_validacion` | String | Usuario que hizo validación |
| `fecha_validacion` | DateTime | Cuándo se validó |
| `cambios_realizados` | String | JSON de cambios o "none" |
| `estado_anterior` | String | Estado antes de validación |
| `estado_nuevo` | String | Estado después de validación |
| `notas` | String | Comentarios del validador |

### 3.2 Formato de cambios_realizados

```json
{
  "nombre": {
    "antes": "García Lóez",
    "después": "García López"
  },
  "puesto": {
    "antes": "Profesor Titulr",
    "después": "Profesor Titular"
  }
}
```

O en caso de sin cambios:
```
none
```

---

## 4. Archivo de Historial: historial.csv

Registro de auditoría completo de todos los cambios:

```csv
timestamp,accion,usuario,id_contrato,campo,valor_anterior,valor_nuevo,detalles
2024-06-23T09:30:45,crear,sistema,1,id,null,1,Contrato procesado desde PDF
2024-06-23T10:00:00,validar,admin,1,nombre,García Lóez,García López,Corrección de OCR
2024-06-23T10:00:00,validar,admin,1,estado,sin_validar,validado,Validación completada
2024-06-23T10:05:30,validar,admin,2,estado,sin_validar,validado,Revisado sin cambios
2024-06-23T11:30:00,modificar,maria_rh,3,puesto,Teccnico,Técnico Académico,Corrección OCR
2024-06-23T11:30:00,modificar,maria_rh,3,estado,pendiente_revision,validado,Validación tras corrección
2024-06-23T12:15:00,rechazar,maria_rh,4,estado,pendiente_revision,rechazado,"Fecha inicio > fin"
2024-06-23T13:00:00,exportar,admin,null,null,null,null,Exportación de datos a sistema externo
```

### 4.1 Columnas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `timestamp` | DateTime ISO | Cuándo sucedió (UTC) |
| `accion` | String (Enum) | crear, validar, modificar, rechazar, exportar, etc. |
| `usuario` | String | Usuario que realizó acción |
| `id_contrato` | Integer | ID del contrato afectado (null si es operación global) |
| `campo` | String | Campo modificado |
| `valor_anterior` | String | Valor antes del cambio |
| `valor_nuevo` | String | Valor después del cambio |
| `detalles` | String | Notas adicionales |

### 4.2 Acciones Permitidas

```
crear              # Nuevo contrato creado
modificar          # Campo editado manualmente
validar            # Contrato validado (sin cambios)
rechazar           # Contrato rechazado
exportar           # Datos exportados a sistema externo
sincronizar        # Sincronización con nube
eliminar           # Contrato eliminado
restaurar          # Contrato restaurado de backup
revalidar          # Re-validación después de cambio
falloocr           # Error durante OCR
```

---

## 5. Importación desde Otros Sistemas

### 5.1 Formato Compatible (Plantilla de Importación)

Si tienes datos en otro sistema y deseas importarlos a REDOCNIZER:

```csv
cedula,nombre,puesto,fecha_inicio,fecha_fin,calendario,dedicacion,departamento,nivel_salarial
123.456.789,García López Juan,Profesor Titular,2024-01-15,2024-12-31,2024A,Tiempo Completo,Ciencias Exactas,Nivel A
987.654.321,Pérez Rodríguez María,Auxiliar de Docencia,2024-02-01,2024-06-30,2024A,Por Horas,Ingeniería,Nivel B
```

**Nota**: No incluir columnas `id`, `estado`, `fecha_procesamiento`, `confianza_ocr`, `error_ocr` — se completan automáticamente.

### 5.2 Script de Importación (Python)

```python
import pandas as pd
from services.csv_service import CSVService

# Cargar archivo importación
df_importacion = pd.read_csv('importacion.csv', encoding='utf-8')

# Validar columnas requeridas
columnas_requeridas = ['cedula', 'nombre', 'puesto', 'fecha_inicio', 'fecha_fin']
if not all(col in df_importacion.columns for col in columnas_requeridas):
    raise ValueError("Faltan columnas requeridas")

# Crear servicio
csv_service = CSVService('C:\\REDOCNIZER_DATA')

# Importar por calendario
for calendario in df_importacion['calendario'].unique():
    df_calendario = df_importacion[df_importacion['calendario'] == calendario]
    csv_service.importar_lote(df_calendario, calendario)

print("Importación completada")
```

---

## 6. Exportación a Otros Formatos

### 6.1 Exportación a Excel

```python
import pandas as pd
from openpyxl.styles import PatternFill, Font

# Leer CSV
df = pd.read_csv('contratos.csv', encoding='utf-8-sig')

# Crear Excel con múltiples hojas
with pd.ExcelWriter('contratos_2024A.xlsx', engine='openpyxl') as writer:
    # Hoja 1: Datos principales
    df.to_excel(writer, sheet_name='Contratos', index=False)
    
    # Hoja 2: Validaciones
    df_validacion = pd.read_csv('validacion.csv', encoding='utf-8-sig')
    df_validacion.to_excel(writer, sheet_name='Validaciones', index=False)
    
    # Formato
    workbook = writer.book
    worksheet = writer.sheets['Contratos']
    fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    font = Font(bold=True, color='FFFFFF')
    for cell in worksheet[1]:
        cell.fill = fill
        cell.font = font
```

### 6.2 Exportación a JSON

```python
import json
import pandas as pd

df = pd.read_csv('contratos.csv', encoding='utf-8-sig')
datos = df.to_dict('records')

with open('contratos.json', 'w', encoding='utf-8') as f:
    json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
```

### 6.3 Exportación a Base de Datos SQL

```python
import sqlite3
import pandas as pd

df = pd.read_csv('contratos.csv', encoding='utf-8-sig')

# Conectar a SQLite
conn = sqlite3.connect('contratos.db')

# Crear tabla y cargar datos
df.to_sql('contratos', conn, if_exists='replace', index=False)

conn.close()
print("Datos exportados a contratos.db")
```

---

## 7. Respaldos y Recuperación

### 7.1 Respaldos Automáticos

REDOCNIZER crea respaldos automáticos:

```
REDOCNIZER_DATA/
└── contratos/
    └── 2024A/
        ├── contratos.csv (archivo actual)
        ├── backup_20240623_090000.csv
        ├── backup_20240623_120000.csv
        ├── backup_20240623_150000.csv
        └── backup_20240623_180000.csv
```

**Política de respaldos**:
- Frecuencia: Cada 3 horas
- Retención: Últimos 7 días
- Total almacenamiento: ~2-5 MB por calendario

### 7.2 Restaurar desde Backup

```python
import shutil
from datetime import datetime

def restaurar_backup(calendario, fecha_backup):
    """Restaurar desde backup específico"""
    
    archivo_respaldo = f"contratos/backup_{fecha_backup}.csv"
    archivo_actual = f"contratos/{calendario}/contratos.csv"
    
    if os.path.exists(archivo_respaldo):
        # Crear backup del actual antes de restaurar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy(archivo_actual, f"contratos/backup_{timestamp}_priorrestauracion.csv")
        
        # Restaurar
        shutil.copy(archivo_respaldo, archivo_actual)
        print(f"Restaurado: {archivo_respaldo}")
    else:
        print(f"Backup no encontrado: {archivo_respaldo}")

# Uso
restaurar_backup('2024A', '20240623_120000')
```

---

## 8. Integridad y Validación de Datos

### 8.1 Script de Validación de CSV

```python
import pandas as pd
from datetime import datetime

def validar_csv(archivo):
    """Validar integridad de archivo CSV"""
    
    errores = []
    
    try:
        df = pd.read_csv(archivo, encoding='utf-8-sig')
    except Exception as e:
        return [f"Error al leer archivo: {e}"]
    
    # Validar columnas requeridas
    columnas_requeridas = ['id', 'cedula', 'nombre', 'puesto', 'fecha_inicio', 'fecha_fin']
    for col in columnas_requeridas:
        if col not in df.columns:
            errores.append(f"Columna faltante: {col}")
    
    # Validar filas
    for idx, row in df.iterrows():
        # Cédula
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}$', str(row['cedula'])):
            errores.append(f"Fila {idx+2}: Cédula inválida: {row['cedula']}")
        
        # Fechas
        try:
            inicio = pd.to_datetime(row['fecha_inicio'])
            fin = pd.to_datetime(row['fecha_fin'])
            if inicio >= fin:
                errores.append(f"Fila {idx+2}: Fecha inicio >= fin")
        except:
            errores.append(f"Fila {idx+2}: Formato de fecha inválido")
        
        # Nombre (mínimo 20 caracteres)
        if len(str(row['nombre'])) < 20:
            errores.append(f"Fila {idx+2}: Nombre muy corto")
    
    if errores:
        print("❌ Errores encontrados:")
        for error in errores:
            print(f"   - {error}")
    else:
        print("✅ CSV válido")
    
    return errores

# Uso
validar_csv('contratos.csv')
```

---

## 9. Preguntas Frecuentes (FAQ)

### P: ¿Puedo editar el CSV directamente en Excel?

R: Sí, pero con cuidado:
- No cambies el orden de columnas
- Usa UTF-8 con BOM
- Respeta formatos (fechas YYYY-MM-DD, cédula XXX.XXX.XXX)
- Después, valida con el script de validación
- Mejor: editar desde REDOCNIZER UI

### P: ¿Cómo fusion múltiples archivos CSV?

R:
```python
import pandas as pd

df1 = pd.read_csv('contratos_2024A.csv', encoding='utf-8-sig')
df2 = pd.read_csv('contratos_2024B.csv', encoding='utf-8-sig')

df_combined = pd.concat([df1, df2], ignore_index=True)
df_combined.to_csv('contratos_combined.csv', index=False, encoding='utf-8-sig')
```

### P: ¿Qué pasa si elimino un archivo CSV?

R: No se puede deshacer. Pero REDOCNIZER tiene respaldos automáticos. Puedes restaurar desde backup en la sección "Configuración → Respaldos".

---

*Última actualización: 23 de junio de 2024*
