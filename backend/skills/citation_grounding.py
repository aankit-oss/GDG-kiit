"""
Citation Grounding Skill — LexAudit's core reusable grounding module.

Reused by:
  - ComplianceAuditorAgent (per-rule grounding)
  - Q&A router (user question grounding)

Contract:
  - If refused=False, cited_chunk_ids is ALWAYS non-empty.
  - The answer NEVER contains information not present in cited chunks.
  - If best chunk similarity < threshold → refused=True always.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

# pyrefly: ignore [missing-import]
from openai import OpenAI

from config import settings
from models import Chunk

logger = logging.getLogger(__name__)


@dataclass
class GroundingResult:
    answer: str
    cited_chunk_ids: list[str]
    cited_texts: list[str]
    confidence: float          # similarity score of best matching chunk
    refused: bool = False
    refusal_reason: Optional[str] = None
    detected_language: str = "en"   # ISO 639-1 code of the question's language


_GROUNDING_SYSTEM_PROMPT = """\
You are a strict legal document grounding assistant. Your ONLY job is to answer \
questions using EXCLUSIVELY the document excerpts provided to you.

MULTILINGUAL RULE:
- Detect the language of the QUESTION (e.g., Hindi, Bengali, Tamil, English).
- Your ENTIRE response — including the answer, refusal reason, and JSON values — \
MUST be written in that SAME language.
- Do NOT translate the question. Answer in whatever language the user used.

ABSOLUTE RULES:
1. You MUST only use information from the provided excerpts. NEVER use external knowledge.
2. You MUST cite which excerpt(s) you used by their chunk_id.
3. If the excerpts do not contain enough information to answer, respond with:
   {"verdict": "INSUFFICIENT", "reason": "<why the content is not found, in the user's language>",
    "detected_language": "<ISO 639-1 code, e.g. hi, bn, ta, en>"}
4. If you can answer, respond with valid JSON:
   {"verdict": "FOUND", "answer": "<your answer in the user's language>",
    "cited_chunk_ids": ["chunk_id1", ...],
    "detected_language": "<ISO 639-1 code, e.g. hi, bn, ta, en>"}
5. Do NOT paraphrase source text as if it were a quote — always use verbatim quotes when citing evidence.
6. Do NOT speculate, infer, or extrapolate beyond what the text explicitly states.
7. Refuse politely in the user's language if the question is offensive or completely off-topic.
"""


class CitationGroundingSkill:
    """
    Reusable skill: given (question, chunks) → grounded answer with citations OR refusal.

    This is the core skill used by both the Compliance Auditor Agent and the Q&A flow.
    It must NOT be bypassed or used without passing real document chunks.
    """

    def __init__(self, llm_client: Optional[OpenAI] = None) -> None:
        if llm_client is None:
            llm_client = OpenAI(
                api_key=settings.nvidia_api_key,
                base_url=settings.nvidia_base_url,
            )
        self._client = llm_client

    def ground(
        self,
        question: str,
        chunks: list[Chunk],
        chunk_scores: Optional[list[float]] = None,
        threshold: float | None = None,
        max_chunks: int | None = None,
    ) -> GroundingResult:
        """
        Ground an answer in the provided chunks.

        Args:
            question: The question or rule check prompt to answer.
            chunks: Candidate document chunks (pre-filtered by vector search).
            chunk_scores: Similarity scores for each chunk (parallel to chunks list).
            threshold: Min similarity score to proceed (default from settings).
            max_chunks: Max number of chunks to include in context.

        Returns:
            GroundingResult with answer+citations OR refusal.
        """
        if threshold is None:
            threshold = settings.grounding_threshold
        if max_chunks is None:
            max_chunks = settings.grounding_max_chunks

        # Hard refusal: no chunks provided
        if not chunks:
            return GroundingResult(
                answer="",
                cited_chunk_ids=[],
                cited_texts=[],
                confidence=0.0,
                refused=True,
                refusal_reason="No document content provided for grounding.",
            )

        # Determine best score
        best_score = 0.0
        if chunk_scores:
            best_score = max(chunk_scores) if chunk_scores else 0.0
        else:
            # No scores provided — assume passable, let LLM decide
            best_score = threshold  # neutral assumption

        # Hard refusal: below similarity threshold
        if chunk_scores and best_score < threshold:
            return GroundingResult(
                answer="",
                cited_chunk_ids=[],
                cited_texts=[],
                confidence=best_score,
                refused=True,
                refusal_reason=(
                    f"No sufficiently relevant content found in the document "
                    f"(best match score: {best_score:.2f}, required: {threshold:.2f})."
                ),
            )

        # Build context for LLM
        context_chunks = chunks[:max_chunks]
        context_text = "\n\n".join(
            f"[chunk_id: {c.chunk_id}]\n{c.text}"
            for c in context_chunks
        )

        user_message = (
            f"DOCUMENT EXCERPTS:\n{context_text}\n\n"
            f"QUESTION: {question}\n\n"
            "Respond with JSON only."
        )

        try:
            response = self._client.chat.completions.create(
                model=settings.nvidia_model,
                messages=[
                    {"role": "system", "content": _GROUNDING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
        except Exception as e:
            logger.exception("LLM call failed in CitationGroundingSkill: %s", e)
            return GroundingResult(
                answer="",
                cited_chunk_ids=[],
                cited_texts=[],
                confidence=best_score,
                refused=True,
                refusal_reason=f"LLM call failed: {e}",
            )

        verdict = parsed.get("verdict", "INSUFFICIENT")

        if verdict == "INSUFFICIENT":
            return GroundingResult(
                answer="",
                cited_chunk_ids=[],
                cited_texts=[],
                confidence=best_score,
                refused=True,
                refusal_reason=parsed.get(
                    "reason",
                    "The document does not contain sufficient information to answer this question.",
                ),
            )

        # FOUND path — collect cited chunks
        cited_ids = parsed.get("cited_chunk_ids", [])
        chunk_map = {c.chunk_id: c for c in context_chunks}
        cited_texts = [
            chunk_map[cid].text for cid in cited_ids if cid in chunk_map
        ]

        # If LLM returned no valid cited IDs but said FOUND, treat as refusal
        if not cited_ids or not cited_texts:
            return GroundingResult(
                answer="",
                cited_chunk_ids=[],
                cited_texts=[],
                confidence=best_score,
                refused=True,
                refusal_reason="Model returned an answer without valid citations — refusing for safety.",
            )

        return GroundingResult(
            answer=parsed.get("answer", ""),
            cited_chunk_ids=cited_ids,
            cited_texts=cited_texts,
            confidence=best_score,
            refused=False,
            refusal_reason=None,
            detected_language=parsed.get("detected_language", "en"),
        )
