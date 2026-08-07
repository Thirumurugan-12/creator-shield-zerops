from datetime import date
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class IncidentMetadata(BaseModel):
    suspicious_username: str = Field(min_length=2, max_length=120)
    claimed_publication_date: date
    suspicious_url: str = ""
    caption: str = ""
    notes: str = ""

    @field_validator("suspicious_username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return str(value).lstrip("@").strip()

    @field_validator("suspicious_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("must be a valid HTTP or HTTPS URL")
        return value
