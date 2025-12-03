#  Documentación Técnica Detallada - Modelo OCR Aether

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Arquitectura del Modelo](#2-arquitectura-del-modelo)
3. [Fundamentos Teóricos](#3-fundamentos-teóricos)
4. [Implementación Detallada](#4-implementación-detallada)
5. [Pipeline de Datos](#5-pipeline-de-datos)
6. [Proceso de Entrenamiento](#6-proceso-de-entrenamiento)
7. [Data Augmentation](#7-data-augmentation)
8. [Optimizaciones de Rendimiento](#8-optimizaciones-de-rendimiento)
9. [Evaluación y Métricas](#9-evaluación-y-métricas)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Introducción

### 1.1 ¿Qué es OCR?

**OCR (Optical Character Recognition)** es la tecnología que permite convertir diferentes tipos de documentos (imágenes escaneadas, fotos de documentos, texto en escenas) en datos de texto editables y buscables.

### 1.2 ¿Por qué CRNN + CTC?

**Ventajas de esta arquitectura**:

1. **No requiere segmentación**: No necesita separar caracteres manualmente
2. **Longitud variable**: Acepta texto de cualquier longitud
3. **End-to-End**: Una sola red neuronal para todo el proceso
4. **Robusta**: Maneja variaciones en espaciado, fuente, tamaño
5. **Eficiente**: Más rápida que métodos basados en detección de caracteres

### 1.3 Casos de Uso del Modelo Aether

-  Reconocimiento de palabras aisladas (3-20 caracteres)
-  Texto en español e inglés con acentos
-  Números, fechas, códigos alfanuméricos
-  Texto impreso en múltiples fuentes
- ️ No optimizado para: texto manuscrito, textos muy largos (>20 chars), múltiples líneas

---

## 2. Arquitectura del Modelo

### 2.1 Visión General

```
┌─────────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   Imagen    │ -> │   CNN   │ -> │ Reshape │ -> │   RNN   │ -> │   CTC   │ -> Texto
│ (256x32x1)  │    │ Extrae  │    │ Seq.    │    │ Context │    │ Decoder │
└─────────────┘    │ Features│    │         │    │         │    │         │
                   └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 2.2 Componentes Detallados

#### 2.2.1 Input Layer

**Especificaciones**:
- Dimensiones: `(batch_size, 32, 512, 1)`
- Formato: Escala de grises (1 canal)
- Rango de valores: [0, 1] (normalizado)
- Tipo de dato: `float32`

**Preprocesamiento**:
```python
# Conversión a escala de grises
img = Image.open(path).convert('L')

# Smart Padding (Dataloader)
# 1. Resize proporcional a altura 32
# 2. Pad con fondo blanco hasta ancho 512
# 3. Centrado de la imagen
```

#### 2.2.2 Convolutional Blocks (Arquitectura High-Res V6)

La arquitectura V6 ha sido diseñada específicamente para maximizar la resolución horizontal, permitiendo el reconocimiento de textos largos y densos (URLs, frases).

**Bloque 1**:
```python
x = Conv2D(32, kernel_size=3, padding='same', activation='relu')(x)
x = MaxPool2D(pool_size=(2, 2))(x)
```
- **Input**: (batch, 32, 512, 1)
- **Output**: (batch, 16, 256, 32)
- **Reducción**: Altura / 2, Ancho / 2

**Bloque 2 (High-Res)**:
```python
x = Conv2D(64, kernel_size=3, padding='same', activation='relu')(x)
x = MaxPool2D(pool_size=(2, 1))(x)  # STRIDE (2,1)
```
- **Input**: (batch, 16, 256, 32)
- **Output**: (batch, 8, 256, 64)
- **Reducción**: Altura / 2, **Ancho intacto**.
- **Por qué**: Al no reducir el ancho, preservamos información espacial crítica para caracteres estrechos o muy juntos.

**Bloque 3 (High-Res)**:
```python
x = Conv2D(128, kernel_size=3, padding='same', activation='relu')(x)
x = MaxPool2D(pool_size=(2, 1))(x)  # STRIDE (2,1)
```
- **Input**: (batch, 8, 256, 64)
- **Output**: (batch, 4, 256, 128)
- **Reducción**: Altura / 2, **Ancho intacto**.

**Bloque 4**:
```python
x = Conv2D(256, kernel_size=3, padding='same', activation='relu')(x)
```
- **Input**: (batch, 4, 256, 128)
- **Output**: (batch, 4, 256, 256)

**Resultado Final**:
- El ancho final es **256**.
- Si hubiéramos usado MaxPool(2,2) estándar en todos los bloques, el ancho final sería 64 (512 -> 256 -> 128 -> 64).
- **64 pasos de tiempo** son insuficientes para una URL de 60 caracteres (CTC necesita al menos 2 pasos por caracter para separar repetidos: "hello" -> "h-e-l-l-o").
- **256 pasos de tiempo** permiten teóricamente hasta ~128 caracteres, lo que da un margen cómodo para nuestros 64 caracteres objetivo.

#### 2.2.3 Reshape para Secuencia

```python
x = layers.Permute((2, 1, 3))(x)  # [B, W, H, C]
x = layers.Reshape((-1, 1024))(x)  # [B, W, H*C]
```

**Proceso**:
1. **Permute**: Cambiar de (B, H, W, C) a (B, W, H, C)
   - De: (batch, 4, 256, 256)
   - A: (batch, 256, 4, 256)

2. **Reshape**: Colapsar H y C en una sola dimensión
   - De: (batch, 256, 4, 256)
   - A: (batch, 256, 1024)  donde 1024 = 4 × 256

**Interpretación**:
- **256 time steps** (posiciones horizontales) - **Alta Resolución**
- Cada time step tiene un vector de features de 1024 dimensiones
- Permite leer secuencias muy largas (hasta 60-70 caracteres) con gran precisión

#### 2.2.4 Recurrent Blocks

**LSTM Bidireccional Capa 1**:
```python
x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.2))(x)
```
- **Input**: (batch, 256, 1024)
- **Output**: (batch, 256, 256)  # 128*2 por bidireccional

**LSTM Bidireccional Capa 2**:
```python
x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.2))(x)
```
- **Input**: (batch, 256, 256)
- **Output**: (batch, 256, 256)

...

#### 7.1.4 Smart Padding (Nuevo en V6)

**Problema**: Palabras cortas se deformaban al estirarlas a un ancho fijo (resize simple), y palabras largas perdían detalle al comprimirlas. Esto causaba una discrepancia entre lo que el modelo veía en entrenamiento vs. inferencia.

**Solución Técnica**:
Se implementó una lógica de preprocesamiento personalizada en `dataloader_optimized.py` (método `_get_image`) que preserva la relación de aspecto:

1.  **Carga**: Se lee la imagen original de ancho variable (ej. 100px o 400px).
2.  **Cálculo de Dimensiones**:
    - Se fija la altura objetivo en **32px**.
    - Se calcula el nuevo ancho proporcional: `new_w = int(img_w * (32 / img_h))`.
3.  **Resize Proporcional**: Se redimensiona la imagen a `(new_w, 32)` usando interpolación `BILINEAR` (PIL).
4.  **Canvas**: Se crea un tensor de ceros (fondo negro/blanco según normalización) de tamaño fijo **512x32**.
5.  **Padding Centrado**:
    - Se calcula el offset para centrar: `start_x = (512 - new_w) // 2`.
    - Se inserta la imagen redimensionada en el centro del canvas.
    - Si `new_w > 512`, se hace un resize forzado a 512x32 (caso extremo).

**Resultado**:
- Todas las imágenes entran al modelo con tensor `(512, 32, 1)`.
- **Cero distorsión** de caracteres: Una "a" tiene el mismo ancho en una palabra corta que en una larga.
- Mejora drástica en generalización (Word Accuracy subió de ~60% a >97%).

#### 7.1.5 Variable Tracking (Nuevo en V6)

**Problema**: Caracteres pegados (kerning estrecho) dificultaban la segmentación CTC.

**Solución**:
- Se añade un espaciado aleatorio entre caracteres (`spacing`).
- Rango: -2 a +6 píxeles.
- Ayuda al modelo a distinguir caracteres individuales en fuentes densas.
```

---

## 6. Proceso de Entrenamiento

### 6.1 Configuración

**config.yaml**:
```yaml
training:
  batch_size: 96              # Imágenes por batch
  epochs: 100                 # Número de épocas
  learning_rate: 0.001        # LR inicial
  warmup_epochs: 3            # Épocas de warmup
  gradient_clip_norm: 1.0     # Norm máxima de gradientes
  scheduler:                  # Configuración V6
    enable: true
    monitor: val_loss
    factor: 0.5
    patience: 2
    min_lr: 0.00001
```

### 6.2 Learning Rate Warmup

```python
def lr_schedule(epoch, initial_lr=0.001, warmup_epochs=3):
    if epoch < warmup_epochs:
        # Incremento lineal de LR
        return initial_lr * (epoch + 1) / warmup_epochs
    return initial_lr

# Ejemplo:
# Época 0: 0.001 * 1/3 = 0.000333
# Época 1: 0.001 * 2/3 = 0.000667
# Época 2: 0.001 * 3/3 = 0.001000
# Época 3+: 0.001 (constante)
```

**¿Por qué warmup?**:
- Al inicio, los pesos son aleatorios
- LR alto puede causar inestabilidad
- Warmup permite al modelo "asentarse" primero

### 6.3 Learning Rate Scheduler (ReduceLROnPlateau)

**Implementación V6**:
Se utiliza un scheduler dinámico que monitorea `val_loss`.

```python
class ReduceLROnPlateauManual:
    def step(self, current_loss, current_lr):
        if current_loss < self.best_loss:
            self.best_loss = current_loss
            self.wait = 0
        else:
            self.wait += 1
            if self.wait >= self.patience:
                new_lr = max(current_lr * self.factor, self.min_lr)
                return new_lr
        return current_lr
```

- **Lógica**: Si `val_loss` no mejora en `patience` validaciones (ej. 2 validaciones = 10 épocas), reduce el LR a la mitad.
- **Beneficio**: Ayuda a salir de mínimos locales y refinar la convergencia final.

### 6.4 Loop de Entrenamiento

```python
for epoch in range(epochs):
    # Actualizar learning rate
    new_lr = lr_schedule(epoch)
    model.optimizer.learning_rate.assign(new_lr)
    
    # Training
    epoch_losses = []
    for step in range(steps_per_epoch):
        imgs, labels = next(train_generator)
        result = model.train_step((imgs, labels))
        epoch_losses.append(result['loss'].numpy())
    
    epoch_loss = np.mean(epoch_losses)
    
    # Validación cada 5 épocas
    if (epoch + 1) % 5 == 0:
        val_accuracy, val_cer = validate(model, val_dataset)
        
        # Guardar mejor modelo
        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            model.save_weights('model_best.weights.h5')
    
    # Checkpoint cada 5 épocas
    if (epoch + 1) % 5 == 0:
        model.save_weights(f'model_epoch_{epoch+1:03d}.weights.h5')
```

### 6.4 Validación

```python
def validate(model, val_dataset, num_batches=50):
    total_correct = 0
    total_samples = 0
    total_char_errors = 0
    total_chars = 0
    
    for _ in range(num_batches):
        imgs, labels = next(val_generator)
        
        # Predicción
        logits = model.base(imgs, training=False)
        decoded = ctc_greedy_decoder(logits, input_lengths)
        
        # Métricas
        for i in range(len(imgs)):
            pred = labels_to_text(decoded[i], idx2char)
            true = labels_to_text(labels[i], idx2char)
            
            if pred == true:
                total_correct += 1
            
            # CER
            ed = edit_distance(pred, true)
            total_char_errors += ed
            total_chars += len(true)
            total_samples += 1
    
    accuracy = (total_correct / total_samples) * 100
    cer = (total_char_errors / total_chars) * 100
    
    return accuracy, cer
```

### 6.5 Detección de Colapso

```python
# Detectar si modelo predice vacío (colapso)
if epoch > 10:
    val_imgs, val_labels = next(val_gen)
    logits = model.base(val_imgs[:10], training=False)
    decoded = ctc_greedy_decoder(logits, input_lengths)
    
    empty_count = 0
    for i in range(10):
        pred = labels_to_text(decoded[i], idx2char)
        if len(pred) == 0:
            empty_count += 1
    
    if empty_count >= 8:
        print("️ ALERTA: Posible colapso del modelo")
        print("   Considera detener y ajustar hiperparámetros")
```

**Señales de colapso**:
- Mayoría de predicciones vacías
- Loss se estanca
- Todas las predicciones son "blank"

**Causas comunes**:
- Learning rate muy alto
- Gradientes mal ajustados
- Datos de entrenamiento incorrectos

---

## 7. Data Augmentation

### 7.1 Transformaciones Implementadas

#### 7.1.1 Rotación

```python
def aplicar_rotacion(img, angulo):
    return img.rotate(angulo, expand=True, fillcolor=(255, 255, 255))

# Uso:
angulo = random.uniform(-3, 3)  # ±3 grados
img_rotada = aplicar_rotacion(img, angulo)
```

**Efecto**:
- Simula texto inclinado ligeramente
- Mejora robustez ante escaneos imperfectos

#### 7.1.2 Blur Gaussiano

```python
def aplicar_blur(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius=radius))

# Uso (15% probabilidad):
if random.random() < 0.15:
    radius = random.uniform(0.5, 2.0)
    img = aplicar_blur(img, radius)
```

**Efecto**:
- Simula desenfoque de cámara
- Fotos de documentos en movimiento

#### 7.1.3 Ruido Gaussiano

```python
def aplicar_ruido(img, intensity=0.03):
    img_array = np.array(img)
    noise = np.random.normal(0, 255 * intensity, img_array.shape)
    noisy_img = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_img)

# Uso (20% probabilidad):
if random.random() < 0.20:
    img = aplicar_ruido(img, intensity=0.03)
```

**Efecto**:
- Simula sensor de cámara ruidoso
- Documentos escaneados con baja calidad

#### 7.1.4 Ajuste de Brillo y Contraste

```python
def aplicar_ajustes_color(img, brightness, contrast):
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness)
    
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)
    
    return img

