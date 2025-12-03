#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Generalización y Cercanía: Evalúa similitud y confusiones
=================================================================
Este script extiende test_generalization.py para:
- Calcular similitud visual (SequenceMatcher)
- Detectar "Near Misses" (errores cercanos)
- Analizar matriz de confusión de caracteres (ej. l vs I, 0 vs O)
"""

import yaml
import numpy as np
import tensorflow as tf
from pathlib import Path
import csv
import time
import difflib
from collections import Counter

import sys
sys.path.append('nuevo_enfoque')

from utils import build_vocab, labels_to_text, ctc_greedy_decoder
from model import build_crnn, CTCPredModel
from dataloader_optimized import OCRDatasetOptimized

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

def get_similarity(s1, s2):
    """Calcula ratio de similitud (0.0 a 1.0)"""
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def analyze_confusions(true_text, pred_text, confusion_counter):
    """
    Analiza diferencias y actualiza contador de confusiones.
    Usa difflib para alinear secuencias.
    """
    matcher = difflib.SequenceMatcher(None, true_text, pred_text)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # Caso de sustitución (ej. 'l' por 'I')
            t_segment = true_text[i1:i2]
            p_segment = pred_text[j1:j2]
            # Si son de igual longitud, asumimos correspondencia 1 a 1
            if len(t_segment) == len(p_segment):
                for t_char, p_char in zip(t_segment, p_segment):
                    confusion_counter[(t_char, p_char)] += 1
            else:
                # Si no, lo registramos como bloque
                confusion_counter[(t_segment, p_segment)] += 1

def main():
    print("="*80)
    print(" TEST DE GENERALIZACIÓN Y CERCANÍA")
    print("   Analizando similitud y confusiones comunes (l/I/1, O/0, etc.)")
    print("="*80)
    
    # Cargar configuración
    config_path = Path(__file__).parent / 'config.yaml'
    cfg = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
    mcfg = cfg['model']
    tcfg = cfg['training']
    
    # Cargar modelo
    checkpoint_dir = Path(tcfg['checkpoint_dir'])
    best_checkpoint = checkpoint_dir / 'model_best.weights.h5'
    final_checkpoint = checkpoint_dir / 'model_final.weights.h5'

    if best_checkpoint.exists():
        checkpoint = best_checkpoint
        print(f" Usando: {checkpoint}")
    elif final_checkpoint.exists():
        checkpoint = final_checkpoint
        print(f" Usando: {checkpoint}")
    else:
        checkpoints = sorted(list(checkpoint_dir.glob("model_epoch_*.weights.h5")))
        if checkpoints:
            checkpoint = checkpoints[-1]
            print(f" Usando último checkpoint: {checkpoint}")
        else:
            print(f" ERROR: No se encontró checkpoint")
            return
    
    print(f" Cargando modelo...")
    idx2char, char2idx = build_vocab(mcfg['vocab_chars'], include_blank=True)
    num_classes = len(idx2char)
    
    base = build_crnn(
        input_shape=(mcfg['input_height'], mcfg['input_width'], mcfg['channels']),
        num_classes=num_classes
    )
    
    model = CTCPredModel(base, idx2char, char2idx, blank_index=0)
    base.load_weights(str(checkpoint))
    print(" Modelo cargado\n")
    
    # Configurar dataset
    test_dataset_dir = Path('./dataset_prueba_final')
    images_dir = test_dataset_dir / 'datos'
    labels_file = images_dir / 'labels.txt'
    
    if not labels_file.exists():
        print(f" Error: No existe {labels_file}. Ejecuta primero test_generalization.py para generar datos.")
        return

    print(" Cargando dataset (Smart Padding)...")
    dataset = OCRDatasetOptimized(
        str(labels_file),
        str(images_dir),
        char2idx,
        img_w=mcfg['input_width'],
        img_h=mcfg['input_height'],
        batch_size=1,
        split='train',
        train_split=1.0,
        seed=42,
        augment=False,
        cache_in_ram=True
    )
    
    total_samples = len(dataset.samples)
    print(f"   Total de muestras: {total_samples}\n")
    
    # Métricas extendidas
    total_correct = 0
    total_samples_evaluated = 0
    total_similarity = 0.0
    confusion_counter = Counter()
    near_misses = [] # (true, pred, similarity)
    
    # CSV
    results_dir = Path('test_results')
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / 'cercania_test_results.csv'
    
    print(f" Iniciando evaluación de cercanía...")
    start_time = time.time()
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['image_path', 'true_label', 'predicted_label', 'correct', 'similarity', 'edit_distance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, (img_path, true_label) in enumerate(dataset.samples):
            if (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                eta = (total_samples - i - 1) / rate
                print(f"   Procesadas: {i+1}/{total_samples} ({rate:.1f} img/s) | ETA: {eta/60:.1f}min")
            
            # Predicción
            img = dataset._get_image(img_path)
            images = np.expand_dims(img, axis=0)
            logits = base(images, training=False)
            input_lengths = tf.constant([logits.shape[1]], dtype=tf.int32)
            decoded = ctc_greedy_decoder(logits, input_lengths)
            pred_label = labels_to_text(decoded[0], idx2char)
            
            # Métricas
            is_correct = (pred_label == true_label)
            sim = get_similarity(true_label, pred_label)
            ed = edit_distance(pred_label, true_label)
            
            total_correct += int(is_correct)
            total_similarity += sim
            total_samples_evaluated += 1
            
            if not is_correct:
                analyze_confusions(true_label, pred_label, confusion_counter)
                if sim >= 0.8: # Umbral de "Near Miss"
                    near_misses.append((true_label, pred_label, sim))
            
            writer.writerow({
                'image_path': str(img_path),
                'true_label': true_label,
                'predicted_label': pred_label,
                'correct': is_correct,
                'similarity': f"{sim:.4f}",
                'edit_distance': ed
            })

    # RESULTADOS
    final_accuracy = (total_correct / total_samples_evaluated) * 100
    avg_similarity = (total_similarity / total_samples_evaluated) * 100
    
    print("\n" + "="*80)
    print(" RESULTADOS DE CERCANÍA")
    print("="*80)
    print(f" Word Accuracy:      {final_accuracy:.2f}%")
    print(f" Similitud Promedio: {avg_similarity:.2f}%")
    print("-" * 80)
    
    print("\n TOP 10 CONFUSIONES DE CARACTERES:")
    print(" (Real -> Predicho : Cantidad)")
    # Filtrar solo confusiones de 1 caracter para el top
    char_confusions = {k: v for k, v in confusion_counter.items() if len(k[0]) == 1 and len(k[1]) == 1}
    for (true_c, pred_c), count in sorted(char_confusions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   '{true_c}' -> '{pred_c}' : {count} veces")
        
    print("\n ANÁLISIS DE CASOS DIFÍCILES:")
    specific_pairs = [('l', 'I'), ('I', 'l'), ('1', 'I'), ('I', '1'), ('0', 'O'), ('O', '0')]
    for t, p in specific_pairs:
        count = confusion_counter[(t, p)]
        if count > 0:
            print(f"   Confusión '{t}' -> '{p}': {count} veces")
            
    print("\n EJEMPLOS DE 'NEAR MISSES' (Similitud > 80%):")
    for t, p, s in near_misses[:10]:
        print(f"   '{t}' vs '{p}' (Sim: {s:.2f})")
        
    print("\n" + "="*80)
    print(f" Resultados guardados en {csv_path}")

if __name__ == '__main__':
    main()
