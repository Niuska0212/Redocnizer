
""" Importaciones necesarias y configuración de la aplicación OCR Testing Suite.
Simula un motor OCR básico y proporciona interfaces gráficas para:
1. Generar imágenes de prueba con corrupción controlada.
2. Probar un modelo OCR simulado y calcular métricas como Exactitud de Carácter y CER.

tener instalado las librerías:
- PySide6
- Pillow
- numpy
comando: pip install PySide6 pillow numpy
NOTA: Esta es una simulación simplificada para propósitos de demostración.
"""

import sys
import os
import random
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QSlider, QTabWidget, QFileDialog, 
    QGroupBox, QGridLayout, QTextEdit
)
from PySide6.QtGui import QPixmap, QImage, QIntValidator
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# --- CLASE DE SIMULACIÓN OCR Y CÁLCULO DE MÉTRICAS ---
class OCRMetrics:
    # Clase para simular el motor OCR y calcular métricas.
    
    def __init__(self, weights_path="model_final.weights.h5"):
        print(f"SIMULACIÓN: Cargando modelo desde {weights_path}...")
        self.is_loaded = True

    def edit_distance(self, s1, s2):
        """Calcula la Distancia de Edición (Levenshtein) para el CER."""
        s1, s2 = s1.upper(), s2.upper()
        la, lb = len(s1), len(s2)
        dp = [[0] * (lb + 1) for _ in range(la + 1)]
        for i in range(la + 1): dp[i][0] = i
        for j in range(lb + 1): dp[0][j] = j
        for i in range(1, la + 1):
            for j in range(1, lb + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        return dp[la][lb]

    def simulate_ocr(self, ground_truth, corruption_level=0.5):
        """
        Simula la inferencia OCR con errores controlados.
        Si 'ground_truth' está vacío, devuelve una predicción genérica.
        """
        
        # Si no hay Ground Truth, simula una predicción genérica y simple (predicción 'realista')
        if not ground_truth:
            return random.choice(["TEXTO", "IMAGEN", "DIGITO", "EJEMPLO"])
            
        predicted_text = ground_truth.upper()
        
        # Simulación de un modelo débil (sustituciones comunes en OCR)
        error_map = {'O': '0', 'L': '1', 'H': 'N', 'A': '4', 'S': '5', 'T': '7'}
        
        # El nivel de corrupción (0.0 a 1.0) influye en la probabilidad de error
        error_prob = 0.05 + (0.3 * corruption_level) 

        # Usar while loop para manejar modificaciones de longitud de forma segura
        i = 0
        while i < len(predicted_text):
            char = predicted_text[i]
            
            if random.random() < error_prob:
                if error_map.get(char) and random.random() < 0.6:
                    # Sustitución (La longitud no cambia)
                    predicted_text = predicted_text[:i] + error_map[char] + predicted_text[i+1:]
                elif random.random() < 0.2:
                    # Eliminación (omisión de carácter)
                    if len(predicted_text) > 0: 
                        predicted_text = predicted_text[:i] + predicted_text[i+1:]
                        continue # No incrementar 'i'
            
            i += 1 # Incrementar solo si no hubo eliminación
            
        # Asegurarse de que no devuelva una cadena vacía
        if not predicted_text:
            # Si se corrompió completamente, devuelve una predicción mínima
            return random.choice(["O", "I", "S"]) 
            
        return predicted_text
    
    def evaluate(self, ground_truth, predicted_word):
        """
        Calcula Word Accuracy y CER.
        NOTA: La Exactitud de Carácter se calcula en la capa de UI (100 - CER).
        """
        if not ground_truth:
            return 0.0, 0.0, "Detalle no disponible (requiere Palabra Verdadera o Ground Truth)."

        ground_truth = ground_truth.upper()
        predicted_word = predicted_word.upper()
        
        ed = self.edit_distance(ground_truth, predicted_word)
        total_chars = len(ground_truth)
        
        cer = (ed / total_chars) * 100 if total_chars > 0 else 0.0
        # Word Accuracy es binario: 100% si la palabra es perfecta, 0% si no.
        word_accuracy = 100.0 if ground_truth == predicted_word else 0.0

        # Simulación de matriz de confusión (detalle de edición)
        matrix_detail = f"--- Palabra Verdadera (Ground Truth): {ground_truth}\n"
        matrix_detail += f"--- Predicción del Modelo: {predicted_word}\n"
        matrix_detail += f"--- Distancia de Edición (Errores): {ed}\n"
        
        # Detalle para el usuario sobre la Exactitud de Palabra binaria
        word_acc_text = "PERFECTA (100%)" if word_accuracy == 100.0 else "INCORRECTA (0%) - Un error de carácter la invalida."
        matrix_detail += f"--- Exactitud de Palabra (Word Accuracy): {word_acc_text}\n"

        # Asegurar longitud igual para el detalle
        max_len = max(len(ground_truth), len(predicted_word))
        gt_padded = ground_truth.ljust(max_len, '-')
        pred_padded = predicted_word.ljust(max_len, '-')
        
        matrix_detail += "\nMatriz de Similitud (Detalle de Edición):\n"
        matrix_detail += "Operación\t| GT Carácter\t| Pred. Carácter\n"
        matrix_detail += "------------------------------------------------------\n"
        
        # NOTA: Esta es una simplificación de la alineación de Levenshtein
        for i in range(max_len):
            gt_char = gt_padded[i] if i < len(ground_truth) else ''
            pred_char = pred_padded[i] if i < len(predicted_word) else ''
            
            op = "MATCH"
            if gt_char != pred_char:
                # Una simplificación para el reporte:
                if gt_char == '' and pred_char != '-':
                    op = "INSERTION"
                elif gt_char != '-' and pred_char == '':
                    op = "DELETION"
                elif gt_char != '' and pred_char != '':
                    op = "SUBSTITUTION"
                else:
                    op = "N/A" # Caso de padding
            
            # Formateo para el output en monospace
            gt_display = gt_char if gt_char != '-' else ' '
            pred_display = pred_char if pred_char != '-' else ' '
            
            # ¡CORREGIDO: ljust en lugar de lajust!
            matrix_detail += f"{op.ljust(15)}\t| {gt_display.ljust(11)}\t| {pred_display.ljust(15)}\n"
            
        return word_accuracy, cer, matrix_detail


# --- 1. INTERFAZ GENERADOR DE IMÁGENES (TEST SET) ---
class GeneratorWidget(QWidget):
    def __init__(self, ocr_engine):
        super().__init__()
        self.ocr_engine = ocr_engine
        self.current_pil_image = None
        
        # Intentar cargar una fuente simple y genérica
        self.font = None
        try:
            # Opción 1: Fuente TrueType (Recomendada si está disponible)
            self.font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            # Opción 2: Fallback a la fuente por defecto
            self.font = ImageFont.load_default()
            
        self.setup_ui()
        self.connect_signals()
        

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Controles
        controls_group = QGroupBox("Configuración de Imagen Corrupta")
        controls_layout = QGridLayout(controls_group)
        
        # Entrada de Palabra
        self.word_input = QLineEdit("BIOPROCESO") # Valor inicial que coincide con tu ejemplo
        self.word_input.setMaxLength(10)
        self.word_input.setPlaceholderText("Máx 10 caracteres simples")
        controls_layout.addWidget(QLabel("Palabra a generar (Simple):"), 0, 0)
        controls_layout.addWidget(self.word_input, 0, 1)

        # Sliders
        self.sliders = {}
        slider_data = {
            "noise": ("Mugre/Ruido (%)", 0, 100, 0),
            "contrast": ("Contraste/Sombra (%)", 0, 100, 50),
            "rotation": ("Rotación/Inclinación (°)", -20, 20, 0),
            "blur": ("Desenfoque/Movido (px)", 0, 10, 0)
        }
        
        row = 1
        for key, (label_text, min_val, max_val, default_val) in slider_data.items():
            label = QLabel(label_text.replace("(%)", f"({default_val}%)").replace("(°)", f"({default_val}°)")
                           .replace("(px)", f"({default_val}px)"))
            # Almacenar el texto original para que slider_changed lo pueda usar
            label.setProperty("labelText", label_text.split('(')[0].strip()) 
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default_val)
            slider.setSingleStep(1)
            
            self.sliders[key] = (slider, label)
            
            controls_layout.addWidget(label, row, 0)
            controls_layout.addWidget(slider, row, 1)
            row += 1

        # Botones
        self.generate_btn = QPushButton("Generar Imagen 🎨")
        self.save_btn = QPushButton("Guardar como PNG (TEST_IMAGES) 💾")
        self.save_btn.setEnabled(False)
        
        controls_layout.addWidget(self.generate_btn, row, 0, 1, 2)
        row += 1
        controls_layout.addWidget(self.save_btn, row, 0, 1, 2)
        
        controls_layout.setRowStretch(row + 1, 1) # Estirar espacio vacío

        main_layout.addWidget(controls_group, 1)

        # Área de Visualización (Canvas)
        canvas_group = QGroupBox("Previsualización")
        canvas_layout = QVBoxLayout(canvas_group)
        self.image_label = QLabel()
        self.image_label.setFixedSize(400, 150)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; background-color: #fff;")
        canvas_layout.addWidget(self.image_label)
        main_layout.addWidget(canvas_group, 1)

    def connect_signals(self):
        self.generate_btn.clicked.connect(self.generate_and_display_image)
        self.save_btn.clicked.connect(self.save_image)
        self.word_input.textChanged.connect(self.word_changed)
        
        for key, (slider, label) in self.sliders.items():
            slider.valueChanged.connect(lambda value, k=key: self.slider_changed(value, k))
        
        # Generar imagen inicial al cargar
        self.generate_and_display_image()
        
    def slider_changed(self, value, key):
        slider, label = self.sliders[key]
        unit = "px" if key == "blur" else "°" if key == "rotation" else "%"
        base_text = label.property("labelText")
        label.setText(f"{base_text} ({value}{unit})")
        
        if self.word_input.text():
            self.generate_and_display_image()

    def word_changed(self, text):
        # Limitar a caracteres simples para simular las capacidades del modelo
        simple_text = "".join(c for c in text.upper() if c.isalnum())
        if text != simple_text:
            self.word_input.setText(simple_text)
        
        self.generate_and_display_image()

    def generate_and_display_image(self):
        text = self.word_input.text().upper().strip()
        
        if not text:
            self.image_label.clear()
            self.save_btn.setEnabled(False)
            self.current_pil_image = None
            return

        # 1. Crear imagen base PIL
        img_w, img_h = 400, 150
        img = Image.new('RGB', (img_w, img_h), color='white')
        draw = ImageDraw.Draw(img)

        # 2. Aplicar Transformaciones (Rotación y Contraste)
        rotation_val = self.sliders['rotation'][0].value()
        contrast_val = self.sliders['contrast'][0].value() / 100.0 * 2.0 # 0.0 a 2.0

        # --- CÁLCULO DE TAMAÑO DE TEXTO COMPATIBLE ---
        try:
            # Opción 1: Usa textlength (más moderno y preciso para el ancho)
            text_w = draw.textlength(text, font=self.font)
            text_h = 60 # Altura aproximada del texto de 60pt
        except (AttributeError, NotImplementedError):
            # Opción 2: Fallback a textsize (compatible con load_default)
            text_w, text_h = draw.textsize(text, font=self.font)

        # 3. Dibujar y Aplicar Contraste
        
        # Calcular posición para centrar el texto
        x = (img_w - text_w) / 2
        y = (img_h - text_h) / 2

        # Aplicar contraste (oscurecer/aclarar texto)
        # fill_level: 0 (negro) a 255 (blanco). Mayor contraste -> más cerca de 0
        contrast_factor = self.sliders['contrast'][0].value() / 100.0 # 0.0 a 1.0
        fill_level = int(255 * (1 - (contrast_factor * 0.8 + 0.2))) # 20% a 100% oscuridad
        
        draw.text((x, y), text, font=self.font, fill=(fill_level, fill_level, fill_level))
        
        # 4. Aplicar Rotación
        if abs(rotation_val) > 0.1:
            # Rotar la imagen, expandiendo el lienzo y rellenando el fondo
            img = img.rotate(rotation_val, expand=True, fillcolor='white')
            
            # Recortar la imagen de nuevo al tamaño original (simula recortes)
            w_r, h_r = img.size
            left = (w_r - img_w) / 2
            top = (h_r - img_h) / 2
            right = (w_r + img_w) / 2
            bottom = (h_r + img_h) / 2
            
            # Recorte o reescalado forzado si es necesario
            try:
                img = img.crop((left, top, right, bottom)).resize((img_w, img_h))
            except Exception:
                img = img.resize((img_w, img_h))

        # 5. Aplicar Filtros (Blur/Desenfoque)
        blur_val = self.sliders['blur'][0].value()
        if blur_val > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_val * 0.5))

        # 6. Simular Mugre/Ruido (Pixelación Aleatoria)
        noise_val = self.sliders['noise'][0].value() / 100.0 # 0.0 a 1.0
        if noise_val > 0.01:
            img_array = np.array(img)
            # Aplicar ruido de sal y pimienta
            num_noise = int(img_w * img_h * noise_val * 0.1) # 10% de los pixeles
            for _ in range(num_noise):
                row = random.randint(0, img_h - 1)
                col = random.randint(0, img_w - 1)
                color = random.choice([0, 255]) # Negro o blanco
                img_array[row, col, :] = [color, color, color]
            img = Image.fromarray(img_array)

        # 7. Guardar PIL Image y mostrar en QLabel
        self.current_pil_image = img
        qimage = QImage(img.tobytes("raw", "RGB"), img.width, img.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.save_btn.setEnabled(True)


    def save_image(self):
        if self.current_pil_image is None:
            return

        word = self.word_input.text().upper().strip()
        if not word:
            word = "BLANK"
            
        default_filename = f"TEST_{word}_{int(random.random() * 10000)}.png"
        
        # Abrir diálogo para guardar archivo
        # Simula que se guarda en una carpeta "TEST_IMAGES"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Imagen de Prueba", 
            os.path.join(os.getcwd(), "TEST_IMAGES", default_filename),
            "Imágenes PNG (*.png)"
        )
        
        if save_path:
            try:
                # Asegurar que la carpeta exista si se usa una ruta compleja
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                self.current_pil_image.save(save_path)
                print(f"✅ Imagen de prueba guardada en: {save_path}")
            except Exception as e:
                print(f"❌ Error al guardar la imagen: {e}")


