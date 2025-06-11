import joblib
import os
import numpy as np
from preprocesamiento import cargar_datos
from clasificacion import interpretar_prediccion, clasificar_conjunto_datos
import random

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
    def __init__(self, input_size, hidden_size1, hidden_size2, output_size, learning_rate=0.01):
        self.learning_rate = learning_rate
        self.W1 = np.random.randn(input_size, hidden_size1) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size1))
        self.W2 = np.random.randn(hidden_size1, hidden_size2) * np.sqrt(2.0 / hidden_size1)
        self.b2 = np.zeros((1, hidden_size2))
        self.W3 = np.random.randn(hidden_size2, output_size) * np.sqrt(2.0 / hidden_size2)
        self.b3 = np.zeros((1, output_size))
        print(f"Red Neuronal: Inicializada con {input_size} entradas, {hidden_size1} y {hidden_size2} ocultas, {output_size} salidas.")


    def relu(self, z):
        #Funcion de activacion ReLU(Unidad lineal rectificada)
        return np.maximum(0, z)
    
    def relu_derivative(self, z):
        #Derivada de la funcion de activacion ReLU
        return (z > 0).astype(float)
     
    #######################################
    #cambio de funcion de sigmoid a relu porque la funcion de activacion ReLU es mas eficiente.
    #def sigmoid(self, z):
        #return 1 / (1 + np.exp(-z))

    #def sigmoid_derivative(self, z):
    #    return self.sigmoid(z) * (1 - self.sigmoid(z))

    ######################################

    def softmax(self, z):
        exp_z = np.exp(z - np.max(z)) # Evitar overflow
        return exp_z / exp_z.sum(axis=1, keepdims=True)

    def fit(self, X, y, epochs=200, lambda_reg=0.01, batch_size=128):
        y_one_hot = np.eye(self.W3.shape[1])[y.astype(int)]
        num_samples = X.shape[0]
        for epoch in range(epochs):
            indices = np.arange(num_samples)
            np.random.shuffle(indices)
            X_shuffled = X[indices]
            y_shuffled = y_one_hot[indices]
            for i in range(0, num_samples, batch_size):
                X_batch = X_shuffled[i:i + batch_size]
                y_batch = y_shuffled[i:i + batch_size]
                # Forward
                Z1 = np.dot(X_batch, self.W1) + self.b1
                A1 = self.relu(Z1)
                Z2 = np.dot(A1, self.W2) + self.b2
                A2 = self.relu(Z2)
                Z3 = np.dot(A2, self.W3) + self.b3
                A3 = self.softmax(Z3)
                # Backward
                dZ3 = A3 - y_batch
                dW3 = np.dot(A2.T, dZ3) / X_batch.shape[0] + lambda_reg * self.W3
                db3 = np.sum(dZ3, axis=0, keepdims=True) / X_batch.shape[0]
                dZ2 = np.dot(dZ3, self.W3.T) * self.relu_derivative(Z2)
                dW2 = np.dot(A1.T, dZ2) / X_batch.shape[0] + lambda_reg * self.W2
                db2 = np.sum(dZ2, axis=0, keepdims=True) / X_batch.shape[0]
                dZ1 = np.dot(dZ2, self.W2.T) * self.relu_derivative(Z1)
                dW1 = np.dot(X_batch.T, dZ1) / X_batch.shape[0] + lambda_reg * self.W1
                db1 = np.sum(dZ1, axis=0, keepdims=True) / X_batch.shape[0]
                # Update
                self.W1 -= self.learning_rate * dW1
                self.b1 -= self.learning_rate * db1
                self.W2 -= self.learning_rate * dW2
                self.b2 -= self.learning_rate * db2
                self.W3 -= self.learning_rate * dW3
                self.b3 -= self.learning_rate * db3
            if epoch % 100 == 0:
                Z1 = np.dot(X, self.W1) + self.b1
                A1 = self.relu(Z1)
                Z2 = np.dot(A1, self.W2) + self.b2
                A2 = self.relu(Z2)
                Z3 = np.dot(A2, self.W3) + self.b3
                A3 = self.softmax(Z3)
                loss = -np.sum(y_one_hot * np.log(A3 + 1e-9)) / X.shape[0]
                print(f"Epoch {epoch}, Pérdida: {loss:.4f}")

    def predict(self, X):
        # Clasifica datos después del entrenamiento
        Z1 = np.dot(X, self.W1) + self.b1
        A1 = self.relu(Z1)
        Z2 = np.dot(A1, self.W2) + self.b2
        A2 = self.relu(Z2)
        Z3 = np.dot(A2, self.W3) + self.b3
        A3 = self.softmax(Z3)
        return np.argmax(A3, axis=1)
    




