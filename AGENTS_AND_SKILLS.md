# AGENTS_AND_SKILLS.md — Custom Agent & Custom Skill Documentation

---

## Custom Agent — "Compliance Auditor Agent"

**File**: `backend/agents/compliance_auditor.py`  
**Class**: `ComplianceAuditorAgent`

### Identity & Persona

The Compliance Auditor Agent is a named, distinct agent with a baked-in system prompt that governs its reasoning. It is not a general-purpose chat assistant — it has one job: evaluate document chunks against legal rules and produce structured Findings.

**System Prompt (embedded):**
```
You are LexAudit's Compliance Auditor. Your role is to evaluate whether a document clause
satisfies a specific legal rule.

HARD CONSTRAINTS:
1. You MUST quote the exact source text you are evaluating. Never paraphrase as if it were a quote.
2. You MUST state a verdict of exactly one of: PASS, FAIL, or NOT_ADDRESSED.
3. If no relevant text exists in the provided chunks, verdict MUST be NOT_ADDRESSED — never guess.
4. Your reasoning must explain WHY the clause passes or fails the rule, citing specific legal requirements.
5. Never assert a verdict without evidence from the provided document chunks.
```

### Interface

```python
class ComplianceAuditorAgent:
    def audit(
        self,
        doc_id: str,
        chunks: List[Chunk],
        rules: List[Rule],
    ) -> AuditReport:
        """
        Evaluate each rule against the document chunks.
        Returns an AuditReport containing one Finding per rule.
        Each Finding contains: rule_id, chunk_id, verdict, evidence_text, reasoning, evaluated_at.
        """
```

### Inputs
| Parameter | Type | Description |
|---|---|---|
| `doc_id` | `str` | Identifier of the document being audited |
| `chunks` | `List[Chunk]` | All text chunks from the document with metadata |
| `rules` | `List[Rule]` | Rules to evaluate (loaded from YAML rule library) |

### Outputs
| Field | Type | Description |
|---|---|---|
| `report_id` | `str` | Unique audit report ID |
| `doc_id` | `str` | Document audited |
| `ruleset` | `str` | Rule set name (e.g., `dpdp_2023`) |
| `findings` | `List[Finding]` | One Finding per rule |
| `generated_at` | `datetime` | ISO timestamp |

### Finding Schema
```json
{
  "finding_id": "f_uuid",
  "rule_id": "DPDP-001",
  "chunk_id": "chunk_uuid",
  "verdict": "PASS | FAIL | NOT_ADDRESSED",
  "evidence_text": "verbatim quoted text from the chunk",
  "reasoning": "why this clause passes/fails the rule",
  "evaluated_at": "2026-08-08T12:00:00Z"
}
```

### What makes it a distinct agent (not just a prompt string)
- Named class with its own system prompt baked in — cannot be bypassed.
- Uses the Citation Grounding Skill internally — enforces grounding at the skill layer too.
- Produces typed, validated Pydantic models (not raw text).
- Has its own retry/fallback logic for LLM calls.

---

## Custom Skill — "Citation Grounding Skill"

**File**: `backend/skills/citation_grounding.py`  
**Class**: `CitationGroundingSkill`

### Purpose

A reusable skill that answers a question (or evaluates a prompt) using **only** the provided document chunks. Returns a grounded answer with cited chunk IDs, or an explicit refusal if the content is not found.

This skill is **reused by both**:
1. The Compliance Auditor Agent (for rule evaluation)
2. The Q&A router (for user questions)

This reuse is what makes it a skill — not a one-off script.

### Interface

```python
@dataclass
class GroundingResult:
    answer: str
    cited_chunk_ids: List[str]
    cited_texts: List[str]
    confidence: float
    refused: bool
    refusal_reason: Optional[str]

class CitationGroundingSkill:
    def ground(
        self,
        question: str,
        chunks: List[Chunk],
        threshold: float = 0.7,
        max_chunks: int = 5,
    ) -> GroundingResult:
        """
        Ground an answer in the provided chunks.
        
        Returns GroundingResult with:
        - answer: the grounded answer (if not refused)
        - cited_chunk_ids: IDs of chunks used as evidence
        - cited_texts: verbatim text of those chunks
        - confidence: float 0.0–1.0
        - refused: True if no relevant content found
        - refusal_reason: explanation if refused
        
        GUARANTEES:
        - If refused=False, cited_chunk_ids is always non-empty.
        - The answer never contains information not present in cited chunks.
        - If similarity score of best chunk < threshold, refused=True always.
        """
```

### Inputs
| Parameter | Type | Default | Description |
|---|---|---|---|
| `question` | `str` | required | The question or rule check prompt |
| `chunks` | `List[Chunk]` | required | Candidate chunks to search |
| `threshold` | `float` | `0.7` | Minimum relevance score to answer (vs. refuse) |
| `max_chunks` | `int` | `5` | Max chunks to include as context |

### Outputs
| Field | Type | Description |
|---|---|---|
| `answer` | `str` | Grounded answer (empty if refused) |
| `cited_chunk_ids` | `List[str]` | Chunk IDs used as evidence |
| `cited_texts` | `List[str]` | Verbatim chunk texts cited |
| `confidence` | `float` | Relevance score of best matching chunk |
| `refused` | `bool` | True if content not found in document |
| `refusal_reason` | `Optional[str]` | Reason for refusal (if refused=True) |

### Refusal Conditions
The skill will refuse (return `refused=True`) when:
1. No chunks are provided.
2. Best matching chunk similarity score < `threshold`.
3. LLM response indicates the chunks do not contain the answer.

### Usage Example
```python
skill = CitationGroundingSkill(llm_client=nvidia_client)

# In Compliance Auditor Agent
result = skill.ground(
    question=rule.check_prompt,
    chunks=document_chunks,
    threshold=0.65,
)
if result.refused:
    verdict = "NOT_ADDRESSED"
else:
    verdict = "PASS" if result.answer.startswith("PASS") else "FAIL"

# In Q&A flow
result = skill.ground(
    question=user_question,
    chunks=document_chunks,
    threshold=0.70,
)
if result.refused:
    return QAResponse(refused=True, refusal_reason=result.refusal_reason)
else:
    return QAResponse(answer=result.answer, cited_passages=result.cited_texts)
```
