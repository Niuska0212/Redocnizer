# 🏗️ Arquitectura del Modelo OCR: CRNN-CTC (v3)

[](https://www.python.org/)
[](https://www.tensorflow.org/)
[](https://www.google.com/search?q=LICENSE)

Este documento detalla la estructura en capas del modelo de Reconocimiento Óptico de Caracteres (OCR) basado en **Convolutional Recurrent Neural Network (CRNN)** y entrenado con **Connectionist Temporal Classification (CTC) Loss**, tal como se implementa en el script `entrenamientoV3.py`.

-----

## 📋 Tabla de Contenidos

1.   [**Arquitectura General (CRNN)**](https://www.google.com/search?q=%231-arquitectura-general-crnn)
          \* [1.1 Dimensiones de Entrada y Salida](https://www.google.com/search?q=%2311-dimensiones-de-entrada-y-salida)
2.   [**Flujo de Datos y Diagrama de Bloques**](https://www.google.com/search?q=%232-flujo-de-datos-y-diagrama-de-bloques)
          \* [2.1 Diagrama de Bloques Simplificado](https://www.google.com/search?q=%2321-diagrama-de-bloques-simplificado)
          \* [2.2 Seguimiento Capa por Capa (Input: $32 \times 256 \times 1$)](https://www.google.com/search?q=%2322-seguimiento-capa-por-capa-input-32-times-256-times-1)
3.   [**Fase I: Preprocesamiento y Data Augmentation**](https://www.google.com/search?q=%233-fase-i-preprocesamiento-y-data-augmentation)
4.   [**Fase II: Extractor de Características (CNN Encoder)**](https://www.google.com/search?q=%234-fase-ii-extractor-de-caracter%C3%ADsticas-cnn-encoder)
          \* [4.1 Tabla de Resumen de Capas CNN](https://www.google.com/search?q=%2341-tabla-de-resumen-de-capas-cnn)
          \* [4.2 La Capa Crítica de Reshape](https://www.google.com/search?q=%2342-la-capa-cr%C3%ADtica-de-reshape)
5.   [**Fase III: Modelador de Secuencia (BiLSTM Decoder)**](https://www.google.com/search?q=%235-fase-iii-modelador-de-secuencia-bilstm-decoder)
6.   [**Función de Pérdida CTC (Connectionist Temporal Classification)**](https://www.google.com/search?q=%236-funci%C3%B3n-de-p%C3%A9rdida-ctc-connectionist-temporal-classification)

-----

## 1\. 🔍 Arquitectura General (CRNN)

La arquitectura CRNN es un modelo **End-to-End** que combina lo mejor de las redes convolucionales y recurrentes para la clasificación de secuencias basadas en imágenes.

1.  **CNN (Extractor)**: Transforma la imagen 2D en una secuencia de *feature vectors* 1D.
2.  **RNN (Modelador)**: Predice las probabilidades de caracteres sobre la secuencia de *feature vectors*.
3.  **CTC (Función de Pérdida)**: Permite entrenar el modelo sin la necesidad de alinear manualmente cada carácter en la imagen.

### 1.1 Dimensiones de Entrada y Salida

| Dimensión | Valor (Pixels/Pasos) | Descripción |
| :--- | :--- | :--- |
| **Input Image** | `(32, 256, 1)` | Altura (H=32), Ancho (W=256), Canal (Gris=1). |
| **Output Sequence** | `32` | Número de pasos de tiempo (caracteres o *blanks*) que el modelo puede predecir. |
| **Feature Vector Size** | `2048` | Tamaño del vector de características por cada paso de tiempo. |
| **Vocabulary Size** | `num_chars + 1` | El número de caracteres únicos + 1 para el *token BLANK* de CTC. |

-----

## 2\. 📊 Flujo de Datos y Diagrama de Bloques

Esta sección detalla cómo el tensor de datos se transforma dimensionalmente a través de las diferentes fases del modelo, desde la imagen $2D$ hasta la secuencia $1D$.

### 2.1 Diagrama de Bloques Simplificado

El modelo CRNN se divide conceptualmente en tres módulos de procesamiento, donde el tensor de datos fluye secuencialmente.

| Bloque | Función | Input Shape | Output Shape |
| :--- | :--- | :--- | :--- |
| **CNN Encoder** | Extracción de features $2D$. | $(32, 256, 1)$ | $(4, 32, 512)$ |
| **Reshape Layer** | Transición de 2D a Secuencia 1D. | $(4, 32, 512)$ | $(32, 2048)$ |
| **BiLSTM Decoder** | Modelado de Secuencia y Predicción CTC. | $(32, 2048)$ | $(32, \text{Vocabulario})$ |

### 2.2 Seguimiento Capa por Capa (Input: $32 \times 256 \times 1$)

Asumiremos un **tamaño de lote (Batch Size)** de $B$. Las dimensiones se describen como: $(B, \text{Altura}, \text{Ancho}, \text{Canales})$ o $(B, \text{Pasos de Tiempo}, \text{Features})$.

| Bloque de Capas | Capas Clave | Operación Dimensional | Tensor Shape de Salida | Propósito |
| :--- | :--- | :--- | :--- | :--- |
| **Entrada** | `Input` | $B \times 32 \times 256 \times 1$ | $(B, 32, 256, 1)$ | Imagen de entrada. |
| **Augmentation** | `RandomRotation, Rescaling` | No cambia dimensiones | $(B, 32, 256, 1)$ | Normalización y aumento de robustez. |
| --- | --- | --- | --- | --- |
| **CNN BLOQUE 1** | `Conv2D(64), MaxPooling2D(2,2)` | $H \downarrow / W \downarrow$ (División por 2) | $(B, 16, 128, 64)$ | Reducción inicial de tamaño. |
| **CNN BLOQUE 2** | `Conv2D(128), MaxPooling2D(2,2)` | $H \downarrow / W \downarrow$ (División por 2) | $(B, 8, 64, 128)$ | Reducción adicional. |
| **CNN BLOQUE 3** | `Conv2D(256)` | *Mantener $H, W$* | $(B, 8, 64, 256)$ | Aumenta profundidad de features. |
| **CNN BLOQUE 4** | `Conv2D(512), MaxPooling2D(2,2)` | $H \downarrow / W \downarrow$ (División por 2) | $(B, 4, 32, 512)$ | Reducción final $H$ y $W$. **Tensor $2D$ final.** |
| --- | --- | --- | --- | --- |
| **Secuenciador** | `Reshape` | Colapsa $H \times C$ en *Features* | **$(B, 32, 2048)$** | Transición crítica a formato secuencia. |
| **RNN BLOQUE 5** | `BiLSTM(256), BiLSTM(128)` | No cambia dimensiones | $(B, 32, 256)$ | Modela el contexto temporal. |
| **Salida CTC** | `Dense (num_chars + 1)` | Colapsa *Features* en Vocabulario | **$(B, 32, \text{Vocabulario})$** | Probabilidades de caracteres por paso. |

-----

## 3\. 🛡️ Fase I: Preprocesamiento y Data Augmentation

Estas capas se ejecutan antes del extractor CNN para aumentar la **robustez** y la capacidad de **generalización** del modelo.

```python
input_img = Input(shape=(img_height, img_width, 1), name='input_img')

# Capas de Data Augmentation en tiempo real
x = RandomRotation(factor=0.05, name='aug_rotation')(input_img)
x = RandomZoom(height_factor=0.1, width_factor=0.1, name='aug_zoom')(x)
x = RandomTranslation(height_factor=0.1, width_factor=0.1, name='aug_translation')(x)
x = tf.keras.layers.Rescaling(1./255)(x) # Normalización
```

| Capa | Configuración | Función |
| :--- | :--- | :--- |
| `RandomRotation` | Factor 0.05 (±2.85 grados) | Simula pequeñas inclinaciones de escaneo. |
| `RandomZoom` | Factor 0.1 | Simula variaciones en el zoom de captura. |
| `RandomTranslation` | Factor 0.1 | Simula desalineaciones del texto. |
| `Rescaling` | `1./255` | Normaliza los valores de píxeles al rango **[0, 1]**. |

-----

## 4\. 🧠 Fase II: Extractor de Características (CNN Encoder)

Esta sección consta de **4 bloques convolucionales** que reducen las dimensiones espaciales de la imagen, extrayendo *features* de texto.

### 4.1 Tabla de Resumen de Capas CNN

| Capa | Tipo | Kernel/Pool | Filtros | Output Shape (H, W, C) | Función |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Input** | | | | (32, 256, 1) | |
| `conv_1` | `Conv2D, BN, ReLU` | (3, 3) | 64 | (32, 256, 64) | Extracción inicial de features. |
| `max_pool_1` | `MaxPooling2D` | (2, 2) | - | **(16, 128, 64)** | Reducción de H y W a la mitad. |
| `conv_2` | `Conv2D, BN, ReLU` | (3, 3) | 128 | (16, 128, 128) | Mayor complejidad de features. |
| `max_pool_2` | `MaxPooling2D` | (2, 2) | - | **(8, 64, 128)** | Reducción de H y W. |
| `conv_3` | `Conv2D, BN, ReLU` | (3, 3) | 256 | (8, 64, 256) | Capacidad de modelado de features. |
| `conv_4` | `Conv2D, BN, ReLU` | (3, 3) | 512 | (8, 64, 512) | Mayor profundidad de canal. |
| `max_pool_3` | `MaxPooling2D` | (2, 2) | - | **(4, 32, 512)** | Reducción final de H. |
| `dropout_cnn` | `Dropout` | - | - | (4, 32, 512) | Regularización. |

```python
# Capas CNN del modelo (Extracto)
x = Conv2D(64, (3, 3), activation='relu', padding='same', name='conv_1')(x)
x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x)
# ...
x = Conv2D(512, (3, 3), activation='relu', padding='same', name='conv_4')(x)
x = MaxPooling2D(pool_size=(2, 2), name='max_pool_3')(x)
```

### 4.2 La Capa Crítica de Reshape

Esta capa es el nexo. Transforma el tensor $2D$ de la CNN en una secuencia $1D$ lista para la RNN.

```python
x = Reshape(target_shape=(output_sequence_length, (img_height // 8) * 512), name='reshape')(x)
x = Dropout(0.3, name='dropout_pre_lstm')(x) 
```

**Mapeo del Reshape:**

  * **Pasos de Tiempo**: El ancho original de **32** se mantiene.
  * **Vector de Features**: La altura (4) y los canales (512) se combinan: **$4 \times 512 = 2048$ features**.
  * **Output Shape para RNN**: **(Batch\_size, 32, 2048)**.

-----

## 5\. 🧠 Fase III: Modelador de Secuencia (BiLSTM Decoder)

Dos capas **Bidirectional LSTM** procesan la secuencia $1D$ de 32 pasos para capturar el contexto de la palabra en ambos sentidos.

```python
x = Bidirectional(LSTM(256, return_sequences=True, dropout=0.3, name='lstm_1'))(x)
x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.3, name='lstm_2'))(x)

output = Dense(num_chars + 1, activation='softmax', name='output')(x)
```

| Capa | Tipo | Unidades | Función |
| :--- | :--- | :--- | :--- |
| `lstm_1` | **Bidirectional LSTM** | 256 | Captura el contexto de secuencia de mayor nivel. |
| `lstm_2` | **Bidirectional LSTM** | 128 | Refina la representación secuencial. |
| `output` | **Dense** (Softmax) | `num_chars + 1` | Genera las probabilidades de caracteres/blank por paso de tiempo. |

-----

## 6\. 📉 Función de Pérdida CTC (Connectionist Temporal Classification)

La pérdida CTC se implementa como una capa `Lambda` personalizada que calcula el costo de alineación entre las predicciones (`output`) y las etiquetas verdaderas (`y_true`).

```python
def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# Capa Lambda en el modelo de entrenamiento
ctc_loss = tf.keras.layers.Lambda(ctc_loss_lambda_func, output_shape=(1,), name='ctc_loss')(
    [y_true, output, input_length, label_length]
)
```

**Nota:** El **Modelo de Inferencia** que se guarda en producción omite esta capa de pérdida.