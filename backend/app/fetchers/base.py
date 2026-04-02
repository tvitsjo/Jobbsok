from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_listing import JobListing
from app.models.job_source import JobSource


class BaseJobFetcher(ABC):
    source_name: str

    @abstractmethod
    async def fetch_jobs(self, source: JobSource, db: AsyncSession) -> list[JobListing]:
        """Fetch new/updated job listings from the source."""
        pass