def entrenar_modelos(K=3): #K=3 es el numero de vecinos mas cercanos 
    print("Cargando datos de entrenamiento...")
    #X_train, y_train = cargar_datos('data/data/training_data')
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_training_data = os.path.join(directorio_actual, "..", "data", "data", "dataset")
    X_train, y_train = cargar_datos(ruta_training_data, is_training= False)  # Cargar datos de entrenamiento con modificaciones
    



    print("Entrenando modelo KNN...")
    knn = KNN(k=K)
    knn.fit(X_train, y_train)
    print("Modelo KNN entrenado con éxito.")

    directorio_modelos = os.path.join(directorio_actual, "..", "models")
    if not os.path.exists(directorio_modelos):
        os.makedirs(directorio_modelos)


    #crear y entrenar modelo de Red Neuronal
    print("Entrenando modelo Red Neuronal...")
    input_size = X_train.shape[1]  # 28x28 = 784
    output_size = int(np.max(y_train)) + 1 #Numero de clases (digitos 0-9 y letras A-Z)
    #nn = NeuralNetwork(input_size=input_size, hidden_size=64, output_size=output_size)
    #nn = NeuralNetwork(input_size=input_size, hidden_size=128, output_size=output_size, learning_rate=0.01)    #en hidden_size podemos cambiar el numero de neuronas

    nn = NeuralNetwork(input_size=input_size, hidden_size1=128, hidden_size2=64, output_size=output_size, learning_rate=0.01)

    nn.fit(X_train, y_train, epochs=1000) #podemos cambiar el numero de epocas

    ruta_knn = os.path.join(directorio_modelos, 'knn_model.pkl')
    joblib.dump(knn, ruta_knn)
    print(f"Modelo KNN guardado en {ruta_knn}.")

    # Guardar el modelo de Red Neuronal
    ruta_nn = os.path.join(directorio_modelos, 'nn_model.pkl')
    joblib.dump(nn, ruta_nn)
    print(f"Modelo Red Neuronal guardado en {ruta_nn}.")


def evaluar_modelos(ruta_datos, knn, nn):
    print("Evaluando modelos en el conjunto de prueba ...")
    knn_preds, nn_preds, y_true = clasificar_conjunto_datos(ruta_datos, knn, nn)
    knn_precision = np.mean(knn_preds == y_true)
    nn_precision = np.mean(nn_preds == y_true)
    print(f"Precisión KNN en prueba: {knn_precision * 100:.2f}")
    print(f"Precisión Red Neuronal en prueba: {nn_precision * 100:.2f}")



if __name__ == '__main__':
    entrenar_modelos()

    ruta_knn = os.path.join('models', 'knn_model.pkl')
    ruta_nn = os.path.join('models', 'nn_model.pkl')

    knn = joblib.load(ruta_knn)
    nn = joblib.load(ruta_nn)

    #Prediccion con retroalimentacion
    print("Cargando datos de prueba...")
    X_test, y_test = cargar_datos('data/data/testing_data' , is_training=False)  # Cargar datos de prueba sin modificaciones

    ruta_testing_data = os.path.join('data', 'data', 'testing_data')
    evaluar_modelos(ruta_testing_data, knn, nn)
    
    #predecir_corregido(knn, X_test, y_test)



#cada que cargues los datos, ejemplo Red Neuronal: Inicializada con 784 entradas, 128 neuronas ocultas y 36 salidas.
#el numero de entradas es 784 porque las imagenes son de 28x28 pixeles, 28*28=784 de pa parte de preprocesamiento.py
#el numero de neuronas ocultas puede ser cambiado, en este caso se puso 128
#el numero de salidas es 36 porque son 36 clases (26 letras y 10 numeros)
#el learning rate es 0.01, este valor puede ser cambiado
#el numero de epocas es 1000, este valor puede ser cambiado
