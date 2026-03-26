# services/ocr_service.py
from core.document_extractor import extract_data_from_image
from core.CRNN_inference import load_inference_model

class OCRService:
    def __init__(self):
        self.model, self.idx2char, self.seq_len = load_inference_model()

    def process_image(self, image_path, preview_dir):
        data, error = extract_data_from_image(
            image_path,
            #self.model,
            #self.idx2char,
            #self.seq_len,
            preview_dir
        )
        return data, error
    
