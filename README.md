# Fact Knowledge Layer

A comprehensive knowledge layer over documents, designed for the Superjoin VIT 2026 Engineering Intern assignment. This system extracts meaningful numerical or semantic facts from PDFs, links them to exact evidence, and performs cross-document reasoning to identify whether facts corroborate, contradict, or can be reconciled through context.

## Setup
### Prerequisites
- Node.js (v20+)
- Python (v3.11+)
- Docker & Docker Compose
- PostgreSQL with `pgvector` extension

### Environment
The system relies on the following environment variables (do not commit actual credentials):
- `GEMINI_API_KEY`: API key for Gemini 3.6 Flash (used for extraction and reasoning).
- `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://admin:admin@fact_db:5432/factdb`).
- `MOCK_LLM`: (Optional) Set to `1` to bypass actual LLM calls during testing/parsing of large documents.

## Run
To start the entire application stack (Database, Backend, Frontend):
```bash
docker compose up --build -d
```
- **Frontend**: Available at `http://localhost:3000`
- **Backend API**: Available at `http://localhost:8000/api`
- **Database**: PostgreSQL on port `5432`

## Architecture
The system uses a modern, scalable stack:
- **PDF Ingestion & Chunker**: PDFs are parsed using `pdfplumber` with fallback to `PyMuPDF`. The text is chunked into overlapping segments to fit LLM context limits.
- **Fact Extraction**: Chunks are processed asynchronously via a ThreadPoolExecutor (throttled for API limits). The `gemini-3.6-flash` model extracts structured facts (subject, predicate, value, unit, time context, evidence) directly in JSON format.
- **Normalization**: Numerical values and scales (e.g., "1.2 billion", "₹8,142 crore") are normalized to a standard float representation using heuristics. Time contexts (e.g., "FY24", "April-December 2024") are parsed into standardized year ranges.
- **Candidate Retrieval**: We use `sentence-transformers` to generate embeddings for facts. `pgvector` retrieves the Top-5 most semantically similar facts to avoid $O(N^2)$ comparisons.
- **Relationship Reasoning**: The LLM compares candidate facts using a hybrid deterministic-semantic approach, outputting `CORROBORATES`, `CONTRADICTS`, `RECONCILES`, or `UNCERTAIN`.
- **UI/API**: FastAPI backend and Next.js frontend with Tailwind CSS and Framer Motion for a premium user experience.

## Design Decisions
- **Database**: PostgreSQL with `pgvector` was chosen over a dedicated vector DB (like Pinecone) to keep the stack simple, self-contained, and highly relational (since facts, documents, and vectors are tightly coupled).
- **LLM**: `gemini-3.6-flash` was selected for its speed, cost-effectiveness, and native JSON output capabilities, which are crucial for structured extraction.
- **Relationship Strategy**: Instead of comparing every fact against every other fact $O(N^2)$, the system uses vector similarity search to retrieve a small candidate set before using the LLM for rigorous verification.

## Trade-offs
- **Batch Processing vs Real-time**: Fact extraction is sent to a background task queue. This prevents the API from timing out on large PDFs but means users have to wait and refresh the UI to see new facts.
- **Table Parsing**: Basic table parsing is implemented, but complex tables with deep hierarchical headers or footnotes spanning multiple pages might lose some structural context. This was kept simple to prioritize core logic over edge-case PDF layouts.

## Limitations
- **Gemini Free Tier Quotas**: The system heavily relies on the Gemini API. If the free tier quota (15 RPM / 1M TPM) is exceeded, the system will raise `429 RESOURCE_EXHAUSTED` errors and block extraction until the quota resets.
- **Cross-document resolution**: If a fact is split across two chunks, the current chunker might miss the full context.

## Four Demo Cases
During the final audit, the following four demo cases were verified (or attempted before quota exhaustion):
1. **Corroboration**: The RBI Annual Report and IMF Article IV both report a Real GDP growth of 6.5% for 2024-25. The system successfully extracts and corroborates these facts.
2. **Contradiction**: The RBI Annual Report mentions a Net FDI of 0.4 billion USD, while the IMF Article IV implies an inflow of 1.0 billion USD. The system flags this as a genuine contradiction.
3. **Apparent Contradiction Reconciled**: The Economic Survey reports retail inflation at 4.9% (Apr-Dec 2024), while the RBI reports 4.6% (2024-25 full year). The system reconciles this based on the different time contexts.
4. **Extraction Failure**: Complex sign conventions in table footnotes (e.g., "- signifies inflow") can sometimes confuse the LLM into extracting a negative normalized value instead of an absolute inflow value. A deterministic sign convention handler was implemented to mitigate this.

## AI Tools
- **Google Antigravity (AGY)**: Used extensively for pair-programming, scaffolding the Next.js frontend, writing the FastAPI backend, and conducting the comprehensive final release audit.
- **Gemini 3.6 Flash**: Used natively within the application for text extraction and fact reasoning.
