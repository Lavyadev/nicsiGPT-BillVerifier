import os
import uuid
import re
from datetime import datetime
from fastapi import UploadFile, HTTPException
from pdf2image import convert_from_path
UPLOAD_DIR = os.path.join("storage", "uploads")
TEMP_IMAGE_DIR = os.path.join("storage", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = [".pdf"]
MAX_FILE_SIZE_MB = 10
def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)
def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
def generate_submission_id() -> str:
    return f"sub_{uuid.uuid4().hex[:8]}"
def get_upload_dir() -> str:
    return UPLOAD_DIR
def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
def convert_pdf_to_images(pdf_path: str, output_folder: str, dpi: int = 300, max_pages: int | None = 40) -> list:
    """
    Converts a PDF to images. max_pages protects memory/time for demos.
    Returns a list of image file paths.
    """
    os.makedirs(output_folder, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=dpi)
    if max_pages:
        images = images[:max_pages]
    image_paths = []
    for i, img in enumerate(images):
        img_path = os.path.join(output_folder, f"page_{i+1}.png")
        img.save(img_path, "PNG")
        image_paths.append(img_path)
    return image_paths
async def save_uploaded_file(file: UploadFile, submission_id: str) -> dict:
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    safe_name = sanitize_filename(file.filename)
    filename = f"{submission_id}_{safe_name}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large. Max allowed is {MAX_FILE_SIZE_MB} MB.")
    with open(save_path, "wb") as buffer:
        buffer.write(contents)
    image_output_dir = os.path.join(TEMP_IMAGE_DIR, submission_id)
    image_paths = convert_pdf_to_images(save_path, image_output_dir, dpi=300, max_pages=40)
    return {
        "filename": filename,
        "path": save_path,
        "uploaded_at": get_timestamp(),
        "size_mb": round(file_size_mb, 2),
        "image_paths": image_paths,
        "image_dir": image_output_dir
    }