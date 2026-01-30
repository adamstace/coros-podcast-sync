"""Storage schemas."""

from pydantic import BaseModel
from typing import List


class LocalStorageResponse(BaseModel):
    """Local storage information."""
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    disk_used_percent: float
    episodes_bytes: int
    converted_bytes: int
    total_podcast_bytes: int
    episodes_mb: float
    converted_mb: float
    total_podcast_mb: float


class PodcastStorageItem(BaseModel):
    """Storage info for a single podcast."""
    podcast_id: int
    podcast_title: str
    total_bytes: int
    total_mb: float
    episode_count: int
    synced_count: int


class StorageByPodcastResponse(BaseModel):
    """Storage breakdown by podcast."""
    podcasts: List[PodcastStorageItem]


class CleanupRequest(BaseModel):
    """Cleanup request parameters."""
    cleanup_type: str  # "age", "storage_limit", "failed", "orphaned"
    days_old: int = 30
    max_storage_mb: int = 1000
    keep_synced: bool = True


class CleanupResponse(BaseModel):
    """Cleanup operation result."""
    success: bool
    items_deleted: int
    bytes_freed: int
    mb_freed: float
    message: str
