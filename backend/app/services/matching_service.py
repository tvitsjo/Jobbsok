import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_listing import JobListing
from app.models.job_preference import JobPreference
from app.models.profile import Profile
from app.models.search_result import SearchResult
from app.models.search_run import SearchRun
from app.services.llm_service import score_jobs

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
MIN_SCORE_THRESHOLD = 0.3


def _pre_filter(job: JobListing, preferences: list[JobPreference]) -> bool:
    """Cheap keyword/location pre-filter to reduce LLM calls."""
    if not preferences:
        return True

    job_text = f"{job.title} {job.description or ''} {job.location or ''}".lower()

    for pref in preferences:
        if not pref.is_active:
            continue

        # Check exclude keywords first
        for kw in (pref.exclude_keywords or []):
            if kw.lower() in job_text:
                return False

        # Check if any positive signal matches
        has_match = False
        for title in (pref.job_titles or []):
            if title.lower() in job_text:
                has_match = True
                break
        if not has_match:
            for kw in (pref.keywords or []):
                if kw.lower() in job_text:
                    has_match = True
                    break
        if not has_match:
            for loc in (pref.locations or []):
                if loc.lower() in job_text:
                    has_match = True
                    break

        if has_match:
            return True

    return False


async def match_for_user(user_id: uuid.UUID, search_run: SearchRun, db: AsyncSession) -> list[SearchResult]:
    # Load profile
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile or not profile.summary:
        logger.warning(f"No profile/summary for user {user_id}")
        return []

    # Load preferences
    result = await db.execute(
        select(JobPreference).where(JobPreference.user_id == user_id, JobPreference.is_active.is_(True))
    )
    preferences = list(result.scalars().all())

    # Get already-scored job IDs for this user
    result = await db.execute(
        select(SearchResult.job_listing_id).where(SearchResult.user_id == user_id)
    )
    scored_job_ids = {row[0] for row in result.all()}

    # Load active job listings not yet scored
    result = await db.execute(
        select(JobListing).where(JobListing.is_active.is_(True))
    )
    all_jobs = result.scalars().all()
    new_jobs = [j for j in all_jobs if j.id not in scored_job_ids]

    # Pre-filter
    filtered_jobs = [j for j in new_jobs if _pre_filter(j, preferences)]
    logger.info(f"Pre-filter: {len(new_jobs)} → {len(filtered_jobs)} jobs for user {user_id}")

    if not filtered_jobs:
        return []

    # Build dismiss history for LLM context
    result = await db.execute(
        select(SearchResult)
        .where(
            SearchResult.user_id == user_id,
            SearchResult.is_dismissed.is_(True),
            SearchResult.dismiss_reason.isnot(None),
        )
        .limit(20)
    )
    dismissed = result.scalars().all()
    dismiss_history = []
    for d in dismissed:
        # Load the job listing for context
        jr = await db.execute(select(JobListing).where(JobListing.id == d.job_listing_id))
        jl = jr.scalar_one_or_none()
        if jl:
            dismiss_history.append({
                "title": jl.title,
                "company": jl.company_name or "Ukjent",
                "reason": d.dismiss_reason,
            })

    # Build preferences dict for LLM
    prefs_dict = {
        "job_titles": [],
        "locations": [],
        "keywords": [],
        "exclude_keywords": [],
    }
    for p in preferences:
        prefs_dict["job_titles"].extend(p.job_titles or [])
        prefs_dict["locations"].extend(p.locations or [])
        prefs_dict["keywords"].extend(p.keywords or [])
        prefs_dict["exclude_keywords"].extend(p.exclude_keywords or [])

    # Batch score with LLM
    results: list[SearchResult] = []
    for i in range(0, len(filtered_jobs), BATCH_SIZE):
        batch = filtered_jobs[i : i + BATCH_SIZE]
        jobs_data = [
            {
                "id": str(j.id),
                "title": j.title,
                "company": j.company_name,
                "location": j.location,
                "description": j.description,
            }
            for j in batch
        ]

        scores = await score_jobs(profile.summary, prefs_dict, dismiss_history, jobs_data, db)

        for score_item in scores:
            job_id = score_item.get("job_id")
            relevance = score_item.get("score", 0.0)
            reasoning = score_item.get("reasoning", "")

            if relevance < MIN_SCORE_THRESHOLD:
                continue

            try:
                sr = SearchResult(
                    search_run_id=search_run.id,
                    user_id=user_id,
                    job_listing_id=uuid.UUID(job_id),
                    relevance_score=relevance,
                    llm_reasoning=reasoning,
                )
                db.add(sr)
                results.append(sr)
            except (ValueError, Exception) as e:
                logger.warning(f"Failed to create search result: {e}")

    await db.flush()
    return results
