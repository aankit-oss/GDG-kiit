"""
Compliance Auditor Agent — LexAudit's named custom agent.

System prompt and identity are BAKED IN. This agent has one role:
evaluate document chunks against legal rules, producing structured Findings.

Hard constraints (cannot be overridden by caller):
  - Never asserts a verdict without quoting exact source chunk.
  - Verdict is exactly one of: PASS, FAIL, NOT_ADDRESSED.
  - If no relevant chunk found → verdict = NOT_ADDRESSED, not a guess.
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import uuid4

from openai import OpenAI

from config import settings
from models import (
    AuditReport,
    Chunk,
    Finding,
    Rule,
    RuleSet,
    Severity,
    Verdict,
)
from skills.citation_grounding import CitationGroundingSkill
from vector_store import VectorStore

logger = logging.getLogger(__name__)


# ── Agent System Prompt (baked in, non-overridable) ───────────────────────────
_AUDITOR_SYSTEM_PROMPT = """\
You are LexAudit's Compliance Auditor Agent. Your role is to evaluate whether a document \
clause satisfies a specific legal rule from Indian law (DPDP 2023 or Indian Contract Act 1872).

IDENTITY: You are a specialized legal compliance auditor, not a general assistant. \
You evaluate documents against specific rules only.

HARD CONSTRAINTS (non-negotiable):
1. You MUST return valid JSON with exactly these fields:
   {"verdict": "PASS|FAIL|NOT_ADDRESSED", "evidence_text": "...", "reasoning": "..."}
2. verdict MUST be exactly one of: PASS, FAIL, NOT_ADDRESSED
3. evidence_text MUST be verbatim text from the document excerpt, not a paraphrase.
4. If no relevant content exists → verdict = "NOT_ADDRESSED", evidence_text = null.
5. NEVER guess or fabricate evidence. If uncertain → NOT_ADDRESSED.
6. reasoning must explain WHY the clause passes/fails, citing specific legal requirements.

You are given: a legal rule description and document excerpts that may be relevant.
Evaluate whether the document satisfies the rule based solely on the provided excerpts.
"""


class ComplianceAuditorAgent:
    """
    Named Compliance Auditor Agent with baked-in system prompt.

    Uses the CitationGroundingSkill internally to retrieve relevant chunks
    before making a verdict. This two-layer grounding ensures:
    1. Vector search finds relevant chunks (semantic layer)
    2. LLM evaluates only those chunks with auditor persona (reasoning layer)
    """

    AGENT_NAME = "ComplianceAuditorAgent"

    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: Optional[OpenAI] = None,
    ) -> None:
        self._vs = vector_store
        if llm_client is None:
            llm_client = OpenAI(
                api_key=settings.nvidia_api_key,
                base_url=settings.nvidia_base_url,
            )
        self._client = llm_client
        self._grounding_skill = CitationGroundingSkill(llm_client=llm_client)

    def audit(
        self,
        doc_id: str,
        filename: str,
        ruleset: RuleSet,
        rules: list[Rule],
    ) -> AuditReport:
        """
        Evaluate each rule against the document stored in the vector store.

        Args:
            doc_id: Document ID (must already be ingested into vector store).
            filename: Original filename (for report metadata).
            ruleset: Which rule set is being applied.
            rules: The loaded rules to evaluate.

        Returns:
            AuditReport with one Finding per rule, each with chunk_id, verdict,
            evidence_text, reasoning, and evaluated_at timestamp.
        """
        findings: list[Finding] = []

        for rule in rules:
            logger.info("Auditing rule %s: %s", rule.rule_id, rule.title)
            finding = self._evaluate_rule(doc_id, rule)
            findings.append(finding)

        report = AuditReport(
            doc_id=doc_id,
            filename=filename,
            ruleset=ruleset,
            findings=findings,
        )
        return report

    def _evaluate_rule(self, doc_id: str, rule: Rule) -> Finding:
        """Evaluate a single rule against the document. Always returns a Finding."""
        # Step 1: Retrieve top-k relevant chunks from vector store
        chunks_with_scores = self._vs.query_chunks(
            query_text=rule.check_prompt,
            doc_id=doc_id,
            n_results=settings.grounding_max_chunks,
        )

        chunks = [c for c, _ in chunks_with_scores]
        scores = [s for _, s in chunks_with_scores]

        # Step 2: Use Citation Grounding Skill to extract relevant content
        grounding = self._grounding_skill.ground(
            question=rule.check_prompt,
            chunks=chunks,
            chunk_scores=scores,
            threshold=settings.grounding_threshold,
        )

        if grounding.refused:
            return Finding(
                doc_id=doc_id,
                rule_id=rule.rule_id,
                rule_title=rule.title,
                chunk_id=None,
                verdict=Verdict.NOT_ADDRESSED,
                evidence_text=None,
                reasoning=(
                    grounding.refusal_reason or
                    "No relevant clause found in the document for this rule."
                ),
                severity=rule.severity,
            )

        # Step 3: Have the auditor agent evaluate the grounded content
        verdict_result = self._call_auditor(
            rule=rule,
            grounded_text=grounding.answer,
            cited_texts=grounding.cited_texts,
        )

        return Finding(
            doc_id=doc_id,
            rule_id=rule.rule_id,
            rule_title=rule.title,
            chunk_id=grounding.cited_chunk_ids[0] if grounding.cited_chunk_ids else None,
            verdict=verdict_result["verdict"],
            evidence_text=verdict_result.get("evidence_text"),
            reasoning=verdict_result.get("reasoning", ""),
            severity=rule.severity,
        )

    def _call_auditor(
        self,
        rule: Rule,
        grounded_text: str,
        cited_texts: list[str],
    ) -> dict:
        """Call LLM with auditor persona to determine PASS/FAIL verdict."""
        excerpt_block = "\n\n".join(f"EXCERPT:\n{t}" for t in cited_texts)
        user_message = (
            f"RULE: {rule.rule_id} — {rule.title}\n"
            f"Rule Description: {rule.description}\n"
            f"Legal Section: {rule.section}\n\n"
            f"RELEVANT DOCUMENT CONTENT:\n{excerpt_block}\n\n"
            "Evaluate whether the document satisfies this rule. "
            "Return JSON: {\"verdict\": \"PASS|FAIL\", \"evidence_text\": \"...\", \"reasoning\": \"...\"}"
        )

        try:
            response = self._client.chat.completions.create(
                model=settings.nvidia_model,
                messages=[
                    {"role": "system", "content": _AUDITOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)

            # Validate verdict value
            raw_verdict = parsed.get("verdict", "NOT_ADDRESSED").upper()
            if raw_verdict not in ("PASS", "FAIL", "NOT_ADDRESSED"):
                raw_verdict = "NOT_ADDRESSED"

            return {
                "verdict": Verdict(raw_verdict),
                "evidence_text": parsed.get("evidence_text"),
                "reasoning": parsed.get("reasoning", ""),
            }

        except Exception as e:
            logger.exception("Auditor LLM call failed for rule %s: %s", rule.rule_id, e)
            return {
                "verdict": Verdict.NOT_ADDRESSED,
                "evidence_text": None,
                "reasoning": f"Evaluation failed due to an internal error: {e}",
            }
