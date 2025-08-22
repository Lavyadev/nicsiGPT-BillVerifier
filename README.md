# nicsiGPT:BillVerifier

##  System Workflow


```text
Start
  ↓
Document Intake
  ↓
Pre-Verification & Alerts (Vendor Portal)
  ↓
Data Extraction (RabbitMQ + LLM + MinIO)
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
-   The LLM model performs integrated OCR and data structuring, outputting clean JSON.

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


##  Scope of the Project

This project automates the verification process through five core modules of intelligence:

### 1.  Invoice & Supporting Document Extraction
The foundation of the platform. The system ingests and understands a wide array of document types submitted as a single package.
-   **Parses:** Invoices, Manpower Reports (MPR), Attendance Reports, Salary Proofs, Completion Certificates, and more.
-   **Technology:** An LLM model with integrated OCR capabilities for high-accuracy, context-aware data extraction.

### 🔁 Enhanced Document Ingestion Workflow (with Pre-Submission Alerts)

```text
Start
↓
────────────────── Phase 1: Staging Area ──────────────────
↓
Vendor Enters PO Number
↓
→ Server fetches PO requirements (e.g., required documents, vendor details).
↓
Vendor Drag-and-Drops PDFs (Invoice, MPR, Salary proofs).
↓
→ Client-side validation: only PDF allowed.
├──> If not PDF → show error → reject file.
└──> If PDF → upload to staging endpoint.
↓
Show "Analyzing..." spinner in UI for each file.
↓
──────────────── Phase 2: High-Speed Pre-Flight Check ────────────────
↓
→ Server triggers a Hybrid Pre-Flight Pipeline in Parallel.
↓
Parallel Real-Time Checks:
• Document Existence Check (Business Logic): Compares uploaded files against the PO's required document list.
• Signature Detection (Dedicated CV Model): A fast CV model checks for a signature on specific documents like certificates.
• Key Field Extraction (Lightweight LLM Call): For the invoice, the first page is sent to a fast, low-latency LLM (e.g., Gemini Flash) with a highly targeted prompt: "Extract vendor_gstin, invoice_total_amount, and vendor_name. Respond ONLY with JSON."
• Basic Consistency Check (Database Query): The extracted vendor_gstin is cross-referenced with the vendor's data in the database.
↓
→ Server consolidates results from all parallel checks and sends back a single JSON response with warnings/errors.
↓
──────────── Phase 3: Interactive Feedback Loop ───────────
↓
UI renders the real-time result checklist:
• ✅ Invoice Found
• ⚠ GST Mismatch: (Result from LLM + DB Check)
• ❌ Missing Completion Certificate: (Result from Business Logic Check)
• ✅ MPR Found
• ❌ Signature Not Detected: (Result from CV Model Check)
↓
"Submit" button remains DISABLED until all critical (❌) errors are resolved.
↓
Vendor Corrects Issues:
→ Uploads missing/corrected files.
→ System re-runs the specific check for the updated file.
→ UI updates checklist in real-time.
↓
→ Loop continues until all checks are ✅.
↓
────────────── Phase 4: Final Submission ────────────────
↓
"Submit" Button is ENABLED.
↓
Vendor clicks "Submit".
↓
→ Server performs Final Validation:
• Valid PDF Magic Number?
• PO Number Present?
├──> If any invalid → reject & delete → return error.
└──> If all valid → continue.
↓
Generate submission_id (e.g., sub_a1b2c3d4).
↓
Move files to permanent storage (e.g., MinIO).
↓
Generate Final JSON Job Message with metadata + file paths.
↓
Publish message to RabbitMQ queue.
↓
→ Server returns "Success" response to UI.
↓
──────────────────── Phase 5: Deep Analysis with LLM ───────────────
↓
Worker picks message from RabbitMQ queue.
↓
→ Downloads files from MinIO.
↓
Convert PDF pages to high-resolution images.
↓
Image Preprocessing:
• Deskew
• Binarize
• Noise Reduction
↓
Dynamic Prompt Engineering:
→ System constructs a detailed prompt defining the required JSON schema for all documents (invoices, line items, MPR tables, etc.).
↓
Multimodal LLM Execution:
→ The images and detailed prompt are sent to a powerful multimodal LLM (e.g., Gemini Pro) to perform comprehensive, context-aware data extraction.
↓
Response Validation & Sanitization:
→ The LLM's JSON response is parsed and validated against the requested schema.
→ Values are sanitized (e.g., text to numbers, date standardization).
↓
Aggregate structured data for the entire submission into a final, clean JSON object.
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

