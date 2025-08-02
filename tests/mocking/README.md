# Network Mocking Infrastructure

This directory contains a lightweight network mocking infrastructure that preserves provider logic while intercepting external dependencies. The design philosophy is **network-only mocking** - we mock HTTP requests/responses but allow real provider classes to run with realistic fake external responses.

## Key Benefits

1. **Preserves Provider Logic**: Real provider instances run their actual error handling, retry logic, and edge cases
2. **Realistic Testing**: Mock responses match real API formats and behaviors  
3. **Isolated Testing**: No external dependencies or API keys required
4. **Minimal Overhead**: Only network calls are intercepted, not entire provider classes

## Architecture

### Core Components

- **`network_mocks.py`**: Core HTTP mocking infrastructure
- **`provider_mocks.py`**: Provider-specific mock responses with realistic API data
- **`audio_mocks.py`**: Audio hardware mocks (PyAudio, ffmpeg, etc.)

### Design Principles

```python
# ❌ Old approach: Mock entire provider classes
mock_provider = MagicMock()
mock_provider.synthesize.return_value = None

# ✅ New approach: Mock only network calls, use real providers
@pytest.fixture
def test_with_network_mocks(mock_elevenlabs_api):
    provider = ElevenLabsProvider()  # Real provider instance
    provider.synthesize("Hello", "/tmp/test.mp3")  # Real logic, mocked network
```

## Usage Examples

### Basic Network Mocking

```python
def test_custom_api_behavior(mock_http_requests):
    # Register custom response for specific URL pattern
    mock_http_requests.register_pattern(
        "api.example.com",
        lambda method, url, kwargs: create_json_response({"status": "ok"})
    )
    
    # Use real provider - network calls will be intercepted
    provider = RealProvider()
    result = provider.api_call()  # Uses mock response
```

### Provider-Specific Mocking

```python
def test_elevenlabs_synthesis(mock_elevenlabs_api, comprehensive_audio_mocks):
    """ElevenLabs API is fully mocked with realistic responses"""
    provider = ElevenLabsProvider()  # Real provider
    
    # Real provider logic with mocked external calls
    provider.synthesize("Hello world", "/tmp/output.mp3", voice="rachel")
    
    # Provider error handling, voice parsing, etc. all work normally
```

### Audio Hardware Mocking

```python
def test_streaming_audio(comprehensive_audio_mocks):
    """All audio hardware dependencies are mocked"""
    provider = StreamingProvider()
    
    # Real streaming logic with mocked PyAudio/ffmpeg
    provider.synthesize("Hello", None, stream=True)
    
    # Verify audio pipeline was used
    processes = comprehensive_audio_mocks["ffmpeg"]["processes"]
    assert len(processes) > 0
```

### Error Scenario Testing

```python
def test_authentication_failure(mock_elevenlabs_api):
    """Test provider error handling with network failures"""
    from tests.mocking import create_api_key_error_scenario
    
    # Set up authentication failure
    create_api_key_error_scenario(mock_elevenlabs_api, "elevenlabs")
    
    provider = ElevenLabsProvider()
    
    # Provider should handle auth error correctly
    with pytest.raises(AuthenticationError):
        provider.synthesize("Hello", "/tmp/test.mp3")
```

## Available Fixtures

### Network Mocking

- `mock_http_requests`: Basic HTTP request mocking
- `network_mock_registry`: Direct access to URL pattern registry
- `mock_network_exceptions`: Helper for creating network errors

### Provider-Specific Mocking

- `mock_elevenlabs_api`: ElevenLabs API with realistic responses
- `mock_openai_api`: OpenAI TTS client mocking
- `mock_google_api`: Google Cloud TTS API (REST + client library)
- `mock_edge_tts_api`: edge-tts library mocking
- `mock_all_provider_apis`: All provider APIs at once

### Audio Hardware Mocking

- `mock_pyaudio`: PyAudio device enumeration and streams
- `mock_audio_environment`: Audio environment detection
- `mock_ffmpeg_operations`: ffmpeg/ffplay subprocess operations
- `mock_audio_file_operations`: Audio conversion and streaming
- `comprehensive_audio_mocks`: All audio mocks combined

