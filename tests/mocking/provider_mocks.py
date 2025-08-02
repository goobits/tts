"""
Provider-specific network mocks with realistic API responses.

This module provides realistic mock responses for each TTS provider's API
endpoints, allowing real provider classes to run with fake external responses
while preserving their error handling, retry logic, and edge cases.
"""

import json
import base64
from typing import Any, Dict, List, Optional
import pytest

from .network_mocks import (
    NetworkMockRegistry,
    MockHTTPResponse,
    create_json_response,
    create_audio_response,
    create_error_response,
    create_streaming_response,
)


# Mock audio data for testing
MOCK_AUDIO_MP3 = b"\xff\xfb\x90\x00" + b"mock_mp3_audio_data" * 100
MOCK_AUDIO_WAV = b"RIFF\x24\x08\x00\x00WAVEfmt " + b"mock_wav_audio_data" * 100
MOCK_AUDIO_CHUNKS = [MOCK_AUDIO_MP3[i:i+1024] for i in range(0, len(MOCK_AUDIO_MP3), 1024)]


class ElevenLabsMockProvider:
    """Mock responses for ElevenLabs API endpoints."""
    
    @staticmethod
    def setup(registry: NetworkMockRegistry) -> None:
        """Register ElevenLabs API mock responses."""
        
        # Voice list endpoint
        registry.register_pattern(
            "api.elevenlabs.io/v1/voices",
            ElevenLabsMockProvider._handle_voices
        )
        
        # Text-to-speech endpoint
        registry.register_pattern(
            "api.elevenlabs.io/v1/text-to-speech",
            ElevenLabsMockProvider._handle_synthesis
        )
    
    @staticmethod
    def _handle_voices(method: str, url: str, kwargs: Dict[str, Any]) -> MockHTTPResponse:
        """Handle voice list requests."""
        if method != "GET":
            return create_error_response(405, "Method not allowed")
        
        # Check for API key
        headers = kwargs.get("headers", {})
        if "xi-api-key" not in headers:
            return create_error_response(401, "Missing API key")
        
        # Mock voice data
        voices_data = {
            "voices": [
                {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "name": "Rachel",
                    "category": "premade",
                    "description": "Calm and soothing female voice",
                    "labels": {"gender": "female", "age": "young"}
                },
                {
                    "voice_id": "AZnzlk1XvdvUeBnXmlld", 
                    "name": "Domi",
                    "category": "premade",
                    "description": "Strong and confident female voice",
                    "labels": {"gender": "female", "age": "adult"}
                },
                {
                    "voice_id": "ErXwobaYiN019PkySvjV",
                    "name": "Antoni",
                    "category": "premade", 
                    "description": "Well-rounded male voice",
                    "labels": {"gender": "male", "age": "adult"}
                }
            ]
        }
        
        return create_json_response(voices_data)
    
    @staticmethod
    def _handle_synthesis(method: str, url: str, kwargs: Dict[str, Any]) -> MockHTTPResponse:
        """Handle text-to-speech synthesis requests."""
        if method != "POST":
            return create_error_response(405, "Method not allowed")
        
        # Check for API key
        headers = kwargs.get("headers", {})
        if "xi-api-key" not in headers:
            return create_error_response(401, "Missing API key")
        
        # Extract voice ID from URL
        voice_id = url.split("/")[-1] if "/" in url else None
        if not voice_id:
            return create_error_response(400, "Missing voice ID")
        
        # Check request data
        request_data = kwargs.get("json", {})
        if not request_data.get("text"):
            return create_error_response(400, "Missing text input")
        
        # Handle streaming vs regular requests
        if "/stream" in url:
            return create_streaming_response(MOCK_AUDIO_CHUNKS)
        else:
            return create_audio_response(MOCK_AUDIO_MP3)


class OpenAIMockProvider:
    """Mock responses for OpenAI TTS API endpoints."""
    
    @staticmethod
    def setup(registry: NetworkMockRegistry) -> None:
        """Register OpenAI API mock responses."""
        # OpenAI uses the client library, so we need to mock that differently
        pass
    
    @staticmethod
    def get_mock_client():
        """Get a mock OpenAI client for testing."""
        from unittest.mock import MagicMock
        
        mock_client = MagicMock()
        
        # Mock audio.speech.create method
        mock_response = MagicMock()
        mock_response.stream_to_file = MagicMock()
        mock_response.iter_bytes = MagicMock(return_value=MOCK_AUDIO_CHUNKS)
        
        mock_client.audio.speech.create.return_value = mock_response
        
        return mock_client