```text
Start
  ↓
──────────── 1. Trigger & Data Fetch ─────────────
  ↓
Trigger: Submission status = "Pending Review" OR "System Verified"
  ↓
Load from PostgreSQL:
  ├── submission_record (includes extracted_data & verification_report)
  ├── po_data (from ERP)
  └── sla_clauses (from ERP)
  ↓
Extract: submission_id, po_number

──────────── 2. Initialize Financial Summary ─────────────
  ↓
total_deductions = 0
deductions_detail = []

──────────── 3. Run Penalty Checks ─────────────
  ↓
▶️ Sub-Step A: Delay Penalty Check
  ↓
If milestone FAIL exists in verification_report:
  ├── Get completion_date (from extracted_data)
  ├── Get milestone_due_date (from po_data)
  ├── Get penalty_rate & grace_period (from sla_clauses)
  └── Calculate:
        penalty_days = (completion_date - due_date) - grace_period
        If penalty_days > 0:
          ├── penalty_amount = milestone_value × penalty_rate × penalty_days
          └── Append to deductions_detail:
              { type: "Late Delivery", amount: ..., reason: ... }
          Update total_deductions

  ↓
▶️ Sub-Step B: Manpower Shortfall Penalty
  ↓
If manpower FAIL exists in verification_report:
  ├── Get actual_manpower (from attendance)
  ├── Get authorized_manpower (from po_data)
  ├── Get per_person_penalty (from sla_clauses)
  └── Calculate:
        shortfall = authorized - actual
        penalty_amount = shortfall × per_person_penalty
        Append to deductions_detail:
          { type: "Manpower Shortfall", amount: ..., reason: ... }
        Update total_deductions

  ↓
▶️ Sub-Step C: Quality Issue Penalty
  ↓
Query Quality DB for complaints by po_number
  ↓
If complaint found:
  ├── Get penalty_percentage (from sla_clauses)
  ├── Get invoice_amount (from extracted_data)
  └── Calculate:
        penalty_amount = invoice_amount × penalty_percentage
        Append to deductions_detail:
          { type: "Quality Issue", amount: ..., reason: ... }
        Update total_deductions

──────────── 4. Apply Penalty Waivers ─────────────
  ↓
For each item in deductions_detail:
  ├── Check if waiver exists in sla_clauses["penalty_waivers"]
  └── If found:
        ├── Adjust penalty amount (e.g., reduce to 0)
        └── Update reason field with waiver note
        Recalculate total_deductions

──────────── 5. Finalize & Save ─────────────
  ↓
Prepare financial_summary JSON:
{
  "deductions": [...],
  "total_deductions": ...
}
  ↓
PostgreSQL Query:
UPDATE submissions
SET verification_report = jsonb_set(verification_report, '{financial_summary}', %s::jsonb)
WHERE submission_id = %s;
  ↓
Commit changes
  ↓
End
```


### 6.  Compliance Document Validation
Ensures all foundational legal and compliance documents are in order.
-   Validate the integrity and validity of **Bank Guarantees** and **Work Orders**.
-   Check for **bill validity** and detect potential **duplicate submissions** across the system.

```text
  Start
  ↓
──────────── 1. Trigger & Purpose ─────────────
  ↓
Trigger:
Part of Cross-Verification Engine — runs BEFORE penalties
  ↓
Purpose:
Catch CRITICAL failures in compliance documents (not financial issues)

──────────── 2. Execute Duplicate Submission Check ─────────────
  ↓
Extract:
  ├── vendor_id
  ├── extracted_invoice_number
  └── extracted_total_amount
  ↓
PostgreSQL Query:
SELECT submission_id FROM submissions
WHERE vendor_id = %s
AND extracted_data->'invoice'->>'invoice_number' = %s
AND extracted_data->'invoice'->>'total_amount' = %s;
  ↓
If rows returned:
  └── CRITICAL FAILURE:
      Set status = "Requires Manual Investigation"
      Reason = "Potential Duplicate of submission_id #XYZ"
      ↓
      STOP processing for this submission

──────────── 3. Execute Bill Validity Check ─────────────
  ↓
Extract:
  └── invoice_date (from extracted_data)
  ↓
Calculate:
  days_old = (today - invoice_date).days
  ↓
Compare with max_invoice_age (e.g., 90 days)
  ↓
If days_old > max_invoice_age:
  └── FAIL with reason: "Invoice is time-barred"

──────────── 4. Execute Work Order / Bank Guarantee Check ─────────────
  ↓
Check if work_order or bank_guarantee object exists in extracted_data
  ↓
If exists:
  ├── Extract expiry_date from document
  ├── If expiry_date < today → FAIL with reason: "Bank Guarantee expired"
  ↓
  ├── Extract order_value or guarantee_amount
  ├── Compare with required value in po_data
  └── If mismatch → FAIL with reason: "Mismatch in Guarantee/Order Value"

──────────── 5. Update Verification Report ─────────────
  ↓
For each check:
  └── Append result (PASS / FAIL + reason) to verification_report["standard_checks"]
  ↓
If any check FAILED:
  └── Set submission status = "Pending Review"

↓
End
```
---

