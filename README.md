# LexAudit

> Compliance-audit + grounded Q&A agent for Indian law documents.  
> Built for Track C: Knowledge & Compliance Agents — "Deploy or Die" (HowToAlgo × GDGoC KIIT)

---

## What it does

**LexAudit** has two flows:

1. **Compliance Auditor** — Upload a contract / privacy policy / HR policy → get a clause-by-clause pass/fail report with exact evidence quotes and rule citations.
2. **Grounded Q&A** — Ask a question about an uploaded document → get an answer grounded *only* in that document, with cited passages — or an explicit refusal if the answer isn't there.

Rule sets covered:
- Digital Personal Data Protection Act (DPDP), 2023
- Indian Contract Act, 1872 (consideration, free consent, capacity, lawful object)

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 22+ (LTS)
- Docker Desktop (for `docker compose` path)

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# Fill in your API keys in .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Option B — Local Dev

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Project Structure

```
/README.md
/ARCHITECTURE.md
/AGENTS.md
/AGENTS_AND_SKILLS.md
/SPEC.md
/rules/                   # Rule library (YAML, data-driven)
/backend/                 # FastAPI app
/frontend/                # React + Vite app
/tests/                   # Unit tests (pytest)
/e2e/                     # Playwright E2E tests
/.github/workflows/ci.yml
/.env.example
/docker-compose.yml
```

---

## Running Tests

```bash
# Unit tests
cd backend
python -m pytest ../tests/ -v

# E2E (requires running stack)
cd e2e
npx playwright install
npx playwright test
```

---

## Environment Variables

Copy `.env.example` → `.env` and fill in your keys. **Never commit `.env`.**

| Variable | Description |
|---|---|
| `NVIDIA_API_KEY` | NVIDIA Build API key (`nvapi-...`) |
| `GEMINI_API_KEY` | Google AI Studio Gemini key |
| `CHROMA_PERSIST_PATH` | Path for ChromaDB persistence (default: `./chroma_data`) |

---

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full stack diagram, data model, and request flows.

---

## License

MIT
