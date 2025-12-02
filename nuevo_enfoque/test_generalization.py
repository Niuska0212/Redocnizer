#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Generalización: Evalúa modelo en 20K muestras NUEVAS
============================================================
Este script verifica si el modelo:
- ✅ Generaliza bien (alta precisión en datos nuevos)
- ❌ Solo memorizó (baja precisión en datos nuevos)
"""

import yaml
import numpy as np
import tensorflow as tf
from pathlib import Path
import csv
import time

import sys
sys.path.append('nuevo_enfoque')

from utils import build_vocab, labels_to_text, ctc_greedy_decoder
from model import build_crnn, CTCPredModel
from dataloader import OCRDataset

def edit_distance(s1, s2):
    """Calcula distancia de Levenshtein"""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def main():
    print("="*80)
    print("🧪 TEST DE GENERALIZACIÓN DEL MODELO OCR")
    print("   Evaluando en 20,000 muestras COMPLETAMENTE NUEVAS")
    print("="*80)
    
    # Cargar configuración del modelo 20k
    config_path = Path(__file__).parent / 'config.yaml'  # Usa la ruta relativa al script
    cfg = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
    mcfg = cfg['model']
    
    # Cargar modelo
    model_dir = Path('dataset_entrenamiento')
    
    # Intentar cargar best_model si existe, sino usar model_final
    best_checkpoint = model_dir / 'checkpoints' / 'model_epoch_100.weights.h5'  # Actualizar nombre
    final_checkpoint = model_dir / 'checkpoints' / 'model_final.weights.h5'

    
    if best_checkpoint.exists():
        checkpoint = best_checkpoint
        print(f"📦 Usando: {checkpoint}")
        print(f"   (best_model.weights.h5)")
    elif final_checkpoint.exists():
        checkpoint = final_checkpoint
        print(f"📦 Usando: {checkpoint}")
        print(f"   (model_final.weights.h5)")
    else:
        print(f"❌ ERROR: No se encontró ningún checkpoint en {model_dir / 'checkpoints'}")
        return
    
    print(f"🔧 Cargando modelo...")
    
    idx2char, char2idx = build_vocab(mcfg['vocab_chars'], include_blank=True)
    num_classes = len(idx2char)
    
    base = build_crnn(
        input_shape=(mcfg['input_height'], mcfg['input_width'], mcfg['channels']),
        num_classes=num_classes
    )
    
    model = CTCPredModel(base, idx2char, char2idx, blank_index=0)
    base.load_weights(str(checkpoint))
    
    print("✅ Modelo cargado\n")
    
    # Cargar dataset de prueba
    test_dataset_dir = Path('./dataset_prueba_final')
    labels_file = test_dataset_dir / 'datos/labels.txt'
    images_dir = test_dataset_dir / 'datos'
    
    if not labels_file.exists():
        print(f"❌ ERROR: Dataset de prueba no encontrado en {test_dataset_dir}")
        print("   Ejecuta primero: python crear_dataset_test_20k.py")
        return
    
    print(f"📁 Dataset de prueba: {test_dataset_dir}")
    
    # Cargar usando OCRDataset
    print("📊 Cargando dataset de prueba...")
    dataset = OCRDataset(
        str(labels_file),
        str(images_dir),
        char2idx,
        img_w=mcfg['input_width'],
        img_h=mcfg['input_height'],
        batch_size=1,
        split='train',  # Usar todo el dataset (no hay split)
        train_split=1.0,
        seed=42
    )
    
    total_samples = len(dataset.samples)
    print(f"   Total de muestras: {total_samples}\n")
    
    # Configurar evaluación
    # Evaluar primero 500 muestras rápido para ver tendencia
    n_quick_test = 500
    print(f"🚀 FASE 1: Test rápido con {n_quick_test} muestras")
    print("-" * 80)
    
    correct = 0
    total_chars = 0
    total_char_errors = 0
    start_time = time.time()
    
    for i in range(n_quick_test):
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (n_quick_test - i - 1) / rate
            print(f"   Procesadas: {i+1}/{n_quick_test} ({rate:.1f} img/s, ETA: {eta:.0f}s)")
        
        img_path, true_label = dataset.samples[i]
        
        # Cargar y predecir
        img = dataset._read_image(img_path)
        images = np.expand_dims(img, axis=0)
        
        logits = base(images, training=False)
        input_lengths = tf.constant([logits.shape[1]], dtype=tf.int32)
        decoded = ctc_greedy_decoder(logits, input_lengths)
        pred_label = labels_to_text(decoded[0], idx2char)
        
        # Métricas
        is_correct = (pred_label == true_label)
        ed = edit_distance(pred_label, true_label)
        
        correct += int(is_correct)
        total_chars += len(true_label)
        total_char_errors += ed
        
        # Mostrar algunos ejemplos
        if i < 10 or (not is_correct and i < 50):
            match = "✅" if is_correct else "❌"
            print(f"      {match} '{true_label:20s}' → '{pred_label:20s}' (ED: {ed})")
    
    # Resultados fase 1
    quick_accuracy = (correct / n_quick_test) * 100
    quick_cer = (total_char_errors / total_chars) * 100 if total_chars > 0 else 0
    
    print("\n" + "="*80)
    print("📊 RESULTADOS FASE 1 (Muestra de 500)")
    print("="*80)
    print(f"🎯 Word Accuracy: {quick_accuracy:.2f}% ({correct}/{n_quick_test})")
    print(f"📝 CER: {quick_cer:.2f}%")
    print("="*80)
    
    # Decisión de continuar
    if quick_accuracy < 50:
        print("\n⚠️  ALERTA: Accuracy < 50% en test rápido")
        print("   El modelo parece estar memorizando y NO generalizando bien.")
        print("   ¿Continuar con evaluación completa? (esto tomará ~30 min)")
        response = input("   Continuar [s/N]: ").lower()
        if response != 's':
            print("\n❌ Evaluación cancelada")
            return
    
    # FASE 2: Evaluación completa
    print(f"\n🚀 FASE 2: Evaluación completa en {total_samples} muestras")
    print(f"   (Esto tomará aproximadamente {total_samples/150/60:.1f} minutos)")
    print("-" * 80)
    
    # Preparar CSV de resultados
    results_dir = Path('test_results')
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / 'generalization_test_results.csv'
    
    # Reiniciar contadores
    total_correct = 0
    total_samples_evaluated = 0
    total_chars = 0
    total_char_errors = 0
    errors_by_length = {}
    
    start_time = time.time()
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['image_path', 'true_label', 'predicted_label', 'correct', 'edit_distance', 'word_length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, (img_path, true_label) in enumerate(dataset.samples):
            if (i + 1) % 500 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                eta = (total_samples - i - 1) / rate
                current_acc = (total_correct / (i + 1)) * 100
                print(f"   Procesadas: {i+1}/{total_samples} ({rate:.1f} img/s) | Acc: {current_acc:.2f}% | ETA: {eta/60:.1f}min")
            
            # Cargar y predecir
            img = dataset._read_image(img_path)
            images = np.expand_dims(img, axis=0)
            
            logits = base(images, training=False)
            input_lengths = tf.constant([logits.shape[1]], dtype=tf.int32)
            decoded = ctc_greedy_decoder(logits, input_lengths)
            pred_label = labels_to_text(decoded[0], idx2char)
            
            # Métricas
            is_correct = (pred_label == true_label)
            ed = edit_distance(pred_label, true_label)
            word_len = len(true_label)
            
            total_correct += int(is_correct)
            total_samples_evaluated += 1
            total_chars += word_len
            total_char_errors += ed
            
            # Por longitud
            if word_len not in errors_by_length:
                errors_by_length[word_len] = [0, 0]
            errors_by_length[word_len][0] += int(is_correct)
            errors_by_length[word_len][1] += 1
            
            # Guardar en CSV
            writer.writerow({
                'image_path': str(img_path),
                'true_label': true_label,
                'predicted_label': pred_label,
                'correct': is_correct,
                'edit_distance': ed,
                'word_length': word_len
            })
    
    # RESULTADOS FINALES
    final_accuracy = (total_correct / total_samples_evaluated) * 100
    final_cer = (total_char_errors / total_chars) * 100
    elapsed_total = time.time() - start_time
    
    print("\n" + "="*80)
    print("🏆 RESULTADOS FINALES - TEST DE GENERALIZACIÓN")
    print("="*80)
    print(f"📊 Muestras evaluadas:    {total_samples_evaluated}")
    print(f"✅ Predicciones correctas: {total_correct}")
    print(f"❌ Predicciones erróneas:  {total_samples_evaluated - total_correct}")
    print(f"\n🎯 Word Accuracy:  {final_accuracy:.2f}%")
    print(f"📝 CER:            {final_cer:.2f}%")
    print(f"⏱️  Tiempo total:   {elapsed_total/60:.1f} minutos")
    print(f"⚡ Velocidad:       {total_samples_evaluated/elapsed_total:.1f} imágenes/segundo")
    print("="*80)
    
    # Interpretación
    print("\n📈 INTERPRETACIÓN DE RESULTADOS:")
    print("-" * 80)
    if final_accuracy >= 95:
        print("🎉 EXCELENTE - El modelo generaliza muy bien!")
        print("   El modelo NO memorizó, aprendió patrones reales de OCR.")
    elif final_accuracy >= 85:
        print("✅ BUENO - El modelo generaliza bien")
        print("   Hay espacio para mejorar, pero el aprendizaje es sólido.")
    elif final_accuracy >= 70:
        print("⚠️  REGULAR - Generalización limitada")
        print("   El modelo puede estar sobre-ajustado al dataset de entrenamiento.")
    else:
        print("❌ MALO - El modelo NO generaliza")
        print("   El modelo memorizó el dataset y no aprendió patrones generales.")
        print("   Recomendación: Aumentar variedad del dataset, data augmentation.")
    print("="*80)
    
    # Accuracy por longitud
    print("\n📏 Accuracy por longitud de palabra:")
    summary_path = results_dir / 'accuracy_by_length.csv'
    with open(summary_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['word_length', 'correct', 'total', 'accuracy'])
        
        for length in sorted(errors_by_length.keys()):
            correct, total = errors_by_length[length]
            acc = (correct / total) * 100
            print(f"   Longitud {length:2d}: {acc:6.2f}% ({correct}/{total})")
            writer.writerow([length, correct, total, f"{acc:.2f}"])
    
    print(f"\n✅ Resultados guardados en:")
    print(f"   - {csv_path}")
    print(f"   - {summary_path}")
    print("\n🏁 Evaluación completada!")
    print("="*80)

if __name__ == '__main__':
    main()
