"""Sync API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db, SyncHistory
from ..services.sync_service import SyncService
from ..services.device_detector import device_detector
from .websocket import broadcast_sync_progress, broadcast_sync_complete


logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class SyncHistoryResponse(BaseModel):
    id: int
    sync_type: str
    episodes_added: int
    episodes_removed: int
    bytes_transferred: int
    status: str
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SyncStatsResponse(BaseModel):
    total_episodes: int
    synced_episodes: int
    pending_sync: int
    watch_connected: bool


class WatchInfoResponse(BaseModel):
    connected: bool
    mount_point: str | None = None
    music_folder: str | None = None
    os: str | None = None
    total_mb: float | None = None
    free_mb: float | None = None
    used_mb: float | None = None
    used_percent: float | None = None


def get_sync_service(db: Session = Depends(get_db)) -> SyncService:
    """Get sync service instance."""
    return SyncService(db)


@router.get("/status", response_model=SyncStatsResponse)
async def get_sync_status(
    service: SyncService = Depends(get_sync_service)
):
    """Get current sync status and statistics."""
    try:
        stats = service.get_sync_stats()
        return SyncStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync status"
        )


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_sync(
    service: SyncService = Depends(get_sync_service)
):
    """Start manual sync to watch."""
    try:
        # Check if watch is connected
        if not device_detector.is_watch_connected():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Watch is not connected. Please connect your watch via USB."
            )

        # Progress callback for WebSocket updates
        async def progress_callback(current: int, total: int, episode_title: str):
            await broadcast_sync_progress(current, total, episode_title, "syncing")

        # Start sync
        result = await service.sync_to_watch(progress_callback=progress_callback)

        # Broadcast completion
        await broadcast_sync_complete(
            success=result['success'],
            episodes_added=result['episodes_added'],
            episodes_removed=result['episodes_removed'],
            error=result.get('error')
        )

        if result['success']:
            return {
                "message": "Sync completed successfully",
                "episodes_added": result['episodes_added'],
                "episodes_removed": result['episodes_removed'],
                "bytes_transferred": result['bytes_transferred']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Sync failed')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        await broadcast_sync_complete(
            success=False,
            episodes_added=0,
            episodes_removed=0,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start sync"
        )


@router.get("/history", response_model=List[SyncHistoryResponse])
async def get_sync_history(
    limit: int = 20,
    service: SyncService = Depends(get_sync_service)
):
    """Get sync history."""
    try:
        history = service.get_sync_history(limit=limit)
        return [SyncHistoryResponse.model_validate(record) for record in history]

    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync history"
        )


@router.get("/watch/detect")
async def detect_watch():
    """Check if watch is connected."""
    try:
        is_connected = device_detector.is_watch_connected()
        mount_point = device_detector.get_watch_mount_point()

        return {
            "connected": is_connected,
            "mount_point": str(mount_point) if mount_point else None,
            "music_folder": str(device_detector.get_watch_music_folder()) if is_connected else None
        }

    except Exception as e:
        logger.error(f"Error detecting watch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect watch"
        )


@router.get("/watch/info", response_model=WatchInfoResponse)
async def get_watch_info():
    """Get watch information including storage."""
    try:
        info = device_detector.get_watch_info()

        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watch is not connected"
            )

        return WatchInfoResponse(**info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting watch info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get watch info"
        )
