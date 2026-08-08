# AGENTS.md — Coding Agent Rules for LexAudit

> This file is re-read at the start of every coding task. Keep it short and current.

---

## 1. Project Constitution

**Scope is exactly §1 of PROJECT_MASTER.md.** This repo does two things and only two things:
- Compliance Auditor (doc → clause-by-clause pass/fail report with evidence)
- Grounded Q&A (question → cited answer from doc, or explicit refusal)

**Out of scope — do not build:**
- User authentication or accounts
- Multi-tenant SaaS features
- Payment flows
- Admin dashboards
- Any rule sets beyond DPDP 2023 and Indian Contract Act 1872

If asked to add something not in scope: stop and say so. Don't guess, don't expand.

---

## 2. Grounding Rule (NON-NEGOTIABLE)

Any agent output that states a fact about a document MUST include:
- `chunk_id` — the exact chunk the fact came from
- `evidence_text` — verbatim quoted text from that chunk

**No exceptions.** "I think the policy probably says..." is a hallucination. Every Finding must have evidence. If no relevant chunk exists: `verdict = "Not Addressed"`, not a guess.

---

## 3. Human-in-the-Loop Rule

- Nothing auto-merges to `main` without a team member reviewing the diff.
- Commit continuously with small, focused commits — never a one-day dump.
- Every code generation pass should produce reviewable, diffable output.

---

## 4. Secrets Rule

- API keys live only in `.env`. Never committed.
- `.env` is in `.gitignore`. Verify before every `git push`.
- Use `.env.example` with placeholder values as the committed template.
- Never paste real secrets into any AI tool prompt.

---

## 5. Test-First for Rules

Every new rule added to `/rules/` MUST have:
- One test fixture: a sample clause that PASSES the rule
- One test fixture: a sample clause that FAILS the rule

A rule without fixtures is not done. Do not move on until tests pass.

---

## 6. Context Hygiene

- Keep this file short. It is re-sent every task, so bloat wastes quota.
- Update this file when rules change — do not let it diverge from reality.
- Reference `PROJECT_MASTER.md` for the full spec; do not duplicate it here.
