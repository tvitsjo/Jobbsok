from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api import auth, profiles, preferences, jobs, notifications, admin
from app.config import settings
from app.database import Base, async_session, engine
from app.models import *  # noqa: F401, F403
from app.models.admin_config import AdminConfig
from app.models.job_source import JobSource

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000", "https://jobbsok.onrender.com"],
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


# Serve frontend static files
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
