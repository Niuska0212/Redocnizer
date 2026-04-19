# entrenamientoV3_modular.py
"""
Versión modular y optimizada de tu entrenamiento V3.
- Usa tf.data (cache + prefetch + autotune)
- Separa 'base model' (CRNN) y modelo de entrenamiento con CTC
- Callbacks: ModelCheckpoint, ReduceLROnPlateau, EarlyStopping, TensorBoard, CSVLogger
- Callback personalizado para CER y muestra ejemplos
- Soporta cargar pesos de modelos previos (transfer learning) con remapeo básico
"""

import os
import time
import json
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow.keras import backend as K
from tensorflow.keras.layers import Input
from tensorflow.keras.callbacks import (
    ModelCheckpoint, ReduceLROnPlateau, EarlyStopping,
    TensorBoard, CSVLogger, Callback
)
from tensorflow.keras.optimizers import Adam
import joblib
import cv2
from sklearn.model_selection import train_test_split
from difflib import SequenceMatcher

# -----------------------------
# CONFIG (puedes mover a config.yaml)
# -----------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data" / "data" / "dataset_palabras"
LABELS_FILE = DATA_DIR / "labels.txt"
MODELS_DIR = BASE_DIR.parent / "models"
REPORT_DIR = MODELS_DIR / "errores_prediccion_v3"
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Imagen
IMG_H = 32
IMG_W = 256
CHANNELS = 1
BATCH_SIZE = 32
EPOCHS = 200
OUTPUT_SEQ_LEN = IMG_W // 8  # coincide con pooling de 3 capas (2.2.3)
AUTOTUNE = tf.data.AUTOTUNE

# Training
INITIAL_LR = 1e-4
PATIENCE_LR = 8
PATIENCE_ES = 20

# Transfer learning: ruta opcional a pesos previos (h5 o .weights.h5)
PRETRAINED_WEIGHTS = None  # Path or None

VOCAB_SAVE_PATH = MODELS_DIR / "vocab_v3.joblib"
CHECKPOINT_BEST = MODELS_DIR / "model_best.weights.h5"
CHECKPOINT_EPOCH = MODELS_DIR / "model_epoch_{epoch:03d}.weights.h5"
TB_LOGDIR = BASE_DIR / "logs" / time.strftime("%Y%m%d-%H%M%S")

# -----------------------------
# UTIL: lectura etiquetas y vocab
# -----------------------------
def read_labels_file(path):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for l in f:
            s = l.strip()
            if not s:
                continue
            parts = s.split(",", 1)
            if len(parts) != 2:
                continue
            imgpath, word = parts
            full = os.path.join(path.parent, imgpath)
            lines.append((full, word))
    return lines

def build_vocab_from_words(words, include_blank=True):
    chars = sorted(list(set("".join(words))))
    char_to_idx = {c: i+1 for i, c in enumerate(chars)}  # reserve 0 for blank/pad
    if include_blank:
        blank_index = 0
    else:
        blank_index = len(char_to_idx)
    idx_to_char = {i: c for c, i in char_to_idx.items()}
    return char_to_idx, idx_to_char, blank_index

# -----------------------------
# PREPROCESS (CPU) -> imagen normalizada
# -----------------------------
def load_and_preprocess_image(path):
    # path: bytes (from tf.data) or str
    if isinstance(path, bytes):
        path = path.decode("utf-8")
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        img = np.zeros((IMG_H, IMG_W), dtype=np.uint8)
    img = cv2.resize(img, (IMG_W, IMG_H), interpolation=cv2.INTER_AREA)
    # Suavizado opcional:
    img = cv2.GaussianBlur(img, (3,3), 0)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=-1)
    return img

def encode_label_to_seq(word, char_to_idx, blank_index, maxlen=OUTPUT_SEQ_LEN):
    seq = [char_to_idx.get(c, 0) for c in word]
    # No incluir blank in label seq; padding value 0 (already blank/pad)
    if len(seq) > maxlen:
        # truncate (prefer rare cases)
        seq = seq[:maxlen]
    # pad post with 0
    seq = seq + [0] * (maxlen - len(seq))
    return np.array(seq, dtype=np.int32), len(word)

# -----------------------------
# TF.DATA pipeline
# -----------------------------
def make_tf_dataset(pairs, char_to_idx, blank_index, batch_size=BATCH_SIZE, augment=False, shuffle=True):
    image_paths = [p for p, w in pairs]
    words = [w for p, w in pairs]
    # encode labels in numpy arrays (to simplify)
    X_paths = np.array(image_paths)
    y_seqs = []
    label_lengths = []
    for w in words:
        seq, ll = encode_label_to_seq(w, char_to_idx, blank_index, maxlen=OUTPUT_SEQ_LEN)
        y_seqs.append(seq)
        label_lengths.append(ll)
    y_seqs = np.array(y_seqs, dtype=np.int32)
    label_lengths = np.array(label_lengths, dtype=np.int32)
    input_lengths = np.full(len(X_paths), OUTPUT_SEQ_LEN, dtype=np.int32)

    ds = tf.data.Dataset.from_tensor_slices((X_paths, y_seqs, input_lengths, label_lengths))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(X_paths))
    def _map_fn(path, y, in_len, lab_len):
        img = tf.numpy_function(func=load_and_preprocess_image, inp=[path], Tout=tf.float32)
        img.set_shape((IMG_H, IMG_W, 1))
        return {"input_img": img, "y_true": y, "input_length": in_len, "label_length": lab_len}, np.zeros(())  # dummy y for CTC-loss model

    ds = ds.map(_map_fn, num_parallel_calls=AUTOTUNE)
    ds = ds.cache()  # si cabe en RAM; si dataset es grande, quitar o usar cache(filename)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(AUTOTUNE)
    return ds