# Uso:
brightness = random.uniform(0.8, 1.2)  # ±20%
contrast = random.uniform(0.9, 1.1)    # ±10%
img = aplicar_ajustes_color(img, brightness, contrast)
```

**Efecto**:
- Simula diferentes condiciones de iluminación
- Documentos fotocopiados (pérdida de contraste)

#### 7.1.5 Shear (Cizallamiento)

```python
def aplicar_shear(img, shear_x, shear_y=0):
    width, height = img.size
    return img.transform(
        (width, height),
        Image.AFFINE,
        (1, shear_x, 0, shear_y, 1, 0),
        fillcolor=(255, 255, 255),
        resample=Image.BICUBIC
    )

# Uso:
shear_amount = random.uniform(-0.2, 0.2)
img = aplicar_shear(img, shear_amount)
```

**Efecto**:
- Simula texto en perspectiva
- Fotos de documentos desde ángulo

### 7.2 Fondos Variables

#### 7.2.1 Fondo Sólido (70%)
```python
bg_value = random.randint(200, 255)
img = Image.new('RGB', (width, height), (bg_value, bg_value, bg_value))
```

#### 7.2.2 Fondo con Gradiente (15%)
```python
def crear_fondo_gradiente(width, height):
    img = Image.new('L', (width, height))
    draw = ImageDraw.Draw(img)
    
    start_color = random.randint(200, 255)
    end_color = random.randint(200, 255)
    
    for y in range(height):
        color = int(start_color + (end_color - start_color) * y / height)
        draw.line([(0, y), (width, y)], fill=color)
    
    return img.convert('RGB')
