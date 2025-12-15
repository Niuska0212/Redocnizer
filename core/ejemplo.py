from crnn_inference import load_inference_model, decode_batch_predictions
from preprocessing import prepare_roi_for_ocr
import cv2

modelo, index_to_char, out_len = load_inference_model()
img = cv2.imread("7716380.jpg", cv2.IMREAD_GRAYSCALE)
roi = img[200:250, 100:300]  # alguna región con texto
X = prepare_roi_for_ocr(roi)
y_pred = modelo.predict(X)
print(decode_batch_predictions(y_pred, index_to_char, out_len))
