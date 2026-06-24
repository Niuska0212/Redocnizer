# ANEXO A: Especificación Técnica Detallada de Campos

## Objetivos del Anexo

Este anexo detalla los campos a extraer de cada contrato académico, incluyendo:
- Definición formal
- Formato esperado
- Reglas de validación
- Ejemplos
- Estrategias de OCR

---

## 1. Matriz de Campos Principales

### 1.1 Campo: Cédula

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `cedula` |
| **Tipo de dato** | String/Numérico |
| **Formato esperado** | `XXX.XXX.XXX` (3 grupos de 3 dígitos) |
| **Longitud** | Exactamente 11 caracteres (9 dígitos + 2 puntos) |
| **Expresión regular** | `^\d{3}\.\d{3}\.\d{3}$` |
| **Ubicación típica** | Encabezado o pie de página |
| **Riesgo OCR** | Medio (confusión 0-O, 1-l) |

**Reglas de Validación**:
```python
def validar_cedula(cedula):
    # Patrón básico
    if not re.match(r'^\d{3}\.\d{3}\.\d{3}$', cedula):
        return False, "Formato inválido"
    
    # Suma de dígitos
    digitos = cedula.replace('.', '')
    suma = sum(int(d) for d in digitos)
    
    # En CUCEI: suma debe ser >0
    if suma == 0:
        return False, "Cédula todas ceros"
    
    return True, "Válido"
```

**Ejemplos**:
- ✅ `123.456.789` - Válido
- ✅ `001.002.003` - Válido (números bajos)
- ❌ `123456789` - Sin puntos
- ❌ `123.456.78` - Solo 2 grupos
- ❌ `12A.456.789` - Contiene letra

**Estrategia OCR**:
1. Buscar patrón numérico-punto repetido
2. Si confianza Tesseract >80%, usar como primaria
3. Si confianza <70%, solicitar validación manual
4. Post-proceamiento: Corregir O→0, l→1 si formato válido

---

### 1.2 Campo: Nombre Completo

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `nombre` |
| **Tipo de dato** | String |
| **Formato esperado** | `APELLIDO, NOMBRE` o `NOMBRE APELLIDO` |
| **Longitud** | 20-100 caracteres |
| **Caracteres permitidos** | Letras (A-Z, a-z), espacios, tildes (á, é, í, ó, ú, ñ), guiones |
| **Expresión regular** | `^[A-ZÀ-Úa-zñ\s\-]{20,100}$` |
| **Ubicación típica** | Línea 1-3, usualmente después de "Nombre:" o similar |
| **Riesgo OCR** | Alto (tildes, espacios múltiples) |

**Reglas de Validación**:
```python
def validar_nombre(nombre):
    # Límites de longitud
    if len(nombre) < 20 or len(nombre) > 100:
        return False, f"Longitud fuera de rango: {len(nombre)}"
    
    # Solo caracteres permitidos
    if not re.match(r"^[A-ZÀ-Úa-zñ\s\-]{20,100}$", nombre):
        return False, "Caracteres inválidos"
    
    # Debe tener al menos 2 palabras
    palabras = nombre.split()
    if len(palabras) < 2:
        return False, "Menos de 2 palabras"
    
    # Cada palabra debe tener >2 caracteres (típicamente)
    if any(len(p) < 2 for p in palabras):
        return False, "Palabras muy cortas"
    
    return True, "Válido"
```

**Ejemplos**:
- ✅ `García López, Juan Carlos` - Válido (formato apellido primero)
- ✅ `María José Pérez Hernández` - Válido (formato nombre primero)
- ✅ `José María López-Martín` - Válido (con guión)
- ❌ `García` - Muy corto (una palabra)
- ❌ `María123` - Contiene números
- ❌ `José @ López` - Caracteres inválidos

**Estrategia OCR**:
1. Segmentar línea de nombre
2. Aplicar CRNN para cada palabra
3. Corrección de tildes: ñ, á, é, í, ó, ú (a menudo confundidas)
4. Validación de patrón nombre-apellido

---

