import string
import tensorflow as tf
import numpy as np

def build_vocab(vocab_chars, include_blank=True):
    # chars string: characters in order
    chars = list(vocab_chars)
    if include_blank:
        # blank will be index 0 for CTC convenience
        idx2char = [''] + chars
        char2idx = {c: i+1 for i, c in enumerate(chars)}
        char2idx[''] = 0
    else:
        idx2char = chars
        char2idx = {c: i for i, c in enumerate(chars)}
    return idx2char, char2idx

def text_to_labels(text, char2idx):
    return [char2idx.get(c, 0) for c in text]

def labels_to_text(labels, idx2char):
    return ''.join(idx2char[i] for i in labels if i!=0)

def ctc_greedy_decoder(logits, input_lengths):
    # logits: [batch, time, classes]
    # return list of decoded strings per batch (greedy)
    preds = tf.nn.softmax(logits, axis=-1)
    decoded, _ = tf.nn.ctc_greedy_decoder(tf.transpose(tf.math.log(preds + 1e-8), [1,0,2]), sequence_length=input_lengths)
    dense = tf.sparse.to_dense(decoded[0], default_value=-1).numpy()
    return dense
