"""Custom exceptions for TTS CLI with standardized error hierarchy."""

from .config import get_config_value


class TTSError(Exception):
    """Base exception for all TTS-related errors."""
    pass


class ProviderError(TTSError):
    """Exception raised when a TTS provider encounters a generic error."""
    pass


class ProviderNotFoundError(TTSError):
    """Exception raised when a requested TTS provider is not available."""
    pass


class ProviderLoadError(TTSError):
    """Exception raised when a TTS provider fails to load."""
    pass


class AuthenticationError(TTSError):
    """Exception raised when API authentication fails.

    This includes API key validation, credential issues, and authorization failures.
    """
    pass


class RateLimitError(TTSError):
    """Exception raised when API rate limits are exceeded.

    Typically occurs with HTTP 429 responses from TTS providers.
    """
    pass


class QuotaError(TTSError):
    """Exception raised when API quota or billing issues occur.

    This includes monthly usage limits, insufficient credits, or billing problems.
    """
    pass


class ServerError(TTSError):
    """Exception raised when provider servers return 5xx errors.

    Indicates issues on the provider's side that are temporary or systemic.
    """
    pass


class TimeoutError(TTSError):
    """Exception raised when operations timeout.

    This includes network timeouts, synthesis timeouts, or streaming timeouts.
    """
    pass


class ConfigurationError(TTSError):
    """Exception raised when provider configuration is invalid.

    This includes missing required settings, invalid parameter values, or
    configuration conflicts.
    """
    pass


class VoiceNotFoundError(TTSError):
    """Exception raised when a requested voice is not available.

    This includes invalid voice names, unavailable voices for a provider,
    or language-specific voice limitations.
    """
    pass


class AudioConversionError(TTSError):
    """Exception raised when audio format conversion fails.

    This includes FFmpeg conversion errors or unsupported format combinations.
    """
    pass


class AudioPlaybackError(TTSError):
    """Exception raised when audio playback fails.

    This includes missing audio devices, driver issues, or streaming problems.
    """
    pass


class NetworkError(TTSError):
    """Exception raised when network-related errors occur.

    This includes connection failures, DNS issues, and general connectivity problems.
    """
    pass


class DependencyError(TTSError):
    """Exception raised when required dependencies are missing.

    This includes missing Python packages, system libraries, or external tools.
    """
    pass


def map_http_error(status_code: int, response_text: str = "", provider: str = "") -> TTSError:
    """Map HTTP status codes to appropriate exception types.

    Args:
        status_code: HTTP status code from provider response
        response_text: Optional response body text for context
        provider: Optional provider name for error context

    Returns:
        Appropriate TTSError subclass instance
    """
    provider_prefix = f"{provider}: " if provider else ""

    if status_code == get_config_value('http_unauthorized'):
        return AuthenticationError(f"{provider_prefix}API authentication failed. Check your API key.")
    elif status_code == get_config_value('http_forbidden'):
        return AuthenticationError(f"{provider_prefix}API access forbidden. Check your permissions.")
    elif status_code == get_config_value('http_rate_limit'):
        return RateLimitError(f"{provider_prefix}API rate limit exceeded. Please wait and try again.")
    elif status_code in get_config_value('http_payment_errors'):  # Payment required, billing conflicts
        return QuotaError(f"{provider_prefix}API quota or billing issue. Check your account status.")
    elif get_config_value('http_server_error_range_start') <= status_code < get_config_value('http_server_error_range_end'):
        return ServerError(f"{provider_prefix}Provider server error (HTTP {status_code}). Try again later.")
    else:
        error_detail = f": {response_text[:get_config_value('error_message_max_length')]}" if response_text else ""
        return ProviderError(f"{provider_prefix}API error {status_code}{error_detail}")
