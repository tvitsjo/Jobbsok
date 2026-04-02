import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_job_matches_email(
    recipients: list[str],
    matches: list[dict],
) -> None:
    """Send email with new job matches.

    matches: list of {"title", "company", "location", "score", "url", "result_id"}
    """
    if not recipients or not matches:
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured, skipping email")
        return

    subject = f"Jobbsøk: {len(matches)} nye jobber funnet!"

    # Build HTML body
    job_rows = ""
    for m in matches:
        score_pct = int(m["score"] * 100)
        frontend_url = f"{settings.FRONTEND_URL}/jobs/{m['result_id']}"
        original_url = m.get("url", "#")
        job_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">
                <strong><a href="{frontend_url}">{m['title']}</a></strong><br>
                <span style="color: #666;">{m.get('company', 'Ukjent')} — {m.get('location', 'Ukjent')}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                <span style="background: {'#22c55e' if score_pct >= 70 else '#f59e0b'}; color: white; padding: 4px 12px; border-radius: 12px;">
                    {score_pct}%
                </span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">
                <a href="{original_url}">Se annonse</a>
            </td>
        </tr>
        """

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1e40af;">Nye jobbmatcher!</h2>
        <p>Vi har funnet {len(matches)} nye relevante jobber for deg:</p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f1f5f9;">
                <th style="padding: 12px; text-align: left;">Stilling</th>
                <th style="padding: 12px;">Match</th>
                <th style="padding: 12px;">Lenke</th>
            </tr>
            {job_rows}
        </table>
        <p style="margin-top: 24px;">
            <a href="{settings.FRONTEND_URL}/jobs" style="background: #1e40af; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                Se alle jobber
            </a>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 32px;">
            Du mottar denne e-posten fordi du har aktivert jobbvarsler på Jobbsøk.
        </p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent to {recipients}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
