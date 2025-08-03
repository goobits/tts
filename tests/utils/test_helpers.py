"""
Shared test utilities for TTS CLI tests.

This module provides common fixtures, helpers, and utilities to reduce
duplication across test files and improve test maintainability.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from tts.base import TTSProvider
from tts.types import Config, ProviderInfo


# =============================================================================
# AUDIO FILE VALIDATION HELPERS
# =============================================================================

try:
    import wave
    import struct
    WAVE_SUPPORT = True
except ImportError:
    WAVE_SUPPORT = False

try:
    import soundfile as sf
    SOUNDFILE_SUPPORT = True
except ImportError:
    SOUNDFILE_SUPPORT = False

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    from mutagen.oggvorbis import OggVorbis
    from mutagen.flac import FLAC
    MUTAGEN_SUPPORT = True
except ImportError:
    MUTAGEN_SUPPORT = False


class AudioValidationResult:
    """Result object for audio validation containing detailed information."""
    
    def __init__(self, valid: bool = False, **metadata):
        self.valid = valid
        self.format = metadata.get('format')
        self.duration = metadata.get('duration')
        self.sample_rate = metadata.get('sample_rate')
        self.channels = metadata.get('channels')
        self.bitrate = metadata.get('bitrate')
        self.file_size = metadata.get('file_size')
        self.has_silence = metadata.get('has_silence')
        self.error = metadata.get('error')
        
    def __bool__(self):
        return self.valid
        
    def __repr__(self):
        return f"AudioValidationResult(valid={self.valid}, format={self.format}, duration={self.duration}s)"


def validate_audio_file(file_path: Path, expected_format: Optional[str] = None) -> bool:
    """
    Validate that an audio file exists and has expected properties.
    
    Args:
        file_path: Path to the audio file
        expected_format: Expected file format (e.g., "mp3", "wav")
        
    Returns:
        True if file is valid, False otherwise
    """
    if not file_path.exists():
        return False
        
    # Check file size (should have some content)
    if file_path.stat().st_size == 0:
        return False
        
    # Check extension matches expected format
    if expected_format and file_path.suffix != f".{expected_format}":
        return False
        
    return True


def validate_audio_file_comprehensive(
    file_path: Path, 
    expected_format: Optional[str] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    expected_sample_rate: Optional[int] = None,
    expected_channels: Optional[int] = None,
    min_file_size: int = 100,
    check_silence: bool = False
) -> AudioValidationResult:
    """
    Comprehensive audio file validation with detailed metadata extraction.
    
    Args:
        file_path: Path to the audio file
        expected_format: Expected file format (e.g., "mp3", "wav")
        min_duration: Minimum expected duration in seconds
        max_duration: Maximum expected duration in seconds
        expected_sample_rate: Expected sample rate in Hz
        expected_channels: Expected number of channels
        min_file_size: Minimum file size in bytes
        check_silence: Whether to check for silence detection
        
    Returns:
        AudioValidationResult with detailed validation info
    """
    if not file_path.exists():
        return AudioValidationResult(valid=False, error="File does not exist")
    
    file_size = file_path.stat().st_size
    if file_size < min_file_size:
        return AudioValidationResult(
            valid=False, 
            file_size=file_size,
            error=f"File too small: {file_size} < {min_file_size} bytes"
        )
    
    # Extract file format from extension
    actual_format = file_path.suffix[1:].lower() if file_path.suffix else None
    
    # Check format matches expectation
    if expected_format and actual_format != expected_format.lower():
        return AudioValidationResult(
            valid=False,
            format=actual_format,
            file_size=file_size,
            error=f"Format mismatch: expected {expected_format}, got {actual_format}"
        )
    
    # Try to extract audio metadata
    metadata = extract_audio_metadata(file_path)
    if not metadata['valid']:
        return AudioValidationResult(
            valid=False,
            format=actual_format,
            file_size=file_size,
            error=metadata.get('error', 'Failed to read audio metadata')
        )
    
    # Validate duration constraints
    duration = metadata.get('duration')
    if duration is not None:
        if min_duration is not None and duration < min_duration:
            return AudioValidationResult(
                valid=False,
                format=actual_format,
                duration=duration,
                file_size=file_size,
                error=f"Duration too short: {duration}s < {min_duration}s"
            )
        if max_duration is not None and duration > max_duration:
            return AudioValidationResult(
                valid=False,
                format=actual_format,
                duration=duration,
                file_size=file_size,
                error=f"Duration too long: {duration}s > {max_duration}s"
            )
    
    # Validate sample rate
    sample_rate = metadata.get('sample_rate')
    if expected_sample_rate is not None and sample_rate != expected_sample_rate:
        return AudioValidationResult(
            valid=False,
            format=actual_format,
            duration=duration,
            sample_rate=sample_rate,
            file_size=file_size,
            error=f"Sample rate mismatch: expected {expected_sample_rate}, got {sample_rate}"
        )
    
    # Validate channels
    channels = metadata.get('channels')
    if expected_channels is not None and channels != expected_channels:
        return AudioValidationResult(
            valid=False,
            format=actual_format,
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            file_size=file_size,
            error=f"Channel count mismatch: expected {expected_channels}, got {channels}"
        )
    
    # Optional silence detection
    has_silence = None
    if check_silence and SOUNDFILE_SUPPORT:
        has_silence = detect_silence(file_path)
    
    return AudioValidationResult(
        valid=True,
        format=actual_format,
        duration=duration,
        sample_rate=sample_rate,
        channels=channels,
        bitrate=metadata.get('bitrate'),
        file_size=file_size,
        has_silence=has_silence
    )


def extract_audio_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract audio metadata from various formats.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dictionary with metadata or error information
    """
    try:
        # Try mutagen first for comprehensive metadata
        if MUTAGEN_SUPPORT:
            return _extract_metadata_mutagen(file_path)
        
        # Fallback to soundfile
        if SOUNDFILE_SUPPORT:
            return _extract_metadata_soundfile(file_path)
        
        # Fallback to wave module for WAV files
        if WAVE_SUPPORT and file_path.suffix.lower() == '.wav':
            return _extract_metadata_wave(file_path)
        
        return {'valid': False, 'error': 'No audio libraries available'}
        
    except Exception as e:
        return {'valid': False, 'error': f'Failed to extract metadata: {str(e)}'}


