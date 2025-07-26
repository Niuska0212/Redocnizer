import os
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix

# Importar las clases de Keras necesarias
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Importar tu función de carga de datos
# Asegúrate de que 'preprocesamiento.py' esté en la misma carpeta o en una ruta accesible
from preprocesamiento import cargar_datos_split

# --- Funciones Auxiliares ---
def interpretar_prediccion(prediccion_softmax, class_labels_map):
    """
    Interpreta las probabilidades de salida de la red neuronal y devuelve la etiqueta de clase predicha.
    """
    indice_predicho = np.argmax(prediccion_softmax)
    # Busca la clave (letra/número) que corresponde al valor (índice)
    letra_predicha = next(key for key, value in class_labels_map.items() if value == indice_predicho)
    return letra_predicha

def etiqueta_a_letra(etiquetas_indices, class_labels_map):
    """
    Convierte una lista de índices numéricos de etiquetas a sus correspondientes letras/caracteres.
    """
    # Invertir el mapeo para ir de índice a letra
    index_to_label_map = {v: k for k, v in class_labels_map.items()}
    return [index_to_label_map[idx] for idx in etiquetas_indices]

# --- Inicio del Script de Entrenamiento ---
if __name__ == "__main__":
    # Define las rutas de tu proyecto
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_dataset_principal = os.path.join(ruta_base, "..", "data", "data", "dataset")
    ruta_modelos = os.path.join(ruta_base, "..", "models")
    os.makedirs(ruta_modelos, exist_ok=True) # Asegúrate de que la carpeta 'models' exista

    print(f"Cargando datos del directorio: {ruta_dataset_principal}")
    X_train_raw, X_test_raw, y_train, y_test, class_labels_map = cargar_datos_split(
        ruta_dataset_principal,
        test_size=0.3,
        random_state=42,
        max_por_carpeta=None, # Mantén esto a None si quieres usar todos los datos
        num_workers=os.cpu_count() # Usa todos los núcleos disponibles para cargar datos más rápido
    )

    num_classes = len(class_labels_map)

    # --- Preprocesamiento de Datos para Keras ---
    # Remodelar las imágenes a (altura, ancho, canales) y normalizar a 0-1
    X_train_keras = X_train_raw.reshape(-1, 28, 28, 1).astype(np.float32) / 255.0
    X_test_keras = X_test_raw.reshape(-1, 28, 28, 1).astype(np.float32) / 255.0

    # Convertir las etiquetas a formato one-hot encoding (necesario para categorical_crossentropy)
    y_train_keras = to_categorical(y_train, num_classes=num_classes)
    y_test_keras = to_categorical(y_test, num_classes=num_classes)

    print(f"Forma de entrada para Keras (entrenamiento): {X_train_keras.shape}")
    print(f"Forma de etiquetas para Keras (entrenamiento): {y_train_keras.shape}")

    # --- Definición del Modelo Keras con Dropout ---
    model = Sequential([
        # Primera Capa Convolucional
        Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1), name='conv_layer_1'),
        
        # Capa de MaxPooling para reducir dimensionalidad
        MaxPooling2D((2, 2), name='pooling_layer_1'),
        
        # Aplanar la salida de las capas convolucionales
        Flatten(name='flatten_features'),
        
        # Capa Densa (Fully Connected)
        Dense(512, activation='relu', name='hidden_dense_layer'),
        
        # Capa de Dropout para regularización
        Dropout(0.5), # Desactiva el 50% de las neuronas aleatoriamente durante el entrenamiento
        
        # Capa de Salida
        Dense(num_classes, activation='softmax', name='output_layer')
    ])

    # --- Compilar el Modelo ---
    # Usamos el optimizador Adam y la función de pérdida cross-entropy categórica
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    # Muestra un resumen de la arquitectura del modelo
    model.summary()

    # --- Callbacks para Early Stopping y Reducción del Learning Rate ---
    # EarlyStopping: Detiene el entrenamiento si la métrica monitoreada no mejora
    early_stopping = EarlyStopping(
        monitor='val_loss',     # Monitorea la pérdida en el conjunto de validación
        patience=25,            # Número de épocas a esperar sin mejora
        restore_best_weights=True, # Restaura los pesos del modelo a la mejor época
        verbose=1               # Muestra mensajes de progreso
    )

    # ReduceLROnPlateau: Reduce la tasa de aprendizaje si la métrica monitoreada se estanca
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,             # Factor por el cual se reducirá el learning rate (ej. 0.2 para reducirlo al 20%)
        patience=10,            # Número de épocas a esperar sin mejora antes de reducir el LR
        min_lr=0.00001,         # Tasa de aprendizaje mínima
        verbose=1               # Muestra mensajes de progreso
    )

    print("\nEntrenando Modelo Keras con Early Stopping y Dropout...")
    # --- Entrenar el Modelo ---
    history = model.fit(
        X_train_keras, y_train_keras,
        epochs=200, # Establece un número alto de épocas, EarlyStopping lo detendrá
        batch_size=128,
        validation_data=(X_test_keras, y_test_keras),
        callbacks=[early_stopping, reduce_lr], # Pasa la lista de callbacks aquí
        verbose=1
    )

    print("\nEvaluando Modelo Keras en conjunto de prueba...")
    # Evaluar el rendimiento final en el conjunto de prueba
    loss, accuracy = model.evaluate(X_test_keras, y_test_keras, verbose=0)
    print(f"Precisión en prueba (Keras): {accuracy*100:.2f}%")

    # --- Guardar el Modelo Keras ---
    # Keras recomienda guardar en formato '.keras' pero '.h5' sigue siendo compatible
    model_save_path = os.path.join(ruta_modelos, "keras_cnn_model.h5")
    model.save(model_save_path)
    joblib.dump(class_labels_map, os.path.join(ruta_modelos, "class_labels_map.pkl"))

    print("Modelos Keras y mapeo de clases guardados exitosamente.")

    # --- Generar Reporte de Clasificación y Matriz de Confusión ---
    # Obtener las predicciones del modelo (probabilidades)
    y_pred_probs = model.predict(X_test_keras)
    # Convertir las probabilidades a índices de clase (la clase con mayor probabilidad)
    y_pred_indices = np.argmax(y_pred_probs, axis=1)

    # Las etiquetas verdaderas ya deben ser índices o convertirlas si son one-hot
    y_true_indices = np.argmax(y_test_keras, axis=1)

    # Preparar los nombres de las clases para el reporte
    class_names = [k for k, v in sorted(class_labels_map.items(), key=lambda item: item[1])]

    print("\nReporte de Clasificación en prueba (Keras):")
    print(classification_report(y_true_indices, y_pred_indices, target_names=class_names, zero_division=0))

    print("\nMatriz de Confusión en prueba (Keras):")
    conf_matrix = confusion_matrix(y_true_indices, y_pred_indices)
    print(conf_matrix)

    # --- Guardar la Evaluación en un Archivo ---
    with open(os.path.join(ruta_modelos, "evaluacion_modelo_keras.txt"), "w") as f:
        f.write("=== Evaluación de Modelo Keras ===\n\n")
        f.write(f"Precisión en prueba: {accuracy*100:.2f}%\n\n")
        f.write("Etiquetas de clase:\n")
        f.write(", ".join(class_names) + "\n\n")
        f.write("Reporte de Clasificación:\n")
        f.write(classification_report(y_true_indices, y_pred_indices, target_names=class_names, zero_division=0))
        f.write("\nMatriz de confusión:\n")
        f.write(str(conf_matrix))

    print("\nEvaluación completada y guardada (Keras).")