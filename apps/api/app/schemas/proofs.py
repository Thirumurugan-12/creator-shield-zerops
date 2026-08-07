from datetime import date
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class ProofMetadata(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    instagram_username: str = Field(min_length=2, max_length=120)
    claimed_publication_date: date
    claimed_publication_url: str = ""

    @field_validator("instagram_username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return str(value).lstrip("@").strip()

    @field_validator("claimed_publication_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("must be a valid HTTP or HTTPS URL")
        return value
