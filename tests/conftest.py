"""
Pytest configuration and fixtures for TTS CLI tests.

This module provides selective mocking infrastructure to isolate tests
from external dependencies while preserving provider business logic:
- Network-only mocking of HTTP requests and API calls
- Audio environment mocking (PyAudio devices, ffmpeg)
- File system operations
- Configuration directory

Design: Uses real provider classes with mocked external dependencies,
preserving provider logic while avoiding network/hardware dependencies.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from tts.base import TTSProvider
from tts.types import Config, ProviderInfo, VoiceInfo

# Import network-only mocking infrastructure (selective imports)
try:
    from .mocking import (
        mock_http_requests,
        comprehensive_audio_mocks,
        network_mock_registry,
    )
    # Don't import API-specific mocks yet - let's use a simpler approach
    MOCKING_AVAILABLE = True
except ImportError:
    # Fallback if mocking module not available
    MOCKING_AVAILABLE = False


# ==============================================================================
# AUDIO ENVIRONMENT MOCKS
# ==============================================================================


@pytest.fixture
def mock_audio_environment(monkeypatch):
    """Mock audio environment to avoid PyAudio initialization."""

    # Mock check_audio_environment function
    def mock_check_audio_env() -> Dict[str, Any]:
        return {
            "available": True,
            "reason": "Mock audio environment",
            "pulse_available": True,
            "alsa_available": True,
        }

    # Apply mock
    monkeypatch.setattr("tts.audio_utils.check_audio_environment", mock_check_audio_env)

    return mock_check_audio_env


@pytest.fixture
def mock_audio_playback(monkeypatch):
    """Mock audio playback functions."""

    # Mock subprocess calls for ffplay
    mock_popen = MagicMock()
    mock_popen.wait.return_value = 0
    mock_popen.returncode = 0
    mock_popen.poll.return_value = 0

    def mock_subprocess_popen(*args, **kwargs):
        # Track the command being run
        if args and args[0] and "ffplay" in args[0][0]:
            mock_popen.command = args[0]
        return mock_popen

    monkeypatch.setattr("subprocess.Popen", mock_subprocess_popen)
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: MagicMock(returncode=0))
    monkeypatch.setattr("shutil.which", lambda x: f"/usr/bin/{x}")

    return mock_popen


@pytest.fixture
def mock_audio_conversion(monkeypatch):
    """Mock audio conversion functions."""
    
    def mock_convert_with_cleanup(input_path: str, output_path: str, output_format: str) -> None:
        """Mock audio conversion that copies the input file to output."""
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the input file to output (simulating conversion)
        if input_file.exists():
            import shutil
            shutil.copy2(input_path, output_path)
        else:
            # Create a mock file if input doesn't exist
            with open(output_path, "wb") as f:
                f.write(b"mock converted audio data")
    
    def mock_convert_audio(input_path: str, output_path: str, target_format: str = "mp3") -> None:
        """Mock convert_audio function."""
        mock_convert_with_cleanup(input_path, output_path, target_format)
    
    # Mock both conversion functions
    monkeypatch.setattr("tts.audio_utils.convert_with_cleanup", mock_convert_with_cleanup)
    monkeypatch.setattr("tts.audio_utils.convert_audio", mock_convert_audio)
    
    return mock_convert_with_cleanup


# ==============================================================================
# CONFIGURATION FIXTURES
# ==============================================================================


@pytest.fixture
def isolated_config_dir(tmp_path, monkeypatch):
    """Create an isolated configuration directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create a test config file
    config_file = config_dir / "config.json"
    config_data = {
        "default_voice": "en-US-AvaNeural",
        "default_provider": "edge_tts",
        "output_format": "mp3",
        "output_directory": str(tmp_path / "output"),
        "openai_api_key": "test-openai-key",
        "elevenlabs_api_key": "test-elevenlabs-key",
        "google_cloud_api_key": "test-google-key",
    }

    import json

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Mock XDG config directory
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    
    # Mock the get_config_path function to return our test config file
    monkeypatch.setattr("tts.config.get_config_path", lambda: config_file)

    # Create output directory
    (tmp_path / "output").mkdir(exist_ok=True)

    return config_dir


@pytest.fixture
def mock_config(isolated_config_dir, monkeypatch):
    """Mock configuration with test values."""

    test_config: Config = {
        "default_voice": "en-US-AvaNeural",
        "default_provider": "edge_tts",
        "output_format": "mp3",
        "output_directory": str(isolated_config_dir.parent / "output"),
        "openai_api_key": "test-openai-key",
        "elevenlabs_api_key": "test-elevenlabs-key",
        "google_cloud_api_key": "test-google-key",
        "auto_provider_selection": True,
        "voice_loading_enabled": True,
        "http_streaming_chunk_size": 1024,
        "streaming_progress_interval": 100,
        "ffmpeg_conversion_timeout": 300,
        "ffplay_timeout": 120,
        "thread_pool_max_workers": 4,
        "browser_page_size": 20,
        "browser_preview_text": "Hello, this is a test.",
    }

    def mock_load_config():
        return test_config.copy()

    def mock_get_config_value(key: str, default: Any = None) -> Any:
        return test_config.get(key, default)

    def mock_set_setting(key: str, value: Any) -> bool:
        test_config[key] = value
        return True

    def mock_get_setting(key: str, default: Any = None) -> Any:
        return test_config.get(key, default)

    monkeypatch.setattr("tts.config.load_config", mock_load_config)
    monkeypatch.setattr("tts.config.get_config_value", mock_get_config_value)
    monkeypatch.setattr("tts.config.set_setting", mock_set_setting)
    monkeypatch.setattr("tts.config.get_setting", mock_get_setting)

    return test_config


