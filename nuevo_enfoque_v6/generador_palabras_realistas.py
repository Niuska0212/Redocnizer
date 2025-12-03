#!/usr/bin/env python3
"""
Generador de Palabras REALISTAS para Dataset OCR
=================================================

Genera palabras con patrones lingüísticos reales:
- Diccionario español/inglés
- Nombres propios comunes
- Fechas en formatos comunes
- Números con patrones reales
- Frecuencias de letras realistas
- N-gramas válidos

Autor: Aether
Fecha: Noviembre 2025
Versión: 2.0 (Realista)
"""

import random
import string
import argparse
import yaml
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import Counter


# ==================== CONFIGURACIÓN ====================

def load_config(path='config.yaml'):
    """Carga configuración desde archivo YAML."""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

# Cargar configuración global
GLOBAL_CONFIG = load_config()
DATASET_CONFIG = GLOBAL_CONFIG.get('dataset', {})
DEFAULT_DATASET_SIZE = DATASET_CONFIG.get('dataset_size', 20000)
DEFAULT_LABELS_PATH = DATASET_CONFIG.get('labels_path', '../modelo_20k/labels_realistas.txt')


# ==================== DATOS LINGÜÍSTICOS REALES ====================

# Palabras comunes en español (top 1000)
PALABRAS_ESPANOL = [
    # Artículos y preposiciones
    "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "haber",
    "por", "con", "su", "para", "como", "estar", "tener", "le", "lo", "todo",
    "pero", "más", "hacer", "o", "poder", "decir", "este", "ir", "otro", "ese",
    "si", "me", "ya", "ver", "porque", "dar", "cuando", "él", "muy", "sin",
    
    # Sustantivos comunes
    "año", "tiempo", "día", "casa", "vida", "mundo", "país", "ciudad", "parte",
    "gobierno", "empresa", "trabajo", "persona", "problema", "caso", "vez",
    "grupo", "forma", "mujer", "hombre", "estado", "nombre", "lugar", "nivel",
    "mes", "hora", "mano", "momento", "agua", "tierra", "luz", "punto", "obra",
    "historia", "sistema", "proceso", "proyecto", "desarrollo", "familia",
    
    # Verbos comunes
    "trabajar", "estudiar", "vivir", "comer", "beber", "dormir", "hablar",
    "escribir", "leer", "escuchar", "mirar", "pensar", "creer", "saber",
    "conocer", "aprender", "enseñar", "comprar", "vender", "pagar", "recibir",
    "enviar", "llamar", "contestar", "preguntar", "responder", "entender",
    
    # Adjetivos comunes
    "grande", "pequeño", "bueno", "malo", "nuevo", "viejo", "alto", "bajo",
    "largo", "corto", "ancho", "estrecho", "fuerte", "débil", "rápido", "lento",
    "fácil", "difícil", "importante", "necesario", "posible", "imposible",
    "diferente", "igual", "mismo", "otro", "varios", "algunos", "todos",
    
    # Palabras técnicas/modernas
    "internet", "computadora", "teléfono", "email", "usuario", "contraseña",
    "archivo", "documento", "imagen", "video", "audio", "mensaje", "correo",
    "página", "sitio", "sistema", "programa", "aplicación", "red", "datos",
    "información", "código", "error", "proceso", "función", "opción"
]

# Palabras comunes en inglés (top 500)
PALABRAS_INGLES = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my",
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "time", "no", "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then", "now", "look",
    "only", "come", "its", "over", "think", "also", "back", "after", "use", "two",
    "how", "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "computer", "internet", "email",
    "phone", "system", "data", "user", "password", "file", "image", "video", "code"
]

