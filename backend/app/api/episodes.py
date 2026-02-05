"""Episode API endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from ..database import get_db, Episode, Podcast
from ..schemas.episode import EpisodeResponse, EpisodeListResponse
from ..services.download_service import DownloadService
from ..services.audio_converter import audio_converter
from pathlib import Path


logger = logging.getLogger(__name__)

router = APIRouter()


def get_download_service(db: Session = Depends(get_db)) -> DownloadService:
    """Get download service instance."""
    return DownloadService(db)


@router.get("", response_model=EpisodeListResponse)
async def list_episodes(
    podcast_id: Optional[int] = Query(None, description="Filter by podcast ID"),
    download_status: Optional[str] = Query(None, description="Filter by download status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of episodes to return"),
    offset: int = Query(0, ge=0, description="Number of episodes to skip"),
    db: Session = Depends(get_db)
):
    """List episodes with optional filters."""
    try:
        query = db.query(Episode).options(joinedload(Episode.podcast))

        # Apply filters
        if podcast_id:
            query = query.filter(Episode.podcast_id == podcast_id)

        if download_status:
            query = query.filter(Episode.download_status == download_status)

        # Get total count
        total = query.count()

        # Get episodes with pagination
        episodes = query.order_by(desc(Episode.pub_date)).offset(offset).limit(limit).all()

        episode_responses = [
            EpisodeResponse(
                id=ep.id,
                podcast_id=ep.podcast_id,
                podcast_image_url=ep.podcast.image_url if ep.podcast else None,
                title=ep.title,
                description=ep.description,
                audio_url=ep.audio_url,
                guid=ep.guid,
                pub_date=ep.pub_date,
                duration=ep.duration,
                file_size=ep.file_size,
                download_status=ep.download_status,
                download_progress=ep.download_progress,
                local_path=ep.local_path,
                converted_path=ep.converted_path,
                synced_to_watch=ep.synced_to_watch,
                sync_date=ep.sync_date,
                created_at=ep.created_at,
                updated_at=ep.updated_at
            )
            for ep in episodes
        ]

        return EpisodeListResponse(
            episodes=episode_responses,
            total=total
        )

    except Exception as e:
        logger.error(f"Error listing episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list episodes"
        )


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: int,
    db: Session = Depends(get_db)
):
    """Get episode by ID."""
    try:
        episode = (
            db.query(Episode)
            .options(joinedload(Episode.podcast))
            .filter(Episode.id == episode_id)
            .first()
        )

        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        return EpisodeResponse(
            id=episode.id,
            podcast_id=episode.podcast_id,
            podcast_image_url=episode.podcast.image_url if episode.podcast else None,
            title=episode.title,
            description=episode.description,
            audio_url=episode.audio_url,
            guid=episode.guid,
            pub_date=episode.pub_date,
            duration=episode.duration,
            file_size=episode.file_size,
            download_status=episode.download_status,
            download_progress=episode.download_progress,
            local_path=episode.local_path,
            converted_path=episode.converted_path,
            synced_to_watch=episode.synced_to_watch,
            sync_date=episode.sync_date,
            created_at=episode.created_at,
            updated_at=episode.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting episode {episode_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get episode"
        )


@router.post("/{episode_id}/download", status_code=status.HTTP_202_ACCEPTED)
async def download_episode(
    episode_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """Trigger episode download."""
    try:
        episode = service.db.query(Episode).filter(Episode.id == episode_id).first()

        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        # Queue download
        queued = await service.queue_download(episode_id)

        if not queued:
            return {
                "message": "Episode already downloading",
                "episode_id": episode_id,
                "status": "already_queued"
            }

        return {
            "message": "Episode download started",
            "episode_id": episode_id,
            "status": "queued"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting download for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start download"
        )


@router.delete("/{episode_id}/download", status_code=status.HTTP_200_OK)
async def cancel_download(
    episode_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """Cancel episode download."""
    try:
        cancelled = service.cancel_download(episode_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode is not currently downloading"
            )

        return {
            "message": "Download cancelled",
            "episode_id": episode_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling download for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel download"
        )


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """Delete episode and its files."""
    try:
        episode = service.db.query(Episode).filter(Episode.id == episode_id).first()

        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        # Delete files
        service.delete_episode_file(episode_id)

        # Delete episode from database
        service.db.delete(episode)
        service.db.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting episode {episode_id}: {e}")
        service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete episode"
        )


@router.get("/{episode_id}/status")
async def get_download_status(
    episode_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """Get download status for an episode."""
    try:
        status_info = service.get_download_status(episode_id)

        if status_info['status'] == 'not_found':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        return status_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download status for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get download status"
        )


@router.post("/podcast/{podcast_id}/download-all", status_code=status.HTTP_202_ACCEPTED)
async def download_podcast_episodes(
    podcast_id: int,
    limit: Optional[int] = Query(None, description="Maximum episodes to download"),
    service: DownloadService = Depends(get_download_service)
):
    """Download all pending episodes for a podcast."""
    try:
        # Check podcast exists
        podcast = service.db.query(Podcast).filter(Podcast.id == podcast_id).first()

        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Podcast {podcast_id} not found"
            )

        # Get pending episodes
        query = service.db.query(Episode).filter(
            Episode.podcast_id == podcast_id,
            Episode.download_status == 'pending'
        )

        if limit:
            query = query.limit(limit)

        episodes = query.all()

        # Queue downloads
        queued_count = 0
        for episode in episodes:
            if await service.queue_download(episode.id):
                queued_count += 1

        return {
            "message": f"Queued {queued_count} episodes for download",
            "podcast_id": podcast_id,
            "queued_count": queued_count,
            "total_pending": len(episodes)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading episodes for podcast {podcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download episodes"
        )


@router.post("/{episode_id}/convert", status_code=status.HTTP_202_ACCEPTED)
async def convert_episode(
    episode_id: int,
    db: Session = Depends(get_db)
):
    """Convert episode audio to MP3 format."""
    try:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()

        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        if not episode.local_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode has not been downloaded yet"
            )

        local_path = Path(episode.local_path)
        if not local_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Episode file does not exist"
            )

        # Check if already converted
        if episode.converted_path:
            converted_path = Path(episode.converted_path)
            if converted_path.exists():
                return {
                    "message": "Episode is already converted",
                    "episode_id": episode_id,
                    "converted_path": str(converted_path)
                }

        # Convert to MP3
        converted_path = await audio_converter.convert_episode_audio(
            episode_id=episode_id,
            input_path=local_path,
            keep_original=True
        )

        if converted_path:
            episode.converted_path = str(converted_path)
            db.commit()

            return {
                "message": "Episode converted successfully",
                "episode_id": episode_id,
                "converted_path": str(converted_path)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio conversion failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting episode {episode_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert episode"
        )