def _extract_metadata_mutagen(file_path: Path) -> Dict[str, Any]:
    """Extract metadata using mutagen library."""
    try:
        audio_file = mutagen.File(str(file_path))
        if audio_file is None:
            return {'valid': False, 'error': 'Mutagen could not parse file'}
        
        metadata = {
            'valid': True,
            'duration': getattr(audio_file.info, 'length', None),
            'bitrate': getattr(audio_file.info, 'bitrate', None),
            'sample_rate': getattr(audio_file.info, 'sample_rate', None),
            'channels': getattr(audio_file.info, 'channels', None)
        }
        
        return metadata
        
    except Exception as e:
        return {'valid': False, 'error': f'Mutagen error: {str(e)}'}


def _extract_metadata_soundfile(file_path: Path) -> Dict[str, Any]:
    """Extract metadata using soundfile library."""
    try:
        info = sf.info(str(file_path))
        return {
            'valid': True,
            'duration': info.duration,
            'sample_rate': info.samplerate,
            'channels': info.channels,
            'format': info.format
        }
    except Exception as e:
        return {'valid': False, 'error': f'Soundfile error: {str(e)}'}


def _extract_metadata_wave(file_path: Path) -> Dict[str, Any]:
    """Extract metadata using wave module for WAV files."""
    try:
        with wave.open(str(file_path), 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            duration = frames / float(sample_rate) if sample_rate > 0 else None
            
            return {
                'valid': True,
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'frames': frames
            }
    except Exception as e:
        return {'valid': False, 'error': f'Wave module error: {str(e)}'}


def detect_silence(file_path: Path, silence_threshold: float = 0.01) -> bool:
    """
    Detect if audio file contains significant silence.
    
    Args:
        file_path: Path to audio file
        silence_threshold: RMS threshold below which audio is considered silence
        
    Returns:
        True if significant silence detected, False otherwise
    """
    if not SOUNDFILE_SUPPORT:
        return False
        
    try:
        data, sample_rate = sf.read(str(file_path))
        
        # Calculate RMS (Root Mean Square) energy
        if len(data.shape) > 1:
            # Multi-channel - take mean across channels
            rms = ((data ** 2).mean(axis=1) ** 0.5).mean()
        else:
            # Single channel
            rms = (data ** 2).mean() ** 0.5
            
        return rms < silence_threshold
        
    except Exception:
        return False


def validate_audio_format_compatibility(file_path: Path, target_format: str) -> bool:
    """
    Check if an audio file can be converted to target format.
    
    Args:
        file_path: Path to audio file
        target_format: Target format to check compatibility for
        
    Returns:
        True if conversion is possible, False otherwise
    """
    if not file_path.exists():
        return False
    
    source_format = file_path.suffix[1:].lower()
    target_format = target_format.lower()
    
    # Common format compatibility matrix
    compatible_formats = {
        'wav': ['mp3', 'ogg', 'flac', 'aac'],
        'mp3': ['wav', 'ogg', 'flac'],
        'flac': ['wav', 'mp3', 'ogg'],
        'ogg': ['wav', 'mp3', 'flac']
    }
    
    if source_format == target_format:
        return True
        
    return target_format in compatible_formats.get(source_format, [])


def estimate_audio_duration_from_text(text: str, wpm: int = 150) -> float:
    """
    Estimate expected audio duration based on text length.
    
    Args:
        text: Text to be synthesized
        wpm: Words per minute speech rate
        
    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    return (word_count / wpm) * 60.0


def measure_synthesis_performance(
    synthesis_func, 
    text: str, 
    output_path: Path,
    **kwargs
) -> Dict[str, Any]:
    """
    Measure performance characteristics of a synthesis operation.
    
    Args:
        synthesis_func: Function to call for synthesis
        text: Text to synthesize
        output_path: Path for output file
        **kwargs: Additional arguments for synthesis function
        
    Returns:
        Dictionary with performance metrics
    """
    import time
    
    start_time = time.time()
    
    try:
        success = synthesis_func(text, str(output_path), **kwargs)
        synthesis_time = time.time() - start_time
        
        # Analyze the result
        if success and output_path.exists():
            validation_result = validate_audio_file_comprehensive(output_path)
            
            return {
                'success': True,
                'synthesis_time': synthesis_time,
                'audio_duration': validation_result.duration if validation_result.valid else None,
                'file_size': validation_result.file_size if validation_result.valid else output_path.stat().st_size,
                'real_time_factor': synthesis_time / validation_result.duration if (validation_result.valid and validation_result.duration) else None,
                'validation_result': validation_result,
                'error': None
            }
        else:
            return {
                'success': False,
                'synthesis_time': synthesis_time,
                'audio_duration': None,
                'file_size': 0,
                'real_time_factor': None,
                'validation_result': None,
                'error': 'Synthesis failed or no output file'
            }
            
    except Exception as e:
        synthesis_time = time.time() - start_time
        return {
            'success': False,
            'synthesis_time': synthesis_time,
            'audio_duration': None,
            'file_size': 0,
            'real_time_factor': None,
            'validation_result': None,
            'error': str(e)
        }


def compare_audio_validation_results(
    results: List[AudioValidationResult],
    tolerance: float = 0.2
) -> Dict[str, Any]:
    """
    Compare multiple audio validation results for consistency.
    
    Args:
        results: List of AudioValidationResult objects
        tolerance: Acceptable variance ratio (0.2 = 20%)
        
    Returns:
        Dictionary with comparison analysis
    """
    valid_results = [r for r in results if r.valid]
    
    if len(valid_results) < 2:
        return {
            'comparable': False,
            'reason': f'Not enough valid results to compare ({len(valid_results)})',
            'statistics': {}
        }
    
    # Collect metrics
    durations = [r.duration for r in valid_results if r.duration is not None]
    file_sizes = [r.file_size for r in valid_results if r.file_size is not None]
    sample_rates = [r.sample_rate for r in valid_results if r.sample_rate is not None]
    channels = [r.channels for r in valid_results if r.channels is not None]
    
    def calculate_variance(values):
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return (variance ** 0.5) / mean if mean > 0 else 0.0
    
    duration_variance = calculate_variance(durations) if durations else 0.0
    size_variance = calculate_variance(file_sizes) if file_sizes else 0.0
    
    # Check consistency
    issues = []
    if duration_variance > tolerance:
        issues.append(f"Duration variance {duration_variance:.3f} > {tolerance}")
    if size_variance > tolerance * 2:  # Allow more variance in file size
        issues.append(f"File size variance {size_variance:.3f} > {tolerance * 2}")
    
    # Check for format consistency
    formats = [r.format for r in valid_results if r.format]
    unique_formats = set(formats)
    if len(unique_formats) > 1:
        issues.append(f"Multiple formats detected: {unique_formats}")
    
    return {
        'comparable': len(issues) == 0,
        'issues': issues,
        'statistics': {
            'valid_count': len(valid_results),
            'total_count': len(results),
            'duration_variance': duration_variance,
            'file_size_variance': size_variance,
            'avg_duration': sum(durations) / len(durations) if durations else None,
            'avg_file_size': sum(file_sizes) / len(file_sizes) if file_sizes else None,
            'unique_formats': list(unique_formats),
            'unique_sample_rates': list(set(sample_rates)) if sample_rates else [],
            'unique_channels': list(set(channels)) if channels else []
        }
    }


def create_mock_audio_file(
    file_path: Path, 
    format: str = "mp3", 
    size_bytes: int = 1024
) -> Path:
    """
    Create a mock audio file for testing.
    
    Args:
        file_path: Path where to create the file
        format: Audio format extension
        size_bytes: Size of the mock file
        
    Returns:
        Path to the created file
    """
    file_path = file_path.with_suffix(f".{format}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"MOCK_AUDIO_DATA" * (size_bytes // 15))
    return file_path


def create_realistic_audio_file(
    file_path: Path,
    format: str = "wav",
    duration: float = 1.0,
    sample_rate: int = 44100,
    channels: int = 2,
    frequency: float = 440.0
) -> Path:
    """
    Create a realistic audio file with actual audio data for testing.
    
    Args:
        file_path: Path where to create the file
        format: Audio format ("wav", "mp3", etc.)
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        frequency: Tone frequency in Hz
        
    Returns:
        Path to the created file
    """
    file_path = file_path.with_suffix(f".{format}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format.lower() == "wav" and WAVE_SUPPORT:
        _create_realistic_wav(file_path, duration, sample_rate, channels, frequency)
    elif SOUNDFILE_SUPPORT:
        _create_realistic_with_soundfile(file_path, format, duration, sample_rate, channels, frequency)
    else:
        # Fallback to mock file if no audio libraries available
        return create_mock_audio_file(file_path, format, int(duration * 1000))
    
    return file_path


def _create_realistic_wav(
    file_path: Path,
    duration: float,
    sample_rate: int,
    channels: int,
    frequency: float
) -> None:
    """Create a realistic WAV file using wave module."""
    import math
    
    frames = int(duration * sample_rate)
    
    with wave.open(str(file_path), 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(frames):
            # Generate sine wave
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            # Convert to bytes
            data = struct.pack('<h', value)
            if channels == 2:
                data = data * 2  # Duplicate for stereo
            wav_file.writeframes(data)


def _create_realistic_with_soundfile(
    file_path: Path,
    format: str,
    duration: float,
    sample_rate: int,
    channels: int,
    frequency: float
) -> None:
    """Create realistic audio file using soundfile."""
    import numpy as np
    
    frames = int(duration * sample_rate)
    t = np.linspace(0, duration, frames, False)
    
    # Generate sine wave
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3  # 30% amplitude
    
    if channels == 2:
        # Create stereo by duplicating mono
        audio_data = np.column_stack((audio_data, audio_data))
    
    sf.write(str(file_path), audio_data, sample_rate, format=format.upper())


def create_corrupted_audio_file(file_path: Path, format: str = "mp3") -> Path:
    """
    Create a corrupted audio file for testing error handling.
    
    Args:
        file_path: Path where to create the file
        format: Audio format extension
        
    Returns:
        Path to the created corrupted file
    """
    file_path = file_path.with_suffix(f".{format}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write random bytes that don't form valid audio
    corrupted_data = b'\x00\xFF\x00\xFF' * 256  # Invalid audio pattern
    file_path.write_bytes(corrupted_data)
    
    return file_path


def create_empty_audio_file(file_path: Path, format: str = "mp3") -> Path:
    """
    Create an empty audio file for testing.
    
    Args:
        file_path: Path where to create the file
        format: Audio format extension
        
    Returns:
        Path to the created empty file
    """
    file_path = Path(file_path).with_suffix(f".{format}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"")
    return file_path


# =============================================================================
# PROVIDER TEST HELPERS
# =============================================================================


def create_mock_provider(
    name: str = "mock_provider",
    available: bool = True,
    voices: Optional[List[str]] = None
) -> MagicMock:
    """
    Create a mock TTS provider for testing.
    
    Args:
        name: Provider name
        available: Whether provider is available
        voices: List of voice names the provider supports
        
    Returns:
        Mock provider instance
    """
    mock_provider = MagicMock(spec=TTSProvider)
    mock_provider.name = name
    # Note: is_available is not part of the base TTSProvider interface
    
    # Mock synthesize method
    def mock_synthesize(text: str, output_path: Optional[str], **kwargs):
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"mock audio from " + name.encode())
    
    mock_provider.synthesize.side_effect = mock_synthesize
    
    # Mock get_info method
    mock_provider.get_info.return_value = {
        "name": name,
        "ShortName": name.lower().replace(" ", "_"),
        "description": f"Mock {name} provider",
        "sample_voices": voices or [f"{name}-voice1", f"{name}-voice2"],
        "output_formats": ["mp3", "wav"],
        "capabilities": ["stream", "save"]
    }
    
    return mock_provider


def assert_provider_called_with(
    provider: MagicMock,
    text: str,
    voice: Optional[str] = None,
    format: Optional[str] = None
) -> None:
    """
    Assert that a mock provider was called with expected parameters.
    
    Args:
        provider: Mock provider instance
        text: Expected text
        voice: Expected voice parameter
        format: Expected format parameter
    """
    provider.synthesize.assert_called()
    call_args = provider.synthesize.call_args
    
    # Check text
    assert call_args[0][0] == text, f"Expected text '{text}', got '{call_args[0][0]}'"
    
    # Check kwargs if provided
    if voice is not None:
        assert call_args[1].get("voice") == voice
    if format is not None:
        assert call_args[1].get("format") == format


# =============================================================================
# CLI INVOCATION UTILITIES
# =============================================================================


class CLITestHelper:
    """Helper class for testing CLI commands."""
    
    def __init__(self, runner: Optional[CliRunner] = None):
        """Initialize with optional CLI runner."""
        self.runner = runner or CliRunner()
        
    def invoke_save(
        self,
        text: str,
        output_path: Optional[str] = None,
        provider: Optional[str] = None,
        format: Optional[str] = None,
        voice: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> Tuple[Any, Path]:
        """
        Invoke the save command with common parameters.
        
        Returns:
            Tuple of (result, output_path)
        """
        from tts.cli import main
        
        # Build command
        cmd = ["save"]
        
        # Add provider shortcut if specified
        if provider and provider.startswith("@"):
            cmd.insert(1, provider)
            
        cmd.append(text)
        
        # Add output path
        if output_path:
            cmd.extend(["-o", str(output_path)])
        else:
            # Create temp file if not specified
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                output_path = tmp.name
                cmd.extend(["-o", output_path])
                
        # Add other options
        if format:
            cmd.extend(["--format", format])
        if voice:
            cmd.extend(["--voice", voice])
        if extra_args:
            cmd.extend(extra_args)
            
        result = self.runner.invoke(main, cmd)
        return result, Path(output_path)
        
    def invoke_speak(
        self,
        text: str,
        provider: Optional[str] = None,
        voice: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> Any:
        """Invoke the speak command with common parameters."""
        from tts.cli import main
        
        # Build command
        cmd = []
        
        # Add provider shortcut if specified
        if provider and provider.startswith("@"):
            cmd.append(provider)
            
        cmd.append(text)
        
        # Add options
        if voice:
            cmd.extend(["--voice", voice])
        if extra_args:
            cmd.extend(extra_args)
            
        return self.runner.invoke(main, cmd)
        
    def assert_success(self, result: Any, expected_output: Optional[str] = None) -> None:
        """Assert that a CLI command succeeded."""
        assert result.exit_code == 0, f"Command failed with: {result.output}"
        if expected_output:
            assert expected_output in result.output
            
    def assert_error(
        self, 
        result: Any, 
        expected_error: Optional[str] = None,
        exit_code: int = 1
    ) -> None:
        """Assert that a CLI command failed with expected error."""
        assert result.exit_code == exit_code, f"Expected exit code {exit_code}, got {result.exit_code}"
        if expected_error:
            assert expected_error in result.output


# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================


def create_test_config(
    config_dir: Path,
    default_provider: str = "edge_tts",
    default_voice: str = "en-US-AvaNeural",
    api_keys: Optional[Dict[str, str]] = None,
    **extra_config
) -> Path:
    """
    Create a test configuration file.
    
    Args:
        config_dir: Directory to create config in
        default_provider: Default provider to use
        default_voice: Default voice to use
        api_keys: Dictionary of API keys
        **extra_config: Additional config values
        
    Returns:
        Path to created config file
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    config_data = {
        "default_provider": default_provider,
        "default_voice": default_voice,
        "output_format": "mp3",
        "output_directory": str(config_dir.parent / "output"),
    }
    
    # Add API keys
    if api_keys:
        for key, value in api_keys.items():
            config_data[key] = value
    else:
        # Add default test API keys
        config_data.update({
            "openai_api_key": "sk-test1234567890abcdefghijklmnopqrstuvwxyz12345678",
            "elevenlabs_api_key": "abcdef0123456789abcdef0123456789",
            "google_cloud_api_key": "AIzaSyD-test1234567890abcdefghijklmnopq",
        })
        
    # Add any extra config
    config_data.update(extra_config)
    
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)
        
    return config_file