### 1.3 Campo: Puesto / Cargo

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `puesto` |
| **Tipo de dato** | String (Enum) |
| **Valores válidos** | Profesor, Auxiliar, Técnico, Coordinador, etc. |
| **Longitud** | 10-50 caracteres |
| **Expresión regular** | Varía según valor |
| **Ubicación típica** | Después de "Puesto:" o "Cargo:" |
| **Riesgo OCR** | Bajo-Medio (palabras comunes) |

**Diccionario de Puestos Conocidos**:
```python
PUESTOS_VALIDOS = {
    'Profesor Titular': ['Profesor Titular', 'Prof. Titular', 'PT'],
    'Profesor Asociado': ['Profesor Asociado', 'Prof. Asociado', 'PA'],
    'Profesor Asistente': ['Profesor Asistente', 'Prof. Asistente'],
    'Auxiliar de Docencia': ['Auxiliar de Docencia', 'Auxiliar Docencia'],
    'Técnico Académico': ['Técnico Académico', 'Técnico'],
    'Coordinador': ['Coordinador', 'Coord.'],
    # ... más puestos
}
```

**Reglas de Validación**:
```python
def validar_puesto(puesto):
    puesto_norm = puesto.strip().title()
    
    # Búsqueda en diccionario
    for puesto_valido, variantes in PUESTOS_VALIDOS.items():
        if puesto_norm in variantes or any(v in puesto_norm for v in variantes):
            return True, puesto_valido
    
    # Si no encuentra exacto, buscar por similitud
    for puesto_valido in PUESTOS_VALIDOS.keys():
        if difflib.SequenceMatcher(None, puesto_norm, puesto_valido).ratio() > 0.85:
            return True, puesto_valido
    
    return False, f"Puesto no reconocido: {puesto}"
```

**Ejemplos**:
- ✅ `Profesor Titular` → Reconocido
- ✅ `Prof. Titular` → Reconocido y normalizado a `Profesor Titular`
- ✅ `Auxiliar de Docencia` → Reconocido
- ❌ `Ingeniero Jefe` → No en diccionario
- ⚠️ `Profsor Titular` → Detecta error, sugiere corrección

**Estrategia OCR**:
1. Extrae región donde está el puesto
2. Realiza OCR con CRNN
3. Busca en diccionario (fuzzy matching)
4. Si no encuentra, marca para validación manual

---

### 1.4 Campo: Fecha Inicio Contrato

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `fecha_inicio` |
| **Tipo de dato** | Date (YYYY-MM-DD) |
| **Formatos aceptados** | `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD` |
| **Rango válido** | Entre 1990 y año actual + 1 |
| **Longitud** | 8-10 caracteres |
| **Expresión regular** | `^(0?[1-9]\|[12][0-9]\|3[01])[-\/](0?[1-9]\|1[12])[-\/](\d{4})$` |
| **Ubicación típica** | Sección de "Vigencia" o "Período" |
| **Riesgo OCR** | Medio (confusión de separadores y números) |

**Reglas de Validación**:
```python
def validar_fecha_inicio(fecha_str):
    try:
        # Intentar múltiples formatos
        formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y']
        fecha = None
        
        for fmt in formatos:
            try:
                fecha = datetime.strptime(fecha_str, fmt)
                break
            except ValueError:
                continue
        
        if not fecha:
            return False, "No se puede parsear fecha"
        
        # Validar rango
        if fecha.year < 1990:
            return False, f"Año {fecha.year} antes de 1990"
        if fecha.year > datetime.now().year + 1:
            return False, f"Año {fecha.year} en el futuro"
        
        # Validar que sea antes de fecha_fin (si se valida en conjunto)
        return True, fecha.strftime('%Y-%m-%d')
    
    except Exception as e:
        return False, str(e)
```

**Ejemplos**:
- ✅ `15/01/2024` → `2024-01-15`
- ✅ `2024-01-15` → `2024-01-15`
- ✅ `15-01-24` → `2024-01-15` (con heurística año)
- ❌ `32/01/2024` → Día inválido
- ❌ `15/13/2024` → Mes inválido
- ❌ `15/01/2099` → Año en futuro

