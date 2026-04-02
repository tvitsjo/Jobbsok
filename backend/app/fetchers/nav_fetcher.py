import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fetchers.base import BaseJobFetcher
from app.models.job_listing import JobListing
from app.models.job_source import JobSource

logger = logging.getLogger(__name__)

NAV_FEED_URL = "https://pam-stilling-feed.nav.no/api/v1/feed"


class NAVFetcher(BaseJobFetcher):
    source_name = "nav_arbeidsplassen"

    async def fetch_jobs(self, source: JobSource, db: AsyncSession) -> list[JobListing]:
        config = source.config or {}
        bearer_token = config.get("bearer_token", "")
        if not bearer_token:
            logger.warning("NAV bearer token not configured")
            return []

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
        }

        # Use cursor for pagination
        cursor_data = json.loads(source.last_fetch_cursor or "{}")
        url = cursor_data.get("next_url", NAV_FEED_URL)
        etag = cursor_data.get("etag")
        if etag:
            headers["If-None-Match"] = etag

        new_listings: list[JobListing] = []

        async with httpx.AsyncClient(timeout=30) as client:
            pages_fetched = 0
            max_pages = 10

            while url and pages_fetched < max_pages:
                response = await client.get(url, headers=headers)

                if response.status_code == 304:
                    logger.info("NAV feed: no changes since last fetch")
                    break

                if response.status_code != 200:
                    logger.error(f"NAV feed returned {response.status_code}")
                    break

                data = response.json()
                items = data.get("items", [])

                for item in items:
                    content = item.get("_source", {})
                    external_id = str(content.get("uuid", item.get("id", "")))
                    if not external_id:
                        continue

                    # Check if already exists
                    existing = await db.execute(
                        select(JobListing).where(
                            JobListing.source_id == source.id,
                            JobListing.external_id == external_id,
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Parse dates
                    posted_at = None
                    if pub := content.get("published"):
                        try:
                            posted_at = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                        except ValueError:
                            pass

                    expires_at = None
                    if exp := content.get("expires"):
                        try:
                            expires_at = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                        except ValueError:
                            pass

                    # Extract location
                    locations = content.get("locations", [])
                    location_str = ", ".join(
                        loc.get("city") or loc.get("municipal") or loc.get("county") or ""
                        for loc in locations
                    )

                    listing = JobListing(
                        source_id=source.id,
                        external_id=external_id,
                        title=content.get("title", "Ukjent stilling"),
                        company_name=content.get("businessName") or content.get("employer", {}).get("name"),
                        description=content.get("adtext_no") or content.get("adtext"),
                        location=location_str or None,
                        job_type=content.get("engagementtype"),
                        url=content.get("sourceurl") or content.get("link"),
                        raw_data=content,
                        posted_at=posted_at,
                        expires_at=expires_at,
                    )
                    db.add(listing)
                    new_listings.append(listing)

                # Update cursor
                next_url = data.get("next")
                new_etag = response.headers.get("ETag")
                source.last_fetch_cursor = json.dumps({
                    "next_url": next_url or url,
                    "etag": new_etag or etag,
                })

                url = next_url
                pages_fetched += 1

                if not next_url:
                    break

        await db.flush()
        return new_listings
