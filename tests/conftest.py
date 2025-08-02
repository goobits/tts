"""
Pytest configuration and fixtures for TTS CLI tests.

This module provides comprehensive mocking infrastructure to isolate tests
from external dependencies including:
- API calls to TTS providers
- Audio environment (PyAudio devices)
- File system operations
- Configuration directory
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


# ==============================================================================
# MOCK PROVIDERS
# ==============================================================================


class MockTTSProvider(TTSProvider):
    """Base mock TTS provider for testing."""

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
            "description": f"Mock {self.name} provider for testing",
            "options": {"voice": "Mock voice selection"},
            "output_formats": ["mp3", "wav"],
            "sample_voices": ["mock-voice-1", "mock-voice-2"],
            "capabilities": ["stream", "save"],
        }


class MockEdgeTTSProvider(MockTTSProvider):
    """Mock Edge TTS provider."""

    def __init__(self):
        super().__init__("edge_tts")

    def get_info(self) -> Optional[ProviderInfo]:
        info = super().get_info()
        info.update({
            "sample_voices": [
                "en-US-AvaNeural",
                "en-GB-SoniaNeural",
                "en-IE-EmilyNeural",
            ],
            "description": "Microsoft Edge TTS (Free)",
            "api_status": "✅ Ready (no API key required)",
        })
        return info


class MockOpenAIProvider(MockTTSProvider):
    """Mock OpenAI TTS provider."""

    def __init__(self):
        super().__init__("openai_tts")

    def get_info(self) -> Optional[ProviderInfo]:
        info = super().get_info()
        info.update({
            "sample_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "description": "OpenAI Text-to-Speech",
            "api_status": "✅ API key configured",
            "model": "tts-1",
        })
        return info


class MockElevenLabsProvider(MockTTSProvider):
    """Mock ElevenLabs provider."""

    def __init__(self):
        super().__init__("elevenlabs")

    def get_info(self) -> Optional[ProviderInfo]:
        info = super().get_info()
        info.update({
            "sample_voices": ["Rachel", "Domi", "Bella", "Antoni", "Elli"],
            "description": "ElevenLabs Text-to-Speech",
            "api_status": "✅ API key configured",
            "pricing": "Paid API with free tier",
        })
        return info


class MockGoogleTTSProvider(MockTTSProvider):
    """Mock Google Cloud TTS provider."""

    def __init__(self):
        super().__init__("google_tts")

    def get_info(self) -> Optional[ProviderInfo]:
        info = super().get_info()
        info.update({
            "sample_voices": [
                "en-US-Wavenet-A",
                "en-US-Wavenet-B",
                "en-US-Neural2-A",
            ],
            "description": "Google Cloud Text-to-Speech",
            "api_status": "✅ API key configured",
            "auth_method": "API Key",
        })
        return info


class MockChatterboxProvider(MockTTSProvider):
    """Mock Chatterbox provider."""

    def __init__(self):
        super().__init__("chatterbox")

    def get_info(self) -> Optional[ProviderInfo]:
        info = super().get_info()
        info.update({
            "sample_voices": ["clone1", "clone2"],
            "description": "Local voice cloning with Chatterbox",
            "api_status": "✅ Ready (local model)",
            "features": {"gpu_available": True, "voice_cloning": True},
        })
        return info


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
# PROVIDER FIXTURES
# ==============================================================================


@pytest.fixture
def mock_edge_tts_provider():
    """Mock Edge TTS provider instance."""
    return MockEdgeTTSProvider()


@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI provider instance."""
    return MockOpenAIProvider()


@pytest.fixture
def mock_elevenlabs_provider():
    """Mock ElevenLabs provider instance."""
    return MockElevenLabsProvider()


@pytest.fixture
def mock_google_provider():
    """Mock Google TTS provider instance."""
    return MockGoogleTTSProvider()


@pytest.fixture
def mock_chatterbox_provider():
    """Mock Chatterbox provider instance."""
    return MockChatterboxProvider()


