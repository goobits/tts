"""
Network-only mocking infrastructure that preserves provider logic.

This module provides lightweight network mocks that intercept HTTP requests
and responses while allowing real provider classes to run with realistic
fake external responses. This approach preserves provider logic including
error handling, retries, and edge cases.
"""

import json
import base64
from typing import Any, Dict, List, Optional, Union, Callable
from unittest.mock import MagicMock, Mock
import pytest
import requests


class MockHTTPResponse:
    """Mock HTTP response that behaves like requests.Response."""
    
    def __init__(
        self,
        status_code: int = 200,
        content: bytes = b"",
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        text: str = "",
        url: str = "",
        raise_for_status_error: Optional[Exception] = None
    ):
        self.status_code = status_code
        self.content = content
        self._json_data = json_data
        self.headers = headers or {}
        self.text = text
        self.url = url
        self._raise_for_status_error = raise_for_status_error
        
    def json(self) -> Dict[str, Any]:
        """Return JSON data or raise ValueError if invalid."""
        if self._json_data is not None:
            return self._json_data
        if self.text:
            try:
                return json.loads(self.text)
            except json.JSONDecodeError:
                raise ValueError("No JSON object could be decoded")
        raise ValueError("No JSON object could be decoded")
    
    def raise_for_status(self) -> None:
        """Raise HTTPError if status indicates an error."""
        if self._raise_for_status_error:
            raise self._raise_for_status_error
        if 400 <= self.status_code < 600:
            raise requests.HTTPError(f"HTTP {self.status_code} Error", response=self)
    
    def iter_content(self, chunk_size: int = 1024) -> List[bytes]:
        """Iterate over content in chunks."""
        if not self.content:
            return []
        
        chunks = []
        for i in range(0, len(self.content), chunk_size):
            chunks.append(self.content[i:i + chunk_size])
        return chunks
    
    def iter_bytes(self, chunk_size: int = 1024) -> List[bytes]:
        """OpenAI-style iter_bytes method."""
        return self.iter_content(chunk_size)


class NetworkMockRegistry:
    """Registry for network mocks that maps URLs to responses."""
    
    def __init__(self):
        self.url_patterns: Dict[str, Callable[[str, str, Dict[str, Any]], MockHTTPResponse]] = {}
        self.default_response = MockHTTPResponse(404, text="Not Found")
    
    def register_pattern(
        self, 
        pattern: str, 
        response_factory: Callable[[str, str, Dict[str, Any]], MockHTTPResponse]
    ) -> None:
        """Register a URL pattern with a response factory function."""
        self.url_patterns[pattern] = response_factory
    
    def get_response(self, method: str, url: str, **kwargs) -> MockHTTPResponse:
        """Get mock response for a given method and URL."""
        for pattern, factory in self.url_patterns.items():
            if pattern in url:
                return factory(method, url, kwargs)
        return self.default_response


# Global registry instance
_network_registry = NetworkMockRegistry()


def mock_requests_request(method: str, url: str, **kwargs) -> MockHTTPResponse:
    """Mock function for requests.request that uses the registry."""
    return _network_registry.get_response(method, url, **kwargs)


def mock_requests_get(url: str, **kwargs) -> MockHTTPResponse:
    """Mock function for requests.get."""
    return mock_requests_request("GET", url, **kwargs)


def mock_requests_post(url: str, **kwargs) -> MockHTTPResponse:
    """Mock function for requests.post."""
    return mock_requests_request("POST", url, **kwargs)


@pytest.fixture
def network_mock_registry():
    """Pytest fixture providing access to the network mock registry."""
    # Clear any existing patterns
    _network_registry.url_patterns.clear()
    yield _network_registry
    # Clean up after test
    _network_registry.url_patterns.clear()


@pytest.fixture  
def mock_http_requests(monkeypatch, network_mock_registry):
    """Mock HTTP requests while preserving provider logic."""
    
    # Mock the requests module functions
    monkeypatch.setattr("requests.request", mock_requests_request)
    monkeypatch.setattr("requests.get", mock_requests_get)
    monkeypatch.setattr("requests.post", mock_requests_post)
    
    # Also mock requests.Session for providers that use sessions
    class MockSession:
        def request(self, method: str, url: str, **kwargs) -> MockHTTPResponse:
            return mock_requests_request(method, url, **kwargs)
        
        def get(self, url: str, **kwargs) -> MockHTTPResponse:
            return mock_requests_get(url, **kwargs)
        
        def post(self, url: str, **kwargs) -> MockHTTPResponse:
            return mock_requests_post(url, **kwargs)
    
    monkeypatch.setattr("requests.Session", MockSession)
    
    return network_mock_registry


@pytest.fixture
def mock_network_exceptions():
    """Mock network exceptions for testing error handling."""
    
    def create_connection_error(message: str = "Connection failed"):
        return requests.ConnectionError(message)
    
    def create_timeout_error(message: str = "Request timeout"):
        return requests.Timeout(message)
    
    def create_http_error(status_code: int, message: str = "HTTP Error"):
        response = MockHTTPResponse(status_code=status_code, text=message)
        return requests.HTTPError(message, response=response)
    
    return {
        "connection_error": create_connection_error,
        "timeout_error": create_timeout_error, 
        "http_error": create_http_error,
    }


# Utility functions for creating common response types

def create_json_response(
    data: Dict[str, Any], 
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> MockHTTPResponse:
    """Create a JSON response."""
    json_text = json.dumps(data)
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)
    
    return MockHTTPResponse(
        status_code=status_code,
        content=json_text.encode(),
        json_data=data,
        text=json_text,
        headers=response_headers
    )


def create_audio_response(
    audio_data: bytes = b"mock_audio_data",
    status_code: int = 200,
    content_type: str = "audio/mpeg"
) -> MockHTTPResponse:
    """Create an audio response."""
    return MockHTTPResponse(
        status_code=status_code,
        content=audio_data,
        headers={"Content-Type": content_type}
    )


def create_error_response(
    status_code: int,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None
) -> MockHTTPResponse:
    """Create an error response."""
    if error_details:
        data = {"error": {"message": error_message, **error_details}}
    else:
        data = {"error": {"message": error_message}}
    
    return create_json_response(data, status_code)


def create_streaming_response(
    chunks: List[bytes],
    status_code: int = 200,
    content_type: str = "audio/mpeg"
) -> MockHTTPResponse:
    """Create a streaming response that returns chunks."""
    total_content = b"".join(chunks)
    
    response = MockHTTPResponse(
        status_code=status_code,
        content=total_content,
        headers={"Content-Type": content_type}
    )
    
    # Override iter_content to return our specific chunks
    response.iter_content = lambda chunk_size: chunks
    response.iter_bytes = lambda chunk_size: chunks
    
    return response