# Nombres propios comunes (español + internacional)
NOMBRES_PROPIOS = [
    # Nombres masculinos
    "Juan", "José", "Carlos", "Miguel", "Antonio", "Francisco", "Manuel",
    "Pedro", "Luis", "Fernando", "Diego", "Javier", "Rafael", "Andrés",
    "Daniel", "David", "Jorge", "Mario", "Alberto", "Ricardo", "Roberto",
    "Alejandro", "Eduardo", "Sergio", "Pablo", "Ramón", "Jesús", "Gabriel",
    
    # Nombres femeninos
    "María", "Ana", "Carmen", "Laura", "Marta", "Elena", "Isabel", "Rosa",
    "Pilar", "Teresa", "Lucía", "Patricia", "Cristina", "Beatriz", "Raquel",
    "Sofía", "Silvia", "Mónica", "Claudia", "Adriana", "Daniela", "Paula",
    "Andrea", "Valentina", "Camila", "Natalia", "Gabriela", "Carolina",
    
    # Apellidos comunes
    "García", "Rodríguez", "González", "Fernández", "López", "Martínez",
    "Sánchez", "Pérez", "Martín", "Gómez", "Ruiz", "Díaz", "Hernández",
    "Álvarez", "Jiménez", "Moreno", "Muñoz", "Romero", "Navarro", "Torres",
    
    # Nombres internacionales
    "John", "Michael", "David", "James", "Robert", "William", "Richard",
    "Thomas", "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Susan",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis"
]

# Ciudades y países
LUGARES = [
    "Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Bilbao",
    "México", "Argentina", "Colombia", "Chile", "Perú", "España",
    "London", "Paris", "Berlin", "Rome", "Tokyo", "NewYork",
    "California", "Texas", "Florida", "Washington"
]

# Frecuencias de letras en español (%)
FRECUENCIAS_ESPANOL = {
    'e': 13.68, 'a': 12.53, 'o': 8.68, 's': 7.98, 'n': 6.71, 'r': 6.87,
    'i': 6.25, 'l': 4.97, 'd': 5.86, 't': 4.63, 'c': 4.68, 'u': 3.93,
    'm': 3.15, 'p': 2.51, 'b': 1.42, 'g': 1.01, 'v': 0.90, 'y': 0.90,
    'q': 0.88, 'h': 0.70, 'f': 0.69, 'z': 0.52, 'j': 0.44, 'ñ': 0.31,
    'x': 0.22, 'w': 0.02, 'k': 0.01
}

# Bigramas comunes en español
BIGRAMAS_COMUNES = [
    "de", "es", "en", "el", "la", "os", "as", "ar", "er", "or",
    "al", "an", "ra", "re", "te", "ti", "to", "qu", "ue", "nt",
    "co", "ca", "se", "st", "do", "ci", "ta", "pa", "pr", "tr"
]

# Trigramas comunes
TRIGRAMAS_COMUNES = [
    "que", "ent", "ion", "del", "est", "con", "nte", "los", "las", "ada",
    "ión", "res", "tra", "pro", "sta", "par", "ado", "cia", "des", "por"
]

# Prefijos comunes
PREFIJOS = ["des", "pre", "re", "in", "sub", "anti", "auto", "co", "ex"]

# Sufijos comunes
SUFIJOS = ["ción", "dad", "mente", "ismo", "ista", "dor", "dora", "able", "ible", "oso", "osa"]

# Variables globales para diccionarios externos
DICCIONARIO_EXTERNO_ES = []
DICCIONARIO_EXTERNO_EN = []


# ==================== CARGA DE DICCIONARIOS EXTERNOS ====================

def cargar_diccionario_externo(path: str, max_palabras: int = 1000000) -> List[str]:
    """
    Carga un diccionario externo desde un archivo de texto.
    
    Args:
        path: Ruta al archivo de diccionario (una palabra por línea)
        max_palabras: Número máximo de palabras a cargar
    
    Returns:
        Lista de palabras únicas
    """
    if not os.path.exists(path):
        print(f"️  Advertencia: No se encontró el diccionario en {path}")
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            palabras = []
            for i, linea in enumerate(f):
                if i >= max_palabras:
                    break
                palabra = linea.strip()
                # Filtrar palabras válidas (solo letras, longitud 2-15)
                if palabra and 2 <= len(palabra) <= 15 and palabra.replace('ñ', '').replace('á', '').replace('é', '').replace('í', '').replace('ó', '').replace('ú', '').replace('ü', '').isalpha():
                    palabras.append(palabra)
            
            print(f" Diccionario cargado: {len(palabras):,} palabras desde {path}")
            return list(set(palabras))  # Eliminar duplicados
    except Exception as e:
        print(f" Error al cargar diccionario {path}: {e}")
        return []


