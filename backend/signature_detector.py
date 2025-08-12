# import cv2
# import numpy as np
# from typing import Tuple

# def detect_signature(image_path: str, region: Tuple[int, int, int, int] = None) -> bool:
#     """
#     Detects presence of a signature in the given image.
    
#     Parameters:
#         image_path (str): Path to the image file (from PDF page).
#         region (Tuple): Optional crop region (x, y, w, h) for faster detection.
    
#     Returns:
#         bool: True if signature-like contours are found, False otherwise.
#     """
#     image = cv2.imread(image_path)

#     if image is None:
#         return False

#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # Optional: crop to bottom-right region where signatures usually are
#     if region:
#         x, y, w, h = region
#         gray = gray[y:y+h, x:x+w]
#     else:
#         # Default: scan bottom 25% of the page
#         h = gray.shape[0]
#         gray = gray[int(h * 0.75):, :]

#     # Binarize
#     _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

#     # Find contours (potential ink marks)
#     contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     # Heuristic: large enough ink blobs, not just noise
#     valid_contours = [cnt for cnt in contours if 100 < cv2.contourArea(cnt) < 5000]

#     return len(valid_contours) > 0
