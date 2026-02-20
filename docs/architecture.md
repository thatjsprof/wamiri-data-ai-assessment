# Architecture

**API-first** design:

- **FastAPI** receives uploads and returns `{job_id, document_id}`.
- **Postgres** is the source of truth for:
  - Documents
  - Jobs
  - Review queue
  - Audit trail
- **Celery + Redis** runs background work (scale by adding workers).
- **AWS Textract** performs OCR for scanned PDFs/images.
- **OpenAI** performs structured extraction with JSON schema enforcement.
- **Prometheus** exposes metrics at `/metrics`.
- **React UI** provides upload + review dashboard.

## Why this is scalable

- API servers scale horizontally behind a load balancer.
- Workers scale horizontally based on throughput.
- Postgres ensures durable state and safe concurrency.
- Review queue uses Postgres row locks to avoid duplicate claims.

## Data safety

- The worker updates status transitions in Postgres.
- Outputs are written atomically.
- Human corrections are stored as locked fields and merged back into the document.
