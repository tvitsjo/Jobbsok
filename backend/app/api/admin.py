import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_config import AdminConfig
from app.models.job_listing import JobListing
from app.models.job_source import JobSource
from app.models.search_result import SearchResult
from app.models.search_run import SearchRun
from app.models.user import User
from app.schemas.admin import (
    AdminConfigResponse,
    AdminConfigUpdate,
    JobSourceResponse,
    JobSourceUpdate,
    SystemStats,
)
from app.api.deps import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/config", response_model=list[AdminConfigResponse])
async def get_config(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AdminConfig))
    return result.scalars().all()


@router.put("/config/{key}", response_model=AdminConfigResponse)
async def update_config(
    key: str,
    data: AdminConfigUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AdminConfig).where(AdminConfig.key == key))
    config = result.scalar_one_or_none()
    if config:
        config.value = data.value
    else:
        config = AdminConfig(key=key, value=data.value)
        db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/sources", response_model=list[JobSourceResponse])
async def list_sources(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobSource))
    return result.scalars().all()


@router.put("/sources/{source_id}", response_model=JobSourceResponse)
async def update_source(
    source_id: uuid.UUID,
    data: JobSourceUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    await db.commit()
    await db.refresh(source)
    return source


@router.get("/stats", response_model=SystemStats)
async def get_stats(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    jobs = (await db.execute(select(func.count(JobListing.id)))).scalar() or 0
    runs = (await db.execute(select(func.count(SearchRun.id)))).scalar() or 0
    matches = (await db.execute(select(func.count(SearchResult.id)))).scalar() or 0
    return SystemStats(total_users=users, total_jobs=jobs, total_search_runs=runs, total_matches=matches)


@router.post("/trigger-fetch")
async def trigger_fetch(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_admin_user),
):
    from app.services.job_search_orchestrator import fetch_all_sources
    background_tasks.add_task(fetch_all_sources)
    return {"status": "fetch_started"}
