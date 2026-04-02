import uuid
from datetime import datetime

from pydantic import BaseModel


class JobPreferenceCreate(BaseModel):
    job_titles: list[str] = []
    job_types: list[str] = []
    locations: list[str] = []
    min_salary: int | None = None
    keywords: list[str] = []
    exclude_keywords: list[str] = []


class JobPreferenceUpdate(BaseModel):
    job_titles: list[str] | None = None
    job_types: list[str] | None = None
    locations: list[str] | None = None
    min_salary: int | None = None
    keywords: list[str] | None = None
    exclude_keywords: list[str] | None = None
    is_active: bool | None = None


class JobPreferenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_titles: list[str]
    job_types: list[str]
    locations: list[str]
    min_salary: int | None = None
    keywords: list[str]
    exclude_keywords: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
