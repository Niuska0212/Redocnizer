```
# Visualización de la Arquitectura - Modelo OCR Aether

## Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ENTRADA: IMAGEN DE TEXTO                        │
│                              (512 x 32 píxeles)                         │
│                                                                         │
│  ╔═══════════════════════════════════════════════════════════════════╗ │
│  ║  H  O  L  A     M  U  N  D  O                                     ║ │
│  ╚═══════════════════════════════════════════════════════════════════╝ │
│                          Imagen en escala de grises                     │
│                          Normalizada [0, 1]                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PREPROCESAMIENTO (Smart Padding)                   │
│  1. Resize Proporcional: Altura fija 32px, Ancho variable (new_w)       │
│  2. Canvas: Tensor 512x32 (Relleno de ceros/blanco)                     │
│  3. Centrado: Pegar imagen en (512 - new_w) // 2                        │
│  4. Normalización: pixels / 255.0                                       │
│  • Output Shape: (batch, 32, 512, 1)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLOQUE CONVOLUCIONAL 1                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Conv2D(32 filtros, kernel 3x3, ReLU)                          │    │
│  │  Input:  (batch, 32, 512, 1)                                   │    │
│  │  Output: (batch, 32, 512, 32)                                  │    │
│  │                                                                  │    │
│  │  MaxPool2D(2x2)                                                 │    │
│  │  Output: (batch, 16, 256, 32)                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Función: Detecta bordes y características básicas                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLOQUE CONVOLUCIONAL 2                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Conv2D(64 filtros, kernel 3x3, ReLU)                          │    │
│  │  Input:  (batch, 16, 256, 32)                                  │    │
│  │  Output: (batch, 16, 256, 64)                                  │    │
│  │                                                                  │    │
│  │  MaxPool2D(2x1)                                                 │    │
│  │  Output: (batch, 8, 256, 64)                                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Función: Detecta patrones más complejos (curvas, formas)              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLOQUE CONVOLUCIONAL 3                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Conv2D(128 filtros, kernel 3x3, ReLU)                         │    │
│  │  Input:  (batch, 8, 256, 64)                                   │    │
│  │  Output: (batch, 8, 256, 128)                                  │    │
│  │                                                                  │    │
│  │  MaxPool2D(2x1)  ️ Solo reduce altura                         │    │
│  │  Output: (batch, 4, 256, 128)                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Función: Features de alto nivel (partes de caracteres)                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BLOQUE CONVOLUCIONAL 4                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Conv2D(256 filtros, kernel 3x3, ReLU)                         │    │
│  │  Input:  (batch, 4, 256, 128)                                  │    │
│  │  Output: (batch, 4, 256, 256)                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Función: Representación rica de características                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESHAPE A SECUENCIA                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Permute(2, 1, 3)  [B, W, H, C]                                │    │
│  │  De: (batch, 4, 256, 256)                                      │    │
│  │  A:  (batch, 256, 4, 256)                                      │    │
│  │                                                                  │    │
│  │  Reshape(-1, 1024)  [B, W, H*C]                                │    │
│  │  Output: (batch, 256, 1024)                                    │    │
│  │          └─────┘  └─────┘                                      │    │
│  │          256 pasos 1024 features                               │    │
│  │          temporales por paso                                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Cada "paso temporal" representa ~2 píxeles de ancho                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               LSTM BIDIRECCIONAL CAPA 1                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Forward LSTM(128)  ─────────────────────────────────────►      │    │
│  │  H → HO → HOL → HOLA (contexto pasado)                         │    │
│  │                                                                  │    │
│  │  Backward LSTM(128) ◄─────────────────────────────────────     │    │
│  │  A ← LA ← OLA ← HOLA (contexto futuro)                         │    │
│  │                                                                  │    │
│  │  Concatenación: 128 + 128 = 256 features                       │    │
│  │  Output: (batch, 256, 256)                                     │    │
│  │  Dropout: 20%                                                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Función: Captura contexto bidireccional                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               LSTM BIDIRECCIONAL CAPA 2                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Input:  (batch, 256, 256)                                     │    │
│  │  Output: (batch, 256, 256)                                     │    │
│  │  Dropout: 20%                                                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  Función: Refina contexto, modela dependencias a largo plazo            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CAPA DE SALIDA                                      │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Dense(75, activation='linear')                                 │    │
│  │  Input:  (batch, 256, 256)                                     │    │
│  │  Output: (batch, 256, 75)  ️ Logits                           │    │
│  │          └─────┘  └───┘                                        │    │
│  │          256 pasos 75 clases                                   │    │
│  │          temporales (alphabet)                                  │    │
│  │                                                                  │    │
│  │  Softmax: Convierte logits a probabilidades                     │    │
│  │  Output: (batch, 256, 75)  ️ Probabilidades                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CTC DECODER (Greedy)                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Para cada time step (256 posiciones):                         │    │
│  │    1. Elegir clase con mayor probabilidad                       │    │
│  │    2. Colapsar repeticiones consecutivas                        │    │
│  │    3. Eliminar blanks (ε)                                       │    │
│  │                                                                  │    │
│  │  Ejemplo:                                                        │    │
│  │  Probabilidades: [H H ε O O ε L L L ε A ε ε ε]                │    │
│  │                   ↓                                             │    │
│  │  Colapsar:      [H ε O ε L ε A ε]                              │    │
│  │                   ↓                                             │    │
│  │  Eliminar ε:    [H O L A]                                       │    │
│  │                   ↓                                             │    │
│  │  Resultado:     "HOLA"                                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SALIDA: TEXTO                                   │
│                                                                         │
│                           "HOLA MUNDO"                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Reducción de Dimensiones

```
ALTURA (H):
32 px  →  16 px  →  8 px  →  4 px  →  4 px
       (Pool)    (Pool)   (Pool)    (Sin pool)