# =============================================================================
# COMMON FIXTURE FACTORIES
# =============================================================================


@pytest.fixture
def cli_helper():
    """Provide CLI test helper instance."""
    return CLITestHelper()


@pytest.fixture
def mock_provider_factory():
    """Factory fixture for creating mock providers."""
    def _create_provider(**kwargs):
        return create_mock_provider(**kwargs)
    return _create_provider


@pytest.fixture
def temp_audio_factory(tmp_path):
    """Factory fixture for creating temporary audio files."""
    def _create_audio(filename: str = "test.mp3", **kwargs):
        file_path = tmp_path / filename
        return create_mock_audio_file(file_path, **kwargs)
    return _create_audio


@pytest.fixture
def config_factory(tmp_path):
    """Factory fixture for creating test configurations."""
    def _create_config(**kwargs):
        config_dir = tmp_path / "config"
        return create_test_config(config_dir, **kwargs)
    return _create_config


# =============================================================================
# PROVIDER SHORTCUT TEST DATA
# =============================================================================

PROVIDER_SHORTCUTS_TEST_DATA = [
    ("@edge", "edge_tts"),
    ("@openai", "openai_tts"),
    ("@elevenlabs", "elevenlabs"),
    ("@google", "google_tts"),
    ("@chatterbox", "chatterbox"),
]


