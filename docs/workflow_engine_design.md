# Workflow engine design

## What it is
A small workflow executor that runs a **DAG of steps**. Each step:
- has a name
- has a `kind` (implementation)
- lists dependencies (`depends_on`)
- can declare retries and rate limits

The workflow file is `configs/workflow.yaml`.

## Why this design
We need:
- DAG validation (no cycles)
- parallel execution when possible
- clear retry + rate limiting around the LLM step
- something a reviewer can read in 10 minutes

So the runner does **layered execution**:
- Compute topological layers (steps with no unmet dependencies)
- Run each layer in parallel (`asyncio.gather`)
- Move to the next layer

## Cycle detection
`WorkflowGraph.validate()` runs a DFS and fails fast on cycles. That prevents accidentally creating a workflow
that can’t ever complete.

## Rate limiting
The `llm_extract` step is rate-limited via a small token bucket:
- `rate_limit_rps`
- `rate_limit_burst`

This keeps the system stable during spikes and prevents hard API throttling.

## Parallelism
We support two kinds:
1) **Document-level parallelism**: run more Celery workers.
2) **Step-level parallelism**: independent steps in the same layer run concurrently.

There’s also a small fan-out example in `normalize_line_items` where we parallelize per line item.

## Failure behavior
- If a step fails, the task is retried (Celery retry + step retries).
- If retries are exhausted, job status becomes `failed` and an audit event is recorded.

This keeps the failure story simple, observable, and safe.
