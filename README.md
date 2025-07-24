# nicsiGPT-BillVerifier

##  Scope of the Project

This project automates the verification process through five core modules of intelligence:

### 1.  Invoice & Supporting Document Extraction
The foundation of the platform. The system ingests and understands a wide array of document types submitted as a single package.
-   **Parses:** Invoices, Manpower Reports (MPR), Attendance Reports, Salary Proofs, Completion Certificates, and more.
-   **Technology:** A Deep Learning model with integrated OCR capabilities (based on LayoutLM architecture) for high-accuracy, context-aware data extraction.

### 🔁 Enhanced Document Ingestion Workflow (with Pre-Submission Alerts)

```text
Start
  ↓
────────────────── Phase 1: Staging Area ──────────────────
  ↓
Vendor Enters PO Number
  ↓
→ Server fetches PO requirements (ground truth)
  ↓
Vendor Drag-and-Drops PDFs (Invoice, MPR, Certificate)
  ↓
→ Client-side validation: only PDF allowed
    ├──> If not PDF → show error → reject file
    └──> If PDF → upload to staging endpoint
  ↓
Show "Analyzing..." spinner in UI for each file
  ↓
──────────────── Phase 2: Pre-Flight Check ────────────────
  ↓
→ Server triggers High-Speed AI Pipeline (Quick Look)
  ↓
Real-Time AI Checks:
  • Document Existence (e.g., Certificate required?)
  • Key Field Extraction (GST, Amount, Vendor Name)
  • Signature Detection (CV model on Certificate)
  • Basic Consistency Check (Vendor data vs DB)
  ↓
→ Server sends back JSON with warnings/errors
  ↓
──────────── Phase 3: Interactive Feedback Loop ───────────
  ↓
UI renders result checklist:
  • ✅ Invoice Found
  • ⚠ GST Mismatch
  • ❌ Missing Completion Certificate
  • ✅ MPR Found
  • ✅ Signature Found (if doc present)
  ↓
"Submit" button remains DISABLED until all ❌ are resolved
  ↓
Vendor Corrects Issues:
  → Upload missing/corrected files
  → System re-runs analysis
  → UI updates checklist in real-time
  ↓
→ Loop continues until all checks are ✅
  ↓
────────────── Phase 4: Final Submission ────────────────
  ↓
"Submit" Button is ENABLED
  ↓
Vendor clicks "Submit"
  ↓
→ Server performs Final Validation:
    • Valid PDF Magic Number?
    • PO Number Present?
    ├──> If any invalid → reject & delete → return error
    └──> If all valid → continue
  ↓
Generate submission_id (e.g., sub_a1b2c3d4)
  ↓
Move files to permanent storage (e.g., MinIO)
  ↓
Generate Final JSON Job Message with metadata + file paths
  ↓
Publish message to RabbitMQ queue
  ↓
→ Server returns "Success" response to UI
  ↓
──────────────────── Phase 5: Deep Analysis ───────────────
  ↓
Worker picks message from RabbitMQ queue
  ↓
→ Downloads files from MinIO
  ↓
Convert PDF to high-res image
  ↓
Image Preprocessing:
  • Deskew
  • Binarize
  • Noise Reduction
  ↓
OCR Engine extracts text + positions (bounding boxes)
  ↓
AI Structuring Model processes:
  • Key-Value Pair Extraction
  • Table Recognition
  • Logical Value Assignment (e.g., Grand Total)
  ↓
Aggregate structured data for entire submission
  ↓
→ Format final output (e.g., standardize dates)
  ↓
End
```
### 2.  Cross-Verification Engine
The first layer of validation. The engine acts as a diligent auditor, comparing the extracted data against internal business records and ensuring consistency across the submitted documents.
-   Match bills with **Purchase Orders (PO)** to check for budget and line-item discrepancies.
-   Verify attendance data against **manpower deployed** as per the PO.
-   Validate **bank statements/salary payments** against claimed labor costs.
-   Confirm **milestone/completion certificates** are present and match the invoiced claims.

  ### 🔍 Cross Verification Workflow

This flow ensures all invoices are valid, justified, and aligned with the Purchase Order, attendance, payments, and milestone documentation.

