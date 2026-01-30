"""Application configuration."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/database.db"

    # Storage paths
    local_storage_path: Path = Path("./data/episodes")
    local_converted_path: Path = Path("./data/converted")
    max_storage_mb: int = 1000

    # Watch configuration
    watch_mount_path: Optional[str] = None
    music_folder_name: str = "Music"

    # Podcast settings
    default_episode_limit: int = 5
    auto_download: bool = True
    check_interval_minutes: int = 60

    # Audio conversion
    audio_format: str = "mp3"
    audio_bitrate: str = "128k"

    # Sync settings
    auto_sync_enabled: bool = True

    # Storage cleanup
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24

    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("./logs/app.log")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def episodes_dir(self) -> Path:
        """Get episodes directory path."""
        return self.local_storage_path

    @property
    def converted_dir(self) -> Path:
        """Get converted files directory path."""
        return self.local_converted_path


# Global settings instance
settings = Settings()


def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        settings.local_storage_path,
        settings.local_converted_path,
        Path("./data"),
        Path("./logs"),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
