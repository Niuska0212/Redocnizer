import os
import sys
import joblib
import cv2
import numpy as np

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from src.entrenamiento import NeuralNetwork, KNN  # Asegúrate de importar KNN si es clase propia
from src.clasificacion import clasificar_imagen

# Mapeo de etiquetas
etiqueta_a_num = {}
num_a_etiqueta = {}

# Números
for i in range(10):
    etiqueta_a_num[str(i)] = i
    num_a_etiqueta[i] = str(i)
# Mayúsculas
for i in range(26):
    etiqueta_a_num[chr(65 + i)] = 10 + i
    num_a_etiqueta[10 + i] = chr(65 + i)
# Minúsculas
for i in range(26):
    etiqueta_a_num[chr(97 + i)] = 36 + i
    num_a_etiqueta[36 + i] = chr(97 + i)

def interpretar_prediccion(valor):
    if 0 <= valor <= 9:
        return str(valor)
    elif 10 <= valor <= 35:
        return chr(valor + 55)
    elif 36 <= valor <= 61:
        return chr(valor + 61)  # Ajusta si usas minúsculas
    else:
        return num_a_etiqueta.get(valor, "No se reconoce")

def predecir_corregido_imagen(ruta_imagen, modelo):
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        raise ValueError(f"No se pudo cargar la imagen en {ruta_imagen}")
    imagen = cv2.resize(imagen, (28, 28)).flatten().astype(np.float32) / 255.0

    pred = modelo.predict(np.array([imagen]))[0]
    print(f"Predicción actual: {interpretar_prediccion(pred)}")

    if isinstance(modelo, NeuralNetwork):
        Z1 = np.dot(np.array([imagen]), modelo.W1) + modelo.b1
        A1 = modelo.relu(Z1)
        Z2 = np.dot(A1, modelo.W2) + modelo.b2
        A2 = modelo.softmax(Z2)
        confianza = A2[0, pred] * 100
        print(f"Confianza: {confianza:.2f}%")

    respuesta = input("¿Es correcta la predicción? (s/n): ").strip().lower()
    if respuesta == 'n':
        etiqueta_letra = input("Ingrese la etiqueta correcta (ejemplo: 0-9, A-Z, a-z): ").strip()
        etiqueta_correcta = etiqueta_a_num.get(etiqueta_letra)
        if etiqueta_correcta is None:
            print("Etiqueta no válida.")
            return
        modelo.fit(np.array([imagen]), np.array([etiqueta_correcta]))
        print("El modelo se ha actualizado con la nueva información.")
    else:
        print("La predicción es aceptada.")

if __name__ == '__main__':
    print("Cargando modelos entrenados...")
    knn_model = joblib.load("models/knn_model.pkl")
    nn_model = joblib.load("models/nn_model.pkl")

    ruta_prueba = input("Ruta de la imagen a probar: ").strip()
    if not os.path.exists(ruta_prueba):
        print("La ruta no existe.")
        sys.exit(1)

    knn_pred, nn_pred = clasificar_imagen(ruta_prueba, knn_model, nn_model)
    print(f"Predicción KNN: {interpretar_prediccion(knn_pred)}")
    print(f"Predicción Red Neuronal: {interpretar_prediccion(nn_pred)}")

    opcion = input("\n¿Deseas corregir la predicción del modelo KNN? (s/n): ").strip().lower()
    if opcion == 's':
        predecir_corregido_imagen(ruta_prueba, knn_model)

    opcion = input("\n¿Deseas corregir la predicción del modelo Red Neuronal? (s/n): ").strip().lower()
    if opcion == 's':
        predecir_corregido_imagen(ruta_prueba, nn_model)