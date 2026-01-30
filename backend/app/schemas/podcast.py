"""Pydantic schemas for Podcast API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class PodcastBase(BaseModel):
    """Base podcast schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None
    episode_limit: int = Field(default=5, ge=1, le=100)
    auto_download: bool = True


class PodcastCreate(BaseModel):
    """Schema for creating a podcast."""

    rss_url: str = Field(..., min_length=1, max_length=512)
    episode_limit: int = Field(default=5, ge=1, le=100)
    auto_download: bool = True


class PodcastUpdate(BaseModel):
    """Schema for updating a podcast."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None
    episode_limit: Optional[int] = Field(None, ge=1, le=100)
    auto_download: Optional[bool] = None


class PodcastResponse(PodcastBase):
    """Schema for podcast response."""

    id: int
    rss_url: str
    last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    episode_count: Optional[int] = 0

    class Config:
        from_attributes = True


class PodcastListResponse(BaseModel):
    """Schema for podcast list response."""

    podcasts: list[PodcastResponse]
    total: int
