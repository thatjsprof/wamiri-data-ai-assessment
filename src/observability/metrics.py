from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

# Core pipeline metrics
DOCS_PROCESSED = Counter("docs_processed_total", "Total documents processed", ["status"])
DOC_PROCESS_LATENCY = Histogram(
    "doc_processing_seconds",
    "Document processing latency seconds",
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60),
)
ERRORS = Counter("doc_processing_errors_total", "Total processing errors")
REVIEW_QUEUE_DEPTH = Gauge("review_queue_depth", "Pending human review items")

# SLA evaluation metrics (computed in-app)
SLA_BREACHES = Counter("sla_breaches_total", "Total SLA breaches detected", ["sla"])
SLA_CURRENT_VALUE = Gauge("sla_current_value", "Current computed SLA value", ["sla"])
SLA_IS_BREACHING = Gauge("sla_is_breaching", "Whether the SLA is currently breaching (0/1)", ["sla"])
