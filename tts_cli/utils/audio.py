"""Shared audio utilities for TTS CLI providers."""

import logging
import os
import subprocess
from typing import Dict, Any

from ..exceptions import DependencyError, ProviderError, AudioPlaybackError


logger = logging.getLogger(__name__)


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
    try:
        subprocess.run([
            'ffplay', '-nodisp', '-autoexit', audio_path
        ], stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError:
        raise DependencyError("ffplay not found. Please install ffmpeg for audio playback.")
    except subprocess.CalledProcessError as e:
        raise AudioPlaybackError(f"Audio playback failed: {e}")


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
    except FileNotFoundError:
        raise DependencyError("ffmpeg not found. Please install ffmpeg for format conversion.")
    except subprocess.CalledProcessError as e:
        raise ProviderError(f"Audio conversion failed: {e}")


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
        try:
            os.unlink(input_path)
        except (OSError, FileNotFoundError):
            # Ignore cleanup failures
            logger.debug(f"Could not clean up temporary file: {input_path}")


def create_ffplay_process(args: list = None, **kwargs) -> subprocess.Popen:
    """Create and start an ffplay process with common settings.
    
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
        return subprocess.Popen(cmd, **default_kwargs)
    except FileNotFoundError:
        raise DependencyError("ffplay not found. Please install ffmpeg for audio streaming.")


def stream_audio_data(audio_data: bytes, format_args: list = None) -> None:
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
            
    except FileNotFoundError:
        raise DependencyError("ffplay not found. Please install ffmpeg for audio streaming.")
    except (subprocess.SubprocessError, OSError) as e:
        raise AudioPlaybackError(f"Audio streaming failed: {e}")


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