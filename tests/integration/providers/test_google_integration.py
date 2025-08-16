"""Integration tests for Google Cloud TTS provider with real API calls."""

import os
import time
from unittest.mock import patch

import pytest

from src.tts.exceptions import AuthenticationError, NetworkError, ProviderError, QuotaError
from src.tts.providers.google_tts import GoogleTTSProvider

from .base_provider_test import BaseProviderIntegrationTest


@pytest.mark.integration
class TestGoogleTTSIntegration(BaseProviderIntegrationTest):
    """Integration tests for Google Cloud TTS provider."""

    def get_provider_class(self):
        return GoogleTTSProvider

    def get_test_voice(self):
        return "en-US-Neural2-A"  # Standard US English female neural voice

    def get_api_key_env_var(self):
        return "GOOGLE_TTS_API_KEY"

    def get_provider_name(self):
        return "Google Cloud TTS"

    def get_additional_config(self):
        """Add service account path if available."""
        service_account = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if service_account:
            return {"service_account_path": service_account}
        return {}

    @pytest.fixture(autouse=True)
    def check_google_available(self):
        """Check if Google auth is available (API key or service account)."""
        api_key = os.getenv("GOOGLE_TTS_API_KEY")
        service_account = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not api_key and not service_account:
            pytest.skip("Google Cloud TTS credentials not found (need GOOGLE_TTS_API_KEY or GOOGLE_APPLICATION_CREDENTIALS)")

    def test_neural_voices(self, provider, temp_audio_file):
        """Test synthesis with different Neural2 voices."""
        voices = [
            "en-US-Neural2-A",  # Female
            "en-US-Neural2-D",  # Male
            "en-GB-Neural2-A",  # UK Female
            "en-AU-Neural2-A",  # Australian Female
        ]

        for voice in voices:
            output_file = f"{temp_audio_file}_{voice.replace('-', '_')}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing {voice} voice from Google.",
                    output_path=output_file,
                    voice=voice
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

            # Small delay to avoid rate limiting
            time.sleep(0.3)

    def test_ssml_support(self, provider, temp_audio_file):
        """Test SSML (Speech Synthesis Markup Language) support."""
        ssml_text = '''<speak>
            Hello! <break time="0.5s"/>
            This is a test of <emphasis level="strong">SSML support</emphasis>.
            <prosody rate="slow" pitch="+2st">Speaking slowly with higher pitch.</prosody>
            <say-as interpret-as="date" format="mdy">12/25/2023</say-as>
        </speak>'''

        provider.synthesize(
            text=ssml_text,
            output_path=temp_audio_file,
            voice=self.get_test_voice()
        )
        self.validate_audio_file(temp_audio_file)

    def test_audio_effects(self, provider, temp_audio_file):
        """Test Google's audio effects."""
        effects = [
            "telephony-class-application",
            "wearable-class-device",
            "handset-class-device",
            "headphone-class-device",
            "small-bluetooth-speaker-class-device",
            "medium-bluetooth-speaker-class-device",
            "large-home-entertainment-class-device",
            "large-automotive-class-device"
        ]

        for effect in effects[:3]:  # Test first 3 to avoid quota limits
            output_file = f"{temp_audio_file}_{effect.replace('-', '_')}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing {effect} audio effect.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    audio_encoding="MP3",
                    effects_profile_id=[effect]
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def test_speaking_rate_and_pitch(self, provider, temp_audio_file):
        """Test speaking rate and pitch adjustments."""
        test_cases = [
            {"speaking_rate": 0.5, "pitch": 0.0},    # Slow, normal pitch
            {"speaking_rate": 1.0, "pitch": 5.0},    # Normal speed, higher pitch
            {"speaking_rate": 1.5, "pitch": -3.0},   # Fast, lower pitch
        ]

        for i, params in enumerate(test_cases):
            output_file = f"{temp_audio_file}_params_{i}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing speaking rate {params['speaking_rate']} and pitch {params['pitch']}.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    **params
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

    def test_output_formats(self, provider):
        """Test different audio output formats."""
        formats = [
            ("MP3", "mp3"),
            ("LINEAR16", "wav"),
            ("OGG_OPUS", "ogg"),
        ]

        for encoding, ext in formats:
            temp_file = f"/tmp/google_test.{ext}"
            try:
                provider.synthesize(
                    text="Testing audio format.",
                    output_path=temp_file,
                    voice=self.get_test_voice(),
                    audio_encoding=encoding
                )
                self.validate_audio_file(temp_file)
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_voice_list_caching(self, provider):
        """Test voice list retrieval and caching."""
        # First call should fetch from API
        voices1 = provider._get_available_voices()
        assert len(voices1) > 0, "Should have voices available"

        # Second call should use cache
        voices2 = provider._get_available_voices()
        assert voices1 == voices2, "Cached voices should match"
        assert len(voices2) > 100, "Google should have 100+ voices"

    def test_invalid_voice_error(self, provider, temp_audio_file):
        """Test invalid voice handling."""
        with pytest.raises((ProviderError)):
            provider.synthesize(
                text="This should fail.",
                output_path=temp_audio_file,
                voice="invalid-voice-12345"
            )

    def test_authentication_methods(self):
        """Test both API key and service account authentication."""
        # This test depends on which credentials are available
        api_key = os.getenv("GOOGLE_TTS_API_KEY")
        service_account = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if api_key:
            # Test API key auth
            provider = GoogleTTSProvider()
            auth_method = provider._determine_auth_method()
            assert auth_method in ["api_key", "service_account"]

        if service_account:
            # Test service account auth
            provider = GoogleTTSProvider()
            auth_method = provider._determine_auth_method()
            assert auth_method in ["api_key", "service_account"]

    def test_invalid_api_key(self):
        """Test authentication error with invalid API key."""
        with patch.dict(os.environ, {"GOOGLE_TTS_API_KEY": "invalid_key_12345"}):
            # Remove service account if set
            env_patch = {"GOOGLE_APPLICATION_CREDENTIALS": ""}
            with patch.dict(os.environ, env_patch, clear=False):
                provider = GoogleTTSProvider()
                with pytest.raises((AuthenticationError, ProviderError)):
                    provider.synthesize(
                        text="This should fail.",
                        output_path="/tmp/fail.mp3",
                        voice=self.get_test_voice()
                    )

    def test_network_error_handling(self, provider, temp_audio_file):
        """Test network error handling."""
        # Mock requests to simulate network error
        with patch('src.tts.providers.google_tts.requests.post') as mock_post:
            mock_post.side_effect = NetworkError("Connection failed")

            with pytest.raises(NetworkError):
                provider.synthesize(
                    text="This should fail.",
                    output_path=temp_audio_file,
                    voice=self.get_test_voice()
                )

    def test_quota_error_handling(self, provider):
        """Test quota exceeded error handling."""
        # This would require actually hitting quota limits
        # For now, just test that the provider can handle quota errors
        with patch('src.tts.providers.google_tts.requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.status_code = 429
            mock_response.json.return_value = {"error": {"message": "Quota exceeded"}}

            with pytest.raises(QuotaError):
                provider.synthesize(
                    text="This should fail.",
                    output_path="/tmp/quota_fail.mp3",
                    voice=self.get_test_voice()
                )

    def test_multilingual_support(self, provider, temp_audio_file):
        """Test voices from different languages."""
        multilingual_tests = [
            ("es-ES-Neural2-A", "Hola, ¿cómo estás?"),
            ("fr-FR-Neural2-A", "Bonjour, comment allez-vous?"),
            ("de-DE-Neural2-A", "Hallo, wie geht es Ihnen?"),
            ("ja-JP-Neural2-B", "こんにちは、元気ですか？"),
        ]

        for voice, text in multilingual_tests:
            output_file = f"{temp_audio_file}_{voice.replace('-', '_')}.mp3"
            try:
                provider.synthesize(
                    text=text,
                    output_path=output_file,
                    voice=voice
                )
                self.validate_audio_file(output_file)
            except ProviderError as e:
                if "not found" in str(e).lower():
                    # Voice might not be available in test project
                    continue
                raise
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)

            # Delay between requests
            time.sleep(0.5)

    @pytest.mark.slow
    def test_rate_limiting_handling(self, provider):
        """Test rate limiting with rapid requests."""
        # Google Cloud TTS has generous quotas, but test handling anyway
        for i in range(3):  # Limited to avoid hitting actual quotas
            temp_file = f"/tmp/rate_test_{i}.mp3"
            try:
                provider.synthesize(
                    text=f"Rate limit test {i}",
                    output_path=temp_file,
                    voice=self.get_test_voice()
                )
                self.validate_audio_file(temp_file)
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
