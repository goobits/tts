"""Abstract base class for TTS providers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .types import ProviderInfo


class TTSProvider(ABC):
    """Abstract base class for all TTS provider implementations.
    
    This class defines the interface that all TTS providers must implement
    to be compatible with the TTS CLI system. Providers handle the actual
    text-to-speech synthesis using their respective APIs or engines.
    """
    
    @abstractmethod
    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """Synthesize speech from text and save to output path.
        
        This is the core method that all providers must implement. It should
        convert the input text to speech and either save it to the specified
        output path or stream it directly if stream=True is in kwargs.
        
        Args:
            text: The text to synthesize into speech
            output_path: Path where the audio file should be saved
            **kwargs: Provider-specific options including:
                - voice: Voice name or identifier
                - output_format: Audio format (mp3, wav, etc.)  
                - stream: Whether to stream audio directly (bool)
                - rate: Speaking rate adjustment
                - pitch: Pitch adjustment
                - Other provider-specific parameters
                
        Raises:
            TTSError: Base exception for any synthesis errors
            ProviderError: Provider-specific errors
            NetworkError: Network connectivity issues
            AuthenticationError: API authentication failures
            VoiceNotFoundError: Invalid voice specified
        """
        pass
    
    def get_info(self) -> Optional[ProviderInfo]:
        """Get provider information including available voices and capabilities.
        
        Returns provider metadata that helps users understand what options
        are available and how to configure the provider properly.
        
        Returns:
            Dictionary containing provider information with keys:
                - name: Human-readable provider name
                - description: Brief description of the provider
                - options: Dict of available configuration options
                - output_format: Supported audio formats
                - sample_voices: List of example voice names
                - capabilities: List of supported features
            Returns None if provider info is not available.
        """
        return None