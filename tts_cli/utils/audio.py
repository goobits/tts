import tempfile
import subprocess
import os
import logging
from typing import Optional
from ..exceptions import AudioConversionError, DependencyError


logger = logging.getLogger(__name__)


def convert_audio(input_path: str, output_path: str, output_format: str) -> None:
    """
    Convert audio file to specified format using ffmpeg.
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        output_format: Target format (e.g., 'mp3', 'wav', 'ogg')
        
    Raises:
        AudioConversionError: If conversion fails
        DependencyError: If ffmpeg is not available
    """
    logger.debug(f"Converting {input_path} to {output_format} format")
    
    try:
        result = subprocess.run([
            'ffmpeg', '-i', input_path, '-y', output_path
        ], check=True, capture_output=True, text=True)
        logger.debug("Format conversion completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e.stderr}")
        raise AudioConversionError(f"Audio format conversion failed. Error: {e.stderr}")
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        raise DependencyError("ffmpeg not found. Please install ffmpeg to use non-default formats.")


def convert_with_cleanup(input_path: str, output_path: str, output_format: str, 
                        cleanup_input: bool = True) -> None:
    """
    Convert audio with automatic cleanup of temporary input file.
    
    Args:
        input_path: Path to input audio file (will be deleted if cleanup_input=True)
        output_path: Path for output audio file  
        output_format: Target format
        cleanup_input: Whether to delete input file after conversion
        
    Raises:
        AudioConversionError: If conversion fails
        DependencyError: If ffmpeg is not available
    """
    try:
        convert_audio(input_path, output_path, output_format)
    finally:
        if cleanup_input and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError as e:
                logger.warning(f"Failed to cleanup temporary file {input_path}: {e}")