# ==============================================================================
# SELECTIVE MOCKING FIXTURES
# ==============================================================================


@pytest.fixture
def mock_selective_imports():
    """Mock only problematic imports while preserving provider loading logic."""
    
    # Mock only the heavy external dependencies that cause import issues
    # while keeping the actual provider classes and logic intact
    
    mocks = {}
    
    # Mock edge-tts async operations that can cause issues in test environment
    try:
        mock_edge_module = MagicMock()
        mock_edge_module.Communicate = MagicMock()
        mock_edge_module.list_voices = AsyncMock(return_value=[
            {"Name": "en-US-AvaNeural", "ShortName": "en-US-AvaNeural", "Gender": "Female"},
            {"Name": "en-GB-SoniaNeural", "ShortName": "en-GB-SoniaNeural", "Gender": "Female"},
        ])
        mocks['edge_tts'] = mock_edge_module
    except ImportError:
        pass
    
    # Don't mock the actual provider modules - let them load normally
    # The network mocking will handle external calls
    
    yield mocks


# ==============================================================================
# LEGACY MOCK PROVIDERS (for backward compatibility only)
# ==============================================================================
# 
# NOTE: These are kept for any remaining tests that still use them directly.
# New tests should use the selective mocking approach that preserves real
# provider logic while mocking only external dependencies.


class MockTTSProvider(TTSProvider):
    """Base mock TTS provider for testing (legacy - use selective mocking instead)."""

    def __init__(self, name: str = "mock_provider"):
        self.name = name
        self.synthesize_called = False
        self.last_text = None
        self.last_output_path = None
        self.last_kwargs = {}

    def synthesize(self, text: str, output_path: Optional[str], **kwargs: Any) -> None:
        """Mock synthesize method that tracks calls."""
        self.synthesize_called = True
        self.last_text = text
        self.last_output_path = output_path
        self.last_kwargs = kwargs

        # If output_path is provided, create a dummy file
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"mock audio data")

    def get_info(self) -> Optional[ProviderInfo]:
        """Return mock provider info."""
        return {
            "name": self.name,
            "ShortName": self.name.lower().replace(" ", "_"),
            "description": f"Mock {self.name} provider for testing",
            "options": {"voice": "Mock voice selection"},
            "output_formats": ["mp3", "wav"],
            "sample_voices": ["mock-voice-1", "mock-voice-2"],
            "capabilities": ["stream", "save"],
        }


# Legacy fixtures removed - use selective mocking approach instead
# which preserves real provider logic while mocking external dependencies


# ==============================================================================
# FILE SYSTEM FIXTURES
# ==============================================================================


@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary audio file for testing."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"mock audio data")
    return audio_file


@pytest.fixture
def temp_voice_file(tmp_path):
    """Create a temporary voice file for testing."""
    voice_file = tmp_path / "test_voice.wav"
    voice_file.write_bytes(b"mock voice data")
    return voice_file


@pytest.fixture
def mock_file_operations(monkeypatch):
    """Mock file operations for safe testing."""
    original_open = open
    original_exists = os.path.exists

    def mock_open(path, mode="r", *args, **kwargs):
        # Allow opening files in temp directories
        if str(path).startswith("/tmp") or "test" in str(path):
            return original_open(path, mode, *args, **kwargs)
        # For other paths, return a mock file
        if "b" in mode:
            from io import BytesIO

            return BytesIO(b"mock file content")
        else:
            from io import StringIO

            return StringIO("mock file content")

    def mock_exists(path):
        # Always return True for config files
        if "config" in str(path):
            return True
        return original_exists(path)

    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("os.path.exists", mock_exists)


# ==============================================================================
# VOICE MANAGER FIXTURES
# ==============================================================================


@pytest.fixture
def mock_voice_manager(monkeypatch, tmp_path):
    """Mock voice manager for testing."""

    class MockVoiceManager:
        def __init__(self):
            self.voice_dir = tmp_path / "voices"
            self.voice_dir.mkdir(exist_ok=True)
            self.loaded_voices = {}

        def load_voice(self, voice_path: str, voice_name: Optional[str] = None) -> str:
            name = voice_name or Path(voice_path).stem
            self.loaded_voices[name] = voice_path
            return name

        def get_voice(self, voice_name: str) -> Optional[str]:
            return self.loaded_voices.get(voice_name)

        def list_voices(self) -> List[str]:
            return list(self.loaded_voices.keys())

        def get_voice_dir(self) -> Path:
            return self.voice_dir

    mock_manager = MockVoiceManager()
    monkeypatch.setattr("tts.voice_manager.VoiceManager", lambda: mock_manager)
    return mock_manager


