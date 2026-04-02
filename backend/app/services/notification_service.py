import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.search_result import SearchResult
from app.models.user import User
from app.services.email_service import send_job_matches_email


async def notify_new_matches(
    user: User,
    results: list[SearchResult],
    job_data: dict[uuid.UUID, dict],
    db: AsyncSession,
) -> None:
    """Create in-app notification and send email for new matches.

    job_data: mapping of job_listing_id → {"title", "company", "location", "url"}
    """
    if not results:
        return

    # Create in-app notification
    notif = Notification(
        user_id=user.id,
        type="new_matches",
        title=f"{len(results)} nye jobbmatcher funnet!",
        body=f"Vi har funnet {len(results)} nye relevante jobber for deg.",
        link="/jobs",
    )
    db.add(notif)

    # Mark results as notified
    email_matches = []
    for sr in results:
        sr.is_notified = True
        jd = job_data.get(sr.job_listing_id, {})
        email_matches.append({
            "title": jd.get("title", "Ukjent stilling"),
            "company": jd.get("company", "Ukjent"),
            "location": jd.get("location", "Ukjent"),
            "score": sr.relevance_score,
            "url": jd.get("url", "#"),
            "result_id": str(sr.id),
        })

    await db.flush()

    # Send email if configured
    recipients = user.notification_emails or []
    if recipients:
        await send_job_matches_email(recipients, email_matches)
