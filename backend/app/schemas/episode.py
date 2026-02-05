"""Pydantic schemas for Episode API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EpisodeBase(BaseModel):
    """Base episode schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    audio_url: str
    pub_date: Optional[datetime] = None
    duration: Optional[int] = None  # in seconds
    file_size: Optional[int] = None  # in bytes


class EpisodeCreate(EpisodeBase):
    """Schema for creating an episode."""

    podcast_id: int
    guid: str


class EpisodeResponse(EpisodeBase):
    """Schema for episode response."""

    id: int
    podcast_id: int
    podcast_image_url: Optional[str] = None
    guid: str
    download_status: str
    download_progress: int
    local_path: Optional[str] = None
    converted_path: Optional[str] = None
    synced_to_watch: bool
    sync_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    """Schema for episode list response."""

    episodes: list[EpisodeResponse]
    total: int
