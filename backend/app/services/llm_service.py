import base64
import json
import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.admin_config import AdminConfig
from app.models.profile import Profile
from app.models.search_result import SearchResult

logger = logging.getLogger(__name__)


async def _get_openrouter_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


async def _get_model(db: AsyncSession) -> str:
    result = await db.execute(select(AdminConfig).where(AdminConfig.key == "openrouter_model"))
    config = result.scalar_one_or_none()
    return config.value if config else "anthropic/claude-sonnet-4"


async def extract_profile(profile_id: str) -> None:
    async with async_session() as db:
        result = await db.execute(select(Profile).where(Profile.id == uuid.UUID(profile_id)))
        profile = result.scalar_one_or_none()
        if not profile:
            return

        try:
            client = await _get_openrouter_client()
            model = await _get_model(db)
            messages: list[dict] = []

            system_prompt = (
                "Du er en ekspert på å analysere CV-er og profesjonelle profiler. "
                "Ekstraher følgende informasjon og returner som JSON:\n"
                '{"skills": ["liste", "med", "ferdigheter"], '
                '"experience": [{"title": "Stilling", "company": "Firma", "years": "Periode"}], '
                '"education": [{"degree": "Grad", "school": "Skole", "year": "År"}], '
                '"languages": ["Norsk", "Engelsk"], '
                '"summary": "Kort oppsummering av kandidaten"}'
            )
            messages.append({"role": "system", "content": system_prompt})

            content_parts: list[dict] = []

            if profile.free_text:
                content_parts.append({"type": "text", "text": f"Brukerens egen beskrivelse:\n{profile.free_text}"})

            if profile.cv_file_path:
                try:
                    with open(profile.cv_file_path, "rb") as f:
                        pdf_data = base64.b64encode(f.read()).decode()
                    content_parts.append({
                        "type": "text",
                        "text": f"CV-fil (base64-kodet PDF):\n{pdf_data[:5000]}...\n\nAnalyser dette som en CV.",
                    })
                except FileNotFoundError:
                    logger.warning(f"CV file not found: {profile.cv_file_path}")

            if profile.linkedin_image_path:
                try:
                    with open(profile.linkedin_image_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    ext = profile.linkedin_image_path.rsplit(".", 1)[-1].lower()
                    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{img_data}"},
                    })
                    content_parts.append({"type": "text", "text": "Analyser dette LinkedIn-skjermbildet."})
                except FileNotFoundError:
                    logger.warning(f"LinkedIn image not found: {profile.linkedin_image_path}")

            if not content_parts:
                content_parts.append({"type": "text", "text": "Ingen data tilgjengelig å analysere."})

            messages.append({"role": "user", "content": content_parts})

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=2000,
            )

            response_text = response.choices[0].message.content or "{}"
            extracted = json.loads(response_text)

            profile.extracted_skills = extracted
            profile.summary = extracted.get("summary", "")
            profile.extracted_text = response_text
            profile.extraction_status = "completed"

        except Exception as e:
            logger.error(f"Profile extraction failed: {e}")
            profile.extraction_status = "failed"

        from datetime import datetime, timezone
        profile.last_extracted_at = datetime.now(timezone.utc)
        await db.commit()


async def score_jobs(
    profile_summary: str,
    preferences: dict,
    dismiss_history: list[dict],
    jobs: list[dict],
    db: AsyncSession,
) -> list[dict]:
    if not jobs:
        return []

    client = await _get_openrouter_client()
    model = await _get_model(db)

    dismiss_context = ""
    if dismiss_history:
        dismiss_lines = []
        for d in dismiss_history[:20]:
            dismiss_lines.append(f'- "{d["title"]}" hos {d["company"]} → Grunn: "{d["reason"]}"')
        dismiss_context = (
            "\n\nBrukeren har tidligere avvist disse jobbene:\n"
            + "\n".join(dismiss_lines)
            + "\nBruk dette for å forstå hva brukeren IKKE ønsker."
        )

    jobs_text = ""
    for i, job in enumerate(jobs):
        jobs_text += (
            f"\n--- Jobb {i + 1} (id: {job['id']}) ---\n"
            f"Tittel: {job['title']}\n"
            f"Firma: {job.get('company', 'Ukjent')}\n"
            f"Sted: {job.get('location', 'Ukjent')}\n"
            f"Beskrivelse: {(job.get('description', '') or '')[:500]}\n"
        )

    system_prompt = (
        "Du er en jobbmatcher. Vurder hvor relevante jobbannonsene er for kandidaten. "
        "Returner JSON med en liste av resultater:\n"
        '{"results": [{"job_id": "...", "score": 0.0-1.0, "reasoning": "Kort begrunnelse"}]}\n'
        "Score 0.0 = helt irrelevant, 1.0 = perfekt match."
    )

    user_prompt = (
        f"Kandidatprofil:\n{profile_summary}\n\n"
        f"Preferanser:\n{json.dumps(preferences, ensure_ascii=False)}"
        f"{dismiss_context}\n\n"
        f"Jobbannonser å vurdere:{jobs_text}"
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=3000,
        )
        response_text = response.choices[0].message.content or '{"results": []}'
        return json.loads(response_text).get("results", [])
    except Exception as e:
        logger.error(f"Job scoring failed: {e}")
        return []
