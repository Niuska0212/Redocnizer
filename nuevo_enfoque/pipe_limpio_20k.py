#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline Limpio: Modelo 20K desde Cero (SIN Transfer Learning)
===============================================================
1. Genera dataset de entrenamiento 20K
2. Entrena modelo desde cero usando train_20k.py
3. Guarda checkpoints y logs

⚠️  IMPORTANTE: Este pipeline NO usa transfer learning.
   Entrena el modelo desde cero con inicialización aleatoria.
"""

import subprocess
import sys
from pathlib import Path
import yaml
import os

def main():
    print("\n" + "🚀"*35)
    print("🚀" + " "*66 + "🚀")
    print("🚀  PIPELINE 20K LIMPIO: Entrenamiento desde Cero  🚀".center(70))
    print("🚀" + " "*66 + "🚀")
    print("🚀"*35 + "\n")
    
    base_dir = Path(__file__).parent
    modelo_dir = base_dir / "dataset_entrenamiento"
    
    # Crear estructura de directorios
    print("📁 Creando estructura de directorios...")
    (modelo_dir / "dataset").mkdir(parents=True, exist_ok=True)
    (modelo_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
    (modelo_dir / "logs").mkdir(parents=True, exist_ok=True)
    print("✅ Estructura creada\n")
    
    # PASO 1: Generar labels realistas (20K palabras)
    print("\n" + "="*70)
    print("📝 PASO 1a/3: Generando 20K palabras realistas")
    print("="*70)
    
    labels_realistas = modelo_dir / "labels_realistas.txt"
    generador_dir = base_dir 
    
    # Verificar si ya existe
    if labels_realistas.exists():
        # imprimimos la ruta de generador_dir
        print(f"📦 Generador de palabras: {generador_dir}")
        print(f"📦 Labels realistas ya existen: {labels_realistas}")
        response = input("   ¿Regenerar palabras? [s/N]: ").lower()
        if response != 's':
            print("✅ Usando palabras existentes")
        else:
            print("🔄 Regenerando palabras...")
            result = subprocess.run(
                [sys.executable, "generador_palabras_realistas.py"],
                cwd=str(generador_dir)
            )
            if result.returncode != 0:
                print("❌ Error generando palabras")
                sys.exit(1)
    else:
        print("🚀 Generando palabras realistas...")
        result = subprocess.run(
            [sys.executable, "generador_palabras_realistas.py"],
            cwd=str(generador_dir)
        )
        if result.returncode != 0:
            print("❌ Error generando palabras")
            sys.exit(1)
    
    print(f"✅ Labels generados: {labels_realistas}\n")
    
    # PASO 1b: Crear imágenes desde las palabras
    print("\n" + "="*70)
    print("🖼️  PASO 1b/3: Creando imágenes (20K)")
    print("="*70)
    
    dataset_creator_dir = base_dir 
    dataset_dir = modelo_dir / "dataset"
    fonts_dir = base_dir / "fonts"
    
    # Verificar si ya existen imágenes
    if dataset_dir.exists() and list(dataset_dir.glob("*.png")):
        num_images = len(list(dataset_dir.glob("*.png")))
        print(f"📦 Dataset ya existe: {num_images} imágenes")
        response = input("   ¿Regenerar imágenes? [s/N]: ").lower()
        if response != 's':
            print("✅ Usando imágenes existentes")
        else:
            print("🔄 Regenerando imágenes...")
            result = subprocess.run([
                sys.executable, "dataset_creator_v2.py",
                "--archivo-palabras", str(labels_realistas),
                "--limpiar",
                "--output", str(dataset_dir),
                "--fonts", str(fonts_dir)
            ], cwd=str(dataset_creator_dir))
            if result.returncode != 0:
                print("❌ Error creando imágenes")
                sys.exit(1)
    else:
        print("🚀 Creando imágenes desde palabras realistas...")
        print(f"   Fuentes: {fonts_dir}")
        print(f"   Output: {dataset_dir}\n")
        
        result = subprocess.run([
            sys.executable, "dataset_creator_v2.py",
            "--archivo-palabras", str(labels_realistas),
            "--limpiar",
            "--output", str(dataset_dir),
            "--fonts", str(fonts_dir)
        ], cwd=str(dataset_creator_dir))
        
        if result.returncode != 0:
            print("❌ Error creando imágenes")
            sys.exit(1)
    
    # Verificar resultado
    num_images = len(list(dataset_dir.glob("*.png")))
    labels_file = dataset_dir / "labels.txt"
    
    if labels_file.exists():
        with open(labels_file, 'r', encoding='utf-8') as f:
            num_labels = len([l for l in f if l.strip()])
        print(f"\n✅ Dataset creado exitosamente:")
        print(f"   • Imágenes: {num_images:,}")
        print(f"   • Labels: {num_labels:,}")
    else:
        print(f"\n❌ Error: No se encontró labels.txt")
        sys.exit(1)
    
    # PASO 2: Configurar entrenamiento
    print("\n" + "="*70)
    print("⚙️  PASO 2/3: Configurando entrenamiento")
    print("="*70)
    
    config_path = base_dir / "config.yaml"
    
    config = {
        'dataset': {
            'labels_path': 'dataset_entrenamiento/dataset/labels.txt',
            'images_dir': 'dataset_entrenamiento/dataset',
            'fonts_dir': 'fonts'
        },
        'model': {
            'input_height': 32,
            'input_width': 256,
            'channels': 1,
            'vocab_chars': r'%+-.\/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÁáéíñóú',
            'include_blank': True
        },
        'training': {
            'batch_size': 96,
            'epochs': 100,  # Reducido para evitar overfitting
            'learning_rate': 0.001,  # LR estándar (no fine-tuning)
            'warmup_epochs': 3,
            'gradient_clip_norm': 1.0,
            'checkpoint_dir': 'dataset_entrenamiento/checkpoints',
            'logs_dir': 'dataset_entrenamiento/logs'
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ Configuración guardada en: {config_path}")
    print(f"\n📊 Configuración del entrenamiento:")
    print(f"   - Dataset: 20,500 imágenes")
    print(f"   - Épocas: 20 (reducido para evitar overfitting)")
    print(f"   - Learning Rate: 0.001 (estándar)")
    print(f"   - Batch Size: 96")
    print(f"   - Transfer Learning: ❌ NO (inicialización aleatoria)")
    print(f"   - Tiempo estimado: ~8-10 minutos")
    
    # PASO 3: Entrenar modelo usando train_20k.py
    print("\n" + "="*70)
    print("🏋️  PASO 3/3: Entrenando modelo desde cero")
    print("="*70)
    print("\n⚠️  NOTA: Este entrenamiento tomará aproximadamente 8-10 minutos")
    print("   El modelo se entrena desde cero (sin pesos pre-entrenados)")
    print("   Con 20 épocas para evitar overfitting\n")
    
    # Preparar el environment para subprocess
    env = os.environ.copy()
    
    # Ejecutar train.py (que usa config.yaml por defecto)
    train_script = base_dir / "train.py"
    
    print(f"🚀 Iniciando entrenamiento...")
    print(f"   Script: {train_script}")
    print(f"   Config: {config_path}")
    print(f"\n{'='*70}\n")
    
    result = subprocess.run(
        [sys.executable, str(train_script)],
        cwd=str(base_dir),
        env=env
    )
    
    if result.returncode != 0:
        print(f"\n❌ Error durante el entrenamiento")
        sys.exit(1)
    
    print("\n" + "🎉"*35)
    print("🎉" + " "*66 + "🎉")
    print("🎉  PIPELINE 20K LIMPIO COMPLETADO EXITOSAMENTE  🎉".center(70))
    print("🎉" + " "*66 + "🎉")
    print("🎉"*35 + "\n")
    
    print("📊 Resultados guardados en:")
    print(f"   - Checkpoints: {modelo_dir / 'checkpoints'}")
    print(f"   - Logs: {modelo_dir / 'logs'}")
    print(f"\n🧪 Siguiente paso: Evaluar generalización")
    print(f"   python test_generalization.py")
    
    # Verificar que se creó el modelo
    best_model = modelo_dir / "checkpoints" / "best_model.weights.h5"
    final_model = modelo_dir / "checkpoints" / "model_final.weights.h5"
    
    if best_model.exists():
        print(f"\n✅ Mejor modelo guardado: best_model.weights.h5")
    if final_model.exists():
        print(f"✅ Modelo final guardado: model_final.weights.h5")

if __name__ == '__main__':
    main()
