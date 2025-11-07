# =================================================================
# entrenamientoV4_Optimizado.py - Listo para GPU DirectML y Producción
# =================================================================

import os
import numpy as np
import cv2
import tensorflow as tf
from sklearn.model_selection import train_test_split
import joblib
from difflib import SequenceMatcher

# -------------------------------
# CONFIGURACIÓN INICIAL Y DEPURACIÓN
# -------------------------------
# Constantes para la compatibilidad forzada
GPU_DISPONIBLE = False
AUTOTUNE = tf.data.AUTOTUNE # Usar AUTOTUNE para optimización de tf.data

# Desactiva los mensajes de depuración de TensorFlow (INFO y WARNINGs)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
# También puedes silenciar el warning específico de NUMA (aunque a veces no funciona con DML)
os.environ["KMP_AFFINITY"] = "noverbose"

# 1. Verificar Versiones y GPU (Asegúrate de que tus versiones coincidan con las instaladas)
try:
    print(f"Versión de TensorFlow: {tf.__version__}")
    print(f"Versión de NumPy: {np.__version__}")
    print(f"Versión de OpenCV (cv2): {cv2.__version__}")
    print("---")
    
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"✅ GPUs detectadas (DirectML): {gpus}")
        print("El entrenamiento usará el backend /GPU:0 (DirectML).")
        GPU_DISPONIBLE = True
    else:
        print("⚠️ No se detectaron dispositivos GPU. El entrenamiento usará la CPU.")
        GPU_DISPONIBLE = False
except Exception as e:
    print(f"Error en la verificación de entorno: {e}")
    GPU_DISPONIBLE = False

# Sustitución de Keras 2 y Keras 3 (Usar tf.keras)
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
Rescaling = tf.keras.layers.Rescaling
# Se eliminan las capas de aumento de Keras (RandomRotation, etc.) del modelo
# para evitar problemas de compatibilidad en el pipeline, se recomienda aplicar
# la aumentación de imagen fuera del pipeline de tf.data si es necesario.

EarlyStopping = tf.keras.callbacks.EarlyStopping
ReduceLROnPlateau = tf.keras.callbacks.ReduceLROnPlateau
Callback = tf.keras.callbacks.Callback

K = tf.keras.backend 
Adam = tf.keras.optimizers.Adam

# -------------------------------
# CONFIGURACIÓN Y PARÁMETROS
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_dataset_palabras = os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")
labels_file_path = os.path.join(ruta_dataset_palabras, "labels.txt")
ruta_modelos = os.path.join(BASE_DIR, "..", "models")
ruta_errores = os.path.join(ruta_modelos, "errores_prediccion_v4")
os.makedirs(ruta_modelos, exist_ok=True)
os.makedirs(ruta_errores, exist_ok=True)

img_height = 32
img_width = 1024 # Aumentado a 1024 para una mejor longitud de secuencia
output_sequence_length = img_width // 4 # 1024 / 4 = 256 pasos (Más adecuado para BiLSTM)
BATCH_SIZE = 8 # Aumento a 8 para saturar la GPU

# =================================================================
# 2. PROCESAMIENTO DE DATOS (tf.data optimizado)
# =================================================================

