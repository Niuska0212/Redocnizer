#!/usr/bin/env python3
"""
Dataset Creator V2 - Generador Mejorado de Imágenes OCR
=======================================================

Versión mejorada del dataset creator con:
- Integración con generador de palabras aleatorias
- Manejo robusto de errores
- Logging
- Configuración flexible (CLI + API)
- Validación de inputs
- Estadísticas detalladas
- Progreso visual

Autor: Equipo OCR  
Fecha: Noviembre 2025
"""

import os
import sys
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

# Añadir path para importar generador de palabras
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from generador_palabras_realistas import (
        generar_palabras_realistas
    )
    generar_palabras = generar_palabras_realistas
    GENERADOR_DISPONIBLE = True
except ImportError:
    GENERADOR_DISPONIBLE = False
    print("⚠️  Generador de palabras no disponible, usar archivo de palabras")


# ==================== CONFIGURACIÓN ====================

DEFAULT_CONFIG = {
    'cantidad_palabras': 1000,
    'cantidad_fechas': 500,
    'longitud_min': 3,
    'longitud_max': 15,
    'font_sizes': [20, 24, 28, 32, 36],
    'padding': 10,
    'bg_color_min': 200,
    'bg_color_max': 255,
    'text_color': (0, 0, 0),  # Negro
    'use_random_words': True,
    'seed': None,
    'verbose': True,
    # 🔥 NUEVAS OPCIONES DE VARIABILIDAD
    'augmentation': {
        'enable': True,
        'rotation_range': 3,          # ±3 grados de rotación
        'blur_probability': 0.15,      # 15% de imágenes con blur
        'blur_radius_range': (0.5, 2.0),
        'noise_probability': 0.20,     # 20% de imágenes con ruido
        'noise_intensity': 0.03,       # 3% de ruido
        'brightness_range': (0.8, 1.2),  # ±20% brillo
        'contrast_range': (0.9, 1.1),    # ±10% contraste
        'elastic_probability': 0.10,   # 10% de distorsión elástica
        'shear_range': 2,              # ±2 grados de shear
        'bg_gradient': 0.15,           # 15% con gradiente de fondo
        'bg_texture': 0.10,            # 10% con textura de fondo
    },
    'font_variations': {
        'enable_bold_simulation': True,  # Simular bold
        'enable_italic_simulation': True, # Simular italic
        'bold_probability': 0.15,
        'italic_probability': 0.10,
        'letter_spacing_range': (-1, 2), # Espaciado entre letras
    }
}


# ==================== SETUP LOGGING ====================

def setup_logger(verbose=True):
    """Configura sistema de logging."""
    level = logging.INFO if verbose else logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger(__name__)


# ==================== VALIDACIÓN ====================

class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    pass


def validar_directorio_fonts(font_dir: str) -> List[str]:
    """
    Valida directorio de fuentes y retorna lista de fuentes válidas.
    
    Args:
        font_dir: Ruta al directorio de fuentes
    
    Returns:
        Lista de rutas a archivos de fuentes
    
    Raises:
        ValidationError: Si no hay fuentes válidas
    """
    if not os.path.exists(font_dir):
        raise ValidationError(f"Directorio de fuentes no encontrado: {font_dir}")
    
    if not os.path.isdir(font_dir):
        raise ValidationError(f"No es un directorio: {font_dir}")
    
    # Buscar archivos .ttf
    font_paths = [
        os.path.join(font_dir, f) 
        for f in os.listdir(font_dir) 
        if f.lower().endswith('.ttf')
    ]
    
    if not font_paths:
        raise ValidationError(f"No se encontraron fuentes .ttf en: {font_dir}")
    
    # Verificar que las fuentes son accesibles
    valid_fonts = []
    for font_path in font_paths:
        try:
            # Intentar cargar la fuente para validar
            ImageFont.truetype(font_path, 20)
            valid_fonts.append(font_path)
        except Exception as e:
            logging.warning(f"Fuente inválida {font_path}: {e}")
    
    if not valid_fonts:
        raise ValidationError("Ninguna fuente pudo ser cargada correctamente")
    
    return valid_fonts


