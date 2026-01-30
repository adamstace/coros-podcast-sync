"""Settings schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class SettingsUpdate(BaseModel):
    """Settings update request."""
    # Podcast settings
    default_episode_limit: Optional[int] = Field(None, ge=1, le=100)
    auto_download: Optional[bool] = None
    check_interval_minutes: Optional[int] = Field(None, ge=5, le=1440)

    # Audio conversion
    audio_format: Optional[str] = None
    audio_bitrate: Optional[str] = None

    # Storage
    max_storage_mb: Optional[int] = Field(None, ge=100)
    auto_cleanup_enabled: Optional[bool] = None
    cleanup_interval_hours: Optional[int] = Field(None, ge=1, le=168)

    # Watch
    watch_mount_path: Optional[str] = None
    music_folder_name: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None


class SettingsResponse(BaseModel):
    """Current settings."""
    # Podcast settings
    default_episode_limit: int
    auto_download: bool
    check_interval_minutes: int

    # Audio conversion
    audio_format: str
    audio_bitrate: str

    # Storage
    max_storage_mb: int
    auto_cleanup_enabled: bool
    cleanup_interval_hours: int

    # Watch
    watch_mount_path: Optional[str]
    music_folder_name: str
    auto_sync_enabled: bool

    # Server info
    host: str
    port: int
    debug: bool
    log_level: str
