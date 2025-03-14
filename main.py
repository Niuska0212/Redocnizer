import  os
import joblib
from src.entrenamiento import entrenar_modelos
from src.clasificacion import clasificar_imagen


if __name__ == '__main__':
    #entrenar modelos
    print("Entrenando modelos OCR...")
    entrenar_modelos()

    #cargar modelos
    #print("Cargando modelos entrenados...")
    knn_model = joblib.load("models/knn_model.pkl")
    nn_model = joblib.load("models/nn_model.pkl")

    # probar clasificar en una imagen de prueba
    print("\n Probando clasificacion en una imagen de prueba...")
    ruta_prueba = 'data/data/training_data/A/10.png'
    knn_pred, nn_pred = clasificar_imagen(ruta_prueba, knn_model, nn_model)
    
    print(f"Predicción KNN: {knn_pred}")
    print(f"Predicción Red Neuronal: {nn_pred}")





#Resumen
#✅ preprocesamiento.py → Carga imágenes en un formato numérico.
#✅ entrenamiento.py → Entrena KNN + Red Neuronal con TODAS las imágenes a la vez.
#✅ clasificacion.py → Usa los modelos entrenados para predecir letras/números en nuevas imágenes.
#✅ main.py → Ejecuta todo el proceso automáticamente.