```

#### 7.2.3 Fondo con Textura (15%)
```python
def crear_fondo_textura(width, height):
    base_color = random.randint(220, 245)
    img = Image.new('RGB', (width, height), (base_color, base_color, base_color))
    
    img_array = np.array(img)
    texture = np.random.normal(0, 5, img_array.shape)
    textured = np.clip(img_array + texture, 0, 255).astype(np.uint8)
    
    return Image.fromarray(textured)
```

### 7.3 Variaciones de Fuente

#### 7.3.1 Simulación de Bold (15%)
```python
# Dibujar texto múltiples veces con offset
draw.text((x, y), texto, font=font, fill=text_color)
if simulate_bold:
    for offset_x, offset_y in [(1, 0), (0, 1), (1, 1)]:
        draw.text((x + offset_x, y + offset_y), texto, font=font, fill=text_color)
```

#### 7.3.2 Simulación de Italic (10%)
```python
# Aplicar shear horizontal
if simulate_italic:
    shear_amount = random.uniform(0.1, 0.2)
    img = aplicar_shear(img, shear_amount)
```

### 7.4 Impacto del Augmentation

**Sin Augmentation**:
- Accuracy en train: 99%
- Accuracy en test: 75%  (overfitting)

**Con Augmentation**:
- Accuracy en train: 96%
- Accuracy en test: 96%  (generalización)

---

## 8. Optimizaciones de Rendimiento

### 8.1 Optimizaciones de GPU

#### 8.1.1 Memory Growth

```python
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
```

**Beneficio**:
- Asigna memoria gradualmente según necesidad
- Previene OOM (Out of Memory)
- Permite múltiples procesos GPU simultáneos

#### 8.1.2 XLA Compilation

```python
os.environ['TF_XLA_FLAGS'] = '--tf_xla_auto_jit=2'
```

**XLA (Accelerated Linear Algebra)**:
- Compila operaciones TensorFlow a código de máquina optimizado
- Fusiona operaciones (kernel fusion)
- Speedup típico: 10-30%

#### 8.1.3 CUDNN Autotune

```python
os.environ['TF_CUDNN_USE_AUTOTUNE'] = '1'
```

**Beneficio**:
- CUDNN busca el algoritmo más rápido para cada operación
- Optimiza convoluciones y RNN
- Primera época más lenta (benchmarking), épocas posteriores más rápidas

### 8.2 Mixed Precision Training (Futuro)

```python
from tensorflow.keras import mixed_precision