def load_data_paths_and_vocab():
    """Carga las rutas, las etiquetas, construye el vocabulario y devuelve los paths y labels."""
    global blank_token_index
    with open(labels_file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    imagenes_paths, palabras = [], []
    for line in lines:
        parts = line.split(",", 1)
        if len(parts) == 2:
            path = os.path.join(ruta_dataset_palabras, parts[0])
            if os.path.exists(path):
                palabra = parts[1]
                # Filtrar palabras demasiado largas para evitar errores de CTC
                if len(palabra) <= output_sequence_length: 
                    imagenes_paths.append(path)
                    palabras.append(palabra)

    if not imagenes_paths:
        print("Error: No hay imágenes válidas para entrenar.")
        exit()

    # --- Construir vocabulario / mappings para CTC ---
    charset = sorted({ch for w in palabras for ch in w})
    char_to_index = {c: i for i, c in enumerate(charset)}
    index_to_char = {i: c for c, i in char_to_index.items()}
    num_chars = len(charset)
    blank_token_index = num_chars  # índice reservado para el token 'blank' de CTC

    # Convertir palabras a secuencias de índices
    y_seq = [[char_to_index[c] for c in w] for w in palabras]
    
    # Dividir: paths, secuencias de índices, palabras originales
    X_train_paths, X_test_paths, y_train_seq_idx, y_test_seq_idx, _, true_words_test = train_test_split(
        imagenes_paths, y_seq, palabras, test_size=0.2, random_state=42
    )

    # Padding de las secuencias de etiquetas (¡Importante para batching!)
    # Se utiliza el índice del token 'blank' para el relleno
    y_train_padded = tf.keras.preprocessing.sequence.pad_sequences(
        y_train_seq_idx, padding='post', value=blank_token_index, maxlen=output_sequence_length
    )
    y_test_padded = tf.keras.preprocessing.sequence.pad_sequences(
        y_test_seq_idx, padding='post', value=blank_token_index, maxlen=output_sequence_length
    )
    
    return (X_train_paths, y_train_padded), \
        (X_test_paths, y_test_padded, true_words_test), \
        (char_to_index, index_to_char, num_chars, blank_token_index)

@tf.function
def parse_and_preprocess(image_path, label_sequence):
    """Función de preprocesamiento para tf.data que carga, redimensiona y prepara la imagen."""
    global blank_token_index
    
    img_height_t = tf.constant(img_height, dtype=tf.int32)
    img_width_t = tf.constant(img_width, dtype=tf.int32)
    output_seq_len_t = tf.constant(float(output_sequence_length), dtype=tf.float32)

    # Cargar y decodificar imagen (Optimización: usa tf.io en lugar de cv2)
    img = tf.io.read_file(image_path)
    img = tf.image.decode_jpeg(img, channels=1) # Asumimos JPEG, ajusta si es PNG
    
    # Redimensionar
    img = tf.image.resize(img, [img_height_t, img_width_t], method=tf.image.ResizeMethod.AREA)
    
    # Convertir a float32 (la normalización / 255 se hace en la capa Rescaling del modelo)
    img = tf.image.convert_image_dtype(img, tf.float32) 
    
    # Calcular input_length y label_length para CTC
    input_length = tf.expand_dims(output_seq_len_t, axis=0)
    
    # La longitud real de la etiqueta es la suma de los elementos que NO son el token blank.
    # Usamos tf.int64 para label_sequence para evitar problemas de casting.
    label_length_val = tf.reduce_sum(tf.cast(tf.not_equal(label_sequence, blank_token_index), tf.int32))
    label_length = tf.cast(tf.expand_dims(label_length_val, axis=0), tf.float32)

    # El modelo de entrenamiento espera 4 inputs, 1 output ficticio
    return (img, label_sequence, input_length, label_length), tf.constant(0.0)

def create_dataset(paths, labels_padded, blank_token_index, is_training=True):
    """Crea y optimiza el pipeline de tf.data.Dataset."""
    
    # Crear Dataset a partir de paths y etiquetas
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels_padded))

    if is_training:
        # 1. Mezclar (shuffle)
        dataset = dataset.shuffle(buffer_size=len(paths))
        # 2. Mapear y preprocesar
        dataset = dataset.map(lambda x, y: parse_and_preprocess(x, y), num_parallel_calls=AUTOTUNE) # <--- CORREGIDO
        # 3. Cachear (si el dataset cabe en RAM) o Prefetch
        # dataset = dataset.cache() 
        # 4. Batching
        dataset = dataset.batch(BATCH_SIZE)
        # 5. Prefetch
        dataset = dataset.prefetch(AUTOTUNE)
    else:
        # Para validación/prueba, no mezclar
        dataset = dataset.map(lambda x, y: parse_and_preprocess(x, y), num_parallel_calls=AUTOTUNE) # <--- CORREGIDO
        dataset = dataset.batch(BATCH_SIZE)
        dataset = dataset.prefetch(AUTOTUNE)
        
    return dataset

# =================================================================
# 3. ARQUITECTURA DEL MODELO CRNN CON CTC
# =================================================================

def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

