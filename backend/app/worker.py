import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import async_session
from app.models.admin_config import AdminConfig
from app.services.job_search_orchestrator import run_scheduled_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_interval_hours() -> int:
    try:
        async with async_session() as db:
            result = await db.execute(
                select(AdminConfig).where(AdminConfig.key == "search_interval_hours")
            )
            config = result.scalar_one_or_none()
            return int(config.value) if config else 6
    except Exception:
        return 6


async def main():
    logger.info("Starting Jobbsøk worker...")

    interval_hours = await get_interval_hours()
    logger.info(f"Search interval: every {interval_hours} hours")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_scheduled_search,
        trigger=IntervalTrigger(hours=interval_hours),
        id="scheduled_search",
        name="Scheduled job search",
        replace_existing=True,
    )
    scheduler.start()

    logger.info("Worker started. Press Ctrl+C to exit.")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
