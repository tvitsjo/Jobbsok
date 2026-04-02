import uuid
from datetime import datetime

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    cv_file_path: str | None = None
    linkedin_image_path: str | None = None
    free_text: str | None = None
    extracted_skills: dict | None = None
    summary: str | None = None
    extraction_status: str
    last_extracted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    free_text: str | None = None


class ExtractedSkillsUpdate(BaseModel):
    extracted_skills: dict
