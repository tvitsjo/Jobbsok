import os
import uuid as uuid_mod
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ExtractedSkillsUpdate, ProfileResponse, ProfileUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


async def _get_profile(user: User, db: AsyncSession) -> Profile:
    result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def _save_upload(file: UploadFile, subdir: str) -> str:
    upload_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    filename = f"{uuid_mod.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)
    return filepath


async def _run_extraction(profile_id: str):
    from app.services.llm_service import extract_profile
    await extract_profile(profile_id)


@router.get("", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _get_profile(user, db)


@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(user, db)
    if data.free_text is not None:
        profile.free_text = data.free_text
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/cv", response_model=ProfileResponse)
async def upload_cv(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    profile = await _get_profile(user, db)
    profile.cv_file_path = await _save_upload(file, "cv")
    profile.extraction_status = "processing"
    await db.commit()
    await db.refresh(profile)

    background_tasks.add_task(_run_extraction, str(profile.id))
    return profile


@router.post("/linkedin", response_model=ProfileResponse)
async def upload_linkedin(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    profile = await _get_profile(user, db)
    profile.linkedin_image_path = await _save_upload(file, "linkedin")
    profile.extraction_status = "processing"
    await db.commit()
    await db.refresh(profile)

    background_tasks.add_task(_run_extraction, str(profile.id))
    return profile


@router.post("/extract", response_model=ProfileResponse)
async def trigger_extraction(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(user, db)
    profile.extraction_status = "processing"
    await db.commit()
    await db.refresh(profile)

    background_tasks.add_task(_run_extraction, str(profile.id))
    return profile


@router.put("/skills", response_model=ProfileResponse)
async def update_skills(
    data: ExtractedSkillsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(user, db)
    profile.extracted_skills = data.extracted_skills
    await db.commit()
    await db.refresh(profile)
    return profile
