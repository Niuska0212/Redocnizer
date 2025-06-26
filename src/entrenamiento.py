import joblib
import pandas as pd
import os
import re
import numpy as np
from preprocesamiento import modificar_imagen, cargar_datos_split # Mantener estas importaciones aquí

import random
from sklearn.metrics import confusion_matrix, classification_report
import cv2

# --- Clase ConvolutionalNeuralNetwork (sin cambios) ---
class ConvolutionalNeuralNetwork:
    def __init__(self, input_shape=(28, 28), num_filters=32, filter_size=3, pool_size=2):
        self.input_shape = input_shape
        self.num_filters = num_filters
        self.filter_size = filter_size
        self.pool_size = pool_size
        
        self.filters = [np.random.randn(filter_size, filter_size).astype(np.float32) * np.sqrt(2.0/(filter_size*filter_size)) 
                       for _ in range(num_filters)]
        
    def relu(self, x):
        return np.maximum(0, x)
    
    def max_pool(self, image, pool_size):
        h, w = image.shape
        new_h = h // pool_size
        new_w = w // pool_size
        pooled = np.zeros((new_h, new_w))
        
        for i in range(new_h):
            for j in range(new_w):
                patch = image[i*pool_size:(i+1)*pool_size, j*pool_size:(j+1)*pool_size]
                pooled[i, j] = np.max(patch)
        return pooled
    
    def convolve(self, image, filters):
        image_h, image_w = image.shape
        num_filters = len(filters)
        filter_h, filter_w = filters[0].shape
        
        output_h = image_h - filter_h + 1
        output_w = image_w - filter_w + 1
        
        conv_output = np.zeros((num_filters, output_h, output_w))
        
        for f_idx, current_filter in enumerate(filters):
            for i in range(output_h):
                for j in range(output_w):
                    patch = image[i:i+filter_h, j:j+filter_w]
                    conv_output[f_idx, i, j] = np.sum(patch * current_filter)
        return conv_output
    
    def extraer_caracteristicas(self, image):
        image = image.astype(np.float32)
        conv_output = self.convolve(image, self.filters)
        activated_output = self.relu(conv_output)
        pooled_output = np.array([self.max_pool(activated_output[f], self.pool_size) 
                                  for f in range(self.num_filters)])
        return pooled_output

# --- Clase RedNeuronal (sin cambios) ---
class RedNeuronal:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))

    def relu(self, x):
        return np.maximum(0, x)

    def relu_derivative(self, x):
        return (x > 0).astype(float)

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def cross_entropy_loss(self, predictions, targets):
        epsilon = 1e-10 
        loss = -np.sum(targets * np.log(predictions + epsilon)) / len(predictions)
        return loss

    def forward(self, X):
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.softmax(self.z2) 
        return self.a2

    def backward(self, X, y_true):
        num_samples = X.shape[0]
        delta2 = self.a2 - y_true
        self.dW2 = np.dot(self.a1.T, delta2) / num_samples
        self.db2 = np.sum(delta2, axis=0, keepdims=True) / num_samples
        delta1 = np.dot(delta2, self.W2.T) * self.relu_derivative(self.z1)
        self.dW1 = np.dot(X.T, delta1) / num_samples
        self.db1 = np.sum(delta1, axis=0, keepdims=True) / num_samples

    def update_weights(self, lambda_reg=0.0):
        self.W1 -= self.learning_rate * (self.dW1 + lambda_reg * self.W1)
        self.b1 -= self.learning_rate * self.db1
        self.W2 -= self.learning_rate * (self.dW2 + lambda_reg * self.W2)
        self.b2 -= self.learning_rate * self.db2

    def fit(self, X_train, y_train, epochs=100, batch_size=32, lambda_reg=0.01, learning_rate_decay=1.0, early_stopping_rounds=None):
        num_samples = X_train.shape[0]
        history = {'loss': [], 'accuracy': []}
        best_loss = float('inf')
        epochs_no_improve = 0

        if y_train.ndim == 1:
            y_train_one_hot = np.zeros((num_samples, self.output_size))
            y_train_one_hot[np.arange(num_samples), y_train] = 1
        else:
            y_train_one_hot = y_train 

        for epoch in range(epochs):
            permutation = np.random.permutation(num_samples)
            X_shuffled = X_train[permutation]
            y_shuffled_one_hot = y_train_one_hot[permutation]

            epoch_loss = 0
            epoch_correct_predictions = 0

            for i in range(0, num_samples, batch_size):
                X_batch = X_shuffled[i:i+batch_size]
                y_batch_one_hot = y_shuffled_one_hot[i:i+batch_size]
                
                predictions = self.forward(X_batch)
                loss = self.cross_entropy_loss(predictions, y_batch_one_hot)
                epoch_loss += loss * X_batch.shape[0] 
                
                self.backward(X_batch, y_batch_one_hot)
                self.update_weights(lambda_reg)

                predicted_classes = np.argmax(predictions, axis=1)
                true_classes = np.argmax(y_batch_one_hot, axis=1)
                epoch_correct_predictions += np.sum(predicted_classes == true_classes)

            epoch_loss /= num_samples 
            epoch_accuracy = epoch_correct_predictions / num_samples
            
            history['loss'].append(epoch_loss)
            history['accuracy'].append(epoch_accuracy)


            if (epoch + 1) % 50 == 0 or (epoch + 1) == epochs:
                # Imprimir el progreso cada 10 épocas o en la última época
                print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}, Accuracy: {epoch_accuracy*100:.2f}%")

            self.learning_rate *= learning_rate_decay

            if early_stopping_rounds:
                if epoch_loss < best_loss:
                    best_loss = epoch_loss
                    epochs_no_improve = 0
                else:
                    epochs_no_improve += 1
                    if epochs_no_improve >= early_stopping_rounds:
                        print(f"Early stopping en Epoch {epoch+1} debido a que la pérdida no mejoró por {early_stopping_rounds} épocas.")
                        break

    def predict(self, X):
        probabilities = self.forward(X)
        return np.argmax(probabilities, axis=1)