def construir_modelo_markov(palabras: List[str], orden: int = 2) -> Dict[str, List[str]]:
    """
    Construye un modelo de Markov de n-gramas desde una lista de palabras.
    
    Args:
        palabras: Lista de palabras para analizar
        orden: Orden del modelo (2 = bigramas, 3 = trigramas)
    
    Returns:
        Diccionario {prefijo: [posibles_sufijos]}
    """
    modelo = {}
    
    for palabra in palabras:
        palabra = palabra.lower()
        # Añadir marcadores de inicio y fin
        palabra_mod = '^' * orden + palabra + '$'
        
        for i in range(len(palabra_mod) - orden):
            prefijo = palabra_mod[i:i+orden]
            sufijo = palabra_mod[i+orden]
            
            if prefijo not in modelo:
                modelo[prefijo] = []
            modelo[prefijo].append(sufijo)
    
    return modelo


def generar_palabra_markov(
    modelo: Dict[str, List[str]], 
    longitud_min: int = 4, 
    longitud_max: int = 10,
    orden: int = 2
) -> str:
    """
    Genera una pseudopalabra usando el modelo de Markov.
    
    Args:
        modelo: Modelo construido con construir_modelo_markov()
        longitud_min: Longitud mínima de la palabra
        longitud_max: Longitud máxima de la palabra
        orden: Orden del modelo
    
    Returns:
        Pseudopalabra generada
    """
    if not modelo:
        return generar_palabra_con_ngramas(random.randint(longitud_min, longitud_max))
    
    # Empezar con el marcador de inicio
    palabra = '^' * orden
    
    # Generar caracteres hasta encontrar fin o límite
    intentos = 0
    while intentos < 100:  # Evitar bucles infinitos
        prefijo = palabra[-orden:]
        
        if prefijo not in modelo:
            # Si no hay continuación, terminar
            break
        
        # Elegir siguiente carácter
        siguiente = random.choice(modelo[prefijo])
        
        if siguiente == '$':
            # Fin de palabra encontrado
            if len(palabra) - orden >= longitud_min:
                break
            else:
                # Palabra muy corta, reintentar
                palabra = '^' * orden
                intentos += 1
                continue
        
        palabra += siguiente
        
        # Límite de longitud
        if len(palabra) - orden >= longitud_max:
            break
        
        intentos += 1
    
    # Eliminar marcadores
    resultado = palabra.replace('^', '').replace('$', '')
    
    # Si falló, generar con n-gramas simples
    if len(resultado) < longitud_min:
        return generar_palabra_con_ngramas(random.randint(longitud_min, longitud_max))
    
    return resultado


# ==================== GENERADORES ESPECIALIZADOS ====================

def generar_fecha_realista() -> str:
    """Genera una fecha en formato realista."""
    formato = random.choice([
        "%d/%m/%Y",      # 15/11/2025
        "%d-%m-%Y",      # 15-11-2025
        "%Y/%m/%d",      # 2025/11/15
        "%Y-%m-%d",      # 2025-11-15
        "%d.%m.%Y",      # 15.11.2025
        "%d/%m/%y",      # 15/11/25
    ])
    
    # Generar fecha entre 1950 y 2030
    inicio = datetime(1950, 1, 1)
    fin = datetime(2030, 12, 31)
    dias = (fin - inicio).days
    fecha_random = inicio + timedelta(days=random.randint(0, dias))
    
    return fecha_random.strftime(formato)


