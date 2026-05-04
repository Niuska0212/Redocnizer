# 📚 Documentación Técnica: Modelo OCR CRNN-CTC (v3)

[](https://www.python.org/)
[](https://www.tensorflow.org/)
[](https://www.google.com/search?q=LICENSE)

Este documento detalla el **Pipeline Completo** del sistema de Reconocimiento Óptico de Caracteres (OCR), desde la generación de datos realistas hasta el entrenamiento y la evaluación del modelo **CRNN (Convolutional Recurrent Neural Network) con CTC Loss**.


## 📋 Tabla de Contenidos

1.  [**Introducción: La Arquitectura CRNN-CTC**](https://www.google.com/search?q=%231-introducci%C3%B3n-la-arquitectura-crnn-ctc)
      * [1.1 ¿Por qué Usar CRNN-CTC?](https://www.google.com/search?q=%2311-por-qu%C3%A9-usar-crnn-ctc)
2.  [**Pipeline de Generación de Dataset Realista (`Generador.py`)**](https://www.google.com/search?q=%232-pipeline-de-generaci%C3%B3n-de-dataset-realista-generadorpy)
      * [2.1 Enfoque de Generación](https://www.google.com/search?q=%2321-enfoque-de-generaci%C3%B3n)
      * [2.2 Creación de Imágenes con Varianza Óptica](https://www.google.com/search?q=%2322-creaci%C3%B3n-de-im%C3%A1genes-con-varianza-%C3%B3ptica)
3.  [**Arquitectura de la Red: El Modelo CRNN (`entrenamientoV3.py`)**](https://www.google.com/search?q=%233-arquitectura-de-la-red-el-modelo-crnn-entrenamientov3py)
      * [3.1 Preprocesamiento y Data Augmentation](https://www.google.com/search?q=%2331-preprocesamiento-y-data-augmentation)
      * [3.2 Extractor de Características (CNN Encoder)](https://www.google.com/search?q=%2332-extractor-de-caracter%C3%ADsticas-cnn-encoder)
      * [3.3 Modelador de Secuencia (BiLSTM Decoder)](https://www.google.com/search?q=%2333-modelador-de-secuencia-bilstm-decoder)
      * [3.4 Función de Pérdida CTC](https://www.google.com/search?q=%2334-funci%C3%B3n-de-p%C3%A9rdida-ctc)
4.  [**Entrenamiento y Evaluación**](https://www.google.com/search?q=%234-entrenamiento-y-evaluaci%C3%B3n)
      * [4.1 Entrenando la Red con Callbacks](https://www.google.com/search?q=%2341-entrenando-la-red-con-callbacks)
      * [4.2 Decodificación y Métricas Finales](https://www.google.com/search?q=%2342-decodificaci%C3%B3n-y-m%C3%A9tricas-finales)

-----

## 1\. 🚀 Introducción: La Arquitectura CRNN-CTC

El modelo es una solución de **Aprendizaje Profundo *End-to-End*** diseñada para leer secuencias de texto directamente desde imágenes.

### 1.1 ¿Por qué Usar CRNN-CTC?

Esta arquitectura es la opción estándar para el OCR a nivel de palabra porque combina tres componentes clave para manejar imágenes y secuencias de longitud variable.

| Componente | Función | Beneficio |
| :--- | :--- | :--- |
| **CNN** (Extractor de Features) | Extrae características visuales de la imagen. | Identifica patrones como bordes y formas de letras. |
| **RNN (BiLSTM)** (Modelador de Secuencia) | Modela las *features* como una secuencia de tiempo. | Captura el **contexto** de la palabra (p. ej., 'q' siempre seguido de 'u'). |
| **CTC Loss** (Función de Pérdida) | Permite alinear la secuencia de predicción con la etiqueta real. | Elimina la necesidad de segmentar cada carácter de la imagen. |

-----

## 2\. ⚙️ Pipeline de Generación de Dataset Realista (`Generador.py`)

El script de generación de datos es crucial para la **Generalización** del modelo, pues asegura que el conjunto de entrenamiento sea variado y represente formatos de datos reales (códigos, fechas, números).

### 2.1 Enfoque de Generación

El script utiliza un enfoque basado en **distribución realista** para simular los tipos de datos encontrados en documentos:

```python
def generar_dataset_realista(cantidad: int = 1000, distribucion: Dict[str, float] = None, seed: int = None) -> List[str]:
    # Define la proporción de tipos de datos para simular un documento real.
    distribucion = {
        'palabras_espanol': 0.35,   # Palabras comunes
        'nombres_propios': 0.15,   # Palabras con mayúsculas
        'fechas': 0.15,           # Ej. 15/03/2023 o 2023-03-15
        'numeros': 0.10,          # Ej. $1.234,50 o +34-91-1234
        'codigos': 0.05,          # Ej. ABC-123 o hJ8Gk9pT
        # ... otros tipos ...
    }
    # ... código para iterar y generar los ítems ...
```

### 2.2 Creación de Imágenes con Varianza Óptica

Se usa **Pillow (PIL)** para generar imágenes, aplicando una variación aleatoria en fuentes, tamaños y colores para simular diversas condiciones de iluminación y captura.

```python
# Fragmento del Generador.py para crear una imagen:

# 1. Seleccionar estilos aleatorios
font_path = random.choice(font_paths)
font_size = random.choice(font_sizes)
bg_color = (random.randint(230, 255),) # Blanco a Gris claro
text_color = (random.randint(0, 50),)  # Negro a Gris oscuro

# 2. Calcular tamaño y crear imagen
img = Image.new('RGB', img_size, color=bg_color)
draw = ImageDraw.Draw(img)

# 3. Dibujar texto con variación
draw.text((x, y), item, font=font, fill=text_color)
img.save(save_path)
```

-----

## 3\. 🏗️ Arquitectura de la Red: El Modelo CRNN (`entrenamientoV3.py`)

El modelo se define en Keras/TensorFlow y está estructurado como un **Encoder-Decoder**.

### 3.1 Preprocesamiento y Data Augmentation

Las capas de *Data Augmentation* se aplican **en tiempo real** justo al inicio del modelo para forzar la robustez.

```python
input_img = Input(shape=(img_height, img_width, 1), name='input_img')

# Capas de Data Augmentation en tiempo real
x = RandomRotation(factor=0.05, name='aug_rotation')(input_img)
x = RandomZoom(height_factor=0.1, width_factor=0.1, name='aug_zoom')(x)
x = RandomTranslation(height_factor=0.1, width_factor=0.1, name='aug_translation')(x)
x = tf.keras.layers.Rescaling(1./255)(x) # Normalización
```

### 3.2 Extractor de Características (CNN Encoder)

Esta sección reduce la imagen $2D$ a una secuencia de *feature vectors* $1D$ mediante convoluciones y *pooling*.

| Capa | Tipo y Configuración | Feature Maps (H x W) | Función |
| :--- | :--- | :--- | :--- |
| **Conv 1, 2** | `Conv2D(64/128), BN, ReLU, MaxPool(2,2)` | $8 \times 64$ | Extracción de bajo nivel y reducción de altura. |
| **Conv 3, 4** | `Conv2D(256/512), BN, ReLU` | $4 \times 32$ | Extracción de alto nivel de las características del texto. |
| **MaxPool 3** | `MaxPool(2,2)` | $4 \times 32$ | Última reducción dimensional (reduce ancho de 256 a 32). |
| **Reshape** | `Reshape(32, 4 * 512)` | **32 x 2048** | Prepara la secuencia temporal para la RNN (32 pasos de tiempo). |

```python
# Fragmento de la CNN Encoder y Reshape:
x = Conv2D(64, (3, 3), activation='relu', padding='same', name='conv_1')(x)
x = BatchNormalization(name='bn_1')(x)
x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x)

# ... otras capas Conv2D y MaxPool ...

# La clave: El Reshape para la RNN
x = Reshape(target_shape=(output_sequence_length, (img_height // 8) * 512), name='reshape')(x) 
# output_sequence_length es 32 (256 / (2.3.0) )
```

### 3.3 Modelador de Secuencia (BiLSTM Decoder)

Dos capas **Bidirectional LSTM** procesan la secuencia de 32 pasos, permitiendo que el modelo considere el contexto de un carácter a su izquierda y derecha.

```python
# Capas recurrentes BiLSTM:
x = Bidirectional(LSTM(256, return_sequences=True, dropout=0.3, name='lstm_1'))(x)
x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.3, name='lstm_2'))(x)

# Capa de salida: 
# Genera las probabilidades para cada carácter + el token BLANK (num_chars + 1)
output = Dense(num_chars + 1, activation='softmax', name='output')(x)
# Output: Tensor (Batch_size, 32, num_chars + 1)
```

### 3.4 Función de Pérdida CTC

La pérdida CTC se define como una capa **Lambda** personalizada en Keras, permitiendo que el modelo se entrene con etiquetas de longitud variable.

```python
def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    # K.ctc_batch_cost es la implementación de la pérdida CTC de Keras
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# Definición de la capa y compilación:
ctc_loss = tf.keras.layers.Lambda(ctc_loss_lambda_func, output_shape=(1,), name='ctc_loss')(
    [y_true, output, input_length, label_length]
)

modelo_entrenamiento.compile(optimizer=Adam(learning_rate=1e-4), 
    loss={'ctc_loss': lambda y_true, y_pred: y_pred}) 
# El loss es una función lambda dummy, ya que el cálculo real se hace en la capa 'ctc_loss'.
```

-----

## 4\. 📈 Entrenamiento y Evaluación

### 4.1 Entrenando la Red con Callbacks

El entrenamiento utiliza *callbacks* estándar para asegurar la estabilidad y eficiencia, como `EarlyStopping` y `ReduceLROnPlateau`.

```python
# Fragmento del main en entrenamientoV3.py

history = modelo_entrenamiento.fit(
    x=[X_train, y_train, input_length_train, label_length_train], # Datos de entrada
    y=np.zeros(len(X_train)),  # y_dummy
    validation_data=([X_test, y_test, input_length_test, label_length_test], np.zeros(len(X_test))),
    epochs=200, 
    batch_size=32,
    callbacks=[early_stopping, reduce_lr, word_accuracy_callback],
    verbose=1
)
```

### 4.2 Decodificación y Métricas Finales

Para obtener la palabra final a partir de las predicciones de la RNN, se usa la función `K.ctc_decode` en el modelo de inferencia.

```python
def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    # Aplica el decodificador greedy (o beam search) a las probabilidades de secuencia
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    for seq in K.get_value(results):
        # Mapea los índices de regreso a caracteres
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

# Métricas clave:
# 1. Word Accuracy: Coincidencia exacta de la palabra predicha.
# 2. Distancia de Levenshtein (CER): Tasa de Error de Carácter.

# Guardar el modelo de INFERENCIA
modelo_inferencia = Model(inputs=input_img, outputs=output_layer)
modelo_inferencia.save(os.path.join(ruta_modelos, "keras_cnn_lstm_v3_ctc.h5"))
```