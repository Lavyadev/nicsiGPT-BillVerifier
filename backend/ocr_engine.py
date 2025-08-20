import tempfile
from pdf2image import convert_from_path
from pytesseract import image_to_string, image_to_osd, Output  # type: ignore
from PIL import Image
from typing import List, Dict, Tuple
import logging
import numpy as np
import cv2
import os
import pytesseract
import re

# Debug output directory
DEBUG_DIR = "debug_output"
os.makedirs(DEBUG_DIR, exist_ok=True)

# Tesseract configs
TESSERACT_OCR_CONFIG = "--psm 6 -c preserve_interword_spaces=1"
TESSERACT_OSD_CONFIG = "--psm 0"

def _alnum_ratio(txt: str) -> float:
    if not txt:
        return 0.0
    alnum = sum(c.isalnum() for c in txt)
    return alnum / max(1, len(txt))

def _binarize(gray: np.ndarray) -> np.ndarray:
    try:
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        return cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 15, 11
        )
    except Exception:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

def _estimate_osd_rotation(pil_image: Image.Image, page_num: int | None) -> int:
    try:
        osd = pytesseract.image_to_osd(pil_image, output_type=Output.DICT, config=TESSERACT_OSD_CONFIG)
        angle = int(osd.get("rotate", 0) or 0)
        if page_num:
            logging.info(f"Detected rotation for page {page_num}: {angle} degrees")
        return angle
    except Exception as e:
        logging.error(f"OSD failed (page {page_num}): {e}")
        return 0

def _safe_rotate(img: Image.Image, angle: int) -> Image.Image:
    return img.rotate(-angle, expand=True)

def _safe_deskew(binary: np.ndarray, allow: bool) -> np.ndarray:
    if not allow:
        return binary
    coords = np.column_stack(np.where(binary > 0))
    if coords.size < 1500:
        return binary
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 1.5 or abs(abs(angle) - 90) < 5:
        return binary
    (h, w) = binary.shape[:2]
    canvas_h = int(h * 1.2)
    canvas_w = int(w * 1.2)
    pad_top = (canvas_h - h) // 2
    pad_left = (canvas_w - w) // 2
    padded = cv2.copyMakeBorder(
        binary,
        pad_top, canvas_h - h - pad_top,
        pad_left, canvas_w - w - pad_left,
        cv2.BORDER_CONSTANT, value=255
    )
    M = cv2.getRotationMatrix2D((canvas_w // 2, canvas_h // 2), angle, 1.0)
    rotated = cv2.warpAffine(
        padded, M, (canvas_w, canvas_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=255
    )
    return rotated

def _ocr_numpy(binary: np.ndarray) -> str:
    return image_to_string(Image.fromarray(binary), lang="eng", config=TESSERACT_OCR_CONFIG)

def _try_ocr_variants(pil_image: Image.Image, page_num: int | None) -> Tuple[str, np.ndarray]:
    grayA = np.array(pil_image.convert("L"))
    binA = _binarize(grayA)
    txtA = _ocr_numpy(binA)
    scoreA = _alnum_ratio(txtA)

    osd_angle = _estimate_osd_rotation(pil_image, page_num)
    binB = None
    txtB = ""
    scoreB = -1.0
    if osd_angle in (90, 180, 270):
        rotB_img = _safe_rotate(pil_image, osd_angle)
        grayB = np.array(rotB_img.convert("L"))
        binB = _binarize(grayB)
        allow_deskew_b = (osd_angle == 180)
        if allow_deskew_b:
            binB = _safe_deskew(binB, allow=True)
        txtB = _ocr_numpy(binB)
        scoreB = _alnum_ratio(txtB)

    binC = _safe_deskew(binA, allow=True)
    txtC = _ocr_numpy(binC)
    scoreC = _alnum_ratio(txtC)

    if page_num:
        try:
            Image.fromarray(binA).save(os.path.join(DEBUG_DIR, f"page_{page_num:03}_A_norotate.png"))
            Image.fromarray(binC).save(os.path.join(DEBUG_DIR, f"page_{page_num:03}_C_deskew.png"))
            if binB is not None:
                Image.fromarray(binB).save(os.path.join(DEBUG_DIR, f"page_{page_num:03}_B_osd.png"))
        except Exception:
            pass

    candidates = [("A", scoreA, txtA, binA), ("C", scoreC, txtC, binC)]
    if binB is not None:
        candidates.append(("B", scoreB, txtB, binB))

    chosen_tag, _, chosen_txt, chosen_bin = max(candidates, key=lambda x: x[1])

    if page_num and chosen_bin is not None:
        try:
            Image.fromarray(chosen_bin).save(os.path.join(DEBUG_DIR, f"page_{page_num:03}_final.png"))
        except Exception:
            pass

    return chosen_txt.strip(), chosen_bin if chosen_bin is not None else binA

def extract_text_from_image(pil_image: Image.Image, page_num: int | None = None) -> str:
    try:
        text, final_bin = _try_ocr_variants(pil_image, page_num)
        if page_num is not None and final_bin is not None:
            Image.fromarray(final_bin).save(os.path.join(DEBUG_DIR, f"page{page_num:03}_final.png"))
        return text
    except Exception as e:
        logging.error(f"[OCR Error - Page {page_num}]: {str(e)}")
        return ""

def extract_text_from_pdf(pdf_path: str) -> str:
    all_text = []
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir)
        for i, img in enumerate(images):
            page_text = extract_text_from_image(img, page_num=i + 1)
            all_text.append(f"\n--- Page {i + 1} ---\n{page_text}")
    return "\n".join(all_text).strip()

def run_ocr_on_images(image_paths: List[str]) -> Dict[int, str]:
    results: Dict[int, str] = {}
    for i, image_path in enumerate(image_paths):
        try:
            img = Image.open(image_path)
            text = extract_text_from_image(img, page_num=i + 1)
            results[i] = text
        except Exception as e:
            logging.error(f"Failed OCR on image {image_path}: {e}")
            results[i] = ""
    return results
