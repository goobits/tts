"""Shared audio utilities for TTS providers to avoid code duplication."""

import logging
import os
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional

from .config import get_config_value
from .exceptions import AudioPlaybackError, DependencyError

# Module logger
logger = logging.getLogger(__name__)


def play_audio_with_ffplay(
    audio_path: str,
    logger: Optional[logging.Logger] = None,
    cleanup: bool = False,
    timeout: Optional[int] = None
) -> None:
    """
    Play an audio file using ffplay.

    Args:
        audio_path: Path to the audio file to play
        logger: Optional logger instance for debugging
        cleanup: Whether to delete the file after playing
        timeout: Optional timeout for ffplay process

    Raises:
        DependencyError: If ffplay is not available
        AudioPlaybackError: If playback fails
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if timeout is None:
        timeout = get_config_value('ffmpeg_conversion_timeout')

    try:
        # Play the audio file
        subprocess.run([
            'ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', audio_path
        ], check=True, timeout=timeout)
        logger.debug(f"Audio playback completed: {audio_path}")

    except FileNotFoundError as e:
        logger.warning(f"FFplay not available, audio saved to: {audio_path}")
        raise DependencyError(
            f"Audio generated but cannot play automatically. File saved to: {audio_path}"
        ) from e
    except subprocess.CalledProcessError as e:
        logger.warning(f"FFplay failed to play audio file: {e}")
        raise AudioPlaybackError(
            f"Audio generated but playback failed. File saved to: {audio_path}"
        ) from e
    except subprocess.TimeoutExpired as e:
        logger.warning(f"FFplay playback timed out after {timeout} seconds")
        raise AudioPlaybackError(
            f"Audio playback timed out. File saved to: {audio_path}"
        ) from e
    finally:
        if cleanup:
            cleanup_file(audio_path, logger)


def cleanup_file(file_path: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Safely clean up a temporary file.

    Args:
        file_path: Path to the file to delete
        logger: Optional logger instance for debugging
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
        else:
            logger.debug(f"Temporary file does not exist, no cleanup needed: {file_path}")
    except OSError as e:
        # Log but don't fail if we can't clean up temp file
        logger.debug(f"Could not clean up temporary file {file_path}: {e}")
    except Exception as e:
        # Unexpected error during cleanup
        logger.warning(f"Unexpected error cleaning up temporary file {file_path}: {e}")


def stream_via_tempfile(
    synthesize_func: Callable,
    text: str,
    logger: logging.Logger,
    file_suffix: str = '.mp3',
    **synthesis_kwargs: Any
) -> None:
    """
    Fallback streaming method using temporary file when direct streaming fails.

    This is a generic implementation that providers can use to avoid duplication.

    Args:
        synthesize_func: Function to call for synthesis
            (should accept text, output_path, and kwargs)
        text: Text to synthesize
        logger: Logger instance for debugging
        file_suffix: File extension for the temporary file
        **synthesis_kwargs: Additional arguments to pass to the synthesis function
    """
    logger.info("Using temporary file fallback for audio streaming")

    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
        temp_file = tmp.name

    try:
        # Generate audio to temporary file
        synthesize_func(text, temp_file, **synthesis_kwargs)

        # Play the temporary file
        play_audio_with_ffplay(temp_file, logger, cleanup=False)

    finally:
        # Always clean up temporary file
        cleanup_file(temp_file, logger)


def create_ffplay_process(
    logger: logging.Logger,
    format_args: Optional[List[str]] = None,
    additional_args: Optional[List[str]] = None
) -> subprocess.Popen:
    """
    Create an ffplay process for streaming audio.

    Args:
        logger: Logger instance for debugging
        format_args: Format-specific arguments (e.g., ['-f', 'mp3'])
        additional_args: Additional ffplay arguments

    Returns:
        subprocess.Popen instance ready to receive audio data

    Raises:
        DependencyError: If ffplay is not available
    """
    ffplay_cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'error']

    if format_args:
        ffplay_cmd.extend(format_args)

    # Add format from stdin
    ffplay_cmd.extend(['-i', 'pipe:0'])

    if additional_args:
        ffplay_cmd.extend(additional_args)

    logger.debug(f"Starting ffplay process: {' '.join(ffplay_cmd)}")

    try:
        process = subprocess.Popen(
            ffplay_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except FileNotFoundError as e:
        raise DependencyError(
            "ffplay not found. Please install ffmpeg:\n"
            "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Windows: Download from https://ffmpeg.org/download.html"
        ) from e


def handle_ffplay_process_error(
    process: subprocess.Popen,
    logger: logging.Logger,
    context: str = "streaming"
) -> None:
    """
    Handle errors from an ffplay process.

    Args:
        process: The ffplay subprocess
        logger: Logger instance
        context: Context string for error messages
    """
    if process.poll() is not None:
        stderr_output = ""
        if process.stderr:
            stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
        exit_code = process.returncode

        if exit_code != 0:
            logger.error(f"FFplay {context} failed (exit code: {exit_code}): {stderr_output}")
            raise AudioPlaybackError(f"Audio {context} failed: {stderr_output}")
        else:
            logger.debug(f"FFplay {context} completed successfully")


def check_audio_environment() -> Dict[str, Any]:
    """Check if audio streaming is available in current environment.

    Returns:
        Dict with 'available' (bool), 'reason' (str), and device availability flags
    """
    result = {
        'available': False,
        'reason': 'Unknown',
        'pulse_available': False,
        'alsa_available': False
    }

    # Check for PulseAudio
    if 'PULSE_SERVER' in os.environ:
        result['pulse_available'] = True
        result['available'] = True
        result['reason'] = 'PulseAudio available'
        return result

    # Check for ALSA devices
    try:
        if os.path.exists('/proc/asound/cards') and os.path.getsize('/proc/asound/cards') > 0:
            result['alsa_available'] = True
            result['available'] = True
            result['reason'] = 'ALSA devices available'
            return result
    except (ImportError, OSError, subprocess.SubprocessError) as e:
        logger.debug(f"ALSA check failed: {e}")

    # Check if we can reach audio system
    try:
        subprocess.run(['aplay', '--version'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     timeout=2)
        result['available'] = True
        result['reason'] = 'Audio system responsive'
        return result
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.debug(f"Audio system check failed: {e}")

    result['reason'] = 'No audio devices or audio system unavailable'
    return result


def stream_audio_file(audio_path: str) -> None:
    """Stream audio file to speakers using ffplay.

    Args:
        audio_path: Path to the audio file to play

    Raises:
        DependencyError: If ffplay is not found
        AudioPlaybackError: If playback fails
    """
    play_audio_with_ffplay(audio_path, logger=logger)


def convert_audio(input_path: str, output_path: str, output_format: str) -> None:
    """Convert audio file to different format using ffmpeg.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        output_format: Target audio format (extension will be added if needed)

    Raises:
        DependencyError: If ffmpeg is not found
        ProviderError: If conversion fails
    """
    try:
        subprocess.run([
            'ffmpeg', '-i', input_path, '-y', output_path
        ], stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError as e:
        raise DependencyError(
            "ffmpeg not found. Please install ffmpeg for format conversion."
        ) from e
    except subprocess.CalledProcessError as e:
        from .exceptions import ProviderError
        raise ProviderError(f"Audio conversion failed: {e}") from e


def convert_with_cleanup(input_path: str, output_path: str, output_format: str) -> None:
    """Convert audio file with automatic cleanup of input file.

    This is a convenience function that converts audio and cleans up the temporary
    input file afterwards, even if conversion fails.

    Args:
        input_path: Path to temporary input audio file (will be deleted)
        output_path: Path for output audio file
        output_format: Target audio format

    Raises:
        DependencyError: If ffmpeg is not found
        ProviderError: If conversion fails
    """
    try:
        convert_audio(input_path, output_path, output_format)
    finally:
        # Always cleanup temporary input file
        cleanup_file(input_path, logger)


def create_ffplay_process_simple(
    args: Optional[List[str]] = None, **kwargs: Any
) -> subprocess.Popen[Any]:
    """Create and start an ffplay process with common settings (simple version).

    This is the simpler version from utils/audio.py with a different signature.
    Use create_ffplay_process for the standard version with logging support.

    Args:
        args: Additional command line arguments for ffplay
        **kwargs: Additional arguments passed to subprocess.Popen

    Returns:
        Running ffplay subprocess

    Raises:
        DependencyError: If ffplay is not found
    """
    cmd = ['ffplay']
    if args:
        cmd.extend(args)

    # Set common defaults
    default_kwargs = {
        'stdin': subprocess.PIPE,
        'stdout': subprocess.DEVNULL,
        'stderr': subprocess.DEVNULL,
        'bufsize': 0
    }
    default_kwargs.update(kwargs)

    try:
        process: subprocess.Popen[Any] = subprocess.Popen(cmd, **default_kwargs)  # type: ignore
        return process
    except FileNotFoundError as e:
        raise DependencyError("ffplay not found. Please install ffmpeg for audio streaming.") from e


def stream_audio_data(audio_data: bytes, format_args: Optional[List[str]] = None) -> None:
    """Stream raw audio data through ffplay.

    Args:
        audio_data: Raw audio bytes to stream
        format_args: Additional format arguments for ffplay

    Raises:
        DependencyError: If ffplay is not found
        AudioPlaybackError: If streaming fails
    """
    cmd = ['ffplay', '-nodisp', '-autoexit', '-']
    if format_args:
        cmd.extend(format_args)

    try:
        process = subprocess.Popen(cmd,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)

        process.communicate(input=audio_data)

        if process.returncode != 0:
            raise AudioPlaybackError(f"Audio streaming failed with code {process.returncode}")

    except FileNotFoundError as e:
        raise DependencyError("ffplay not found. Please install ffmpeg for audio streaming.") from e
    except (subprocess.SubprocessError, OSError) as e:
        raise AudioPlaybackError(f"Audio streaming failed: {e}") from e


def normalize_audio_path(path: str, default_format: str = "wav") -> str:
    """Normalize audio file path and ensure it has proper extension.

    Args:
        path: Input file path
        default_format: Default format extension to add if missing

    Returns:
        Normalized path with proper extension
    """
    if not path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac')):
        if not path.endswith('.'):
            path += '.'
        path += default_format
    return path


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using ffprobe.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds, or 0.0 if cannot be determined
    """
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', audio_path
        ], capture_output=True, text=True, timeout=5)

        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.SubprocessError, ValueError, subprocess.TimeoutExpired):
        logger.debug(f"Could not get duration for {audio_path}")

    return 0.0


def validate_audio_file(audio_path: str) -> bool:
    """Validate that a file is a readable audio file.

    Args:
        audio_path: Path to audio file to validate

    Returns:
        True if file appears to be valid audio, False otherwise
    """
    if not os.path.exists(audio_path):
        return False

    try:
        # Use ffprobe to validate the file
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=format_name',
            audio_path
        ], capture_output=True, timeout=5)

        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False