# -----------------------------
# MODEL: base CRNN (devuelve base_model y modelo de entrenamiento con loss lambda)
# -----------------------------
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, BatchNormalization, Reshape, Dense, Bidirectional, LSTM, Dropout
)

def build_crnn_base(input_shape=(IMG_H, IMG_W, 1), rnn_units=(256,128), num_chars=30):
    inp = Input(shape=input_shape, name="input_img")
    x = inp

    # Simple CNN stack similar a tu V3
    x = Conv2D(64, (3,3), activation='relu', padding='same')(x)
    x = BatchNormalization()(x)
    x = MaxPooling2D((2,2))(x)

    x = Conv2D(128, (3,3), activation='relu', padding='same')(x)
    x = BatchNormalization()(x)
    x = MaxPooling2D((2,2))(x)

    x = Conv2D(256, (3,3), activation='relu', padding='same')(x)
    x = BatchNormalization()(x)

    x = Conv2D(512, (3,3), activation='relu', padding='same')(x)
    x = BatchNormalization()(x)
    x = MaxPooling2D((2,2))(x)

    x = Dropout(0.3)(x)
    # reshape to (T, features)
    features = (IMG_H // 8) * 512
    x = Reshape((OUTPUT_SEQ_LEN, features))(x)
    x = Dropout(0.3)(x)

    x = Bidirectional(LSTM(rnn_units[0], return_sequences=True, dropout=0.3))(x)
    x = Bidirectional(LSTM(rnn_units[1], return_sequences=True, dropout=0.3))(x)

    out = Dense(num_chars + 1, activation='softmax', name='output')(x)  # +1 for blank/pad
    base_model = tf.keras.Model(inputs=inp, outputs=out, name="crnn_base")
    return base_model

# CTC Loss lambda
def ctc_lambda_func(args):
    y_true, y_pred, input_length, label_length = args
    # y_pred shape: (B, T, C)
    return K.ctc_batch_cost(y_true, y_pred, input_length, label_length)

def build_training_model(base_model):
    # inputs
    y_true = Input(shape=(OUTPUT_SEQ_LEN,), dtype='int32', name='y_true')
    input_length = Input(shape=(1,), dtype='int32', name='input_length')
    label_length = Input(shape=(1,), dtype='int32', name='label_length')

    y_pred = base_model.output
    loss_out = tf.keras.layers.Lambda(ctc_lambda_func, output_shape=(1,), name='ctc_loss')(
        [y_true, y_pred, input_length, label_length]
    )

    model = tf.keras.Model(inputs=[base_model.input, y_true, input_length, label_length], outputs=loss_out)
    # compile with dummy loss (the lambda layer returns the real loss)
    model.compile(optimizer=Adam(learning_rate=INITIAL_LR), loss={'ctc_loss': lambda y_true, y_pred: y_pred})
    return model

# -----------------------------
# DECODIFICACIÓN GREEDY Y CER
# -----------------------------
def decode_batch_predictions(y_pred_probs, idx_to_char):
    input_len = np.full(y_pred_probs.shape[0], y_pred_probs.shape[1], dtype=np.int32)
    # K.ctc_decode expects logits (not softmax) in some TF versions; but with softmax works with greedy
    decoded, _ = K.ctc_decode(y_pred_probs, input_length=input_len, greedy=True)
    decoded = decoded[0].numpy()
    texts = []
    for seq in decoded:
        word = "".join([idx_to_char.get(int(i), "") for i in seq if int(i) != -1 and int(i) != 0])
        texts.append(word)
    return texts

def cer_between_lists(trues, preds):
    # Levenshtein via SequenceMatcher ratio -> convert to error
    total = 0.0
    for t, p in zip(trues, preds):
        r = SequenceMatcher(None, t, p).ratio()
        total += (1.0 - r)
    return total / max(1, len(trues))

# -----------------------------
# CALLBACK personalizado para CER y ejemplos
# -----------------------------
class CERCallback(Callback):
    def __init__(self, base_model, X_test, true_words_test, idx_to_char, batch_size=32, log_dir=REPORT_DIR):
        super().__init__()
        self.base = base_model
        self.X_test = X_test  # numpy array of images
        self.true_words_test = true_words_test
        self.idx_to_char = idx_to_char
        self.batch_size = batch_size
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)

    def on_epoch_end(self, epoch, logs=None):
        if (epoch + 1) % 5 != 0 and epoch != 0:
            return
        # predict all test (careful memory)
        y_pred_probs = self.base.predict(self.X_test, batch_size=self.batch_size, verbose=0)
        preds = decode_batch_predictions(y_pred_probs, self.idx_to_char)
        cer = cer_between_lists(self.true_words_test, preds)
        correct = sum(1 for t, p in zip(self.true_words_test, preds) if t.strip().lower() == p.strip().lower())
        acc = correct / len(self.true_words_test)
        print(f"\n[Callback] Epoch {epoch+1} -> CER: {cer:.4f}, Word Acc: {acc*100:.2f}%")
        # Save a small sample of errors
        errors = []
        for i, (t, p) in enumerate(zip(self.true_words_test, preds)):
            if t.strip().lower() != p.strip().lower():
                errors.append((t, p, i))
            if len(errors) >= 10:
                break
        if errors:
            report_path = self.log_dir / f"errors_epoch_{epoch+1:03d}.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                for t, p, idx in errors:
                    f.write(f"{idx}\tTRUE: {t}\tPRED: {p}\n")

