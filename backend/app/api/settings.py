"""Settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db, Setting
from ..schemas.settings import SettingsUpdate, SettingsResponse
from ..config import settings as app_settings
from ..tasks.scheduler import task_scheduler

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current application settings."""
    return {
        # Podcast settings
        "default_episode_limit": app_settings.default_episode_limit,
        "auto_download": app_settings.auto_download,
        "check_interval_minutes": app_settings.check_interval_minutes,

        # Audio conversion
        "audio_format": app_settings.audio_format,
        "audio_bitrate": app_settings.audio_bitrate,

        # Storage
        "max_storage_mb": app_settings.max_storage_mb,
        "auto_cleanup_enabled": app_settings.auto_cleanup_enabled,
        "cleanup_interval_hours": app_settings.cleanup_interval_hours,

        # Watch
        "watch_mount_path": app_settings.watch_mount_path,
        "music_folder_name": app_settings.music_folder_name,
        "auto_sync_enabled": app_settings.auto_sync_enabled,

        # Server info
        "host": app_settings.host,
        "port": app_settings.port,
        "debug": app_settings.debug,
        "log_level": app_settings.log_level,
    }


@router.put("", response_model=SettingsResponse)
async def update_settings(
    updates: SettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application settings.

    Note: Some settings (like check_interval_minutes) require app restart to take effect.
    Background task schedules will be updated if the app is restarted.
    """
    try:
        # Update settings in database
        for key, value in updates.model_dump(exclude_none=True).items():
            # Update or create setting in database
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = str(value)
            else:
                setting = Setting(key=key, value=str(value))
                db.add(setting)

        db.commit()

        # Update in-memory settings (for current session)
        for key, value in updates.model_dump(exclude_none=True).items():
            if hasattr(app_settings, key):
                setattr(app_settings, key, value)

        # Return current settings
        return await get_settings()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_settings(db: Session = Depends(get_db)):
    """Reset all settings to defaults."""
    try:
        # Delete all settings from database
        db.query(Setting).delete()
        db.commit()

        # Reload settings from defaults
        # This would require app restart to fully take effect
        return {"message": "Settings reset to defaults. Restart the application for changes to take effect."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
