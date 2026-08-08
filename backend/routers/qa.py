"""Q&A router — grounded question answering from uploaded documents."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from config import settings
from models import CitedPassage, QARequest, QAResponse
from skills.citation_grounding import CitationGroundingSkill
from vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/qa", tags=["qa"])

# Q&A uses a more permissive threshold than audit (real-world docs are messy)
_QA_THRESHOLD = 0.50


@router.post("/", response_model=QAResponse)
async def answer_question(request: QARequest) -> QAResponse:
    """
    Answer a question grounded only in the uploaded document.

    Returns either:
    - A grounded answer with cited passages (refused=false)
    - An explicit refusal if the answer is not in the document (refused=true)

    GUARANTEE: Never returns an answer that cannot be cited from the document.
    """
    vs = get_vector_store()

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Validate document exists
    if not vs.doc_exists(request.doc_id):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.doc_id}' not found. Please upload it first.",
        )

    # Retrieve top-k relevant chunks
    chunks_with_scores = vs.query_chunks(
        query_text=request.question,
        doc_id=request.doc_id,
        n_results=settings.grounding_max_chunks,
    )
    chunks = [c for c, _ in chunks_with_scores]
    scores = [s for _, s in chunks_with_scores]

    logger.info(
        "Q&A: doc=%s question='%s...' top_score=%.3f",
        request.doc_id,
        request.question[:60],
        scores[0] if scores else 0.0,
    )

    # Run Citation Grounding Skill — use permissive Q&A threshold
    skill = CitationGroundingSkill()
    result = skill.ground(
        question=request.question,
        chunks=chunks,
        chunk_scores=scores,
        threshold=_QA_THRESHOLD,   # 0.50 — more forgiving for messy real-world docs
    )

    if result.refused:
        logger.info("Q&A refused: %s", result.refusal_reason)
        return QAResponse(
            doc_id=request.doc_id,
            question=request.question,
            refused=True,
            refusal_reason=result.refusal_reason,
        )

    # Build cited passages with metadata
    chunk_map = {c.chunk_id: c for c in chunks}
    cited_passages = []
    for cid, ctext in zip(result.cited_chunk_ids, result.cited_texts):
        source_chunk = chunk_map.get(cid)
        cited_passages.append(
            CitedPassage(
                chunk_id=cid,
                text=ctext,
                page_number=source_chunk.page_number if source_chunk else None,
                section_title=source_chunk.section_title if source_chunk else None,
                relevance_score=result.confidence,
            )
        )

    return QAResponse(
        doc_id=request.doc_id,
        question=request.question,
        answer=result.answer,
        cited_passages=cited_passages,
        refused=False,
    )


@router.get("/rulesets")
async def list_rulesets() -> list[dict]:
    """List available rule sets for audit."""
    from rule_loader import list_available_rulesets
    return list_available_rulesets()


class DocDescription(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
    summary: str          # 2-3 sentence overview of what the document is
    topics: list[str]     # bullet-point topics detected in the document
    suggested_questions: list[str]  # 3 example questions the user can ask


@router.get("/describe/{doc_id}", response_model=DocDescription)
async def describe_document(doc_id: str) -> DocDescription:
    """
    Auto-analyse an uploaded document and return a plain-language description:
    what it is, what topics it covers, and suggested questions to ask.
    """
    vs = get_vector_store()
    if not vs.doc_exists(doc_id):
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    # Grab up to 12 chunks for a broad overview of the document
    chunks_with_scores = vs.query_chunks(
        query_text="document overview summary structure contents",
        doc_id=doc_id,
        n_results=12,
    )
    chunks = [c for c, _ in chunks_with_scores]

    if not chunks:
        raise HTTPException(status_code=422, detail="Document has no indexed content yet.")

    # Get filename from first chunk
    filename = chunks[0].doc_id  # fallback
    try:
        docs = vs.list_documents()
        match = next((d for d in docs if d["doc_id"] == doc_id), None)
        if match:
            filename = match.get("filename", doc_id)
    except Exception:
        pass

    context = "\n\n".join(f"[Excerpt {i+1}]\n{c.text}" for i, c in enumerate(chunks))

    system_prompt = """\
You are a document analyst. Read the provided excerpts and return a JSON object describing the document.

Return ONLY valid JSON with this exact structure:
{
  "summary": "2-3 sentence plain-language description of what this document is and its purpose",
  "topics": ["topic 1", "topic 2", "topic 3"],
  "suggested_questions": [
    "Specific question a user could ask about this document?",
    "Another specific question?",
    "A third specific question?"
  ]
}

Rules:
- summary must be factual, based ONLY on the excerpts
- topics: 3-6 short topic labels (e.g. "Payment terms", "Liability clause")
- suggested_questions: 3 questions that CAN be answered from the document
- Do NOT invent content not in the excerpts
"""

    try:
        client = OpenAI(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
        )
        response = client.chat.completions.create(
            model=settings.nvidia_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"DOCUMENT EXCERPTS:\n{context}\n\nDescribe this document."},
            ],
            temperature=0.2,
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
    except Exception as e:
        logger.exception("Document description LLM call failed: %s", e)
        # Graceful fallback — no LLM, just count chunks
        parsed = {
            "summary": f"Document indexed with {len(chunks)} passages. Ask any question to search its content.",
            "topics": ["Document content"],
            "suggested_questions": [
                "What is the main purpose of this document?",
                "What are the key obligations mentioned?",
                "What dates or deadlines are specified?",
            ],
        }

    return DocDescription(
        doc_id=doc_id,
        filename=filename,
        chunk_count=len(chunks),
        summary=parsed.get("summary", ""),
        topics=parsed.get("topics", []),
        suggested_questions=parsed.get("suggested_questions", []),
    )
