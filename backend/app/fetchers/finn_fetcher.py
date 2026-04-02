import logging
import re

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fetchers.base import BaseJobFetcher
from app.models.job_listing import JobListing
from app.models.job_source import JobSource

logger = logging.getLogger(__name__)

FINN_SEARCH_URL = "https://www.finn.no/job/fulltime/search"


class FinnFetcher(BaseJobFetcher):
    source_name = "finn"

    async def fetch_jobs(self, source: JobSource, db: AsyncSession) -> list[JobListing]:
        config = source.config or {}
        search_query = config.get("search_query", "")
        location = config.get("location", "")
        max_pages = config.get("max_pages", 3)

        new_listings: list[JobListing] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(1, max_pages + 1):
                params = {"page": page}
                if search_query:
                    params["q"] = search_query
                if location:
                    params["location"] = location

                try:
                    response = await client.get(
                        FINN_SEARCH_URL,
                        params=params,
                        headers={"User-Agent": "Jobbsok/1.0"},
                    )
                    if response.status_code != 200:
                        logger.warning(f"Finn returned {response.status_code}")
                        break

                    soup = BeautifulSoup(response.text, "html.parser")
                    articles = soup.find_all("article")

                    if not articles:
                        break

                    for article in articles:
                        link = article.find("a", href=True)
                        if not link:
                            continue

                        href = link.get("href", "")
                        # Extract Finn ID from URL
                        match = re.search(r"/(\d+)$", href)
                        if not match:
                            continue

                        external_id = match.group(1)

                        # Check if already exists
                        existing = await db.execute(
                            select(JobListing).where(
                                JobListing.source_id == source.id,
                                JobListing.external_id == external_id,
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        title = link.get_text(strip=True) or "Ukjent stilling"
                        company_el = article.find(string=re.compile(r".+"))
                        location_el = article.find("span", class_=re.compile(r"location", re.I))

                        listing = JobListing(
                            source_id=source.id,
                            external_id=external_id,
                            title=title,
                            company_name=None,
                            location=location_el.get_text(strip=True) if location_el else None,
                            url=href if href.startswith("http") else f"https://www.finn.no{href}",
                        )
                        db.add(listing)
                        new_listings.append(listing)

                except Exception as e:
                    logger.error(f"Finn scraping error on page {page}: {e}")
                    break

        await db.flush()
        return new_listings