def generar_numero_realista() -> str:
    """Genera números con patrones realistas."""
    tipo = random.choice([
        'entero_corto',      # 1-999
        'entero_medio',      # 1000-9999
        'decimal',           # 123.45
        'telefono',          # +34-123-456-789
        'codigo_postal',     # 28001, 08001
        'porcentaje',        # 15%, 99.9%
        'moneda',            # 1500.00, 99.99
        'año',               # 1990-2025
    ])
    
    if tipo == 'entero_corto':
        return str(random.randint(1, 999))
    elif tipo == 'entero_medio':
        return str(random.randint(1000, 9999))
    elif tipo == 'decimal':
        return f"{random.uniform(0, 999):.2f}"
    elif tipo == 'telefono':
        return f"+{random.randint(1,99)}-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}"
    elif tipo == 'codigo_postal':
        return f"{random.randint(10000, 99999)}"
    elif tipo == 'porcentaje':
        return f"{random.uniform(0, 100):.1f}%"
    elif tipo == 'moneda':
        return f"{random.uniform(0, 9999):.2f}"
    elif tipo == 'año':
        return str(random.randint(1950, 2025))


def generar_palabra_con_ngramas(longitud: int) -> str:
    """Genera una palabra respetando n-gramas comunes."""
    if longitud < 2:
        return random.choice(list(FRECUENCIAS_ESPANOL.keys()))
    
    palabra = ""
    
    # Empezar con un bigrama común
    palabra = random.choice(BIGRAMAS_COMUNES)
    
    # Continuar añadiendo caracteres con frecuencias realistas
    letras = list(FRECUENCIAS_ESPANOL.keys())
    pesos = list(FRECUENCIAS_ESPANOL.values())
    
    while len(palabra) < longitud:
        # Añadir letra según frecuencia
        letra = random.choices(letras, weights=pesos, k=1)[0]
        palabra += letra
    
    return palabra[:longitud]


def generar_palabra_con_afijos() -> str:
    """Genera palabra con prefijos/sufijos comunes."""
    # Base aleatoria
    base = random.choice(PALABRAS_ESPANOL[:50])
    
    # 50% chance de añadir prefijo
    if random.random() > 0.5:
        prefijo = random.choice(PREFIJOS)
        base = prefijo + base
    
    # 50% chance de añadir sufijo
    if random.random() > 0.5:
        sufijo = random.choice(SUFIJOS)
        base = base + sufijo
    
    return base


def generar_email() -> str:
    """Genera un email realista."""
    usuario = random.choice(NOMBRES_PROPIOS).lower()
    numero = random.randint(1, 999) if random.random() > 0.5 else ""
    dominio = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'empresa.com'])
    
    return f"{usuario}{numero}@{dominio}"