```text
Start
  ↓
──────────── 1. Match Invoice with PO ─────────────
  ↓
Fetch extracted_data (PostgreSQL) & po_data (ERP)
  ↓
Define Tolerance for Total Amount (e.g., 0.5%)
  ↓
Compare Invoice Total vs PO Total (with tolerance)
  ├──> If Exceeds → FAIL: "Invoice total exceeds PO"
  └──> If Within Limit → PASS
  ↓
Loop Through Invoice Line Items
  ↓
→ For Each Item:
   ├── Find Matching PO Line Item (using fuzzy match)
   ├── Compare rate and quantity
   └── Append Result: PASS / FAIL (with reason)
  ↓
Compile Results into JSON Step Report
  ↓
──────── 2. Verify Attendance vs PO Manpower ────────
  ↓
Fetch extracted_data['attendance_reports'] & po_data
  ↓
Aggregate Total Employees from Attendance Reports
  ↓
Compare total_employees vs PO required_manpower_count
  ├──> If Overstaffed → FAIL: "Manpower exceeds PO"
  └──> Else → PASS
  ↓
Compile Attendance Check Report
  ↓
─────── 3. Validate Salary Payments vs Billing ───────
  ↓
Fetch billed_employees from MPR/invoice
  ↓
Fetch paid_employees from salary proofs (bank data)
  ↓
Find Discrepancies: billed - paid → unpaid_employees
  ↓
If unpaid_employees exists:
  ├──> FAIL: List of names without salary proof
  └──> Else → PASS
  ↓
Compile Salary Validation Report
  ↓
────── 4. Confirm Completion Certificates (Milestones) ──────
  ↓
Fetch extracted_data & invoice line items
  ↓
Scan Descriptions for Keywords (milestone, phase, delivery)
  ↓
If Keywords Detected:
  ├──> Check if Certificate Exists
        ├── If Missing → FAIL: "No certificate provided"
        └── If Present → Compare Certificate & Line Item Description
            ├── If Match → PASS
            └── If Mismatch → FAIL: "Milestone does not match certificate"
  ↓
Compile Milestone Check Report
  ↓
────────────── Final Output ──────────────
→ Aggregate All Step Reports
→ Output Final Cross Verification JSON
→ Continue to Next Phase (Objection Analysis)
  ↓
End
```

### 3.  Objection-Aware Validation
The second layer of validation. This module acts as an experienced risk analyst, flagging submissions that, while technically correct, are suspicious based on historical patterns.
-   Flag objections based on a vendor's **historical data**, identifying chronic issues, anomalous billing behavior, and high-risk attributes.

  ### 🚨 Objection-Aware Validation Workflow

This process runs periodically via a cron-triggered script (`objection_engine.py`) and performs deep analysis on already-verified submissions using historical and statistical patterns.

```text
Start
  ↓
──────────── 1. Fetch Submissions for Objection Analysis ─────────────
  ↓
Connect to PostgreSQL
  ↓
Query:
SELECT submission_id, vendor_id, verification_report, extracted_data
FROM submissions
WHERE status = 'Pending Review'
AND verification_report->>'objections_processed' IS NULL;
  ↓
Loop Through Each Pending Submission
  ↓
──────────── 2. Historical Analysis (Per Submission) ─────────────
  ↓
Load: submission_id, vendor_id, extracted_data, verification_report
  ↓
▶️ Sub-Step A: Chronic Failure Analysis
  ↓
For each FAIL in verification_report:
  ├── Query past similar failures for the same vendor
  ├── If failure count > threshold:
  └── Create objection: { type: "Chronic Violation", detail: ... }

▶️ Sub-Step B: Statistical Anomaly Analysis
  ↓
Fetch all historical invoice totals for vendor_id
  ↓
Convert to pandas Series → Calculate Mean & Std Dev
  ↓
If current total > 3×std_dev from mean:
  └── Create objection: { type: "Anomalous Behavior", detail: ... }

▶️ Sub-Step C: High-Risk Attribute Check
  ↓
Look for risky attributes (e.g., 'Miscellaneous Fees') in line items
  ↓
Fetch historical rejection rate for that attribute
  ↓
If risk is high:
  └── Create objection: { type: "High-Risk Attribute", detail: ... }

──────────── 3. Merge & Save Objection Results ─────────────
  ↓
Compile objections:
objections_found = [
  { "type": "...", "detail": "..." },
  ...
]
  ↓
Prepare JSON Merge Payload:
{
  "objections": objections_found,
  "objections_processed": true
}
  ↓
PostgreSQL Query:
UPDATE submissions
SET verification_report = verification_report || %s::jsonb
WHERE submission_id = %s;
  ↓
Commit the changes
  ↓
Repeat for next submission
  ↓
End
```

