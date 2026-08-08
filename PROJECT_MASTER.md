# PROJECT MASTER — LexAudit
### Track C: Knowledge & Compliance Agents — "Deploy or Die" (HowToAlgo x GDGoC KIIT)

> **Read this whole file before writing any code.** This is the single source of truth for scope,
> architecture, agent rules, and grading. If a decision isn't in here, stop and ask the human, don't guess.

---

## 1. Product Definition

**LexAudit** — a compliance-audit + grounded Q&A agent for Indian law documents.

Two capabilities, both required by the PS examples for Track C:

1. **Compliance Auditor** — ingest a contract / privacy policy / HR policy → check it clause-by-clause
   against a defined rule library → output a **pass/fail report with evidence** (exact clause quoted +
   rule ID + verdict + reasoning).
2. **Grounded Q&A** — user asks a question about an uploaded document → agent answers **only from the
   document**, cites the exact passage/section it used, and **explicitly refuses** if the answer isn't
   in the source (no hallucination, ever).

**Rule library scope (pick this, don't expand):**
- Digital Personal Data Protection Act (DPDP), 2023 — for privacy policy audits
- Indian Contract Act, 1872 (core validity clauses: consideration, free consent, capacity, lawful object)
- Keep the rule library to ~15–25 rules total. Depth over breadth — a small, well-tested rule set beats
  a huge, unverified one.

**Why this wins on the rubric:**
- Grounding + citations + refusal-on-unknown = exactly what "Testing and Verification" and "Agent
  Engineering" judges look for — it's *checkable*, not vibes.
- Pass/fail + evidence = auditable trail (the "what good looks like" bar for Track C).
- Two clean, demoable flows = strong "Working Software" score without scope bloat.

---

## 2. Architecture (write this into `ARCHITECTURE.md` in the repo — checkpoint #1)

- **Frontend**: minimal web UI (React or plain HTML) — upload doc, pick rule set, view report / ask Q&A.
- **Backend**: FastAPI (Python) or Express (Node) — pick one, document why.
- **Ingestion**: PDF/DOCX → text chunks with page/section metadata preserved (metadata is mandatory —
  citations are worthless without it).
- **Retrieval**: simple vector store (e.g. Chroma/FAISS, local, no paid service) keyed by chunk + metadata.
- **LLM layer**: NVIDIA Build for the audit/reasoning loop, Gemini Flash for planning/spec generation
  (see §6 Rate-Limit Strategy).
- **Data model**: `Document → Chunks → Rules → Findings (rule_id, chunk_id, verdict, evidence_text, reasoning)`
- **Audit trail**: every Finding stores the exact source chunk id + text, timestamped. This is your
  "traceable and auditable" requirement — do not skip it.

`ARCHITECTURE.md` must contain: stack choice + why, data model diagram (mermaid is fine), request flow
for both features, and known limitations.

---

## 3. The Five Non-Negotiables — how LexAudit clears each

These are **entry gates, not scoring**. Miss one = zero, no matter how good the product is.

| # | Checkpoint | What must exist in repo | LexAudit's answer |
|---|---|---|---|
| 1 | Architecture document | `ARCHITECTURE.md` | Stack, data model, request flow (§2 above) |
| 2 | Agent rules file | `AGENTS.md` or `.clinerules` or `constitution.md` | See §5 — defines how the coding agent must behave in this repo |
| 3 | Working code | App builds + runs, demonstrable | Both flows (audit + Q&A) runnable via `docker compose up` or documented local run |
| 4 | Custom agent + custom skill | Committed, documented in `AGENTS_AND_SKILLS.md` | See §4 |
| 5 | Green CI/CD | GitHub Actions, latest run passing | Lint + unit tests + Playwright, on every push |

Before submission: open each of these 5 files and confirm they exist, are non-empty, and are current.
Do this as a literal checklist pass the night before Day-1 deadline.

---

## 4. Custom Agent + Custom Skill (checkpoint #4)

Document both in `AGENTS_AND_SKILLS.md`.

**Custom Agent — "Compliance Auditor Agent"**
- Role: takes (document chunks, rule library) → produces structured Findings JSON.
- Must be a distinct, named agent/persona in your framework (Spec Kit sub-agent, Cline custom mode, or
  a dedicated system prompt + tool binding) — not just "the same chat with a different prompt string."
- Hard constraint baked into its prompt: **never assert a verdict without quoting the exact source
  chunk it used.** If no relevant chunk exists, verdict = "Not Addressed", not a guess.

**Custom Skill — "Citation Grounding Skill"**
- A reusable function/module: given (question, chunk set) → returns (answer, cited_chunk_ids) OR
  explicit refusal if confidence/match is below threshold.
- Reused by both the Auditor Agent and the Q&A flow — this reuse is what makes it a "skill" and not a
  one-off script. Document the interface (inputs/outputs) in `AGENTS_AND_SKILLS.md`.

---

## 5. `AGENTS.md` — rules for the coding agent building this repo

Write this file for real, not as filler — the checkpoint script looks for it and judges read it.
Minimum contents:
1. **Project constitution**: scope is exactly §1 above. No feature creep (no auth system, no multi-tenant
   SaaS, no payment flow — this is a hackathon demo, not a startup).
2. **Grounding rule**: any agent output that states a fact about a document MUST cite chunk id + text.
   No exceptions, no "I think the policy probably says...".
3. **Human-in-the-loop rule**: nothing auto-merges to `main` without the team reviewing the diff. Commit
   continuously (small commits), never one end-of-day dump.
4. **Secrets rule**: API keys only in `.env`, never committed. Add `.env` to `.gitignore` on commit #1.
5. **Test-first for rules**: every new rule added to the rule library needs at least one test fixture
   (a sample clause that should pass, one that should fail) before it's considered done.
6. **Context hygiene**: keep this file itself short and current — it gets re-read every task, so bloat
   costs quota (see §6).

---

## 6. Rate-Limit Survival — provider split

| Provider | Use for | Why |
|---|---|---|
| NVIDIA Build (`nvapi-...`) | Bulk implement loop, the Auditor Agent's reasoning calls | Free, strong code models, no card |
| Google AI Studio (Gemini Flash) | Spec Kit planning phase, PRD/spec generation, rule-library drafting | Permanent free tier, good at structured/quality-sensitive text |
| Groq | Fast small edits, quick iteration during Day-1 crunch | Speed |
| OpenRouter | Fallback only, when the above 429s | Model variety |

Rules:
- Every team member (3–4 people) creates **their own keys on every service** — free limits are per
  account, so this multiplies your real capacity.
- Request the NVIDIA credit top-up **on Day 1 morning**, before you need it.
- Keep `AGENTS.md`/rule files short — you re-send them every task, so bloat = wasted quota.
- On a 429, switch provider immediately. Don't wait it out.

---

## 6.5 Deployment — is a live hosted URL required?

**No.** Nowhere in the checkpoints or submission list is a hosted/public URL mandatory. What's actually
gated:
- App **builds and runs locally/via Docker**, demonstrable
- **CI/CD pipeline green** (this is the "deploy" step in GitHub Actions — build+test on push, not hosting)
- Demo video / screenshots as proof it runs

"Deploy or Die" is the event's philosophy (ship something real, not a slide deck), not a literal hosting
mandate. That said, a live deployed instance (Render/Railway/Fly.io free tier, or a GitHub Pages +
serverless backend) **strengthens** your "Working Software & Delivery" score (30%) since it proves
someone else can bring it up with zero setup. Treat it as a strong optional add, not a gate — don't burn
Day-1 hours on cloud infra if the CI + local-run + video path is at risk instead.

---

## 7. Prerequisites (do before Day 1 — non-negotiable for time)

**Accounts (all free):**
- [ ] GitHub account + Student Developer Pack verified with KIIT email
- [ ] NVIDIA Build account, `nvapi-...` key generated and saved (shown once)
- [ ] Google AI Studio account, Gemini API key generated
- [ ] One fallback: OpenRouter or Groq key

**Tools installed:**
- [ ] VS Code, Node.js LTS, Python 3.11+, Git, Docker Desktop, `uv`
- [ ] Cline (recommended for human-in-the-loop Plan/Act approval) or Roo Code, NVIDIA key wired in

**Verify the day before:**
- [ ] One test prompt through Cline via NVIDIA key returns a response
- [ ] `specify init test` runs successfully (GitHub Spec Kit)
- [ ] Throwaway public repo confirms a GitHub Actions workflow actually runs green
- [ ] All keys stored in local `.env`, never committed

---

## 8. Rules & Requirements (hard constraints, not suggestions)

- Team size 3–4. Repo **must be public** (also unlocks unlimited free Actions minutes).
- No paid Claude Code / paid Copilot required — free agents + free LLM backends only.
- Everything must be **demonstrable and traceable in the repo** — if a judge can't run it, see it, or
  trace it, it does not count, full stop.
- Never paste secrets, passwords, or real personal data into any AI tool (free tiers may train on input).
  → **This is a privacy rule for test fixtures, not a scope reduction.** The system itself (ingestion,
  rule engine, citation grounding, verdicts) must be fully real and work on arbitrary, genuine documents.
  Only the sample docs you feed it during dev/CI should avoid containing real people's private data —
  use realistic but synthetic/anonymized contracts, not toy stub text. Judges will likely test with
  their own real documents; the engine must not be hardcoded to demo fixtures.
- Human-in-the-loop is mandatory. Blind, unreviewed auto-generation scores poorly by design.
- Commit continuously. Progressive history >> one giant commit.

---

## 9. Scoring Map — where LexAudit earns points

| Area | Weight | LexAudit's play |
|---|---|---|
| Specification & Architecture | 25% | Spec Kit `/speckit.specify` → clear PRD with user stories per feature (audit, Q&A); `ARCHITECTURE.md` with data model |
| Working Software & Delivery | 30% | Both flows run via one `docker compose up`; README with exact run steps; demo video |
| Agent Engineering & Code Quality | 30% | Named custom Agent + reusable Skill (§4); tight `AGENTS.md`; lint/pre-commit configured |
| Testing & Verification | 15% | Unit tests per rule (pass/fail fixtures) + Playwright E2E for upload→report and upload→Q&A, both green in CI |

**Day 2 twist prep**: architecture must let you swap in a **new rule set or new document type without
touching the Auditor Agent's core logic** — keep rules data-driven (JSON/YAML rule definitions), not
hardcoded in Python. This is the single highest-leverage design decision for surviving Day 2.

---

## 10. Repo Structure (target)

```
/README.md
/ARCHITECTURE.md
/AGENTS.md
/AGENTS_AND_SKILLS.md
/SPEC.md                  # PRD + user stories + acceptance criteria
/rules/                   # rule library, data-driven (YAML/JSON), one file per act
/backend/
/frontend/
/tests/                   # unit tests: rule fixtures
/e2e/                      # Playwright tests
/.github/workflows/ci.yml
/.env.example
```

---

## 11. Submission Checklist

**End of Day 1:**
- [ ] Public repo link
- [ ] All 5 non-negotiables verified present (§3 table)
- [ ] `SPEC.md` with user stories + acceptance criteria
- [ ] Playwright E2E green in CI, report uploaded as CI artifact
- [ ] Lint/static-analysis config, ideally pre-commit hooks
- [ ] Clean progressive commit history
- [ ] Task breakdown doc (what the agent worked through)
- [ ] Tagged release (semver + git tag/GitHub Release)
- [ ] Confirmation CI is green + tests pass (screenshot or link)
- [ ] ~3 min demo video or screenshots

**Day 2 (if finalist):**
- [ ] New surprise requirement implemented without breaking existing features
- [ ] Updated repo + short presentation deck (problem, approach, architecture, what the ADLC gave you)
- [ ] Ready for live repo walkthrough + Q&A on design trade-offs

---

## 12. Build Order (for the coding agent — follow in sequence)

1. `specify init lexaudit` → run `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`,
   `/speckit.tasks`, `/speckit.analyze` (read-only check — do not skip), then `/speckit.implement`.
2. Scaffold repo structure (§10). Commit.
3. Write 2–3 rules in `/rules/` with pass/fail fixtures first. Prove the grounding pipeline on a tiny
   scope before expanding to the full rule library.
4. Build ingestion (PDF/DOCX → chunks with metadata). Test on one sample doc. Commit.
5. Build the Citation Grounding Skill. Unit test it standalone before wiring into agents.
6. Build the Compliance Auditor Agent on top of the skill. Test against fixtures from step 3.
7. Build the Q&A flow reusing the same skill.
8. Wire minimal frontend for both flows.
9. Add CI: lint + unit tests + Playwright, get it green.
10. Fill `ARCHITECTURE.md`, `AGENTS.md`, `AGENTS_AND_SKILLS.md`, `SPEC.md` — these are graded artifacts,
    not afterthoughts. Write them as you go, not all at the end.
11. Tag a release. Record demo video.
12. Do the §11 checklist pass, literally, before submitting.
