# Intelligent Bill Verifier

##  Scope of the Project

This project automates the verification process through five core modules of intelligence:

### 1.  Invoice & Supporting Document Extraction
The foundation of the platform. The system ingests and understands a wide array of document types submitted as a single package.
-   **Parses:** Invoices, Manpower Reports (MPR), Attendance Reports, Salary Proofs, Completion Certificates, and more.
-   **Technology:** A Deep Learning model with integrated OCR capabilities (based on LayoutLM architecture) for high-accuracy, context-aware data extraction.

### 2.  Cross-Verification Engine
The first layer of validation. The engine acts as a diligent auditor, comparing the extracted data against internal business records and ensuring consistency across the submitted documents.
-   Match bills with **Purchase Orders (PO)** to check for budget and line-item discrepancies.
-   Verify attendance data against **manpower deployed** as per the PO.
-   Validate **bank statements/salary payments** against claimed labor costs.
-   Confirm **milestone/completion certificates** are present and match the invoiced claims.

### 3.  Objection-Aware Validation
The second layer of validation. This module acts as an experienced risk analyst, flagging submissions that, while technically correct, are suspicious based on historical patterns.
-   Flag objections based on a vendor's **historical data**, identifying chronic issues, anomalous billing behavior, and high-risk attributes.

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
    ├──> No Issues → Auto-Approve → Payment Processing
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

### Pre-Submission Process

This flowchart outlines the enhanced vendor submission process, incorporating real-time pre-submission alerts to ensure high-quality data before deep analysis begins.

**[ Vendor Portal - Interactive Session ]**

1.  **Vendor Enters PO Number**
    `-->` Server fetches PO requirements in the background.

2.  **Vendor Drags & Drops PDF Files**
    `-->` JavaScript performs initial PDF-only format check.
        `-->` **[ If NOT PDF ]** --> Display immediate error message.
        `-->` **[ If PDF ]** --> Upload files to a temporary staging area.

3.  **Real-Time Pre-Submission Analysis (Server-Side "Quick Look")**
    `-->` AI performs high-speed checks:
        -   Document existence (e.g., Is the required certificate present?)
        -   Key field extraction (e.g., GST number, invoice total)
        -   Signature detection
        -   Basic consistency checks

4.  **Interactive Feedback Loop (Vendor Portal UI)**
    `-->` Display a checklist of results (`✅`, `⚠️`, `❌`).
    `-->` **"Submit" button remains DISABLED if there are critical errors (`❌`).**

5.  **Vendor Corrects Errors**
    `-->` Vendor sees `❌ Missing Document` and uploads the correct file.
    `-->` **[ Go back to Step 3 ]** - The system re-analyzes the new file.
    `-->` This loop continues until all checks pass (`✅`).

**[ Final Submission ]**

6.  **"Submit" Button is ENABLED**
    `-->` All pre-flight checks are now green (`✅`).

7.  **Vendor Clicks "Submit"**
    `-->` This triggers the main, in-depth processing workflow.

**[ Backend - Asynchronous Processing ]**

8.  **Server Finalizes Submission**
    `-->` Generates a permanent `submission_id`.
    `-->` Moves staged files to permanent storage (MinIO).
    `-->` Creates the final JSON Job Message with all metadata and file paths.

9.  **Send to Processing Queue**
    `-->` The JSON Job Message is published to RabbitMQ.
    `-->` An instant "Success!" message is sent back to the vendor's browser.

10. **Deep Analysis Begins**
    `-->` A worker service picks up the job from the queue to perform the full, multi-stage verification (Data Extraction, Cross-Verification, Objection Analysis, etc.).

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
