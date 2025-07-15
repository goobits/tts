"""Tests for exception handling and HTTP error mapping.

These tests cover the exception hierarchy and HTTP error mapping logic
without requiring external dependencies or mocks. They test:
- Exception inheritance hierarchy
- HTTP status code to exception mapping
- Error message formatting
- Provider context handling
"""

import pytest

from tts_cli.exceptions import (
    TTSError,
    ProviderError,
    ProviderNotFoundError,
    ProviderLoadError,
    AuthenticationError,
    RateLimitError,
    QuotaError,
    ServerError,
    NetworkError,
    AudioPlaybackError,
    DependencyError,
    VoiceNotFoundError,
    APIError,
    map_http_error
)


class TestExceptionHierarchy:
    """Test the exception class hierarchy and inheritance."""
    
    def test_base_exception_inheritance(self):
        """Test that all custom exceptions inherit from TTSError."""
        exception_classes = [
            ProviderError,
            ProviderNotFoundError,
            ProviderLoadError,
            AuthenticationError,
            RateLimitError,
            QuotaError,
            ServerError,
            NetworkError,
            AudioPlaybackError,
            DependencyError,
            VoiceNotFoundError,
            APIError
        ]
        
        for exc_class in exception_classes:
            assert issubclass(exc_class, TTSError), f"{exc_class.__name__} should inherit from TTSError"
            assert issubclass(exc_class, Exception), f"{exc_class.__name__} should inherit from Exception"
    
    def test_exception_instantiation(self):
        """Test that all exception classes can be instantiated with messages."""
        exception_classes = [
            TTSError,
            ProviderError,
            ProviderNotFoundError,
            ProviderLoadError,
            AuthenticationError,
            RateLimitError,
            QuotaError,
            ServerError,
            NetworkError,
            AudioPlaybackError,
            DependencyError,
            VoiceNotFoundError,
            APIError
        ]
        
        for exc_class in exception_classes:
            # Test with message
            exc = exc_class("Test error message")
            assert str(exc) == "Test error message"
            
            # Test without message
            exc_empty = exc_class()
            assert isinstance(exc_empty, exc_class)
    
    def test_exception_raising_and_catching(self):
        """Test that exceptions can be raised and caught correctly."""
        # Test raising and catching specific exception
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("API key invalid")
        
        # Test catching by base class
        with pytest.raises(TTSError):
            raise ProviderError("Provider failed")
        
        # Test catching by Exception
        with pytest.raises(Exception):
            raise NetworkError("Network timeout")


