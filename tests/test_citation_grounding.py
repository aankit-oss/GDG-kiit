"""Unit tests for the Citation Grounding Skill.

Tests verify:
- Refusal when no chunks provided
- Refusal when chunk scores below threshold
- Answer returned when valid chunks provided (mocked LLM)
- cited_chunk_ids always non-empty when refused=False
"""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional

# Patch openai before importing the skill (must precede skill import)
import sys
sys.modules.setdefault("openai", MagicMock())

from skills.citation_grounding import CitationGroundingSkill, GroundingResult  # noqa: E402
from models import Chunk  # noqa: E402


def make_chunk(text: str, chunk_id: str = "chunk_test_001", doc_id: str = "doc_001") -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id=doc_id, text=text, page_number=1, section_title="Test Section")


class TestCitationGroundingSkill:
    """Tests for the Citation Grounding Skill contract."""

    def test_refusal_when_no_chunks(self):
        """MUST refuse when no chunks provided."""
        skill = CitationGroundingSkill(llm_client=MagicMock())
        result = skill.ground(question="What is the data retention period?", chunks=[])
        assert result.refused is True
        assert result.cited_chunk_ids == []
        assert result.answer == ""
        assert "No document content" in (result.refusal_reason or "")

    def test_refusal_when_score_below_threshold(self):
        """MUST refuse when best chunk similarity score is below threshold."""
        skill = CitationGroundingSkill(llm_client=MagicMock())
        chunks = [make_chunk("Unrelated text about cooking recipes.")]
        result = skill.ground(
            question="What is the data retention policy?",
            chunks=chunks,
            chunk_scores=[0.1],   # well below default threshold 0.65
            threshold=0.65,
        )
        assert result.refused is True
        assert result.confidence == 0.1
        assert "required: 0.65" in (result.refusal_reason or "")

    def test_grounded_answer_has_citations(self):
        """When answer found, cited_chunk_ids MUST be non-empty."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"verdict": "FOUND", "answer": "Data is retained for 30 days.", "cited_chunk_ids": ["chunk_test_001"]}'))]
        )
        skill = CitationGroundingSkill(llm_client=mock_client)
        chunks = [make_chunk("We retain your personal data for 30 days after account closure.")]
        result = skill.ground(
            question="How long is data retained?",
            chunks=chunks,
            chunk_scores=[0.9],
            threshold=0.65,
        )
        assert result.refused is False
        assert len(result.cited_chunk_ids) > 0
        assert "chunk_test_001" in result.cited_chunk_ids
        assert result.answer == "Data is retained for 30 days."

    def test_refusal_when_llm_returns_insufficient(self):
        """MUST refuse when LLM says INSUFFICIENT."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"verdict": "INSUFFICIENT", "reason": "The excerpts do not address this question."}'))]
        )
        skill = CitationGroundingSkill(llm_client=mock_client)
        chunks = [make_chunk("This contract is between Party A and Party B.")]
        result = skill.ground(
            question="What is the data retention period?",
            chunks=chunks,
            chunk_scores=[0.8],
            threshold=0.65,
        )
        assert result.refused is True
        assert "excerpts do not address" in (result.refusal_reason or "")

    def test_refusal_when_llm_returns_no_valid_citations(self):
        """MUST refuse if LLM says FOUND but cites no valid chunk IDs."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"verdict": "FOUND", "answer": "Some answer", "cited_chunk_ids": []}'))]
        )
        skill = CitationGroundingSkill(llm_client=mock_client)
        chunks = [make_chunk("Some document text.")]
        result = skill.ground(
            question="What does section 3 say?",
            chunks=chunks,
            chunk_scores=[0.8],
            threshold=0.65,
        )
        assert result.refused is True
        assert "without valid citations" in (result.refusal_reason or "")

    def test_llm_error_returns_refusal(self):
        """LLM call failure MUST return a refusal, not raise an exception."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API timeout")
        skill = CitationGroundingSkill(llm_client=mock_client)
        chunks = [make_chunk("Some text.")]
        result = skill.ground(
            question="What is stated here?",
            chunks=chunks,
            chunk_scores=[0.8],
        )
        assert result.refused is True
        assert "LLM call failed" in (result.refusal_reason or "")
