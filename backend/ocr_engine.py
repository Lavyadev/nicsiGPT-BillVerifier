import tempfile
from pdf2image import convert_from_path
from pytesseract import image_to_string
from PIL import Image
from typing import List, Dict
import logging
import numpy as np
import cv2

# ─────────────────────── Preprocessing + OCR ───────────────────────

def extract_text_from_image(pil_image: Image.Image, page_num: int = None) -> str:
    """
    Preprocesses image (grayscale + binarization) and extracts text using Tesseract.
    """
    try:
        # Convert to grayscale OpenCV format
        gray = np.array(pil_image.convert("L"))

        # Adaptive thresholding (improves OCR on scans)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Convert back to PIL for Tesseract
        processed_img = Image.fromarray(binary)

        # OCR with Tesseract
        text = image_to_string(processed_img)
        return text.strip()

    except Exception as e:
        logging.error(f"[OCR Error - Page {page_num}]: {str(e)}")
        return ""

# ─────────────────────── PDF to Full Text ───────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Converts PDF to images, runs OCR on all pages, returns full text.
    """
    all_text = []
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir)
        for i, img in enumerate(images):
            page_text = extract_text_from_image(img, page_num=i + 1)
            all_text.append(f"\n--- Page {i + 1} ---\n{page_text}")
    return "\n".join(all_text).strip()

# ─────────────────────── OCR Per Page (Dict) ───────────────────────

def run_ocr_on_images(image_paths: List[str]) -> Dict[int, str]:
    """
    Runs OCR on a list of image paths and returns text per page.
    """
    results = {}
    for i, image_path in enumerate(image_paths):
        try:
            img = Image.open(image_path)
            text = extract_text_from_image(img, page_num=i + 1)
            results[i] = text
        except Exception as e:
            logging.error(f"❌ Failed OCR on image {image_path}: {e}")
            results[i] = ""
    return results
