import joblib
import os
import numpy as np
from preprocesamiento import cargar_datos

# Implementación manual de KNN
class KNN:
    def __init__(self, k=3):
        self.k = k
        self.X_train = None
        self.y_train = None

    def fit(self, X, y):
        # Almacena los datos de entrenamiento
        self.X_train = X
        self.y_train = y
        print(f"KNN: Datos de entrenamiento almacenados. Tamaño: {X.shape}")

    def predict(self, X):
        # Clasifica cada muestra de X basado en la distancia a los vecinos más cercanos
        y_pred = []
        for x in X:
            distancia = np.linalg.norm(self.X_train - x, axis=1)  # Calcular distancia euclidiana
            indices_vecinos = np.argsort(distancia)[:self.k]
            etiquetas_vecinos = self.y_train[indices_vecinos]
            etiqueta_predicha = np.bincount(etiquetas_vecinos.astype(int)).argmax()
            y_pred.append(etiqueta_predicha)
        return np.array(y_pred)


# Implementación manual de una red neuronal simple con una capa oculta
class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.learning_rate = learning_rate
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros((1, output_size))
        print(f"Red Neuronal: Inicializada con {input_size} entradas, {hidden_size} neuronas ocultas y {output_size} salidas.")

    def sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def sigmoid_derivative(self, z):
        return self.sigmoid(z) * (1 - self.sigmoid(z))

    def softmax(self, z):
        exp_z = np.exp(z - np.max(z))
        return exp_z / exp_z.sum(axis=1, keepdims=True)

    def fit(self, X, y, epochs=500):
        # Entrena la red con descenso de gradiente
        y = np.eye(np.max(y) + 1)[y.astype(int)]  # One-hot encoding
        for epoch in range(epochs):
            # Forward Propagation
            Z1 = np.dot(X, self.W1) + self.b1
            A1 = self.sigmoid(Z1)
            Z2 = np.dot(A1, self.W2) + self.b2
            A2 = self.softmax(Z2)

            # Backward Propagation
            dZ2 = A2 - y
            dW2 = np.dot(A1.T, dZ2) / X.shape[0]
            db2 = np.sum(dZ2, axis=0, keepdims=True) / X.shape[0]

            dZ1 = np.dot(dZ2, self.W2.T) * self.sigmoid_derivative(Z1)
            dW1 = np.dot(X.T, dZ1) / X.shape[0]
            db1 = np.sum(dZ1, axis=0, keepdims=True) / X.shape[0]

            # Gradient Descent
            self.W1 -= self.learning_rate * dW1
            self.b1 -= self.learning_rate * db1
            self.W2 -= self.learning_rate * dW2
            self.b2 -= self.learning_rate * db2

            if epoch % 100 == 0:
                loss = -np.sum(y * np.log(A2)) / X.shape[0]
                print(f"Epoch {epoch}, Pérdida: {loss:.4f}")

    def predict(self, X):
        # Clasifica datos después del entrenamiento
        Z1 = np.dot(X, self.W1) + self.b1
        A1 = self.sigmoid(Z1)
        Z2 = np.dot(A1, self.W2) + self.b2
        A2 = self.softmax(Z2)
        return np.argmax(A2, axis=1)


def entrenar_modelos(K=3):
    print("Cargando datos de entrenamiento...")
    #X_train, y_train = cargar_datos('data/data/training_data')
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_training_data = os.path.join(directorio_actual, "..", "data", "data", "training_data")
    X_train, y_train = cargar_datos(ruta_training_data)

    # Verificaciones
    #print(f"Datos de entrenamiento cargados: {X_train.shape} muestras, {y_train.shape} etiquetas.")
    #print(f"Ejemplo de etiquetas: {np.unique(y_train)}")
    #print(f"Primera muestra (normalizada): {X_train[0]}")
    #print(f"Primera etiqueta: {y_train[0]}")

    print("Entrenando modelo KNN...")
    knn = KNN(k=K)
    knn.fit(X_train, y_train)
    print("Modelo KNN entrenado con éxito.")

    # Verificar si el directorio 'models' existe, si no, crearlo
    directorio_modelos = 'models'
    if not os.path.exists(directorio_modelos):
        os.makedirs(directorio_modelos)

    # Guardar el modelo KNN
    ruta_knn = os.path.join(directorio_modelos, 'knn_model.pkl')
    joblib.dump(knn, ruta_knn)
    print(f"Modelo KNN guardado en {ruta_knn}.")

    print("Entrenando modelo Red Neuronal...")
    input_size = X_train.shape[1]  # 28x28 = 784
    output_size = len(set(y_train))
    #nn = NeuralNetwork(input_size=input_size, hidden_size=64, output_size=output_size)
    nn = NeuralNetwork(input_size=input_size, hidden_size=128, output_size=output_size, learning_rate=0.01)    #en hidden_size podemos cambiar el numero de neuronas
    nn.fit(X_train, y_train, epochs=1000) #podemos cambiar el numero de epocas

    # Guardar el modelo de Red Neuronal
    ruta_nn = os.path.join(directorio_modelos, 'nn_model.pkl')
    joblib.dump(nn, ruta_nn)
    print(f"Modelo Red Neuronal guardado en {ruta_nn}.")


if __name__ == '__main__':
    entrenar_modelos()



#cada que cargues los datos, ejemplo Red Neuronal: Inicializada con 784 entradas, 128 neuronas ocultas y 36 salidas.
#el numero de entradas es 784 porque las imagenes son de 28x28 pixeles, 28*28=784 de pa parte de preprocesamiento.py
#el numero de neuronas ocultas puede ser cambiado, en este caso se puso 128
#el numero de salidas es 36 porque son 36 clases (26 letras y 10 numeros)
#el learning rate es 0.01, este valor puede ser cambiado
#el numero de epocas es 1000, este valor puede ser cambiado