def validar_output_dir(output_dir: str, limpiar: bool = False):
    """
    Valida y prepara directorio de salida.
    
    Args:
        output_dir: Ruta al directorio de salida
        limpiar: Si limpiar archivos existentes
    """
    output_path = Path(output_dir)
    
    # Crear directorio si no existe
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Verificar permisos de escritura
    if not os.access(output_dir, os.W_OK):
        raise ValidationError(f"Sin permisos de escritura en: {output_dir}")
    
    # Limpiar si se solicita
    if limpiar:
        for file in output_path.glob('*.png'):
            file.unlink()
        labels_file = output_path / 'labels.txt'
        if labels_file.exists():
            labels_file.unlink()
        logging.info(f"Directorio limpiado: {output_dir}")


# ==================== GENERACIÓN DE DATOS ====================

def generar_fechas_aleatorias(
    cantidad: int,
    start_year: int = 2000,
    end_year: int = 2030
) -> List[str]:
    """
    Genera fechas aleatorias en formato DD/MM/YY.
    
    Args:
        cantidad: Número de fechas a generar
        start_year: Año inicial
        end_year: Año final
    
    Returns:
        Lista de fechas formateadas
    """
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    delta_days = (end_date - start_date).days
    
    fechas = []
    for _ in range(cantidad):
        random_days = random.randint(0, delta_days)
        fecha = start_date + timedelta(days=random_days)
        fechas.append(fecha.strftime("%d/%m/%y"))
    
    return fechas


def cargar_o_generar_palabras(
    usar_aleatorias: bool = True,
    cantidad: int = 1000,
    longitud_min: int = 3,
    longitud_max: int = 15,
    archivo_palabras: str = None,
    seed: int = None
) -> List[str]:
    """
    Carga palabras desde archivo o genera aleatorias.
    
    Args:
        usar_aleatorias: Si usar generador aleatorio
        cantidad: Cantidad de palabras a generar
        longitud_min: Longitud mínima
        longitud_max: Longitud máxima
        archivo_palabras: Ruta a archivo de palabras (opcional)
        seed: Semilla para reproducibilidad
    
    Returns:
        Lista de palabras
    """
    if usar_aleatorias and GENERADOR_DISPONIBLE:
        logging.info("Generando palabras aleatorias...")
        
        palabras = generar_palabras(
            cantidad=cantidad,
            longitud_min=longitud_min,
            longitud_max=longitud_max,
            charset='alfanumerico',
            mayusculas='mixto',
            permitir_duplicados=False,
            seed=seed,
            verbose=False
        )
        
        logging.info(f"✅ {len(palabras)} palabras aleatorias generadas")
        return palabras
    
    elif archivo_palabras and os.path.exists(archivo_palabras):
        logging.info(f"Cargando palabras desde: {archivo_palabras}")
        
        try:
            with open(archivo_palabras, 'r', encoding='utf-8') as f:
                palabras = [line.strip() for line in f if line.strip()]
            
            if not palabras:
                raise ValidationError(f"Archivo de palabras vacío: {archivo_palabras}")
            
            # Tomar solo la cantidad solicitada
            if len(palabras) > cantidad:
                palabras = random.sample(palabras, cantidad)
            
            logging.info(f"✅ {len(palabras)} palabras cargadas desde archivo")
            return palabras
        
        except Exception as e:
            raise ValidationError(f"Error al leer archivo de palabras: {e}")
    
    else:
        raise ValidationError(
            "Debe especificar archivo de palabras o habilitar generación aleatoria"
        )


# ==================== GENERACIÓN DE IMÁGENES ====================

def aplicar_rotacion(img: Image.Image, angulo: float) -> Image.Image:
    """Aplica rotación leve a la imagen."""
    return img.rotate(angulo, expand=True, fillcolor=(255, 255, 255))


def aplicar_blur(img: Image.Image, radius: float) -> Image.Image:
    """Aplica desenfoque gaussiano."""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def aplicar_ruido(img: Image.Image, intensity: float = 0.03) -> Image.Image:
    """Añade ruido gaussiano a la imagen."""
    img_array = np.array(img)
    noise = np.random.normal(0, 255 * intensity, img_array.shape)
    noisy_img = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_img)


def aplicar_ajustes_color(
    img: Image.Image,
    brightness_factor: float = 1.0,
    contrast_factor: float = 1.0
) -> Image.Image:
    """Ajusta brillo y contraste."""
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness_factor)
    
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast_factor)
    
    return img


def aplicar_shear(img: Image.Image, shear_x: float, shear_y: float = 0) -> Image.Image:
    """Aplica transformación de shear (cizallamiento)."""
    width, height = img.size
    
    # Matriz de transformación: (1, shear_x, 0, shear_y, 1, 0)
    m = 1.0 / (1.0 + abs(shear_x))
    
    return img.transform(
        (width, height),
        Image.AFFINE,
        (1, shear_x, 0, shear_y, 1, 0),
        fillcolor=(255, 255, 255),
        resample=Image.BICUBIC
    )


