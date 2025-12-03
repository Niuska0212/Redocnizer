#  Flujo de Trabajo del Pipeline OCR

##  Resumen del Pipeline Actual (V6)

```
pipe_v6.py (orquestador)
    ↓
1. generador_palabras_realistas.py  → Genera labels.txt (200k items)
    ↓
2. dataset_creator_v2.py           → Genera imágenes PNG desde labels.txt  
    ↓
3. train.py                        → Entrena el modelo OCR
```

---

##  Paso a Paso Detallado

### **PASO 1: Generar Labels (Palabras Realistas)**

**Script:** `generador_palabras_realistas.py`

**Qué hace:**
- Genera un archivo `labels.txt` con palabras/textos variados (200,000 líneas).
- Usa diccionarios externos (opcional pero recomendado).
- Aplica variaciones (mayúsculas, puntuación, etc.).
- **Mejora V6**: Genera URLs largas y frases de hasta 64 caracteres.
- Genera pseudopalabras con Markov.
- Añade casos difíciles OCR (l/I/1, O/0).

**Comando actual en `pipe_v6.py`:**
```python
subprocess.run(
    [sys.executable, "generador_palabras_realistas.py", 
     "-c", str(dataset_size),  # 200,000 por defecto
     "-o", str(labels_path)],   # dataset_entrenamiento/dataset/labels.txt
    cwd=str(generador_dir)
)
```

---

### **PASO 2: Crear Imágenes desde Labels (Tight Generation)**

**Script:** `dataset_creator_v2.py`

**Qué hace:**
- Lee `labels.txt`
- Genera imágenes PNG (una por cada línea)
- **Tight Images**: Genera la imagen al tamaño exacto del texto (sin ancho mínimo).
- **Soporte V6**: Maneja textos largos sin truncar (hasta 64 chars).
- Aplica augmentation (rotación, blur, ruido, etc.)
- Guarda en `dataset_entrenamiento/dataset/`

**Comando actual en `pipe_v6.py`:**
```python
subprocess.run([
    sys.executable, "dataset_creator_v2.py",
    "--archivo-palabras", str(labels_path),  # labels.txt
    "--limpiar",                             # Borra dataset anterior
    "--output", str(images_dir),             # dataset_entrenamiento/dataset/
    "--fonts", str(fonts_dir)                # fonts/
], cwd=str(dataset_creator_dir))
```

---

### **PASO 3: Entrenar Modelo (Smart Padding)**

**Script:** `train.py`

**Qué hace:**
- Lee `config.yaml` para configuración
- **Dataloader Optimizado (`OCRDatasetOptimized`)**:
    - Carga imágenes de tamaño variable desde disco o RAM.
    - Aplica **Smart Padding** on-the-fly: Redimensiona a 32px de alto manteniendo aspect ratio y rellena centrado hasta 512px.
- Entrena modelo CRNN desde cero
- Guarda checkpoints y logs

**Configuración actual (`config.yaml`):**
```yaml
dataset:
  dataset_size: 200000
  fonts_dir: fonts
  images_dir: dataset_entrenamiento/dataset
  labels_path: dataset_entrenamiento/dataset/labels.txt
  max_text_length: 64

model:
  input_width: 512 # Ancho fijo para el modelo
```

---

##  Modificaciones Necesarias

### **1. Actualizar `pipe_limpio.py`** (RECOMENDADO)

Añadir soporte para diccionarios externos:

```python
# Líneas 68-98 (PASO 1a)
print("Generando palabras realistas...")

# Rutas a diccionarios
dict_es_path = base_dir / "diccionarios" / "spanish.txt"
dict_en_path = base_dir / "diccionarios" / "english.txt"

# Construir comando
cmd = [
    sys.executable, "generador_palabras_realistas.py", 
    "-c", str(dataset_size), 
    "-o", str(labels_path)
]

# Añadir diccionarios si existen
if dict_es_path.exists():
    cmd.extend(["--dict-es", str(dict_es_path)])
if dict_en_path.exists():
    cmd.extend(["--dict-en", str(dict_en_path)])

result = subprocess.run(cmd, cwd=str(generador_dir))
```

### **2. (Opcional) Limpiar Import en `dataset_creator_v2.py`**