class GoogleTTSMockProvider:
    """Mock responses for Google Cloud TTS API endpoints."""
    
    @staticmethod
    def setup(registry: NetworkMockRegistry) -> None:
        """Register Google Cloud TTS API mock responses."""
        
        # Voice list endpoint
        registry.register_pattern(
            "texttospeech.googleapis.com/v1/voices",
            GoogleTTSMockProvider._handle_voices
        )
        
        # Text-to-speech synthesis endpoint
        registry.register_pattern(
            "texttospeech.googleapis.com/v1/text:synthesize",
            GoogleTTSMockProvider._handle_synthesis
        )
    
    @staticmethod
    def _handle_voices(method: str, url: str, kwargs: Dict[str, Any]) -> MockHTTPResponse:
        """Handle voice list requests."""
        if method != "GET":
            return create_error_response(405, "Method not allowed")
        
        # Check for API key in params
        params = kwargs.get("params", {})
        if "key" not in params:
            return create_error_response(401, "Missing API key")
        
        # Mock voice data
        voices_data = {
            "voices": [
                {
                    "name": "en-US-Neural2-A",
                    "languageCodes": ["en-US"],
                    "ssmlGender": "FEMALE",
                    "naturalSampleRateHertz": 24000
                },
                {
                    "name": "en-US-Neural2-C", 
                    "languageCodes": ["en-US"],
                    "ssmlGender": "FEMALE",
                    "naturalSampleRateHertz": 24000
                },
                {
                    "name": "en-US-Neural2-D",
                    "languageCodes": ["en-US"], 
                    "ssmlGender": "MALE",
                    "naturalSampleRateHertz": 24000
                },
                {
                    "name": "en-GB-Neural2-A",
                    "languageCodes": ["en-GB"],
                    "ssmlGender": "FEMALE", 
                    "naturalSampleRateHertz": 24000
                }
            ]
        }
        
        return create_json_response(voices_data)
    
    @staticmethod
    def _handle_synthesis(method: str, url: str, kwargs: Dict[str, Any]) -> MockHTTPResponse:
        """Handle text-to-speech synthesis requests."""
        if method != "POST":
            return create_error_response(405, "Method not allowed")
        
        # Check for API key
        params = kwargs.get("params", {})
        if "key" not in params:
            return create_error_response(401, "Missing API key")
        
        # Check request data
        request_data = kwargs.get("json", {})
        if not request_data.get("input"):
            return create_error_response(400, "Missing input")
        
        if not request_data.get("voice"):
            return create_error_response(400, "Missing voice")
        
        # Mock response with base64-encoded audio
        audio_b64 = base64.b64encode(MOCK_AUDIO_WAV).decode()
        response_data = {
            "audioContent": audio_b64
        }
        
        return create_json_response(response_data)
    
    @staticmethod
    def get_mock_client():
        """Get a mock Google Cloud TTS client for testing."""
        from unittest.mock import MagicMock
        
        mock_client = MagicMock()
        
        # Mock list_voices method
        mock_voices_response = MagicMock()
        mock_voices_response.voices = [
            MagicMock(name="en-US-Neural2-A"),
            MagicMock(name="en-US-Neural2-C"),
            MagicMock(name="en-GB-Neural2-A"),
        ]
        mock_client.list_voices.return_value = mock_voices_response
        
        # Mock synthesize_speech method
        mock_synthesis_response = MagicMock()
        mock_synthesis_response.audio_content = MOCK_AUDIO_WAV
        mock_client.synthesize_speech.return_value = mock_synthesis_response
        
        return mock_client


class EdgeTTSMockProvider:
    """Mock responses for Edge TTS (uses edge-tts library, not HTTP directly)."""
    
    @staticmethod
    def get_mock_communicate():
        """Get a mock Communicate class for edge-tts."""
        from unittest.mock import MagicMock, AsyncMock
        
        class MockCommunicate:
            def __init__(self, text: str, voice: str, **kwargs):
                self.text = text
                self.voice = voice
                self.kwargs = kwargs
            
            async def save(self, output_path: str) -> None:
                """Mock save method."""
                from pathlib import Path
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(MOCK_AUDIO_MP3)
            
            def stream(self):
                """Mock stream method - returns async generator."""
                async def _stream():
                    for chunk in MOCK_AUDIO_CHUNKS:
                        yield {"type": "audio", "data": chunk}
                return _stream()
        
        return MockCommunicate
    
    @staticmethod
    def get_mock_list_voices():
        """Get a mock list_voices function for edge-tts."""
        from unittest.mock import AsyncMock
        
        async def mock_list_voices():
            return [
                {"Name": "en-US-AvaNeural", "ShortName": "en-US-AvaNeural", "Gender": "Female"},
                {"Name": "en-US-JennyNeural", "ShortName": "en-US-JennyNeural", "Gender": "Female"},
                {"Name": "en-US-GuyNeural", "ShortName": "en-US-GuyNeural", "Gender": "Male"},
                {"Name": "en-GB-SoniaNeural", "ShortName": "en-GB-SoniaNeural", "Gender": "Female"},
                {"Name": "en-IE-EmilyNeural", "ShortName": "en-IE-EmilyNeural", "Gender": "Female"},
            ]
        
        return mock_list_voices


