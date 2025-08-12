import re
from rapidfuzz import fuzz, process
from backend.config import DOCUMENT_KEYWORDS, FUZZY_THRESHOLD

# ────────────────────────── Enhanced Fuzzy Matching ──────────────────────────

def fuzzy_keyword_match(text: str, keyword_list: list, threshold: int = FUZZY_THRESHOLD) -> bool:
    """
    Checks whether any keyword in the list appears in the text using:
    - Exact match for short keywords
    - Word-by-word presence for multi-word phrases
    - Fallback fuzzy match using partial_ratio
    """
    text = text.lower()

    for keyword in keyword_list:
        keyword = keyword.lower()

        # Case 1: very short keyword (<=3 chars) → exact match
        if len(keyword) <= 3:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                return True

        # Case 2: multi-word keyword → all words must exist
        elif " " in keyword:
            words = keyword.split()
            if all(re.search(rf"\b{re.escape(word)}\b", text) for word in words):
                return True

        # Case 3: fallback fuzzy match
        else:
            matches = process.extract(keyword, [text], scorer=fuzz.partial_ratio, limit=1)
            score = matches[0][1] if matches else 0
            if score >= threshold:
                return True

    return False

# ─────────────────────── Document Presence Detector ───────────────────────

def detect_document_presence_in_text(text: str, required_docs: list) -> dict:
    """
    Checks for presence of required document types in the full OCR text.
    Returns: {doc_type: True/False}
    """
    text = " ".join(text.lower().split())  # Normalize whitespace
    presence = {}

    for doc_type in required_docs:
        keyword_list = DOCUMENT_KEYWORDS.get(doc_type, [])
        presence[doc_type] = fuzzy_keyword_match(text, keyword_list)

    return presence

# ─────────────────────── Page-wise Document Classifier ───────────────────────

def classify_pages_by_type(ocr_text_by_page: dict) -> dict:
    """
    Classifies each page based on fuzzy keyword detection.
    Returns: {page_num: doc_type or 'unknown'}
    """
    page_classification = {}

    for page_num, text in ocr_text_by_page.items():
        clean_text = " ".join(text.lower().split())
        classified = "unknown"

        for doc_type, keywords in DOCUMENT_KEYWORDS.items():
            if fuzzy_keyword_match(clean_text, keywords):
                classified = doc_type
                break

        page_classification[page_num] = classified

    return page_classification
