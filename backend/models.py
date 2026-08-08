"""Core Pydantic data models for LexAudit."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_ADDRESSED = "NOT_ADDRESSED"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleSet(str, Enum):
    DPDP_2023 = "dpdp_2023"
    CONTRACT_ACT_1872 = "contract_act_1872"


# ─── Document & Chunks ────────────────────────────────────────────────────────

class Chunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chunk_{uuid4().hex[:12]}")
    doc_id: str
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_index: int = 0

    def short_preview(self, n: int = 120) -> str:
        return self.text[:n] + ("…" if len(self.text) > n else "")


class Document(BaseModel):
    doc_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:12]}")
    filename: str
    file_type: str  # "pdf" | "docx"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    total_chunks: int = 0


# ─── Rules ────────────────────────────────────────────────────────────────────

class Rule(BaseModel):
    rule_id: str
    act: str
    act_short: str
    title: str
    description: str
    check_prompt: str
    severity: Severity
    section: str


# ─── Findings & Reports ───────────────────────────────────────────────────────

class Finding(BaseModel):
    finding_id: str = Field(default_factory=lambda: f"f_{uuid4().hex[:12]}")
    doc_id: str
    rule_id: str
    rule_title: str
    chunk_id: Optional[str] = None        # None when NOT_ADDRESSED
    verdict: Verdict
    evidence_text: Optional[str] = None   # verbatim quoted text
    reasoning: str
    severity: Severity
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"report_{uuid4().hex[:12]}")
    doc_id: str
    filename: str
    ruleset: RuleSet
    findings: list[Finding] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def pass_count(self) -> int:
        return sum(1 for f in self.findings if f.verdict == Verdict.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for f in self.findings if f.verdict == Verdict.FAIL)

    @property
    def not_addressed_count(self) -> int:
        return sum(1 for f in self.findings if f.verdict == Verdict.NOT_ADDRESSED)


# ─── Q&A ──────────────────────────────────────────────────────────────────────

class CitedPassage(BaseModel):
    chunk_id: str
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    relevance_score: float = 0.0


class QAResponse(BaseModel):
    response_id: str = Field(default_factory=lambda: f"qa_{uuid4().hex[:12]}")
    doc_id: str
    question: str
    answer: Optional[str] = None
    cited_passages: list[CitedPassage] = []
    refused: bool = False
    refusal_reason: Optional[str] = None
    answered_at: datetime = Field(default_factory=datetime.utcnow)


# ─── API Request/Response Schemas ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    total_chunks: int
    message: str


class AuditRequest(BaseModel):
    doc_id: str
    ruleset: RuleSet


class QARequest(BaseModel):
    doc_id: str
    question: str


class AuditReportSummary(BaseModel):
    report_id: str
    doc_id: str
    filename: str
    ruleset: str
    pass_count: int
    fail_count: int
    not_addressed_count: int
    generated_at: datetime
