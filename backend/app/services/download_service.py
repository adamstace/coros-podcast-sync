"""Episode download service with progress tracking."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import httpx
import aiofiles

from ..database import Episode, Podcast
from ..config import settings
from .audio_converter import audio_converter


logger = logging.getLogger(__name__)


class DownloadService:
    """Service for downloading podcast episodes."""

    def __init__(self, db: Session):
        self.db = db
        self.active_downloads: Dict[int, asyncio.Task] = {}

    async def download_episode(
        self,
        episode_id: int,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> Optional[Path]:
        """
        Download episode audio file.

        Args:
            episode_id: Episode ID to download
            progress_callback: Optional callback(episode_id, bytes_downloaded, total_bytes)

        Returns:
            Path to downloaded file or None if failed
        """
        episode = self.db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            logger.error(f"Episode {episode_id} not found")
            return None

        # Check if already downloaded
        if episode.download_status == 'downloaded' and episode.local_path:
            local_path = Path(episode.local_path)
            if local_path.exists():
                logger.info(f"Episode {episode_id} already downloaded: {local_path}")
                return local_path

        # Update status to downloading
        episode.download_status = 'downloading'
        episode.download_progress = 0
        self.db.commit()

        try:
            # Get podcast for filename generation
            podcast = self.db.query(Podcast).filter(Podcast.id == episode.podcast_id).first()
            if not podcast:
                raise ValueError(f"Podcast {episode.podcast_id} not found")

            # Generate filename
            filename = self._generate_filename(podcast, episode)
            local_path = settings.local_storage_path / filename

            # Ensure directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file with progress tracking
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream('GET', episode.audio_url) as response:
                    response.raise_for_status()

                    # Get total file size
                    total_size = int(response.headers.get('content-length', 0))
                    episode.file_size = total_size

                    bytes_downloaded = 0

                    # Download in chunks
                    async with aiofiles.open(local_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            if chunk:
                                await f.write(chunk)
                                bytes_downloaded += len(chunk)

                                # Update progress
                                if total_size > 0:
                                    progress = int((bytes_downloaded / total_size) * 100)
                                    episode.download_progress = progress

                                    # Call progress callback
                                    if progress_callback:
                                        try:
                                            progress_callback(episode_id, bytes_downloaded, total_size)
                                        except Exception as e:
                                            logger.error(f"Error in progress callback: {e}")

                                    # Commit every 10%
                                    if progress % 10 == 0:
                                        self.db.commit()

            # Update episode with success
            episode.download_status = 'downloaded'
            episode.download_progress = 100
            episode.local_path = str(local_path)
            self.db.commit()

            logger.info(f"Successfully downloaded episode {episode_id} to {local_path}")

            # Auto-convert to MP3 if needed
            try:
                logger.info(f"Starting audio conversion for episode {episode_id}")
                converted_path = await audio_converter.convert_episode_audio(
                    episode_id=episode_id,
                    input_path=local_path,
                    keep_original=True  # Keep original file
                )

                if converted_path and converted_path != local_path:
                    # Update episode with converted path
                    episode.converted_path = str(converted_path)
                    self.db.commit()
                    logger.info(f"Episode {episode_id} converted to MP3: {converted_path}")
                elif converted_path == local_path:
                    # File was already MP3
                    episode.converted_path = str(local_path)
                    self.db.commit()
                    logger.info(f"Episode {episode_id} is already MP3")
                else:
                    logger.warning(f"Failed to convert episode {episode_id}, but download was successful")

            except Exception as convert_error:
                logger.error(f"Error converting episode {episode_id}: {convert_error}")
                # Don't fail the download if conversion fails

            return local_path

        except Exception as e:
            logger.error(f"Error downloading episode {episode_id}: {e}")

            # Update status to failed
            episode.download_status = 'failed'
            episode.download_progress = 0
            self.db.commit()

            # Clean up partial file
            if local_path and local_path.exists():
                try:
                    local_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up partial download: {cleanup_error}")

            return None

    def _generate_filename(self, podcast: Podcast, episode: Episode) -> str:
        """Generate a safe filename for the episode."""
        # Sanitize podcast and episode titles
        podcast_name = self._sanitize_filename(podcast.title)
        episode_title = self._sanitize_filename(episode.title)

        # Get file extension from audio URL
        extension = self._get_extension(episode.audio_url)

        # Create filename: podcast_name - episode_title.ext
        filename = f"{podcast_name} - {episode_title}{extension}"

        # Limit filename length (max 255 chars for most filesystems)
        if len(filename) > 200:
            episode_title = episode_title[:100]
            filename = f"{podcast_name} - {episode_title}{extension}"

        return filename

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use in filename."""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')

        # Remove leading/trailing spaces and dots
        name = name.strip('. ')

        # Replace multiple spaces with single space
        name = ' '.join(name.split())

        return name

    def _get_extension(self, url: str) -> str:
        """Extract file extension from URL."""
        # Try to get extension from URL
        url_path = url.split('?')[0]  # Remove query params
        extension = Path(url_path).suffix

        # Default to .mp3 if no extension found
        if not extension:
            extension = '.mp3'

        return extension.lower()

    async def queue_download(self, episode_id: int) -> bool:
        """
        Queue episode for download (non-blocking).

        Args:
            episode_id: Episode ID to download

        Returns:
            True if queued successfully, False otherwise
        """
        if episode_id in self.active_downloads:
            logger.info(f"Episode {episode_id} already queued for download")
            return False

        # Create download task
        task = asyncio.create_task(self.download_episode(episode_id))
        self.active_downloads[episode_id] = task

        # Clean up task when done
        def cleanup(task):
            if episode_id in self.active_downloads:
                del self.active_downloads[episode_id]

        task.add_done_callback(cleanup)

        logger.info(f"Queued episode {episode_id} for download")
        return True

    def cancel_download(self, episode_id: int) -> bool:
        """
        Cancel ongoing download.

        Args:
            episode_id: Episode ID to cancel

        Returns:
            True if cancelled, False if not downloading
        """
        if episode_id not in self.active_downloads:
            return False

        task = self.active_downloads[episode_id]
        task.cancel()

        # Update episode status
        episode = self.db.query(Episode).filter(Episode.id == episode_id).first()
        if episode:
            episode.download_status = 'pending'
            episode.download_progress = 0
            self.db.commit()

        logger.info(f"Cancelled download for episode {episode_id}")
        return True

    def get_download_status(self, episode_id: int) -> dict:
        """Get current download status for an episode."""
        episode = self.db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            return {
                'status': 'not_found',
                'progress': 0,
                'is_downloading': False
            }

        return {
            'status': episode.download_status,
            'progress': episode.download_progress,
            'is_downloading': episode_id in self.active_downloads,
            'local_path': episode.local_path,
            'file_size': episode.file_size
        }

    async def download_podcast_episodes(
        self,
        podcast_id: int,
        limit: Optional[int] = None
    ) -> list[Episode]:
        """
        Download episodes for a podcast.

        Args:
            podcast_id: Podcast ID
            limit: Maximum number of episodes to download (None = no limit)

        Returns:
            List of downloaded episodes
        """
        # Get pending episodes
        query = self.db.query(Episode).filter(
            Episode.podcast_id == podcast_id,
            Episode.download_status == 'pending'
        ).order_by(Episode.pub_date.desc())

        if limit:
            query = query.limit(limit)

        episodes = query.all()

        downloaded = []
        for episode in episodes:
            result = await self.download_episode(episode.id)
            if result:
                downloaded.append(episode)

        return downloaded

    def delete_episode_file(self, episode_id: int) -> bool:
        """
        Delete episode file from disk.

        Args:
            episode_id: Episode ID

        Returns:
            True if deleted, False otherwise
        """
        episode = self.db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode or not episode.local_path:
            return False

        try:
            local_path = Path(episode.local_path)
            if local_path.exists():
                local_path.unlink()
                logger.info(f"Deleted file for episode {episode_id}: {local_path}")

            # Update episode
            episode.local_path = None
            episode.download_status = 'pending'
            episode.download_progress = 0

            # Also delete converted file if exists
            if episode.converted_path:
                converted_path = Path(episode.converted_path)
                if converted_path.exists():
                    converted_path.unlink()
                    logger.info(f"Deleted converted file: {converted_path}")
                episode.converted_path = None

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error deleting episode file {episode_id}: {e}")
            return False
