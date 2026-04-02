import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.job_listing import JobListing
from app.models.job_source import JobSource
from app.models.search_run import SearchRun
from app.models.user import User
from app.services.matching_service import match_for_user
from app.services.notification_service import notify_new_matches

logger = logging.getLogger(__name__)


async def fetch_all_sources() -> int:
    """Fetch jobs from all enabled sources. Returns total new jobs."""
    from app.fetchers.registry import get_fetchers

    async with async_session() as db:
        result = await db.execute(select(JobSource).where(JobSource.is_enabled.is_(True)))
        sources = result.scalars().all()

        total_new = 0
        fetchers = get_fetchers()

        for source in sources:
            fetcher = fetchers.get(source.name)
            if not fetcher:
                logger.warning(f"No fetcher for source: {source.name}")
                continue

            try:
                new_jobs = await fetcher.fetch_jobs(source, db)
                total_new += len(new_jobs)
                source.last_fetched_at = datetime.now(timezone.utc)
                logger.info(f"Fetched {len(new_jobs)} new jobs from {source.display_name}")
            except Exception as e:
                logger.error(f"Failed to fetch from {source.name}: {e}")

        await db.commit()
        return total_new


async def execute_search_run(user_id: str, triggered_by: str) -> None:
    """Execute a full search run for a user: fetch + match + notify."""
    uid = uuid.UUID(user_id)

    async with async_session() as db:
        # Load user
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found: {user_id}")
            return

        # Create search run
        search_run = SearchRun(user_id=uid, triggered_by=triggered_by)
        db.add(search_run)
        await db.flush()

        try:
            # Fetch new jobs from all sources
            new_jobs_count = await fetch_all_sources()
            search_run.jobs_fetched = new_jobs_count

            # Match jobs for this user
            results = await match_for_user(uid, search_run, db)
            search_run.jobs_matched = len(results)

            # Notify user of high-score matches
            high_score = [r for r in results if r.relevance_score >= 0.5]
            if high_score:
                # Build job data lookup
                job_ids = [r.job_listing_id for r in high_score]
                jr = await db.execute(select(JobListing).where(JobListing.id.in_(job_ids)))
                jobs = {j.id: {"title": j.title, "company": j.company_name, "location": j.location, "url": j.url} for j in jr.scalars().all()}
                await notify_new_matches(user, high_score, jobs, db)

            search_run.status = "completed"
            search_run.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Search run failed: {e}")
            search_run.status = "failed"
            search_run.error_message = str(e)
            search_run.completed_at = datetime.now(timezone.utc)

        await db.commit()


async def run_scheduled_search() -> None:
    """Run search for all active users. Called by the scheduler."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.is_active.is_(True)))
        users = result.scalars().all()

    for user in users:
        try:
            await execute_search_run(str(user.id), "scheduled")
        except Exception as e:
            logger.error(f"Scheduled search failed for user {user.id}: {e}")