**Estrategia OCR**:
1. Buscar patrón de fecha (números-separadores)
2. Aplicar CRNN para cada componente
3. Validar formato y rango
4. Inferir separadores faltantes si es posible
5. Corregir 0→O, 1→l si no afecta validación

---

### 1.5 Campo: Fecha Fin Contrato

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `fecha_fin` |
| **Tipo de dato** | Date (YYYY-MM-DD) |
| **Formatos aceptados** | Igual a fecha_inicio |
| **Rango válido** | Debe ser > fecha_inicio, antes de +2 años de inicio |
| **Ubicación típica** | Sección de "Vigencia" o "Período" |
| **Riesgo OCR** | Medio (igual a fecha_inicio) |

**Reglas de Validación**:
```python
def validar_fecha_fin(fecha_fin_str, fecha_inicio):
    fecha_fin, es_valida = validar_fecha_inicio(fecha_fin_str)
    
    if not es_valida:
        return False, es_valida
    
    # Debe ser posterior a inicio
    if fecha_fin <= fecha_inicio:
        return False, "Fecha fin anterior o igual a inicio"
    
    # No debe ser más de 2 años después del inicio
    diferencia = (fecha_fin - fecha_inicio).days
    if diferencia > 730:  # ~2 años
        return False, f"Duración anómala: {diferencia} días"
    
    return True, fecha_fin.strftime('%Y-%m-%d')
```

**Ejemplos**:
- ✅ `31/12/2024` (si inicio es `15/01/2024`) - Válido
- ❌ `15/01/2024` (igual a inicio) - No permitido
- ❌ `10/01/2024` (antes de inicio) - No permitido
- ❌ `15/01/2026` (más de 2 años después) - Anómalo

---

### 1.6 Campo: Calendario Académico

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `calendario` |
| **Tipo de dato** | String (Enum) |
| **Valores válidos** | `2024A`, `2024B`, `2023A`, `2023B`, etc. |
| **Formato** | `YYYYX` donde X es A o B |
| **Expresión regular** | `^(19\|2[0-9])\d{2}[AB]$` |
| **Ubicación típica** | Nombre de archivo o sección inicial |
| **Riesgo OCR** | Bajo (texto muy distintivo) |

**Reglas de Validación**:
```python
def validar_calendario(calendario):
    if not re.match(r'^(19|2[0-9])\d{2}[AB]$', calendario):
        return False, f"Formato inválido: {calendario}"
    
    año = int(calendario[:4])
    semestre = calendario[4]
    
    # Año debe ser razonable
    if año < 2000 or año > datetime.now().year + 1:
        return False, f"Año {año} fuera de rango"
    
    return True, calendario
```

**Ejemplos**:
- ✅ `2024A` - Válido
- ✅ `2024B` - Válido
- ✅ `2023A` - Válido (año anterior)
- ❌ `2024C` - Semestre inválido
- ❌ `24A` - Año incompleto
- ❌ `2099A` - Año futuro

---

## 2. Matriz de Campos Secundarios (Opcionales)

### 2.1 Campo: Nivel de Dedicación

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `dedicacion` |
| **Tipo de dato** | String (Enum) |
| **Valores válidos** | `Tiempo Completo`, `Medio Tiempo`, `Por Horas` |
| **Ubicación típica** | Sección de términos |
| **Riesgo OCR** | Bajo |

---

### 2.2 Campo: Departamento

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `departamento` |
| **Tipo de dato** | String |
| **Valores válidos** | Departamentos CUCEI (Ciencias Exactas, Ingeniería, etc.) |
| **Longitud** | 15-80 caracteres |
| **Riesgo OCR** | Medio (nombres largos) |

---

### 2.3 Campo: Salario / Nivel Salarial

| Atributo | Valor |
|----------|-------|
| **Nombre técnico** | `nivel_salarial` |
| **Tipo de dato** | String (Enum) |
| **Valores válidos** | `Nivel A`, `Nivel B`, `Nivel C`, etc. |
| **Ubicación típica** | Sección de compensación |
| **Riesgo OCR** | Bajo |

