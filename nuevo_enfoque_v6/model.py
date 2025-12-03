import tensorflow as tf
from tensorflow.keras import layers
import numpy as np

def build_crnn(input_shape=(32,256,1), num_classes=75, dropout=0.2):
    inp = tf.keras.Input(shape=input_shape, name='image')
    x = inp
    # Conv block 1
    x = layers.Conv2D(32, 3, padding='same', activation='relu')(x)
    x = layers.MaxPool2D(pool_size=(2,2))(x)
    # Conv block 2
    x = layers.Conv2D(64, 3, padding='same', activation='relu')(x)
    x = layers.MaxPool2D(pool_size=(2,1))(x)
    # Conv block 3
    x = layers.Conv2D(128, 3, padding='same', activation='relu')(x)
    x = layers.MaxPool2D(pool_size=(2,1))(x)
    x = layers.Conv2D(256, 3, padding='same', activation='relu')(x)

    # collapse height dimension
    # x: [B, H, W, C] -> reshape to [B, W, H*C]
    # After 3 maxpools: 32 -> 16 -> 8 -> 4 (height)
    # Width: 256 -> 128 -> 64 -> 64
    x = layers.Permute((2,1,3))(x)  # [B, W, H, C]
    x = layers.Reshape((-1, 1024))(x)  # [B, W, H*C] where H*C = 4*256 = 1024

    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=dropout))(x)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=dropout))(x)

    logits = layers.Dense(num_classes, activation='linear', name='logits')(x)
    y_pred = layers.Activation('softmax', name='softmax')(logits)

    model = tf.keras.Model(inputs=inp, outputs=logits, name='crnn_logits')
    return model

class CTCPredModel(tf.keras.Model):
    def __init__(self, base_model, idx2char, char2idx, blank_index=0, **kwargs):
        super().__init__(**kwargs)
        self.base = base_model
        self.idx2char = idx2char
        self.char2idx = char2idx
        self.blank_index = blank_index

    def compile(self, optimizer, **kwargs):
        super().compile(**kwargs)
        self.optimizer = optimizer

    def train_step(self, data):
        images, labels = data
        batch_size = tf.shape(images)[0]
        with tf.GradientTape() as tape:
            logits = self.base(images, training=True)  # [B, T, C]
            logit_len = tf.fill([batch_size], tf.shape(logits)[1])
            # prepare labels as sparse tensor
            # labels is list of lists of ints
            indices = []
            values = []
            for b in range(len(labels)):
                for t, v in enumerate(labels[b]):
                    indices.append([b, t])
                    values.append(v)
            if len(indices) == 0:
                return {"loss": tf.constant(0.0)}
            indices = tf.convert_to_tensor(indices, dtype=tf.int64)
            values = tf.convert_to_tensor(values, dtype=tf.int32)
            dense_shape = tf.convert_to_tensor([batch_size, tf.reduce_max(indices[:,1])+1], dtype=tf.int64)
            sparse_labels = tf.SparseTensor(indices=indices, values=values, dense_shape=dense_shape)

            # CTC loss (uses logits, must be float32)
            log_probs = tf.nn.log_softmax(logits, axis=-1)
            ctc_loss = tf.nn.ctc_loss(labels=sparse_labels, logits=log_probs, label_length=None, logit_length=logit_len, logits_time_major=False, blank_index=self.blank_index)
            loss = tf.reduce_mean(ctc_loss)

        grads = tape.gradient(loss, self.base.trainable_variables)
        grads, _ = tf.clip_by_global_norm(grads, 1.0)
        self.optimizer.apply_gradients(zip(grads, self.base.trainable_variables))
        return {"loss": loss}
    
    def call(self, inputs, training=False):
        """Forward pass - retorna logits del modelo base"""
        return self.base(inputs, training=training)
    
    def test_step(self, data):
        """Validación sin gradientes"""
        images, labels = data
        batch_size = tf.shape(images)[0]
        
        # Forward pass
        logits = self.base(images, training=False)
        logit_len = tf.fill([batch_size], tf.shape(logits)[1])
        
        # Preparar labels como sparse tensor
        indices = []
        values = []
        for b in range(len(labels)):
            for t, v in enumerate(labels[b]):
                indices.append([b, t])
                values.append(v)
        
        if len(indices) == 0:
            return {"loss": tf.constant(0.0)}
        
        indices = tf.convert_to_tensor(indices, dtype=tf.int64)
        values = tf.convert_to_tensor(values, dtype=tf.int32)
        dense_shape = tf.convert_to_tensor([batch_size, tf.reduce_max(indices[:,1])+1], dtype=tf.int64)
        sparse_labels = tf.SparseTensor(indices=indices, values=values, dense_shape=dense_shape)
        
        # CTC loss
        log_probs = tf.nn.log_softmax(logits, axis=-1)
        ctc_loss = tf.nn.ctc_loss(
            labels=sparse_labels, 
            logits=log_probs, 
            label_length=None, 
            logit_length=logit_len, 
            logits_time_major=False, 
            blank_index=self.blank_index
        )
        loss = tf.reduce_mean(ctc_loss)
        
        return {"loss": loss}
