import re
from rapidfuzz import fuzz, process
from backend.config import DOCUMENT_KEYWORDS, FUZZY_THRESHOLD
import logging

# Strong anchors to reduce false positives
STRONG_ANCHORS = {
    "invoice": [
        "tax invoice", "invoice no", "invoice number", "igst", "cgst", "sgst",
        "hsn", "sac", "place of supply", "gstin"
    ],
    "mpr": [
        "monthly progress report", "monthly performance report", "service period",
        "from", "to", "satisfactory", "work order no", "project no", "leaves taken"
    ],
    "salary_proof": [
        "salary breakup", "net pay", "beneficiary a/c", "beneficiary a/c no",
        "utr", "neft", "rtgs", "employees' provident fund", "epfo",
        "trrn", "ecr id", "payment confirmation", "bank statement"
    ]
}

# ────────────────────────── Enhanced Fuzzy Matching ──────────────────────────
def fuzzy_keyword_match(text: str, keyword_list: list, threshold: int = FUZZY_THRESHOLD) -> bool:
    t = text.lower()
    for keyword in keyword_list:
        kw = keyword.lower()
        if len(kw) <= 3:
            if re.search(rf"\b{re.escape(kw)}\b", t):
                logging.info(f"Exact short match: '{kw}' found")
                return True
        elif " " in kw:
            words = kw.split()
            if all(re.search(rf"\b{re.escape(w)}\b", t) for w in words):
                logging.info(f"All words found in multi-word keyword: '{kw}'")
                return True
        else:
            matches = process.extract(kw, [t], scorer=fuzz.partial_ratio, limit=1)
            score = matches[0][1] if matches else 0
            logging.info(f"Fuzzy match for '{kw}': Score={score}")
            if score >= threshold:
                return True
    return False

def count_keyword_hits(text: str, keywords: list) -> int:
    hits = 0
    for kw in keywords:
        if fuzzy_keyword_match(text, [kw]):
            hits += 1
    return hits

# ───────────────────── Document Presence Detector ─────────────────────
def detect_document_presence_in_text(text: str, required_docs: list) -> dict:
    """
    Checks presence for requested document types using keywords.
    Returns: {doc_type: True/False}
    """
    t = " ".join(text.lower().split())
    presence = {}
    for doc_type in required_docs:
        keyword_list = DOCUMENT_KEYWORDS.get(doc_type, [])
        strong_list = STRONG_ANCHORS.get(doc_type, [])
        total_hits = count_keyword_hits(t, keyword_list)
        strong_hits = count_keyword_hits(t, strong_list)
        presence[doc_type] = (strong_hits >= 1 and total_hits >= 2)
    return presence

# ───────────────────── Page-wise Document Classifier ─────────────────────
def classify_pages_by_type(ocr_text_by_page: dict) -> dict:
    """
    Classifies each page; requires at least one strong anchor and 2 total hits.
    Returns: {page_num: doc_type or 'unknown'}
    """
    page_classification = {}
    for page_num, text in ocr_text_by_page.items():
        clean_text = " ".join((text or "").lower().split())
        classified = "unknown"
        for doc_type, keywords in DOCUMENT_KEYWORDS.items():
            total_hits = count_keyword_hits(clean_text, keywords)
            strong_hits = count_keyword_hits(clean_text, STRONG_ANCHORS.get(doc_type, []))
            if strong_hits >= 1 and total_hits >= 2:
                classified = doc_type
                break
        page_classification[page_num] = classified
    return page_classification
