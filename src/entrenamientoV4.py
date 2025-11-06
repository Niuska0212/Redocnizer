import os
import numpy as np
import cv2
import tensorflow as tf
from sklearn.model_selection import train_test_split
import joblib
from difflib import SequenceMatcher

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# =================================================================
# 1. CONFIGURACIÓN INICIAL DE TF Y GPU (¡Optimización 1!)
# =================================================================
# Asegurarse de que TensorFlow utiliza eficientemente la GPU
#gpus = tf.config.experimental.list_physical_devices('GPU')
#if gpus:
#    try:
#        # Habilitar el crecimiento de memoria para evitar que la GPU reserve toda la RAM de golpe
#        for gpu in gpus:
#            tf.config.experimental.set_memory_growth(gpu, True)
#        print(f"GPUs detectadas: {len(gpus)}. Crecimiento de memoria habilitado.")
#    except RuntimeError as e:
#        print(f"Error al configurar la GPU: {e}")
#else:
#    print("Advertencia: No se detectó ninguna GPU. El entrenamiento será lento.")

# Sustituir las importaciones que dan error por el acceso directo a través de tf.keras
Model = tf.keras.models.Model
Input = tf.keras.layers.Input
Conv2D = tf.keras.layers.Conv2D
MaxPooling2D = tf.keras.layers.MaxPooling2D
BatchNormalization = tf.keras.layers.BatchNormalization
Reshape = tf.keras.layers.Reshape
Dense = tf.keras.layers.Dense
Bidirectional = tf.keras.layers.Bidirectional
LSTM = tf.keras.layers.LSTM
Dropout = tf.keras.layers.Dropout
RandomRotation = tf.keras.layers.RandomRotation
RandomZoom = tf.keras.layers.RandomZoom
RandomTranslation = tf.keras.layers.RandomTranslation
Rescaling = tf.keras.layers.Rescaling

EarlyStopping = tf.keras.callbacks.EarlyStopping
ReduceLROnPlateau = tf.keras.callbacks.ReduceLROnPlateau
Callback = tf.keras.callbacks.Callback

K = tf.keras.backend 
Adam = tf.keras.optimizers.Adam
AUTOTUNE = tf.data.experimental.AUTOTUNE # Para tf.data

# -------------------------------
# CONFIGURACIÓN Y PARÁMETROS
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_dataset_palabras = os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")
labels_file_path = os.path.join(ruta_dataset_palabras, "labels.txt")
ruta_modelos = os.path.join(BASE_DIR, "..", "models")
ruta_errores = os.path.join(ruta_modelos, "errores_prediccion_v3")
os.makedirs(ruta_modelos, exist_ok=True)
os.makedirs(ruta_errores, exist_ok=True)

img_height = 32
img_width = 1024 
output_sequence_length = img_width // 4 # 1024 / 4 = 256
BATCH_SIZE = 64 # ¡Optimización 2: Aumento del Batch Size!

# =================================================================
# 2. PROCESAMIENTO DE DATOS (Preparación para tf.data)
# =================================================================