Reemplazar líneas 34-42:
```python
# ANTES (ROMPE):
try:
    from generador_palabras_realistas import (
        generar_palabras_realistas  # ← NO EXISTE
    )
    generar_palabras = generar_palabras_realistas
    GENERADOR_DISPONIBLE = True
except ImportError:
    GENERADOR_DISPONIBLE = False

# DESPUÉS (OK):
# El import no es necesario ya que usamos archivo de palabras
GENERADOR_DISPONIBLE = False
```

**Nota:** Esto no afecta tu flujo actual porque `pipe_limpio.py` siempre pasa `--archivo-palabras`.

---

##  Cómo Ejecutar el Pipeline Completo

### **Opción A: Pipeline Automático (Recomendado)**

```bash
# Ejecutar todo el pipeline de una vez
python3 pipe_limpio.py
```

**Qué hará:**
1.  Generar 50,000 labels (con diccionarios si modificaste `pipe_limpio.py`)
2.  Crear 50,000 imágenes PNG
3.  Entrenar modelo durante 100 épocas
4.  Guardar checkpoints y logs

---

### **Opción B: Paso a Paso Manual**

```bash
# PASO 1: Generar labels con diccionarios externos
python3 generador_palabras_realistas.py \
  -c 50000 \
  -o dataset_entrenamiento/dataset/labels.txt \
  --dict-es diccionarios/spanish.txt \
  --dict-en diccionarios/english.txt

# PASO 2: Crear imágenes desde labels
python3 dataset_creator_v2.py \
  --archivo-palabras dataset_entrenamiento/dataset/labels.txt \
  --output dataset_entrenamiento/dataset \
  --fonts fonts \
  --limpiar

# PASO 3: Entrenar modelo
python3 train.py
```

---

##  Checklist de Verificación

Antes de ejecutar el pipeline completo:

- [ ] Diccionarios descargados en `diccionarios/`
  - [ ] `spanish.txt` (636K palabras)
  - [ ] `english.txt` (275K palabras)
  
- [ ] Fuentes TTF en directorio `fonts/`
  - Mínimo recomendado: 10-20 fuentes diferentes

- [ ] `config.yaml` configurado correctamente
  - [ ] `dataset_size`: 50000
  - [ ] `epochs`: 100
  - [ ] Rutas correctas

- [ ] (Opcional) `pipe_limpio.py` modificado para usar diccionarios

---

##  Salida Esperada

```
dataset_entrenamiento/
├── dataset/
│   ├── 000000.png        # 50,000 imágenes
│   ├── 000001.png
│   ├── ...
│   └── labels.txt        # 50,000 líneas (filename,texto)
├── checkpoints/
│   ├── model_best.weights.h5
│   └── model_final.weights.h5
└── logs/
    └── training.log
```

---

##  Mejoras vs Versión Anterior

| Aspecto | Antes | Ahora (Con Diccionarios) |
|---------|-------|--------------------------|
| **Vocabulario** | ~100 palabras repetidas | 10,000+ palabras únicas |
| **Pseudopalabras** | Aleatorias impronunciables | Markov (realistas) |
| **Variaciones** | Solo minúsculas | Mayúsculas, puntuación |
| **Casos OCR** | Solo palabras simples | l/I/1, O/0, URLs, IBANs |
| **Contexto** | Palabras aisladas | Frases de 2-4 palabras |

---

## ️ Tiempo Estimado

| Fase | Dataset 50K | Dataset 20K |
|------|-------------|-------------|
| Generar labels | ~5 segundos | ~2 segundos |
| Crear imágenes | ~10-15 min | ~4-6 min |
| Entrenar (100 épocas) | ~2-6 horas* | ~1-3 horas* |

*Depende de GPU/CPU disponible

---

## 🆘 Solución de Problemas

### Error: "No se encontró el diccionario"
```bash
# Verifica que existen los archivos
ls -lh diccionarios/
```

### Error: Import `generar_palabras_realistas`
No afecta si usas `--archivo-palabras`. Puedes ignorarlo o limpiar el código.

### Pocas palabras únicas en el dataset
Aumenta `max_palabras` en la función `cargar_diccionario_externo()` (ya modificado a 1,000,000).
