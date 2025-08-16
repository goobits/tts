"""Integration tests for OpenAI TTS provider with real API calls."""

import os
import time
from unittest.mock import patch

import pytest

from src.tts.exceptions import AuthenticationError, NetworkError, ProviderError
from src.tts.providers.openai_tts import OpenAITTSProvider

from .base_provider_test import BaseProviderIntegrationTest


@pytest.mark.integration
class TestOpenAIIntegration(BaseProviderIntegrationTest):
    """Integration tests for OpenAI TTS provider."""

    def get_provider_class(self):
        return OpenAITTSProvider

    def get_test_voice(self):
        return "alloy"  # Default OpenAI voice

    def get_api_key_env_var(self):
        return "OPENAI_API_KEY"

    def get_provider_name(self):
        return "OpenAI"

    @pytest.fixture(autouse=True)
    def check_openai_available(self):
        """Check if OpenAI module is available."""
        try:
            import openai
        except ImportError:
            pytest.skip("OpenAI library not installed")

    def test_all_voices(self, provider, temp_audio_file):
        """Test synthesis with all available OpenAI voices."""
        voices = ["alloy", "echo", "fable", "nova", "onyx", "shimmer"]

        for voice in voices:
            output_file = f"{temp_audio_file}_{voice}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing {voice} voice.",
                    output_path=output_file,
                    voice=voice
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

            # Small delay to avoid rate limiting
            time.sleep(0.5)

    def test_different_models(self, provider, temp_audio_file):
        """Test both tts-1 and tts-1-hd models."""
        models = ["tts-1", "tts-1-hd"]

        for model in models:
            output_file = f"{temp_audio_file}_{model}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing {model} model quality.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    model=model
                )
                self.validate_audio_file(output_file)

                # HD model should produce larger files
                if model == "tts-1-hd":
                    base_size = os.path.getsize(f"{temp_audio_file}_tts-1.mp3")
                    hd_size = os.path.getsize(output_file)
                    # HD is typically 20-50% larger
                    assert hd_size >= base_size, "HD model should produce larger files"
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def test_speed_parameter(self, provider, temp_audio_file):
        """Test speech speed adjustment."""
        speeds = [0.5, 1.0, 2.0]  # Slow, normal, fast

        for speed in speeds:
            output_file = f"{temp_audio_file}_speed{speed}.mp3"
            try:
                provider.synthesize(
                    text="Testing speech speed adjustment.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    speed=speed
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def test_output_formats(self, provider):
        """Test different output formats."""
        formats = ["mp3", "opus", "aac", "flac"]

        for fmt in formats:
            temp_file = f"/tmp/openai_test.{fmt}"
            try:
                provider.synthesize(
                    text="Testing output format.",
                    output_path=temp_file,
                    voice=self.get_test_voice(),
                    response_format=fmt
                )
                self.validate_audio_file(temp_file)
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_streaming_mode(self, provider):
        """Test streaming functionality (if supported)."""
        # OpenAI supports streaming - we'll test by not providing output_path
        # and using stream=True
        with patch('src.tts.providers.openai_tts.stream_via_tempfile') as mock_stream:
            provider.synthesize(
                text="Testing streaming mode.",
                output_path=None,
                voice=self.get_test_voice(),
                stream=True
            )
            mock_stream.assert_called_once()

    def test_invalid_api_key(self):
        """Test authentication error with invalid API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "invalid_key_12345"}):
            provider = OpenAITTSProvider()
            with pytest.raises((AuthenticationError, ProviderError)):
                provider.synthesize(
                    text="This should fail.",
                    output_path="/tmp/fail.mp3",
                    voice=self.get_test_voice()
                )

    def test_network_error_handling(self, provider, temp_audio_file):
        """Test network error handling."""
        # Mock the OpenAI client to simulate network error
        with patch.object(provider, '_get_client') as mock_client:
            mock_client.side_effect = NetworkError("Connection failed")

            with pytest.raises(NetworkError):
                provider.synthesize(
                    text="This should fail.",
                    output_path=temp_audio_file,
                    voice=self.get_test_voice()
                )

    def test_long_text_chunking(self, provider, temp_audio_file):
        """Test handling of very long text (over 4096 chars limit)."""
        # OpenAI has a 4096 character limit
        long_text = "This is a test sentence. " * 300  # ~7500 chars

        provider.synthesize(
            text=long_text,
            output_path=temp_audio_file,
            voice=self.get_test_voice()
        )
        self.validate_audio_file(temp_audio_file)

    def test_ssml_stripping(self, provider, temp_audio_file):
        """Test that SSML tags are properly stripped."""
        ssml_text = '<speak>Hello <break time="1s"/> world!</speak>'

        provider.synthesize(
            text=ssml_text,
            output_path=temp_audio_file,
            voice=self.get_test_voice()
        )
        self.validate_audio_file(temp_audio_file)

    @pytest.mark.slow
    def test_rate_limiting_handling(self, provider):
        """Test rate limiting with rapid requests."""
        # OpenAI has rate limits - test graceful handling
        for i in range(5):
            temp_file = f"/tmp/rate_test_{i}.mp3"
            try:
                provider.synthesize(
                    text=f"Rate limit test {i}",
                    output_path=temp_file,
                    voice=self.get_test_voice()
                )
                self.validate_audio_file(temp_file)
            except ProviderError as e:
                if "rate" in str(e).lower():
                    # Expected rate limit error
                    assert i > 2, "Rate limit hit too early"
                    break
                raise
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
