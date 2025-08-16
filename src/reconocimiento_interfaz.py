import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import tensorflow as tf
import joblib
import os

# --- Configuración de rutas ---
script_dir = os.path.dirname(__file__)
models_dir = os.path.join(script_dir, '..', 'models')
model_path = os.path.join(models_dir, 'keras_cnn_model_augmented.h5')
class_map_path = os.path.join(models_dir, 'class_labels_map.pkl')

# --- Cargar el modelo y el mapeo de clases ---
try:
    model = tf.keras.models.load_model(model_path)
    class_labels_map = joblib.load(class_map_path)
    # Crear un mapeo inverso de índice a etiqueta para la predicción
    index_to_label_map = {v: k for k, v in class_labels_map.items()}
    print("Modelo y mapeo de clases cargados exitosamente.")
except Exception as e:
    messagebox.showerror("Error de Carga", f"No se pudo cargar el modelo o el mapeo de clases: {e}\n"
                                           f"Asegúrate de que '{model_path}' y '{class_map_path}' existan.")
    model = None
    class_labels_map = None

# --- Función de preprocesamiento de imagen (igual que en preprocesamientoV2.py) ---
def preprocess_image_for_prediction(image_path):
    """
    Carga, preprocesa (suavizado, binarización, dilatación) y redimensiona
    una imagen para que sea compatible con la entrada del modelo Keras (28x28, escala de grises).
    """
    try:
        imagen = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if imagen is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen desde: {image_path}")

        imagen_suavizada = cv2.GaussianBlur(imagen, (7, 7), 0)
        imagen_binarizada = cv2.adaptiveThreshold(imagen_suavizada, 255,
                                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                  cv2.THRESH_BINARY, 15, 2)
        kernel = np.ones((1, 1), np.uint8)
        imagen_dilatada = cv2.dilate(imagen_binarizada, kernel, iterations=1)
        
        # Redimensionar al tamaño esperado por el modelo
        imagen_final = cv2.resize(imagen_dilatada, (28, 28))

        # El modelo espera una imagen con 1 canal y normalizada [0, 1]
        # (La capa Rescaling 1./255 de Keras ya se encarga de la normalización si el modelo la tiene)
        # Si tu modelo *no* tiene tf.keras.layers.Rescaling(1./255), normaliza aquí:
        # imagen_final = imagen_final.astype(np.float32) / 255.0

        # Expandir dimensiones para que sea (1, 28, 28, 1)
        return np.expand_dims(imagen_final, axis=0) # Añadir dimensión de batch
    except Exception as e:
        messagebox.showerror("Error de Preprocesamiento", f"Error al preprocesar la imagen: {e}")
        return None

# --- Funciones de la Interfaz Gráfica ---
def select_image():
    if model is None:
        messagebox.showwarning("Modelo no cargado", "El modelo de reconocimiento no está cargado. No se puede procesar.")
        return

    file_path = filedialog.askopenfilename(
        title="Seleccionar imagen de letra",
        filetypes=[("Archivos de Imagen", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Todos los archivos", "*.*")]
    )
    if not file_path:
        return

    # Mostrar la imagen seleccionada en la interfaz
    display_image(file_path)

    # Preprocesar y predecir
    processed_image = preprocess_image_for_prediction(file_path)
    if processed_image is not None:
        try:
            # Realizar la predicción
            predictions = model.predict(processed_image)
            predicted_class_index = np.argmax(predictions)
            predicted_label = index_to_label_map.get(predicted_class_index, "Desconocido")
            
            # Mostrar el resultado
            result_label.config(text=f"Predicción: {predicted_label}", fg="green")
        except Exception as e:
            messagebox.showerror("Error de Predicción", f"Error al realizar la predicción: {e}")
            result_label.config(text="Error en la predicción", fg="red")
    else:
        result_label.config(text="Error de preprocesamiento", fg="red")

def display_image(file_path):
    try:
        img_pil = Image.open(file_path).convert("L") # Cargar en escala de grises
        img_pil = img_pil.resize((100, 100), Image.LANCZOS) # Redimensionar para mostrar en la GUI
        img_tk = ImageTk.PhotoImage(img_pil)
        image_panel.config(image=img_tk)
        image_panel.image = img_tk # Mantener una referencia para evitar que sea recolectada por el garbage collector
    except Exception as e:
        messagebox.showerror("Error al mostrar imagen", f"No se pudo mostrar la imagen: {e}")

# --- Configuración de la Ventana Principal de Tkinter ---
root = tk.Tk()
root.title("Reconocimiento de Caracteres OCR")
root.geometry("400x400")
root.resizable(False, False) # Evitar que la ventana sea redimensionable

# Estilo
root.configure(bg="#f0f0f0")
font_large = ("Arial", 16, "bold")
font_medium = ("Arial", 12)

# Título
title_label = tk.Label(root, text="Detector de Letras", font=("Arial", 20, "bold"), bg="#f0f0f0", fg="#333")
title_label.pack(pady=20)

# Panel para mostrar la imagen
image_panel = tk.Label(root, bg="#e0e0e0", relief="solid", bd=1)
image_panel.pack(pady=10)

# Etiqueta para mostrar el resultado
result_label = tk.Label(root, text="Selecciona una imagen para predecir...", font=font_large, bg="#f0f0f0", fg="#333")
result_label.pack(pady=20)

# Botón para seleccionar imagen
select_button = tk.Button(root, text="Seleccionar Imagen", command=select_image, font=font_medium, bg="#4CAF50", fg="white", padx=10, pady=5)
select_button.pack(pady=10)

# Iniciar el bucle principal de la interfaz gráfica
root.mainloop()