@pytest.fixture
def mock_all_providers(
    mock_edge_tts_provider,
    mock_openai_provider,
    mock_elevenlabs_provider,
    mock_google_provider,
    mock_chatterbox_provider,
):
    """Dictionary of all mock providers."""
    return {
        "edge_tts": mock_edge_tts_provider,
        "openai_tts": mock_openai_provider,
        "elevenlabs": mock_elevenlabs_provider,
        "google_tts": mock_google_provider,
        "chatterbox": mock_chatterbox_provider,
    }


@pytest.fixture
def mock_provider_imports(monkeypatch, mock_all_providers):
    """Mock provider imports to avoid importing actual provider modules."""

    # Create mock modules for each provider
    mock_modules = {}
    for provider_name in mock_all_providers:
        mock_module = MagicMock()
        provider_class_name = {
            "edge_tts": "EdgeTTSProvider",
            "openai_tts": "OpenAITTSProvider",
            "elevenlabs": "ElevenLabsProvider",
            "google_tts": "GoogleTTSProvider",
            "chatterbox": "ChatterboxProvider",
        }[provider_name]
        
        # Add the mock provider class to the module
        provider_class = type(mock_all_providers[provider_name])
        setattr(mock_module, provider_class_name, provider_class)
        
        # Make sure dir() returns the class name (capture by value not reference)
        mock_module.__dir__ = lambda class_name=provider_class_name: [class_name]
        
        mock_modules[f"tts.providers.{provider_name}"] = mock_module

    # Mock importlib.import_module to return our mock modules
    original_import = __import__
    
    def mock_import_module(name, *args, **kwargs):
        if name in mock_modules:
            return mock_modules[name]
        # For relative imports in providers
        if name.startswith("tts.providers."):
            provider = name.split(".")[-1]
            if f"tts.providers.{provider}" in mock_modules:
                return mock_modules[f"tts.providers.{provider}"]
        return original_import(name, *args, **kwargs)
    
    import importlib
    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    return mock_all_providers


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
# NETWORK FIXTURES
# ==============================================================================


@pytest.fixture
def mock_network_requests(monkeypatch):
    """Mock network requests for API calls."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.content = b"mock audio content"
    mock_response.headers = {"content-type": "audio/mpeg"}
    mock_response.iter_content = lambda chunk_size: [b"chunk1", b"chunk2", b"chunk3"]

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response

    monkeypatch.setattr("requests.Session", lambda: mock_session)
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock_response)
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: mock_response)

    return mock_session


# ==============================================================================
# ASYNC FIXTURES
# ==============================================================================


@pytest.fixture
def mock_edge_tts_async(monkeypatch):
    """Mock edge-tts async operations."""

    class MockCommunicate:
        def __init__(self, text, voice, **kwargs):
            self.text = text
            self.voice = voice

        async def save(self, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"mock edge-tts audio")

        def stream(self):
            """Async generator for streaming."""

            async def _stream():
                yield {"type": "audio", "data": b"chunk1"}
                yield {"type": "audio", "data": b"chunk2"}
                yield {"type": "audio", "data": b"chunk3"}

            return _stream()

    mock_edge_module = MagicMock()
    mock_edge_module.Communicate = MockCommunicate
    mock_edge_module.list_voices = AsyncMock(
        return_value=[
            {"Name": "en-US-AvaNeural", "Gender": "Female"},
            {"Name": "en-GB-SoniaNeural", "Gender": "Female"},
        ]
    )

    monkeypatch.setattr("edge_tts.Communicate", MockCommunicate)
    monkeypatch.setattr("edge_tts.list_voices", mock_edge_module.list_voices)

    return mock_edge_module


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
def mock_cli_environment(
    mock_config,
    mock_provider_imports,
    mock_audio_environment,
    mock_audio_playback,
    mock_network_requests,
    mock_edge_tts_async,
    isolated_config_dir,
):
    """Complete mock environment for CLI testing."""
    # This fixture combines all necessary mocks for CLI tests
    return {
        "config": mock_config,
        "providers": mock_provider_imports,
        "audio_env": mock_audio_environment,
        "audio_playback": mock_audio_playback,
        "network": mock_network_requests,
        "edge_tts": mock_edge_tts_async,
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