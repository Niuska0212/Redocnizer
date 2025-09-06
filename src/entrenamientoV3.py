import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, BatchNormalization, Reshape, Dense, Bidirectional, LSTM, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, Callback
from tensorflow.keras import backend as K
from tensorflow.keras.utils import plot_model
from sklearn.model_selection import train_test_split
import joblib
from difflib import SequenceMatcher

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
img_width = 256
output_sequence_length = img_width // 4

# -------------------------------
# PROCESAMIENTO DE DATOS
# -------------------------------
def load_and_preprocess_data():
    """Carga y prepara las imágenes y etiquetas."""
    with open(labels_file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    imagenes_paths, palabras = [], []
    for line in lines:
        parts = line.split(",", 1)
        if len(parts) == 2:
            imagenes_paths.append(os.path.join(ruta_dataset_palabras, parts[0]))
            palabras.append(parts[1])

    if not palabras:
        print("Error: No se encontraron palabras en el archivo de etiquetas.")
        exit()

    all_chars = sorted(list(set("".join(palabras))))
    char_to_index = {c: i for i, c in enumerate(all_chars)}
    index_to_char = {i: c for c, i in char_to_index.items()}
    num_chars = len(all_chars)
    blank_token_index = num_chars

    filtered_data = [(path, word) for path, word in zip(imagenes_paths, palabras) if len(word) <= output_sequence_length]
    if not filtered_data:
        print("Error: Todas las palabras son más largas que la longitud máxima de la secuencia. Ajusta `img_width`.")
        exit()

    imagenes_paths, palabras = zip(*filtered_data)
    palabras, imagenes_paths = list(palabras), list(imagenes_paths)

    def cargar_imagen(path):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return np.zeros((img_height, img_width), dtype=np.float32)
        img = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_AREA)
        img = cv2.GaussianBlur(img, (7, 7), 0)
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)
        return img / 255.0

    X = np.array([cargar_imagen(p) for p in imagenes_paths])
    X = X.reshape(-1, img_height, img_width, 1).astype(np.float32)
    y_seq = [[char_to_index[c] for c in w] for w in palabras]
    y_padded = tf.keras.preprocessing.sequence.pad_sequences(y_seq, padding='post', value=blank_token_index)
    label_length = np.array([len(s) for s in y_seq])

    X_train, X_test, y_train, y_test, label_length_train, label_length_test, _, true_words_test = train_test_split(
        X, y_padded, label_length, palabras, test_size=0.2, random_state=42
    )

    input_length_train = np.full(X_train.shape[0], output_sequence_length)
    input_length_test = np.full(X_test.shape[0], output_sequence_length)

    return (X_train, y_train, input_length_train, label_length_train), \
           (X_test, y_test, input_length_test, label_length_test, true_words_test), \
           (char_to_index, index_to_char, num_chars, blank_token_index)

# -------------------------------
# ARQUITECTURA DEL MODELO CRNN CON CTC
# -------------------------------
def build_crnn_model(num_chars):
    """Construye y compila el modelo CRNN con una capa de pérdida CTC."""
    input_img = Input(shape=(img_height, img_width, 1), name='input_img')

    # Bloque CNN para extraer características
    x = Conv2D(64, (3, 3), activation='relu', padding='same', name='conv_1')(input_img)
    x = BatchNormalization(name='bn_1')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x)

    x = Conv2D(128, (3, 3), activation='relu', padding='same', name='conv_2')(x)
    x = BatchNormalization(name='bn_2')(x)
    x = MaxPooling2D(pool_size=(2, 2), name='max_pool_2')(x)

    x = Conv2D(256, (3, 3), activation='relu', padding='same', name='conv_3')(x)
    x = BatchNormalization(name='bn_3')(x)
    x = Dropout(0.2, name='dropout_cnn')(x)

    # Conectar a las capas LSTM
    x = Reshape(target_shape=(output_sequence_length, (img_height // 4) * 256), name='reshape')(x)
    x = Dense(128, activation='relu', name='dense_pre_lstm')(x) 
    x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.2, name='lstm_1'))(x) 
    x = Bidirectional(LSTM(64, return_sequences=True, dropout=0.2, name='lstm_2'))(x)

    output = Dense(num_chars + 1, activation='softmax', name='output')(x)

    y_true = Input(shape=[None], name='y_true')
    input_length = Input(shape=[1], name='input_length')
    label_length = Input(shape=[1], name='label_length')
    ctc_loss = tf.keras.layers.Lambda(ctc_loss_lambda_func, output_shape=(1,), name='ctc_loss')(
        [y_true, output, input_length, label_length]
    )

    modelo_entrenamiento = Model(
        inputs=[input_img, y_true, input_length, label_length],
        outputs=ctc_loss
    )
    modelo_entrenamiento.compile(optimizer='adam', loss={'ctc_loss': lambda y_true, y_pred: y_pred})
    
    return modelo_entrenamiento, output, input_img

def ctc_loss_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# -------------------------------
# DECODIFICACIÓN Y ANÁLISIS DE ERRORES
# -------------------------------
def decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length):
    """Decodifica las predicciones del modelo usando CTC."""
    input_len = np.full(y_pred_probs.shape[0], output_sequence_length)
    results = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)[0][0]
    
    decoded_words = []
    for seq in K.get_value(results):
        word = "".join([index_to_char[idx] for idx in seq if idx != -1])
        decoded_words.append(word.strip())
    return decoded_words

def calculate_levenshtein_distance(true_words, pred_words):
    """Calcula la distancia de Levenshtein promedio."""
    total_distance = 0
    total_length = 0
    for true, pred in zip(true_words, pred_words):
        total_distance += SequenceMatcher(None, true, pred).ratio()
        total_length += 1
    return 1 - (total_distance / total_length)

