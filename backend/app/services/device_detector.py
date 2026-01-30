"""USB device detection service for Coros watches."""

import logging
from pathlib import Path
from typing import Optional
import platform
import os
from string import ascii_uppercase

from ..config import settings


logger = logging.getLogger(__name__)


class DeviceDetector:
    """Service for detecting Coros watch via USB."""

    def __init__(self):
        self.os_name = platform.system()

    def is_watch_connected(self) -> bool:
        """Check if Coros watch is connected via USB."""
        watch_path = self.get_watch_mount_point()
        if watch_path and watch_path.exists():
            # Verify Music folder exists
            music_folder = watch_path / settings.music_folder_name
            return music_folder.exists() and music_folder.is_dir()
        return False

    def get_watch_mount_point(self) -> Optional[Path]:
        """
        Find the watch mount point by checking common locations.

        Returns:
            Path to watch mount point, or None if not found
        """
        # Check user-configured path first
        if settings.watch_mount_path:
            configured_path = Path(settings.watch_mount_path)
            if self._is_valid_watch_path(configured_path):
                logger.debug(f"Watch found at configured path: {configured_path}")
                return configured_path

        # Auto-detect based on OS
        if self.os_name == "Darwin":  # macOS
            return self._detect_macos()
        elif self.os_name == "Windows":
            return self._detect_windows()
        elif self.os_name == "Linux":
            return self._detect_linux()

        logger.warning(f"Unsupported operating system: {self.os_name}")
        return None

    def _is_valid_watch_path(self, path: Path) -> bool:
        """Check if path is a valid Coros watch mount."""
        if not path.exists() or not path.is_dir():
            return False

        # Check for Music folder
        music_folder = path / settings.music_folder_name
        if not music_folder.exists() or not music_folder.is_dir():
            return False

        # Additional validation: check if path is writable
        try:
            test_file = music_folder / ".coros_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            logger.debug(f"Path not writable: {path}")
            return False

    def _detect_macos(self) -> Optional[Path]:
        """Detect watch on macOS."""
        volumes_path = Path("/Volumes")

        if not volumes_path.exists():
            return None

        try:
            for device in volumes_path.iterdir():
                if device.is_dir() and self._is_valid_watch_path(device):
                    logger.info(f"Watch detected on macOS: {device}")
                    return device
        except PermissionError as e:
            logger.error(f"Permission error scanning /Volumes: {e}")

        return None

    def _detect_windows(self) -> Optional[Path]:
        """Detect watch on Windows."""
        # Scan all drive letters
        for letter in ascii_uppercase:
            drive = Path(f"{letter}:/")

            # Check if drive exists
            if not drive.exists():
                continue

            if self._is_valid_watch_path(drive):
                logger.info(f"Watch detected on Windows: {drive}")
                return drive

        return None

    def _detect_linux(self) -> Optional[Path]:
        """Detect watch on Linux."""
        # Try common mount points
        mount_points = [
            Path("/media") / os.getenv("USER", ""),
            Path("/run/media") / os.getenv("USER", ""),
            Path("/mnt")
        ]

        for base_path in mount_points:
            if not base_path.exists():
                continue

            try:
                for device in base_path.iterdir():
                    if device.is_dir() and self._is_valid_watch_path(device):
                        logger.info(f"Watch detected on Linux: {device}")
                        return device
            except PermissionError as e:
                logger.error(f"Permission error scanning {base_path}: {e}")
                continue

        return None

    def get_watch_music_folder(self) -> Optional[Path]:
        """
        Get the Music folder path on the watch.

        Returns:
            Path to Music folder, or None if watch not connected
        """
        watch_path = self.get_watch_mount_point()
        if watch_path:
            music_folder = watch_path / settings.music_folder_name
            if music_folder.exists():
                return music_folder
        return None

    def get_watch_storage_info(self) -> Optional[dict]:
        """
        Get storage information for the watch.

        Returns:
            Dictionary with storage info, or None if watch not connected
        """
        watch_path = self.get_watch_mount_point()
        if not watch_path:
            return None

        try:
            # Get disk usage statistics
            stat = os.statvfs(str(watch_path))

            # Calculate sizes in bytes
            total_bytes = stat.f_frsize * stat.f_blocks
            free_bytes = stat.f_frsize * stat.f_bavail
            used_bytes = total_bytes - free_bytes

            # Convert to MB for readability
            total_mb = total_bytes / (1024 * 1024)
            free_mb = free_bytes / (1024 * 1024)
            used_mb = used_bytes / (1024 * 1024)
            used_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0

            return {
                'total_bytes': total_bytes,
                'free_bytes': free_bytes,
                'used_bytes': used_bytes,
                'total_mb': round(total_mb, 2),
                'free_mb': round(free_mb, 2),
                'used_mb': round(used_mb, 2),
                'used_percent': round(used_percent, 2),
                'mount_point': str(watch_path)
            }

        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return None

    def get_watch_info(self) -> Optional[dict]:
        """
        Get comprehensive watch information.

        Returns:
            Dictionary with watch info, or None if not connected
        """
        if not self.is_watch_connected():
            return None

        watch_path = self.get_watch_mount_point()
        storage_info = self.get_watch_storage_info()

        info = {
            'connected': True,
            'mount_point': str(watch_path) if watch_path else None,
            'music_folder': str(self.get_watch_music_folder()),
            'os': self.os_name
        }

        if storage_info:
            info.update(storage_info)

        return info


# Global instance
device_detector = DeviceDetector()
