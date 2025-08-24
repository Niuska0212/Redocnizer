import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, BatchNormalization, Reshape, Dense, Bidirectional, LSTM
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras import backend as K
from sklearn.model_selection import train_test_split
import joblib

# Definir la función de pérdida CTC (Connectionist Temporal Classification)
# Esta es la parte clave que nos permite manejar secuencias de longitud variable.
def ctc_loss_lambda_func(args):
    """
    Función de pérdida CTC.
    :param args: Una tupla que contiene: y_true, y_pred, input_length, label_length.
    """
    y_true, y_pred, input_length, label_length = args
    # input_length y label_length deben ser tensores 1D para tf.keras.backend.ctc_batch_cost
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

# Configuración de las rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_dataset_palabras = os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")
labels_file_path = os.path.join(ruta_dataset_palabras, "labels.txt")
ruta_modelos = os.path.join(BASE_DIR, "..", "models")
os.makedirs(ruta_modelos, exist_ok=True)


# Parámetros del modelo y preprocesamiento
img_height = 32
img_width = 256
# La longitud de la secuencia de salida de la CNN, crucial para CTC
# Un ancho de 256 con dos max-pooling de 2x2 resulta en un ancho de 64.
output_sequence_length = img_width // 4


# Cargar etiquetas y palabras
with open(labels_file_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

imagenes_paths = []
palabras = []
for line in lines:
    parts = line.split(",", 1)
    if len(parts) == 2:
        imagenes_paths.append(os.path.join(ruta_dataset_palabras, parts[0]))
        palabras.append(parts[1])

if not palabras:
    print("Error: No se encontraron palabras en el archivo de etiquetas.")
    exit()

# Crear vocabulario de caracteres
all_chars = sorted(list(set("".join(palabras))))
char_to_index = {c: i for i, c in enumerate(all_chars)}
index_to_char = {i: c for c, i in char_to_index.items()}
num_chars = len(all_chars)
blank_token_index = num_chars

# CORRECCIÓN CLAVE: Filtrar las palabras que son demasiado largas.
# La longitud de la secuencia de etiquetas no puede ser mayor que la de la secuencia de entrada
# que sale de la CNN.
max_label_length = output_sequence_length
filtered_data = [(path, word) for path, word in zip(imagenes_paths, palabras) if len(word) <= max_label_length]
if not filtered_data:
    print("Error: Todas las palabras son más largas que la longitud máxima de la secuencia. Considera un modelo más grande o un preprocesamiento diferente.")
    exit()

imagenes_paths, palabras = zip(*filtered_data)
palabras = list(palabras)
imagenes_paths = list(imagenes_paths)

# Cargar y preprocesar imágenes
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


# Convertir palabras a secuencias de índices
y_seq = [[char_to_index[c] for c in w] for w in palabras]
y_padded = tf.keras.preprocessing.sequence.pad_sequences(y_seq, padding='post', value=blank_token_index)
label_length = np.array([len(s) for s in y_seq])


# Dividir en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test, label_length_train, label_length_test = train_test_split(
    X, y_padded, label_length, test_size=0.2, random_state=42
)

# La longitud de la secuencia de entrada para el modelo (de la CNN)
input_length_train = np.full(X_train.shape[0], output_sequence_length)
input_length_test = np.full(X_test.shape[0], output_sequence_length)

# IMPRESIÓN PARA DEBUGGING
print("\n--- Longitudes de Secuencia para Debugging ---")
print(f"Longitud de secuencia de salida del modelo (input_length): {output_sequence_length}")
print(f"Longitud máxima de etiqueta después de filtrado: {np.max(label_length)}")
print(f"Longitud del conjunto de entrenamiento: {len(X_train)}")
print("-" * 40)


# --- Arquitectura del modelo (CNN-BiLSTM) con CTC ---
input_img = Input(shape=(img_height, img_width, 1), name='input_img')

# Bloque CNN para extraer características
x = Conv2D(32, (3, 3), activation='relu', padding='same', name='conv_1')(input_img)
x = BatchNormalization(name='bn_1')(x)
x = MaxPooling2D(pool_size=(2, 2), name='max_pool_1')(x)

x = Conv2D(64, (3, 3), activation='relu', padding='same', name='conv_2')(x)
x = BatchNormalization(name='bn_2')(x)
x = MaxPooling2D(pool_size=(2, 2), name='max_pool_2')(x)

x = Conv2D(128, (3, 3), activation='relu', padding='same', name='conv_3')(x)
x = BatchNormalization(name='bn_3')(x)

