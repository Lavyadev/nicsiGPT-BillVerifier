# from difflib import SequenceMatcher
# from databases.po_data import PO_DATABASE

# def is_name_similar(name1: str, name2: str, threshold: float = 0.85) -> bool:
#     """
#     Fuzzy string comparison using SequenceMatcher.
#     """
#     ratio = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
#     return ratio >= threshold

# def validate_fields(po_number: str, extracted_fields: dict) -> dict:
#     """
#     Validates LLaMA-extracted fields against PO DB.
#     Returns a dictionary of validation results.
#     """
#     result = {
#         "vendor_gstin_match": False,
#         "vendor_name_match": False,
#         "invoice_total_amount_valid": False,
#         "errors": []
#     }

#     if po_number not in PO_DATABASE:
#         result["errors"].append("Invalid PO number.")
#         return result

#     po_data = PO_DATABASE[po_number]

#     # GSTIN Validation
#     if extracted_fields.get("vendor_gstin") == po_data.get("vendor_gstin"):
#         result["vendor_gstin_match"] = True
#     else:
#         result["errors"].append("GSTIN mismatch.")

#     # Vendor Name Fuzzy Validation
#     if is_name_similar(extracted_fields.get("vendor_name", ""), po_data.get("vendor_name", "")):
#         result["vendor_name_match"] = True
#     else:
#         result["errors"].append("Vendor name mismatch.")

#     # Invoice Amount Validation (just numeric check for now)
#     try:
#         amount = float(str(extracted_fields.get("invoice_total_amount", "0")).replace(",", "").strip())
#         result["invoice_total_amount_valid"] = amount > 0
#     except:
#         result["errors"].append("Invalid invoice amount.")

#     return result