ANCHO (W):
256 px  →  128 px  →  64 px  →  64 px  →  64 px
        (Pool)     (Pool)    (Sin pool) (Sin pool)

CANALES (C):
1  →  32  →  64  →  128  →  256
   (Conv) (Conv) (Conv)  (Conv)
```

**Resultado final antes de LSTM**:
- **64 time steps** (posiciones horizontales)
- **1024 features** por time step (4 × 256)
- Cada time step representa ~4 píxeles de ancho (256/64)

---

## Flujo de CTC Loss

```
┌──────────────────────────────────────────────────────────────────┐
│                        ENTRENAMIENTO                             │
└──────────────────────────────────────────────────────────────────┘

Input Imagen: "HOLA"
     │
     ▼
┌────────────────────────────────────────┐
│  MODELO (Forward Pass)                 │
│  Logits: (batch, 64, 75)              │
│                                        │
│  Para cada time step (64):             │
│  [0.1, 0.05, ..., 0.8, ..., 0.01]    │
│         ▲                  ▲           │
│       blank               'H'          │
└────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Log Softmax                           │
│  log_probs = log_softmax(logits)      │
└────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Preparar Labels                       │
│  "HOLA" → [8, 15, 12, 1]              │
│  (índices en vocabulario)              │
│                                        │
│  Sparse Tensor:                        │
│  indices: [[0,0], [0,1], [0,2], [0,3]]│
│  values:  [8, 15, 12, 1]              │
└────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│  CTC LOSS                                                  │
│                                                            │
│  Calcula: -log P(label | input)                           │
│                                                            │
│  Donde P(label | input) = Σ P(alineamiento | input)       │
│                           sobre TODAS las alineaciones     │
│                           válidas                          │
│                                                            │
│  Ejemplo de alineaciones válidas para "HOLA":              │
│  1. [H, H, ε, O, O, ε, L, L, L, ε, A, ε, ε, ε]          │
│  2. [ε, H, ε, O, ε, L, ε, A, ε, ε, ε, ε, ε, ε]          │
│  3. [H, ε, ε, O, ε, ε, L, ε, ε, ε, A, ε, ε, ε]          │
│  ... (millones de alineaciones posibles)                   │
│                                                            │
│  CTC usa Forward-Backward Algorithm                        │
│  (Programación dinámica eficiente)                         │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  BACKPROPAGATION                       │
│                                        │
│  Gradientes: ∂Loss/∂Weights            │
│                                        │
│  Gradient Clipping: ||grad|| ≤ 1.0    │
└────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  OPTIMIZER (Adam)                      │
│                                        │
│  Actualiza pesos:                      │
│  W_new = W_old - lr * gradients        │
└────────────────────────────────────────┘
```

---

## Ejemplo Detallado: Predicción de "HOLA"

### Paso 1: CNN Feature Extraction

```
Imagen "HOLA" (256x32):
┌─────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  32 px
│ ░░▓▓░░▓▓░░▓▓▓▓░░▓░░░░░▓▓▓░░░░░░░░░░░░░░░ │
│ ░░▓▓░░▓▓░░▓▓░░░░▓░░░░▓░░▓░░░░░░░░░░░░░░░ │
│ ░░▓▓▓▓▓▓░░▓▓░░░░▓░░░░▓░░▓░░░░░░░░░░░░░░░ │
│ ░░▓▓░░▓▓░░▓▓░░░░▓░░░░▓░░▓░░░░░░░░░░░░░░░ │
│ ░░▓▓░░▓▓░░▓▓▓▓░░▓▓▓▓░░▓▓▓░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────────────────┘
        256 px

     ↓ CNN (4 bloques convolutionales)