## Provider-Specific Details

### ElevenLabs

```python
def test_elevenlabs_features(mock_elevenlabs_api):
    provider = ElevenLabsProvider()
    
    # Voice listing with realistic mock data
    voices = provider._get_available_voices()
    assert "Rachel" in [v["name"] for v in voices]
    
    # Synthesis with parameter validation
    provider.synthesize(
        text="Hello",
        output_path="/tmp/test.mp3", 
        voice="rachel",
        stability=0.5,
        similarity_boost=0.7
    )
```

**Mocked Endpoints:**
- `GET /v1/voices` - Returns realistic voice list
- `POST /v1/text-to-speech/{voice_id}` - Returns mock audio data
- `POST /v1/text-to-speech/{voice_id}/stream` - Returns chunked audio

### OpenAI

```python
def test_openai_features(mock_openai_api):
    provider = OpenAITTSProvider()
    
    # Real provider logic with mocked OpenAI client
    provider.synthesize("Hello", "/tmp/test.mp3", voice="nova")
    
    # Verify correct API usage
    mock_openai_api.audio.speech.create.assert_called_once()
```

**Mocked Components:**
- `OpenAI` client class
- `audio.speech.create()` method
- Response streaming (`iter_bytes()`)

### Google Cloud TTS

```python
def test_google_features(mock_google_api):
    provider = GoogleTTSProvider()
    
    # Supports both API key and service account auth
    provider.synthesize(
        text="<speak>Hello <break time='1s'/> world</speak>",
        output_path="/tmp/test.wav",
        voice="en-US-Neural2-A"
    )
```

**Mocked Endpoints:**
- `GET /v1/voices` - Returns voice list
- `POST /v1/text:synthesize` - Returns base64-encoded audio

**Mocked Libraries:**
- `google.cloud.texttospeech` client library
- Service account authentication

### Edge TTS

```python
def test_edge_tts_features(mock_edge_tts_api):
    provider = EdgeTTSProvider()
    
    # Real async logic with mocked edge-tts library
    provider.synthesize(
        text="Hello",
        output_path="/tmp/test.mp3",
        voice="en-US-JennyNeural",
        rate="+10%"
    )
```

**Mocked Components:**
- `edge_tts.Communicate` class
- `edge_tts.list_voices()` function
- Async streaming (`stream()` method)

## Testing Error Scenarios

### Authentication Errors

```python
def test_auth_failure(mock_http_requests):
    create_api_key_error_scenario(mock_http_requests, "elevenlabs")
    
    provider = ElevenLabsProvider()
    with pytest.raises(AuthenticationError):
        provider.synthesize("Hello", "/tmp/test.mp3")
```

### Network Failures

```python
def test_network_failure(mock_http_requests):
    create_network_error_scenario(mock_http_requests)
    
    provider = ElevenLabsProvider()  
    with pytest.raises(NetworkError):
        provider.synthesize("Hello", "/tmp/test.mp3")
```

### Quota/Rate Limiting

```python
def test_quota_exceeded(mock_http_requests):
    create_quota_exceeded_scenario(mock_http_requests, "google")
    
    provider = GoogleTTSProvider()
    with pytest.raises(QuotaError):
        provider.synthesize("Hello", "/tmp/test.wav")
```

### Audio Hardware Issues

```python
def test_audio_unavailable(mock_audio_environment_unavailable):
    provider = EdgeTTSProvider()
    
    # Should fall back to tempfile method
    provider.synthesize("Hello", None, stream=True)

def test_ffmpeg_missing(mock_ffmpeg_unavailable):
    provider = StreamingProvider()
    
    with pytest.raises(DependencyError):
        provider.synthesize("Hello", None, stream=True)
```

## Creating Custom Mock Scenarios

### Custom API Responses

```python
def test_custom_scenario(mock_http_requests):
    def custom_response(method: str, url: str, kwargs: dict):
        if "special_endpoint" in url:
            return create_json_response({"custom": "data"})
        return create_error_response(404, "Not found")
    
    mock_http_requests.register_pattern("api.provider.com", custom_response)
```

