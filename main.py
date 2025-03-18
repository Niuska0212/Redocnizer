import  os
import joblib
from src.entrenamiento import entrenar_modelos
from src.clasificacion import clasificar_imagen

def interpretar_prediccion(valor):
    if 0 <= valor <= 9:
        return str(valor)   #numeros 0-9
    elif 10 <= valor <= 35:
        return chr(valor + 55) #letras A-Z (A=10, B=11, ..., chr(66), etc.)
    else:
        return "No se reconoce"

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
    ruta_prueba = 'data/data/training_data/O/8916.png'
    knn_pred, nn_pred = clasificar_imagen(ruta_prueba, knn_model, nn_model)
    
    print(f"Predicción KNN: {interpretar_prediccion(knn_pred)}")
    print(f"Predicción Red Neuronal: {interpretar_prediccion(nn_pred)}")





#Resumen
#✅ preprocesamiento.py → Carga imágenes en un formato numérico.
#✅ entrenamiento.py → Entrena KNN + Red Neuronal con TODAS las imágenes a la vez.
#✅ clasificacion.py → Usa los modelos entrenados para predecir letras/números en nuevas imágenes.
#✅ main.py → Ejecuta todo el proceso automáticamente.