def crear_fondo_gradiente(width: int, height: int) -> Image.Image:
    """Crea fondo con gradiente sutil."""
    img = Image.new('L', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Gradiente vertical
    start_color = random.randint(200, 255)
    end_color = random.randint(200, 255)
    
    for y in range(height):
        color = int(start_color + (end_color - start_color) * y / height)
        draw.line([(0, y), (width, y)], fill=color)
    
    return img.convert('RGB')


def crear_fondo_textura(width: int, height: int) -> Image.Image:
    """Crea fondo con textura de ruido sutil."""
    # Fondo base
    base_color = random.randint(220, 245)
    img = Image.new('RGB', (width, height), (base_color, base_color, base_color))
    
    # Añadir textura muy sutil
    img_array = np.array(img)
    texture = np.random.normal(0, 5, img_array.shape)
    textured = np.clip(img_array + texture, 0, 255).astype(np.uint8)
    
    return Image.fromarray(textured)


def calcular_dimensiones_texto(
    texto: str,
    font: ImageFont.FreeTypeFont,
    padding: int = 10
) -> Tuple[int, int, int, int]:
    """
    Calcula dimensiones necesarias para renderizar texto.
    
    Args:
        texto: Texto a renderizar
        font: Fuente a usar
        padding: Padding alrededor del texto
    
    Returns:
        Tupla (width, height, text_width, text_height)
    """
    # Crear imagen temporal para medir texto
    temp_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    
    # Obtener bbox del texto
    bbox = draw.textbbox((0, 0), texto, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calcular dimensiones finales con padding
    width = text_width + padding * 2
    height = text_height + padding * 2
    
    return width, height, text_width, text_height


def generar_imagen_texto(
    texto: str,
    font_path: str,
    font_size: int,
    bg_color_range: Tuple[int, int] = (200, 255),
    text_color: Tuple[int, int, int] = (0, 0, 0),
    padding: int = 10,
    augmentation_config: Dict = None
) -> Image.Image:
    """
    Genera una imagen con el texto especificado CON AUGMENTATION.
    
    Args:
        texto: Texto a renderizar
        font_path: Ruta a la fuente
        font_size: Tamaño de fuente
        bg_color_range: Rango de color de fondo (min, max)
        text_color: Color del texto RGB
        padding: Padding alrededor del texto
        augmentation_config: Configuración de data augmentation
    
    Returns:
        Imagen PIL generada con variaciones
    """
    aug_cfg = augmentation_config or {}
    enable_aug = aug_cfg.get('enable', True)
    
    # Cargar fuente
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        raise RuntimeError(f"Error al cargar fuente {font_path}: {e}")
    
    # 🎨 VARIACIÓN 1: Simular bold/italic
    font_var_cfg = aug_cfg.get('font_variations', {})
    simulate_bold = (
        font_var_cfg.get('enable_bold_simulation', False) and
        random.random() < font_var_cfg.get('bold_probability', 0)
    )
    simulate_italic = (
        font_var_cfg.get('enable_italic_simulation', False) and
        random.random() < font_var_cfg.get('italic_probability', 0)
    )
    
    # Calcular dimensiones
    width, height, text_width, text_height = calcular_dimensiones_texto(
        texto, font, padding
    )
    
    # 🎨 VARIACIÓN 2: Tipo de fondo
    bg_gradient = enable_aug and random.random() < aug_cfg.get('bg_gradient', 0)
    bg_texture = enable_aug and random.random() < aug_cfg.get('bg_texture', 0)
    
    if bg_gradient:
        img = crear_fondo_gradiente(width, height)
    elif bg_texture:
        img = crear_fondo_textura(width, height)
    else:
        # Fondo sólido con color aleatorio
        bg_value = random.randint(bg_color_range[0], bg_color_range[1])
        bg_color = (bg_value, bg_value, bg_value)
        img = Image.new('RGB', (width, height), color=bg_color)
    
    draw = ImageDraw.Draw(img)
    
    # Calcular posición centrada del texto
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Dibujar texto
    draw.text((x, y), texto, font=font, fill=text_color)
    
    # 🎨 VARIACIÓN 3: Simular bold (dibujar texto desplazado ligeramente)
    if simulate_bold:
        for offset_x, offset_y in [(1, 0), (0, 1), (1, 1)]:
            draw.text((x + offset_x, y + offset_y), texto, font=font, fill=text_color)
    
    # 🎨 VARIACIÓN 4: Simular italic con shear
    if simulate_italic and enable_aug:
        shear_amount = random.uniform(0.1, 0.2)
        img = aplicar_shear(img, shear_amount)
    
    # 🎨 VARIACIÓN 5: Rotación leve
    if enable_aug and 'rotation_range' in aug_cfg:
        rotation_range = aug_cfg['rotation_range']
        if rotation_range > 0:
            angulo = random.uniform(-rotation_range, rotation_range)
            img = aplicar_rotacion(img, angulo)
    
    # 🎨 VARIACIÓN 6: Blur
    if enable_aug and random.random() < aug_cfg.get('blur_probability', 0):
        blur_range = aug_cfg.get('blur_radius_range', (0.5, 2.0))
        blur_radius = random.uniform(*blur_range)
        img = aplicar_blur(img, blur_radius)
    
    # 🎨 VARIACIÓN 7: Ruido
    if enable_aug and random.random() < aug_cfg.get('noise_probability', 0):
        noise_intensity = aug_cfg.get('noise_intensity', 0.03)
        img = aplicar_ruido(img, noise_intensity)
    
    # 🎨 VARIACIÓN 8: Ajustes de brillo y contraste
    if enable_aug:
        brightness_range = aug_cfg.get('brightness_range', (1.0, 1.0))
        contrast_range = aug_cfg.get('contrast_range', (1.0, 1.0))
        
        if brightness_range != (1.0, 1.0) or contrast_range != (1.0, 1.0):
            brightness = random.uniform(*brightness_range)
            contrast = random.uniform(*contrast_range)
            img = aplicar_ajustes_color(img, brightness, contrast)
    
    return img


# ==================== DATASET CREATOR PRINCIPAL ====================

class DatasetCreator:
    """Clase principal para crear dataset de imágenes OCR."""
    
    def __init__(
        self,
        output_dir: str,
        font_dir: str,
        config: Dict = None,
        logger: logging.Logger = None
    ):
        """
        Inicializa el creador de dataset.
        
        Args:
            output_dir: Directorio de salida
            font_dir: Directorio de fuentes
            config: Configuración personalizada
            logger: Logger personalizado
        """
        self.output_dir = Path(output_dir)
        self.font_dir = Path(font_dir)
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.logger = logger or logging.getLogger(__name__)
        
        # Validar directorios
        self.font_paths = validar_directorio_fonts(str(self.font_dir))
        validar_output_dir(str(self.output_dir))
        
        self.logger.info(f"✅ Dataset Creator inicializado")
        self.logger.info(f"   • Fuentes disponibles: {len(self.font_paths)}")
        self.logger.info(f"   • Output: {self.output_dir}")
        
        # Estadísticas
        self.stats = {
            'imagenes_generadas': 0,
            'errores': 0,
            'palabras_procesadas': 0,
            'fechas_procesadas': 0
        }
    
    def generar_dataset(
        self,
        palabras: List[str] = None,
        fechas: List[str] = None,
        limpiar: bool = False
    ) -> Dict:
        """
        Genera el dataset completo.
        
        Args:
            palabras: Lista de palabras (None = generar automáticamente)
            fechas: Lista de fechas (None = generar automáticamente)
            limpiar: Si limpiar directorio antes de generar
        
        Returns:
            Diccionario con estadísticas de generación
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 INICIANDO GENERACIÓN DE DATASET")
        self.logger.info("="*60)
        
        # Limpiar si se solicita
        if limpiar:
            validar_output_dir(str(self.output_dir), limpiar=True)
        
        # Obtener palabras
        if palabras is None:
            palabras = cargar_o_generar_palabras(
                usar_aleatorias=self.config['use_random_words'],
                cantidad=self.config['cantidad_palabras'],
                longitud_min=self.config['longitud_min'],
                longitud_max=self.config['longitud_max'],
                seed=self.config['seed']
            )
        
        # Obtener fechas
        if fechas is None:
            self.logger.info("Generando fechas aleatorias...")
            fechas = generar_fechas_aleatorias(
                self.config['cantidad_fechas']
            )
            self.logger.info(f"✅ {len(fechas)} fechas generadas")
        
        # Generar imágenes
        labels_file = self.output_dir / 'labels.txt'
        
        # Determinar contador inicial
        existing_images = list(self.output_dir.glob('*.png'))
        count = len(existing_images) if not limpiar else 0
        
        self.logger.info(f"\n📝 Generando imágenes...")
        self.logger.info(f"   • Total textos: {len(palabras) + len(fechas)}")
        self.logger.info(f"   • Contador inicial: {count}")
        
        # Abrir archivo de etiquetas
        mode = 'w' if limpiar else 'a'
        with open(labels_file, mode, encoding='utf-8') as f:
            # Generar imágenes de palabras
            count = self._generar_imagenes_batch(
                textos=palabras,
                labels_file=f,
                count=count,
                tipo='palabra'
            )
            
            # Generar imágenes de fechas
            count = self._generar_imagenes_batch(
                textos=fechas,
                labels_file=f,
                count=count,
                tipo='fecha'
            )
        
        self.logger.info("\n" + "="*60)
        self.logger.info("✅ GENERACIÓN COMPLETADA")
        self.logger.info("="*60)
        self._mostrar_estadisticas()
        
        return self.stats
    
    def _generar_imagenes_batch(
        self,
        textos: List[str],
        labels_file,
        count: int,
        tipo: str
    ) -> int:
        """
        Genera un batch de imágenes.
        
        Args:
            textos: Lista de textos a procesar
            labels_file: Archivo de etiquetas abierto
            count: Contador actual
            tipo: Tipo de texto ('palabra' o 'fecha')
        
        Returns:
            Nuevo valor del contador
        """
        total = len(textos)
        errores_batch = 0
        
        self.logger.info(f"\n🔤 Generando {total} imágenes de {tipo}s...")
        
        for i, texto in enumerate(textos, 1):
            try:
                # Seleccionar fuente y tamaño aleatorios
                font_path = random.choice(self.font_paths)
                font_size = random.choice(self.config['font_sizes'])
                
                # Generar imagen CON AUGMENTATION
                img = generar_imagen_texto(
                    texto=texto,
                    font_path=font_path,
                    font_size=font_size,
                    bg_color_range=(
                        self.config['bg_color_min'],
                        self.config['bg_color_max']
                    ),
                    text_color=self.config['text_color'],
                    padding=self.config['padding'],
                    augmentation_config={
                        'enable': self.config['augmentation']['enable'],
                        **self.config['augmentation'],
                        'font_variations': self.config['font_variations']
                    }
                )
                
                # Guardar imagen
                filename = f"{count:06d}.png"
                filepath = self.output_dir / filename
                img.save(filepath)
                
                # Escribir etiqueta
                labels_file.write(f"{filename},{texto}\n")
                
                # Actualizar contador y stats
                count += 1
                self.stats['imagenes_generadas'] += 1
                
                if tipo == 'palabra':
                    self.stats['palabras_procesadas'] += 1
                else:
                    self.stats['fechas_procesadas'] += 1
                
                # Mostrar progreso
                if i % 100 == 0 or i == total:
                    porcentaje = (i / total) * 100
                    self.logger.info(
                        f"   Progreso: {i}/{total} ({porcentaje:.1f}%) - "
                        f"Total generado: {self.stats['imagenes_generadas']}"
                    )
            
            except Exception as e:
                self.logger.error(f"   ❌ Error generando '{texto}': {e}")
                errores_batch += 1
                self.stats['errores'] += 1
        
        if errores_batch > 0:
            self.logger.warning(f"   ⚠️  {errores_batch} errores en este batch")
        
        return count
    
    def _mostrar_estadisticas(self):
        """Muestra estadísticas finales."""
        # Calcular tamaño del dataset
        total_size = sum(
            f.stat().st_size 
            for f in self.output_dir.glob('*.png')
        )
        total_size_mb = total_size / 1024 / 1024
        
        # Guardar en stats
        self.stats['tamano_total_mb'] = total_size_mb
        
        self.logger.info(f"\n📊 ESTADÍSTICAS:")
        self.logger.info(f"   • Imágenes generadas: {self.stats['imagenes_generadas']}")
        self.logger.info(f"   • Palabras: {self.stats['palabras_procesadas']}")
        self.logger.info(f"   • Fechas: {self.stats['fechas_procesadas']}")
        self.logger.info(f"   • Errores: {self.stats['errores']}")
        self.logger.info(f"   • Tamaño total: {total_size_mb:.2f} MB")
        
        labels_file = self.output_dir / 'labels.txt'
        if labels_file.exists():
            self.logger.info(f"   • Archivo etiquetas: {labels_file}")


# ==================== CLI ====================

def parse_args():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Dataset Creator V2 - Generador de Imágenes OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Generar con palabras aleatorias (por defecto)
  python dataset_creator_v2.py

  # Especificar cantidad
  python dataset_creator_v2.py --palabras 5000 --fechas 1000

  # Usar archivo de palabras existente
  python dataset_creator_v2.py --archivo-palabras ../data/palabras.txt

  # Limpiar directorio antes de generar
  python dataset_creator_v2.py --limpiar

  # Con seed para reproducibilidad
  python dataset_creator_v2.py --seed 42

  # Salida personalizada
  python dataset_creator_v2.py --output ./mi_dataset --fonts ../../fonts
        """
    )
    
    # Configuración de dataset
    parser.add_argument(
        '--palabras',
        type=int,
        default=DEFAULT_CONFIG['cantidad_palabras'],
        help=f"Número de palabras a generar (default: {DEFAULT_CONFIG['cantidad_palabras']})"
    )
    
    parser.add_argument(
        '--fechas',
        type=int,
        default=DEFAULT_CONFIG['cantidad_fechas'],
        help=f"Número de fechas a generar (default: {DEFAULT_CONFIG['cantidad_fechas']})"
    )
    
    parser.add_argument(
        '--longitud-min',
        type=int,
        default=DEFAULT_CONFIG['longitud_min'],
        help=f"Longitud mínima de palabra (default: {DEFAULT_CONFIG['longitud_min']})"
    )
    
    parser.add_argument(
        '--longitud-max',
        type=int,
        default=DEFAULT_CONFIG['longitud_max'],
        help=f"Longitud máxima de palabra (default: {DEFAULT_CONFIG['longitud_max']})"
    )
    
    # Archivos y directorios
    parser.add_argument(
        '--output',
        type=str,
        default='./output',
        help='Directorio de salida para imágenes (default: ./output)'
    )
    
    parser.add_argument(
        '--fonts',
        type=str,
        default='../../fonts',
        help='Directorio de fuentes .ttf (default: ../../fonts)'
    )
    
    parser.add_argument(
        '--archivo-palabras',
        type=str,
        default=None,
        help='Archivo de palabras (si no se usa generación aleatoria)'
    )
    
    # Opciones
    parser.add_argument(
        '--no-random',
        action='store_true',
        help='No usar generador aleatorio (requiere --archivo-palabras)'
    )
    
    parser.add_argument(
        '--limpiar',
        action='store_true',
        help='Limpiar directorio de salida antes de generar'
    )
    
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=None,
        help='Semilla para reproducibilidad'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Modo silencioso'
    )
    
    return parser.parse_args()


