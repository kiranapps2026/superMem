from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Project
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from datetime import datetime, timezone

router = APIRouter(prefix="/projects", tags=["projects"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    return result.scalars().all()


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        workspace_id=tc.workspace_id,
        name=data.name,
        description=data.description,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    project.updated_at = _now()
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.deleted_at = _now()
    await db.commit()
