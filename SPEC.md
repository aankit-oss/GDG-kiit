# SPEC.md — LexAudit Product Requirement Document

**Version**: 1.0.0 | **Date**: 2026-08-08 | **Track**: C — Knowledge & Compliance Agents

---

## Problem Statement

Legal and compliance teams in India spend significant manual effort reviewing documents against statutory requirements (DPDP 2023, Indian Contract Act 1872). The review process is slow, error-prone, and hard to audit. There is no tool that provides clause-by-clause compliance checking with traceable evidence and refuses to hallucinate.

---

## Product Vision

LexAudit makes legal compliance review faster and auditable by:
1. Automating clause-by-clause evaluation with exact evidence citations.
2. Answering document questions with strict grounding — refusing rather than guessing.

---

## Users

| User | Goal |
|---|---|
| Legal Associate | "Check if this privacy policy complies with DPDP 2023" |
| HR Manager | "Does our HR policy cover all mandatory consent requirements?" |
| Startup Founder | "Is my contract legally valid under the Indian Contract Act?" |
| Any stakeholder | "What does section 4 of this document say about data retention?" |

---

## Feature 1: Compliance Auditor

### User Story 1.1 — Upload and Select Ruleset
> As a user, I want to upload a PDF or DOCX document and select a rule set (DPDP 2023 or Contract Act 1872), so that the system can evaluate my document.

**Acceptance Criteria:**
- [ ] User can upload a PDF or DOCX file up to 10MB
- [ ] User can select from available rule sets: `dpdp_2023`, `contract_act_1872`
- [ ] Upload succeeds and returns a `doc_id`
- [ ] Error message shown if unsupported file type uploaded

### User Story 1.2 — View Audit Report
> As a user, I want to see a structured pass/fail report after the audit, so that I can identify compliance gaps.

**Acceptance Criteria:**
- [ ] Report shows one row per rule: Rule ID, Rule Title, Verdict (PASS/FAIL/NOT_ADDRESSED)
- [ ] Each FAIL and PASS verdict shows the exact quoted clause used as evidence
- [ ] Each verdict shows the reasoning explaining WHY it passed or failed
- [ ] NOT_ADDRESSED verdict shows "No relevant clause found in document"
- [ ] Report shows summary counts: X passed, Y failed, Z not addressed
- [ ] Report is retrievable by `report_id`

### User Story 1.3 — Audit Trail
> As a user, I want every finding to have a traceable source, so that I can verify the AI's reasoning.

**Acceptance Criteria:**
- [ ] Each Finding records: `rule_id`, `chunk_id`, `evidence_text`, `reasoning`, `evaluated_at` (ISO timestamp)
- [ ] `evidence_text` is verbatim text from the document (not paraphrased)
- [ ] `chunk_id` maps back to an exact position in the document (page number, section)

---

## Feature 2: Grounded Q&A

### User Story 2.1 — Ask a Question
> As a user, I want to ask a question about an uploaded document and get an answer grounded only in that document.

**Acceptance Criteria:**
- [ ] User can select an already-uploaded document (by `doc_id`) and type a question
- [ ] Answer is sourced only from the document — no external knowledge injected
- [ ] Answer includes the exact passage(s) used, with page/section reference
- [ ] Answer is shown with highlighted cited text

### User Story 2.2 — Explicit Refusal
> As a user, I want the system to tell me clearly if the answer is not in the document, so that I know not to rely on a hallucinated response.

**Acceptance Criteria:**
- [ ] If no relevant content found in document, system shows: "This information is not addressed in the provided document."
- [ ] Refusal message is distinct from an actual answer (clear visual differentiation)
- [ ] System NEVER provides an answer it cannot cite from the document

---

## Non-Functional Requirements

| Requirement | Spec |
|---|---|
| Response time (audit) | < 60 seconds for a 10-page document |
| Response time (Q&A) | < 10 seconds |
| Supported file types | PDF, DOCX |
| Max file size | 10MB |
| Rule library size | 15–25 rules total |
| Hallucination rate | 0% — system must refuse rather than guess |
| Data privacy | No document content stored beyond session (no persistent user data) |

---

## Out of Scope

- User authentication / login
- Multi-tenant or team accounts
- Rule sets beyond DPDP 2023 and Indian Contract Act 1872
- Payment / subscription flows
- Mobile native app
- Real-time collaborative review

---

## Acceptance Criteria Summary (E2E)

| Flow | End-to-End Test |
|---|---|
| Audit | Upload PDF → Select DPDP ruleset → Run audit → See ≥1 PASS and ≥1 FAIL finding with evidence |
| Q&A (found) | Upload PDF → Ask question present in doc → See grounded answer with cited passage |
| Q&A (not found) | Upload PDF → Ask question NOT in doc → See explicit refusal message |
