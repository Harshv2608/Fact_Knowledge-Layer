# Fact Knowledge Layer 🧠📊

> An evidence-backed knowledge layer for extracting, normalizing, and cross-validating facts from real-world documents.

## 📖 Overview

Most document-processing systems stop at:
`PDF → text → summary`

That is not enough when the important question is:
*"What exactly does this document claim, where does that claim come from, and how does it compare with what other documents say?"*

**Fact Knowledge Layer** treats extracted information as structured, evidence-backed facts rather than isolated pieces of generated text. 

The system ingests PDFs, extracts semantic and numerical facts, preserves their source evidence, normalizes values and temporal context, retrieves potentially related facts, and determines whether those facts are:
- 🟢 **Corroborated**
- 🔴 **Contradictory**
- 🟡 **Apparently contradictory but explainable by context**
- ⚠️ **Unable to be reliably resolved**

**The central design principle is simple:**
> *A fact is useful only when its evidence and context are preserved.*

---

## 🎥 Video Demo
[**Link to 3-Minute Video Demo**](#) *(Replace with actual YouTube/Loom link)*

---

## 🤔 Why this project exists

Consider three reports discussing India's economy.

One document might say:
> *Real GDP growth was 6.5% in FY2024/25.*

Another might report:
> *Real GDP growth remained at 6.5%.*

At first glance, these are easy to reconcile. But consider:
- **Document A:** Inflation = 4.9% (Period = Apr–Dec 2024)
- **Document B:** Inflation = 4.6% (Period = FY2024/25)

These numbers are not necessarily contradictory. They refer to different time windows. A naive comparison system may flag `4.9 ≠ 4.6 → CONTRADICTION`.

Fact Knowledge Layer instead attempts to reason over:
`value + unit + time + scope + geography + qualifiers + source evidence`

This distinction is the core of the project.

---

## 🏗️ What the system does

```mermaid
flowchart TD
    A[📄 PDF Files] --> B[⚙️ PDF Ingestion <br> <i>pdfplumber / PyMuPDF</i>]
    B --> C[🗂️ Chunk + Page Context]
    C --> D[🧠 Structured Extraction <br> <i>Gemini 3.6 Flash</i>]
    D --> E[📐 Fact Normalization <br> <i>value • unit • time • scope</i>]
    E --> F[🔗 Evidence / Provenance <br> <i>Doc → Page → Chunk → Fact</i>]
    F --> G[(🐘 PostgreSQL + pgvector <br> <i>Facts + Embeddings</i>)]
    G --> H[🔍 Candidate Retrieval <br> <i>Semantic Top-K Search</i>]
    H --> I[🤝 Relationship Analysis <br> <i>Deterministic + Semantic</i>]
    I --> J[💻 API + Web Interface <br> <i>Facts / Evidence / Cases</i>]
```

### Core Capabilities

#### 1. PDF Ingestion
The system accepts new PDF documents rather than relying on document-specific rules. The ingestion layer extracts page-level text, preserves page boundaries, handles PDFs using `pdfplumber` (falling back to `PyMuPDF`), and creates processable chunks. The goal is to answer: *"Where did this fact come from?"*

#### 2. Structured Fact Extraction
Facts are represented as structured JSON objects:
```json
{
  "subject": "India",
  "predicate": "real GDP growth",
  "value": 6.5,
  "unit": "%",
  "time_context": "FY2024/25",
  "geography": "India",
  "confidence": 0.94
}
```

#### 3. Evidence-First Provenance
Every extracted fact is linked back to its exact source string. 
`Document → Page → Chunk → Fact → Evidence`

#### 4. Evidence Validation
The pipeline does not blindly trust the model. Extracted evidence is checked against the source text using deterministic validation.
> *The model proposes the fact. The source document remains the authority.*

#### 5. Normalization
Documents express quantities differently (e.g., `6.5%`, `0.065`, `₹1.2 trillion`). Normalization converts representations into comparable float forms while retaining the original text.

#### 6. Temporal Reasoning
Time is treated as part of the fact. `FY2024/25` is parsed to `April 2024 → March 2025`. The system considers `metric + value + period + scope + unit` before attempting to classify a relationship.

#### 7. Relationship Discovery
Comparing every fact against every other fact is $O(N^2)$. The system uses a staged approach: **Top-K semantic candidates** via vector search are retrieved first, followed by deterministic filtering.

#### 8. Relationship Reasoning
The system distinguishes between situations instead of forcing a binary `TRUE/FALSE`:
| Relationship | Meaning |
| :--- | :--- |
| **Corroborated** | Independent sources support substantially the same fact |
| **Contradicted** | Sources make incompatible claims under comparable context |
| **Reconciled** | Values differ, but the difference is explainable by context |
| **Unresolved** | Evidence is insufficient to safely determine the relationship |

---

## 🧪 The Four Required Demo Cases

| Case | What it tests | Description |
| :--- | :--- | :--- |
| 🟢 **Corroboration** | Independent Support | Two sources independently support the same fact. |
| 🔴 **Contradiction** | Incompatible Claims | Sources make genuinely incompatible claims despite normalizations. |
| 🟡 **Reconciliation** | Contextual Explanation | Apparent disagreement is explained by differing time frames, units, or scopes. |
| ⚠️ **Failure/Uncertainty** | Ambiguous Evidence | Extraction or reasoning cannot safely resolve the case. Uncertainty is exposed for human review. |

---

## 🚀 Setup and Run Instructions

### Prerequisites
- **Python 3.11+**
- **Node.js 20+**
- **Docker + Docker Compose**
- **Gemini API key** for live extraction/reasoning

### Quickstart

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Harshv2608/Fact_Knowledge-Layer.git
   cd Fact_Knowledge-Layer
   ```

2. **Environment Variables:**
   Create a `.env` file in the root based on `.env.example`:
   ```env
   GEMINI_API_KEY=your_key_here
   DATABASE_URL=postgresql://admin:admin@fact_db:5432/factdb
   ```
   *(Note: Set `MOCK_LLM=1` in the backend if you wish to bypass the real LLM and run mock deterministic tests without consuming quota).*

3. **Start the Stack (Docker):**
   ```bash
   docker compose up --build -d
   ```

4. **Access the Application:**
   - **Frontend UI:** `http://localhost:3000`
   - **Backend API:** `http://localhost:8000/api`
   - **Database:** PostgreSQL on port `5432`

---

## 🏗️ Architecture & Important Decisions

### Separation of Concerns
The architecture deliberately separates the LLM from Deterministic Layers. 
- **LLM Responsibilities**: Semantic fact extraction, interpretation of complex language, relationship reasoning where deterministic rules are insufficient.
- **Deterministic Responsibilities**: PDF processing, evidence validation, normalization, vector candidate filtering, persistence.

### PostgreSQL + pgvector
A dedicated vector database was avoided to prevent infrastructure bloat. PostgreSQL provides relational persistence, structured querying, and metadata filtering, while `pgvector` handles semantic similarity search perfectly.

### Trade-offs
- **Batch Processing vs Real-Time:** Fact extraction is processed in background task threads. This prevents the API from timing out on massive PDFs, but requires users to refresh the UI to see incoming facts.
- **Table Parsing:** Basic text-flow extraction is prioritized. Complex tables with deep hierarchical headers spanning multiple pages might lose structural context.

---

## 🤖 AI Tools Used
**Google Antigravity (AGY)** was used as an engineering copilot during development for scaffolding, implementation assistance, debugging, test generation, and documentation. The project architecture and validation requirements remained explicitly defined at the engineering level. 

**Gemini 3.6 Flash** handles native structured fact extraction and contextual relationship reasoning via the API.

---

## 🚧 Limitations & Next Steps
What does not work perfectly yet, and what I would build next:
- **Layout-aware Table Extraction:** PDFs do not contain semantic tables. Multi-page tables currently disrupt data extraction.
- **Footnote Association:** Values often depend on spatially separated footnotes. I would build a linking mechanism.
- **Durable Background Jobs:** Replacing the native `ThreadPoolExecutor` with a dedicated queue like Celery/Redis for robust retry policies.
- **Hybrid Retrieval:** Implementing hybrid lexical (BM25) + vector retrieval.
- **Human-in-the-Loop:** Allowing users to manually override `UNCERTAIN` relationship logic.

---

## 👨‍💻 Author
**Harsh Vardhan**  
B.Tech — Electronics and Computer Engineering, VIT Chennai  
GitHub: [Harshv2608](https://github.com/Harshv2608)  

> *Final Note: This project is intentionally designed around a simple idea: Don't just extract what a document says. Preserve enough evidence and context to understand why that statement should—or should not—be considered compatible with what other documents say. That turns a PDF parser into an evidence-backed factual knowledge layer.*
