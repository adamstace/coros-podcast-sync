"""Podcast API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.podcast import (
    PodcastCreate,
    PodcastUpdate,
    PodcastResponse,
    PodcastListResponse
)
from ..services.podcast_service import PodcastService


logger = logging.getLogger(__name__)

router = APIRouter()


def get_podcast_service(db: Session = Depends(get_db)) -> PodcastService:
    """Get podcast service instance."""
    return PodcastService(db)


@router.get("", response_model=PodcastListResponse)
async def list_podcasts(
    service: PodcastService = Depends(get_podcast_service)
):
    """List all podcasts with episode counts."""
    try:
        podcasts_data = service.get_all_podcasts_with_counts()

        podcasts = []
        for data in podcasts_data:
            podcast_dict = {
                'id': data['podcast'].id,
                'title': data['podcast'].title,
                'rss_url': data['podcast'].rss_url,
                'description': data['podcast'].description,
                'image_url': data['podcast'].image_url,
                'episode_limit': data['podcast'].episode_limit,
                'auto_download': data['podcast'].auto_download,
                'last_checked': data['podcast'].last_checked,
                'created_at': data['podcast'].created_at,
                'updated_at': data['podcast'].updated_at,
                'episode_count': data['episode_count']
            }
            podcasts.append(PodcastResponse(**podcast_dict))

        return PodcastListResponse(
            podcasts=podcasts,
            total=len(podcasts)
        )
    except Exception as e:
        logger.error(f"Error listing podcasts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list podcasts"
        )


@router.post("", response_model=PodcastResponse, status_code=status.HTTP_201_CREATED)
async def create_podcast(
    podcast_create: PodcastCreate,
    service: PodcastService = Depends(get_podcast_service)
):
    """Create a new podcast from RSS URL."""
    try:
        podcast = await service.create_podcast(podcast_create)

        podcast_dict = {
            'id': podcast.id,
            'title': podcast.title,
            'rss_url': podcast.rss_url,
            'description': podcast.description,
            'image_url': podcast.image_url,
            'episode_limit': podcast.episode_limit,
            'auto_download': podcast.auto_download,
            'last_checked': podcast.last_checked,
            'created_at': podcast.created_at,
            'updated_at': podcast.updated_at,
            'episode_count': 0  # Will be populated after initial fetch
        }

        return PodcastResponse(**podcast_dict)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating podcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create podcast"
        )


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: int,
    service: PodcastService = Depends(get_podcast_service)
):
    """Get podcast by ID."""
    try:
        podcast_data = service.get_podcast_with_episode_count(podcast_id)

        if not podcast_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Podcast {podcast_id} not found"
            )

        podcast = podcast_data['podcast']
        podcast_dict = {
            'id': podcast.id,
            'title': podcast.title,
            'rss_url': podcast.rss_url,
            'description': podcast.description,
            'image_url': podcast.image_url,
            'episode_limit': podcast.episode_limit,
            'auto_download': podcast.auto_download,
            'last_checked': podcast.last_checked,
            'created_at': podcast.created_at,
            'updated_at': podcast.updated_at,
            'episode_count': podcast_data['episode_count']
        }

        return PodcastResponse(**podcast_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting podcast {podcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get podcast"
        )


@router.put("/{podcast_id}", response_model=PodcastResponse)
async def update_podcast(
    podcast_id: int,
    podcast_update: PodcastUpdate,
    service: PodcastService = Depends(get_podcast_service)
):
    """Update podcast settings."""
    try:
        podcast = service.update_podcast(podcast_id, podcast_update)

        podcast_data = service.get_podcast_with_episode_count(podcast_id)

        podcast_dict = {
            'id': podcast.id,
            'title': podcast.title,
            'rss_url': podcast.rss_url,
            'description': podcast.description,
            'image_url': podcast.image_url,
            'episode_limit': podcast.episode_limit,
            'auto_download': podcast.auto_download,
            'last_checked': podcast.last_checked,
            'created_at': podcast.created_at,
            'updated_at': podcast.updated_at,
            'episode_count': podcast_data['episode_count'] if podcast_data else 0
        }

        return PodcastResponse(**podcast_dict)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating podcast {podcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update podcast"
        )


@router.delete("/{podcast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_podcast(
    podcast_id: int,
    service: PodcastService = Depends(get_podcast_service)
):
    """Delete podcast and all associated episodes."""
    try:
        service.delete_podcast(podcast_id)
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting podcast {podcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete podcast"
        )


@router.post("/{podcast_id}/refresh", status_code=status.HTTP_200_OK)
async def refresh_podcast(
    podcast_id: int,
    service: PodcastService = Depends(get_podcast_service)
):
    """Force refresh podcast episodes from RSS feed."""
    try:
        episodes = await service.fetch_episodes(podcast_id)

        return {
            "message": f"Successfully fetched {len(episodes)} new episodes",
            "new_episodes_count": len(episodes)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refreshing podcast {podcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh podcast"
        )