# Conectar a las capas LSTM (usamos Bidirectional para mejor contexto)
# CORRECCIÓN: Ajustar el target_shape para que coincida con la salida de la CNN
# La salida es (batch_size, img_height/4, img_width/4, 128)
# Reshape a (batch_size, img_width/4, (img_height/4) * 128)
x = Reshape(target_shape=(output_sequence_length, (img_height // 4) * 128), name='reshape')(x)
x = Dense(64, activation='relu', name='dense_pre_lstm')(x) 
x = Bidirectional(LSTM(128, return_sequences=True, dropout=0.2, name='lstm_1'))(x) 
x = Bidirectional(LSTM(64, return_sequences=True, dropout=0.2, name='lstm_2'))(x)

output = Dense(num_chars + 1, activation='softmax', name='output')(x)

# Definir la pérdida de CTC como una capa lambda
y_true = Input(shape=[None], name='y_true')
input_length = Input(shape=[1], name='input_length')
label_length = Input(shape=[1], name='label_length')
ctc_loss = tf.keras.layers.Lambda(ctc_loss_lambda_func, output_shape=(1,), name='ctc_loss')(
    [y_true, output, input_length, label_length]
)

# Crear y compilar el modelo de entrenamiento
modelo_ctc_entrenamiento = Model(
    inputs=[input_img, y_true, input_length, label_length],
    outputs=ctc_loss
)
modelo_ctc_entrenamiento.compile(optimizer='adam', loss={'ctc_loss': lambda y_true, y_pred: y_pred})
modelo_ctc_entrenamiento.summary()


# --- Callbacks y entrenamiento ---
early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=8, min_lr=1e-7)

print("\nEntrenando Modelo V3 (CNN-BiLSTM con CTC)...")
modelo_ctc_entrenamiento.fit(
    x=[X_train, y_train, input_length_train, label_length_train],
    y=np.zeros(len(X_train)),  # y_true_dummy
    validation_data=([X_test, y_test, input_length_test, label_length_test], np.zeros(len(X_test))),
    epochs=100,
    batch_size=64,
    callbacks=[early_stopping, reduce_lr],
    verbose=1
)


# --- Guardar el modelo de inferencia y vocabulario ---
# Creamos un modelo de inferencia sin la capa de pérdida CTC
modelo_inferencia = Model(inputs=input_img, outputs=output)
modelo_inferencia.save(os.path.join(ruta_modelos, "keras_cnn_lstm_v3_ctc.h5"))
joblib.dump({
    'char_to_index': char_to_index, 
    'index_to_char': index_to_char, 
    'output_sequence_length': output_sequence_length,
    'num_chars': num_chars,
    'blank_token_index': blank_token_index
    }, os.path.join(ruta_modelos, "vocabulario_v3.pkl"))

print("\nEntrenamiento V3 completado y modelo guardado.")


# --- Evaluación del modelo con CTC ---
print("\n--- Evaluación de la precisión a nivel de palabra con CTC ---")
# Obtener las predicciones del modelo de inferencia
y_pred_probs = modelo_inferencia.predict(X_test)

# Decodificar las predicciones usando la decodificación de 'greedy' de CTC
# K.get_value(K.ctc_decode(...)) es el método correcto para obtener los resultados
y_pred_indices = K.get_value(K.ctc_decode(y_pred_probs, input_length=np.full(X_test.shape[0], output_sequence_length))[0][0])
# El segundo [0] es para elegir el mejor camino de decodificación
# El tercer [0] es para acceder al tensor real

# Decodificar los índices de vuelta a palabras
pred_words = []
for seq in y_pred_indices:
    # Ahora la lógica es más simple: solo eliminamos los -1 que representan padding.
    word = "".join([index_to_char[idx] for idx in seq if idx != -1])
    pred_words.append(word.strip())

# Obtenemos las palabras verdaderas del conjunto de prueba
_, _, _, _, _, true_words_test_split = train_test_split(
    X, y_padded, palabras, test_size=0.2, random_state=42
)
true_words_test = true_words_test_split


# Comparar las palabras predichas con las palabras verdaderas
correct_predictions = sum([1 for pred, true in zip(pred_words, true_words_test) if pred == true])
total_predictions = len(true_words_test)
accuracy_word = correct_predictions / total_predictions

print(f"\nPrecisión de coincidencia exacta a nivel de palabra: {accuracy_word * 100:.2f}%")

print("\n--- Ejemplo de Predicciones ---")
for i in range(10):
    print(f"Verdadera: {true_words_test[i]}")
    print(f"Predicción: {pred_words[i]}")
    print("-" * 20)

print("\n--- Análisis de Errores de Predicción a Nivel de Palabra ---")
correctly_predicted_words = []
incorrect_predictions = []

for true_word, pred_word in zip(true_words_test, pred_words):
    if true_word == pred_word:
        correctly_predicted_words.append((true_word, pred_word))
    else:
        incorrect_predictions.append((true_word, pred_word))

print(f"Número de palabras correctamente predichas: {len(correctly_predicted_words)}")
print(f"Número de palabras incorrectamente predichas: {len(incorrect_predictions)}")

print("\n--- Ejemplos de Predicciones Incorrectas ---")
if incorrect_predictions:
    for i, (true_word, pred_word) in enumerate(incorrect_predictions[:10]):
        print(f"Verdadera: '{true_word}'")
        print(f"Predicción: '{pred_word}'")
        print("-" * 20)
else:
    print("¡No hay predicciones incorrectas! El modelo alcanzó 100% de precisión.")