### Simulating Rate Limiting

```python
def test_rate_limiting(mock_http_requests):
    call_count = 0
    
    def rate_limited_response(method: str, url: str, kwargs: dict):
        nonlocal call_count
        call_count += 1
        
        if call_count <= 2:
            return create_error_response(429, "Rate limit exceeded")
        else:
            return create_audio_response(b"success_after_retry")
    
    mock_http_requests.register_pattern("api.provider.com", rate_limited_response)
```

## Best Practices

### 1. Use Real Provider Instances

```python
# ✅ Good: Real provider with mocked network
def test_provider_logic(mock_elevenlabs_api):
    provider = ElevenLabsProvider()  # Real instance
    provider.synthesize("Hello", "/tmp/test.mp3")

# ❌ Avoid: Mocking provider classes
def test_provider_mock():
    mock_provider = MagicMock()
    mock_provider.synthesize.return_value = None
```

### 2. Test Provider-Specific Logic

```python
def test_voice_validation(mock_openai_api):
    provider = OpenAITTSProvider()
    
    # Test invalid voice handling
    provider.synthesize("Hello", "/tmp/test.mp3", voice="invalid")
    
    # Verify provider defaulted correctly
    call_args = mock_openai_api.audio.speech.create.call_args
    assert call_args[1]["voice"] == "nova"  # Provider's fallback
```

### 3. Verify Error Handling

```python
def test_error_mapping(mock_http_requests):
    mock_http_requests.register_pattern(
        "api.provider.com",
        lambda m, u, k: create_error_response(401, "Invalid key")
    )
    
    provider = Provider()
    
    # Verify provider maps HTTP errors correctly
    with pytest.raises(AuthenticationError):  # Not generic Exception
        provider.synthesize("Hello", "/tmp/test.mp3")
```

### 4. Test Audio Pipeline Integration

```python
def test_streaming_pipeline(mock_all_provider_apis, comprehensive_audio_mocks):
    provider = StreamingProvider()
    provider.synthesize("Hello", None, stream=True)
    
    # Verify complete pipeline was used
    assert comprehensive_audio_mocks["environment"].check_audio_environment()
    assert len(comprehensive_audio_mocks["ffmpeg"]["processes"]) > 0
```

## Migration from Old Mocks

### Before (Provider Class Mocking)

```python
@pytest.fixture
def mock_provider():
    mock = MagicMock()
    mock.synthesize.return_value = None
    mock.get_info.return_value = {"name": "Mock"}
    return mock

def test_old_way(mock_provider):
    # Doesn't test real provider logic
    mock_provider.synthesize("Hello", "/tmp/test.mp3")
    mock_provider.synthesize.assert_called_once()
```

### After (Network-Only Mocking)

```python
def test_new_way(mock_elevenlabs_api, comprehensive_audio_mocks):
    # Tests real provider logic with mocked external dependencies
    provider = ElevenLabsProvider()
    provider.synthesize("Hello", "/tmp/test.mp3", voice="rachel")
    
    # Real error handling, voice parsing, etc. all tested
```

## Debugging Mock Issues

### Enable Mock Logging

```python
def test_with_logging(mock_http_requests, caplog):
    # Log all mock requests for debugging
    def logging_response(method: str, url: str, kwargs: dict):
        print(f"Mock request: {method} {url}")
        return create_json_response({"debug": "data"})
    
    mock_http_requests.register_pattern("api.provider.com", logging_response)
```

### Inspect Mock State

```python
def test_mock_inspection(comprehensive_audio_mocks):
    provider = StreamingProvider()
    provider.synthesize("Hello", None, stream=True)
    
    # Inspect what happened
    processes = comprehensive_audio_mocks["ffmpeg"]["processes"]
    print(f"Created {len(processes)} ffmpeg processes")
    
    for process in processes:
        print(f"Command: {process.cmd}")
        print(f"Stdin writes: {len(process.stdin.write.call_args_list)}")
```

This infrastructure enables comprehensive testing of TTS provider logic while maintaining isolation from external dependencies and preserving the actual error handling, retry mechanisms, and edge cases that make the providers robust.