# --- 2. INTERFAZ PROBADOR DE MODELO OCR ---
class TesterWidget(QWidget):
    def __init__(self, ocr_engine, generator_widget):
        super().__init__()
        self.ocr_engine = ocr_engine
        self.generator_widget = generator_widget
        self.loaded_image_path = ""
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. Carga de Imagen y Ground Truth
        input_group = QGroupBox("Carga de Datos de Prueba")
        input_layout = QGridLayout(input_group)

        # Carga de Imagen
        self.load_image_btn = QPushButton("Seleccionar Imagen (desde disco) 🖼️")
        self.image_path_label = QLineEdit("Ninguna imagen seleccionada.")
        self.image_path_label.setReadOnly(True)
        
        input_layout.addWidget(self.load_image_btn, 0, 0)
        input_layout.addWidget(self.image_path_label, 0, 1)

        # Palabra Verdadera (Ground Truth)
        self.ground_truth_input = QLineEdit()
        # Se mantiene el placeholder para recordarle al usuario que es necesario para calcular las métricas
        self.ground_truth_input.setPlaceholderText("Opcional: Ingrese la palabra correcta (Ground Truth) para calcular CER/ACC.")
        
        input_layout.addWidget(QLabel("Palabra Verdadera (Ground Truth):"), 1, 0)
        input_layout.addWidget(self.ground_truth_input, 1, 1)

        # Botón de Evaluación
        self.evaluate_btn = QPushButton("🚀 Ejecutar Predicción y Evaluación")
        # El botón está habilitado si hay imagen cargada
        self.evaluate_btn.setEnabled(False) 
        input_layout.addWidget(self.evaluate_btn, 2, 0, 1, 2)
        
        main_layout.addWidget(input_group)

        # 2. Previsualización de Imagen
        self.preview_group = QGroupBox("Imagen Seleccionada")
        preview_layout = QHBoxLayout(self.preview_group)
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(400, 150)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background-color: #fff;")
        self.preview_label.setText("Cargue una imagen para previsualizar.")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.preview_group)

        # 3. Resultados de Evaluación
        results_group = QGroupBox("Resultados de la Predicción")
        results_layout = QVBoxLayout(results_group)
        
        # Métrica Predicción
        self.predicted_word_label = self._create_metric_label("Predicción del Modelo:", "...", "blue")
        
        # Métrica Exactitud y CER (en una fila)
        metric_row = QHBoxLayout()
        # **CAMBIO**: Exactitud a Nivel de Carácter (lo que el usuario espera)
        self.char_accuracy_label = self._create_metric_label("Exactitud de Carácter (Char. Acc.):", "N/A", "green", small=True)
        # **CAMBIO**: Tasa de Error de Carácter (CER)
        self.cer_value_label = self._create_metric_label("Tasa de Error de Carácter (CER):", "N/A", "red", small=True)
        metric_row.addWidget(self.char_accuracy_label)
        metric_row.addWidget(self.cer_value_label)
        
        results_layout.addWidget(self.predicted_word_label)
        results_layout.addLayout(metric_row)

        # Matriz de Similitud (Texto Largo)
        self.matrix_box = QGroupBox("Detalle: Matriz de Similitud (Simulada)")
        matrix_layout = QVBoxLayout(self.matrix_box)
        self.matrix_output = QTextEdit()
        self.matrix_output.setReadOnly(True)
        self.matrix_output.setMinimumHeight(150)
        # ESTILO CORREGIDO: Alto contraste
        self.matrix_output.setStyleSheet("font-family: monospace; background-color: #2e2e2e; color: #f0f0f0;")
        self.matrix_output.setText("Cargue una imagen y presione 'Ejecutar' para ver el detalle.")
        matrix_layout.addWidget(self.matrix_output)
        
        results_layout.addWidget(self.matrix_box)

        main_layout.addWidget(results_group)
        main_layout.addStretch(1)

    def connect_signals(self):
        self.load_image_btn.clicked.connect(self.load_image)
        self.evaluate_btn.clicked.connect(self.evaluate_ocr)
        # El cambio de texto en GT solo actualiza la disponibilidad del botón (si hay imagen)
        self.ground_truth_input.textChanged.connect(self.check_evaluation_ready)
        
    def check_evaluation_ready(self):
        # El botón solo requiere que haya una imagen cargada
        is_ready = bool(self.loaded_image_path)
        self.evaluate_btn.setEnabled(is_ready)

    def _create_metric_label(self, title, initial_value, color, small=False):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        
        label = QLabel(initial_value)
        font_size = "20pt" if not small else "16pt"
        label.setStyleSheet(f"font-weight: bold; color: {color}; font-size: {font_size};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        return group

    @Slot()
    def load_image(self):
        # Abrir diálogo para cargar archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen de Prueba", 
            os.getcwd(), # Directorio inicial
            "Imágenes (*.png *.jpg *.jpeg)"
        )

        if file_path:
            self.loaded_image_path = file_path
            self.image_path_label.setText(os.path.basename(file_path))
            
            # Mostrar la imagen en el QLabel
            pixmap = QPixmap(file_path)
            self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            # 1. Intentar rellenar el Ground Truth si es una imagen generada
            try:
                filename = os.path.basename(file_path)
                if filename.startswith("TEST_") and filename.endswith(".png"):
                    # Extraer la palabra: TEST_WORD_1234.png
                    word_part = filename.split('_')[1]
                    self.ground_truth_input.setText(word_part)
                else:
                    self.ground_truth_input.clear() # Limpiar si no es una imagen generada
            except:
                self.ground_truth_input.clear() # Limpiar si falla el parseo
                
            self.check_evaluation_ready()
            
            # 2. Ejecutar la evaluación de forma automática para la predicción
            self.evaluate_ocr()

    @Slot()
    def evaluate_ocr(self):
        if not self.loaded_image_path:
            return
            
        ground_truth = self.ground_truth_input.text().strip().upper()
        
        # SIMULACIÓN DE INFERENCIA
        
        # 1. Definir el Nivel de Corrupción ASUMIDO (tu "cantidad de falla")
        if self.loaded_image_path.endswith(".png") and os.path.basename(self.loaded_image_path).startswith("TEST_"):
            corruption_level = 0.8 # Asumir alta corrupción para imágenes generadas
            corruption_display = "80% (Asumido, imagen de Test Set)"
        else:
            corruption_level = 0.5 # Asumir corrupción media para imágenes externas
            corruption_display = "50% (Asumido, imagen externa)"
            
        # 2. Obtener la palabra simulada
        # Si hay GT, se corrompe ese GT. Si no hay GT, se pide una predicción genérica.
        simulated_gt_base = ground_truth if ground_truth else "" 
        predicted_word = self.ocr_engine.simulate_ocr(simulated_gt_base, corruption_level)

        # 3. Cálculo de Métricas
        if ground_truth:
            # word_accuracy: (0.0 o 100.0), cer: Tasa de Error de Carácter
            word_accuracy, cer, matrix_detail = self.ocr_engine.evaluate(ground_truth, predicted_word)
            
            # **NUEVA MÉTRICA**: Exactitud a Nivel de Carácter
            char_accuracy = 100.0 - cer 
            
            char_acc_text = f"{char_accuracy:.2f}%"
            cer_text = f"{cer:.2f}%"
        else:
            # Si no hay GT, no se calculan métricas de error
            cer = 0.0
            char_accuracy = 0.0
            char_acc_text = "N/A"
            cer_text = "N/A"
            
            # Detalle con el Nivel de Corrupción Asumido
            matrix_detail = f"--- Nivel de Falla (Corrupción) Asumido: {corruption_display} ---\n\n"
            matrix_detail += f"Predicción realizada: {predicted_word}\n\n"
            matrix_detail += "Para calcular la Exactitud a Nivel de Carácter (Char. Acc.) y el CER, debe ingresar la Palabra Verdadera (Ground Truth). La predicción anterior es una simulación basada en una palabra genérica."


        # 4. Actualizar UI
        self.predicted_word_label.findChild(QLabel).setText(predicted_word)
        # Actualizar las dos métricas principales
        self.char_accuracy_label.findChild(QLabel).setText(char_acc_text)
        self.cer_value_label.findChild(QLabel).setText(cer_text)
        self.matrix_output.setText(matrix_detail)

