"""Audit router — run compliance audit and retrieve reports."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from agents.compliance_auditor import ComplianceAuditorAgent
from config import settings
from models import AuditReport, AuditRequest, AuditReportSummary, RuleSet
from rule_loader import load_rules
from vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["audit"])

_REPORTS_DIR = Path(settings.reports_dir) / "audit"
_DOCS_STORE_PATH = Path(settings.reports_dir) / "documents.json"


def _get_doc_meta(doc_id: str) -> dict:
    if _DOCS_STORE_PATH.exists():
        with open(_DOCS_STORE_PATH) as f:
            docs = json.load(f)
        return docs.get(doc_id, {})
    return {}


def _save_report(report: AuditReport) -> None:
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _REPORTS_DIR / f"{report.report_id}.json"
    with open(path, "w") as f:
        f.write(report.model_dump_json(indent=2))


def _load_report(report_id: str) -> AuditReport | None:
    path = _REPORTS_DIR / f"{report_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return AuditReport.model_validate_json(f.read())


@router.post("/", response_model=AuditReport)
async def run_audit(request: AuditRequest) -> AuditReport:
    """
    Run a compliance audit on an already-uploaded document.

    Args:
        doc_id: The document to audit (must be uploaded first).
        ruleset: Which rule set to apply (dpdp_2023 | contract_act_1872).

    Returns:
        Full AuditReport with one Finding per rule, each with verdict + evidence.
    """
    vs = get_vector_store()

    # Validate document exists
    if not vs.doc_exists(request.doc_id):
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.doc_id}' not found. Please upload it first.",
        )

    doc_meta = _get_doc_meta(request.doc_id)
    filename = doc_meta.get("filename", request.doc_id)

    # Load rules
    try:
        rules = load_rules(request.ruleset)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rules:
        raise HTTPException(status_code=500, detail="No rules loaded — check rule library.")

    logger.info(
        "Starting audit: doc=%s ruleset=%s rules=%d",
        request.doc_id, request.ruleset, len(rules),
    )

    # Run audit via agent
    agent = ComplianceAuditorAgent(vector_store=vs)
    try:
        report = agent.audit(
            doc_id=request.doc_id,
            filename=filename,
            ruleset=request.ruleset,
            rules=rules,
        )
    except Exception as e:
        logger.exception("Audit failed for doc %s", request.doc_id)
        raise HTTPException(status_code=500, detail=f"Audit failed: {e}")

    # Persist report
    _save_report(report)

    logger.info(
        "Audit complete: report=%s pass=%d fail=%d na=%d",
        report.report_id, report.pass_count, report.fail_count, report.not_addressed_count,
    )

    return report


@router.get("/{report_id}", response_model=AuditReport)
async def get_report(report_id: str) -> AuditReport:
    """Retrieve a stored audit report by report_id."""
    report = _load_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return report


@router.get("/")
async def list_reports() -> list[AuditReportSummary]:
    """List all stored audit reports (summaries only)."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    for path in sorted(_REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            report = _load_report(path.stem)
            if report:
                summaries.append(AuditReportSummary(
                    report_id=report.report_id,
                    doc_id=report.doc_id,
                    filename=report.filename,
                    ruleset=report.ruleset.value,
                    pass_count=report.pass_count,
                    fail_count=report.fail_count,
                    not_addressed_count=report.not_addressed_count,
                    generated_at=report.generated_at,
                ))
        except Exception:
            continue
    return summaries