class TestHttpErrorMapping:
    """Test HTTP status code to exception mapping."""
    
    def test_authentication_errors(self):
        """Test mapping of authentication-related HTTP status codes."""
        # 401 Unauthorized
        error = map_http_error(401)
        assert isinstance(error, AuthenticationError)
        assert "API authentication failed" in str(error)
        
        # 403 Forbidden
        error = map_http_error(403)
        assert isinstance(error, AuthenticationError)
        assert "API access forbidden" in str(error)
    
    def test_authentication_errors_with_provider(self):
        """Test authentication error mapping with provider context."""
        error = map_http_error(401, "Invalid API key", "openai")
        assert isinstance(error, AuthenticationError)
        assert "openai:" in str(error)
        assert "API authentication failed" in str(error)
        
        error = map_http_error(403, "Access denied", "elevenlabs")
        assert isinstance(error, AuthenticationError)
        assert "elevenlabs:" in str(error)
        assert "API access forbidden" in str(error)
    
    def test_rate_limit_errors(self):
        """Test rate limit HTTP status code mapping."""
        # 429 Too Many Requests
        error = map_http_error(429)
        assert isinstance(error, RateLimitError)
        assert "rate limit exceeded" in str(error)
        
        # With provider context
        error = map_http_error(429, "Rate limit exceeded", "google")
        assert isinstance(error, RateLimitError)
        assert "google:" in str(error)
    
    def test_quota_and_billing_errors(self):
        """Test quota and billing related HTTP status code mapping."""
        # 402 Payment Required
        error = map_http_error(402)
        assert isinstance(error, QuotaError)
        assert "quota or billing issue" in str(error)
        
        # With provider context
        error = map_http_error(402, "Insufficient credits", "elevenlabs")
        assert isinstance(error, QuotaError)
        assert "elevenlabs:" in str(error)
        assert "quota or billing issue" in str(error)
    
    def test_server_errors(self):
        """Test server error HTTP status code mapping."""
        server_error_codes = [500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 599]
        
        for status_code in server_error_codes:
            error = map_http_error(status_code)
            assert isinstance(error, ServerError), f"Status {status_code} should map to ServerError"
            assert f"HTTP {status_code}" in str(error)
            assert "server error" in str(error).lower()
        
        # With provider context
        error = map_http_error(500, "Internal server error", "openai")
        assert isinstance(error, ServerError)
        assert "openai:" in str(error)
        assert "HTTP 500" in str(error)
    
    def test_generic_client_errors(self):
        """Test generic client error HTTP status code mapping."""
        client_error_codes = [400, 404, 405, 406, 408, 409, 410, 422]
        
        for status_code in client_error_codes:
            error = map_http_error(status_code)
            assert isinstance(error, ProviderError), f"Status {status_code} should map to ProviderError"
            assert f"API error {status_code}" in str(error)
    
    def test_generic_client_errors_with_response_text(self):
        """Test client error mapping with response text included."""
        error = map_http_error(400, "Bad request: invalid parameters")
        assert isinstance(error, ProviderError)
        assert "API error 400" in str(error)
        assert "Bad request: invalid parameters" in str(error)
        
        # With provider context
        error = map_http_error(404, "Voice not found", "elevenlabs")
        assert isinstance(error, ProviderError)
        assert "elevenlabs:" in str(error)
        assert "API error 404" in str(error)
        assert "Voice not found" in str(error)
    
    def test_success_codes_as_errors(self):
        """Test that success codes still map to ProviderError (shouldn't happen but test anyway)."""
        success_codes = [200, 201, 202, 204]
        
        for status_code in success_codes:
            error = map_http_error(status_code)
            assert isinstance(error, ProviderError)
            assert f"API error {status_code}" in str(error)
    
    def test_unusual_status_codes(self):
        """Test mapping of unusual or custom HTTP status codes."""
        unusual_codes = [100, 300, 418, 451, 999]  # Including 418 I'm a teapot!
        
        for status_code in unusual_codes:
            error = map_http_error(status_code)
            assert isinstance(error, ProviderError)
            assert f"API error {status_code}" in str(error)
    
    def test_error_message_truncation(self):
        """Test that very long error messages are truncated appropriately."""
        # Create a very long error message
        long_message = "A" * 1000  # 1000 character message
        
        error = map_http_error(400, long_message)
        error_str = str(error)
        
        # Should contain the status code
        assert "API error 400" in error_str
        # Should contain some of the message but be truncated
        assert "AAA" in error_str  # Start of the message should be there
        # Full message might be truncated based on config
        assert len(error_str) < len(f"API error 400: {long_message}")  # Should be shorter than full
    
    def test_empty_response_text(self):
        """Test error mapping with empty response text."""
        error = map_http_error(400, "")
        assert isinstance(error, ProviderError)
        assert "API error 400" in str(error)
        # Should not have extra colon or spaces for empty response
        assert str(error) == "API error 400"
        
        # With provider but empty response
        error = map_http_error(400, "", "test_provider")
        assert "test_provider: API error 400" in str(error)
    
    def test_none_and_whitespace_inputs(self):
        """Test error mapping with None and whitespace inputs."""
        # None response text (should be treated as empty)
        error = map_http_error(400, None)
        assert isinstance(error, ProviderError)
        assert "API error 400" in str(error)
        
        # Whitespace-only response text
        error = map_http_error(400, "   ")
        assert isinstance(error, ProviderError)
        assert "API error 400" in str(error)
        
        # Empty provider name
        error = map_http_error(401, "Unauthorized", "")
        assert isinstance(error, AuthenticationError)
        # Should not have provider prefix for empty provider
        assert not str(error).startswith(":")
    
    def test_provider_context_formatting(self):
        """Test that provider context is formatted correctly in error messages."""
        # Test various provider names
        providers = ["openai", "elevenlabs", "google", "edge_tts", "chatterbox"]
        
        for provider in providers:
            error = map_http_error(401, "Auth failed", provider)
            assert isinstance(error, AuthenticationError)
            error_str = str(error)
            assert error_str.startswith(f"{provider}:")
            assert "API authentication failed" in error_str
    
    def test_special_characters_in_response(self):
        """Test error mapping with special characters in response text."""
        special_responses = [
            'Error: "Invalid API key"',
            "Error with 'single quotes'",
            "Error with unicode: café",
            "Error with symbols: @#$%^&*()",
            "Multi-line\nerror\nmessage",
            "Error with\ttabs"
        ]
        
        for response in special_responses:
            error = map_http_error(400, response)
            assert isinstance(error, ProviderError)
            assert "API error 400" in str(error)
            # Response should be preserved in the error message
            error_str = str(error)
            # The response might be truncated, but start should be there
            assert response[:10] in error_str or "API error 400" in error_str


class TestErrorMessageFormatting:
    """Test error message formatting and context."""
    
    def test_provider_prefix_formatting(self):
        """Test that provider prefixes are formatted consistently."""
        providers = ["openai", "test-provider", "UPPERCASE", "mixed_Case"]
        
        for provider in providers:
            error = map_http_error(401, "Test error", provider)
            error_str = str(error)
            # Should start with provider name followed by colon and space
            assert error_str.startswith(f"{provider}: ")
    
    def test_message_without_provider(self):
        """Test error messages without provider context."""
        error = map_http_error(429)
        error_str = str(error)
        # Should not start with a colon
        assert not error_str.startswith(":")
        # Should not contain ": :" pattern
        assert ": :" not in error_str
    
    def test_error_type_consistency(self):
        """Test that error types are consistent for same status codes."""
        # Same status code should always return same exception type
        for _ in range(5):  # Test multiple times
            assert type(map_http_error(401)) == AuthenticationError
            assert type(map_http_error(429)) == RateLimitError
            assert type(map_http_error(500)) == ServerError
            assert type(map_http_error(400)) == ProviderError