def parametrize_provider_shortcuts():
    """Decorator for parameterizing tests with provider shortcuts."""
    return pytest.mark.parametrize("shortcut,provider_name", PROVIDER_SHORTCUTS_TEST_DATA)


# =============================================================================
# MOCK NETWORK RESPONSES
# =============================================================================


def create_mock_api_response(
    provider: str,
    endpoint: str,
    success: bool = True,
    data: Optional[Dict[str, Any]] = None
) -> MagicMock:
    """
    Create a mock API response for different providers.
    
    Args:
        provider: Provider name (openai, elevenlabs, google)
        endpoint: API endpoint being mocked
        success: Whether response should indicate success
        data: Response data
        
    Returns:
        Mock response object
    """
    mock_response = MagicMock()
    mock_response.status_code = 200 if success else 400
    
    if provider == "elevenlabs":
        if endpoint == "voices":
            mock_response.json.return_value = data or {
                "voices": [
                    {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"},
                    {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi"},
                ]
            }
        elif endpoint == "text-to-speech":
            mock_response.content = b"mock elevenlabs audio"
            mock_response.iter_content = lambda chunk_size: [b"chunk1", b"chunk2"]
            
    elif provider == "openai":
        mock_response.content = b"mock openai audio"
        
    elif provider == "google":
        mock_response.json.return_value = data or {
            "audioContent": "bW9jayBnb29nbGUgYXVkaW8="
        }
        
    return mock_response


# =============================================================================
# TEST ENVIRONMENT VALIDATION
# =============================================================================


def validate_test_environment(env_dict: Dict[str, Any]) -> None:
    """
    Validate that a test environment is properly configured.
    
    Args:
        env_dict: Environment dictionary from fixture
        
    Raises:
        AssertionError if environment is invalid
    """
    # Check for required keys
    required_keys = ["test_mode", "disable_playback", "has_api_keys"]
    for key in required_keys:
        assert key in env_dict, f"Missing required environment key: {key}"
        
    # Validate values
    assert env_dict["test_mode"] is True
    assert env_dict["disable_playback"] is True
    assert env_dict["has_api_keys"] is True