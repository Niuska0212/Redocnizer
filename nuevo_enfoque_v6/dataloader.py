import os
import random
import cv2
import numpy as np
from PIL import Image
import tensorflow as tf

from utils import text_to_labels

class OCRDataset:
    def __init__(self, labels_path, images_dir, char2idx, img_w=256, img_h=32, batch_size=32, 
                 augment=False, split='train', train_split=0.7, seed=42):
        self.labels_path = labels_path
        self.images_dir = images_dir
        self.char2idx = char2idx
        self.img_w = img_w
        self.img_h = img_h
        self.batch_size = batch_size
        self.augment = augment
        self.split = split

        all_samples = []
        with open(labels_path, 'r', encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if not line: continue
                parts = line.split(',')
                if len(parts) < 2: continue
                imgname, label = parts[0], ','.join(parts[1:])
                path = os.path.join(images_dir, imgname)
                all_samples.append((path, label))
        
        # Split train/val
        random.seed(seed)
        random.shuffle(all_samples)
        split_idx = int(len(all_samples) * train_split)
        
        if split == 'train':
            self.samples = all_samples[:split_idx]
        else:  # 'val'
            self.samples = all_samples[split_idx:]

    def __len__(self):
        return max(1, len(self.samples)//self.batch_size)

    def _read_image(self, path):
        img = Image.open(path).convert('L')
        img = img.resize((self.img_w, self.img_h), Image.BILINEAR)
        arr = np.array(img).astype(np.float32)/255.0
        arr = np.expand_dims(arr, axis=-1)
        return arr

    def _augment(self, img):
        # simple augmentations: small rotation and translation
        if not self.augment: return img
        # rotation
        ang = random.uniform(-3, 3)
        M = cv2.getRotationMatrix2D((self.img_w//2, self.img_h//2), ang, 1)
        arr = (img.squeeze()*255).astype(np.uint8)
        rotated = cv2.warpAffine(arr, M, (self.img_w, self.img_h), borderMode=cv2.BORDER_REPLICATE)
        rotated = rotated.astype(np.float32)/255.0
        return rotated[..., np.newaxis]

    def generator(self):
        while True:
            random.shuffle(self.samples)
            batch_imgs = []
            batch_labels = []
            for path, label in self.samples:
                try:
                    img = self._read_image(path)
                except Exception:
                    continue
                if self.augment:
                    img = self._augment(img)
                batch_imgs.append(img)
                batch_labels.append(text_to_labels(label, self.char2idx))
                if len(batch_imgs) >= self.batch_size:
                    # pad labels for CTC usage externally
                    imgs = np.stack(batch_imgs, axis=0)
                    yield imgs, batch_labels
                    batch_imgs = []
                    batch_labels = []
