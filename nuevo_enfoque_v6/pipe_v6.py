#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline V6: Salto a High-Res + 200K Imágenes
=============================================
1. Genera dataset masivo de 200K imágenes con textos largos (hasta 64 chars)
2. Entrena modelo High-Res desde cero
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
    print("PIPELINE V6: High-Res + 200K".center(70))
    print("=" + " "*66 + "=")
    print("="*35 + "\n")
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config.yaml"
    
    # Cargar configuración
    if not config_path.exists():
        print(f"Error: No se encontró {config_path}")
        sys.exit(1)
        
    config = load_config(config_path)
    dataset_size = config['dataset'].get('dataset_size', 200000)
    
    # Directorios desde config
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
    print(f"PASO 1a/3: Generando {dataset_size:,} palabras realistas (V6)")
    print("="*70)
    
    generador_dir = base_dir 
    
    # Verificar si existen diccionarios externos
    dict_es_path = base_dir / "diccionarios" / "spanish.txt"
    dict_en_path = base_dir / "diccionarios" / "english.txt"
    
    # Verificar si ya existe
    if labels_path.exists():
        print(f"Labels realistas ya existen: {labels_path}")
        # Contar líneas para ver si coincide con el tamaño deseado
        with open(labels_path, 'r', encoding='utf-8') as f:
            count = sum(1 for _ in f)
        
        print(f"   Items actuales: {count:,}")
        print(f"   Items deseados: {dataset_size:,}")
        
        if count < dataset_size:
            print("   ⚠️  El archivo existente es menor al deseado. REGENERANDO...")
            response = 's'
        else:
            response = input("¿Regenerar palabras? [s/N]: ").lower()
        
        if response != 's':
            print("Usando palabras existentes")
        else:
            print("Regenerando palabras...")
            cmd = [
                sys.executable, "generador_palabras_realistas.py", 
                "-c", str(dataset_size), 
                "-o", str(labels_path)
            ]
            if dict_es_path.exists(): cmd.extend(["--dict-es", str(dict_es_path)])
            if dict_en_path.exists(): cmd.extend(["--dict-en", str(dict_en_path)])
            
            result = subprocess.run(cmd, cwd=str(generador_dir))
            if result.returncode != 0: sys.exit(1)
    else:
        print("Generando palabras realistas...")
        cmd = [
            sys.executable, "generador_palabras_realistas.py", 
            "-c", str(dataset_size), 
            "-o", str(labels_path)
        ]
        if dict_es_path.exists(): cmd.extend(["--dict-es", str(dict_es_path)])
        if dict_en_path.exists(): cmd.extend(["--dict-en", str(dict_en_path)])
        
        result = subprocess.run(cmd, cwd=str(generador_dir))
        if result.returncode != 0: sys.exit(1)
    
    print(f"Labels generados: {labels_path}\n")
    
    # PASO 1b: Crear imágenes desde las palabras
    print("\n" + "="*70)
    print(f"PASO 1b/3: Creando imágenes ({dataset_size:,})")
    print("="*70)
    
    dataset_creator_dir = base_dir 
    
    # Verificar si ya existen imágenes
    existing_images = list(images_dir.glob("*.png"))
    num_images = len(existing_images)
    
    if num_images > 0:
        print(f"Dataset ya existe: {num_images:,} imágenes")
        if num_images < dataset_size * 0.9: # Si falta más del 10%
             print("   ⚠️  Faltan imágenes. REGENERANDO (Limpiando anterior)...")
             response = 's'
        else:
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
            if result.returncode != 0: sys.exit(1)
    else:
        print("Creando imágenes desde palabras realistas...")
        result = subprocess.run([
            sys.executable, "dataset_creator_v2.py",
            "--archivo-palabras", str(labels_path),
            "--limpiar",
            "--output", str(images_dir),
            "--fonts", str(fonts_dir)
        ], cwd=str(dataset_creator_dir))
        if result.returncode != 0: sys.exit(1)
    
    # PASO 2: Configurar entrenamiento
    print("\n" + "="*70)
    print("PASO 2/3: Configuración V6")
    print("="*70)
    print(f"   - Dataset size: {dataset_size:,}")
    print(f"   - Max Length: {config['dataset']['max_text_length']}")
    print(f"   - Épocas: {config['training']['epochs']}")
    
    # PASO 3: Entrenar modelo usando train.py
    print("\n" + "="*70)
    print("PASO 3/3: Entrenando modelo V6 desde cero")
    print("="*70)
    
    env = os.environ.copy()
    train_script = base_dir / "train.py"
    
    result = subprocess.run(
        [sys.executable, str(train_script)],
        cwd=str(base_dir),
        env=env
    )
    
    if result.returncode != 0:
        print(f"\nError durante el entrenamiento")
        sys.exit(1)
    
    print("\n" + "="*35)
    print("PIPELINE V6 COMPLETADO".center(70))
    print("="*35 + "\n")

if __name__ == '__main__':
    main()
