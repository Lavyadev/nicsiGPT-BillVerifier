import streamlit as st
import requests
import json
from io import BytesIO

def _get_api_base():
    try:
        return st.secrets.get("API_BASE", "http://127.0.0.1:8000")
    except Exception:
        return "http://127.0.0.1:8000"

API_BASE = _get_api_base()
ANALYZE_URL = f"{API_BASE}/analyze/"
HEALTH_URL = f"{API_BASE}/health"
VERSION_URL = f"{API_BASE}/version"

st.set_page_config(page_title="📄 Bill Verifier", layout="centered")
st.title("📤 Upload & Analyze Document")

# Sidebar: backend status
with st.sidebar:
    st.header("Backend status")
    try:
        health = requests.get(HEALTH_URL, timeout=10).json()
        st.success(f"Health: {health.get('status','ok')}")
    except Exception as e:
        st.error(f"Health: unavailable ({e})")
    try:
        ver = requests.get(VERSION_URL, timeout=10).json()
        st.info(f"Version: {ver.get('version','unknown')}")
    except Exception:
        pass

# Step 1: Input
po_number = st.text_input("Enter PO Number:", placeholder="e.g., PO12345")
uploaded_file = st.file_uploader("Upload merged PDF (Invoice + MPR + Salary proofs)", type=["pdf"])

# Optional: advanced section
with st.expander("Advanced", expanded=False):
    st.caption("These affect only the request handling on the client side.")
    req_timeout = st.number_input("Request Timeout (seconds)", min_value=60, max_value=900, value=300, step=30)

# Analyze button
analyze_disabled = not (uploaded_file and po_number)
if st.button("Analyze", disabled=analyze_disabled, type="primary"):
    if not po_number:
        st.warning("Please enter a PO Number.")
    elif not uploaded_file:
        st.warning("Please upload a PDF file.")
    else:
        with st.spinner("Analyzing document... This may take a few minutes for large PDFs."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                data = {"po_number": po_number}
                resp = requests.post(ANALYZE_URL, data=data, files=files, timeout=int(req_timeout))

                if resp.status_code == 200:
                    result = resp.json()
                    st.success("✅ File analyzed successfully.")

                    # Top metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Submission ID: {result.get('submission_id','-')}")
                        st.write(f"PO Number: {result.get('po_number','-')}")
                    with col2:
                        file_info = result.get("file_info", {}) or {}
                        st.write(f"Uploaded at: {file_info.get('uploaded_at','-')}")
                        st.write(f"File size: {file_info.get('size_mb','-')} MB")

                    # Document presence checklist
                    if "document_checklist" in result:
                        st.subheader("📋 Document Presence Checklist")
                        checks = result.get("document_checklist") or {}
                        if not checks:
                            st.info("No checklist returned.")
                        else:
                            cols = st.columns(max(1, len(checks)))
                            for idx, (doc, present) in enumerate(checks.items()):
                                badge = "✅" if present else "❌"
                                label = doc.replace("_", " ").title() if isinstance(doc, str) else str(doc)
                                cols[idx % len(cols)].markdown(f"{badge} **{label}**")

                    # Page classification
                    if "page_classification" in result:
                        st.subheader("📄 Page Classification")
                        pc = result.get("page_classification") or {}
                        buckets = {}
                        for p, t in pc.items():
                            try:
                                page_idx = int(p) + 1
                            except Exception:
                                try:
                                    page_idx = int(p)
                                except Exception:
                                    page_idx = p
                            label = (t or "unknown")
                            buckets.setdefault(label, []).append(page_idx)

                        for doc_type, pages in buckets.items():
                            try:
                                pages_sorted = sorted(
                                    pages,
                                    key=lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0
                                )
                            except Exception:
                                pages_sorted = pages
                            doc_label = (doc_type if isinstance(doc_type, str) else str(doc_type)).replace("_", " ").title()
                            st.write(f"- {doc_label}: {len(pages_sorted)} page(s) → {pages_sorted}")

                    # Extracted fields
                    if "extracted_fields" in result:
                        st.subheader("🧾 Extracted Invoice Fields")
                        st.json(result["extracted_fields"])

                    # Validation info
                    if "validation" in result:
                        st.subheader("🔍 Field Validation")
                        v = result["validation"]
                        if isinstance(v, str):
                            st.info(v)
                        elif isinstance(v, dict):
                            st.write(v)
                        else:
                            st.warning("Unexpected validation format.")

                    # Debug artifacts
                    if "ocr_debug_file" in result:
                        with st.expander("🛠 Debug Artifacts"):
                            st.code(result["ocr_debug_file"])

                    # Raw JSON download
                    with st.expander("📦 Full JSON Response", expanded=False):
                        st.json(result)
                        buf = BytesIO(json.dumps(result, indent=2).encode("utf-8"))
                        st.download_button(
                            "Download JSON",
                            data=buf,
                            file_name=f"analysis_{result.get('submission_id','output')}.json",
                            mime="application/json"
                        )

                else:
                    st.error(f"❌ Analysis failed (HTTP {resp.status_code}).")
                    try:
                        st.json(resp.json())
                    except Exception:
                        st.text(resp.text)

            except requests.exceptions.Timeout:
                st.error("⏳ Request timed out. Increase the timeout in Advanced settings and try again.")
            except Exception as e:
                st.error(f"🚨 Request failed: {str(e)}")
                