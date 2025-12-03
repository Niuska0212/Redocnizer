
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
import uuid
import shutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QSlider, QTabWidget, QFileDialog, 
    QGroupBox, QGridLayout, QTextEdit
)
from PySide6.QtGui import QPixmap, QImage, QIntValidator
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import yaml
import tensorflow as tf
# Forzar uso de CPU para evitar conflictos con el entrenamiento en background
try:
    tf.config.set_visible_devices([], 'GPU')
    print(" Configurado para usar SOLO CPU")
except Exception as e:
    print(f" Advertencia al configurar CPU: {e}")

from pathlib import Path

# Importar módulos del proyecto
from model import build_crnn, CTCPredModel
from utils import build_vocab, labels_to_text, ctc_greedy_decoder

# --- CLASE DE SIMULACIÓN OCR Y CÁLCULO DE MÉTRICAS ---
class OCRMetrics:
    # Clase para manejar el motor OCR real y calcular métricas.
    
    def __init__(self, config_path="config.yaml"):
        print(f"INICIALIZANDO MOTOR OCR REAL...")
        
        # 1. Cargar Configuración
        self.config = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
        self.mcfg = self.config['model']
        
        # 2. Construir Vocabulario
        self.idx2char, self.char2idx = build_vocab(self.mcfg['vocab_chars'], include_blank=self.mcfg['include_blank'])
        self.num_classes = len(self.idx2char)
        
        # 3. Construir Modelo
        self.input_shape = (self.mcfg['input_height'], self.mcfg['input_width'], self.mcfg['channels'])
        self.base_model = build_crnn(self.input_shape, self.num_classes)
        self.model = CTCPredModel(self.base_model, self.idx2char, self.char2idx)
        
        # 4. Cargar Pesos
        checkpoint_dir = Path(self.config['training']['checkpoint_dir'])
        weights_path = checkpoint_dir / 'model_best.weights.h5'
        
        if weights_path.exists():
            print(f" Cargando pesos desde: {weights_path}")
            self.base_model.load_weights(str(weights_path))
            self.is_loaded = True
        else:
            print(f" ERROR: No se encontraron pesos en {weights_path}")
            self.is_loaded = False

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

    def predict(self, image_path_or_pil):
        """
        Realiza inferencia real sobre una imagen.
        Aplica 'Smart Padding' para ajustar la imagen al ancho esperado por el modelo (512)
        sin distorsionarla.
        """
        if not self.is_loaded:
            return "ERROR_MODELO_NO_CARGADO"

        # Preprocesamiento de imagen usando PIL (Igual que dataloader_optimized.py)
        try:
            if isinstance(image_path_or_pil, str):
                img = Image.open(image_path_or_pil).convert('L')
            else:
                img = image_path_or_pil.convert('L')
                
            # --- SMART PADDING (Lógica exacta del Dataloader) ---
            target_h = self.mcfg['input_height']
            target_w = self.mcfg['input_width']
            
            # 1. Resize manteniendo aspect ratio para altura target_h (32)
            w, h = img.size
            scale = target_h / h
            new_w = int(w * scale)
            img = img.resize((new_w, target_h), Image.BILINEAR)
            
            # 2. Crear canvas de tamaño final (target_w, target_h) con fondo BLANCO (255)
            final_img = Image.new('L', (target_w, target_h), color=255)
            
            # 3. Pegar imagen centrada
            if new_w > target_w:
                # Si es más grande, forzar resize al ancho máximo
                img = img.resize((target_w, target_h), Image.BILINEAR)
                final_img.paste(img, (0, 0))
            else:
                # Centrar
                paste_x = (target_w - new_w) // 2
                final_img.paste(img, (paste_x, 0))
            
            # Convertir a Tensor y Normalizar
            img_array = np.array(final_img).astype(np.float32) / 255.0
            img_array = np.expand_dims(img_array, axis=-1) # [H, W, 1]
            
            # Batch dimension
            images = tf.convert_to_tensor([img_array], dtype=tf.float32) # [1, H, W, C]

        except Exception as e:
            print(f"Error en preprocesamiento: {e}")
            return "ERROR_PREPROC"

        # Inferencia
        logits = self.base_model(images, training=False)
        input_lengths = tf.constant([logits.shape[1]], dtype=tf.int32)
        decoded = ctc_greedy_decoder(logits, input_lengths)
        pred_text = labels_to_text(decoded[0], self.idx2char)
        
        return pred_text

    def simulate_ocr(self, ground_truth, corruption_level=0.5):
        """
        MÉTODO DEPRECADO: Mantenido por compatibilidad, pero ahora llama a predict si es posible.
        Si se pasa una imagen (path o PIL) en lugar de ground_truth, hace predicción real.
        """
        # Hack para compatibilidad: si ground_truth parece una ruta o objeto imagen, predecir
        return self.predict(ground_truth)
    
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
    # Señal para solicitar prueba inmediata: (ruta_imagen, ground_truth)
    test_requested = Signal(str, str)

    def __init__(self, ocr_engine):
        super().__init__()
        self.ocr_engine = ocr_engine
        self.current_pil_image = None
        self.font_map = {} # Nombre -> Ruta
        self.setup_ui()
        self.connect_signals()
        
    def load_fonts(self):
        """Carga fuentes disponibles en el directorio fonts/"""
        font_dir = Path("fonts")
        self.font_map = {"Default": None}
        
        if font_dir.exists():
            for ext in ['*.ttf', '*.otf']:
                for font_path in font_dir.glob(ext):
                    self.font_map[font_path.name] = str(font_path)
        
        return list(self.font_map.keys())

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Controles
        controls_group = QGroupBox("Configuración de Imagen Corrupta")
        controls_layout = QGridLayout(controls_group)
        
        # Entrada de Palabra
        self.word_input = QLineEdit("Bioproceso") 
        self.word_input.setMaxLength(40)
        self.word_input.setPlaceholderText("Máx 40 caracteres")
        controls_layout.addWidget(QLabel("Palabra a generar:"), 0, 0)
        controls_layout.addWidget(self.word_input, 0, 1)

        # Selector de Fuente
        from PySide6.QtWidgets import QComboBox # Importación local o mover arriba
        self.font_combo = QComboBox()
        fonts = self.load_fonts()
        self.font_combo.addItems(fonts)
        controls_layout.addWidget(QLabel("Fuente:"), 1, 0)
        controls_layout.addWidget(self.font_combo, 1, 1)

        # Sliders
        self.sliders = {}
        slider_data = {
            "noise": ("Mugre/Ruido (%)", 0, 100, 0),
            "contrast": ("Contraste/Sombra (%)", 0, 100, 50),
            "rotation": ("Rotación/Inclinación (°)", -20, 20, 0),
            "blur": ("Desenfoque/Movido (px)", 0, 10, 0)
        }
        
        row = 2
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
        # Botones
        self.generate_btn = QPushButton("Probar Ahora 🚀")
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.save_btn = QPushButton("Guardar como PNG (TEST_IMAGES) ")
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
        # El botón ahora dispara el flujo de prueba inmediata
        self.generate_btn.clicked.connect(self.on_test_now)
        self.save_btn.clicked.connect(self.save_image)
        self.word_input.textChanged.connect(self.word_changed)
        self.font_combo.currentTextChanged.connect(lambda: self.generate_and_display_image())
        
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
        self.generate_and_display_image()

    def get_current_font(self):
        font_name = self.font_combo.currentText()
        font_path = self.font_map.get(font_name)
        
        try:
            if font_path:
                return ImageFont.truetype(font_path, 32)
            else:
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def generate_and_display_image(self):
        # CORRECCIÓN: Permitir minúsculas (quitar .upper())
        text = self.word_input.text().strip()
        
        if not text:
            self.image_label.clear()
            self.save_btn.setEnabled(False)
            self.current_pil_image = None
            return

        # Cargar fuente seleccionada
        font = self.get_current_font()

        # --- CÁLCULO DE TAMAÑO Y SMART PADDING (Igual que dataset_creator) ---
        # Necesitamos un objeto draw dummy para medir texto
        dummy_img = Image.new('RGB', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        try:
            text_w = dummy_draw.textlength(text, font=font)
            # Estimación de altura (ascent + descent)
            ascent, descent = font.getmetrics()
            text_h = ascent + descent
        except (AttributeError, NotImplementedError):
            text_w, text_h = dummy_draw.textsize(text, font=font)

        # Configuración de Padding y Tamaño (Ajustado a la palabra)
        padding = 10
        
        # Calcular dimensiones finales (Ajustado al contenido)
        final_w = int(text_w + padding * 2)
        final_h = int(text_h + padding * 2)
        
        # Asegurar altura mínima razonable para visualización
        final_h = max(final_h, 50)
        final_w = max(final_w, 100) # Mínimo razonable para que no sea diminuto

        # Crear imagen con el tamaño correcto
        img = Image.new('RGB', (final_w, final_h), color='white')
        draw = ImageDraw.Draw(img)

        # 3. Dibujar y Aplicar Contraste
        
        # Calcular posición para centrar el texto
        x = (final_w - text_w) / 2
        y = (final_h - text_h) / 2

        # Aplicar contraste
        contrast_factor = self.sliders['contrast'][0].value() / 100.0
        fill_level = int(255 * (1 - (contrast_factor * 0.8 + 0.2)))
        
        draw.text((x, y), text, font=font, fill=(fill_level, fill_level, fill_level))
        
        # 4. Aplicar Rotación
        rotation_val = self.sliders['rotation'][0].value()
        if abs(rotation_val) > 0.1:
            img = img.rotate(rotation_val, expand=True, fillcolor='white')
            # No recortamos forzosamente al tamaño original para no perder info,
            # pero el modelo hará resize a 512x32.
            # Para visualización, mantenemos el tamaño rotado.

        # 5. Aplicar Filtros (Blur/Desenfoque)
        blur_val = self.sliders['blur'][0].value()
        if blur_val > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_val * 0.5))

        # 6. Simular Mugre/Ruido (Pixelación Aleatoria)
        noise_val = self.sliders['noise'][0].value() / 100.0 # 0.0 a 1.0
        if noise_val > 0.01:
            img_array = np.array(img)
            # CORRECCIÓN: Definir dimensiones de la imagen actual
            img_h, img_w = img_array.shape[:2]
            
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
                print(f" Imagen de prueba guardada en: {save_path}")
            except Exception as e:
                print(f" Error al guardar la imagen: {e}")
    def on_test_now(self):
        """Genera la imagen, la guarda temporalmente con nombre seguro y solicita prueba."""
        # 1. Asegurar que la imagen está generada y actualizada
        self.generate_and_display_image()
        
        if self.current_pil_image is None:
            return

        # 2. Obtener texto (Ground Truth)
        text = self.word_input.text().strip()
        if not text: return

        # 3. Guardar en carpeta temporal con nombre SEGURO (UUID)
        # Esto evita problemas con caracteres especiales en el nombre del archivo
        temp_dir = os.path.join(os.getcwd(), "TEMP_GEN_IMAGES")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Nombre seguro: temp_uuid.png
        safe_filename = f"temp_{uuid.uuid4().hex[:8]}.png"
        save_path = os.path.join(temp_dir, safe_filename)
        
        try:
            self.current_pil_image.save(save_path)
            print(f" Imagen temporal guardada en: {save_path}")
            
            # 4. Emitir señal para que la ventana principal cambie de pestaña y pruebe
            self.test_requested.emit(save_path, text)
            
        except Exception as e:
            print(f" Error al guardar imagen temporal: {e}")

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
        self.load_image_btn = QPushButton("Seleccionar Imagen (desde disco) ️")
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
        self.evaluate_btn = QPushButton(" Ejecutar Predicción y Evaluación")
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
            
        # 2. Obtener la palabra PREDICHA REALMENTE
        # Pasamos la ruta de la imagen al motor OCR real
        predicted_word = self.ocr_engine.predict(self.loaded_image_path)

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
            matrix_detail = f"--- Predicción Real del Modelo ---\n\n"
            matrix_detail += f"Predicción: {predicted_word}\n\n"
            matrix_detail += "Para calcular la Exactitud a Nivel de Carácter (Char. Acc.) y el CER, debe ingresar la Palabra Verdadera (Ground Truth)."


        # 4. Actualizar UI
        self.predicted_word_label.findChild(QLabel).setText(predicted_word)
        # Actualizar las dos métricas principales
        self.char_accuracy_label.findChild(QLabel).setText(char_acc_text)
        self.cer_value_label.findChild(QLabel).setText(cer_text)
        self.matrix_output.setText(matrix_detail)

    def load_and_test(self, image_path, ground_truth):
        """Carga una imagen y ejecuta la prueba automáticamente (llamado desde Generator)."""
        if not os.path.exists(image_path):
            print(f"Error: No se encuentra la imagen {image_path}")
            return

        self.loaded_image_path = image_path
        self.image_path_label.setText(os.path.basename(image_path))
        
        # Mostrar preview
        pixmap = QPixmap(image_path)
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # Setear Ground Truth
        self.ground_truth_input.setText(ground_truth)
        
        # Habilitar y Ejecutar
        self.check_evaluation_ready()
        self.evaluate_ocr()