# --- Inicio del script de entrenamiento ---
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
        max_por_carpeta=500
    )

    num_classes = len(class_labels_map)
    print(f"Número de clases detectadas: {num_classes}")
    print(f"Mapeo de clases: {class_labels_map}")

    X_train_cnn = np.array([cv2.resize(img, (28, 28)).astype(np.float32) / 255.0 for img in X_train_raw.reshape(-1, 28, 28)])
    X_test_cnn = np.array([cv2.resize(img, (28, 28)).astype(np.float32) / 255.0 for img in X_test_raw.reshape(-1, 28, 28)])

    X_train_augmented = []
    y_train_augmented = []
    for i in range(len(X_train_cnn)):
        img = (X_train_cnn[i] * 255).astype(np.uint8)
        augmented_img = modificar_imagen(img)
        X_train_augmented.append(augmented_img.astype(np.float32) / 255.0)
        y_train_augmented.append(y_train[i])
    
    X_train_cnn = np.array(X_train_augmented)
    y_train = np.array(y_train_augmented)

    cnn = ConvolutionalNeuralNetwork(input_shape=(28, 28), num_filters=32, filter_size=3, pool_size=2)
    

    print("Extrayendo características con CNN para el conjunto de entrenamiento...")
    X_train_features = []
    for img in X_train_cnn:
        features = cnn.extraer_caracteristicas(img).flatten()
        X_train_features.append(features)
    X_train_features = np.array(X_train_features)
    
    print("Extrayendo características con CNN para el conjunto de prueba...")
    X_test_features = []
    for img in X_test_cnn:
        features = cnn.extraer_caracteristicas(img).flatten()
        X_test_features.append(features)
    X_test_features = np.array(X_test_features)

    input_size_nn = X_train_features.shape[1]
    print(f"Tamaño de las características de entrada para la NN: {input_size_nn}")

    hidden_size = 512  # Tamaño del layer oculto, puedes ajustar este valor
    output_size = num_classes
    nn = RedNeuronal(input_size=input_size_nn, hidden_size=hidden_size, output_size=output_size, learning_rate=0.01)

    print("\nEntrenando Red Neuronal...")
    nn.fit(X_train_features, y_train, 
           epochs=1000,
           batch_size=256,
           lambda_reg=0.001,
           learning_rate_decay=0.995,
           early_stopping_rounds=50)

    print("\nGuardando modelos...")
    joblib.dump(nn, os.path.join(ruta_modelos, "nn_model_mejorado.pkl"))
    joblib.dump(cnn, os.path.join(ruta_modelos, "cnn_model.pkl"))
    joblib.dump(class_labels_map, os.path.join(ruta_modelos, "class_labels_map.pkl"))

    print("Modelos guardados exitosamente.")

    print("\nEvaluando modelo en conjunto de prueba...")

    test_preds_indices = nn.predict(X_test_features)

    test_acc = np.mean(test_preds_indices == y_test)
    print(f"Precisión en prueba: {test_acc*100:.2f}%")

    class_names = [k for k, v in sorted(class_labels_map.items(), key=lambda item: item[1])]
    print("\nReporte de Clasificación en prueba:")
    #print(classification_report(y_test, test_preds_indices, target_names=class_names, zero_division=0))

    print("\nMatriz de Confusión en prueba:")
    conf_matrix = confusion_matrix(y_test, test_preds_indices)
    #print(conf_matrix)

    with open(os.path.join(ruta_modelos, "evaluacion_modelo_CNN_mejorado.txt"), "w") as f:
        f.write("=== Evaluación de Modelos ===\n\n")
        #f.write(f"Precisión Red Neuronal en prueba: {test_acc*100:.2f}%\n\n")
        f.write("Etiquetas de clase:\n")
        f.write(", ".join(class_names) + "\n\n")
        f.write("Reporte de Clasificación Red Neuronal:\n")
        f.write(classification_report(y_test, test_preds_indices, target_names=class_names, zero_division=0))
        f.write("\nMatriz de confusión Red Neuronal:\n")
        f.write(str(conf_matrix))

    print("\nEvaluación completada y guardada.")