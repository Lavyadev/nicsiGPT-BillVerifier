import tempfile
from pdf2image import convert_from_path
from pytesseract import image_to_string, image_to_osd, Output 
from PIL import Image
from typing import List, Dict
import logging
import numpy as np
import cv2
import os
import pytesseract

# Create debug output directory
DEBUG_DIR = "debug_output"
os.makedirs(DEBUG_DIR, exist_ok=True)

# ─────────────────────── Preprocessing + OCR ───────────────────────

def correct_image_orientation(image: Image.Image, page_num: int = None) -> Image.Image:
    try:
        osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT) #type:ignore 
        angle = osd.get("rotate", 0)

        # 🧭 Log detected orientation for debugging
        if page_num is not None:
            logging.info(f"🧭 Detected rotation for Page {page_num}: {angle} degrees")

        rotated_image = image.rotate(-angle, expand=True)
        return rotated_image
    except Exception as e:
        logging.error(f"Orientation correction failed on Page {page_num}: {str(e)}")
        return image



def extract_text_from_image(pil_image: Image.Image, page_num: int = None) -> str:
    try:
        pil_image = correct_image_orientation(pil_image, page_num)
        gray = np.array(pil_image.convert("L"))

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Adaptive thresholding (try both THRESH_BINARY and THRESH_BINARY_INV)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 15, 11
        )

        # De-skew the image (if needed)
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = binary.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Save preprocessed image
        if page_num is not None:
            Image.fromarray(rotated).save(os.path.join(DEBUG_DIR, f"page_{page_num:03}_processed_rotated.png"))

        text = image_to_string(Image.fromarray(rotated))
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
