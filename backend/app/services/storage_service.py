"""Storage monitoring and cleanup service."""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db, Episode, Podcast, Setting
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Manage storage monitoring and cleanup."""

    def __init__(self):
        self.episodes_dir = Path(settings.episodes_dir)
        self.converted_dir = Path(settings.converted_dir)

    def get_local_storage_info(self) -> Dict:
        """Get local storage information for episodes directory."""
        try:
            # Get storage stats for the episodes directory
            stat = shutil.disk_usage(str(self.episodes_dir))

            # Calculate size of episodes directory
            episodes_size = self._get_directory_size(self.episodes_dir)
            converted_size = self._get_directory_size(self.converted_dir)
            total_podcast_data = episodes_size + converted_size

            return {
                "disk_total_bytes": stat.total,
                "disk_used_bytes": stat.used,
                "disk_free_bytes": stat.free,
                "disk_used_percent": (stat.used / stat.total * 100) if stat.total > 0 else 0,
                "episodes_bytes": episodes_size,
                "converted_bytes": converted_size,
                "total_podcast_bytes": total_podcast_data,
                "episodes_mb": round(episodes_size / (1024 * 1024), 2),
                "converted_mb": round(converted_size / (1024 * 1024), 2),
                "total_podcast_mb": round(total_podcast_data / (1024 * 1024), 2),
            }
        except Exception as e:
            logger.error(f"Failed to get local storage info: {e}")
            return {
                "disk_total_bytes": 0,
                "disk_used_bytes": 0,
                "disk_free_bytes": 0,
                "disk_used_percent": 0,
                "episodes_bytes": 0,
                "converted_bytes": 0,
                "total_podcast_bytes": 0,
                "episodes_mb": 0,
                "converted_mb": 0,
                "total_podcast_mb": 0,
            }

    def get_storage_by_podcast(self, db: Session) -> List[Dict]:
        """Get storage usage breakdown by podcast."""
        podcasts = db.query(Podcast).all()
        storage_breakdown = []

        for podcast in podcasts:
            episodes = db.query(Episode).filter(Episode.podcast_id == podcast.id).all()

            total_size = 0
            episode_count = 0
            synced_count = 0

            for episode in episodes:
                # Count original files
                if episode.local_path and Path(episode.local_path).exists():
                    total_size += Path(episode.local_path).stat().st_size
                    episode_count += 1

                # Count converted files (if different from original)
                if episode.converted_path and episode.converted_path != episode.local_path:
                    if Path(episode.converted_path).exists():
                        total_size += Path(episode.converted_path).stat().st_size

                if episode.synced_to_watch:
                    synced_count += 1

            storage_breakdown.append({
                "podcast_id": podcast.id,
                "podcast_title": podcast.title,
                "total_bytes": total_size,
                "total_mb": round(total_size / (1024 * 1024), 2),
                "episode_count": episode_count,
                "synced_count": synced_count,
            })

        # Sort by size descending
        storage_breakdown.sort(key=lambda x: x["total_bytes"], reverse=True)
        return storage_breakdown

    def cleanup_old_episodes(
        self,
        db: Session,
        days_old: int = 30,
        keep_synced: bool = True,
    ) -> Tuple[int, int]:
        """
        Clean up old episodes based on age.

        Args:
            db: Database session
            days_old: Delete episodes older than this many days
            keep_synced: If True, keep episodes that are synced to watch

        Returns:
            Tuple of (episodes_deleted, bytes_freed)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        query = db.query(Episode).filter(Episode.created_at < cutoff_date)

        if keep_synced:
            query = query.filter(Episode.synced_to_watch == False)

        old_episodes = query.all()

        deleted_count = 0
        bytes_freed = 0

        for episode in old_episodes:
            size = self._delete_episode_files(episode)
            if size > 0:
                db.delete(episode)
                deleted_count += 1
                bytes_freed += size

        db.commit()
        logger.info(f"Cleaned up {deleted_count} old episodes, freed {bytes_freed / (1024*1024):.2f} MB")

        return deleted_count, bytes_freed

    def cleanup_by_storage_limit(
        self,
        db: Session,
        max_storage_mb: int,
        keep_synced: bool = True,
    ) -> Tuple[int, int]:
        """
        Clean up episodes to stay under storage limit.
        Deletes oldest episodes first.

        Args:
            db: Database session
            max_storage_mb: Maximum storage in MB to keep
            keep_synced: If True, keep episodes that are synced to watch

        Returns:
            Tuple of (episodes_deleted, bytes_freed)
        """
        storage_info = self.get_local_storage_info()
        current_mb = storage_info["total_podcast_mb"]

        if current_mb <= max_storage_mb:
            logger.info(f"Storage ({current_mb} MB) is under limit ({max_storage_mb} MB)")
            return 0, 0

        target_mb = max_storage_mb * 0.9  # Target 90% of limit for some buffer
        mb_to_free = current_mb - target_mb

        query = db.query(Episode).filter(Episode.local_path.isnot(None))

        if keep_synced:
            query = query.filter(Episode.synced_to_watch == False)

        # Order by oldest first
        query = query.order_by(Episode.created_at.asc())

        old_episodes = query.all()

        deleted_count = 0
        bytes_freed = 0
        mb_freed = 0.0

        for episode in old_episodes:
            if mb_freed >= mb_to_free:
                break

            size = self._delete_episode_files(episode)
            if size > 0:
                db.delete(episode)
                deleted_count += 1
                bytes_freed += size
                mb_freed = bytes_freed / (1024 * 1024)

        db.commit()
        logger.info(f"Cleaned up {deleted_count} episodes to meet storage limit, freed {mb_freed:.2f} MB")

        return deleted_count, bytes_freed

    def cleanup_failed_downloads(self, db: Session) -> Tuple[int, int]:
        """
        Clean up episodes with failed download status.

        Returns:
            Tuple of (episodes_deleted, bytes_freed)
        """
        failed_episodes = db.query(Episode).filter(Episode.download_status == "failed").all()

        deleted_count = 0
        bytes_freed = 0

        for episode in failed_episodes:
            size = self._delete_episode_files(episode)
            db.delete(episode)
            deleted_count += 1
            bytes_freed += size

        db.commit()
        logger.info(f"Cleaned up {deleted_count} failed episodes, freed {bytes_freed / (1024*1024):.2f} MB")

        return deleted_count, bytes_freed

    def cleanup_orphaned_files(self, db: Session) -> Tuple[int, int]:
        """
        Clean up files that exist on disk but have no database record.

        Returns:
            Tuple of (files_deleted, bytes_freed)
        """
        # Get all file paths from database
        db_files = set()
        episodes = db.query(Episode).all()
        for episode in episodes:
            if episode.local_path:
                db_files.add(str(Path(episode.local_path).resolve()))
            if episode.converted_path:
                db_files.add(str(Path(episode.converted_path).resolve()))

        deleted_count = 0
        bytes_freed = 0

        # Scan episodes directory
        for file_path in self.episodes_dir.rglob("*"):
            if file_path.is_file():
                if str(file_path.resolve()) not in db_files:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    bytes_freed += size
                    logger.info(f"Deleted orphaned file: {file_path}")

        # Scan converted directory
        for file_path in self.converted_dir.rglob("*"):
            if file_path.is_file():
                if str(file_path.resolve()) not in db_files:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    bytes_freed += size
                    logger.info(f"Deleted orphaned file: {file_path}")

        logger.info(f"Cleaned up {deleted_count} orphaned files, freed {bytes_freed / (1024*1024):.2f} MB")

        return deleted_count, bytes_freed

    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of a directory in bytes."""
        if not directory.exists():
            return 0

        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception as e:
                    logger.warning(f"Could not get size of {file_path}: {e}")
        return total_size

    def _delete_episode_files(self, episode: Episode) -> int:
        """
        Delete files associated with an episode.

        Returns:
            Total bytes deleted
        """
        bytes_deleted = 0

        # Delete original file
        if episode.local_path:
            local_path = Path(episode.local_path)
            if local_path.exists():
                try:
                    size = local_path.stat().st_size
                    local_path.unlink()
                    bytes_deleted += size
                    logger.debug(f"Deleted: {local_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {local_path}: {e}")

        # Delete converted file (if different)
        if episode.converted_path and episode.converted_path != episode.local_path:
            converted_path = Path(episode.converted_path)
            if converted_path.exists():
                try:
                    size = converted_path.stat().st_size
                    converted_path.unlink()
                    bytes_deleted += size
                    logger.debug(f"Deleted: {converted_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {converted_path}: {e}")

        return bytes_deleted


# Global instance
storage_service = StorageService()