def generar_codigo() -> str:
    """Genera código/identificador realista."""
    tipo = random.choice([
        'alfanumerico',  # ABC123
        'guiones',       # ABC-123-XYZ
        'hash',          # A1B2C3D4
    ])
    
    if tipo == 'alfanumerico':
        letras = ''.join(random.choices(string.ascii_uppercase, k=3))
        numeros = ''.join(random.choices(string.digits, k=3))
        return letras + numeros
    elif tipo == 'guiones':
        p1 = ''.join(random.choices(string.ascii_uppercase, k=3))
        p2 = ''.join(random.choices(string.digits, k=3))
        p3 = ''.join(random.choices(string.ascii_uppercase, k=3))
        return f"{p1}-{p2}-{p3}"
    elif tipo == 'hash':
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generar_caso_dificil_ocr() -> str:
    """Genera casos diseñados para confundir OCR (caracteres similares)."""
    tipo = random.choice([
        'confusion_lI1',     # l, I, 1
        'confusion_O0',      # O, 0
        'password_mixed',    # Password1Il0O
        'url',               # https://example.com/path
        'iban',              # ES12 3456 7890 1234 5678
    ])
    
    if tipo == 'confusion_lI1':
        # Mezclar l (L minúscula), I (i mayúscula), 1 (uno)
        chars = ['l', 'I', '1']
        return ''.join(random.choices(chars, k=random.randint(4, 8)))
    
    elif tipo == 'confusion_O0':
        # Mezclar O (o mayúscula) y 0 (cero)
        chars = ['O', '0']
        return ''.join(random.choices(chars, k=random.randint(4, 8)))
    
    elif tipo == 'password_mixed':
        # Password con todos los caracteres confusos
        base = random.choice(['Pass', 'User', 'Admin', 'Login'])
        confuso = ''.join(random.choices(['1', 'l', 'I', '0', 'O'], k=4))
        return base + confuso
    
    elif tipo == 'url':
        # URL realista y más larga (ahora soportada por input_width=512)
        protocolo = random.choice(['http://', 'https://'])
        subdominio = random.choice(['www.', 'api.', 'blog.', 'shop.', ''])
        dominio = random.choice(['example', 'website', 'page', 'site', 'amazon', 'google', 'github'])
        ext = random.choice(['.com', '.org', '.net', '.es', '.io', '.co.uk'])
        
        # Generar path más complejo
        segmentos = ['page', 'user', 'product', 'item', 'category', 'article', 'id']
        path = f"/{random.choice(segmentos)}/{random.randint(1000,9999)}"
        
        # Opcionalmente añadir más profundidad o query params
        if random.random() > 0.5:
            path += f"/{random.choice(['details', 'view', 'edit'])}"
        
        if random.random() > 0.6:
            path += f"?id={random.randint(100,999)}&ref={random.choice(['a', 'b', 'c'])}"
            
        # Asegurar longitud máxima de 64 caracteres para URLs (antes 40)
        url = f"{protocolo}{subdominio}{dominio}{ext}{path}"
        if len(url) > 64:
            # Truncar o regenerar más corto
            return url[:64]
        return url
    
    elif tipo == 'iban':
        # IBAN español simulado
        return f"ES{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"


def aplicar_variaciones_texto(palabra: str) -> str:
    """Aplica variaciones de casing y puntuación a una palabra."""
    # Distribución aproximada para cumplir con:
    # 40% minúsculas, 30% capitalize, 10% mayúsculas (en el total del dataset)
    # Como esto solo aplica a palabras (80% del dataset), ajustamos los pesos internos:
    # Lower: 0.5, Capitalize: 0.35, Upper: 0.15
    
    opciones = ['lower', 'capitalize', 'upper', 'puntuacion']
    pesos = [0.45, 0.35, 0.15, 0.05]
    
    variacion = random.choices(opciones, weights=pesos, k=1)[0]
    
    if variacion == 'lower':
        return palabra.lower()
    elif variacion == 'upper':
        return palabra.upper()
    elif variacion == 'capitalize':
        return palabra.capitalize()
    elif variacion == 'puntuacion':
        # Aplicar puntuación y mantener casing original o random
        palabra_base = random.choice([palabra.lower(), palabra.capitalize()])
        signo = random.choice(['()', '[]', '.', ',', ';', ':', '?', '!', '¿?', '¡!'])
        if signo in ['()', '[]']:
            return f"{signo[0]}{palabra_base}{signo[1]}"
        elif signo in ['¿?', '¡!']:
            return f"{signo[0]}{palabra_base}{signo[1]}"
        else:
            return f"{palabra_base}{signo}"
    else:
        return palabra


def generar_frase_corta() -> str:
    """Genera una frase corta de 2-4 palabras."""
    longitud = random.randint(2, 4)
    
    # Patrones simples de frases
    if longitud == 2:
        # Artículo + Sustantivo, Verbo + Sustantivo
        patron = random.choice([
            lambda: f"{random.choice(['el', 'la', 'un', 'una'])} {random.choice(PALABRAS_ESPANOL[56:70])}",
            lambda: f"{random.choice(PALABRAS_ESPANOL[63:68])} {random.choice(PALABRAS_ESPANOL[56:70])}",
        ])
    elif longitud == 3:
        # Artículo + Adjetivo + Sustantivo
        patron = lambda: f"{random.choice(['el', 'la'])} {random.choice(PALABRAS_ESPANOL[69:75])} {random.choice(PALABRAS_ESPANOL[56:70])}"
    else:  # 4
        # Artículo + Sustantivo + Preposición + Sustantivo
        patron = lambda: f"{random.choice(['el', 'la'])} {random.choice(PALABRAS_ESPANOL[56:70])} {random.choice(['de', 'en', 'con'])} {random.choice(PALABRAS_ESPANOL[56:70])}"
    
    frase = patron()
    frase = patron()
    # Asegurar límite de 64 caracteres
    if len(frase) > 64:
        return frase[:64]
    return frase


