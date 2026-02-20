# Module architecture

This project is split into a few boring (good) layers. Each layer has one job.

## API layer (FastAPI)
Location: `src/routes/*`

- Receives uploads
- Returns job status
- Exposes the review queue endpoints for the UI

The API layer does not do heavy work. It writes state to Postgres and schedules a worker task.

## Persistence layer (Postgres)
Location: `src/db/*`, `src/repositories/*`

Postgres is the source of truth. If the worker dies mid-way, we can still see exactly what happened:
- `documents` keeps the latest extraction snapshot + locked fields
- `jobs` tracks a single processing run (status, outputs, timestamps)
- `review_items` is the human queue
- `audit_logs` is an append-only trail

## Workflow layer (DAG)
Location: `src/workflow/*`

The processing itself runs as a small DAG (directed acyclic graph). The workflow definition lives in
`configs/workflow.yaml`.

Why not a full workflow framework?
- The assessment needs DAG support and validation.
- We keep it small so it’s easy to read and explain.

## Service layer
Location: `src/services/*`

These are concrete implementations:
- OCR: AWS Textract (real OCR)
- LLM extraction: OpenAI with JSON schema
- Validation: config-driven checks
- Output writer: JSON + Parquet

The workflow steps call these services.
