import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.search_result import SearchResult
from app.models.user import User
from app.schemas.job_listing import DismissRequest, SearchResultResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[SearchResultResponse])
async def list_jobs(
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    saved_only: bool = False,
    hide_dismissed: bool = True,
    limit: int = Query(50, le=200),
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SearchResult)
        .options(joinedload(SearchResult.job_listing))
        .where(SearchResult.user_id == user.id, SearchResult.relevance_score >= min_score)
        .order_by(SearchResult.relevance_score.desc(), SearchResult.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if saved_only:
        query = query.where(SearchResult.is_saved.is_(True))
    if hide_dismissed:
        query = query.where(SearchResult.is_dismissed.is_(False))

    result = await db.execute(query)
    return result.scalars().unique().all()


@router.get("/{result_id}", response_model=SearchResultResponse)
async def get_job(
    result_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SearchResult)
        .options(joinedload(SearchResult.job_listing))
        .where(SearchResult.id == result_id, SearchResult.user_id == user.id)
    )
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Result not found")

    sr.is_seen = True
    await db.commit()
    await db.refresh(sr)
    return sr


@router.post("/{result_id}/save")
async def toggle_save(
    result_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SearchResult).where(SearchResult.id == result_id, SearchResult.user_id == user.id)
    )
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Result not found")

    sr.is_saved = not sr.is_saved
    await db.commit()
    return {"is_saved": sr.is_saved}


@router.post("/{result_id}/dismiss")
async def dismiss_job(
    result_id: uuid.UUID,
    data: DismissRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SearchResult).where(SearchResult.id == result_id, SearchResult.user_id == user.id)
    )
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Result not found")

    sr.is_dismissed = True
    sr.dismiss_reason = data.reason
    await db.commit()
    return {"is_dismissed": True, "dismiss_reason": data.reason}


@router.post("/search")
async def trigger_search(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    from app.services.job_search_orchestrator import execute_search_run
    background_tasks.add_task(execute_search_run, str(user.id), "manual")
    return {"status": "search_started"}
