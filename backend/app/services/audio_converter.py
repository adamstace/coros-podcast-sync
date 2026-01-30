"""Audio converter service using FFmpeg."""

import logging
from pathlib import Path
from typing import Optional
import subprocess
import ffmpeg

from ..config import settings


logger = logging.getLogger(__name__)


class AudioConverter:
    """Service for converting audio files to MP3 format."""

    def __init__(self):
        self.output_format = settings.audio_format
        self.bitrate = settings.audio_bitrate

    def check_ffmpeg_installed(self) -> bool:
        """Check if FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_conversion_needed(self, file_path: Path) -> bool:
        """
        Check if audio file needs conversion.

        Args:
            file_path: Path to audio file

        Returns:
            True if conversion is needed, False if already MP3
        """
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False

        # Check file extension
        extension = file_path.suffix.lower()

        # If already MP3, no conversion needed
        if extension == '.mp3':
            logger.debug(f"File is already MP3: {file_path}")
            return False

        # List of supported formats that need conversion
        supported_formats = ['.m4a', '.aac', '.ogg', '.opus', '.flac', '.wav', '.wma']

        if extension in supported_formats:
            logger.debug(f"File needs conversion: {file_path} ({extension})")
            return True

        logger.warning(f"Unknown audio format: {extension}")
        return False

    async def convert_to_mp3(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        bitrate: Optional[str] = None
    ) -> Optional[Path]:
        """
        Convert audio file to MP3 format.

        Args:
            input_path: Path to input audio file
            output_path: Optional output path (defaults to converted/ directory)
            bitrate: Optional bitrate (e.g., '128k', '192k'). Defaults to config value.

        Returns:
            Path to converted MP3 file, or None if conversion failed
        """
        if not input_path.exists():
            logger.error(f"Input file does not exist: {input_path}")
            return None

        # Check if FFmpeg is installed
        if not self.check_ffmpeg_installed():
            logger.error("FFmpeg is not installed. Please install FFmpeg to convert audio files.")
            return None

        # Use default output path if not provided
        if output_path is None:
            output_filename = input_path.stem + '.mp3'
            output_path = settings.local_converted_path / output_filename

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use provided bitrate or default
        bitrate = bitrate or self.bitrate

        try:
            logger.info(f"Converting {input_path} to MP3 (bitrate: {bitrate})")

            # Use ffmpeg-python to convert
            stream = ffmpeg.input(str(input_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                audio_bitrate=bitrate,
                format='mp3',
                acodec='libmp3lame',
                **{'q:a': 2}  # Quality parameter for MP3
            )

            # Run conversion
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            logger.info(f"Successfully converted to: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error converting {input_path}: {e.stderr.decode() if e.stderr else str(e)}")

            # Clean up partial output file
            if output_path and output_path.exists():
                try:
                    output_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up partial conversion: {cleanup_error}")

            return None
        except Exception as e:
            logger.error(f"Error converting {input_path} to MP3: {e}")

            # Clean up partial output file
            if output_path and output_path.exists():
                try:
                    output_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up partial conversion: {cleanup_error}")

            return None

    def get_audio_info(self, file_path: Path) -> Optional[dict]:
        """
        Get information about an audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio info (duration, sample_rate, etc.)
        """
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None

        try:
            probe = ffmpeg.probe(str(file_path))

            # Get audio stream
            audio_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )

            if not audio_stream:
                logger.error(f"No audio stream found in {file_path}")
                return None

            info = {
                'duration_seconds': float(probe['format'].get('duration', 0)),
                'channels': audio_stream.get('channels'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'codec': audio_stream.get('codec_name'),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'file_size_bytes': int(probe['format'].get('size', 0))
            }

            return info

        except Exception as e:
            logger.error(f"Error getting audio info for {file_path}: {e}")
            return None

    def delete_original_after_conversion(self, original_path: Path) -> bool:
        """
        Delete original audio file after successful conversion.

        Args:
            original_path: Path to original audio file

        Returns:
            True if deleted, False otherwise
        """
        try:
            if original_path.exists():
                original_path.unlink()
                logger.info(f"Deleted original file: {original_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting original file {original_path}: {e}")
            return False

    async def convert_episode_audio(
        self,
        episode_id: int,
        input_path: Path,
        keep_original: bool = True
    ) -> Optional[Path]:
        """
        Convert episode audio file to MP3.

        Args:
            episode_id: Episode ID
            input_path: Path to downloaded audio file
            keep_original: Whether to keep original file after conversion

        Returns:
            Path to converted MP3 file, or None if conversion failed
        """
        logger.info(f"Converting episode {episode_id}: {input_path}")

        # Check if conversion is needed
        if not self.is_conversion_needed(input_path):
            logger.info(f"Episode {episode_id} does not need conversion")
            return input_path  # Return original path if already MP3

        # Convert to MP3
        converted_path = await self.convert_to_mp3(input_path)

        if converted_path:
            logger.info(f"Successfully converted episode {episode_id} to {converted_path}")

            # Optionally delete original
            if not keep_original:
                self.delete_original_after_conversion(input_path)

            return converted_path
        else:
            logger.error(f"Failed to convert episode {episode_id}")
            return None


# Global instance
audio_converter = AudioConverter()
