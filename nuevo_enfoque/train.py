import os
import sys
import yaml
import numpy as np
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from pathlib import Path

# ⚡ OPTIMIZACIONES DE GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        pass

# XLA compilation para acelerar operaciones
os.environ['TF_XLA_FLAGS'] = '--tf_xla_auto_jit=2'
os.environ['TF_CUDNN_USE_AUTOTUNE'] = '1'

# Añadir el directorio actual al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import build_vocab, ctc_greedy_decoder, labels_to_text
from dataloader import OCRDataset
from dataloader_optimized import OCRDatasetOptimized  # Nuevo dataloader
from model import build_crnn, CTCPredModel

def load_config(path='config.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main(config_path=None, pretrained_weights=None):
    if config_path is None:
        config_path = Path(__file__).parent / 'config.yaml'
    
    cfg = load_config(config_path)
    ds_cfg = cfg['dataset']
    mcfg = cfg['model']
    tcfg = cfg['training']
    
    # Ajustar rutas relativas al directorio padre del proyecto
    base_dir = Path(__file__).parent
    labels_path = str(base_dir / ds_cfg['labels_path'])
    images_dir = str(base_dir / ds_cfg['images_dir'])

    print("\n" + "="*70)
    print("🚀 ENTRENAMIENTO MODELO CRNN")
    print("="*70 + "\n")
    print(f"📂 Dataset: {labels_path}")
    print(f"📂 Imágenes: {images_dir}")
    print(f"🎯 Épocas: {tcfg['epochs']}")
    print(f"📦 Batch size: {tcfg['batch_size']}")
    print(f"📈 Learning rate: {tcfg['learning_rate']}")
    
    # Crear directorios
    checkpoint_dir = base_dir / tcfg['checkpoint_dir']
    logs_dir = base_dir / tcfg['logs_dir']
    checkpoint_dir.mkdir(exist_ok=True, parents=True)
    logs_dir.mkdir(exist_ok=True, parents=True)

    # Vocabulario
    idx2char, char2idx = build_vocab(mcfg['vocab_chars'], include_blank=mcfg.get('include_blank', True))
    num_classes = len(idx2char)
    print(f"\n✅ Vocabulario: {num_classes} caracteres\n")

    # Dataset OPTIMIZADO con caché en RAM + Split Train/Val 70/30
    use_optimized = True  # Flag para usar dataloader optimizado
    
    if use_optimized:
        print(f"⚡ Usando dataloader OPTIMIZADO (caché en RAM + prefetching)")
        print(f"📊 Split: 70% train / 30% validation\n")
        
        train_ds = OCRDatasetOptimized(
            labels_path, images_dir, char2idx, 
            img_w=mcfg['input_width'], 
            img_h=mcfg['input_height'], 
            batch_size=tcfg['batch_size'], 
            augment=True,
            cache_in_ram=True,
            num_workers=4,
            split='train',
            train_split=0.7
        )
        
        val_ds = OCRDatasetOptimized(
            labels_path, images_dir, char2idx, 
            img_w=mcfg['input_width'], 
            img_h=mcfg['input_height'], 
            batch_size=tcfg['batch_size'], 
            augment=False,  # Sin augmentation en validación
            cache_in_ram=True,
            num_workers=4,
            split='val',
            train_split=0.7
        )
    else:
        train_ds = OCRDataset(labels_path, images_dir, char2idx, 
                             img_w=mcfg['input_width'], img_h=mcfg['input_height'], 
                             batch_size=tcfg['batch_size'], augment=True,
                             split='train', train_split=0.7)
        val_ds = OCRDataset(labels_path, images_dir, char2idx, 
                           img_w=mcfg['input_width'], img_h=mcfg['input_height'], 
                           batch_size=tcfg['batch_size'], augment=False,
                           split='val', train_split=0.7)
    
    print(f"✅ Dataset TRAIN: {len(train_ds.samples)} muestras")
    print(f"✅ Dataset VAL: {len(val_ds.samples)} muestras")
    print(f"✅ Steps por época (train): {len(train_ds)}\n")

    # Modelo
    base = build_crnn(input_shape=(mcfg['input_height'], mcfg['input_width'], mcfg['channels']), 
                     num_classes=num_classes)
    
    # Cargar pesos preentrenados si están disponibles
    if pretrained_weights and Path(pretrained_weights).exists():
        print(f"⏳ Cargando pesos preentrenados desde: {pretrained_weights}")
        try:
            base.load_weights(pretrained_weights)
            print(f"✅ Transfer Learning: Pesos cargados exitosamente")
            print(f"💡 El modelo continuará aprendiendo desde el checkpoint previo\n")
        except Exception as e:
            print(f"⚠️  Error cargando pesos: {e}")
            print(f"💡 Se entrenará desde cero\n")
    elif pretrained_weights:
        print(f"⚠️  Archivo de pesos no encontrado: {pretrained_weights}")
        print(f"💡 Se entrenará desde cero\n")
    
    model = CTCPredModel(base, idx2char, char2idx, blank_index=0)
    
    # Optimizer con warmup
    initial_lr = tcfg['learning_rate']
    warmup_epochs = tcfg.get('warmup_epochs', 5)
    
    def lr_schedule(epoch):
        if epoch < warmup_epochs:
            return initial_lr * (epoch + 1) / warmup_epochs
        return initial_lr
    
    optimizer = Adam(learning_rate=initial_lr)
    model.compile(optimizer=optimizer)
    
    print(f"✅ Modelo compilado: {base.count_params():,} parámetros\n")

    # Preparar logging con métricas de validación (incluyendo CER)
    log_file = logs_dir / "training.log"
    with open(log_file, 'w') as f:
        f.write("epoch,loss,lr,val_accuracy,val_loss,val_cer\n")
    
    # Mejor modelo tracking
    best_val_accuracy = 0.0
    best_checkpoint_path = checkpoint_dir / "model_best.weights.h5"

    # Training loop manual (porque labels son listas)
    print("🔥 Iniciando entrenamiento...\n")
    print("="*70)
    
    gen = train_ds.generator()
    steps_per_epoch = len(train_ds)
    
    for epoch in range(tcfg['epochs']):
        print(f"\n{'='*70}")
        print(f"Época {epoch+1}/{tcfg['epochs']}")
        print(f"{'='*70}")
        
        # Update learning rate
        new_lr = lr_schedule(epoch)
        model.optimizer.learning_rate.assign(new_lr)
        print(f"📈 Learning Rate: {new_lr:.6f}")
        
        epoch_losses = []
        for step in range(steps_per_epoch):
            imgs, labels = next(gen)
            result = model.train_step((imgs, labels))
            loss = result['loss'].numpy()
            epoch_losses.append(loss)
            
            # Mostrar progreso cada step
            if (step + 1) % 5 == 0 or step == 0:
                avg_loss = np.mean(epoch_losses[-min(10, len(epoch_losses)):])
                progress = (step + 1) / steps_per_epoch * 100
                bar_length = 40
                filled = int(bar_length * (step + 1) / steps_per_epoch)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\r  [{bar}] {progress:5.1f}% | Step {step+1:3d}/{steps_per_epoch} | Loss: {avg_loss:7.4f}", end='', flush=True)
        
        epoch_loss = np.mean(epoch_losses)
        print(f"\n\n  📊 Loss promedio de la época: {epoch_loss:.4f}")
        print(f"  📉 Loss mínimo: {min(epoch_losses):.4f}")
        print(f"  📈 Loss máximo: {max(epoch_losses):.4f}")
        
        # VALIDACIÓN COMPLETA cada 5 épocas
        val_accuracy = 0.0
        val_loss = 0.0
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"\n  🔍 VALIDACIÓN EN DATASET VAL ({len(val_ds.samples)} muestras):")
            
            val_gen = val_ds.generator()
            val_steps = min(len(val_ds), 50)  # Evaluar hasta 50 batches
            
            total_correct = 0
            total_samples = 0
            val_losses = []
            total_char_errors = 0
            total_chars = 0
            
            # Función auxiliar para edit distance (CER)
            def edit_distance(a, b):
                la, lb = len(a), len(b)
                dp = [[0]*(lb+1) for _ in range(la+1)]
                for i in range(la+1): dp[i][0] = i
                for j in range(lb+1): dp[0][j] = j
                for i in range(1, la+1):
                    for j in range(1, lb+1):
                        cost = 0 if a[i-1]==b[j-1] else 1
                        dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
                return dp[la][lb]
            
            for val_step in range(val_steps):
                val_imgs, val_labels = next(val_gen)
                
                # Calcular loss
                result = model.test_step((val_imgs, val_labels))
                val_losses.append(result['loss'].numpy())
                
                # Calcular accuracy usando decodificador CTC (greedy) y colapso de repeticiones
                logits = base(val_imgs, training=False)
                # logits shape: [B, T, C]
                batch_size = logits.shape[0]
                input_lengths = [int(logits.shape[1])] * batch_size
                decoded = ctc_greedy_decoder(logits, input_lengths)  # dense array with -1 as padding

                for i in range(len(val_imgs)):
                    seq = [int(x) for x in decoded[i] if int(x) >= 0]
                    pred = labels_to_text(seq, idx2char)
                    true = ''.join([idx2char[int(k)] for k in val_labels[i] if int(k) != 0])
                    if pred == true:
                        total_correct += 1
                    # Calcular CER
                    ed = edit_distance(pred, true)
                    total_char_errors += ed
                    total_chars += len(true)
                    total_samples += 1
            
            val_accuracy = (total_correct / total_samples) * 100
            val_loss = np.mean(val_losses)
            val_cer = (total_char_errors / total_chars) * 100 if total_chars > 0 else 0.0
            
            print(f"     📊 VAL Loss: {val_loss:.4f}")
            print(f"     🎯 VAL Accuracy: {val_accuracy:.2f}% ({total_correct}/{total_samples})")
            print(f"     📝 VAL CER: {val_cer:.2f}%")
            
            # Mostrar ejemplos (usar CTC greedy decoder)
            print(f"\n     Ejemplos de predicciones:")
            val_gen = val_ds.generator()
            val_imgs, val_labels = next(val_gen)
            logits = base(val_imgs[:5], training=False)
            input_lengths = [int(logits.shape[1])] * logits.shape[0]
            decoded = ctc_greedy_decoder(logits, input_lengths)

            for i in range(5):
                seq = [int(x) for x in decoded[i] if int(x) >= 0]
                pred = labels_to_text(seq, idx2char)
                true = ''.join([idx2char[int(k)] for k in val_labels[i] if int(k) != 0])
                match = "✅" if pred == true else "❌"
                print(f"     {match} Real: '{true:15s}' | Pred: '{pred:15s}'")
        
        # Guardar log con métricas de validación
        with open(log_file, 'a') as f:
            f.write(f"{epoch+1},{epoch_loss:.6f},{new_lr:.8f},{val_accuracy:.2f},{val_loss:.6f},{val_cer:.2f}\n")
        
        # Guardar mejor checkpoint si Val Accuracy mejoró
        if (epoch + 1) % 5 == 0 or epoch == 0:
            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                base.save_weights(str(best_checkpoint_path))
                print(f"\n  🌟 MEJOR MODELO guardado: {best_checkpoint_path.name} (Val Acc: {val_accuracy:.2f}%)")
        
        # Guardar checkpoint cada 5 épocas
        if (epoch + 1) % 5 == 0:
            save_path = checkpoint_dir / f"model_epoch_{epoch+1:03d}.weights.h5"
            base.save_weights(str(save_path))
            print(f"\n  💾 Checkpoint guardado: {save_path.name}")
        
        # Detectar colapso (predicciones vacías) en dataset de validación
        if epoch > 10:
            val_gen = val_ds.generator()
            val_imgs, val_labels = next(val_gen)
            logits = base(val_imgs[:10], training=False)
            input_lengths = [int(logits.shape[1])] * logits.shape[0]
            decoded = ctc_greedy_decoder(logits, input_lengths)

            empty_count = 0
            for i in range(10):
                seq = [int(x) for x in decoded[i] if int(x) >= 0]
                pred = labels_to_text(seq, idx2char)
                if len(pred) == 0:
                    empty_count += 1
            
            if empty_count >= 8:
                print(f"\n  ⚠️  ALERTA: {empty_count}/10 predicciones vacías - Posible colapso")
                print(f"  💡 Considera detener y ajustar hiperparámetros")
            elif empty_count > 0 and (epoch + 1) % 5 == 0:
                print(f"  ⚡ Info: {empty_count}/10 predicciones vacías en validación")
    
    # Guardar modelo final
    final_path = checkpoint_dir / "model_final.weights.h5"
    base.save_weights(str(final_path))
    print(f"\n✅ Modelo final guardado: {final_path}")
    print("\n" + "="*70)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