def generate_error_report(true_words, pred_words, X_test, ruta_errores):
    """Genera un reporte de errores y guarda las imágenes fallidas."""
    incorrect_predictions = []
    for i, (true_word, pred_word) in enumerate(zip(true_words, pred_words)):
        if true_word.lower().strip() != pred_word.lower().strip(): # Comparación insensibble a mayúsculas
            incorrect_predictions.append((true_word, pred_word, i))
            
    print("\n--- Reporte de Errores ---")
    print(f"Número de predicciones incorrectas: {len(incorrect_predictions)}")
    
    for i, (true, pred, idx) in enumerate(incorrect_predictions[:10]):
        print(f"Error {i+1}:")
        print(f"  Verdadera: '{true}'")
        print(f"  Predicción: '{pred}'")
        
        # Guardar la imagen del error
        img_to_save = (X_test[idx] * 255).astype(np.uint8).squeeze()
        error_filename = f"error_{i:02d}_{true.replace('/', '_')}_pred_{pred.replace('/', '_')}.png"
        cv2.imwrite(os.path.join(ruta_errores, error_filename), img_to_save)
        
    if len(incorrect_predictions) > 10:
        print(f"... y {len(incorrect_predictions)-10} errores más guardados en '{ruta_errores}'")

# -------------------------------
# CALLBACK PARA VALIDACIÓN DURANTE EL ENTRENAMIENTO
# -------------------------------
class WordAccuracyCallback(Callback):
    def __init__(self, model_inferencia, X_test, true_words_test, index_to_char, output_sequence_length):
        super().__init__()
        self.model_inferencia = model_inferencia
        self.X_test = X_test
        self.true_words_test = true_words_test
        self.index_to_char = index_to_char
        self.output_sequence_length = output_sequence_length

    def on_epoch_end(self, epoch, logs=None):
        if (epoch + 1) % 5 == 0:  # Evaluar cada 5 épocas
            y_pred_probs = self.model_inferencia.predict(self.X_test)
            pred_words = decode_batch_predictions(y_pred_probs, self.index_to_char, self.output_sequence_length)
            
            correct_predictions = sum(1 for true, pred in zip(self.true_words_test, pred_words) if true.lower().strip() == pred.lower().strip())
            accuracy = correct_predictions / len(self.true_words_test)
            
            print(f"\n--- Precisión de la palabra de validación en la época {epoch+1}: {accuracy * 100:.2f}% ---")
            
# -------------------------------
# FUNCIÓN PRINCIPAL DE ENTRENAMIENTO
# -------------------------------
def main():
    (X_train, y_train, input_length_train, label_length_train), \
    (X_test, y_test, input_length_test, label_length_test, true_words_test), \
    (char_to_index, index_to_char, num_chars, blank_token_index) = load_and_preprocess_data()

    print("\n--- Longitudes de Secuencia para Debugging ---")
    print(f"Longitud de secuencia de salida del modelo: {output_sequence_length}")
    print(f"Longitud máxima de etiqueta: {np.max([len(s) for s in true_words_test])}")
    print(f"Longitud del conjunto de entrenamiento: {len(X_train)}")
    print("-" * 40)
    
    modelo_entrenamiento, output_layer, input_img = build_crnn_model(num_chars)
    modelo_entrenamiento.summary()
    
    # Modelo de inferencia para usar en la decodificación de CTC
    modelo_inferencia = Model(inputs=input_img, outputs=output_layer)
    
    # Callbacks
    early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=8, min_lr=1e-7)
    word_accuracy_callback = WordAccuracyCallback(modelo_inferencia, X_test, true_words_test, index_to_char, output_sequence_length)

    print("\nEntrenando Modelo V3 (CNN-BiLSTM con CTC)...")
    history = modelo_entrenamiento.fit(
        x=[X_train, y_train, input_length_train, label_length_train],
        y=np.zeros(len(X_train)),
        validation_data=([X_test, y_test, input_length_test, label_length_test], np.zeros(len(X_test))),
        epochs=100,
        batch_size=32,
        callbacks=[early_stopping, reduce_lr, word_accuracy_callback],
        verbose=1
    )

    # Guardar el modelo y el vocabulario
    modelo_inferencia.save(os.path.join(ruta_modelos, "keras_cnn_lstm_v3_ctc.h5"))
    #plot_model(modelo_inferencia, to_file=os.path.join(ruta_modelos, "modelo_inferencia_v3.png"), show_shapes=True, show_layer_names=True)
    joblib.dump({
        'char_to_index': char_to_index, 
        'index_to_char': index_to_char, 
        'output_sequence_length': output_sequence_length,
        'num_chars': num_chars
        }, os.path.join(ruta_modelos, "vocabulario_v3.pkl"))
    print("\nEntrenamiento V3 completado y modelo guardado.")
    
    # Evaluación final y reporte
    y_pred_probs = modelo_inferencia.predict(X_test)
    pred_words = decode_batch_predictions(y_pred_probs, index_to_char, output_sequence_length)
    
    correct_predictions = sum([1 for pred, true in zip(pred_words, true_words_test) if pred.lower().strip() == true.lower().strip()])
    accuracy_word = correct_predictions / len(true_words_test)
    levenshtein_dist = calculate_levenshtein_distance(true_words_test, pred_words)

    print(f"\n--- Evaluación Final ---")
    print(f"Precisión de coincidencia exacta a nivel de palabra: {accuracy_word * 100:.2f}%")
    print(f"Distancia de Levenshtein (ERROR) promedio: {levenshtein_dist:.4f}")
    
    generate_error_report(true_words_test, pred_words, X_test, ruta_errores)

if __name__ == "__main__":
    main()