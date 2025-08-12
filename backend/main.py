from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.file_handler import is_allowed_file, save_uploaded_file, generate_submission_id
from backend.ocr_engine import run_ocr_on_images
from backend.doc_detector import classify_pages_by_type, detect_document_presence_in_text
from backend.field_extractor import extract_invoice_fields_from_text
from backend.databases.po_data import PO_DATABASE

app = FastAPI()

# Optional: Add CORS if calling from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze/")
async def analyze_document(po_number: str = Form(...), file: UploadFile = Form(...)):
    print("📥 Received request for analysis")

    if po_number not in PO_DATABASE:
        return JSONResponse(content={"error": "Invalid PO Number"}, status_code=400)

    if not is_allowed_file(file.filename):
        return JSONResponse(content={"error": "Only PDF files are allowed."}, status_code=400)

    submission_id = generate_submission_id()

    try:
        # STEP 1: Save uploaded PDF and convert to images
        print("💾 Saving file and generating images...")
        save_result = await save_uploaded_file(file, submission_id)
        image_paths = save_result["image_paths"]

        # STEP 2: OCR on images
        print("🔍 Running OCR...")
        ocr_text_by_page = run_ocr_on_images(image_paths)

        # ───────────── Debug: Save OCR output to file ─────────────
        debug_file_path = f"ocr_debug_output_{submission_id}.txt"
        with open(debug_file_path, "w", encoding="utf-8") as f:
          for page_num, page_text in ocr_text_by_page.items():
            f.write(f"\n\n=== OCR TEXT: Page {page_num + 1} ===\n")
            f.write(page_text if page_text else "[Empty Page]")
        print(f"✅ OCR debug output saved at: {debug_file_path}")


        # STEP 3: Classify document types per page
        print("📄 Classifying page types...")
        page_doc_types = classify_pages_by_type(ocr_text_by_page)
        print('page doc tyopes', page_doc_types)
        print("\n=== Page Classification ===")
        for page, doc_type in page_doc_types.items():
           print(f"Page {page + 1}: {doc_type}")


        # STEP 4: Check required document types from PO
        print("🧾 Checking required document types from PO...")
        required_docs = PO_DATABASE[po_number]["required_docs"]
        all_text = " ".join(ocr_text_by_page.values())
        doc_checklist = detect_document_presence_in_text(all_text, required_docs)

        # STEP 5: Extract invoice fields (if invoice found)
        print("🤖 Extracting invoice fields with LLM...")
        invoice_pages = [p for p, t in page_doc_types.items() if t == "invoice"]

        if invoice_pages:
           full_invoice_text = " ".join([ocr_text_by_page[p] for p in invoice_pages])
           invoice_text = full_invoice_text[:2000]  # Truncate to avoid overload
        else:
            print("⚠️ No page classified as invoice. Falling back to Page 1 for LLM.")
            invoice_text = ocr_text_by_page.get(0, "")[:2000]  # Also truncate fallback


        print("\n=== Invoice Text Sent to LLM ===")
        print(invoice_text[:1500] if invoice_text else "⚠️ EMPTY invoice_text!")

        extracted_fields = extract_invoice_fields_from_text(invoice_text) if invoice_text else {}

        # STEP 6: Build response
        return {
            "submission_id": submission_id,
            "po_number": po_number,
            "document_checklist": doc_checklist,
            "page_classification": page_doc_types,
            "extracted_fields": extracted_fields,
            "file_info": save_result,
            "validation": "Field validation skipped in current phase."
        }

    except Exception as e:
        print(f"🔥 ERROR: {e}")
        return JSONResponse(content={"error": f"Server error: {str(e)}"}, status_code=500)
