from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.file_handler import is_allowed_file, save_uploaded_file, generate_submission_id
from backend.ocr_engine import run_ocr_on_images
from backend.doc_detector import classify_pages_by_type, detect_document_presence_in_text
from backend.field_extractor import extract_invoice_fields_from_text
from backend.databases.po_data import PO_DATABASE
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def _score_invoice_page(text: str) -> int:
    keys = ["tax invoice", "invoice no", "igst", "cgst", "sgst", "total amount", "hsn", "sac", "place of supply", "gstin"]
    t = text.lower()
    return sum(1 for k in keys if k in t)
@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/version")
def version():
    return {"version": "mvp-0.1.3"}
@app.post("/analyze/")
async def analyze_document(po_number: str = Form(...), file: UploadFile = Form(...)):
    if po_number not in PO_DATABASE:
        return JSONResponse(content={"error": "Invalid PO Number"}, status_code=400)
    if not is_allowed_file(file.filename):
        return JSONResponse(content={"error": "Only PDF files are allowed."}, status_code=400)
    submission_id = generate_submission_id()
    try:
        # STEP 1: Save uploaded PDF and convert to images
        save_result = await save_uploaded_file(file, submission_id)
        image_paths = save_result["image_paths"]
        # STEP 2: OCR on images
        ocr_text_by_page = run_ocr_on_images(image_paths)
        # Debug: Save OCR output to file
        debug_file_path = f"ocr_debug_output_{submission_id}.txt"
        with open(debug_file_path, "w", encoding="utf-8") as f:
            for page_num, page_text in ocr_text_by_page.items():
                f.write(f"\n\n=== OCR TEXT: Page {page_num + 1} ===\n")
                f.write(page_text if page_text else "[Empty Page]")
        # STEP 3: Classify document types per page
        page_doc_types = classify_pages_by_type(ocr_text_by_page)
        # STEP 4: Check required document types from PO
        required_docs = PO_DATABASE[po_number]["required_docs"]
        all_text = " ".join(ocr_text_by_page.values())
        doc_checklist = detect_document_presence_in_text(all_text, required_docs)
        # STEP 5: Extract invoice fields (if invoice found)
        invoice_pages = [p for p, t in page_doc_types.items() if t == "invoice"]
        if invoice_pages:
            scored = sorted(invoice_pages, key=lambda p: _score_invoice_page(ocr_text_by_page[p]), reverse=True)
            top_pages = scored[:2]
            full_invoice_text = " ".join([ocr_text_by_page[p] for p in top_pages])
            invoice_text = full_invoice_text[:2500]
        else:
            invoice_text = ocr_text_by_page.get(0, "")[:2000]
        extracted_fields = {}
        if invoice_text:
            try:
                extracted_fields = extract_invoice_fields_from_text(invoice_text)
            except Exception as e:
                extracted_fields = {"error": f"Extraction failed: {str(e)}"}
        # STEP 6: Build response
        return {
            "submission_id": submission_id,
            "po_number": po_number,
            "document_checklist": doc_checklist,
            "page_classification": page_doc_types,
            "extracted_fields": extracted_fields,
            "file_info": save_result,
            "ocr_debug_file": debug_file_path,
            "validation": "Field validation skipped in current phase."
        }
    except Exception as e:
        return JSONResponse(content={"error": f"Server error: {str(e)}"}, status_code=500)