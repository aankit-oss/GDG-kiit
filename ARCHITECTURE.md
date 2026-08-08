# LexAudit — Architecture

## Stack Choice

| Layer | Technology | Rationale |
|---|---|---|
| Backend | FastAPI (Python 3.11+) | Native async, Pydantic models, excellent AI/ML ecosystem, auto OpenAPI docs |
| Frontend | React + Vite + TypeScript | Fast dev server, minimal footprint, strong typing |
| Vector Store | ChromaDB (local) | No paid service, runs in-process, persistent, simple Python API |
| LLM (reasoning) | NVIDIA NIM — Llama-3.1-70B-Instruct | Free tier, strong instruction-following for legal reasoning |
| LLM (planning) | Google Gemini Flash | Permanent free tier, structured text generation |
| Document parsing | pypdf + python-docx | Pure Python, no binary deps, good metadata extraction |

### Known Limitations
- ChromaDB is local-only (not distributed). Single-node only. Acceptable for hackathon scope.
- No authentication layer — explicitly out of scope per PROJECT_MASTER §8.
- Rule library is capped at ~22 rules (15 DPDP + 7 Contract Act). Depth over breadth by design.
- LLM calls are sequential per rule (not parallelized) — acceptable latency for demo, optimize post-hackathon.

---

## Data Model

```mermaid
erDiagram
    DOCUMENT {
        string doc_id PK
        string filename
        string file_type
        datetime uploaded_at
        int total_chunks
    }
    CHUNK {
        string chunk_id PK
        string doc_id FK
        string text
        int page_number
        string section_title
        int chunk_index
    }
    RULE {
        string rule_id PK
        string act
        string title
        string description
        string check_prompt
        string severity
    }
    FINDING {
        string finding_id PK
        string doc_id FK
        string rule_id FK
        string chunk_id FK
        string verdict
        string evidence_text
        string reasoning
        datetime evaluated_at
    }
    AUDIT_REPORT {
        string report_id PK
        string doc_id FK
        string ruleset
        datetime generated_at
        int pass_count
        int fail_count
        int not_addressed_count
    }
    QA_RESPONSE {
        string response_id PK
        string doc_id FK
        string question
        string answer
        bool refused
        string refusal_reason
        datetime answered_at
    }
    CITED_CHUNK {
        string response_id FK
        string chunk_id FK
        float relevance_score
    }

    DOCUMENT ||--o{ CHUNK : contains
    DOCUMENT ||--o{ AUDIT_REPORT : generates
    AUDIT_REPORT ||--o{ FINDING : contains
    FINDING }o--|| RULE : evaluates
    FINDING }o--|| CHUNK : cites
    DOCUMENT ||--o{ QA_RESPONSE : answers
    QA_RESPONSE ||--o{ CITED_CHUNK : cites
    CITED_CHUNK }o--|| CHUNK : references
```

---

## Request Flow — Compliance Audit

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as Frontend (React)
    participant BE as Backend (FastAPI)
    participant ING as Ingestion
    participant VS as ChromaDB
    participant CA as Compliance Auditor Agent
    participant CGS as Citation Grounding Skill
    participant LLM as NVIDIA NIM

    U->>FE: Upload document + select ruleset
    FE->>BE: POST /api/documents/upload (multipart)
    BE->>ING: parse PDF/DOCX → chunks with metadata
    ING-->>BE: List[Chunk]
    BE->>VS: store chunks (embed + index)
    VS-->>BE: stored OK
    BE-->>FE: { doc_id }

    FE->>BE: POST /api/audit { doc_id, ruleset }
    BE->>CA: audit(chunks, rules)
    loop For each Rule
        CA->>CGS: ground(rule.check_prompt, chunks)
        CGS->>VS: query nearest chunks
        VS-->>CGS: top-k chunks
        CGS->>LLM: [system: auditor persona] evaluate chunk vs rule
        LLM-->>CGS: verdict + reasoning + evidence
        CGS-->>CA: GroundingResult(answer, cited_chunk_ids) OR Refusal
        CA->>CA: create Finding(rule_id, chunk_id, verdict, evidence_text, reasoning, timestamp)
    end
    CA-->>BE: List[Finding]
    BE->>BE: build AuditReport, persist
    BE-->>FE: AuditReport JSON
    FE->>U: Render pass/fail table with evidence quotes
```

---

## Request Flow — Grounded Q&A

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as Frontend (React)
    participant BE as Backend (FastAPI)
    participant VS as ChromaDB
    participant CGS as Citation Grounding Skill
    participant LLM as NVIDIA NIM

    U->>FE: Upload document (or select existing) + type question
    FE->>BE: POST /api/qa { doc_id, question }
    BE->>VS: query chunks for question
    VS-->>BE: top-k relevant chunks
    BE->>CGS: ground(question, chunks, threshold=0.7)
    alt Chunks found above threshold
        CGS->>LLM: answer question using only provided chunks
        LLM-->>CGS: answer + cited_chunk_ids
        CGS-->>BE: GroundingResult(answer, cited_chunks)
        BE-->>FE: QAResponse { answer, cited_passages, refused=false }
        FE->>U: Show answer + highlighted source passages
    else No relevant chunks / below threshold
        CGS-->>BE: Refusal(reason="No relevant content found in document")
        BE-->>FE: QAResponse { refused=true, refusal_reason=... }
        FE->>U: Show explicit refusal message
    end
```

---

## Audit Trail

Every `Finding` record stores:
- `chunk_id` — exact chunk used for evidence
- `evidence_text` — verbatim text from that chunk
- `reasoning` — LLM's explanation of verdict
- `evaluated_at` — ISO timestamp

This satisfies the "traceable and auditable" requirement. Reports are persisted to disk (JSON) and retrievable by `report_id`.
