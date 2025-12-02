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
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import Counter


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


# ==================== GENERADOR PRINCIPAL ====================

def generar_dataset_realista(
    cantidad: int = 50000,
    distribucion: Dict[str, float] = None,
    seed: int = None,
    verbose: bool = True
) -> List[str]:
    """
    Genera un dataset realista con diferentes tipos de texto.
    
    Args:
        cantidad: Número total de items a generar
        distribucion: Distribución de tipos (None = default)
        seed: Semilla para reproducibilidad
        verbose: Mostrar progreso
    
    Returns:
        Lista de strings generados
    """
    if seed is not None:
        random.seed(seed)
    
    # Distribución por defecto (optimizada para OCR español)
    if distribucion is None:
        distribucion = {
            'palabras_espanol': 0.40,      # 40% palabras reales español
            'palabras_ingles': 0.10,       # 10% palabras inglés
            'nombres_propios': 0.15,       # 15% nombres/apellidos
            'fechas': 0.10,                # 10% fechas
            'numeros': 0.10,               # 10% números
            'lugares': 0.05,               # 5% ciudades/países
            'palabras_ngramas': 0.05,      # 5% palabras con n-gramas
            'palabras_afijos': 0.03,       # 3% palabras con prefijos/sufijos
            'codigos': 0.02,               # 2% códigos/IDs
        }
    
    # Validar distribución
    total = sum(distribucion.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"La distribución debe sumar 1.0 (actual: {total})")
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🎯 GENERANDO DATASET REALISTA")
        print(f"{'='*70}")
        print(f"\n📊 Distribución:")
        for tipo, porcentaje in sorted(distribucion.items(), key=lambda x: -x[1]):
            cant = int(cantidad * porcentaje)
            print(f"   • {tipo:25s}: {porcentaje*100:5.1f}% ({cant:6,} items)")
        print()
    
    dataset = []
    
    # Generar cada tipo según distribución
    for tipo, porcentaje in distribucion.items():
        cant_tipo = int(cantidad * porcentaje)
        
        if verbose:
            print(f"⏳ Generando {cant_tipo:,} {tipo}...", end=' ')
        
        for _ in range(cant_tipo):
            if tipo == 'palabras_espanol':
                item = random.choice(PALABRAS_ESPANOL)
            elif tipo == 'palabras_ingles':
                item = random.choice(PALABRAS_INGLES)
            elif tipo == 'nombres_propios':
                item = random.choice(NOMBRES_PROPIOS)
            elif tipo == 'fechas':
                item = generar_fecha_realista()
            elif tipo == 'numeros':
                item = generar_numero_realista()
            elif tipo == 'lugares':
                item = random.choice(LUGARES)
            elif tipo == 'palabras_ngramas':
                longitud = random.randint(4, 10)
                item = generar_palabra_con_ngramas(longitud)
            elif tipo == 'palabras_afijos':
                item = generar_palabra_con_afijos()
            elif tipo == 'codigos':
                item = generar_codigo()
            else:
                item = random.choice(PALABRAS_ESPANOL)
            
            dataset.append(item)
        
        if verbose:
            print("✅")
    
    # Shuffle final
    random.shuffle(dataset)
    
    if verbose:
        print(f"\n✨ Dataset generado: {len(dataset):,} items")
        print(f"{'='*70}\n")
    
    return dataset


def mostrar_estadisticas_realistas(dataset: List[str]) -> None:
    """Muestra estadísticas del dataset realista."""
    print(f"\n{'='*70}")
    print(f"📊 ESTADÍSTICAS DEL DATASET REALISTA")
    print(f"{'='*70}\n")
    
    # Análisis básico
    total = len(dataset)
    unicos = len(set(dataset))
    longitudes = [len(item) for item in dataset]
    
    print(f"📝 Items:")
    print(f"   • Total: {total:,}")
    print(f"   • Únicos: {unicos:,} ({unicos/total*100:.1f}%)")
    print(f"   • Longitud min: {min(longitudes)}")
    print(f"   • Longitud max: {max(longitudes)}")
    print(f"   • Longitud promedio: {sum(longitudes)/len(longitudes):.2f}")
    
    # Análisis de tipos
    print(f"\n🔍 Tipos detectados:")
    contiene_numeros = sum(1 for item in dataset if any(c.isdigit() for c in item))
    contiene_letras = sum(1 for item in dataset if any(c.isalpha() for c in item))
    contiene_simbolos = sum(1 for item in dataset if any(c in '/-.:@%' for c in item))
    mayusculas = sum(1 for item in dataset if any(c.isupper() for c in item))
    
    print(f"   • Con números: {contiene_numeros:,} ({contiene_numeros/total*100:.1f}%)")
    print(f"   • Con letras: {contiene_letras:,} ({contiene_letras/total*100:.1f}%)")
    print(f"   • Con símbolos: {contiene_simbolos:,} ({contiene_simbolos/total*100:.1f}%)")
    print(f"   • Con mayúsculas: {mayusculas:,} ({mayusculas/total*100:.1f}%)")
    
    # Muestra
    print(f"\n📋 Muestra aleatoria (20 items):")
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
    
    print(f"💾 Archivo guardado: {archivo_path.absolute()}")
    print(f"   Tamaño: {archivo_path.stat().st_size / 1024:.2f} KB")
    
    if mostrar_stats:
        mostrar_estadisticas_realistas(dataset)
    
    return str(archivo_path.absolute())


# ==================== MAIN ====================

def main():
    """Función principal con interfaz CLI."""
    parser = argparse.ArgumentParser(
        description='🎯 Generador de Palabras Realistas para Dataset OCR V2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s -c 20000 -o dataset.txt
  %(prog)s -c 50000 -s 42 -o ../datos/labels.txt
  %(prog)s -c 10000 -o test.txt --no-verbose --no-stats
        """
    )
    
    # Argumentos principales
    parser.add_argument(
        '-c', '--cantidad',
        type=int,
        default=20000,
        help='Cantidad de palabras a generar (default: 20000)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='../modelo_20k/labels_realistas.txt',
        help='Archivo de salida (default: ../modelo_20k/labels_realistas.txt)'
    )
    
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=30,
        help='Semilla para reproducibilidad (default: 30)'
    )
    
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
    
    # Parsear argumentos
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🎯 GENERADOR DE PALABRAS REALISTAS V2.0")
    print("="*70)
    
    # Generar dataset
    dataset = generar_dataset_realista(
        cantidad=args.cantidad,
        seed=args.seed,
        verbose=not args.no_verbose
    )
    
    # Guardar
    archivo = guardar_dataset_realista(
        dataset,
        archivo=args.output,
        mostrar_stats=not args.no_stats
    )
    
    print(f"\n✨ ¡Dataset realista generado exitosamente!")
    print(f"📂 Ubicación: {archivo}\n")


if __name__ == "__main__":
    main()
