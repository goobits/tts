"""Base class for provider integration tests with common functionality."""

import os
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pytest

from matilda_voice.base import TTSProvider
from matilda_voice.exceptions import (
    ProviderError,
    VoiceNotFoundError,
)


class BaseProviderIntegrationTest(ABC):
    """Base class for provider integration tests.

    Provides common test utilities and patterns for testing TTS providers
    with real API calls. Subclasses should implement provider-specific
    setup and test cases.
    """

    # Test configuration
    TEST_TEXT_SHORT = "Hello, this is a test."
    TEST_TEXT_MEDIUM = (
        "The quick brown fox jumps over the lazy dog. " "This pangram contains all letters of the alphabet."
    )
    TEST_TEXT_LONG = TEST_TEXT_MEDIUM * 5  # ~500 chars

    # Audio validation thresholds
    MIN_AUDIO_DURATION = 0.5  # seconds
    MAX_AUDIO_DURATION = 60.0  # seconds
    MIN_FILE_SIZE = 1024  # bytes (1KB)

    @abstractmethod
    def get_provider_class(self) -> type[TTSProvider]:
        """Return the provider class to test."""
        pass

    @abstractmethod
    def get_test_voice(self) -> str:
        """Return a valid voice name for testing."""
        pass

    @abstractmethod
    def get_api_key_env_var(self) -> Optional[str]:
        """Return the environment variable name for API key."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name for skip messages."""
        pass

    def get_additional_config(self) -> Dict[str, Any]:
        """Return any additional provider-specific configuration."""
        return {}

    @pytest.fixture
    def provider(self):
        """Create provider instance with test configuration."""
        provider_class = self.get_provider_class()
        config = self.get_additional_config()

        # Skip real API tests in CI environment unless explicitly enabled
        if (os.getenv("CI") or os.getenv("GITHUB_ACTIONS")) and not os.getenv("ENABLE_REAL_API_TESTS"):
            pytest.skip("Skipping real API test in CI environment")

        # Add API key if needed
        api_key_var = self.get_api_key_env_var()
        if api_key_var:
            api_key = os.getenv(api_key_var)
            if not api_key:
                pytest.skip(f"{self.get_provider_name()} API key not found in {api_key_var}")

            # Map to provider-specific config key
            if "openai" in self.get_provider_name().lower():
                config["api_key"] = api_key
            elif "google" in self.get_provider_name().lower():
                config["api_key"] = api_key
            elif "elevenlabs" in self.get_provider_name().lower():
                config["api_key"] = api_key

        return provider_class(**config)

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary file for audio output."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def validate_audio_file(self, file_path: str, min_duration: float = None):
        """Validate that an audio file was created correctly."""
        # Check file exists and has content
        assert os.path.exists(file_path), f"Audio file not created: {file_path}"
        file_size = os.path.getsize(file_path)
        assert file_size > self.MIN_FILE_SIZE, f"Audio file too small: {file_size} bytes"

        # Try to validate it's actual audio (basic check)
        # For MP3s, check magic bytes
        with open(file_path, "rb") as f:
            header = f.read(3)
            if file_path.endswith(".mp3"):
                # MP3 files start with ID3 or 0xFFFB
                assert header[:3] == b"ID3" or header[:2] == b"\xff\xfb", "Invalid MP3 header"
            elif file_path.endswith(".wav"):
                # WAV files start with RIFF
                assert header[:3] == b"RIF", "Invalid WAV header"

    def test_basic_synthesis(self, provider, temp_audio_file):
        """Test basic text-to-speech synthesis."""
        provider.synthesize(text=self.TEST_TEXT_SHORT, output_path=temp_audio_file, voice=self.get_test_voice())
        self.validate_audio_file(temp_audio_file)

    def test_synthesis_without_voice(self, provider, temp_audio_file):
        """Test synthesis with default voice."""
        provider.synthesize(text=self.TEST_TEXT_SHORT, output_path=temp_audio_file)
        self.validate_audio_file(temp_audio_file)

    def test_long_text_synthesis(self, provider, temp_audio_file):
        """Test synthesis with longer text."""
        provider.synthesize(text=self.TEST_TEXT_LONG, output_path=temp_audio_file, voice=self.get_test_voice())
        self.validate_audio_file(temp_audio_file)

    def test_invalid_voice_error(self, provider, temp_audio_file):
        """Test that invalid voice raises appropriate error."""
        with pytest.raises((VoiceNotFoundError, ProviderError)):
            provider.synthesize(
                text=self.TEST_TEXT_SHORT, output_path=temp_audio_file, voice="invalid_voice_that_does_not_exist_12345"
            )

    def test_empty_text_handling(self, provider, temp_audio_file):
        """Test handling of empty text input."""
        # Most providers should handle this gracefully
        with pytest.raises((ValueError, ProviderError)):
            provider.synthesize(text="", output_path=temp_audio_file, voice=self.get_test_voice())

    def test_provider_info(self, provider):
        """Test that provider returns valid info."""
        info = provider.get_info()
        if info is not None:
            assert hasattr(info, "name")
            assert hasattr(info, "voices")
            assert len(info.voices) > 0, "Provider should have at least one voice"

    def test_special_characters(self, provider, temp_audio_file):
        """Test synthesis with special characters and punctuation."""
        test_text = "Hello! How are you? I'm testing @ 100% capacity & it's great."
        provider.synthesize(text=test_text, output_path=temp_audio_file, voice=self.get_test_voice())
        self.validate_audio_file(temp_audio_file)

    @pytest.mark.slow  # noqa: B027
    def test_rate_limiting_handling(self, provider):
        """Test multiple rapid requests to check rate limiting."""
        # This test is marked slow and can be skipped in quick test runs
        # Subclasses can override to test provider-specific rate limits
        pass