# ==============================================================================
# CLI FIXTURES
# ==============================================================================


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture
def mock_minimal_network_calls(monkeypatch):
    """Minimal network mocking - just mock requests to avoid actual network calls."""
    
    def mock_request_handler(method, url, *args, **kwargs):
        """Handle different API endpoints with realistic responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        
        # ElevenLabs API endpoints
        if "api.elevenlabs.io" in str(url):
            if "/voices" in str(url):
                mock_response.json.return_value = {
                    "voices": [
                        {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"},
                        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi"}
                    ]
                }
            elif "/text-to-speech" in str(url):
                mock_response.content = b"mock audio content"
                mock_response.headers = {"content-type": "audio/mpeg"}
                mock_response.iter_content = lambda chunk_size: [b"chunk1", b"chunk2"]
            else:
                mock_response.json.return_value = {"status": "ok"}
        
        # OpenAI API endpoints
        elif "api.openai.com" in str(url):
            mock_response.json.return_value = {"status": "ok"}
            
        # Google Cloud TTS endpoints
        elif "texttospeech.googleapis.com" in str(url):
            mock_response.json.return_value = {"audioContent": "bW9jayBhdWRpbw=="}
            
        # Default response
        else:
            mock_response.content = b"mock audio content"
            mock_response.headers = {"content-type": "audio/mpeg"}
            mock_response.json.return_value = {"status": "ok"}
        
        return mock_response
    
    # Mock requests at the module level
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock_request_handler("GET", *args, **kwargs))
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: mock_request_handler("POST", *args, **kwargs))
    
    return mock_request_handler


@pytest.fixture  
def mock_edge_tts_simple(monkeypatch):
    """Simple edge-tts mocking that handles basic synthesis."""
    
    class MockCommunicate:
        def __init__(self, text, voice, **kwargs):
            self.text = text
            self.voice = voice

        async def save(self, output_path):
            """Mock save method that creates a real audio file."""
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Create a mock audio file with some realistic content
            with open(output_path, "wb") as f:
                f.write(b"mock edge-tts audio data with sufficient content for testing")

        def stream(self):
            """Mock async generator for streaming."""
            async def _stream():
                yield {"type": "audio", "data": b"chunk1"}
                yield {"type": "audio", "data": b"chunk2"}
                yield {"type": "audio", "data": b"chunk3"}
            return _stream()

    # Create a comprehensive edge_tts mock module
    mock_edge_module = MagicMock()
    mock_edge_module.Communicate = MockCommunicate
    mock_edge_module.list_voices = AsyncMock(return_value=[
        {"Name": "en-US-AvaNeural", "ShortName": "en-US-AvaNeural", "Gender": "Female"},
        {"Name": "en-GB-SoniaNeural", "ShortName": "en-GB-SoniaNeural", "Gender": "Female"},
    ])
    
    # Mock the import in sys.modules so any import will get our mock
    import sys
    sys.modules['edge_tts'] = mock_edge_module
    
    # Also set up monkeypatch mocking in case edge_tts is already imported
    try:
        import edge_tts
        monkeypatch.setattr("edge_tts.Communicate", MockCommunicate)
        # Mock list_voices as well
        async def mock_list_voices():
            return [
                {"Name": "en-US-AvaNeural", "ShortName": "en-US-AvaNeural", "Gender": "Female"},
                {"Name": "en-GB-SoniaNeural", "ShortName": "en-GB-SoniaNeural", "Gender": "Female"},
            ]
        monkeypatch.setattr("edge_tts.list_voices", mock_list_voices)
    except ImportError:
        pass
    
    return MockCommunicate


@pytest.fixture
def mock_cli_environment(
    mock_config,
    mock_selective_imports,
    mock_audio_environment,
    mock_audio_playback,
    mock_audio_conversion,
    mock_minimal_network_calls,
    mock_edge_tts_simple,
    isolated_config_dir,
):
    """Complete selective mock environment for CLI testing."""
    # This fixture combines minimal mocks that preserve provider logic
    # while mocking only essential external dependencies
    return {
        "config": mock_config,
        "selective_imports": mock_selective_imports,
        "audio_env": mock_audio_environment,
        "audio_playback": mock_audio_playback,
        "audio_conversion": mock_audio_conversion,
        "minimal_network": mock_minimal_network_calls,
        "edge_tts": mock_edge_tts_simple,
        "config_dir": isolated_config_dir,
    }


# ==============================================================================
# UTILITY FIXTURES
# ==============================================================================


@pytest.fixture
def capture_logs():
    """Capture log output for testing."""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    yield log_capture

    # Clean up
    root_logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically clean up temporary files after each test."""
    yield
    # Clean up any temp files created during tests
    temp_dir = tempfile.gettempdir()
    for file in Path(temp_dir).glob("tts_test_*"):
        try:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
        except Exception:
            pass