"""Podcast service for RSS feed parsing and management."""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import feedparser
import httpx

from ..database import Podcast, Episode
from ..schemas.podcast import PodcastCreate, PodcastUpdate
from ..schemas.episode import EpisodeCreate


logger = logging.getLogger(__name__)


class PodcastService:
    """Service for managing podcasts and RSS feeds."""

    def __init__(self, db: Session):
        self.db = db

    async def validate_rss_url(self, rss_url: str) -> bool:
        """Validate that the RSS URL is accessible and parseable."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(rss_url)
                response.raise_for_status()

            # Try to parse the feed
            feed = feedparser.parse(response.text)

            # Check if it's a valid feed
            if not feed.get('feed') or not feed.get('entries'):
                logger.warning(f"Invalid RSS feed structure: {rss_url}")
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating RSS URL {rss_url}: {e}")
            return False

    async def parse_rss_feed(self, rss_url: str) -> dict:
        """Parse RSS feed and extract podcast metadata."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(rss_url)
                response.raise_for_status()

            feed = feedparser.parse(response.text)

            if not feed.get('feed'):
                raise ValueError("Invalid RSS feed structure")

            feed_data = feed.feed

            # Extract podcast metadata
            podcast_data = {
                'title': feed_data.get('title', 'Unknown Podcast'),
                'description': feed_data.get('description') or feed_data.get('subtitle'),
                'image_url': None
            }

            # Try to get image URL from various possible locations
            if hasattr(feed_data, 'image'):
                podcast_data['image_url'] = feed_data.image.get('href')
            elif hasattr(feed_data, 'itunes_image'):
                podcast_data['image_url'] = feed_data.itunes_image.get('href')

            return podcast_data

        except Exception as e:
            logger.error(f"Error parsing RSS feed {rss_url}: {e}")
            raise ValueError(f"Failed to parse RSS feed: {str(e)}")

    async def create_podcast(self, podcast_create: PodcastCreate) -> Podcast:
        """Create a new podcast from RSS URL."""
        # Check if podcast already exists
        existing = self.db.query(Podcast).filter(
            Podcast.rss_url == podcast_create.rss_url
        ).first()

        if existing:
            raise ValueError("Podcast with this RSS URL already exists")

        # Validate RSS URL
        is_valid = await self.validate_rss_url(podcast_create.rss_url)
        if not is_valid:
            raise ValueError("Invalid or inaccessible RSS feed URL")

        # Parse feed to get metadata
        feed_data = await self.parse_rss_feed(podcast_create.rss_url)

        # Create podcast
        podcast = Podcast(
            title=feed_data['title'],
            rss_url=podcast_create.rss_url,
            description=feed_data.get('description'),
            image_url=feed_data.get('image_url'),
            episode_limit=podcast_create.episode_limit,
            auto_download=podcast_create.auto_download,
            last_checked=None
        )

        self.db.add(podcast)
        self.db.commit()
        self.db.refresh(podcast)

        # Fetch initial episodes
        await self.fetch_episodes(podcast.id)

        logger.info(f"Created podcast: {podcast.title} (ID: {podcast.id})")
        return podcast

    async def fetch_episodes(self, podcast_id: int) -> List[Episode]:
        """Fetch episodes from podcast RSS feed."""
        podcast = self.db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast:
            raise ValueError(f"Podcast {podcast_id} not found")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(podcast.rss_url)
                response.raise_for_status()

            feed = feedparser.parse(response.text)

            new_episodes = []

            for entry in feed.entries:
                # Extract episode GUID (unique identifier)
                guid = entry.get('id') or entry.get('guid') or entry.get('link')
                if not guid:
                    logger.warning(f"Episode missing GUID, skipping: {entry.get('title')}")
                    continue

                # Check if episode already exists
                existing = self.db.query(Episode).filter(Episode.guid == guid).first()
                if existing:
                    continue

                # Extract audio URL
                audio_url = None
                if hasattr(entry, 'enclosures') and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if 'audio' in enclosure.get('type', ''):
                            audio_url = enclosure.get('href') or enclosure.get('url')
                            break

                if not audio_url:
                    logger.warning(f"No audio URL found for episode: {entry.get('title')}")
                    continue

                # Parse publication date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])

                # Extract duration (in seconds)
                duration = None
                if hasattr(entry, 'itunes_duration'):
                    try:
                        # Duration can be in format "HH:MM:SS" or seconds
                        duration_str = entry.itunes_duration
                        if ':' in duration_str:
                            parts = duration_str.split(':')
                            if len(parts) == 3:  # HH:MM:SS
                                duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            elif len(parts) == 2:  # MM:SS
                                duration = int(parts[0]) * 60 + int(parts[1])
                        else:
                            duration = int(duration_str)
                    except (ValueError, AttributeError):
                        pass

                # Create episode
                episode = Episode(
                    podcast_id=podcast_id,
                    title=entry.get('title', 'Untitled Episode'),
                    description=entry.get('description') or entry.get('summary'),
                    audio_url=audio_url,
                    guid=guid,
                    pub_date=pub_date,
                    duration=duration,
                    file_size=None,  # Will be determined during download
                    download_status='pending',
                    download_progress=0,
                    synced_to_watch=False
                )

                self.db.add(episode)
                new_episodes.append(episode)

            # Update last_checked timestamp
            podcast.last_checked = datetime.utcnow()

            self.db.commit()

            logger.info(f"Fetched {len(new_episodes)} new episodes for podcast {podcast.title}")
            return new_episodes

        except Exception as e:
            logger.error(f"Error fetching episodes for podcast {podcast_id}: {e}")
            self.db.rollback()
            raise ValueError(f"Failed to fetch episodes: {str(e)}")

    def get_podcast(self, podcast_id: int) -> Optional[Podcast]:
        """Get podcast by ID."""
        return self.db.query(Podcast).filter(Podcast.id == podcast_id).first()

    def get_all_podcasts(self) -> List[Podcast]:
        """Get all podcasts."""
        return self.db.query(Podcast).all()

    def update_podcast(self, podcast_id: int, podcast_update: PodcastUpdate) -> Podcast:
        """Update podcast settings."""
        podcast = self.db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast:
            raise ValueError(f"Podcast {podcast_id} not found")

        # Update fields
        update_data = podcast_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(podcast, field, value)

        podcast.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(podcast)

        logger.info(f"Updated podcast: {podcast.title} (ID: {podcast.id})")
        return podcast

    def delete_podcast(self, podcast_id: int) -> bool:
        """Delete podcast and all associated episodes."""
        podcast = self.db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast:
            raise ValueError(f"Podcast {podcast_id} not found")

        # Episodes will be cascade deleted due to relationship
        self.db.delete(podcast)
        self.db.commit()

        logger.info(f"Deleted podcast: {podcast.title} (ID: {podcast_id})")
        return True

    def get_podcast_with_episode_count(self, podcast_id: int) -> Optional[dict]:
        """Get podcast with episode count."""
        podcast = self.get_podcast(podcast_id)
        if not podcast:
            return None

        episode_count = self.db.query(func.count(Episode.id)).filter(
            Episode.podcast_id == podcast_id
        ).scalar()

        return {
            'podcast': podcast,
            'episode_count': episode_count
        }

    def get_all_podcasts_with_counts(self) -> List[dict]:
        """Get all podcasts with episode counts."""
        podcasts = self.get_all_podcasts()

        result = []
        for podcast in podcasts:
            episode_count = self.db.query(func.count(Episode.id)).filter(
                Episode.podcast_id == podcast.id
            ).scalar()

            result.append({
                'podcast': podcast,
                'episode_count': episode_count
            })

        return result