---

## 3. Matriz de Validaciones Cruzadas

### 3.1 Lógica de Coherencia Inter-campos

```python
def validar_coherencia_contrato(contrato):
    errores = []
    
    # 1. Fecha fin debe ser después de inicio
    if contrato['fecha_fin'] <= contrato['fecha_inicio']:
        errores.append("fecha_fin no es posterior a fecha_inicio")
    
    # 2. Calendario debe coincidir con fechas
    año_calendario = int(contrato['calendario'][:4])
    año_inicio = contrato['fecha_inicio'].year
    año_fin = contrato['fecha_fin'].year
    
    if año_inicio > año_calendario or año_fin < año_calendario:
        errores.append(f"Fechas {año_inicio}-{año_fin} no coinciden con calendario {año_calendario}")
    
    # 3. Si dedicación es "Por Horas", duración no debe ser > 1 año
    if contrato['dedicacion'] == 'Por Horas':
        dias = (contrato['fecha_fin'] - contrato['fecha_inicio']).days
        if dias > 365:
            errores.append("Por Horas: duración > 1 año")
    
    # 4. Nombre debe tener al menos una palabra de >3 caracteres
    palabras = contrato['nombre'].split()
    if not any(len(p) > 3 for p in palabras):
        errores.append("Nombre sin palabras significativas")
    
    # 5. Puesto debe ser uno de los válidos
    if contrato['puesto'] not in PUESTOS_VALIDOS:
        errores.append(f"Puesto no reconocido: {contrato['puesto']}")
    
    return len(errores) == 0, errores
```

---

## 4. Matriz de Estrategias de OCR por Campo

| Campo | Estrategia EasyOCR | Preprocesamiento | Validación |
|-------|-------------------|------------------|-----------|
| **Cédula** | Segmentación directa | CLAHE + Denoising | Regex + Checksum |
| **Nombre** | Lectura completa | CLAHE moderado | Longitud + Chars válidos |
| **Puesto** | Lectura por línea | CLAHE estándar | Diccionario + Fuzzy |
| **Fecha Inicio** | Lectura de bloque | CLAHE + aumento brillo | Parse + Rango |
| **Fecha Fin** | Lectura de bloque | CLAHE + aumento brillo | Parse + Coherencia |
| **Calendario** | Lectura directa | CLAHE mínimo | Regex + Año |

---

## 5. Tabla de Caracteres Especiales Frecuentes

| Carácter | Confusión EasyOCR | Forma Correcta | Estrategia |
|----------|-------------------|----------------|-----------|
| ñ | n (frecuente) | ñ | Corrección post-OCR |
| á | a (ocasional) | á | CLAHE mejora detección |
| é | e (raro) | é | CLAHE mejora detección |
| 0 | O (frecuente) | 0 | Corrección contextual si en cédula |
| 1 | l/I (frecuente) | 1 | Corrección contextual si en fechas |
| . | , (ocasional) | . | Regex detecta patrón correcto |
| - | _ (raro) | - | CLAHE preserva bordes |
| / | \ (muy raro) | / | Validación de formato |

---

## 6. Tabla de Casos de Prueba Mínimos

| Campo | Caso Válido | Caso Inválido | Caso Límite (CLAHE crítico) |
|-------|-------------|---------------|--------------------------|
| Cédula | `123.456.789` | `123456789` | Cédula con fondo gris oscuro |
| Nombre | `Juan García López` | `Juan` | Nombre manuscrito claro |
| Puesto | `Profesor Titular` | `Ingeniero Jefe` | Puesto en tinta tenue |
| F. Inicio | `15/01/2024` | `32/01/2024` | Fecha bajo sello/anotación |
| F. Fin | `31/12/2024` | `15/01/2024` | Fecha baja resolución |
| Calendario | `2024A` | `2024C` | Calendario en esquina oscura |

---

*Última actualización: 23 de junio de 2024*
