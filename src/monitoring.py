from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

import yaml
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .common.time import utcnow
from .db.engine import SessionLocal
from .db.models import Job, ReviewItem
from .observability.metrics import SLA_BREACHES, SLA_CURRENT_VALUE, SLA_IS_BREACHING


def _parse_window(s: str) -> timedelta:
    s = s.strip().lower()
    if s.endswith("m"):
        return timedelta(minutes=int(s[:-1]))
    if s.endswith("h"):
        return timedelta(hours=int(s[:-1]))
    raise ValueError(f"unsupported_window:{s}")


def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = max(0, math.ceil(0.95 * len(values)) - 1)
    return float(values[k])


@dataclass(frozen=True)
class SLADef:
    name: str
    threshold: float
    comparator: str  # lt/gt
    window: str
    severity: str
    description: str = ""


def load_sla_definitions(path: str = "configs/sla_definitions.yaml") -> List[SLADef]:
    raw = yaml.safe_load(open(path, "r", encoding="utf-8"))
    out = []
    for s in raw.get("slas", []):
        out.append(
            SLADef(
                name=s["name"],
                threshold=float(s["threshold"]),
                comparator=s["comparator"],
                window=s["window"],
                severity=s["severity"],
                description=s.get("description", ""),
            )
        )
    return out


async def compute_sla_values(session: AsyncSession) -> Dict[str, float]:
    now = utcnow()

    # 5m latency window
    latency_window = timedelta(minutes=5)
    q = select(Job.started_at, Job.completed_at).where(
        Job.completed_at.is_not(None),
        Job.started_at.is_not(None),
        Job.completed_at >= (now - latency_window),
    )
    res = await session.execute(q)
    latencies = []
    for started, completed in res.all():
        if started and completed:
            latencies.append((completed - started).total_seconds())
    p95_latency = _p95(latencies)

    # 15m throughput window -> docs/hour
    throughput_window = timedelta(minutes=15)
    q2 = (
        select(func.count())
        .select_from(Job)
        .where(
            Job.completed_at.is_not(None),
            Job.completed_at >= (now - throughput_window),
            Job.status.in_(["completed", "review_pending"]),
        )
    )
    completed_15m = int((await session.execute(q2)).scalar() or 0)
    docs_per_hour = (
        (completed_15m / (throughput_window.total_seconds() / 3600.0))
        if throughput_window.total_seconds()
        else 0.0
    )

    # 5m error rate %
    err_window = timedelta(minutes=5)
    q_total = (
        select(func.count())
        .select_from(Job)
        .where(
            Job.completed_at.is_not(None),
            Job.completed_at >= (now - err_window),
            Job.status.in_(["completed", "review_pending", "failed"]),
        )
    )
    total_5m = int((await session.execute(q_total)).scalar() or 0)

    q_fail = (
        select(func.count())
        .select_from(Job)
        .where(
            Job.completed_at.is_not(None),
            Job.completed_at >= (now - err_window),
            Job.status == "failed",
        )
    )
    failed_5m = int((await session.execute(q_fail)).scalar() or 0)
    error_rate_percent = (failed_5m / total_5m * 100.0) if total_5m else 0.0

    # queue depth
    q_qd = (
        select(func.count())
        .select_from(ReviewItem)
        .where(ReviewItem.status == "pending")
    )
    queue_depth = int((await session.execute(q_qd)).scalar() or 0)

    # 1h breach percent (latency > 30s OR failed)
    breach_window = timedelta(hours=1)
    q_jobs = select(Job.started_at, Job.completed_at, Job.status).where(
        Job.completed_at.is_not(None),
        Job.started_at.is_not(None),
        Job.completed_at >= (now - breach_window),
    )
    res = await session.execute(q_jobs)
    jobs = res.all()

    total_1h = len(jobs)
    breaches = 0
    for started, completed, status in jobs:
        if status == "failed":
            breaches += 1
            continue
        if started and completed and (completed - started).total_seconds() > 30:
            breaches += 1
    sla_breach_percent = (breaches / total_1h * 100.0) if total_1h else 0.0

    return {
        "p95_latency_seconds": p95_latency,
        "docs_per_hour": float(docs_per_hour),
        "error_rate_percent": float(error_rate_percent),
        "review_queue_depth": float(queue_depth),
        "sla_breach_percent": float(sla_breach_percent),
    }


def _is_breaching(value: float, comparator: str, threshold: float) -> bool:
    if comparator == "lt":
        return value >= threshold
    if comparator == "gt":
        return value <= threshold
    raise ValueError(f"bad_comparator:{comparator}")


async def evaluate_slas_once(
    session: AsyncSession, defs: List[SLADef]
) -> Dict[str, Any]:
    values = await compute_sla_values(session)
    results = {}
    for d in defs:
        v = float(values.get(d.name, 0.0))
        breaching = _is_breaching(v, d.comparator, d.threshold)
        SLA_CURRENT_VALUE.labels(sla=d.name).set(v)
        SLA_IS_BREACHING.labels(sla=d.name).set(1 if breaching else 0)
        if breaching:
            SLA_BREACHES.labels(sla=d.name).inc()
        results[d.name] = {"value": v, "breaching": breaching, "severity": d.severity}
    return results


# Celery periodic scheduling hook (optional but included)
def maybe_start_sla_scheduler(sender) -> None:
    try:
        sender.add_periodic_task(60.0, run_sla_evaluation.s())
    except Exception:
        # If beat isn't running, this is harmless.
        pass


# Celery task entrypoint
from celery import shared_task  # noqa: E402


@shared_task(name="src.monitoring.run_sla_evaluation")
def run_sla_evaluation() -> dict:
    import asyncio

    return asyncio.run(_run_eval())


async def _run_eval() -> dict:
    defs = load_sla_definitions()
    async with SessionLocal() as session:
        return await evaluate_slas_once(session, defs)