# Fixtures for each provider

@pytest.fixture
def mock_elevenlabs_api(mock_http_requests):
    """Mock ElevenLabs API responses."""
    ElevenLabsMockProvider.setup(mock_http_requests)
    return mock_http_requests


@pytest.fixture 
def mock_openai_api(monkeypatch):
    """Mock OpenAI API client."""
    mock_client = OpenAIMockProvider.get_mock_client()
    
    # Mock the OpenAI import and client creation
    def mock_openai_import():
        mock_openai = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        return mock_openai
    
    monkeypatch.setattr("tts.providers.openai_tts.OpenAI", lambda **kwargs: mock_client)
    
    return mock_client


@pytest.fixture
def mock_google_api(mock_http_requests, monkeypatch):
    """Mock Google Cloud TTS API responses."""
    GoogleTTSMockProvider.setup(mock_http_requests)
    
    # Also mock the Google Cloud client library
    mock_client = GoogleTTSMockProvider.get_mock_client()
    
    def mock_texttospeech():
        mock_module = MagicMock()
        mock_module.TextToSpeechClient.from_service_account_info.return_value = mock_client
        
        # Mock the data classes
        mock_module.SynthesisInput = MagicMock()
        mock_module.VoiceSelectionParams = MagicMock() 
        mock_module.AudioConfig = MagicMock()
        mock_module.AudioEncoding.LINEAR16 = "LINEAR16"
        
        return mock_module
    
    monkeypatch.setattr("google.cloud.texttospeech", mock_texttospeech(), raising=False)
    
    return mock_http_requests


@pytest.fixture
def mock_edge_tts_api(monkeypatch):
    """Mock edge-tts library."""
    
    # Mock the edge_tts module
    mock_communicate = EdgeTTSMockProvider.get_mock_communicate()
    mock_list_voices = EdgeTTSMockProvider.get_mock_list_voices()
    
    monkeypatch.setattr("edge_tts.Communicate", mock_communicate, raising=False)
    monkeypatch.setattr("edge_tts.list_voices", mock_list_voices, raising=False)
    
    return {
        "Communicate": mock_communicate,
        "list_voices": mock_list_voices
    }


@pytest.fixture
def mock_all_provider_apis(
    mock_elevenlabs_api,
    mock_openai_api, 
    mock_google_api,
    mock_edge_tts_api
):
    """Mock all provider APIs at once."""
    return {
        "elevenlabs": mock_elevenlabs_api,
        "openai": mock_openai_api,
        "google": mock_google_api,
        "edge_tts": mock_edge_tts_api,
    }


# Helper functions for creating specific test scenarios

def create_api_key_error_scenario(registry: NetworkMockRegistry, provider: str) -> None:
    """Create a scenario where API key authentication fails."""
    if provider == "elevenlabs":
        registry.register_pattern(
            "api.elevenlabs.io",
            lambda method, url, kwargs: create_error_response(401, "Invalid API key")
        )
    elif provider == "google":
        registry.register_pattern(
            "texttospeech.googleapis.com", 
            lambda method, url, kwargs: create_error_response(401, "Invalid API key")
        )


def create_quota_exceeded_scenario(registry: NetworkMockRegistry, provider: str) -> None:
    """Create a scenario where API quota is exceeded."""
    if provider == "elevenlabs":
        registry.register_pattern(
            "api.elevenlabs.io",
            lambda method, url, kwargs: create_error_response(429, "Quota exceeded")
        )
    elif provider == "google":
        registry.register_pattern(
            "texttospeech.googleapis.com",
            lambda method, url, kwargs: create_error_response(429, "Quota exceeded") 
        )


def create_network_error_scenario(registry: NetworkMockRegistry) -> None:
    """Create a scenario where network requests fail."""
    import requests
    
    def network_error_response(method: str, url: str, kwargs: Dict[str, Any]) -> MockHTTPResponse:
        raise requests.ConnectionError("Network unreachable")
    
    # Apply to all providers
    for pattern in ["api.elevenlabs.io", "texttospeech.googleapis.com"]:
        registry.register_pattern(pattern, network_error_response)