def main():
    """Función principal para modo CLI."""
    args = parse_args()
    
    # Setup logging
    logger = setup_logger(verbose=not args.quiet)
    
    # Configurar seed global si se especifica
    if args.seed is not None:
        random.seed(args.seed)
        logger.info(f"🎲 Seed configurado: {args.seed}")
    
    # Preparar configuración
    config = {
        'cantidad_palabras': args.palabras,
        'cantidad_fechas': args.fechas,
        'longitud_min': args.longitud_min,
        'longitud_max': args.longitud_max,
        'use_random_words': not args.no_random,
        'seed': args.seed,
        'verbose': not args.quiet
    }
    
    try:
        # Crear dataset creator
        creator = DatasetCreator(
            output_dir=args.output,
            font_dir=args.fonts,
            config=config,
            logger=logger
        )
        
        # 🔧 CARGAR PALABRAS SI SE PROPORCIONA ARCHIVO
        palabras_custom = None
        if args.archivo_palabras:
            if os.path.exists(args.archivo_palabras):
                logger.info(f"📂 Cargando palabras desde: {args.archivo_palabras}")
                with open(args.archivo_palabras, 'r', encoding='utf-8') as f:
                    palabras_custom = [line.strip() for line in f if line.strip()]
                logger.info(f"✅ {len(palabras_custom):,} palabras cargadas del archivo")
            else:
                logger.error(f"❌ No existe el archivo: {args.archivo_palabras}")
                sys.exit(1)
        
        # Generar dataset
        stats = creator.generar_dataset(
            palabras=palabras_custom,
            limpiar=args.limpiar
        )
        
        logger.info("\n✨ ¡Proceso completado exitosamente!")
        
    except ValidationError as e:
        logger.error(f"\n❌ Error de validación: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