## 📊 Data Requirements & Prerequisites

### 1. AI Model Training Data
This data is required **one-time** for the initial training and subsequent periodic re-training of the platform's custom Deep Learning models.

-   **Requirement:** A representative, historical sample for each *custom* document type that the system needs to process.
-   **Specification:** A minimum of **50-100 examples** for each document category. The dataset must be diverse, including documents from various vendors and of varying scan quality (both digital-native and scanned).
-   **Document Types:**
    -   [ ] Vendor Master Record
    -   [ ] Manpower Reports (MPRs)
    -   [ ] Completion Certificates
    -   [ ] Bank Guarantees
    -   [ ] Work Orders
    -   [ ] Salary Proofs / Bank Statements (Anonymized where necessary to protect PII)


---

### 2. Live Transactional Data (For Real-Time Verification)
This data is required for the day-to-day operation of the **Cross-Verification Engine**. The system needs real-time access to query this data.

-   **Requirement:** Access to the **Vendor Master** and **Purchase Order (PO)** data from the primary ERP or business management system.
-   **Specification:** An API endpoint or a read-only database user capable of fetching the following data structure when queried by a `po_number`:

    -   **Vendor Master Record:**
        -   `vendor_id`
        -   `vendor_name`
        -   `vendor_address`
        -   `vendor_gst_number`
        -   `vendor_bank_account_details`
    -   **Purchase Order Header:**
        -   `po_number`
        -   `po_total_value` (Total budget)
        -   `po_status` ('Approved', 'Closed', etc.)
        -   `milestone_due_date`
        -   `required_manpower_count`
        -   `po_category` ('Capital Project', 'Operational Expense', etc.)
    -   **Purchase Order Line Items:**
        -   An array of `approved_line_items`, each containing:
            -   `item_code` (if applicable)
            -   `description`
            -   `quantity_approved`
            -   `rate_approved`

---

### 3. Contractual & Compliance Data
This data is required for the **Penalty & SLA Compliance Engine** to automatically enforce contractual terms.

-   **Requirement:** Access to structured data defining the rules of the contract.
-   **Specification:** For a given PO or Contract ID, the system must be able to retrieve:
    -   **SLA Penalty Clauses:** A structured list of penalty rules (e.g., JSON object) containing:
        -   Rules for `late_delivery_penalty` (type, value, grace period).
        -   Rules for `manpower_shortfall_penalty` (type, value).
        -   Rules for `quality_issue_penalty` (type, value).
    -   **Penalty Waivers:** A list of any pre-approved, active waivers, including the type of penalty waived and the amount/duration.
    -   **Business Rules:** Key operational rules, such as `max_invoice_age_for_submission` (e.g., 90 days).

---

### 4. Ancillary Operational Data
This data is required for specific, advanced validation checks.

-   **Requirement:** Access to any internal systems that log service quality or operational issues.
-   **Specification:** Read-only access to the **Internal Quality Issues Log**. The system needs to be able to query this log by `po_number` to check for any open complaints or documented service failures that may trigger a quality-related penalty.

---

##  Technology Stack

This project is built with a focus on on-premises deployment, security, and scalability.

-   **Backend:** Python (FastAPI)
-   **AI/ML:** Llama3, OpenCV, Tesseract
-   **Database:** PostgreSQL (with JSONB support)
-   **Message Queue:** RabbitMQ
-   **File Storage:** MinIO (S3-Compatible Object Storage)
-   **Frontend Dashboard:** Streamlit
-   **Deployment:** Docker, Cron (for scheduled tasks)

---
