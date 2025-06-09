import os
import sys
import joblib
import cv2
import numpy as np

# Obtén la ruta absoluta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Agrega la carpeta src al PYTHONPATH
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from src.entrenamiento import entrenar_modelos, NeuralNetwork
from src.clasificacion import clasificar_imagen

def interpretar_prediccion(valor):
    if 0 <= valor <= 9:
        return str(valor)   # Números 0-9
    elif 10 <= valor <= 35:
        return chr(valor + 55)  # Letras A-Z (A=10, B=11, ...)
    else:
        return "No se reconoce"

def predecir_corregido_imagen(ruta_imagen, modelo):
    """
    Realiza la predicción para una imagen en particular y permite la corrección si es necesario.
    Actualiza el modelo con la nueva etiqueta en caso de que la predicción sea incorrecta.
    """
    # Cargar y preprocesar la imagen (igual que en clasificar_imagen)
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        raise ValueError(f"No se pudo cargar la imagen en {ruta_imagen}")
    imagen = cv2.resize(imagen, (28, 28)).flatten().astype(np.float32) / 255.0 #

    # Realizar la predicción
    pred = modelo.predict(np.array([imagen]))[0]
    print(f"Predicción actual: {interpretar_prediccion(pred)}")
    
    # Si el modelo es una red neuronal, calcular y mostrar el porcentaje de confianza
    if isinstance(modelo, NeuralNetwork):
        Z1 = np.dot(np.array([imagen]), modelo.W1) + modelo.b1
        A1 = modelo.relu(Z1)
        Z2 = np.dot(A1, modelo.W2) + modelo.b2
        A2 = modelo.softmax(Z2)
        confianza = A2[0, pred] * 100
        print(f"Confianza: {confianza:.2f}%")
    
    # Solicitar retroalimentación
    respuesta = input("¿Es correcta la predicción? (s/n): ").strip().lower()
    if respuesta == 'n':
        etiqueta_correcta = int(input("Ingrese la etiqueta correcta (en formato numérico, por ejemplo, 0-9 o 10 para A, etc.): "))
        # Actualizar el modelo con el dato corregido
        modelo.fit(np.array([imagen]), np.array([etiqueta_correcta]))
        print("El modelo se ha actualizado con la nueva información.")
    else:
        print("La predicción es aceptada.")

if __name__ == '__main__':
    # Entrenar modelos
    #sentrenar_modelos()

    # Cargar modelos entrenados
    print("Cargando modelos entrenados...")
    knn_model = joblib.load("models/knn_model.pkl")
    nn_model = joblib.load("models/nn_model.pkl")

    # Probar clasificación en una imagen de prueba
    print("\nProbando clasificación en una imagen de prueba...")
    ruta_prueba = 'data/data/testing_data/debug/debug_modificada_3 copy.png'
    knn_pred, nn_pred = clasificar_imagen(ruta_prueba, knn_model, nn_model)
    
    print(f"Predicción KNN: {interpretar_prediccion(knn_pred)}")
    print(f"Predicción Red Neuronal: {interpretar_prediccion(nn_pred)}")
    
    # Ofrecer corrección interactiva para KNNn
    
    opcion = input("\n¿Deseas corregir la predicción del modelo KNN? (s/n): ").strip().lower()
    if opcion == 's':
        predecir_corregido_imagen(ruta_prueba, knn_model)
    
    # Ofrecer corrección interactiva para la Red Neuronal
    opcion = input("\n¿Deseas corregir la predicción del modelo Red Neuronal? (s/n): ").strip().lower()
    if opcion == 's':
        predecir_corregido_imagen(ruta_prueba, nn_model)






#Resumen
#✅ preprocesamiento.py → Carga imágenes en un formato numérico.
#✅ entrenamiento.py → Entrena KNN + Red Neuronal con TODAS las imágenes a la vez.
#✅ clasificacion.py → Usa los modelos entrenados para predecir letras/números en nuevas imágenes.
#✅ main.py → Ejecuta todo el proceso automáticamente.