# -----------------------------
# TRANSFER LEARNING (cargar pesos y remapear vocab si necesario)
# -----------------------------
def load_pretrained_weights(base_model, weights_path, strict=False):
    """
    Intenta cargar pesos en base_model. Si shapes coinciden, carga; si no,
    permite cargar capas compatibles y reporta incompatibilidades.
    """
    if weights_path is None:
        return
    if not Path(weights_path).exists():
        print(f"Pretrained weights not found: {weights_path}")
        return
    try:
        base_model.load_weights(weights_path, by_name=True, skip_mismatch=not strict)
        print("Pretrained weights cargados (by_name, skip_mismatch={})".format(not strict))
    except Exception as e:
        print("Error cargando pesos preentrenados:", e)

# -----------------------------
# MAIN
# -----------------------------
def main():
    # 1) read labels
    pairs = read_labels_file(LABELS_FILE)
    if len(pairs) == 0:
        raise RuntimeError("No hay datos en labels.txt")
    # split 80/20
    train_pairs, test_pairs = train_test_split(pairs, test_size=0.2, random_state=42)
    train_pairs, val_pairs = train_test_split(train_pairs, test_size=0.15, random_state=42)  # ~ 68/17/15

    words_all = [w for _, w in pairs]
    char_to_idx, idx_to_char, blank_index = build_vocab_from_words(words_all, include_blank=True)
    num_chars = len(char_to_idx) + 1  # +1 para blank

    # Save vocab
    joblib.dump({"char_to_idx": char_to_idx, "idx_to_char": idx_to_char, "blank_index": blank_index}, VOCAB_SAVE_PATH)
    print(f"Vocab saved to {VOCAB_SAVE_PATH}. Num chars: {len(char_to_idx)}")

    # Build datasets
    train_ds = make_tf_dataset(train_pairs, char_to_idx, blank_index, batch_size=BATCH_SIZE, augment=False, shuffle=True)
    val_ds = make_tf_dataset(val_pairs, char_to_idx, blank_index, batch_size=BATCH_SIZE, augment=False, shuffle=False)

    # Build model
    base = build_crnn_base(input_shape=(IMG_H, IMG_W, 1), num_chars=len(char_to_idx))
    # Optionally load pretrained weights into base
    if PRETRAINED_WEIGHTS:
        load_pretrained_weights(base, PRETRAINED_WEIGHTS, strict=False)
    train_model = build_training_model(base)
    train_model.summary()

    # Prepare X_test for CER callback (we'll load and preprocess to numpy to speed up callback)
    X_test_imgs = []
    true_words_test = []
    for p, w in test_pairs:
        img = load_and_preprocess_image(p)
        X_test_imgs.append(img)
        true_words_test.append(w)
    X_test_imgs = np.array(X_test_imgs, dtype=np.float32)

    # Callbacks
    callbacks = []
    callbacks.append(ModelCheckpoint(str(CHECKPOINT_BEST), monitor='val_loss', save_best_only=True, save_weights_only=True))
    callbacks.append(ModelCheckpoint(str(CHECKPOINT_EPOCH), period=5, monitor='val_loss', save_weights_only=True))  # save every 5 epochs
    callbacks.append(ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=PATIENCE_LR, min_lr=1e-7, verbose=1))
    callbacks.append(EarlyStopping(monitor='val_loss', patience=PATIENCE_ES, restore_best_weights=True, verbose=1))
    callbacks.append(TensorBoard(log_dir=str(TB_LOGDIR)))
    callbacks.append(CSVLogger(str(BASE_DIR / "training_log.csv")))
    callbacks.append(CERCallback(base, X_test_imgs, true_words_test, idx_to_char, batch_size=BATCH_SIZE))

    # Fit
    print("Start training...")
    start_time = time.time()
    history = train_model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    duration = time.time() - start_time
    print(f"Training finished in {duration/60:.2f} minutes")

    # save base inference model and vocab
    base.save(str(MODELS_DIR / "keras_crnn_v3_inference.h5"))
    print("Saved inference model and vocab.")

if __name__ == "__main__":
    main()