Feature Maps (4x64x256):
┌─────────────────────────────────────────────┐
│ Canal 0:  [valores de features...]         │  4 px
│ Canal 1:  [valores de features...]         │
│ ...                                         │
│ Canal 255: [valores de features...]        │
└─────────────────────────────────────────────┘
        64 posiciones horizontales

Cada posición horizontal captura ~4 píxeles de la imagen original.
```

### Paso 2: Reshape a Secuencia

```
Feature Maps (4, 64, 256)
     ↓ Permute + Reshape
Secuencia (64, 1024)

Interpretación:
Posición 0:  [features de píxeles 0-3]   → probablemente background
Posición 5:  [features de píxeles 16-19]  → borde izquierdo de 'H'
Posición 10: [features de píxeles 36-39]  → centro de 'H'
Posición 15: [features de píxeles 56-59]  → borde derecho de 'H', inicio 'O'
Posición 25: [features de píxeles 96-99]  → centro de 'O'
...
```

### Paso 3: LSTM Procesa Secuencia

```
Forward LSTM (izquierda → derecha):
Posición 0:  [background]         → estado: "nada visto aún"
Posición 10: [centro de 'H']      → estado: "veo una H"
Posición 15: [transición H→O]     → estado: "H completa, empieza O"
Posición 25: [centro de 'O']      → estado: "HO visto"
...

Backward LSTM (derecha ← izquierda):
Posición 63: [background]         → estado: "nada después"
Posición 50: [centro de 'A']      → estado: "veo una A"
Posición 40: [transición L→A]     → estado: "A después, antes L"
...

Combinación:
Cada posición tiene contexto de:
- Lo que vino antes (Forward)
- Lo que viene después (Backward)
→ Mejor predicción de cada carácter
```

### Paso 4: Output Layer

```
Dense Layer (64, 75):
Para cada time step, probabilidades sobre 75 clases:

