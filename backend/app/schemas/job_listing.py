import uuid
from datetime import datetime

from pydantic import BaseModel


class JobListingResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    external_id: str
    title: str
    company_name: str | None = None
    description: str | None = None
    location: str | None = None
    job_type: str | None = None
    salary_info: str | None = None
    url: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchResultResponse(BaseModel):
    id: uuid.UUID
    job_listing: JobListingResponse
    relevance_score: float
    llm_reasoning: str | None = None
    is_seen: bool
    is_saved: bool
    is_dismissed: bool
    dismiss_reason: str | None = None
    is_notified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DismissRequest(BaseModel):
    reason: str