# ==================== GENERADOR PRINCIPAL ====================

def generar_dataset_realista(
    cantidad: int = 50000,
    distribucion: Dict[str, float] = None,
    seed: int = None,
    verbose: bool = True,
    dict_español: str = None,
    dict_ingles: str = None,
    usar_variaciones: bool = True,
    longitud_min: int = 3,
    longitud_max: int = 40,
    **kwargs
) -> List[str]:
    """
    Genera un dataset realista con diferentes tipos de texto.
    
    Args:
        cantidad: Número total de items a generar
        distribucion: Distribución de tipos (None = default)
        seed: Semilla para reproducibilidad
        verbose: Mostrar progreso
        dict_español: Ruta a diccionario español externo
        dict_ingles: Ruta a diccionario inglés externo
        usar_variaciones: Aplicar variaciones de casing/puntuación
    
    Returns:
        Lista de strings generados
    """
    if seed is not None:
        random.seed(seed)
    
    # Cargar diccionarios externos si se proporcionan
    global DICCIONARIO_EXTERNO_ES, DICCIONARIO_EXTERNO_EN
    
    if dict_español:
        DICCIONARIO_EXTERNO_ES = cargar_diccionario_externo(dict_español, max_palabras=10000)
    
    if dict_ingles:
        DICCIONARIO_EXTERNO_EN = cargar_diccionario_externo(dict_ingles, max_palabras=5000)
    
    # Construir modelo de Markov para pseudopalabras
    modelo_markov = None
    if DICCIONARIO_EXTERNO_ES or PALABRAS_ESPANOL:
        fuente_markov = DICCIONARIO_EXTERNO_ES if DICCIONARIO_EXTERNO_ES else PALABRAS_ESPANOL
        if verbose:
            print(f" Construyendo modelo Markov con {len(fuente_markov):,} palabras...")
        modelo_markov = construir_modelo_markov(fuente_markov, orden=2)
        if verbose:
            print(f" Modelo Markov creado con {len(modelo_markov):,} n-gramas")
    
    # Distribución por defecto (optimizada para OCR español con nuevos tipos)
    if distribucion is None:
        distribucion = {
            'palabras_espanol': 0.25,      # 25% palabras reales español
            'palabras_ingles': 0.06,       # 6% palabras inglés
            'nombres_propios': 0.13,       # 13% nombres/apellidos
            'fechas': 0.06,                # 6% fechas
            'numeros': 0.06,               # 6% números
            'lugares': 0.03,               # 3% ciudades/países
            'palabras_ngramas': 0.02,      # 2% palabras con n-gramas básicos
            'palabras_afijos': 0.02,       # 2% palabras con prefijos/sufijos
            'codigos': 0.05,               # 5% códigos/IDs
            'palabras_markov': 0.11,       # 11% pseudopalabras realistas (Markov)
            'casos_dificiles_ocr': 0.15,   # 15% casos confusos y URLs
            'frases_cortas': 0.04,         # 4% frases de 2-4 palabras
            'emails': 0.02,                # 2% emails (@)
            # Total technical/hard: 5% + 15% + 2% + 6% = 28%
            # Total text: 72%
        }
    
    # Validar distribución
    total = sum(distribucion.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"La distribución debe sumar 1.0 (actual: {total})")
    
    if verbose:
        print(f"\n{'='*70}")
        print(f" GENERANDO DATASET REALISTA V2.1")
        print(f"{'='*70}")
        print(f"\n Distribución:")
        for tipo, porcentaje in sorted(distribucion.items(), key=lambda x: -x[1]):
            cant = int(cantidad * porcentaje)
            print(f"   • {tipo:25s}: {porcentaje*100:5.1f}% ({cant:6,} items)")
        print(f"\n️  Variaciones de texto: {'ACTIVADAS' if usar_variaciones else 'DESACTIVADAS'}")
        print()
    
    dataset = []
    
    # Generar cada tipo según distribución
    for tipo, porcentaje in distribucion.items():
        cant_tipo = int(cantidad * porcentaje)
        
        if verbose:
            print(f" Generando {cant_tipo:,} {tipo}...", end=' ')
        
        for _ in range(cant_tipo):
            if tipo == 'palabras_espanol':
                fuente = DICCIONARIO_EXTERNO_ES if DICCIONARIO_EXTERNO_ES else PALABRAS_ESPANOL
                item = random.choice(fuente)
            elif tipo == 'palabras_ingles':
                fuente = DICCIONARIO_EXTERNO_EN if DICCIONARIO_EXTERNO_EN else PALABRAS_INGLES
                item = random.choice(fuente)
            elif tipo == 'nombres_propios':
                item = random.choice(NOMBRES_PROPIOS)
            elif tipo == 'fechas':
                item = generar_fecha_realista()
            elif tipo == 'numeros':
                item = generar_numero_realista()
            elif tipo == 'lugares':
                item = random.choice(LUGARES)
            elif tipo == 'palabras_ngramas':
                # Usar longitud variable hasta el máximo permitido
                l_min = max(4, longitud_min)
                l_min = max(4, longitud_min)
                l_max = min(longitud_max, 64) # Límite aumentado a 64

                longitud = random.randint(l_min, l_max)
                item = generar_palabra_con_ngramas(longitud)
            elif tipo == 'palabras_afijos':
                item = generar_palabra_con_afijos()
            elif tipo == 'codigos':
                item = generar_codigo()
            elif tipo == 'palabras_markov':
                if modelo_markov:
                    # Usar límites pasados a la función
                    l_min = max(4, longitud_min)
                    l_max = min(longitud_max, 64) # Límite aumentado a 64

                    item = generar_palabra_markov(modelo_markov, longitud_min=l_min, longitud_max=l_max)
                else:
                    item = generar_palabra_con_ngramas(random.randint(5, 10))
            elif tipo == 'casos_dificiles_ocr':
                item = generar_caso_dificil_ocr()
            elif tipo == 'frases_cortas':
                item = generar_frase_corta()
            elif tipo == 'emails':
                item = generar_email()
            else:
                item = random.choice(PALABRAS_ESPANOL)
            
            # Aplicar variaciones de texto (casing, puntuación)
            if usar_variaciones and tipo in ['palabras_espanol', 'palabras_ingles', 'nombres_propios', 
                                               'palabras_markov', 'palabras_ngramas', 'palabras_afijos']:
                item = aplicar_variaciones_texto(item)
            
            dataset.append(item)
        
        if verbose:
            print("")
    
    # Shuffle final
    random.shuffle(dataset)
    
    if verbose:
        print(f"\n Dataset generado: {len(dataset):,} items")
        print(f"{'='*70}\n")
    
    return dataset


