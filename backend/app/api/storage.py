"""Storage management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.storage import (
    LocalStorageResponse,
    StorageByPodcastResponse,
    PodcastStorageItem,
    CleanupRequest,
    CleanupResponse,
)
from ..services.storage_service import storage_service

router = APIRouter()


@router.get("/local", response_model=LocalStorageResponse)
async def get_local_storage(db: Session = Depends(get_db)):
    """Get local storage information."""
    storage_info = storage_service.get_local_storage_info()
    return storage_info


@router.get("/by-podcast", response_model=StorageByPodcastResponse)
async def get_storage_by_podcast(db: Session = Depends(get_db)):
    """Get storage usage breakdown by podcast."""
    breakdown = storage_service.get_storage_by_podcast(db)
    return {"podcasts": breakdown}


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_storage(
    request: CleanupRequest,
    db: Session = Depends(get_db)
):
    """
    Clean up storage based on specified criteria.

    Cleanup types:
    - "age": Delete episodes older than specified days
    - "storage_limit": Delete oldest episodes to meet storage limit
    - "failed": Delete episodes with failed download status
    - "orphaned": Delete files without database records
    """
    try:
        if request.cleanup_type == "age":
            deleted, bytes_freed = storage_service.cleanup_old_episodes(
                db,
                days_old=request.days_old,
                keep_synced=request.keep_synced
            )
            message = f"Deleted {deleted} episodes older than {request.days_old} days"

        elif request.cleanup_type == "storage_limit":
            deleted, bytes_freed = storage_service.cleanup_by_storage_limit(
                db,
                max_storage_mb=request.max_storage_mb,
                keep_synced=request.keep_synced
            )
            message = f"Deleted {deleted} episodes to meet {request.max_storage_mb} MB limit"

        elif request.cleanup_type == "failed":
            deleted, bytes_freed = storage_service.cleanup_failed_downloads(db)
            message = f"Deleted {deleted} failed episodes"

        elif request.cleanup_type == "orphaned":
            deleted, bytes_freed = storage_service.cleanup_orphaned_files(db)
            message = f"Deleted {deleted} orphaned files"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cleanup type: {request.cleanup_type}"
            )

        mb_freed = round(bytes_freed / (1024 * 1024), 2)

        return {
            "success": True,
            "items_deleted": deleted,
            "bytes_freed": bytes_freed,
            "mb_freed": mb_freed,
            "message": message,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
