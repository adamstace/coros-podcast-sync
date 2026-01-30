"""Automatic storage cleanup task."""

import logging
from ..database import get_db
from ..services.storage_service import storage_service

logger = logging.getLogger(__name__)


def auto_cleanup_task():
    """
    Periodic cleanup task.

    Runs the following cleanup operations:
    1. Clean up failed downloads
    2. Clean up orphaned files
    3. Optionally clean up old episodes (configurable)
    """
    logger.info("Starting automatic cleanup task...")

    db = next(get_db())

    try:
        # Clean up failed downloads
        failed_deleted, failed_bytes = storage_service.cleanup_failed_downloads(db)
        if failed_deleted > 0:
            logger.info(f"Cleaned up {failed_deleted} failed downloads, freed {failed_bytes / (1024*1024):.2f} MB")

        # Clean up orphaned files
        orphaned_deleted, orphaned_bytes = storage_service.cleanup_orphaned_files(db)
        if orphaned_deleted > 0:
            logger.info(f"Cleaned up {orphaned_deleted} orphaned files, freed {orphaned_bytes / (1024*1024):.2f} MB")

        total_deleted = failed_deleted + orphaned_deleted
        total_freed = failed_bytes + orphaned_bytes

        logger.info(f"Auto-cleanup complete: {total_deleted} items deleted, {total_freed / (1024*1024):.2f} MB freed")

    except Exception as e:
        logger.error(f"Auto-cleanup task failed: {e}")
    finally:
        db.close()
