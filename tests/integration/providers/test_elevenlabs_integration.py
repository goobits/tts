"""Integration tests for ElevenLabs TTS provider with real API calls."""

import os
import time
from unittest.mock import patch

import pytest

from src.tts.exceptions import AuthenticationError, NetworkError, ProviderError, VoiceNotFoundError
from src.tts.providers.elevenlabs import ElevenLabsProvider

from .base_provider_test import BaseProviderIntegrationTest


@pytest.mark.integration
class TestElevenLabsIntegration(BaseProviderIntegrationTest):
    """Integration tests for ElevenLabs TTS provider."""
    
    def get_provider_class(self):
        return ElevenLabsProvider
    
    def get_test_voice(self):
        return "rachel"  # Default ElevenLabs voice
    
    def get_api_key_env_var(self):
        return "ELEVENLABS_API_KEY"
    
    def get_provider_name(self):
        return "ElevenLabs"
    
    def test_default_voices(self, provider, temp_audio_file):
        """Test synthesis with default ElevenLabs voices."""
        # Test a subset to avoid quota usage
        voices = ["rachel", "antoni", "bella"]
        
        for voice in voices:
            output_file = f"{temp_audio_file}_{voice}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing {voice} voice from ElevenLabs.",
                    output_path=output_file,
                    voice=voice
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            
            # ElevenLabs has strict rate limits
            time.sleep(1.0)
    
    def test_voice_settings(self, provider, temp_audio_file):
        """Test voice stability and clarity settings."""
        settings_tests = [
            {"stability": 0.3, "similarity_boost": 0.7},   # More variable
            {"stability": 0.7, "similarity_boost": 0.3},   # More stable
            {"stability": 0.5, "similarity_boost": 0.5},   # Balanced
        ]
        
        for i, settings in enumerate(settings_tests):
            output_file = f"{temp_audio_file}_settings_{i}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing voice settings: stability {settings['stability']}, similarity {settings['similarity_boost']}.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    voice_settings=settings
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            
            time.sleep(1.0)
    
    def test_models(self, provider, temp_audio_file):
        """Test different ElevenLabs models."""
        models = [
            "eleven_monolingual_v1",
            "eleven_multilingual_v1", 
            "eleven_multilingual_v2",
        ]
        
        for model in models:
            output_file = f"{temp_audio_file}_{model}.mp3"
            try:
                provider.synthesize(
                    text=f"Testing {model} model.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    model_id=model
                )
                self.validate_audio_file(output_file)
            except ProviderError as e:
                if "not available" in str(e).lower() or "access" in str(e).lower():
                    # Model might not be available for this account
                    continue
                raise
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            
            time.sleep(1.0)
    
    def test_streaming_mode(self, provider):
        """Test streaming functionality."""
        with patch('src.tts.providers.elevenlabs.stream_via_tempfile') as mock_stream:
            provider.synthesize(
                text="Testing streaming mode.",
                output_path=None,
                voice=self.get_test_voice(),
                stream=True
            )
            mock_stream.assert_called_once()
    
    def test_voice_list_retrieval(self, provider):
        """Test retrieving available voices from API."""
        voices = provider._get_available_voices()
        assert len(voices) > 0, "Should have voices available"
        
        # Check that default voices are included
        voice_names = [v["name"].lower() for v in voices]
        assert "rachel" in voice_names, "Rachel should be in voice list"
        
        # Verify voice structure
        for voice in voices[:3]:  # Check first 3
            assert "voice_id" in voice
            assert "name" in voice
            assert "category" in voice
    
    def test_custom_voice_handling(self, provider, temp_audio_file):
        """Test handling of custom/cloned voices."""
        # Use a voice ID format that would be a custom voice
        # This will likely fail but should handle gracefully
        custom_voice_id = "custom_voice_test_12345"
        
        with pytest.raises((VoiceNotFoundError, ProviderError)):
            provider.synthesize(
                text="Testing custom voice.",
                output_path=temp_audio_file,
                voice=custom_voice_id
            )
    
    def test_multilingual_model(self, provider, temp_audio_file):
        """Test multilingual model with different languages."""
        multilingual_tests = [
            ("spanish", "Hola, ¿cómo estás hoy?"),
            ("french", "Bonjour, comment allez-vous?"),
            ("german", "Hallo, wie geht es Ihnen?"),
        ]
        
        for lang, text in multilingual_tests:
            output_file = f"{temp_audio_file}_{lang}.mp3"
            try:
                provider.synthesize(
                    text=text,
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    model_id="eleven_multilingual_v2"
                )
                self.validate_audio_file(output_file)
            except ProviderError as e:
                if "not available" in str(e).lower():
                    # Multilingual model might not be available
                    continue
                raise
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            
            time.sleep(1.5)  # Longer delay for multilingual
    
    def test_invalid_api_key(self):
        """Test authentication error with invalid API key."""
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "invalid_key_12345"}):
            provider = ElevenLabsProvider()
            with pytest.raises((AuthenticationError, ProviderError)):
                provider.synthesize(
                    text="This should fail.",
                    output_path="/tmp/fail.mp3",
                    voice=self.get_test_voice()
                )
    
    def test_quota_limits(self, provider):
        """Test quota/usage tracking."""
        # ElevenLabs provides usage info in headers
        # This test just verifies the provider can handle quota responses
        with patch('src.tts.providers.elevenlabs.requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.status_code = 429
            mock_response.json.return_value = {"detail": {"message": "Quota exceeded"}}
            
            with pytest.raises(ProviderError):
                provider.synthesize(
                    text="This should fail.",
                    output_path="/tmp/quota_fail.mp3",
                    voice=self.get_test_voice()
                )
    
    def test_network_error_handling(self, provider, temp_audio_file):
        """Test network error handling."""
        with patch('src.tts.providers.elevenlabs.requests.post') as mock_post:
            mock_post.side_effect = NetworkError("Connection failed")
            
            with pytest.raises(NetworkError):
                provider.synthesize(
                    text="This should fail.",
                    output_path=temp_audio_file,
                    voice=self.get_test_voice()
                )
    
    def test_long_text_handling(self, provider, temp_audio_file):
        """Test handling of longer text."""
        # ElevenLabs has character limits per request
        long_text = self.TEST_TEXT_MEDIUM  # Use medium text to avoid limits
        
        provider.synthesize(
            text=long_text,
            output_path=temp_audio_file,
            voice=self.get_test_voice()
        )
        self.validate_audio_file(temp_audio_file)
    
    def test_output_format_optimization(self, provider, temp_audio_file):
        """Test different optimization settings."""
        optimize_settings = [True, False]
        
        for optimize in optimize_settings:
            output_file = f"{temp_audio_file}_opt_{optimize}.mp3"
            try:
                provider.synthesize(
                    text="Testing optimization setting.",
                    output_path=output_file,
                    voice=self.get_test_voice(),
                    optimize_streaming_latency=optimize
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            
            time.sleep(1.0)
    
    @pytest.mark.slow
    def test_rate_limiting_handling(self, provider):
        """Test rate limiting with rapid requests."""
        # ElevenLabs has strict rate limits - test graceful handling
        for i in range(3):  # Limited to avoid hitting actual limits
            temp_file = f"/tmp/rate_test_{i}.mp3"
            try:
                provider.synthesize(
                    text=f"Rate limit test {i}",
                    output_path=temp_file,
                    voice=self.get_test_voice()
                )
                self.validate_audio_file(temp_file)
            except ProviderError as e:
                if "rate" in str(e).lower() or "limit" in str(e).lower():
                    # Expected rate limit error
                    break
                raise
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
            # Mandatory delay between requests
            time.sleep(2.0)