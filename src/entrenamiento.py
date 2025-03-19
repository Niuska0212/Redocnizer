import joblib
import numpy as np
from preprocesamiento import cargar_datos


#implementacion manual de KNN
class KNN:
    def __init__(self, k=3):
        self.k = k
        self.X_train = None
        self.y_train = None

    def fit(self, X, y):
        #Almacena los datos de entrenamiento
        self.X_train = X
        self.y_train = y

    def predict(self, X):
        #Clasifica cada muestra de X basado en la distancia a los vecinos mas cercanos.
        y_pred = []
        for x in X:
            distancia = np.linalg.norm(self.X_train - x, axis=1) #calcular distancia euclidiana
            indices_vecinos = np.argsort(distancia)[:self.k]
            etiquetas_vecinos = self.y_train[indices_vecinos]
            etiqueta_predicha = np.bincount(etiquetas_vecinos.astype(int)).argmax()
            y_pred.append(etiqueta_predicha)
        return np.array(y_pred)

 
 #implementacion manual de una red neuronal simple con una capa oculta
class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.learning_rate = learning_rate
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros((1, output_size))

    def sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def sigmoid_derivative(self, z):
        return self.sigmoid(z) * (1 - self.sigmoid(z))
    
    def softmax(self, z):
        exp_z = np.exp(z - np.max(z))
        return exp_z / exp_z.sum(axis=1, keepdims=True)
    
    def fit(self, X, y, epochs=500):
       #Entrena la red con descenso de gradiente.
       y = np.eye(np.max(y) + 1)[y.astype(int)] #One-hot encoding
       for epoch in range(epochs):
           #Forward Propagation
           Z1 = np.dot(X, self.W1) + self.b1
           A1 = self.sigmoid(Z1)
           Z2 = np.dot(A1, self.W2) + self.b2
           A2 = self.softmax(Z2)
           
           #Backward Propagation
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
                print(f"Epoch {epoch}, Perdida: {loss:.4f}")   #Muestra la perdida cada 100 epocas, si las perdidas disminuyen, el modelo esta aprendiendo.

    def predict(self, X):
        #Clasifica datos despues deñ entrenamiento.
        Z1 = np.dot(X, self.W1) + self.b1
        A1 = self.sigmoid(Z1)
        Z2 = np.dot(A1, self.W2) + self.b2
        A2 = self.softmax(Z2)
        return np.argmax(A2, axis=1)
    
def cargar_datos_corregidos(archivo):
    try:
        datos= np.load(archivo, allow_pickle=True)
        return datos["X"], datos["y"]
    except FileNotFoundError:
        print("No hay datos corregidos")
        return None, None

def entrenar_modelos(K = 3):
    print("Cargando datos de entrenamiento...")
    X_train, y_train = cargar_datos('data/data2/training_data')

    X_corr, y_corr = cargar_datos_corregidos("datos_corregidos.npz")

    if X_corr is not None and y_corr is not None:
        X_train = np.vstack([X_train, X_corr])
        y_train = np.append(y_train, y_corr)

    print("Entrenando modelo KNN...")
    knn = KNN(k=K)
    knn.fit(X_train, y_train)
    joblib.dump(knn, 'models/knn_model.pkl')
    print("Modelo KNN entrenado y guardado.")

    print("Entrenando modelo Red Neuronal...")
    input_size = X_train.shape[1] # 28x28 = 784
    output_size = len(set(y_train))
    nn = NeuralNetwork(input_size = input_size, hidden_size=64, output_size=output_size)
    nn.fit(X_train, y_train, epochs=500)
    joblib.dump(nn, 'models/nn_model.pkl')
    print("Modelo Red Neuronal entrenado y guardado.")


if __name__ == '__main__':
    entrenar_modelos()