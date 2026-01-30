"""Database models and session management."""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from .config import settings, ensure_directories


# Ensure data directory exists
ensure_directories()

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Podcast(Base):
    """Podcast model."""

    __tablename__ = "podcasts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    rss_url = Column(String(512), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    episode_limit = Column(Integer, default=5, nullable=False)
    auto_download = Column(Boolean, default=True, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    episodes = relationship("Episode", back_populates="podcast", cascade="all, delete-orphan")


class Episode(Base):
    """Episode model."""

    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    audio_url = Column(String(1024), nullable=False)
    guid = Column(String(512), unique=True, nullable=False, index=True)
    pub_date = Column(DateTime, nullable=True, index=True)
    duration = Column(Integer, nullable=True)  # in seconds
    file_size = Column(Integer, nullable=True)  # in bytes

    # Download tracking
    download_status = Column(String(50), default="pending", nullable=False)  # pending, downloading, downloaded, failed
    download_progress = Column(Integer, default=0, nullable=False)  # 0-100
    local_path = Column(String(512), nullable=True)
    converted_path = Column(String(512), nullable=True)

    # Sync tracking
    synced_to_watch = Column(Boolean, default=False, nullable=False)
    sync_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    podcast = relationship("Podcast", back_populates="episodes")


class SyncHistory(Base):
    """Sync history model."""

    __tablename__ = "sync_history"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False)  # auto, manual
    episodes_added = Column(Integer, default=0, nullable=False)
    episodes_removed = Column(Integer, default=0, nullable=False)
    bytes_transferred = Column(Integer, default=0, nullable=False)
    status = Column(String(50), nullable=False)  # success, failed, partial
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Setting(Base):
    """Application settings model."""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database and create tables."""
    Base.metadata.create_all(bind=engine)

    # Add default settings if they don't exist
    db = SessionLocal()
    try:
        default_settings = {
            "watch_mount_path": "",
            "local_storage_path": str(settings.local_storage_path),
            "max_storage_mb": str(settings.max_storage_mb),
            "check_interval_minutes": str(settings.check_interval_minutes),
            "auto_sync_enabled": str(settings.auto_sync_enabled).lower(),
            "audio_format": settings.audio_format,
            "audio_bitrate": settings.audio_bitrate,
        }

        for key, value in default_settings.items():
            existing = db.query(Setting).filter(Setting.key == key).first()
            if not existing:
                db.add(Setting(key=key, value=value))

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing database settings: {e}")
    finally:
        db.close()
