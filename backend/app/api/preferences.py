import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job_preference import JobPreference
from app.models.user import User
from app.schemas.job_preference import JobPreferenceCreate, JobPreferenceResponse, JobPreferenceUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=list[JobPreferenceResponse])
async def list_preferences(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobPreference).where(JobPreference.user_id == user.id))
    return result.scalars().all()


@router.post("", response_model=JobPreferenceResponse, status_code=201)
async def create_preference(
    data: JobPreferenceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pref = JobPreference(user_id=user.id, **data.model_dump())
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref


@router.put("/{pref_id}", response_model=JobPreferenceResponse)
async def update_preference(
    pref_id: uuid.UUID,
    data: JobPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobPreference).where(JobPreference.id == pref_id, JobPreference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)
    await db.commit()
    await db.refresh(pref)
    return pref


@router.delete("/{pref_id}", status_code=204)
async def delete_preference(
    pref_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobPreference).where(JobPreference.id == pref_id, JobPreference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    await db.delete(pref)
    await db.commit()