def mostrar_estadisticas_realistas(dataset: List[str]) -> None:
    """Muestra estadísticas del dataset realista."""
    print(f"\n{'='*70}")
    print(f" ESTADÍSTICAS DEL DATASET REALISTA")
    print(f"{'='*70}\n")
    
    # Análisis básico
    total = len(dataset)
    unicos = len(set(dataset))
    longitudes = [len(item) for item in dataset]
    
    print(f" Items:")
    print(f"   • Total: {total:,}")
    print(f"   • Únicos: {unicos:,} ({unicos/total*100:.1f}%)")
    print(f"   • Longitud min: {min(longitudes)}")
    print(f"   • Longitud max: {max(longitudes)}")
    print(f"   • Longitud promedio: {sum(longitudes)/len(longitudes):.2f}")
    
    # Análisis de tipos
    print(f"\n Tipos detectados:")
    contiene_numeros = sum(1 for item in dataset if any(c.isdigit() for c in item))
    contiene_letras = sum(1 for item in dataset if any(c.isalpha() for c in item))
    contiene_simbolos = sum(1 for item in dataset if any(c in '/-.:@%' for c in item))
    mayusculas = sum(1 for item in dataset if any(c.isupper() for c in item))
    
    print(f"   • Con números: {contiene_numeros:,} ({contiene_numeros/total*100:.1f}%)")
    print(f"   • Con letras: {contiene_letras:,} ({contiene_letras/total*100:.1f}%)")
    print(f"   • Con símbolos: {contiene_simbolos:,} ({contiene_simbolos/total*100:.1f}%)")
    print(f"   • Con mayúsculas: {mayusculas:,} ({mayusculas/total*100:.1f}%)")
    
    # Muestra
    print(f"\n Muestra aleatoria (20 items):")
    muestra = random.sample(dataset, min(20, len(dataset)))
    for i, item in enumerate(muestra, 1):
        print(f"   {i:2d}. {item}")
    
    print(f"\n{'='*70}\n")


