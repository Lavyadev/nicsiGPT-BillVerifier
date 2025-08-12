import json
import logging
from backend.utils.llm_ollama import call_llm_with_prompt

logging.basicConfig(level=logging.INFO)

def extract_invoice_fields_from_text(ocr_text: str) -> dict:
    try:
        prompt = f"""
You are a document-understanding AI that extracts structured data from invoices.

From the text below, extract and return the following fields in a valid JSON object:

- vendor_name
- vendor_gstin
- invoice_number
- invoice_date
- invoice_total_amount
- billing_address_gstin
- shipping_address_gstin
- reverse_charge

⚠️ IMPORTANT: Output only a JSON object. No explanation, no markdown.

Text:
\"\"\"{ocr_text.strip()}\"\"\"
"""
        logging.info("⏱ Sending prompt to Ollama...")
        llm_output = call_llm_with_prompt(prompt)

        json_start = llm_output.find("{")
        json_end = llm_output.rfind("}") + 1
        json_text = llm_output[json_start:json_end]

        extracted = json.loads(json_text)

        # Ensure all keys exist
        expected_keys = [
            "vendor_name", "vendor_gstin", "invoice_number", "invoice_date",
            "invoice_total_amount", "billing_address_gstin",
            "shipping_address_gstin", "reverse_charge"
        ]

        for key in expected_keys:
            if key not in extracted:
                extracted[key] = None

        return extracted

    except Exception as e:
        logging.error(f"🔥 Error in invoice field extraction: {e}")
        return {"error": f"LLM Extraction Error: {str(e)}"}
