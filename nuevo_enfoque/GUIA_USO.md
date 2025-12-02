# 📘 Guía de Uso Práctica - Modelo OCR Aether

## Índice

1. [Inicio Rápido](#1-inicio-rápido)
2. [Entrenamiento Paso a Paso](#2-entrenamiento-paso-a-paso)
3. [Inferencia y Predicción](#3-inferencia-y-predicción)
4. [Personalización](#4-personalización)
5. [Ejemplos Avanzados](#5-ejemplos-avanzados)
6. [FAQ](#6-faq)

---

## 1. Inicio Rápido

### 1.1 Instalación en 2 Minutos

```bash
# Clonar repositorio
git clone https://github.com/usuario/modeloOCR_Aether.git
cd modeloOCR_Aether

# Instalar dependencias
pip install -r requirements.txt

# Verificar GPU (opcional pero recomendado)
python -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

### 1.2 Entrenar Modelo en 3 Comandos

```bash
# Pipeline completo: genera dataset + entrena
python pipe_limpio_20k.py

# Esperar ~10 minutos...
# ✅ Modelo entrenado guardado en: dataset_entrenamiento/checkpoints/
```

### 1.3 Evaluar Modelo

```bash
# Test de generalización
python test_generalization.py

# Ver resultados en: test_results/generalization_test_results.csv
```

---

## 2. Entrenamiento Paso a Paso

### 2.1 Paso 1: Preparar Fuentes

```bash
# Crear directorio de fuentes
mkdir -p fonts

# Copiar fuentes .ttf al directorio
cp /path/to/your/fonts/*.ttf fonts/

# Verificar
ls fonts/
# Output: Arial.ttf, Times.ttf, Courier.ttf, ...
```

**Fuentes recomendadas**:
- Arial, Times New Roman, Courier (básicas)
- Helvetica, Verdana (sans-serif)
- Georgia, Garamond (serif)
- Comic Sans (informal)

### 2.2 Paso 2: Generar Palabras

```bash
# Opción A: Usar generador de palabras realistas (RECOMENDADO)
python generador_palabras_realistas.py -c 20000 -o palabras.txt -s 42

# Opción B: Usar tu propio archivo
# Formato: una palabra por línea
cat > palabras.txt << EOF
HOLA
CASA
PERRO
123456
EOF
```

**Opciones del generador**:
```bash
# Más palabras
python generador_palabras_realistas.py -c 50000 -o palabras.txt

# Seed específico (reproducibilidad)
python generador_palabras_realistas.py -c 20000 -s 123 -o palabras.txt

# Sin verbose
python generador_palabras_realistas.py -c 20000 -o palabras.txt --no-verbose
```

### 2.3 Paso 3: Crear Dataset de Imágenes

```bash
# Crear imágenes desde palabras
python dataset_creator_v2.py \
    --archivo-palabras palabras.txt \
    --output ./mi_dataset \
    --fonts ./fonts \
    --limpiar

# Verificar resultado
ls mi_dataset/
# Output: 000000.png, 000001.png, ..., labels.txt
```

**Opciones avanzadas**:
```bash
# Más palabras, sin fechas
python dataset_creator_v2.py \
    --archivo-palabras palabras.txt \
    --palabras 10000 \
    --fechas 0 \
    --output ./dataset_palabras

# Con seed
python dataset_creator_v2.py \
    --archivo-palabras palabras.txt \
    --seed 42 \
    --output ./dataset_reproducible
```

### 2.4 Paso 4: Configurar Entrenamiento

```bash
# Editar config.yaml
nano config.yaml
```

```yaml
dataset:
  labels_path: mi_dataset/labels.txt  # ⬅️ Actualizar
  images_dir: mi_dataset               # ⬅️ Actualizar
  fonts_dir: fonts

model:
  input_height: 32
  input_width: 256
  channels: 1
  vocab_chars: '%+-.\/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÁáéíñóú'
  include_blank: true

training:
  batch_size: 96        # ⬅️ Reducir si OOM
  epochs: 100           # ⬅️ Ajustar según necesidad
  learning_rate: 0.001
  warmup_epochs: 3
  checkpoint_dir: checkpoints  # ⬅️ Donde guardar modelo
  logs_dir: logs
```

### 2.5 Paso 5: Entrenar

```bash
# Entrenar desde cero
python train.py

# Con GPU, toma ~10 min para 20K imágenes
# Monitorear progreso en tiempo real
```

**Output esperado**:
```
🚀 ENTRENAMIENTO MODELO CRNN
======================================================================
📂 Dataset: mi_dataset/labels.txt
📂 Imágenes: mi_dataset
🎯 Épocas: 100
📦 Batch size: 96
📈 Learning rate: 0.001

✅ Vocabulario: 75 caracteres
⚡ Usando dataloader OPTIMIZADO
📊 Split: 70% train / 30% validation

✅ Dataset TRAIN: 14000 muestras
✅ Dataset VAL: 6000 muestras
✅ Steps por época (train): 145

✅ Modelo compilado: 4,567,891 parámetros

🔥 Iniciando entrenamiento...
======================================================================
Época 1/100
======================================================================
📈 Learning Rate: 0.000333
  [████████████████████████████████████████] 100.0% | Step 145/145 | Loss:  2.3456

  📊 Loss promedio de la época: 2.3456
  📉 Loss mínimo: 1.8923
  📈 Loss máximo: 3.2145
...
```

### 2.6 Paso 6: Transfer Learning (Opcional)

```bash
# Continuar entrenamiento desde checkpoint
python train.py --pretrained checkpoints/model_best.weights.h5

# Útil para:
# - Fine-tuning con nuevos datos
# - Entrenar más épocas
# - Ajustar hiperparámetros
```

---

## 3. Inferencia y Predicción

### 3.1 Script Básico de Predicción

Crear archivo `predict.py`:

```python
#!/usr/bin/env python3
import yaml
import numpy as np
import tensorflow as tf
from PIL import Image
from pathlib import Path

from utils import build_vocab, labels_to_text, ctc_greedy_decoder
from model import build_crnn

def cargar_modelo(config_path='config.yaml', checkpoint_path=None):
    """Carga modelo entrenado"""
    # Cargar config
    cfg = yaml.safe_load(open(config_path, 'r'))
    mcfg = cfg['model']
    
    # Build vocabulario
    idx2char, char2idx = build_vocab(mcfg['vocab_chars'], include_blank=True)
    num_classes = len(idx2char)
    
    # Build modelo
    model = build_crnn(
        input_shape=(mcfg['input_height'], mcfg['input_width'], mcfg['channels']),
        num_classes=num_classes
    )
    
    # Cargar pesos
    if checkpoint_path is None:
        checkpoint_path = 'dataset_entrenamiento/checkpoints/model_best.weights.h5'
    
    model.load_weights(checkpoint_path)
    print(f"✅ Modelo cargado desde: {checkpoint_path}")
    
    return model, idx2char

def preprocesar_imagen(imagen_path, img_w=256, img_h=32):
    """Preprocesa imagen para el modelo"""
    img = Image.open(imagen_path).convert('L')
    img = img.resize((img_w, img_h), Image.BILINEAR)
    arr = np.array(img).astype(np.float32) / 255.0
    arr = np.expand_dims(arr, axis=-1)  # (32, 256, 1)
    arr = np.expand_dims(arr, axis=0)   # (1, 32, 256, 1)
    return arr

def predecir(modelo, imagen_path, idx2char):
    """Predice texto de una imagen"""
    # Preprocesar
    img = preprocesar_imagen(imagen_path)
    
    # Predicción
    logits = modelo(img, training=False)
    input_lengths = tf.constant([logits.shape[1]], dtype=tf.int32)
    decoded = ctc_greedy_decoder(logits, input_lengths)
    
    # Decodificar
    texto = labels_to_text(decoded[0], idx2char)
    
    return texto

# Uso
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python predict.py <imagen.png>")
        sys.exit(1)
    
    imagen_path = sys.argv[1]
    
    # Cargar modelo
    modelo, idx2char = cargar_modelo()
    
    # Predecir
    texto = predecir(modelo, imagen_path, idx2char)
    
    print(f"\n🔍 Predicción: '{texto}'")
```

**Uso**:
```bash
# Predecir una imagen
python predict.py mi_imagen.png
# Output: 🔍 Predicción: 'HOLA'

# Predecir múltiples imágenes
for img in *.png; do
    echo "Procesando $img:"
    python predict.py "$img"
done
```

### 3.2 Batch Prediction

```python
def predecir_batch(modelo, imagenes_paths, idx2char, batch_size=32):
    """Predice múltiples imágenes eficientemente"""
    predicciones = []
    
    for i in range(0, len(imagenes_paths), batch_size):
        batch_paths = imagenes_paths[i:i+batch_size]
        
        # Cargar batch
        batch_imgs = np.stack([
            preprocesar_imagen(path).squeeze(0) 
            for path in batch_paths
        ])
        
        # Predicción
        logits = modelo(batch_imgs, training=False)
        input_lengths = tf.constant([logits.shape[1]] * len(batch_imgs), dtype=tf.int32)
        decoded = ctc_greedy_decoder(logits, input_lengths)
        
        # Decodificar
        for j in range(len(batch_paths)):
            texto = labels_to_text(decoded[j], idx2char)
            predicciones.append((batch_paths[j], texto))
    
    return predicciones

# Uso
imagenes = ['img1.png', 'img2.png', 'img3.png', ...]
resultados = predecir_batch(modelo, imagenes, idx2char)

for path, texto in resultados:
    print(f"{path}: {texto}")
```

### 3.3 API REST con Flask

Crear `api.py`:

```python
from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import io

# Importar funciones de predicción
from predict import cargar_modelo, preprocesar_imagen, predecir

app = Flask(__name__)

# Cargar modelo al inicio
print("Cargando modelo...")
modelo, idx2char = cargar_modelo()
print("✅ Modelo listo")

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    """
    Endpoint de predicción
    
    Uso:
        curl -X POST -F "image=@imagen.png" http://localhost:5000/predict
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No se envió imagen'}), 400
    
    file = request.files['image']
    
    # Leer imagen
    img_bytes = file.read()
    img = Image.open(io.BytesIO(img_bytes)).convert('L')
    
    # Guardar temporalmente
    temp_path = '/tmp/temp_ocr.png'
    img.save(temp_path)
    
    # Predecir
    texto = predecir(modelo, temp_path, idx2char)
    
    return jsonify({
        'texto': texto,
        'confianza': 0.95  # TODO: calcular confianza real
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'OK', 'modelo': 'CRNN-CTC'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Uso**:
```bash
# Iniciar servidor
python api.py

# En otra terminal:
curl -X POST -F "image=@test.png" http://localhost:5000/predict
# Output: {"texto": "HOLA", "confianza": 0.95}
```

---

## 4. Personalización

### 4.1 Añadir Nuevos Caracteres

**Problema**: Necesitas reconocer emojis o símbolos especiales.

```python
# En config.yaml, actualizar vocab_chars:
vocab_chars: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@#$%&*'
#                                                                           ^^^^^^^^
#                                                                           Nuevos caracteres
```

**IMPORTANTE**: Debes reentrenar el modelo desde cero si cambias el vocabulario.

### 4.2 Ajustar para Palabras Largas

**Problema**: Necesitas reconocer palabras de 30+ caracteres.

```python
# En config.yaml:
model:
  input_width: 512  # ⬅️ Aumentar (antes 256)
  input_height: 32
  
# En model.py, ajustar Reshape:
x = layers.Reshape((-1, 2048))(x)  # ⬅️ 4*512 = 2048 (antes 1024)
```

**Trade-off**: Más ancho = más parámetros = más memoria = más lento

### 4.3 Modelo para Manuscritos

**Requerido**:
1. Dataset de texto manuscrito (ej: IAM Handwriting Database)
2. Fine-tuning desde modelo preentrenado

```python
# 1. Generar dataset manuscrito
# (usar IAM, RIMES, u otro dataset público)

# 2. Fine-tuning
python train.py \
    --pretrained dataset_entrenamiento/checkpoints/model_best.weights.h5 \
    --config config_manuscrito.yaml \
    --learning-rate 0.0001  # ⬅️ LR más bajo para fine-tuning
```

```yaml
# config_manuscrito.yaml
dataset:
  labels_path: manuscrito_dataset/labels.txt
  images_dir: manuscrito_dataset

training:
  learning_rate: 0.0001  # ⬅️ Más bajo
  epochs: 50             # ⬅️ Menos épocas
```

### 4.4 Multi-idioma

**Ejemplo**: Añadir caracteres cirílicos (ruso).

```python
# vocab_chars en config.yaml:
vocab_chars: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя'
#                                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                                                           Alfabeto cirílico
```

**Dataset**: Necesitas generar/recopilar texto en ruso.

---

## 5. Ejemplos Avanzados

### 5.1 OCR en Video (Frame-by-Frame)

```python
import cv2

def ocr_video(video_path, modelo, idx2char, roi=(50, 100, 300, 150)):
    """
    Aplica OCR a región de interés en video
    
    Args:
        video_path: Ruta al video
        modelo: Modelo CRNN cargado
        idx2char: Vocabulario
        roi: (x, y, w, h) región de interés
    """
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extraer ROI
        x, y, w, h = roi
        roi_img = frame[y:y+h, x:x+w]
        
        # Convertir a PIL
        roi_pil = Image.fromarray(cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY))
        
        # Guardar temp
        temp_path = '/tmp/frame_roi.png'
        roi_pil.save(temp_path)
        
        # OCR
        texto = predecir(modelo, temp_path, idx2char)
        
        # Mostrar
        cv2.putText(frame, texto, (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        cv2.imshow('OCR Video', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
    
    cap.release()
    cv2.destroyAllWindows()

# Uso
modelo, idx2char = cargar_modelo()
ocr_video('video.mp4', modelo, idx2char, roi=(100, 50, 400, 100))
```

### 5.2 OCR con Detección Automática de Texto

```python
import pytesseract  # Para detección de ROI

def ocr_con_deteccion(imagen_path, modelo, idx2char):
    """
    1. Detecta regiones de texto con Tesseract
    2. Aplica CRNN a cada región
    """
    img = cv2.imread(imagen_path)
    
    # Detectar cajas de texto
    boxes = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    resultados = []
    
    for i in range(len(boxes['text'])):
        if int(boxes['conf'][i]) > 60:  # Confianza > 60%
            x, y, w, h = boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i]
            
            # Extraer ROI
            roi = img[y:y+h, x:x+w]
            
            # Convertir y guardar
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            roi_pil = Image.fromarray(roi_gray)
            temp_path = f'/tmp/roi_{i}.png'
            roi_pil.save(temp_path)
            
            # OCR con CRNN
            texto = predecir(modelo, temp_path, idx2char)
            
            resultados.append({
                'texto': texto,
                'bbox': (x, y, w, h),
                'confianza': boxes['conf'][i]
            })
    
    return resultados

# Uso
resultados = ocr_con_deteccion('documento.jpg', modelo, idx2char)
for r in resultados:
    print(f"{r['texto']} @ {r['bbox']}")
```

### 5.3 OCR Paralelo (Múltiples GPUs)

```python
import tensorflow as tf

def entrenar_multi_gpu():
    """Entrena usando múltiples GPUs con MirroredStrategy"""
    strategy = tf.distribute.MirroredStrategy()
    
    print(f"Número de GPUs: {strategy.num_replicas_in_sync}")
    
    with strategy.scope():
        # Build modelo dentro del scope
        idx2char, char2idx = build_vocab(vocab_chars, include_blank=True)
        base = build_crnn(input_shape=(32, 256, 1), num_classes=len(idx2char))
        model = CTCPredModel(base, idx2char, char2idx)
        
        optimizer = Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer)
    
    # Entrenar normalmente
    # El modelo se replica automáticamente en todas las GPUs
    for epoch in range(epochs):
        # ... training loop
        pass

# Uso
entrenar_multi_gpu()
```

### 5.4 Exportar a TensorFlow Lite (Mobile)

```python
def exportar_tflite(modelo, output_path='modelo.tflite'):
    """Exporta modelo a TFLite para móviles/edge devices"""
    
    # Convertir a TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(modelo)
    
    # Optimizaciones
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]  # FP16
    
    # Convertir
    tflite_model = converter.convert()
    
    # Guardar
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"✅ Modelo exportado a: {output_path}")
    print(f"   Tamaño: {len(tflite_model) / 1024 / 1024:.2f} MB")

# Uso
modelo, _ = cargar_modelo()
exportar_tflite(modelo.base, 'ocr_mobile.tflite')
```

**Inferencia en Android** (Java):
```java
// Cargar modelo
Interpreter tflite = new Interpreter(loadModelFile("ocr_mobile.tflite"));

// Preparar input
float[][][][] input = new float[1][32][256][1];
// ... llenar con imagen preprocesada

// Inferencia
float[][][] output = new float[1][64][75];  // (batch, time, classes)
tflite.run(input, output);

// Decodificar
String texto = ctcGreedyDecoder(output[0]);
```

---

## 6. FAQ

### 6.1 ¿Cuánto tarda el entrenamiento?

**Con GPU (NVIDIA RTX 3060 / AMD RX 6700 XT)**:
- 20K imágenes, 100 épocas: ~8-10 minutos
- 50K imágenes, 100 épocas: ~20-25 minutos

**Sin GPU (CPU)**:
- 20K imágenes, 100 épocas: ~2-3 horas
- 50K imágenes, 100 épocas: ~5-7 horas

**Recomendación**: Usar GPU para entrenamiento, CPU suficiente para inferencia.

### 6.2 ¿Cuánta memoria RAM necesito?

**Entrenamiento**:
- Con caché en RAM: 8GB mínimo, 16GB recomendado
- Sin caché: 4GB suficiente

**Inferencia**:
- 2GB suficiente

### 6.3 ¿Puedo usar el modelo sin entrenar?

Sí, si tienes un checkpoint pre-entrenado:

```bash
# Descargar checkpoint (si disponible)
wget https://example.com/model_best.weights.h5

# Usar directamente
python predict.py imagen.png
```

### 6.4 ¿Cómo mejoro la precisión?

1. **Más datos**: 50K+ imágenes mejor que 20K
2. **Más variedad**: Diferentes fuentes, tamaños, ruidos
3. **Data augmentation**: Activar todas las transformaciones
4. **Más épocas**: Entrenar hasta que Val Loss se estabilice
5. **Hyperparameter tuning**: Ajustar LR, batch size, dropout

### 6.5 ¿El modelo funciona con texto manuscrito?

**No directamente**. El modelo está entrenado en texto impreso.

Para manuscrito:
1. Fine-tuning en dataset manuscrito (IAM, RIMES)
2. Entrenar desde cero con solo manuscritos
3. Usar modelo híbrido (impreso + manuscrito)

### 6.6 ¿Puedo reconocer múltiples líneas?

**No directamente**. El modelo actual maneja una sola línea.

Para múltiples líneas:
1. Detectar líneas de texto (OpenCV, Tesseract)
2. Aplicar OCR a cada línea individualmente
3. Concatenar resultados

### 6.7 ¿Funciona con imágenes de baja calidad?

**Depende**:
- ✅ Blur moderado: Sí (gracias a augmentation)
- ✅ Ruido bajo-medio: Sí
- ⚠️ Muy pixeladas: Precisión reducida
- ❌ Ilegibles para humanos: No

**Recomendación**: Preprocesar imágenes (aumentar contraste, denoising).

### 6.8 ¿Cómo implemento en producción?

**Opción 1: API REST**
```bash
# Ver ejemplo en sección 3.3
python api.py
```

**Opción 2: Docker**
```dockerfile
FROM tensorflow/tensorflow:2.15.0-gpu

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "api.py"]
```

**Opción 3: TensorFlow Serving**
```bash
# Exportar modelo
modelo.save('saved_model/1/')

# Servir
docker run -p 8501:8501 \
  --mount type=bind,source=/path/to/saved_model,target=/models/ocr \
  -e MODEL_NAME=ocr \
  tensorflow/serving
```

### 6.9 ¿Cómo optimizo la velocidad de inferencia?

1. **TensorRT** (NVIDIA):
```python
from tensorflow.python.compiler.tensorrt import trt_convert as trt

converter = trt.TrtGraphConverterV2(input_saved_model_dir='saved_model/1/')
converter.convert()
converter.save('saved_model_trt/1/')
```

2. **TFLite** (Edge devices):
```python
# Ver ejemplo en sección 5.4
exportar_tflite(modelo)
```

3. **Batch inference**:
```python
# Procesar múltiples imágenes a la vez
predicciones = predecir_batch(modelo, imagenes, idx2char, batch_size=32)
```

### 6.10 ¿Dónde puedo obtener más datos de entrenamiento?

**Datasets públicos**:
- IIIT-5K: Texto en escenas
- Street View Text (SVT): Texto en fotos urbanas
- ICDAR Datasets: Competiciones OCR
- IAM: Manuscritos en inglés
- RIMES: Manuscritos en francés

**Generación sintética** (como este proyecto):
- Usar diferentes fuentes
- Aplicar augmentation agresivo
- Mezclar con datos reales

---

## 7. Recursos Adicionales

### 7.1 Lecturas Recomendadas

- [CRNN Paper](https://arxiv.org/abs/1507.05717) - Paper original de Shi et al.
- [CTC Paper](https://www.cs.toronto.edu/~graves/icml_2006.pdf) - Graves et al.
- [TensorFlow Docs](https://www.tensorflow.org/api_docs/python/tf/nn/ctc_loss) - CTC Loss

### 7.2 Comunidad

- [GitHub Issues](https://github.com/usuario/modeloOCR_Aether/issues) - Reportar bugs
- [Stack Overflow](https://stackoverflow.com/questions/tagged/ocr) - Preguntas OCR

### 7.3 Contacto

- Email: tu_email@ejemplo.com
- GitHub: @usuario

---

**Última actualización**: Noviembre 2025  
**Versión**: 1.0