policy = mixed_precision.Policy('mixed_float16')
mixed_precision.set_global_policy(policy)
```

**Beneficios**:
- 2-3x speedup en GPUs con Tensor Cores (RTX 20xx+, A100)
- Reduce uso de memoria VRAM (~50%)
- Mantiene precisión con loss scaling

### 8.3 Comparación de Rendimiento

**Configuración de prueba**: 20K imágenes, 10 épocas, batch_size=96

| Optimización | Tiempo/época | GPU Util | VRAM |
|--------------|--------------|----------|------|
| Baseline (Dataloader simple) | 120s | 45% | 4GB |
| + Memory Growth | 120s | 45% | 3GB |
| **+ OCRDatasetOptimized (RAM Cache)** | **45s** | **90%** | **5GB** |
| + XLA + CUDNN | 40s | 95% | 5GB |

**Detalles de OCRDatasetOptimized**:
- **Caché en RAM**: Al iniciar, carga todas las imágenes decodificadas en memoria (si caben). Esto elimina la latencia de I/O de disco durante el entrenamiento.
- **ThreadPoolExecutor**: Utiliza múltiples hilos para la carga inicial y el preprocesamiento on-the-fly.
- **Prefetching**: Usa `tf.data.Dataset.prefetch(AUTOTUNE)` para preparar el siguiente batch mientras la GPU procesa el actual.
- **Eliminación de OpenCV**: Se migró todo el pipeline a **Pillow (PIL)** para evitar bloqueos de GIL y conflictos de threading que tenía `cv2`.

---

## 9. Evaluación y Métricas

### 9.1 Word Accuracy

```python
def word_accuracy(predictions, ground_truths):
    correct = sum(1 for pred, true in zip(predictions, ground_truths) 
                  if pred == true)
    return (correct / len(predictions)) * 100
