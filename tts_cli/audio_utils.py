"""Shared audio utilities for TTS providers to avoid code duplication."""

import os
import tempfile
import subprocess
import logging
from typing import Optional, List, Callable, Any
from pathlib import Path

from .config import get_config_value
from .exceptions import DependencyError, AudioPlaybackError


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
        
    except FileNotFoundError:
        logger.warning(f"FFplay not available, audio saved to: {audio_path}")
        raise DependencyError(
            f"Audio generated but cannot play automatically. File saved to: {audio_path}"
        )
    except subprocess.CalledProcessError as e:
        logger.warning(f"FFplay failed to play audio file: {e}")
        raise AudioPlaybackError(
            f"Audio generated but playback failed. File saved to: {audio_path}"
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"FFplay playback timed out after {timeout} seconds")
        raise AudioPlaybackError(
            f"Audio playback timed out. File saved to: {audio_path}"
        )
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
        synthesize_func: Function to call for synthesis (should accept text, output_path, and kwargs)
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
    except FileNotFoundError:
        raise DependencyError(
            "ffplay not found. Please install ffmpeg:\n"
            "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Windows: Download from https://ffmpeg.org/download.html"
        )


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
        stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
        exit_code = process.returncode
        
        if exit_code != 0:
            logger.error(f"FFplay {context} failed (exit code: {exit_code}): {stderr_output}")
            raise AudioPlaybackError(f"Audio {context} failed: {stderr_output}")
        else:
            logger.debug(f"FFplay {context} completed successfully")