Time Step 0:  [blank: 0.95, 'H': 0.02, ...]  → Probablemente blank
Time Step 5:  [blank: 0.10, 'H': 0.80, ...]  → Probablemente 'H'
Time Step 10: [blank: 0.05, 'H': 0.85, ...]  → Probablemente 'H'
Time Step 15: [blank: 0.70, 'H': 0.10, ...] → Blank (transición)
Time Step 20: [blank: 0.05, 'O': 0.88, ...]  → Probablemente 'O'
Time Step 25: [blank: 0.03, 'O': 0.90, ...]  → Probablemente 'O'
Time Step 30: [blank: 0.75, 'O': 0.08, ...]  → Blank (transición)
Time Step 35: [blank: 0.04, 'L': 0.87, ...]  → Probablemente 'L'
Time Step 40: [blank: 0.02, 'L': 0.92, ...]  → Probablemente 'L'
Time Step 45: [blank: 0.08, 'L': 0.85, ...]  → Probablemente 'L'
Time Step 50: [blank: 0.80, 'L': 0.05, ...]  → Blank (transición)
Time Step 55: [blank: 0.06, 'A': 0.86, ...]  → Probablemente 'A'
Time Step 60: [blank: 0.03, 'A': 0.90, ...]  → Probablemente 'A'
Time Step 63: [blank: 0.95, 'A': 0.02, ...]  → Blank (final)
```

### Paso 5: CTC Greedy Decoder

```
Predicciones (argmax):
[ε, ε, ε, ε, ε, H, H, H, H, H, ε, ε, ε, ε, ε, 
 O, O, O, O, ε, ε, ε, ε, ε, ε, L, L, L, L, L,
 ε, ε, ε, ε, ε, A, A, A, ε, ε, ε, ε, ε, ...]

Colapsar repeticiones:
[ε, H, ε, O, ε, L, ε, A, ε]

Eliminar blanks:
[H, O, L, A]

Resultado final:
"HOLA" 
```

---

## Comparación: Con vs Sin LSTM

### Sin LSTM (Solo CNN + Dense)

```
┌─────────────────────────────────────────────┐
│  Imagen "HOLA"                              │
│                                             │
│  ░░▓▓░░▓▓░░▓▓▓▓░░▓░░░░░▓▓▓░                │
└─────────────────────────────────────────────┘
     ↓ CNN
┌─────────────────────────────────────────────┐
│  Features (64 posiciones)                   │
└─────────────────────────────────────────────┘
     ↓ Dense (sin contexto)
┌─────────────────────────────────────────────┐
│  Predicciones:                              │
│  Posición 10: 'H' o 'I' o 'l'?          │
│  (sin contexto, difícil distinguir)         │
└─────────────────────────────────────────────┘
```

### Con LSTM (Arquitectura actual)

```
┌─────────────────────────────────────────────┐
│  Imagen "HOLA"                              │
└─────────────────────────────────────────────┘
     ↓ CNN
┌─────────────────────────────────────────────┐
│  Features (64 posiciones)                   │
└─────────────────────────────────────────────┘
     ↓ LSTM (con contexto bidireccional)
┌─────────────────────────────────────────────┐
│  Predicciones:                              │
│  Posición 10: 'H'                         │
│  (sabe que viene O después, no I ni l)      │
│  (sabe que no vino nada antes)              │
└─────────────────────────────────────────────┘
```

**Ventaja del LSTM**: Captura contexto secuencial, mejora precisión.

---

## Resumen de Shapes

| Capa | Input Shape | Output Shape | Parámetros |
|------|-------------|--------------|------------|
| Input | - | (B, 32, 256, 1) | 0 |
| Conv2D + Pool 1 | (B, 32, 256, 1) | (B, 16, 128, 32) | 320 |
| Conv2D + Pool 2 | (B, 16, 128, 32) | (B, 8, 64, 64) | 18,496 |
| Conv2D + Pool 3 | (B, 8, 64, 64) | (B, 4, 64, 128) | 73,856 |
| Conv2D 4 | (B, 4, 64, 128) | (B, 4, 64, 256) | 295,168 |
| Reshape | (B, 4, 64, 256) | (B, 64, 1024) | 0 |
| BiLSTM 1 | (B, 64, 1024) | (B, 64, 256) | 1,182,720 |
| BiLSTM 2 | (B, 64, 256) | (B, 64, 256) | 394,240 |
| Dense | (B, 64, 256) | (B, 64, 75) | 19,275 |
| **TOTAL** | | | **~2M parámetros** |

```
B = batch size (típicamente 96)
Memoria GPU: ~3 GB durante entrenamiento
```

---

**Autor**: Aether  
**Fecha**: Noviembre 2025  
**Versión**: 1.0