```

**Interpretación**:
- 100%: Todas las palabras correctas
- 95%: 1 error cada 20 palabras
- 90%: 1 error cada 10 palabras

**Limitación**:
- Muy estricta (un carácter mal → 0% para esa palabra)
- No refleja cuán cerca estuvo la predicción

### 9.2 CER (Character Error Rate)

```python
def character_error_rate(predictions, ground_truths):
    total_chars = sum(len(gt) for gt in ground_truths)
    total_errors = sum(edit_distance(pred, gt) 
                      for pred, gt in zip(predictions, ground_truths))
    return (total_errors / total_chars) * 100
```

**Edit Distance (Levenshtein)**:
```python
def edit_distance(s1, s2):
    # Programación dinámica
    dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    
    for i in range(len(s1) + 1):
        dp[i][0] = i
    for j in range(len(s2) + 1):
        dp[0][j] = j
    
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i-1] == s2[j-1]:
                cost = 0
            else:
                cost = 1
            
            dp[i][j] = min(
                dp[i-1][j] + 1,      # Eliminación
                dp[i][j-1] + 1,      # Inserción
                dp[i-1][j-1] + cost  # Sustitución
            )
    
    return dp[len(s1)][len(s2)]
```

**Ejemplo**:
```
edit_distance("HOLA", "HORA") = 1 (sustituir L por R)
edit_distance("CASA", "CAZA") = 1 (sustituir S por Z)
edit_distance("PERRO", "PIERO") = 2 (sustituir R por I, insertar O)
```

**CER vs Word Accuracy**:
```
Ground Truth: "HOLA"
Prediction:   "HORA"

