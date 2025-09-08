import os
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization, RandomRotation, RandomZoom, RandomTranslation, RandomShear
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Importar tu función de carga de datos
from preprocesamientoV2 import cargar_datos_split

# --- Funciones Auxiliares ---
def interpretar_prediccion(prediccion_softmax, class_labels_map):
    indice_predicho = np.argmax(prediccion_softmax)
    letra_predicha = next(key for key, value in class_labels_map.items() if value == indice_predicho)
    return letra_predicha

def etiqueta_a_letra(etiquetas_indices, class_labels_map):
    index_to_label_map = {v: k for k, v in class_labels_map.items()}
    return [index_to_label_map[idx] for idx in etiquetas_indices]

# --- Inicio del Script de Entrenamiento ---
if __name__ == "__main__":
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_dataset_principal = os.path.join(ruta_base, "..", "data", "data", "dataset")
    ruta_modelos = os.path.join(ruta_base, "..", "models")
    os.makedirs(ruta_modelos, exist_ok=True)

    print(f"Cargando datos del directorio: {ruta_dataset_principal}")
    X_train_raw, X_test_raw, y_train, y_test, class_labels_map = cargar_datos_split(
        ruta_dataset_principal,
        test_size=0.3,
        random_state=42,
        max_por_carpeta=None,
        num_workers=os.cpu_count()
    )

    num_classes = len(class_labels_map)

    # --- Preprocesamiento de Datos para Keras ---
    X_train_keras = X_train_raw.reshape(-1, 28, 28, 1).astype(np.float32)
    X_test_keras = X_test_raw.reshape(-1, 28, 28, 1).astype(np.float32)
    y_train_keras = to_categorical(y_train, num_classes=num_classes)
    y_test_keras = to_categorical(y_test, num_classes=num_classes)

    print(f"Forma de entrada para Keras (entrenamiento): {X_train_keras.shape}")
    print(f"Forma de etiquetas para Keras (entrenamiento): {y_train_keras.shape}")

    # --- Definición del Modelo Keras con Aumento de Datos y Dropout ---
    model = Sequential([
        tf.keras.Input(shape=(28, 28, 1)),

        # Capas de Aumento de Datos
        RandomRotation(factor=0.04, seed=42, name='data_augmentation_rotation'),
        RandomZoom(height_factor=0.1, width_factor=0.1, seed=42, name='data_augmentation_zoom'),
        RandomTranslation(height_factor=0.1, width_factor=0.1, seed=42, name='data_augmentation_translation'),
        # RandomShear(x_factor=(0.2), y_factor=(0.2), fill_mode='constant', fill_value=0),

        # Capa de normalización
        tf.keras.layers.Rescaling(1./255, name='rescaling_pixels'),

        # Capas Convolucionales y de Pooling
        Conv2D(64, (3, 3), activation='relu', name='conv_layer_1'),
        MaxPooling2D((2, 2), name='pooling_layer_1'),

        Conv2D(128, (3, 3), activation='relu', name='conv_layer_2'),
        MaxPooling2D((2, 2), name='pooling_layer_2'),

        Conv2D(256, (3, 3), activation='relu', name='conv_layer_3'),
        MaxPooling2D((2, 2), name='pooling_layer_3'), # Salida aquí es (None, 1, 1, 256)

        # --- NUEVA CAPA CONVOLUCIONAL ---
        # No se añade un MaxPooling2D después de esta si la salida ya es 1x1.
        # Si la salida de pooling_layer_3 fuera mayor a 1x1, podrías añadir un MaxPooling2D aquí.
        # En este caso, la conv_layer_3 + pooling_layer_3 ya reducen a 1x1.
        # Para que esta capa conv_layer_4 tenga un impacto, los kernels deberían ser (1,1)
        # o tendríamos que cambiar las capas de pooling anteriores.
        # Si la intención es solo añadir capacidad sin más reducción espacial,
        # simplemente la agregamos sin pooling.
        Conv2D(512, (1, 1), activation='relu', name='conv_layer_4'), # Usar (1,1) kernel si la entrada es 1x1

        Conv2D(1024, (1, 1), activation='relu', name='conv_layer_5'),

        # Aplanar las características
        Flatten(name='flatten_features'),

        # Capa Densa (Fully Connected)
        Dense(512, activation='relu', name='hidden_dense_layer'),

        # Capa de Dropout para regularización
        Dropout(0.5, name='dropout_layer'),

        # Capa de Salida
        Dense(num_classes, activation='softmax', name='outputent_layer')
    ])

    # --- Compilar el Modelo ---
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.summary()

    # --- Callbacks para Early Stopping y Reducción del Learning Rate ---
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=20, # Aumenté la paciencia para dar más oportunidades al modelo más grande
        restore_best_weights=True,
        verbose=1
    )

    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=8, # Aumenté la paciencia aquí también
        min_lr=0.000001,
        verbose=1
    )

    print("\nEntrenando Modelo Keras con Early Stopping, Dropout y Aumento de Datos...")
    history = model.fit(
        X_train_keras, y_train_keras,
        epochs=300,
        batch_size=128,
        validation_data=(X_test_keras, y_test_keras),
        callbacks=[early_stopping, reduce_lr],
        verbose=1
    )

    print("\nEvaluando Modelo Keras en conjunto de prueba...")
    loss, accuracy = model.evaluate(X_test_keras, y_test_keras, verbose=0)
    print(f"Precisión en prueba (Keras): {accuracy*100:.2f}%")

    model_save_path = os.path.join(ruta_modelos, "keras_cnn_model_augmented.h5")
    model.save(model_save_path)
    joblib.dump(class_labels_map, os.path.join(ruta_modelos, "class_labels_map.pkl"))

    print("Modelos Keras y mapeo de clases guardados exitosamente.")

    # --- Generar Reporte de Clasificación y Matriz de Confusión ---
    y_pred_probs = model.predict(X_test_keras)
    y_pred_indices = np.argmax(y_pred_probs, axis=1)
    y_true_indices = np.argmax(y_test_keras, axis=1)

    class_names = [k for k, v in sorted(class_labels_map.items(), key=lambda item: item[1])]

    print("\nReporte de Clasificación en prueba (Keras):")
    print(classification_report(y_true_indices, y_pred_indices, target_names=class_names, zero_division=0))

    print("\nMatriz de Confusión en prueba (Keras):")
    conf_matrix = confusion_matrix(y_true_indices, y_pred_indices)
    print(conf_matrix)

    with open(os.path.join(ruta_modelos, "evaluacion_modelo_keras_augmented.txt"), "w") as f:
        f.write("=== Evaluación de Modelo Keras con Aumento de Datos ===\n\n")
        f.write(f"Precisión en prueba: {accuracy*100:.2f}%\n\n")
        f.write("Etiquetas de clase:\n")
        f.write(", ".join(class_names) + "\n\n")
        f.write("Reporte de Clasificación:\n")
        f.write(classification_report(y_true_indices, y_pred_indices, target_names=class_names, zero_division=0))
        f.write("\nMatriz de confusión:\n")
        f.write(str(conf_matrix))

    print("\nEvaluación completada y guardada (Keras).")