def guardar_dataset_realista(
    dataset: List[str],
    archivo: str = None,
    mostrar_stats: bool = True
) -> str:
    """Guarda el dataset realista en un archivo."""
    if archivo is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"dataset_realista_{timestamp}.txt"
    
    archivo_path = Path(archivo)
    archivo_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(archivo_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dataset))
    
    print(f" Archivo guardado: {archivo_path.absolute()}")
    print(f"   Tamaño: {archivo_path.stat().st_size / 1024:.2f} KB")
    
    if mostrar_stats:
        mostrar_estadisticas_realistas(dataset)
    
    return str(archivo_path.absolute())


# ==================== MAIN ====================

def main():
    """Función principal con interfaz CLI."""
    parser = argparse.ArgumentParser(
        description=' Generador de Palabras Realistas para Dataset OCR V2.1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s -c 20000 -o dataset.txt
  %(prog)s -c 50000 -s 42 -o ../datos/labels.txt
  %(prog)s -c 10000 -o test.txt --dict-es diccionario_es.txt
  %(prog)s -c 10000 --no-verbose --no-stats --no-variaciones
        """
    )
    
    # Argumentos principales
    parser.add_argument(
        '-c', '--cantidad',
        type=int,
        default=DEFAULT_DATASET_SIZE,
        help=f'Cantidad de palabras a generar (default: {DEFAULT_DATASET_SIZE})'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=DEFAULT_LABELS_PATH,
        help=f'Archivo de salida (default: {DEFAULT_LABELS_PATH})'
    )
    
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=30,
        help='Semilla para reproducibilidad (default: 30)'
    )
    
    # Nuevos argumentos para diccionarios externos
    parser.add_argument(
        '--dict-es',
        type=str,
        default=None,
        help='Ruta a diccionario español externo (una palabra por línea)'
    )
    
    parser.add_argument(
        '--dict-en',
        type=str,
        default=None,
        help='Ruta a diccionario inglés externo (una palabra por línea)'
    )
    
    # Argumentos de control
    parser.add_argument(
        '--no-verbose',
        action='store_true',
        help='Desactivar mensajes de progreso'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='No mostrar estadísticas al finalizar'
    )
    
    parser.add_argument(
        '--no-variaciones',
        action='store_true',
        help='Desactivar variaciones de casing y puntuación'
    )
    
    # Parsear argumentos
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print(" GENERADOR DE PALABRAS REALISTAS V2.1")
    print("="*70)
    
    # Generar dataset
    dataset = generar_dataset_realista(
        cantidad=args.cantidad,
        seed=args.seed,
        verbose=not args.no_verbose,
        dict_español=args.dict_es,
        dict_ingles=args.dict_en,
        usar_variaciones=not args.no_variaciones
    )
    
    # Guardar
    archivo = guardar_dataset_realista(
        dataset,
        archivo=args.output,
        mostrar_stats=not args.no_stats
    )
    
    print(f"\n ¡Dataset realista generado exitosamente!")
    print(f" Ubicación: {archivo}\n")


if __name__ == "__main__":
    main()
