from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, profiles, preferences, jobs, notifications, admin
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed default admin config and job sources
    from app.database import async_session
    from app.models.admin_config import AdminConfig
    from app.models.job_source import JobSource
    from sqlalchemy import select

    async with async_session() as db:
        # Seed default OpenRouter model
        result = await db.execute(select(AdminConfig).where(AdminConfig.key == "openrouter_model"))
        if not result.scalar_one_or_none():
            db.add(AdminConfig(key="openrouter_model", value="anthropic/claude-sonnet-4"))
            db.add(AdminConfig(key="search_interval_hours", value="6"))

        # Seed job sources
        result = await db.execute(select(JobSource).where(JobSource.name == "nav_arbeidsplassen"))
        if not result.scalar_one_or_none():
            db.add(JobSource(name="nav_arbeidsplassen", display_name="NAV Arbeidsplassen", is_enabled=True))

        result = await db.execute(select(JobSource).where(JobSource.name == "finn"))
        if not result.scalar_one_or_none():
            db.add(JobSource(name="finn", display_name="Finn.no", is_enabled=False))

        await db.commit()

    yield


app = FastAPI(title="Jobbsøk", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(preferences.router)
app.include_router(jobs.router)
app.include_router(notifications.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
