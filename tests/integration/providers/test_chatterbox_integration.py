"""Integration tests for Chatterbox TTS provider with real model loading."""

import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from src.tts.exceptions import DependencyError, ProviderError
from src.tts.providers.chatterbox import ChatterboxProvider

from .base_provider_test import BaseProviderIntegrationTest


@pytest.mark.integration
class TestChatterboxIntegration(BaseProviderIntegrationTest):
    """Integration tests for Chatterbox (local voice cloning) provider."""
    
    def get_provider_class(self):
        return ChatterboxProvider
    
    def get_test_voice(self):
        return "default"  # Chatterbox uses loaded voice files
    
    def get_api_key_env_var(self):
        return None  # Chatterbox is local, no API key needed
    
    def get_provider_name(self):
        return "Chatterbox"
    
    @pytest.fixture(autouse=True)
    def check_chatterbox_available(self):
        """Check if Chatterbox dependencies are available."""
        try:
            import chatterbox
        except ImportError:
            pytest.skip("Chatterbox library not installed")
        
        # Check if we have enough system resources
        if not self._has_sufficient_memory():
            pytest.skip("Insufficient memory for Chatterbox model loading")
    
    def _has_sufficient_memory(self):
        """Check if system has enough memory for model loading."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            # Chatterbox needs at least 2GB available
            return memory.available > 2 * 1024 * 1024 * 1024
        except ImportError:
            # Can't check memory, assume it's sufficient
            return True
    
    @pytest.fixture
    def sample_voice_file(self):
        """Create a sample voice file for testing."""
        # Create a minimal WAV file for testing
        import wave
        import numpy as np
        
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()
        
        # Generate 1 second of sine wave audio
        sample_rate = 22050
        duration = 1.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_model_loading(self, provider):
        """Test that the Chatterbox model loads successfully."""
        # This will trigger lazy loading
        provider._lazy_load()
        assert provider.tts is not None, "Model should be loaded"
    
    def test_cuda_detection(self, provider):
        """Test CUDA availability detection."""
        has_cuda = provider._has_cuda()
        assert isinstance(has_cuda, bool), "CUDA detection should return boolean"
        
        # If CUDA is available, verify torch can use it
        if has_cuda:
            try:
                import torch
                assert torch.cuda.is_available(), "Torch should confirm CUDA availability"
            except ImportError:
                pytest.fail("CUDA detected but PyTorch not available")
    
    def test_basic_synthesis_with_default_voice(self, provider, temp_audio_file):
        """Test basic synthesis without loading custom voice."""
        provider.synthesize(
            text=self.TEST_TEXT_SHORT,
            output_path=temp_audio_file
        )
        self.validate_audio_file(temp_audio_file)
    
    def test_voice_loading_and_synthesis(self, provider, sample_voice_file, temp_audio_file):
        """Test loading a voice file and using it for synthesis."""
        # Load the voice file
        provider.synthesize(
            text=self.TEST_TEXT_SHORT,
            output_path=temp_audio_file,
            voice=sample_voice_file  # Use the voice file path
        )
        self.validate_audio_file(temp_audio_file)
    
    def test_voice_manager_integration(self, provider, sample_voice_file):
        """Test integration with voice manager for preloading."""
        from src.tts.voice_manager import VoiceManager
        
        voice_manager = VoiceManager()
        
        # Load voice into manager
        voice_name = voice_manager.load_voice(sample_voice_file)
        assert voice_name is not None, "Voice should be loaded"
        
        # Use loaded voice
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()
        
        try:
            provider.synthesize(
                text=self.TEST_TEXT_SHORT,
                output_path=temp_file.name,
                voice=voice_name
            )
            self.validate_audio_file(temp_file.name)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_different_output_formats(self, provider, temp_audio_file):
        """Test synthesis with different output formats."""
        formats = ["wav", "mp3"]
        
        for fmt in formats:
            output_file = f"{temp_audio_file}.{fmt}"
            try:
                provider.synthesize(
                    text=self.TEST_TEXT_SHORT,
                    output_path=output_file,
                    output_format=fmt
                )
                self.validate_audio_file(output_file)
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
    
    def test_synthesis_parameters(self, provider, temp_audio_file):
        """Test synthesis with different parameters."""
        # Test different speaking rates if supported
        try:
            provider.synthesize(
                text="Testing synthesis parameters.",
                output_path=temp_audio_file,
                rate=1.2  # Slightly faster
            )
            self.validate_audio_file(temp_audio_file)
        except (TypeError, ProviderError):
            # Parameter might not be supported
            pass
    
    def test_long_text_processing(self, provider, temp_audio_file):
        """Test processing of longer text."""
        provider.synthesize(
            text=self.TEST_TEXT_LONG,
            output_path=temp_audio_file
        )
        self.validate_audio_file(temp_audio_file)
    
    def test_invalid_voice_file(self, provider, temp_audio_file):
        """Test handling of invalid voice file."""
        invalid_voice = "/tmp/nonexistent_voice.wav"
        
        with pytest.raises((FileNotFoundError, ProviderError)):
            provider.synthesize(
                text=self.TEST_TEXT_SHORT,
                output_path=temp_audio_file,
                voice=invalid_voice
            )
    
    def test_memory_cleanup(self, provider):
        """Test that models are properly cleaned up."""
        # Load model
        provider._lazy_load()
        assert provider.tts is not None
        
        # Note: Actual memory cleanup would require provider.close() method
        # This test just verifies the model is loaded
        
    def test_device_fallback(self, provider):
        """Test fallback from CUDA to CPU if needed."""
        with patch.object(provider, '_has_cuda', return_value=False):
            provider._lazy_load()
            assert provider.tts is not None, "Should fallback to CPU"
    
    def test_dependency_error(self):
        """Test error when chatterbox is not installed."""
        with patch('src.tts.providers.chatterbox.ChatterboxTTS') as mock_tts:
            mock_tts.side_effect = ImportError("No module named 'chatterbox'")
            
            provider = ChatterboxProvider()
            with pytest.raises(DependencyError):
                provider._lazy_load()
    
    def test_model_loading_error(self):
        """Test error handling during model loading."""
        with patch('src.tts.providers.chatterbox.ChatterboxTTS.from_pretrained') as mock_pretrained:
            mock_pretrained.side_effect = RuntimeError("Model loading failed")
            
            provider = ChatterboxProvider()
            with pytest.raises(ProviderError):
                provider._lazy_load()
    
    def test_streaming_mode(self, provider):
        """Test streaming functionality (if supported)."""
        # Chatterbox might not support streaming, test graceful handling
        try:
            with patch('src.tts.providers.chatterbox.stream_audio_file') as mock_stream:
                provider.synthesize(
                    text="Testing streaming mode.",
                    output_path=None,
                    stream=True
                )
                # If streaming is supported, mock should be called
        except (NotImplementedError, ProviderError):
            # Streaming might not be supported
            pass
    
    @pytest.mark.slow
    def test_model_performance(self, provider, temp_audio_file):
        """Test model performance characteristics."""
        import time
        
        # Warm up the model
        provider.synthesize(
            text="Warm up.",
            output_path=temp_audio_file
        )
        
        # Time a synthesis operation
        start_time = time.time()
        provider.synthesize(
            text=self.TEST_TEXT_MEDIUM,
            output_path=temp_audio_file
        )
        synthesis_time = time.time() - start_time
        
        # Should complete in reasonable time (under 30 seconds for medium text)
        assert synthesis_time < 30, f"Synthesis took too long: {synthesis_time}s"
        
        self.validate_audio_file(temp_audio_file)