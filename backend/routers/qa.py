"""Q&A router — grounded question answering from uploaded documents."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from config import settings
from models import CitedPassage, QARequest, QAResponse
from skills.citation_grounding import CitationGroundingSkill
from vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/qa", tags=["qa"])


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

    # Run Citation Grounding Skill
    skill = CitationGroundingSkill()
    result = skill.ground(
        question=request.question,
        chunks=chunks,
        chunk_scores=scores,
        threshold=settings.grounding_threshold,
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
