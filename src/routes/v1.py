from __future__ import annotations
from fastapi import APIRouter
from .v1_process import router as process_router
from .v1_jobs import router as jobs_router
from .v1_queue import router as queue_router

router = APIRouter()
router.include_router(process_router)
router.include_router(jobs_router)
router.include_router(queue_router)