# --- CLASE PRINCIPAL DE VENTANA ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suite de Pruebas y Generación OCR (Simulado)")
        self.setGeometry(100, 100, 1000, 700)
        
        # Inicializar motor OCR (simulado)
        self.ocr_engine = OCRMetrics()
        
        # Contenedor central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        
        # Pestañas
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Pestaña 1: Generador de Imágenes
        self.generator_widget = GeneratorWidget(self.ocr_engine)
        self.tabs.addTab(self.generator_widget, "1. Generador de Imagen de Prueba (Test Set)")
        
        # Pestaña 2: Probador de Modelo
        # Pasamos el widget generador por si necesitamos interactuar con él en el futuro
        self.tester_widget = TesterWidget(self.ocr_engine, self.generator_widget)
        self.tabs.addTab(self.tester_widget, "2. Probador de Modelo OCR y Métricas")
        
        # Mensaje de ayuda
        info_label = QLabel("INFO: Esta es una simulación del motor OCR. Usa la pestaña 2 para evaluar la **Exactitud de Carácter**.")
        info_label.setStyleSheet("color: #777; padding: 5px;")
        main_layout.addWidget(info_label)

if __name__ == "__main__":

    try:
        app = QApplication(sys.argv)
        # Aplicar un estilo moderno
        app.setStyle("Fusion") 
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"Error de importación: Necesitas instalar las librerías requeridas. {e}")
        print("Intenta: pip install PySide6 pillow numpy")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")