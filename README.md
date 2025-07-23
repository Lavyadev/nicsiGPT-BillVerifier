# Intelligent Bill Verifier

An AI-powered, end-to-end platform designed to automate the entire lifecycle of vendor bill processing, from submission and data extraction to verification, compliance, and payment approval.

## The Problem: The Hidden Costs of Manual Bill Processing

In many large-scale operations, particularly those involving contract labor and milestone-based projects, processing vendor invoices is a slow, manual, and error-prone process. This traditional workflow creates significant operational bottlenecks and financial risks, including:

*   **High Operational Overhead:** Accounts Payable (AP) teams spend countless hours manually cross-referencing invoices with purchase orders, attendance sheets, and completion certificates.
*   **Costly Human Errors:** Manual data entry and verification inevitably lead to mistakes, resulting in overpayments, underpayments, and duplicate payments.
*   **Delayed Payments:** The slow and inefficient process can delay payments to vendors, straining business relationships and potentially incurring late fees.
*   **Revenue Leakage:** Without automated checks, penalties for SLA violations (like delays or manpower shortfalls) are often missed, leading to direct financial loss.
*   **Lack of Insight:** Manual processes make it impossible to analyze vendor behavior, identify patterns of non-compliance, or spot fraudulent activity over time.

This project aims to solve these problems by replacing the manual workflow with an intelligent, automated, and data-driven system.

---

## Project Scope & Core Features

This platform is composed of five intelligent modules that work in concert to deliver a complete automation solution:

1.  **Invoice & Supporting Document Extraction:**
    *   Leverages AI-powered OCR and Deep Learning to accurately parse a wide range of documents, including invoices, Manpower Reports (MPR), attendance sheets, salary proofs, and completion certificates.

2.  **Vendor Pre-Submission Alerts:**
    *   An interactive, real-time "pre-flight check" that validates documents *before* final submission. It notifies vendors of missing documents, inconsistent data, or signature errors, drastically improving the quality of submissions and reducing back-and-forth communication.

3.  **Cross-Verification Engine:**
    *   The core automated auditor that matches extracted bill data against business records. It verifies invoice amounts against Purchase Orders (POs), attendance against manpower deployed per the PO, and confirms the existence and validity of supporting documents like milestone certificates.

4.  **Objection-Aware Validation:**
    *   A risk analysis engine that goes beyond simple rule-based checks. It analyzes a vendor's historical data to flag statistical anomalies, chronic rule violations, and other patterns that might indicate a hidden issue, even if the submission appears correct on the surface.

5.  **Penalty & SLA Compliance:**
    *   The financial enforcement module. It automatically detects contractual penalties for issues like project delays, manpower shortfalls, or quality problems. It calculates these deductions as per the contract/SLA and adjusts the final payable amount.

---

## System Architecture & Workflow

The system is built on a microservices architecture to ensure scalability and separation of concerns. The core services are:

1.  **Portal Frontend (`portal_frontend`):** A React/Vue-based interface for vendors to upload their documents. It handles the real-time Pre-Submission Alert workflow.
2.  **API Server (`api_server`):** A backend service (Python/Flask) that supports the frontend, handles user authentication, and performs the real-time "quick look" analysis. It is also responsible for creating and queueing the main processing job.
3.  **Document Worker (`document_worker`):** The main asynchronous AI engine. It consumes jobs from the queue and performs full OCR, data extraction, and standard cross-verification.
4.  **Objection Engine (`objection_engine`):** A separate, scheduled service that runs periodically to analyze verified submissions and flag historical objections.
5.  **Shared Infrastructure (via Docker Compose):**
    *   **PostgreSQL:** The primary database.
    *   **RabbitMQ:** The message queue for managing asynchronous jobs.
    *   **MinIO:** On-premises object storage for all documents.

### System Flowcharts

#### 1. Vendor Pre-Submission & Ingestion Flow

This chart illustrates the real-time, interactive workflow the vendor experiences *before* a submission is finalized, preventing errors at the source.

![Vendor Pre-Submission Flow](https://i.imgur.com/gYd5z9a.png)

#### 2. Backend Asynchronous Processing Flow

This chart illustrates the entire backend pipeline that begins *after* the vendor clicks the final "Submit" button. It shows the interaction between the different microservices as they perform extraction, verification, and analysis.

![Backend Processing Flow](https://i.imgur.com/k6lPqQ7.png)

---

## Repository Structure

```
Intelligent-Bill-Verifier/
├── docs/
│   ├── architecture.md
│   ├── pre_submission_flow.png
│   └── backend_processing_flow.png
│
├── services/
│   ├── api_server/
│   ├── portal_frontend/
│   ├── document_worker/
│   └── objection_engine/
│
├── .env.example
├── docker-compose.yml
└── README.md
```
*(For a detailed file structure, please refer to the `docs/architecture.md` file.)*

---

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Intelligent-Bill-Verifier.git
    cd Intelligent-Bill-Verifier
    ```
2.  **Configure Environment:**
    *   Copy `.env.example` to `.env`.
    *   Fill in the necessary credentials for PostgreSQL, RabbitMQ, etc.
3.  **Run the System:**
    ```bash
    docker-compose up --build
    ```
This will build and run all the containerized services. The vendor portal will be available on `http://localhost:3000`, and the backend API on `http://localhost:5000` (or as configured).