# --- CLASE PRINCIPAL DE VENTANA ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suite de Pruebas y Generación OCR (MODELO REAL)")
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
        # Pestaña 1: Generador de Imágenes
        self.generator_widget = GeneratorWidget(self.ocr_engine)
        # Conectar señal de prueba
        self.generator_widget.test_requested.connect(self.on_test_requested)
        
        self.tabs.addTab(self.generator_widget, "1. Generador de Imagen de Prueba (Test Set)")
        
        # Pestaña 2: Probador de Modelo
        # Pasamos el widget generador por si necesitamos interactuar con él en el futuro
        self.tester_widget = TesterWidget(self.ocr_engine, self.generator_widget)
        self.tabs.addTab(self.tester_widget, "2. Probador de Modelo OCR y Métricas")
        
        # Mensaje de ayuda
        info_label = QLabel("INFO: Usando modelo real (model_best.weights.h5). Usa la pestaña 2 para evaluar.")
        info_label.setStyleSheet("color: #777; padding: 5px;")
        main_layout.addWidget(info_label)

    @Slot(str, str)
    def on_test_requested(self, image_path, ground_truth):
        """Maneja la solicitud de prueba desde el generador."""
        # 1. Cambiar a la pestaña del probador (índice 1)
        self.tabs.setCurrentIndex(1)
        
        # 2. Cargar datos y ejecutar prueba en el widget tester
        self.tester_widget.load_and_test(image_path, ground_truth)

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