def build_crnn_model(num_chars):
    """Construye y compila el modelo CRNN con implementación LSTM compatible con DML."""
    
    base_filters = [64, 128, 256, 512]

    input_img = Input(shape=(img_height, img_width, 1), name='input_img')

    # Normalización: Necesaria cuando se usa tf.data
    x = Rescaling(1./255)(input_img) 

    # --- Capas CNN ---
    x = Conv2D(base_filters[0], (3, 3), activation='relu', padding='same', name='conv_1')(x)
    x = BatchNormalization(name='bn_1')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x) # 1/2

    x = Conv2D(base_filters[1], (3, 3), activation='relu', padding='same', name='conv_2')(x)
    x = BatchNormalization(name='bn_2')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_2')(x) # 1/4
    
    x = Conv2D(base_filters[2], (3, 3), activation='relu', padding='same', name='conv_3')(x)
    x = BatchNormalization(name='bn_3')(x)
    
    x = Conv2D(base_filters[3], (3, 3), activation='relu', padding='same', name='conv_4')(x)
    x = BatchNormalization(name='bn_4')(x)
    # No usamos max_pool_3 para mantener 256 pasos (1024/4 = 256)
    
    x = Dropout(0.3, name='dropout_cnn')(x)

    # Ajustar reshape para 1024x32
    # output_sequence_length = 256. Altura de las features = 32 / 4 = 8
    features_per_step = (img_height // 4) * base_filters[3] # 8 * 512 = 4096
    x = Reshape(target_shape=(output_sequence_length, features_per_step), name='reshape')(x)
    x = Dropout(0.3, name='dropout_pre_lstm')(x) 
    
    # --- Capas BiLSTM (Solución al error CudnnRNN) ---
    # Al usar recurrent_dropout y implementation=2, forzamos la implementación 
    # genérica de LSTM compatible con DirectML (DML) y que no requiere cuDNN.
    x = Bidirectional(LSTM(
        128, 
        return_sequences=True, 
        dropout=0.3, 
        recurrent_dropout=0.3, # Desactiva cuDNN
        implementation=2, # Usa la implementación genérica (no-cuDNN)
    ), name='bilstm_1')(x)
    
    x = Bidirectional(LSTM(
        64, 
        return_sequences=True, 
        dropout=0.3, 
        recurrent_dropout=0.3, # Desactiva cuDNN
        implementation=2, # Usa la implementación genérica (no-cuDNN)
    ), name='bilstm_2')(x)

    output = Dense(num_chars + 1, activation='softmax', name='output')(x)

    # --- Pérdida CTC (inputs) ---
    y_true = Input(shape=[None], dtype='int32', name='y_true')
    input_length = Input(shape=[1], dtype='float32', name='input_length')
    label_length = Input(shape=[1], dtype='float32', name='label_length')
    
    ctc_loss = tf.keras.layers.Lambda(ctc_loss_lambda_func, output_shape=(1,), name='ctc_loss')(
        [y_true, output, input_length, label_length]
    )

    modelo_entrenamiento = Model(
        inputs=[input_img, y_true, input_length, label_length],
        outputs=ctc_loss
    )
    # Optimizador con learning rate bajo (1e-4) para estabilidad
    modelo_entrenamiento.compile(optimizer=Adam(learning_rate=1e-4), loss={'ctc_loss': lambda y_true, y_pred: y_pred})

    modelo_inferencia = Model(inputs=input_img, outputs=output)
    
    return modelo_entrenamiento, modelo_inferencia

# =================================================================
# 4. DECODIFICACIÓN Y CALLBACKS (Reutilizados y optimizados)
# =================================================================

def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    """Decodifica las predicciones del modelo usando CTC."""
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    # Asegurarse de que K.get_value() se use para extraer los resultados de Keras
    for seq in K.get_value(results):
        # Filtrar el padding (idx != -1)
        word = "".join([index_to_char.get(idx, "") for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def calculate_levenshtein_distance(true_words, pred_words):
    """Calcula la distancia de Levenshtein promedio (basado en SequenceMatcher ratio)."""
    total_ratio = 0
    for true, pred in zip(true_words, pred_words):
        total_ratio += SequenceMatcher(None, true, pred).ratio()
    return 1 - (total_ratio / len(true_words))

class WordAccuracyCallback(Callback):
    def __init__(self, model_inferencia, X_test_paths, y_test_padded, true_words_test, index_to_char, output_sequence_length, blank_token_index):
        super().__init__()
        self.model_inferencia = model_inferencia
        self.true_words_test = true_words_test
        self.index_to_char = index_to_char
        self.output_sequence_length = output_sequence_length
        
        # Crear un dataset de inferencia (solo con imagen) para el callback
        # Es más fácil y rápido cargar el dataset de prueba directamente para la predicción
        self.test_dataset_paths = X_test_paths
        
    def on_epoch_end(self, epoch, logs=None):
        if (epoch + 1) % 5 == 0:  # Evaluar cada 5 épocas
            # Cargar imágenes de prueba justo antes de la predicción (eficiente)
            X_test_imgs = []
            for path in self.test_dataset_paths:
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                img = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_AREA)
                img = img.reshape(img_height, img_width, 1).astype(np.float32)
                X_test_imgs.append(img)
            X_test_array = np.array(X_test_imgs)
            
            y_pred_probs = self.model_inferencia.predict(X_test_array, verbose=0)
            pred_words = decode_batch_predictions(y_pred_probs, self.index_to_char, self.output_sequence_length)
            
            correct_predictions = sum(1 for true, pred in zip(self.true_words_test, pred_words) if true.lower().strip() == pred.lower().strip())
            accuracy = correct_predictions / len(self.true_words_test)
            
            logs['val_word_accuracy'] = accuracy # Añadir métrica a los logs
            print(f"\n--- Precisión de la palabra de validación en la época {epoch+1}: {accuracy * 100:.2f}% ---")

def generate_error_report(true_words, pred_words, X_test_paths, ruta_errores):
    """Genera un reporte de errores y guarda las imágenes fallidas."""
    
    # Cargar las imágenes solo para los errores
    X_test_imgs = []
    for path in X_test_paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_AREA)
        X_test_imgs.append(img)
    X_test_array = np.array(X_test_imgs)
    
    incorrect_predictions = []
    for i, (true_word, pred_word) in enumerate(zip(true_words, pred_words)):
        if true_word.lower().strip() != pred_word.lower().strip(): 
            incorrect_predictions.append((true_word, pred_word, i))
            
    print("\n--- Reporte de Errores ---")
    print(f"Número de predicciones incorrectas: {len(incorrect_predictions)}")
    
    # Guardar solo las primeras 10 imágenes fallidas
    for i, (true, pred, idx) in enumerate(incorrect_predictions[:10]):
        print(f"Error {i+1}: Verdadera: '{true}', Predicción: '{pred}'")
        
        img_to_save = X_test_array[idx] # Imagen ya re-escalada, sin normalizar (0-255)
        error_filename = f"error_{i:02d}_{true.replace('/', '_')}_pred_{pred.replace('/', '_')}.png"
        cv2.imwrite(os.path.join(ruta_errores, error_filename), img_to_save)

    if len(incorrect_predictions) > 10:
        print(f"... y {len(incorrect_predictions)-10} errores más, solo se guardaron las primeras 10 imágenes.")
        
# =================================================================
# 5. FUNCIÓN PRINCIPAL DE ENTRENAMIENTO
# =================================================================

def main():
    
    # 1. Cargar paths y preparar vocabulario
    (X_train_paths, y_train_padded), \
    (X_test_paths, y_test_padded, true_words_test), \
    (char_to_index, index_to_char, num_chars, blank_token_index) = load_data_paths_and_vocab()
    
    # Calcular input_length y label_length para el conjunto de prueba (necesario para el modelo.fit)
    input_length_test = np.full((len(X_test_paths), 1), output_sequence_length, dtype=np.float32)
    label_length_test = np.array([len([idx for idx in seq if idx != blank_token_index]) for seq in y_test_padded], dtype=np.float32).reshape(-1, 1)

    print("\n--- Longitudes de Secuencia para Debugging ---")
    print(f"Longitud de secuencia de salida del modelo: {output_sequence_length}")
    print(f"Longitud del conjunto de entrenamiento: {len(X_train_paths)}")
    print(f"Tamaño de lote (BATCH_SIZE): {BATCH_SIZE}")
    print("-" * 40)
    
    # 2. Crear Datasets optimizados (tf.data)
    train_dataset = create_dataset(X_train_paths, y_train_padded, blank_token_index, is_training=True)
    val_dataset = create_dataset(X_test_paths, y_test_padded, blank_token_index, is_training=False)

    # 3. Construir Modelos
    modelo_entrenamiento, modelo_inferencia = build_crnn_model(num_chars)
    modelo_inferencia.summary() # Imprimir el resumen del modelo de inferencia
    
    # 4. Callbacks
    early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=8, min_lr=1e-7)
    
    # Usamos el callback modificado para leer del disco en cada evaluación
    word_accuracy_callback = WordAccuracyCallback(
        modelo_inferencia, X_test_paths, y_test_padded, 
        true_words_test, index_to_char, output_sequence_length, blank_token_index
    )

    print("\nEntrenando Modelo V4 (Optimizado para DirectML y tf.data)...")
    
    # 5. Entrenamiento
    # Los datasets de tf.data no requieren los arrays x=[X_train, y_train, ...] y y=np.zeros(len(X_train))
    # Simplemente se pasa el objeto dataset que ya tiene la estructura (x, y)
    history = modelo_entrenamiento.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=200, 
        callbacks=[early_stopping, reduce_lr, word_accuracy_callback],
        verbose=1
    )

    # 6. Guardar y evaluar
    modelo_inferencia.save(os.path.join(ruta_modelos, "keras_cnn_lstm_v4_ctc.h5"))
    joblib.dump({
        'char_to_index': char_to_index, 
        'index_to_char': index_to_char, 
        'output_sequence_length': output_sequence_length,
        'num_chars': num_chars
        }, os.path.join(ruta_modelos, "vocabulario_v4.pkl"))
    print("\nEntrenamiento V4 completado y modelo guardado.")
    
    # Evaluación Final
    # ----------------
    # Volvemos a cargar las imágenes de prueba para la predicción final
    X_test_imgs = []
    for path in X_test_paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_AREA)
        img = img.reshape(img_height, img_width, 1).astype(np.float32) / 255.0 # Normalización
        X_test_imgs.append(img)
    X_test_array = np.array(X_test_imgs)

    y_pred_probs = modelo_inferencia.predict(X_test_array, verbose=0)
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