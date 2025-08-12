import streamlit as st
import requests

st.set_page_config(page_title="📄 Bill Verifier")

st.title("📤 Upload & Analyze Document")

# Step 1: Input fields
po_number = st.text_input("Enter PO Number:")
uploaded_file = st.file_uploader("Upload Merged PDF (Invoice + MPR + Bank Statement)", type=["pdf"])

# Step 2: Button and call
if uploaded_file and po_number:
    if st.button("Analyze"):
        with st.spinner("Analyzing document..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/analyze/",
                    data={"po_number": po_number},
                    files={"file": (uploaded_file.name, uploaded_file, "application/pdf")},
                    timeout=300
                )

                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ File analyzed successfully.")

                    # Step 3: Show Document Checklist
                    if "document_checklist" in result:
                        with st.expander("📋 Document Presence Checklist", expanded=True):
                            for doc, present in result["document_checklist"].items():
                                emoji = "✅" if present else "❌"
                                st.write(f"{emoji} {doc.replace('_', ' ').title()}")

                    # Step 4: Show Extracted Fields
                    if "extracted_fields" in result:
                        with st.expander("🧾 Extracted Invoice Fields"):
                            st.json(result["extracted_fields"])

                    # Step 5: Show Validation Info
                    if "validation" in result:
                        with st.expander("🔍 Field Validation"):
                            if isinstance(result["validation"], str):
                                st.info(result["validation"])
                            elif isinstance(result["validation"], dict):
                                val = result["validation"]
                                st.write(f"**GSTIN Match:** {'✅' if val['vendor_gstin_match'] else '❌'}")
                                st.write(f"**Vendor Name Match:** {'✅' if val['vendor_name_match'] else '❌'}")
                                st.write(f"**Invoice Amount Valid:** {'✅' if val['invoice_total_amount_valid'] else '❌'}")
                                if val.get("errors"):
                                    st.error("⚠️ Errors:")
                                    for err in val["errors"]:
                                        st.write(f"• {err}")
                            else:
                                st.warning("⚠️ Unexpected format in validation result.")

                else:
                    st.error("❌ Analysis failed.")
                    with st.expander("Server Response"):
                        st.json(response.json())

            except Exception as e:
                st.error(f"🚨 Request failed: {str(e)}")
