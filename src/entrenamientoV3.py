import os
import numpy as np
import cv2
import tensorflow as tf
import joblib
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Input, LSTM, Dense, TimeDistributed, Flatten
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.sequence import pad_sequences


#Configuracion de la rutas (Luis Diego no tocar)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_modelo_v2=os.path.join(BASE_DIR, "..", "models", "keras_cnn_model_augmented.h5")
ruta_dataset_palabras=os.path.join(BASE_DIR, "..", "data", "data", "dataset_palabras")
labels_file_path = os.path.join(ruta_dataset_palabras, "labels.txt")


#Para cargar etiquetas y palabras
with open(labels_file_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

imagenes_paths = []
palabras = []
for line in lines:
    parts = line.split(",", 1)
    if len(parts) == 2:
        imagenes_paths.append(os.path.join(ruta_dataset_palabras, parts[0]))
        palabras.append(parts[1])


# Crear vocavulario de caracteres
all_chars = sorted(list(set("".join(palabras)))) #todos los caracteres unicos estan aqui
char_to_index = {c: i for i, c in enumerate(all_chars)}
index_to_char = {i: c for c, i in char_to_index.items()}
num_chars = len(all_chars)


#cargar imagenes.
def cargar_imagen(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.GaussianBlur(img, (7,7), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)
    img = cv2.resize(img, (28,28))
    return img / 255.0 #para normalizar


X = np.array([cargar_imagen(p) for p in imagenes_paths])
X = X.reshape(-1, 28, 28, 1).astype(np.float32)


# Convertir palabras a secuencias de indices
y_seq = [[char_to_index[c] for c in w] for w in palabras]
max_len = max(len(seq) for seq in y_seq)
y_seq_padded = pad_sequences(y_seq, maxlen=max_len, padding='post', value= -1) # el -1 es para el padding ayuda a la red a identificar el final de la secuencia


#convertir a one-hot encoding
y_onehot = np.zeros((len(y_seq_padded), max_len, num_chars), dtype= np.float32)
for i, seq in enumerate(y_seq_padded):
    for t, idx in enumerate(seq):
        if idx >= 0:
            y_onehot[i, t, idx] = 1.0


#dividir train/test
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y_onehot[:split], y_onehot[split:]


# Cargar modelo CNN preentrenado y reutilizar CNN
modelo_v2 = load_model(ruta_modelo_v2)
for layer in modelo_v2.layers:
    layer.trainable = False  # el false es para congelar capas existentes.

# crear nuevo modelo para secuencias
input_img = Input(shape=(28,28,1))
x = modelo_v2.layers[0](input_img)  #capa de entrada original
for layer in modelo_v2.layers[1:-1]: # usar todas menos la de salida
    x = layer(x)


x = Flatten()(x)
x = tf.keras.layers.RepeatVector(max_len)(x)  # repetir para cada paso de LSTM
x = LSTM(256, return_sequences=True)(x)
x = LSTM(128, return_sequences=True)(x)
output_seq = TimeDistributed(Dense(num_chars, activation='softmax'))(x)

modelo_v3 = Model(inputs=input_img, outputs=output_seq)
modelo_v3.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

modelo_v3.summary()

# --- Callbacks ---
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=1e-6)

# --- Entrenamiento ---
modelo_v3.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=300,
    batch_size=64,
    callbacks=[early_stopping, reduce_lr],
    verbose=1
)

# --- Guardar modelo y vocabulario ---
modelo_v3.save(os.path.join(BASE_DIR, "..", "models", "keras_cnn_lstm_v3.h5"))

joblib.dump({'char_to_index': char_to_index, 'index_to_char': index_to_char}, 
            os.path.join(BASE_DIR, "..", "models", "vocabulario_v3.pkl"))

print("Entrenamiento V3 completado y modelo guardado.")