def load_data_paths_and_vocab():
    """Carga las rutas, las etiquetas y construye el vocabulario, sin cargar imágenes."""
    global blank_token_index # Necesitas blank_token_index global para parse_and_preprocess

    with open(labels_file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    imagenes_paths, palabras = [], []
    for line in lines:
        parts = line.split(",", 1)
        if len(parts) == 2:
            path = os.path.join(ruta_dataset_palabras, parts[0])
            # Filtrado básico de existencia de archivo aquí
            if os.path.exists(path):
                imagenes_paths.append(path)
                palabras.append(parts[1])

    if not imagenes_paths:
        print("Error: No hay imágenes válidas para entrenar después de filtrar archivos faltantes.")
        exit()

    print(f"Archivos de datos válidos encontrados: {len(imagenes_paths)}")
    
    # --- Construir vocabulario / mappings para CTC ---
    charset = sorted({ch for w in palabras for ch in w})
    char_to_index = {c: i for i, c in enumerate(charset)}
    index_to_char = {i: c for c, i in char_to_index.items()}
    num_chars = len(charset)
    blank_token_index = num_chars  # índice reservado para el token 'blank' de CTC

    # Convertir palabras a secuencias de índices
    y_seq = [[char_to_index[c] for c in w] for w in palabras]
    
    # Dividir: paths, secuencias de índices, palabras originales
    # train_test_split con 3 inputs devuelve 6 outputs.
    # [1] paths_train, [2] paths_test, [3] seq_idx_train, [4] seq_idx_test, 
    # [5] words_train, [6] words_test
    X_train_paths, X_test_paths, y_train_seq_idx, y_test_seq_idx, _, true_words_test = train_test_split(
        imagenes_paths, y_seq, palabras, test_size=0.2, random_state=42
    )

    # Padding de las secuencias de etiquetas (¡Importante para batching!)
    # Se utiliza la secuencia de índices, no las palabras originales
    y_train_padded = tf.keras.preprocessing.sequence.pad_sequences(y_train_seq_idx, padding='post', value=blank_token_index)
    y_test_padded = tf.keras.preprocessing.sequence.pad_sequences(y_test_seq_idx, padding='post', value=blank_token_index)
    
    # Retornamos los paths y los arrays padded
    return (X_train_paths, y_train_padded), \
        (X_test_paths, y_test_padded, true_words_test), \
        (char_to_index, index_to_char, num_chars, blank_token_index)
    """Carga las rutas, las etiquetas y construye el vocabulario, sin cargar imágenes."""
    with open(labels_file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    imagenes_paths, palabras = [], []
    for line in lines:
        parts = line.split(",", 1)
        if len(parts) == 2:
            path = os.path.join(ruta_dataset_palabras, parts[0])
            # Filtrado básico de existencia de archivo aquí
            if os.path.exists(path):
                imagenes_paths.append(path)
                palabras.append(parts[1])

    if not imagenes_paths:
        print("Error: No hay imágenes válidas para entrenar después de filtrar archivos faltantes.")
        exit()

    print(f"Archivos de datos válidos encontrados: {len(imagenes_paths)}")
    
    # --- Construir vocabulario / mappings para CTC ---
    charset = sorted({ch for w in palabras for ch in w})
    char_to_index = {c: i for i, c in enumerate(charset)}
    index_to_char = {i: c for c, i in char_to_index.items()}
    num_chars = len(charset)
    blank_token_index = num_chars  # índice reservado para el token 'blank' de CTC

    # Convertir palabras a secuencias de índices
    y_seq = [[char_to_index[c] for c in w] for w in palabras]
    
    # Dividir solo los paths y las secuencias de índices
    X_train_paths, X_test_paths, y_train_seq_idx, y_test_seq_idx, true_words_train, true_words_test = train_test_split(
    imagenes_paths, y_seq, palabras, test_size=0.2, random_state=42
    )

    # Padding de las secuencias de etiquetas (¡Importante para batching!)
    y_train_padded = tf.keras.preprocessing.sequence.pad_sequences(y_train_seq_idx, padding='post', value=blank_token_index)
    y_test_padded = tf.keras.preprocessing.sequence.pad_sequences(y_test_seq_idx, padding='post', value=blank_token_index)

    return (X_train_paths, y_train_padded), \
           (X_test_paths, y_test_padded, true_words_test), \
           (char_to_index, index_to_char, num_chars, blank_token_index)

@tf.function
def parse_and_preprocess(image_path, label_sequence, blank_token_index):
    """Función de preprocesamiento para tf.data que corre en el CPU."""
    # Convertir las constantes a tensores para el uso dentro de tf.function
    img_height_t = tf.constant(img_height, dtype=tf.int32)
    img_width_t = tf.constant(img_width, dtype=tf.int32)
    output_seq_len_t = tf.constant(output_sequence_length, dtype=tf.float32)

    # Cargar y decodificar imagen
    img = tf.io.read_file(image_path)
    # Asumimos que las imágenes son JPEG o PNG en escala de grises (channels=1)
    img = tf.image.decode_jpeg(img, channels=1) 
    
    # Redimensionar al tamaño estándar
    img = tf.image.resize(img, [img_height_t, img_width_t], method=tf.image.ResizeMethod.AREA)
    
    # Convertir a float32 y normalizar (0-1). El modelo aplicará la normalización final 1./255.
    img = tf.image.convert_image_dtype(img, tf.float32) 
    
    # Calcular input_length (fijo) y label_length (variable) para CTC
    input_length = tf.expand_dims(output_seq_len_t, axis=0)
    
    # Calcular la longitud real de la etiqueta antes del padding (quitando el blank_token_index)
    label_length_val = tf.reduce_sum(tf.cast(tf.not_equal(label_sequence, blank_token_index), tf.int32))
    label_length = tf.cast(tf.expand_dims(label_length_val, axis=0), tf.float32)

    # El modelo de entrenamiento espera 4 inputs: [img, y_true (padded), input_len, label_len]
    # y 1 output ficticio (0.0) para la pérdida.
    return (img, label_sequence, input_length, label_length), tf.constant(0.0)


@tf.function
def augment_image(image, label_sequence, input_length, label_length):
    """Aplica la aumentación de datos aleatoria a la imagen."""
    # Aplica las transformaciones de Keras (que internamente usan tf.keras.layers)
    # usando una función lambda o re-implementando las capas.

    # Implementación usando tf.image (más directo y compatible con tf.function):
    # Rotación (pequeños ángulos)
    angle = tf.random.uniform(shape=[], minval=-0.05, maxval=0.05) # +/- 5% de rotación en radianes
    image = tf.image.rot90(image, k=tf.cast(angle * 10, tf.int32)) # Aproximación simple si no se quiere usar ImageProjectiveTransformV3

    # Zoom y traslación se manejan con tf.image.pad_to_bounding_box y tf.image.crop_to_bounding_box
    # Para ser breves, usemos solo la rotación más sencilla por ahora, o mantengamos la complejidad.

    # Opción 2: Re-implementar las capas como funciones para usar en el map
    # Esto puede seguir generando warnings si el kernel subyacente de la capa no está optimizado.
    
    # Vamos a usar solo Rescaling, y dejamos que la aumentación se maneje de forma simplificada:
    
    # 1. Rotación simple (menos propensa a while_loop)
    # Usar tf.image.random_crop/flip si su problema es solo el while_loop.
    
    # Por ahora, volvamos a la aumentación que ya tiene definida el tensor:
    image = tf.keras.layers.RandomRotation(factor=0.05, interpolation='nearest')(image)
    image = tf.keras.layers.RandomTranslation(height_factor=0.1, width_factor=0.1, interpolation='nearest')(image)
    image = tf.keras.layers.RandomZoom(height_factor=0.1, width_factor=0.1, interpolation='nearest')(image)

    # Nota: Asegúrese de usar `interpolation='nearest'` o la que prefiera
    # para evitar errores de tipo de datos con la aumentación en tf.function.

    # El dataset mapeado debe devolver la estructura (x, y) esperada por el modelo
    return (image, label_sequence, input_length, label_length), tf.constant(0.0)

# =================================================================
# 3. ARQUITECTURA DEL MODELO CRNN CON CTC
# =================================================================
def build_crnn_model(num_chars):
    """Construye y compila el modelo CRNN con control de tamaño."""
    base_filters = [48, 96, 192, 192]
    lstm_units = [192, 96]

    input_img = Input(shape=(img_height, img_width, 1), name='input_img')

    # AUMENTACIÓN DE DATOS se deja en el modelo para aprovechar la GPU
    # Nota: Keras 3 recomienda usar Rescaling como primera capa
    x = Rescaling(1./255)(input_img) # Normalización


    # Bloque 1 (1024 -> 512)
    x = Conv2D(base_filters[0], (3, 3), activation='relu', padding='same', name='conv_1')(x)
    x = BatchNormalization(name='bn_1')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x)

    # Bloque 2 (512 -> 256)
    x = Conv2D(base_filters[1], (3, 3), activation='relu', padding='same', name='conv_2')(x)
    x = BatchNormalization(name='bn_2')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_2')(x)

    # Bloque 3 (mantiene 256)
    x = Conv2D(base_filters[2], (3, 3), activation='relu', padding='same', name='conv_3')(x)
    x = BatchNormalization(name='bn_3')(x)

    # Bloque 4 (mantiene 256)
    x = Conv2D(base_filters[3], (3, 3), activation='relu', padding='same', name='conv_4')(x)
    x = BatchNormalization(name='bn_4')(x)

    x = Dropout(0.3, name='dropout_cnn')(x)

    # Ajustar reshape
    features_per_step = (img_height // 4) * base_filters[3] 
    x = Reshape(target_shape=(output_sequence_length, features_per_step), name='reshape')(x)
    x = Dropout(0.3, name='dropout_pre_lstm')(x)

    # LSTM bidireccionales
    #x = Bidirectional(LSTM(lstm_units[0], return_sequences=True, dropout=0.3), name='bilstm_1')(x)
    #x = Bidirectional(LSTM(lstm_units[1], return_sequences=True, dropout=0.3), name='bilstm_2')(x)
    # LSTM bidireccionales
    # Al cambiar 'recurrent_activation' se fuerza la implementación no-cuDNN.
    # Alternativamente, podrías usar: LSTM(..., implementation=2)
    x = Bidirectional(LSTM(
        lstm_units[0],
        return_sequences=True,
        dropout=0.3,
        recurrent_activation='sigmoid', # CAMBIO CLAVE: fuerza la implementación genérica
        use_bias=True, # Asegura consistencia
        implementation=2
    ), name='bilstm_1')(x)
    
    x = Bidirectional(LSTM(
        lstm_units[1],
        return_sequences=True,
        dropout=0.3,
        recurrent_activation='sigmoid', # CAMBIO CLAVE: fuerza la implementación genérica
        use_bias=True, # Asegura consistencia
        implementation=2
    ), name='bilstm_2')(x)

    output = Dense(num_chars + 1, activation='softmax', name='output')(x)

    # Pérdida CTC (inputs)
    y_true = Input(shape=[None], dtype='int32', name='y_true')
    # Usar dtype='float32' ya que el parseo de tf.data devuelve float32
    input_length = Input(shape=[1], dtype='float32', name='input_length') 
    label_length = Input(shape=[1], dtype='float32', name='label_length')
    
    ctc_loss = tf.keras.layers.Lambda(ctc_loss_lambda_func, output_shape=(1,), name='ctc_loss')(
        [y_true, output, input_length, label_length]
    )

    modelo_entrenamiento = Model(
        inputs=[input_img, y_true, input_length, label_length],
        outputs=ctc_loss
    )
    # Tasa de aprendizaje inicial ligeramente más alta podría acelerar
    modelo_entrenamiento.compile(optimizer=Adam(learning_rate=3e-4), loss={'ctc_loss': lambda y_true, y_pred: y_pred})

    modelo_inferencia = Model(inputs=input_img, outputs=output)
    print("\nResumen del modelo de inferencia:")
    modelo_inferencia.summary()

    return modelo_entrenamiento, output, input_img, modelo_inferencia
# -------------------------------
# FUNCIÓN DE PÉRDIDA CTC

def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# =================================================================
# 4. DECODIFICACIÓN Y CALLBACKS (Ajustados)
# =================================================================
def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    """Decodifica las predicciones del modelo usando CTC."""
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    # La salida de ctc_decode es un tensor (sparse) de Keras
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    for seq in K.get_value(results):
        word = "".join([index_to_char.get(idx, "") for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def calculate_levenshtein_distance(true_words, pred_words):
    """Calcula la distancia de Levenshtein promedio."""
    total_ratio = 0
    for true, pred in zip(true_words, pred_words):
        total_ratio += SequenceMatcher(None, true, pred).ratio()
    return 1 - (total_ratio / len(true_words))

def generate_error_report(true_words, pred_words, X_test_paths, ruta_errores):
    """Genera un reporte de errores y guarda las imágenes fallidas."""
    incorrect_predictions = []
    
    # Se necesita cargar las imágenes de prueba solo en este momento
    X_test_imgs = []
    for path in X_test_paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_AREA)
        # Normalización para guardar
        X_test_imgs.append(img)
        
    print("\n--- Reporte de Errores ---")
    
    for i, (true_word, pred_word) in enumerate(zip(true_words, pred_words)):
        if true_word.lower().strip() != pred_word.lower().strip():
            incorrect_predictions.append((true_word, pred_word, i))
            
    print(f"Número de predicciones incorrectas: {len(incorrect_predictions)}")
    
    for i, (true, pred, idx) in enumerate(incorrect_predictions[:10]):
        print(f"Error {i+1}:")
        print(f"  Verdadera: '{true}'")
        print(f"  Predicción: '{pred}'")
        
        # Guardar la imagen original re-escalada
        img_to_save = X_test_imgs[idx]
        error_filename = f"error_{i:02d}_{true.replace('/', '_')}_pred_{pred.replace('/', '_')}.png"
        cv2.imwrite(os.path.join(ruta_errores, error_filename), img_to_save)
        
    if len(incorrect_predictions) > 10:
        print(f"... y {len(incorrect_predictions)-10} errores más guardados en '{ruta_errores}'")


class WordAccuracyCallback(Callback):
    def __init__(self, model_inferencia, X_test_paths, true_words_test, index_to_char, output_sequence_length, blank_token_index):
        super().__init__()
        self.model_inferencia = model_inferencia
        self.true_words_test = true_words_test
        self.index_to_char = index_to_char
        self.output_sequence_length = output_sequence_length
        
        # Crear un conjunto de datos de inferencia (solo imágenes) para el callback
        # Es necesario crear un dataset solo con las imágenes para el 'predict'
        self.X_test_ds = tf.data.Dataset.from_tensor_slices(X_test_paths)
        # Adaptar el parseo para la predicción: solo necesitamos la imagen
        def parse_for_predict(image_path):
            img = tf.io.read_file(image_path)
            img = tf.image.decode_jpeg(img, channels=1)
            img = tf.image.resize(img, [img_height, img_width], method=tf.image.ResizeMethod.AREA)
            img = tf.image.convert_image_dtype(img, tf.float32) 
            return img

        self.X_test_ds = self.X_test_ds.map(parse_for_predict, num_parallel_calls=AUTOTUNE).batch(BATCH_SIZE).prefetch(AUTOTUNE)

    def on_epoch_end(self, epoch, logs=None):
        # Mantenemos la evaluación cada 5 épocas para ahorrar tiempo
        if (epoch + 1) % 5 == 0: 
            print(f"\n--- Ejecutando predicción en validación (Época {epoch+1}) ---")
            # Predicción usando el tf.data.Dataset
            y_pred_probs = self.model_inferencia.predict(self.X_test_ds, verbose=0)
            
            pred_words = decode_batch_predictions(y_pred_probs, self.index_to_char, self.output_sequence_length)
            
            correct_predictions = sum(1 for true, pred in zip(self.true_words_test, pred_words) if true.lower().strip() == pred.lower().strip())
            accuracy = correct_predictions / len(self.true_words_test)
            
            print(f"--- Precisión de la palabra de validación: {accuracy * 100:.2f}% ---")

class SaveInferenceEveryNEpochs(Callback):
    def __init__(self, model_inferencia, save_dir, every=10, prefix="ckpt"):
        super().__init__()
        self.model_inferencia = model_inferencia
        self.save_dir = save_dir
        self.every = every
        self.prefix = prefix
        os.makedirs(self.save_dir, exist_ok=True)

    def on_epoch_end(self, epoch, logs=None):
        if (epoch + 1) % self.every == 0:
            filename = os.path.join(self.save_dir, f"{self.prefix}_epoch_{epoch+1}.h5")
            try:
                self.model_inferencia.save(filename)
                print(f"Checkpoint guardado: {filename}")
            except Exception as e:
                print(f"Error al guardar checkpoint en epoch {epoch+1}: {e}")

# =================================================================
# 5. FUNCIÓN PRINCIPAL DE ENTRENAMIENTO (¡Uso de tf.data!)
# =================================================================
def main():
    (X_train_paths, y_train_padded), \
    (X_test_paths, y_test_padded, true_words_test), \
    (char_to_index, index_to_char, num_chars, blank_token_index) = load_data_paths_and_vocab()
    
    # ----------------------------------------------------
    # Creación de los Datasets tf.data (¡Optimización 3!)
    # ----------------------------------------------------
    # Mapeo y paralelización: ¡Esto acelera la lectura de imágenes!
    # 1. Leer y preprocesar
    train_ds = tf.data.Dataset.from_tensor_slices((X_train_paths, y_train_padded))
    test_ds = tf.data.Dataset.from_tensor_slices((X_test_paths, y_test_padded))
    
    train_ds = train_ds.map(lambda x, y: parse_and_preprocess(x, y, blank_token_index), num_parallel_calls=AUTOTUNE)
    test_ds = test_ds.map(lambda x, y: parse_and_preprocess(x, y, blank_token_index), num_parallel_calls=AUTOTUNE)

    # 2. Aumentación de datos (Solo para entrenamiento).
    # Como ya eliminamos las capas de aumentación del modelo, las aplicamos aquí como funciones.
    def apply_augmentation(inputs, output_ficticio):
        img, label_sequence, input_length, label_length = inputs
        
        # Debe re-crear las operaciones que hacía en Keras aquí
        # Nota: Estas operaciones también son propensas a while_loop, pero en el pipeline
        # de tf.data son manejadas por el CPU de forma paralela, mejorando el rendimiento.
        
        img = tf.image.stateless_random_flip_left_right(img, seed=[42, 42]) # Ejemplo de otra aumentación simple
        
        # Para RandomRotation/Zoom/Translation, puede usar operaciones de tf.raw_ops
        # o las funciones de Keras que ya se usan en el modelo, asegurándose de que
        # el input sea un tensor sin batch y el output sea correcto.
        
        # Para simplificar y aprovechar la paralelización del CPU:
        img = tf.keras.layers.RandomRotation(factor=0.05, interpolation='nearest')(img)
        img = tf.keras.layers.RandomTranslation(height_factor=0.1, width_factor=0.1, interpolation='nearest')(img)
        img = tf.keras.layers.RandomZoom(height_factor=0.1, width_factor=0.1, interpolation='nearest')(img)

        return (img, label_sequence, input_length, label_length), output_ficticio
    
    # Aplicar SOLO al conjunto de entrenamiento
    #train_ds = train_ds.map(apply_augmentation, num_parallel_calls=AUTOTUNE)

    # Shuffling y Prefetching: Mantiene la GPU ocupada
    train_ds = train_ds.shuffle(buffer_size=5000).batch(BATCH_SIZE).prefetch(AUTOTUNE)
    test_ds = test_ds.batch(BATCH_SIZE).prefetch(AUTOTUNE)
    
    print("\n--- Longitudes de Secuencia para Debugging ---")
    print(f"Longitud de secuencia de salida del modelo: {output_sequence_length}")
    print(f"Longitud del conjunto de entrenamiento: {len(X_train_paths)}")
    print(f"Tamaño de lote (BATCH_SIZE): {BATCH_SIZE}")
    print("-" * 40)
    
    modelo_entrenamiento, output_layer, input_img, modelo_inferencia = build_crnn_model(num_chars)
    
    # Callbacks
    save_every_10 = SaveInferenceEveryNEpochs(modelo_inferencia, ruta_modelos, every=10, prefix="keras_cnn_lstm_v3_ctc")
    early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=8, min_lr=1e-7)
    word_accuracy_callback = WordAccuracyCallback(
        modelo_inferencia, X_test_paths, true_words_test, index_to_char, output_sequence_length, blank_token_index
    )

    callbacks=[early_stopping, reduce_lr, word_accuracy_callback, save_every_10]

    print("\nEntrenando Modelo V3 (CNN-BiLSTM con CTC)...")
    history = modelo_entrenamiento.fit(
        # Ahora se pasa el Dataset directamente
        train_ds,
        validation_data=test_ds,
        epochs=100,
        callbacks=callbacks,
        verbose=1
    )

    # ----------------------------------------------------
    # Evaluación Final
    # ----------------------------------------------------
    modelo_inferencia.save(os.path.join(ruta_modelos, "keras_cnn_lstm_v3_ctc.h5"))
    joblib.dump({
        'char_to_index': char_to_index, 
        'index_to_char': index_to_char, 
        'output_sequence_length': output_sequence_length,
        'num_chars': num_chars
        }, os.path.join(ruta_modelos, "vocabulario_v3.pkl"))
    print("\nEntrenamiento V3 completado y modelo guardado.")
    
    # Evaluar con el dataset de predicción (solo imágenes)
    y_pred_probs = modelo_inferencia.predict(word_accuracy_callback.X_test_ds)
    pred_words = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
    
    correct_predictions = sum([1 for pred, true in zip(pred_words, true_words_test) if pred.lower().strip() == true.lower().strip()])
    accuracy_word = correct_predictions / len(true_words_test)
    levenshtein_dist = calculate_levenshtein_distance(true_words_test, pred_words)

    print(f"\n--- Evaluación Final ---")
    print(f"Precisión de coincidencia exacta a nivel de palabra: {accuracy_word * 100:.2f}%")
    print(f"Distancia de Levenshtein (ERROR) promedio: {levenshtein_dist:.4f}")
    
    generate_error_report(true_words_test, pred_words, X_test_paths, ruta_errores)

if __name__ == "__main__":
    main()