Word Accuracy: 0% (diferente)
CER:           25% (1 error en 4 caracteres)
```

### 9.3 Accuracy por Longitud

```python
def accuracy_by_length(predictions, ground_truths):
    results = {}
    
    for pred, gt in zip(predictions, ground_truths):
        length = len(gt)
        if length not in results:
            results[length] = {'correct': 0, 'total': 0}
        
        results[length]['total'] += 1
        if pred == gt:
            results[length]['correct'] += 1
    
    # Calcular accuracy
    for length in results:
        correct = results[length]['correct']
        total = results[length]['total']
        results[length]['accuracy'] = (correct / total) * 100
    
    return results
```

**Análisis típico**:
```
Longitud 3-5:  98.5% (palabras cortas, muy precisas)
Longitud 6-8:  96.8% (óptimo del modelo)
Longitud 9-12: 93.2% (mayor dificultad)
Longitud 13+:  88.5% (límite del modelo)
```

### 9.4 Matriz de Confusión de Caracteres

```python
def character_confusion_matrix(predictions, ground_truths, vocab):
    confusion = {c1: {c2: 0 for c2 in vocab} for c1 in vocab}
    
    for pred, gt in zip(predictions, ground_truths):
        # Alinear secuencias
        for pred_char, gt_char in align_sequences(pred, gt):
            if pred_char != gt_char:
                confusion[gt_char][pred_char] += 1
    
    return confusion
```

**Errores comunes**:
```
'O' confundido con '0': 234 veces
'I' confundido con 'l': 189 veces
'S' confundido con '5': 156 veces
```

---

## 10. Troubleshooting

### 10.1 Problemas Comunes

#### 10.1.1 Modelo predice siempre vacío

**Síntomas**:
```
Época 10: Val Accuracy = 0%, todas predicciones vacías
```

**Causas**:
1. Learning rate muy alto
2. Gradientes explosivos
3. Labels incorrectos (índices mal mapeados)

**Solución**:
```python
# Reducir LR
learning_rate = 0.0001  # en vez de 0.001

# Aumentar gradient clipping
gradient_clip_norm = 0.5  # en vez de 1.0

# Verificar vocabulario
print("idx2char:", idx2char)
print("char2idx:", char2idx)
print("Ejemplo label:", text_to_labels("HOLA", char2idx))
```

#### 10.1.2 Loss no disminuye

**Síntomas**:
```
Época 1: Loss = 3.45
Época 10: Loss = 3.42
Época 20: Loss = 3.40
```

**Causas**:
1. Learning rate muy bajo
2. Dataset muy difícil
3. Arquitectura insuficiente

**Solución**:
```python
# Aumentar LR
learning_rate = 0.01

# Simplificar dataset (menos variabilidad)
# Verificar que las imágenes son legibles

# Mostrar batch de entrenamiento
imgs, labels = next(train_generator)
plt.imshow(imgs[0].squeeze(), cmap='gray')
print("Label:", labels_to_text(labels[0], idx2char))
```

#### 10.1.3 Overfitting severo

**Síntomas**:
```
Train Acc: 99.5%
Val Acc:   75.0%
```

**Causas**:
1. Dataset muy pequeño
2. Poco augmentation
3. Modelo muy grande

**Solución**:
```python
# Aumentar augmentation
augmentation = {
    'enable': True,
    'rotation_range': 5,        # aumentar
    'blur_probability': 0.25,   # aumentar
    'noise_probability': 0.30,  # aumentar
}

