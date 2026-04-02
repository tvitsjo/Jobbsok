import uuid
from datetime import datetime

from pydantic import BaseModel


class AdminConfigResponse(BaseModel):
    key: str
    value: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminConfigUpdate(BaseModel):
    value: str


class JobSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    is_enabled: bool
    config: dict | None = None
    last_fetched_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobSourceUpdate(BaseModel):
    is_enabled: bool | None = None
    config: dict | None = None


class SystemStats(BaseModel):
    total_users: int
    total_jobs: int
    total_search_runs: int
    total_matches: int
