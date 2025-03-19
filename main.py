import os
import sys
import joblib

# Obtén la ruta absoluta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Agrega la carpeta src al PYTHONPATH
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from src.entrenamiento import entrenar_modelos
from src.clasificacion import clasificar_imagen

def interpretar_prediccion(valor):
    if 0 <= valor <= 9:
        return str(valor)   # Números 0-9
    elif 10 <= valor <= 35:
        return chr(valor + 55)  # Letras A-Z (A=10, B=11, ..., chr(66), etc.)
    else:
        return "No se reconoce"

if __name__ == '__main__':
    # Entrenar modelos
    #print("Entrenando modelos OCR...")
    #entrenar_modelos()

    # Cargar modelos
    print("Cargando modelos entrenados...")
    knn_model = joblib.load("models/knn_model.pkl")
    nn_model = joblib.load("models/nn_model.pkl")

    # Probar clasificación en una imagen de prueba
    print("\n Probando clasificación en una imagen de prueba...")
    ruta_prueba = 'data/data/testing_data/O/29090.png'
    knn_pred, nn_pred = clasificar_imagen(ruta_prueba, knn_model, nn_model)
    
    print(f"Predicción KNN: {interpretar_prediccion(knn_pred)}")
    print(f"Predicción Red Neuronal: {interpretar_prediccion(nn_pred)}")





#Resumen
#✅ preprocesamiento.py → Carga imágenes en un formato numérico.
#✅ entrenamiento.py → Entrena KNN + Red Neuronal con TODAS las imágenes a la vez.
#✅ clasificacion.py → Usa los modelos entrenados para predecir letras/números en nuevas imágenes.
#✅ main.py → Ejecuta todo el proceso automáticamente.