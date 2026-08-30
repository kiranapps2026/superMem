from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import IngestJob, Project
from app.schemas import IngestQueued, IngestJobOut, IngestJobListResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/", response_model=IngestJobOut, status_code=status.HTTP_201_CREATED)
async def start_ingest(
    data: IngestQueued,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    project_result = await db.execute(
        select(Project).where(
            Project.id == data.project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    if project_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    job = IngestJob(
        project_id=data.project_id,
        workspace_id=tc.workspace_id,
        source_type=data.source_type,
        config=data.config,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/jobs", response_model=IngestJobListResponse)
async def list_jobs(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    result = await db.execute(
        select(IngestJob)
        .where(IngestJob.workspace_id == tc.workspace_id)
        .order_by(IngestJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    jobs = result.scalars().all()

    count_result = await db.execute(
        select(IngestJob).where(IngestJob.workspace_id == tc.workspace_id)
    )
    total = len(count_result.scalars().all())

    return IngestJobListResponse(
        items=[IngestJobOut.model_validate(j) for j in jobs],
        total=total,
    )


@router.get("/jobs/{job_id}", response_model=IngestJobOut)
async def get_job(
    job_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngestJob).where(
            IngestJob.id == job_id,
            IngestJob.workspace_id == tc.workspace_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Ingest job not found")
    return job
