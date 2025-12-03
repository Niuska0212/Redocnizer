#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline Limpio: Modelo 20K desde Cero (SIN Transfer Learning)
===============================================================
1. Genera dataset de entrenamiento 20K
2. Entrena modelo desde cero usando train_20k.py
3. Guarda checkpoints y logs

IMPORTANTE: Este pipeline NO usa transfer learning.
   Entrena el modelo desde cero con inicialización aleatoria.
"""

import subprocess
import sys
from pathlib import Path
import yaml
import os

def load_config(path='config.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    print("\n" + "="*35)
    print("=" + " "*66 + "=")
    print("PIPELINE LIMPIO: Entrenamiento desde Cero".center(70))
    print("=" + " "*66 + "=")
    print("="*35 + "\n")
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config.yaml"
    
    # Cargar configuración
    if not config_path.exists():
        print(f"Error: No se encontró {config_path}")
        sys.exit(1)
        
    config = load_config(config_path)
    dataset_size = config['dataset'].get('dataset_size', 20000)
    
    # Directorios desde config
    modelo_dir = base_dir / "dataset_entrenamiento" # Mantener estructura original o leer de config si se prefiere
    # Nota: config.yaml tiene rutas relativas como 'dataset_entrenamiento/dataset'
    # Vamos a respetar las rutas del config para consistencia
    
    images_dir = base_dir / config['dataset']['images_dir']
    labels_path = base_dir / config['dataset']['labels_path']
    checkpoints_dir = base_dir / config['training']['checkpoint_dir']
    logs_dir = base_dir / config['training']['logs_dir']
    fonts_dir = base_dir / config['dataset']['fonts_dir']

    # Crear estructura de directorios
    print("Creando estructura de directorios...")
    images_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    print("Estructura creada\n")
    
    # PASO 1: Generar labels realistas
    print("\n" + "="*70)
    print(f"PASO 1a/3: Generando {dataset_size:,} palabras realistas")
    print("="*70)
    
    # Usamos labels_path definido en config
    generador_dir = base_dir 
    
    # Verificar si existen diccionarios externos
    dict_es_path = base_dir / "diccionarios" / "spanish.txt"
    dict_en_path = base_dir / "diccionarios" / "english.txt"
    
    # Verificar si ya existe
    if labels_path.exists():
        print(f"Generador de palabras: {generador_dir}")
        print(f"Labels realistas ya existen: {labels_path}")
        response = input("   ¿Regenerar palabras? [s/N]: ").lower()
        if response != 's':
            print("Usando palabras existentes")
        else:
            print("Regenerando palabras...")
            
            # Construir comando con diccionarios externos
            cmd = [
                sys.executable, "generador_palabras_realistas.py", 
                "-c", str(dataset_size), 
                "-o", str(labels_path)
            ]
            
            # Añadir diccionarios si existen
            if dict_es_path.exists():
                cmd.extend(["--dict-es", str(dict_es_path)])
                print(f"    Usando diccionario español: {dict_es_path.name}")
            if dict_en_path.exists():
                cmd.extend(["--dict-en", str(dict_en_path)])
                print(f"    Usando diccionario inglés: {dict_en_path.name}")
            
            result = subprocess.run(cmd, cwd=str(generador_dir))
            if result.returncode != 0:
                print("Error generando palabras")
                sys.exit(1)
    else:
        print("Generando palabras realistas...")
        
        # Construir comando con diccionarios externos
        cmd = [
            sys.executable, "generador_palabras_realistas.py", 
            "-c", str(dataset_size), 
            "-o", str(labels_path)
        ]
        
        # Añadir diccionarios si existen
        if dict_es_path.exists():
            cmd.extend(["--dict-es", str(dict_es_path)])
            print(f"    Usando diccionario español: {dict_es_path.name}")
        else:
            print(f"   ℹ️  No se encontró {dict_es_path.name} (usando vocabulario interno)")
            
        if dict_en_path.exists():
            cmd.extend(["--dict-en", str(dict_en_path)])
            print(f"    Usando diccionario inglés: {dict_en_path.name}")
        else:
            print(f"   ℹ️  No se encontró {dict_en_path.name} (usando vocabulario interno)")
        
        result = subprocess.run(cmd, cwd=str(generador_dir))
        if result.returncode != 0:
            print("Error generando palabras")
            sys.exit(1)
    
    print(f"Labels generados: {labels_path}\n")
    
    # PASO 1b: Crear imágenes desde las palabras
    print("\n" + "="*70)
    print(f"PASO 1b/3: Creando imágenes ({dataset_size:,})")
    print("="*70)
    
    dataset_creator_dir = base_dir 
    
    # Verificar si ya existen imágenes
    if images_dir.exists() and list(images_dir.glob("*.png")):
        num_images = len(list(images_dir.glob("*.png")))
        print(f"Dataset ya existe: {num_images} imágenes")
        response = input("   ¿Regenerar imágenes? [s/N]: ").lower()
        if response != 's':
            print("Usando imágenes existentes")
        else:
            print("Regenerando imágenes...")
            result = subprocess.run([
                sys.executable, "dataset_creator_v2.py",
                "--archivo-palabras", str(labels_path),
                "--limpiar",
                "--output", str(images_dir),
                "--fonts", str(fonts_dir)
            ], cwd=str(dataset_creator_dir))
            if result.returncode != 0:
                print("Error creando imágenes")
                sys.exit(1)
    else:
        print("Creando imágenes desde palabras realistas...")
        print(f"   Fuentes: {fonts_dir}")
        print(f"   Output: {images_dir}\n")
        
        result = subprocess.run([
            sys.executable, "dataset_creator_v2.py",
            "--archivo-palabras", str(labels_path),
            "--limpiar",
            "--output", str(images_dir),
            "--fonts", str(fonts_dir)
        ], cwd=str(dataset_creator_dir))
        
        if result.returncode != 0:
            print("Error creando imágenes")
            sys.exit(1)
    
    # Verificar resultado
    num_images = len(list(images_dir.glob("*.png")))
    
    if labels_path.exists():
        with open(labels_path, 'r', encoding='utf-8') as f:
            num_labels = len([l for l in f if l.strip()])
        print(f"\nDataset creado exitosamente:")
        print(f"   • Imágenes: {num_images:,}")
        print(f"   • Labels: {num_labels:,}")
    else:
        print(f"\nError: No se encontró labels.txt")
        sys.exit(1)
    
    # PASO 2: Configurar entrenamiento
    print("\n" + "="*70)
    print("PASO 2/3: Configuración cargada desde config.yaml")
    print("="*70)
    
    print(f"Configuración actual:")
    print(f"   - Dataset size: {dataset_size:,}")
    print(f"   - Épocas: {config['training']['epochs']}")
    print(f"   - Learning Rate: {config['training']['learning_rate']}")
    print(f"   - Batch Size: {config['training']['batch_size']}")
    print(f"   - Transfer Learning: NO (inicialización aleatoria)")
    
    # PASO 3: Entrenar modelo usando train.py
    print("\n" + "="*70)
    print("PASO 3/3: Entrenando modelo desde cero")
    print("="*70)
    print("\nNOTA: El tiempo dependerá del tamaño del dataset y hardware")
    print("   El modelo se entrena desde cero (sin pesos pre-entrenados)\n")
    
    # Preparar el environment para subprocess
    env = os.environ.copy()
    
    # Ejecutar train.py (que usa config.yaml por defecto)
    train_script = base_dir / "train.py"
    
    print(f"Iniciando entrenamiento...")
    print(f"   Script: {train_script}")
    print(f"   Config: {config_path}")
    print(f"\n{'='*70}\n")
    
    result = subprocess.run(
        [sys.executable, str(train_script)],
        cwd=str(base_dir),
        env=env
    )
    
    if result.returncode != 0:
        print(f"\nError durante el entrenamiento")
        sys.exit(1)
    
    print("\n" + "="*35)
    print("=" + " "*66 + "=")
    print("PIPELINE COMPLETADO EXITOSAMENTE".center(70))
    print("=" + " "*66 + "=")
    print("="*35 + "\n")
    
    print("Resultados guardados en:")
    print(f"   - Checkpoints: {checkpoints_dir}")
    print(f"   - Logs: {logs_dir}")
    print(f"\nSiguiente paso: Evaluar generalización")
    print(f"   python test_generalization.py")
    
    # Verificar que se creó el modelo
    best_model = checkpoints_dir / "model_best.weights.h5"
    final_model = checkpoints_dir / "model_final.weights.h5"
    
    if best_model.exists():
        print(f"\nMejor modelo guardado: {best_model.name}")
    if final_model.exists():
        print(f"Modelo final guardado: {final_model.name}")

if __name__ == '__main__':
    main()
