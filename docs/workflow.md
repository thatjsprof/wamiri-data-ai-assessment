# Workflow execution (DAG)

The system runs document processing as a small DAG (directed acyclic graph).  
A DAG is just a set of steps where some steps must finish before others can start.

Why a DAG?
- It's easy to validate (no cycles).
- We can run independent steps in parallel.
- It's simple to extend without rewriting the worker.

## Current workflow (invoice_processing_v1)

1) **ocr**  
   Reads text from PDF/image using Textract.

2) **llm_extract**  
   Turns raw text into structured invoice fields using OpenAI with a JSON schema.

3) **normalize_line_items** (fan-out)  
   Cleans each line item in parallel (small, fast step).

4) **validate**  
   Applies required field checks and formats.

5) **write_outputs**  
   Writes JSON + Parquet outputs.

6) **persist**  
   Updates Document + Job rows and writes an audit event.

7) **review_gate**  
   If validation failed, enqueue a ReviewItem and attach it to the Job.

## Concurrency + rate limiting

- The runner executes steps when their dependencies are satisfied.
- `llm_extract` is rate-limited (RPS + burst) to avoid API throttling.
- Steps can also declare `max_concurrency` for internal fan-out.

This is intentionally small and explicit: no heavy workflow framework, but it covers the core expectations.