### 4.  Vendor Pre-Submission Alerts
A proactive module designed to improve first-time submission quality by preventing errors before they happen.
-   Provides a real-time, interactive feedback loop on the vendor portal.
-   Notifies vendors of **missing documents, data inconsistencies, signature errors, or GST number mismatches** *before* they are allowed to finalize their submission.

### 5.   Penalty & SLA Compliance
The final layer of financial control. The engine automatically calculates and applies contractual financial penalties.
-   Detect contract penalties for **delays, manpower shortfalls, and quality issues**.
-   Calculate penalties as per **RFP, Work Order, or SLA clauses**.
-   Automatically detect and apply any **penalty waivers** to adjust final deductions.

### 6.  Compliance Document Validation
Ensures all foundational legal and compliance documents are in order.
-   Validate the integrity and validity of **Bank Guarantees** and **Work Orders**.
-   Check for **bill validity** and detect potential **duplicate submissions** across the system.

---

##  System Workflow


```text
Start
  ↓
Document Intake
  ↓
Pre-Verification & Alerts (Vendor Portal)
  ↓
Data Extraction (RabbitMQ + AI OCR + MinIO)
  ↓
Cross-Verification (ERP & PO Matching)
  ↓
Objection & Penalty Analysis (Anomalies, SLA, Contracts)
  ↓
Approval Workflow
    ├──> No Issues → Human Check → Auto-Approve → Payment Processing
    └──> Issues Found → Dashboard Review → Manual Resolution
  ↓
Integration with ERP/Accounting Systems (APIs)
  ↓
Continuous Learning (User Feedback → AI Model Retraining)
  ↓
End
```


The platform operates on a sophisticated, event-driven workflow designed for scalability and reliability.


**1. Document Intake:**
-   Invoices and supporting documents are received through various channels, with the primary channel being a secure, on-premises **Vendor Portal**.

**2. Pre-Verification & Alerts (Vendor Portal):**
-   If submitted via the portal, a real-time validation engine performs a "pre-flight check." It alerts the vendor of any immediate errors (missing documents, signature issues), preventing incorrect submissions from entering the system.

**3. Data Extraction (Asynchronous Processing):**
-   Upon successful submission, a job message is sent to a **RabbitMQ** processing queue.
-   A Python-based worker service picks up the job, retrieves the documents from **MinIO** object storage, and feeds them into the AI engine.
-   The Deep Learning model performs integrated OCR and data structuring, outputting clean JSON.

**4. Cross-Verification:**
-   The system matches the extracted data against POs and other records fetched from the primary business database (ERP). Discrepancies are flagged.

**5. Objection & Penalty Analysis:**
-   The AI analyzes the invoice against all historical data in the **PostgreSQL** database to flag statistical anomalies and suspicious patterns.
-   It then checks for any applicable penalties or SLA violations based on stored contract terms.

**6. Approval Workflow:**
-   **Straight-Through Processing:** If zero discrepancies or objections are found, the invoice is automatically flagged as "Approved" and sent for payment processing.
-   **Exception Handling:** If any issues are flagged, the invoice and its detailed verification report are routed to the appropriate personnel via a user-facing dashboard for manual review and resolution.

**7. Integration with Core Systems:**
-   The entire system is designed with APIs to integrate seamlessly with existing **Enterprise Resource Planning (ERP)** and accounting systems for data synchronization and financial record-keeping.

**8. Continuous Learning:**
-   The system architecture includes feedback loops where user actions (e.g., overriding a flag, rejecting an invoice) are logged. This data is used to periodically re-train and improve the accuracy of the AI models and the effectiveness of the objection and fraud detection capabilities.

---

##  Technology Stack

This project is built with a focus on on-premises deployment, security, and scalability.

-   **Backend:** Python (Flask/Django)
-   **AI/ML:** PyTorch, LayoutLM, OpenCV, Tesseract
-   **Database:** PostgreSQL (with JSONB support)
-   **Message Queue:** RabbitMQ
-   **File Storage:** MinIO (S3-Compatible Object Storage)
-   **Frontend Dashboard:** React / Angular / Vue.js
-   **Deployment:** Docker, Cron (for scheduled tasks)

---