# Aumentar dropout
dropout = 0.3  # en vez de 0.2

# Reducir épocas
epochs = 50  # en vez de 100
```

#### 10.1.4 GPU Out of Memory

**Síntomas**:
```
ResourceExhaustedError: OOM when allocating tensor
```

**Solución**:
```python
# Reducir batch size
batch_size = 48  # en vez de 96

# Habilitar memory growth
tf.config.experimental.set_memory_growth(gpu, True)

# Limpiar sesión
from tensorflow.keras import backend as K
K.clear_session()
```

#### 10.1.5 Predicciones aleatorias

**Síntomas**:
```
Ground Truth: "HOLA"
Prediction:   "XKQP"
```

**Causas**:
1. Modelo no entrenado
2. Checkpoint corrupto
3. Vocabulario desalineado

**Solución**:
```python
# Verificar que se cargaron los pesos
print("Cargando pesos desde:", checkpoint_path)
model.load_weights(checkpoint_path)
print("Pesos cargados exitosamente")

# Verificar vocabulario
print("Vocabulario del modelo:", idx2char)
print("Vocabulario esperado:", vocab_chars)

# Test en datos simples
simple_test = ["HOLA", "TEST", "123"]
for text in simple_test:
    img = generar_imagen_texto(text, ...)
    pred = predecir(img)
    print(f"{text} -> {pred}")
```

### 10.2 Debugging Tips

#### 10.2.1 Visualizar Activaciones

```python
# Extraer features CNN
cnn_output_model = tf.keras.Model(
    inputs=model.base.input,
    outputs=model.base.get_layer('conv2d_3').output
)

features = cnn_output_model.predict(imgs[:1])
print("CNN features shape:", features.shape)

# Visualizar
plt.figure(figsize=(15, 5))
for i in range(16):
    plt.subplot(2, 8, i+1)
    plt.imshow(features[0, :, :, i], cmap='viridis')
    plt.axis('off')
plt.show()
```

#### 10.2.2 Analizar Gradientes

```python
with tf.GradientTape() as tape:
    logits = model.base(imgs, training=True)
    # ... calcular loss
    
grads = tape.gradient(loss, model.base.trainable_variables)

# Ver magnitudes de gradientes
for i, grad in enumerate(grads):
    if grad is not None:
        grad_norm = tf.norm(grad).numpy()
        print(f"Layer {i}: grad_norm = {grad_norm:.4f}")
```

#### 10.2.3 Probar en Subset Pequeño

```python
# Tomar solo 100 muestras
mini_dataset = dataset.samples[:100]

# Entrenar hasta overfittear completamente
# Si NO puede overfittear 100 samples, hay un bug
for epoch in range(100):
    train_on_mini_dataset()
    if train_acc > 99%:
        print(" Modelo puede aprender (no hay bug)")
        break
```

---

## 11. Conclusiones

### 11.1 Logros del Modelo

 **Alta Precisión**: 96%+ accuracy en palabras realistas
 **Generalización**: No memoriza, aprende patrones
 **Eficiencia**: 150 img/s en inferencia
 **Robusto**: Maneja variaciones de fuente, tamaño, ruido
 **Extensible**: Fácil añadir nuevos caracteres/idiomas

### 11.2 Limitaciones

 **Palabras largas**: Accuracy baja en >15 caracteres
 **Manuscrito**: No entrenado para texto manuscrito
 **Multi-línea**: Solo maneja una línea de texto
 **Orientación**: Asume texto horizontal

### 11.3 Próximos Pasos

1. **Attention Mechanism**: Mejorar accuracy en palabras largas
2. **Transformer**: Reemplazar LSTM con self-attention
3. **Multi-idioma**: Expandir vocabulario (árabe, chino)
4. **Manuscrito**: Fine-tuning en IAM Handwriting DB
5. **Producción**: API REST, TensorRT, Docker

---

**Autor**: Aether  
**Fecha**: Noviembre 2025  
**Versión**: 1.0

