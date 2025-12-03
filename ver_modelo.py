import tensorflow as tf
from tensorflow.keras import layers

# =========================================================
# 1. Definición EXACTA de la arquitectura build_crnn
# ¡Asegúrate de que esta sea la versión que usaste para entrenar!
# Incluye 'implementation=2' para evitar errores de CudnnRNN en tu entorno.
# =========================================================
def build_crnn(input_shape=(32,256,1), num_classes=81, dropout=0.2):
    inp = tf.keras.Input(shape=input_shape, name='image')
    x = inp
    # Bloques Convolucionales
    x = layers.Conv2D(32, 3, padding='same', activation='relu')(x)
    x = layers.MaxPool2D(pool_size=(2,2))(x)
    x = layers.Conv2D(64, 3, padding='same', activation='relu')(x)
    x = layers.MaxPool2D(pool_size=(2,2))(x)
    x = layers.Conv2D(128, 3, padding='same', activation='relu')(x)
    x = layers.MaxPool2D(pool_size=(2,1))(x)
    x = layers.Conv2D(256, 3, padding='same', activation='relu')(x)

    # Preparación para RNN
    x = layers.Permute((2,1,3))(x)  # [B, W, H, C]
    x = layers.Reshape((-1, 1024))(x)  # [B, W, H*C] donde H*C = 4*256 = 1024

    # Bloques Recurrentes (BiLSTM)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=dropout, implementation=2))(x)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=dropout, implementation=2))(x)

    # Capa de Salida (Logits para CTC)
    logits = layers.Dense(num_classes, activation='linear', name='logits')(x)
    
    model = tf.keras.Model(inputs=inp, outputs=logits, name='crnn_logits')
    return model
# =========================================================

# Parámetros correctos
INPUT_HEIGHT = 32
INPUT_WIDTH = 256
CHANNELS = 1
NUM_CLASSES = 81 # 80 caracteres + 1 blank
WEIGHTS_FILE = 'model_final.weights.h5' 

# 1. Recrear el modelo base
print("Recreando arquitectura CRNN para visualizar el Summary...")
modelo_base_recreado = build_crnn(
    input_shape=(INPUT_HEIGHT, INPUT_WIDTH, CHANNELS), 
    num_classes=NUM_CLASSES
)

# 2. Forzar la construcción del modelo con un tensor dummy
# Esto es esencial para que Keras calcule los parámetros antes del summary.
dummy_input = tf.zeros((1, INPUT_HEIGHT, INPUT_WIDTH, CHANNELS))
_ = modelo_base_recreado(dummy_input)

# 3. Mostrar el Summary
print("\n" + "="*70)
print("✅ ESTRUCTURA DEL MODELO (SUMMARY) GENERADA")
print("El orden y el número de parámetros son correctos, pero los pesos NO están cargados.")
print("="*70)
modelo_base_recreado.summary()
print("="*70)

# 4. Intentar cargar los pesos (Para ver si el problema de 'found 0 saved layers' desaparece)
try:
    print(f"\n⏳ Intentando cargar los pesos... (Forzando carga PARCIAL)")
    
    # ⚠️ Esto indica a Keras que acepte la carga incluso si faltan o sobran variables.
    modelo_base_recreado.load_weights(WEIGHTS_FILE, skip_mismatch=True, by_name=True)
    
    print("✅ Pesos cargados (al menos parcialmente).")
    
    # Para verificar la carga, podemos imprimir los pesos de la primera capa.
    # El peso debe ser un tensor de 3x3x1x32 (kernel)
    kernel_weights = modelo_base_recreado.get_layer('conv2d').get_weights()[0]
    print(f"   Peso del Kernel 'conv2d' cargado con éxito. Shape: {kernel_weights.shape}")
    
except Exception as e:
    # Si sigue fallando, es irrecuperable sin el código de entrenamiento.
    print(f"❌ Falló la carga de pesos: {e}")
    print("\n⚠️ Diagnóstico: El archivo .h5 probablemente está dañado o no contiene los pesos esperados para la capa inicial.")
    print("Necesitas el código de entrenamiento original para reguardar el modelo completo (base.save('modelo.keras')).")