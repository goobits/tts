"""Custom exceptions for TTS CLI."""


class TTSError(Exception):
    """Base exception for all TTS-related errors."""
    pass


class ProviderError(TTSError):
    """Exception raised when a TTS provider encounters an error."""
    pass


class ProviderNotFoundError(TTSError):
    """Exception raised when a requested TTS provider is not available."""
    pass


class ProviderLoadError(TTSError):
    """Exception raised when a TTS provider fails to load."""
    pass


class AudioConversionError(TTSError):
    """Exception raised when audio format conversion fails."""
    pass


class AudioPlaybackError(TTSError):
    """Exception raised when audio playback fails."""
    pass


class VoiceNotFoundError(TTSError):
    """Exception raised when a requested voice is not available."""
    pass


class NetworkError(TTSError):
    """Exception raised when network-related errors occur."""
    pass


class DependencyError(TTSError):
    """Exception raised when required dependencies are missing."""
    pass