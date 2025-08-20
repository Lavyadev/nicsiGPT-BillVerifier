import json
import logging
import re
from backend.utils.llm_ollama import call_llm_with_prompt

logging.basicConfig(level=logging.INFO)

def _find_first(patterns, text):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

def _normalize_amount(s):
    if not s:
        return None
    s = s.replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else None

def _extract_first_json(s: str) -> str:
    # Extract the first balanced {...} block and remove trailing commas before }
    start = s.find("{")
    if start == -1:
        return ""
    depth = 0
    out = []
    for ch in s[start:]:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        out.append(ch)
        if depth == 0:
            break
    text = "".join(out)
    text = re.sub(r",\s*}", "}", text)
    return text

def extract_invoice_fields_from_text(ocr_text: str) -> dict:
    try:
        expected_keys = [
            "vendor_name", "vendor_gstin", "invoice_number", "invoice_date",
            "invoice_total_amount", "billing_address_gstin",
            "shipping_address_gstin", "reverse_charge"
        ]

        # Regex seed
        seed = {
            "invoice_number": _find_first([
                r"invoice\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Z0-9\-\/]+)"
            ], ocr_text),
            "invoice_date": _find_first([
                r"invoice\s*date\s*[:\-]?\s*([0-9]{1,2}\s*[A-Za-z]{3,9}\s*[0-9]{2,4})",
                r"invoice\s*date\s*[:\-]?\s*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})"
            ], ocr_text),
            "vendor_gstin": _find_first([
                r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b"
            ], ocr_text),
            "billing_address_gstin": _find_first([
                r"gstin[^A-Za-z0-9]{0,5}[:\-]?\s*(07[A-Z0-9]{13})"
            ], ocr_text),
            "shipping_address_gstin": _find_first([
                r"gstin[^A-Za-z0-9]{0,5}[:\-]?\s*(07[A-Z0-9]{13})"
            ], ocr_text),
            "invoice_total_amount": _find_first([
                r"(?:total\s*amount\s*(?:after\s*tax|incl\.?\s*tax)?|grand\s*total)\s*[:\-]?\s*₹?\s*([0-9,]+\.\d{2})"
            ], ocr_text)
        }

        # Optional fallback patterns if invoice number is missed by OCR spacing
        if not seed["invoice_number"]:
            seed["invoice_number"] = _find_first([
                r"\b(mh|in|dl|up)[a-z0-9\/\-]{6,}\b"
            ], ocr_text)

        if seed["invoice_total_amount"]:
            seed["invoice_total_amount"] = _normalize_amount(seed["invoice_total_amount"])

        prompt = f"""
You are a document-understanding AI that extracts structured data from invoices.
Return ONLY valid compact JSON with these exact keys:
vendor_name (string|null)
vendor_gstin (string|null)
invoice_number (string|null)
invoice_date (string|null)
invoice_total_amount (number|null)
billing_address_gstin (string|null)
shipping_address_gstin (string|null)
reverse_charge (string|null)
Rules:
Do not include any extra keys or text.
If a field is not present, use null.
Do not guess GSTINs; only return those present in the text.
Text:
  {ocr_text.strip()}
"""

        logging.info("Sending prompt to Ollama...")
        llm_output = call_llm_with_prompt(prompt)

        # If LLM is empty/timeout → regex-only
        if not llm_output:
            logging.warning("LLM returned empty; falling back to regex-only.")
            extracted = {k: None for k in expected_keys}
            for k, v in seed.items():
                if v is not None:
                    extracted[k] = v
            if isinstance(extracted.get("invoice_total_amount"), str):
                extracted["invoice_total_amount"] = _normalize_amount(extracted["invoice_total_amount"])
            return extracted

        # Parse JSON safely
        json_text = _extract_first_json(llm_output)
        extracted = {}
        try:
            extracted = json.loads(json_text) if json_text else {}
        except Exception as e:
            logging.error(f"LLM JSON parse failed: {e}")
            extracted = {}

        # Ensure keys and merge seeds
        for key in expected_keys:
            if key not in extracted:
                extracted[key] = None

        for k, v in seed.items():
            if v and (extracted.get(k) in (None, "")):
                extracted[k] = v

        if isinstance(extracted.get("invoice_total_amount"), str):
            extracted["invoice_total_amount"] = _normalize_amount(extracted["invoice_total_amount"])

        return extracted

    except Exception as e:
        logging.error(f"Error in invoice field extraction: {e}")
        return {
            "vendor_name": None,
            "vendor_gstin": None,
            "invoice_number": None,
            "invoice_date": None,
            "invoice_total_amount": None,
            "billing_address_gstin": None,
            "shipping_address_gstin": None,
            "reverse_charge": None,
            "error": f"LLM Extraction Error: {str(e)}"
        }
