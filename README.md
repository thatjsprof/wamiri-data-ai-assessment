# DocProc — OCR + Extraction + Review Queue (API-first)

A small, production-shaped document processing service:

- Upload PDF/image
- OCR with **AWS Textract**
- Extract structured invoice fields with **OpenAI JSON schema**
- Validate fields
- Save outputs (JSON + Parquet)
- Route questionable cases into a **human review queue**
- Track everything by both **document_id** and **job_id**
- Expose metrics + SLA signals via **Prometheus**

## Quick start (local)

### 0) Requirements

- Python 3.11+
- Node 18+
- Docker (for Postgres + Redis)

### 1) Start Postgres + Redis

```bash
docker compose up -d
```

### 2) Create and activate a virtualenv

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install packages

```bash
pip install -r requirements.txt
```

### 4) Configure environment

Create a `.env` file in the repo root:

```env
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/docproc
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini

# AWS (Textract + S3)
AWS_REGION=eu-west-1
AWS_TEXTRACT_S3_BUCKET=your-bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

> Textract multi-page PDFs require the document to be in S3. The worker uploads a temp object and deletes it after OCR.

### 5) Run the API

```bash
uvicorn src.app:app --reload
```

### 6) Run the worker (new terminal, same venv)

```bash
celery -A src.worker.celery_app worker -l INFO
```

### 7) Run SLA evaluation (optional, but part of the assessment)

You can run the SLA evaluator as a scheduled task using Celery beat:

```bash
celery -A src.worker.celery_app beat -l INFO
```

### 8) Run the UI

```bash
cd ui
npm install
npm run dev
```

Open the dashboard at `http://localhost:5173`.

---

## API endpoints

- `POST /v1/process` — upload a document, returns `{job_id, document_id}`
- `GET /v1/jobs/{job_id}` — job status + outputs + extraction snapshot
- `GET /v1/queue` — list pending review items
- `POST /v1/queue/claim` — atomically claim next item (no double-claims)
- `POST /v1/queue/{id}/submit` — approve/correct/reject

Operational:

- `GET /health`
- `GET /metrics`

---

## Workflow (DAG)

Workflow steps are defined in `configs/workflow.yaml` and executed as a validated DAG:

- cycle detection
- topological layers (parallel where possible)
- per-step retries
- per-step rate limiting (used for LLM calls)

Docs:

- `docs/workflow_engine_design.md`
- `docs/module_architecture.md`

---

## Tests

Run everything that doesn't require AWS/OpenAI:

```bash
pytest -q
```

Quality + perf tests are present under `tests/quality` and `tests/performance`.
Some integration tests are designed to be run with AWS credentials (Textract) or LocalStack.
