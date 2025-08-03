"""
Lightweight network mocking infrastructure that preserves provider logic.

This package provides network-only mocks that intercept HTTP requests and responses
while allowing real provider classes to run with realistic fake external responses.
This approach preserves provider logic including error handling, retries, and edge cases.

## Key Components

### network_mocks.py
- Core HTTP mocking infrastructure
- MockHTTPResponse class that behaves like requests.Response
- NetworkMockRegistry for mapping URLs to responses
- Fixtures for mocking requests without touching provider classes

### provider_mocks.py
- Provider-specific mock responses with realistic API data
- Separate mock classes for each provider (ElevenLabs, OpenAI, Google, Edge TTS)
- Helper functions for creating specific test scenarios (auth failures, quota errors, etc.)

### audio_mocks.py
- Minimal mocks for audio hardware dependencies
- PyAudio device enumeration and playback mocking
- ffmpeg/ffplay subprocess operation mocking
- Audio file operation mocking (conversion, streaming)

## Usage Examples

### Basic Network Mocking
```python
def test_provider_with_network_mock(mock_http_requests):
    # Register custom responses
    mock_http_requests.register_pattern(
        "api.example.com",
        lambda method, url, kwargs: create_json_response({"status": "ok"})
    )

    # Use real provider - network calls will be mocked
    provider = RealProvider()
    provider.synthesize("Hello world", "/tmp/output.mp3")
```

### Provider-Specific Mocking
```python
def test_elevenlabs_synthesis(mock_elevenlabs_api):
    # ElevenLabs API is fully mocked with realistic responses
    provider = ElevenLabsProvider()
    provider.synthesize("Hello world", "/tmp/output.mp3", voice="rachel")
```

### Audio Hardware Mocking
```python
def test_audio_streaming(comprehensive_audio_mocks):
    # All audio hardware is mocked (PyAudio, ffmpeg, etc.)
    provider = StreamingProvider()
    provider.synthesize("Hello world", None, stream=True)
```

## Design Principles

1. **Network-Only Mocking**: Mock only HTTP requests/responses, not provider classes
2. **Realistic Responses**: Use realistic fake data that matches real API responses
3. **Preserve Logic**: Allow real provider instantiation and method calls
4. **Error Handling**: Mock authentication flows, quotas, and network errors
5. **Minimal Hardware Mocks**: Mock only what's necessary for audio operations

This approach ensures that provider logic (error handling, retries, edge cases)
is thoroughly tested while avoiding external dependencies.
"""

from .audio_mocks import (
    AudioEnvironmentMock,
    MockAudioDevice,
    MockAudioStream,
    MockFFmpegProcess,
    MockPyAudio,
    comprehensive_audio_mocks,
    create_audio_conversion_failure_scenario,
    create_audio_device_busy_scenario,
    create_ffmpeg_broken_pipe_scenario,
    mock_audio_environment,
    mock_audio_environment_unavailable,
    mock_audio_file_operations,
    mock_ffmpeg_operations,
    mock_ffmpeg_unavailable,
    mock_pyaudio,
    mock_tempfile_operations,
)
from .network_mocks import (
    MockHTTPResponse,
    NetworkMockRegistry,
    create_audio_response,
    create_error_response,
    create_json_response,
    create_streaming_response,
    mock_http_requests,
    mock_network_exceptions,
    network_mock_registry,
)
from .provider_mocks import (
    EdgeTTSMockProvider,
    ElevenLabsMockProvider,
    GoogleTTSMockProvider,
    OpenAIMockProvider,
    create_api_key_error_scenario,
    create_network_error_scenario,
    create_quota_exceeded_scenario,
    mock_all_provider_apis,
    mock_edge_tts_api,
    mock_elevenlabs_api,
    mock_google_api,
    mock_openai_api,
)

__all__ = [
    # Network mocking
    "MockHTTPResponse",
    "NetworkMockRegistry",
    "mock_http_requests",
    "network_mock_registry",
    "mock_network_exceptions",
    "create_json_response",
    "create_audio_response",
    "create_error_response",
    "create_streaming_response",
    # Provider mocking
    "ElevenLabsMockProvider",
    "OpenAIMockProvider",
    "GoogleTTSMockProvider",
    "EdgeTTSMockProvider",
    "mock_elevenlabs_api",
    "mock_openai_api",
    "mock_google_api",
    "mock_edge_tts_api",
    "mock_all_provider_apis",
    "create_api_key_error_scenario",
    "create_quota_exceeded_scenario",
    "create_network_error_scenario",
    # Audio mocking
    "MockAudioDevice",
    "MockPyAudio",
    "MockAudioStream",
    "MockFFmpegProcess",
    "AudioEnvironmentMock",
    "mock_pyaudio",
    "mock_audio_environment",
    "mock_audio_environment_unavailable",
    "mock_ffmpeg_operations",
    "mock_ffmpeg_unavailable",
    "mock_audio_file_operations",
    "mock_tempfile_operations",
    "comprehensive_audio_mocks",
    "create_audio_device_busy_scenario",
    "create_ffmpeg_broken_pipe_scenario",
    "create_audio_conversion_failure_scenario",
]
