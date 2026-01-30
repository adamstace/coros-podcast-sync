"""Automatic episode download task."""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import SessionLocal, Podcast, Episode
from ..services.podcast_service import PodcastService
from ..services.download_service import DownloadService


logger = logging.getLogger(__name__)


async def auto_download_task():
    """
    Background task to automatically download new episodes.

    This task:
    1. Checks all podcasts for new episodes
    2. Downloads pending episodes for podcasts with auto_download enabled
    3. Respects episode limits
    """
    logger.info("Starting auto-download task")

    db = SessionLocal()
    try:
        # Get all podcasts with auto_download enabled
        podcasts = db.query(Podcast).filter(Podcast.auto_download == True).all()

        if not podcasts:
            logger.info("No podcasts with auto-download enabled")
            return

        logger.info(f"Found {len(podcasts)} podcasts with auto-download enabled")

        podcast_service = PodcastService(db)
        download_service = DownloadService(db)

        total_refreshed = 0
        total_downloaded = 0

        for podcast in podcasts:
            try:
                logger.info(f"Processing podcast: {podcast.title} (ID: {podcast.id})")

                # Refresh episodes from RSS feed
                new_episodes = await podcast_service.fetch_episodes(podcast.id)
                total_refreshed += len(new_episodes)

                if new_episodes:
                    logger.info(f"Found {len(new_episodes)} new episodes for {podcast.title}")

                # Get pending episodes (up to episode limit)
                pending_episodes = db.query(Episode).filter(
                    Episode.podcast_id == podcast.id,
                    Episode.download_status == 'pending'
                ).order_by(Episode.pub_date.desc()).limit(podcast.episode_limit).all()

                # Download pending episodes
                for episode in pending_episodes:
                    try:
                        logger.info(f"Auto-downloading: {episode.title}")
                        result = await download_service.download_episode(episode.id)

                        if result:
                            total_downloaded += 1
                            logger.info(f"Successfully downloaded: {episode.title}")
                        else:
                            logger.warning(f"Failed to download: {episode.title}")

                    except Exception as episode_error:
                        logger.error(f"Error downloading episode {episode.id}: {episode_error}")
                        continue

            except Exception as podcast_error:
                logger.error(f"Error processing podcast {podcast.id}: {podcast_error}")
                continue

        logger.info(
            f"Auto-download task completed: "
            f"{total_refreshed} new episodes found, "
            f"{total_downloaded} episodes downloaded"
        )

    except Exception as e:
        logger.error(f"Error in auto-download task: {e}")
    finally:
        db.close()


async def check_for_new_episodes():
    """
    Background task to check for new episodes without downloading.

    This task only refreshes the episode list from RSS feeds.
    """
    logger.info("Checking for new episodes")

    db = SessionLocal()
    try:
        podcasts = db.query(Podcast).all()
        podcast_service = PodcastService(db)

        total_new = 0

        for podcast in podcasts:
            try:
                new_episodes = await podcast_service.fetch_episodes(podcast.id)
                total_new += len(new_episodes)

                if new_episodes:
                    logger.info(f"Found {len(new_episodes)} new episodes for {podcast.title}")

            except Exception as e:
                logger.error(f"Error checking episodes for podcast {podcast.id}: {e}")
                continue

        logger.info(f"Episode check completed: {total_new} new episodes found")

    except Exception as e:
        logger.error(f"Error checking for new episodes: {e}")
    finally:
        db.close()
