"""Sync service for copying episodes to Coros watch."""

import logging
import shutil
from pathlib import Path
from typing import Optional, List, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import Episode, Podcast, SyncHistory
from .device_detector import device_detector


logger = logging.getLogger(__name__)


class SyncService:
    """Service for syncing episodes to watch."""

    def __init__(self, db: Session):
        self.db = db

    def get_episodes_to_sync(self) -> List[Episode]:
        """
        Get list of episodes that should be synced to watch.

        For each podcast, returns the latest N episodes (up to episode_limit)
        that are downloaded and converted.

        Returns:
            List of episodes to sync
        """
        episodes_to_sync = []

        # Get all podcasts
        podcasts = self.db.query(Podcast).all()

        for podcast in podcasts:
            # Get downloaded and converted episodes for this podcast
            episodes = self.db.query(Episode).filter(
                Episode.podcast_id == podcast.id,
                Episode.download_status == 'downloaded',
                Episode.converted_path.isnot(None)
            ).order_by(desc(Episode.pub_date)).limit(podcast.episode_limit).all()

            episodes_to_sync.extend(episodes)

        return episodes_to_sync

    async def sync_to_watch(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> dict:
        """
        Sync episodes to watch.

        Args:
            progress_callback: Optional callback(current, total, episode_title)

        Returns:
            Dictionary with sync results
        """
        # Check if watch is connected
        if not device_detector.is_watch_connected():
            logger.error("Watch is not connected")
            return {
                'success': False,
                'error': 'Watch is not connected',
                'episodes_added': 0,
                'episodes_removed': 0
            }

        music_folder = device_detector.get_watch_music_folder()
        if not music_folder:
            logger.error("Could not find Music folder on watch")
            return {
                'success': False,
                'error': 'Could not find Music folder on watch',
                'episodes_added': 0,
                'episodes_removed': 0
            }

        # Create sync history entry
        sync_history = SyncHistory(
            sync_type='manual',
            started_at=datetime.utcnow(),
            status='in_progress'
        )
        self.db.add(sync_history)
        self.db.commit()

        try:
            # Get episodes to sync
            episodes_to_sync = self.get_episodes_to_sync()
            total_episodes = len(episodes_to_sync)

            logger.info(f"Starting sync: {total_episodes} episodes to process")

            episodes_added = 0
            episodes_removed = 0
            bytes_transferred = 0

            # Copy episodes to watch
            for i, episode in enumerate(episodes_to_sync):
                try:
                    # Call progress callback
                    if progress_callback:
                        progress_callback(i + 1, total_episodes, episode.title)

                    # Check if episode is already on watch
                    converted_path = Path(episode.converted_path)
                    if not converted_path.exists():
                        logger.warning(f"Converted file not found: {converted_path}")
                        continue

                    watch_file_path = music_folder / converted_path.name

                    # Check if file already exists and is up to date
                    if watch_file_path.exists():
                        # Compare file sizes
                        if watch_file_path.stat().st_size == converted_path.stat().st_size:
                            # File already synced, just update database
                            if not episode.synced_to_watch:
                                episode.synced_to_watch = True
                                episode.sync_date = datetime.utcnow()
                            logger.debug(f"Episode already on watch: {episode.title}")
                            continue

                    # Copy file to watch
                    logger.info(f"Copying to watch: {episode.title}")
                    shutil.copy2(str(converted_path), str(watch_file_path))

                    # Update episode
                    episode.synced_to_watch = True
                    episode.sync_date = datetime.utcnow()

                    episodes_added += 1
                    bytes_transferred += converted_path.stat().st_size

                    logger.info(f"Successfully synced: {episode.title}")

                except Exception as episode_error:
                    logger.error(f"Error syncing episode {episode.id}: {episode_error}")
                    continue

            # Cleanup old episodes from watch
            removed_count, removed_bytes = await self._cleanup_watch(music_folder, episodes_to_sync)
            episodes_removed = removed_count
            bytes_transferred += removed_bytes

            # Update sync history
            sync_history.episodes_added = episodes_added
            sync_history.episodes_removed = episodes_removed
            sync_history.bytes_transferred = bytes_transferred
            sync_history.status = 'success'
            sync_history.completed_at = datetime.utcnow()

            self.db.commit()

            logger.info(
                f"Sync completed: {episodes_added} added, "
                f"{episodes_removed} removed, "
                f"{bytes_transferred / (1024*1024):.2f} MB transferred"
            )

            return {
                'success': True,
                'episodes_added': episodes_added,
                'episodes_removed': episodes_removed,
                'bytes_transferred': bytes_transferred
            }

        except Exception as e:
            logger.error(f"Sync failed: {e}")

            # Update sync history
            sync_history.status = 'failed'
            sync_history.error_message = str(e)
            sync_history.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                'success': False,
                'error': str(e),
                'episodes_added': 0,
                'episodes_removed': 0
            }

    async def _cleanup_watch(
        self,
        music_folder: Path,
        episodes_to_keep: List[Episode]
    ) -> tuple[int, int]:
        """
        Remove episodes from watch that are no longer needed.

        Args:
            music_folder: Path to watch Music folder
            episodes_to_keep: List of episodes that should remain on watch

        Returns:
            Tuple of (count_removed, bytes_removed)
        """
        # Get list of files that should be on watch
        keep_filenames = {Path(ep.converted_path).name for ep in episodes_to_keep if ep.converted_path}

        count_removed = 0
        bytes_removed = 0

        try:
            # Get all MP3 files on watch
            watch_files = list(music_folder.glob('*.mp3'))

            for watch_file in watch_files:
                # If file is not in the keep list, remove it
                if watch_file.name not in keep_filenames:
                    try:
                        file_size = watch_file.stat().st_size
                        watch_file.unlink()
                        count_removed += 1
                        bytes_removed += file_size

                        # Update database - mark episode as not synced
                        episode = self.db.query(Episode).filter(
                            Episode.converted_path.like(f'%{watch_file.name}')
                        ).first()

                        if episode:
                            episode.synced_to_watch = False
                            episode.sync_date = None

                        logger.info(f"Removed from watch: {watch_file.name}")

                    except Exception as file_error:
                        logger.error(f"Error removing file {watch_file}: {file_error}")
                        continue

            if count_removed > 0:
                self.db.commit()

        except Exception as e:
            logger.error(f"Error during watch cleanup: {e}")

        return count_removed, bytes_removed

    def get_sync_history(self, limit: int = 20) -> List[SyncHistory]:
        """
        Get sync history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of sync history records
        """
        return self.db.query(SyncHistory).order_by(
            desc(SyncHistory.created_at)
        ).limit(limit).all()

    def get_synced_episodes(self) -> List[Episode]:
        """Get list of episodes currently synced to watch."""
        return self.db.query(Episode).filter(
            Episode.synced_to_watch == True
        ).all()

    def get_sync_stats(self) -> dict:
        """
        Get sync statistics.

        Returns:
            Dictionary with sync stats
        """
        total_episodes = self.db.query(Episode).filter(
            Episode.download_status == 'downloaded',
            Episode.converted_path.isnot(None)
        ).count()

        synced_episodes = self.db.query(Episode).filter(
            Episode.synced_to_watch == True
        ).count()

        pending_sync = total_episodes - synced_episodes

        return {
            'total_episodes': total_episodes,
            'synced_episodes': synced_episodes,
            'pending_sync': pending_sync,
            'watch_connected': device_detector.is_watch_connected()
        }
