# Monitoring & alerting runbook

This project exposes metrics at `/metrics` (Prometheus format). The main purpose is:
- detect latency regressions
- detect throughput drops
- detect error spikes
- detect review queue build-up
- track SLA compliance

## Required SLAs (from the assessment)

- p95 latency < 30s (5 min window) — critical
- throughput > 4500 docs/hour (15 min window) — warning
- error rate < 1% (5 min window) — critical
- review queue depth < 500 (5 min window) — warning
- SLA breach percent < 0.1% (1 hour window) — critical

The definitions live in `configs/sla_definitions.yaml`.

## Metrics emitted by the service

### Core
- `docs_processed_total{status="completed|review_pending|failed"}`
- `doc_processing_seconds` (histogram)
- `doc_processing_errors_total`
- `review_queue_depth`

### SLA evaluation
- `sla_breaches_total{sla="<name>"}`
- `sla_current_value{sla="<name>"}`
- `sla_is_breaching{sla="<name>"}`

## How SLA monitoring works here (simple + practical)
There are two layers:

1) **Prometheus/Grafana layer** (recommended in real ops)
   - Use PromQL to compute p95 from the histogram
   - Use rates over counters for throughput and error rate
   - Alert based on `configs/sla_definitions.yaml`

2) **In-app evaluator** (included to satisfy the assessment)
   - A Celery periodic task runs every minute
   - It queries Postgres for the relevant window and computes:
     - p95 latency
     - docs/hour
     - error rate %
     - review queue depth
     - breach percent
   - It updates Prometheus gauges and increments breach counters

This is intentionally lightweight. In production you’d lean more heavily on Prometheus rules,
but it’s useful to have a “ground truth” evaluator too.

## Suggested alerts (examples)

### Critical: Latency p95 > 30s for 5m
Actions:
- check worker saturation
- check OpenAI response time / throttling
- check DB slow queries
- scale workers

### Critical: Error rate > 1% for 5m
Actions:
- inspect recent job failures (`GET /v1/jobs/{job_id}`)
- check AWS creds / Textract failures
- check OpenAI API key / model access
- roll back recent changes if needed

### Warning: Throughput < 4500/hour for 15m
Actions:
- scale worker count
- verify queue backlog
- check rate limiting settings for llm step

### Warning: Review queue depth > 500
Actions:
- add reviewers
- check if validation rules are too strict
- review LLM prompt/schema changes

## On-call quick checks
- `/health` should return `ok`
- `/metrics` should include `docs_processed_total`
- Postgres: are jobs moving from queued → processing → completed?
- Redis: is worker consuming tasks?

## Common fixes
- Scale out celery workers
- Increase OpenAI rate limit (carefully)
- Increase DB pool size if connections are saturated
