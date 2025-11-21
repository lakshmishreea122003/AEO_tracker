from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator
from typing import List, Optional


class AEOAnalysisRequest(BaseModel):

    email: EmailStr = Field(...)

    target_urls: str = Field(
        ...,
        description="Comma-separated list of URLs"
    )

    brand_name: str = Field(...)

    queries: str = Field(
        ...,
        description="Comma-separated search queries"
    )

    country: str = Field(default="us")

    competitors: Optional[str] = Field(
        None,
        description="Comma-separated competitor names"
    )

    # # Convert to list of URLs
    # @field_validator("target_urls")
    # def split_urls(cls, v):
    #     urls = [u.strip() for u in v.split(",") if u.strip()]
    #     # Validate URLs using HttpUrl
    #     validated = [HttpUrl(url) for url in urls]
    #     return validated

    # # Convert queries string → list
    # @field_validator("queries")
    # def split_queries(cls, v):
    #     return [q.strip() for q in v.split(",") if q.strip()]

    # # Convert competitors string → list
    # @field_validator("competitors", mode="before")
    # def split_competitors(cls, v):
    #     if not v:
    #         return None
    #     return [c.strip() for c in v.split(",") if c.strip()]
