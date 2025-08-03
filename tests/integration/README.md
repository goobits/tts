# TTS Provider Integration Tests

This directory contains real integration tests for TTS providers that make actual API calls and test real functionality.

## Overview

These tests are designed to validate that TTS providers work correctly with real APIs and services, not just mocked responses. They test:

- Actual audio synthesis with real API calls
- Audio file generation and validation
- Provider-specific features and parameters
- Error handling with real error responses
- Rate limiting and quota management

## Test Structure

### Base Test Class
- `base_provider_test.py` - Common functionality for all provider tests
- Provides audio validation, temporary file management, and standard test patterns

### Provider Tests
- `test_openai_integration.py` - OpenAI TTS API integration tests
- `test_google_integration.py` - Google Cloud TTS integration tests  
- `test_elevenlabs_integration.py` - ElevenLabs API integration tests
- `test_chatterbox_integration.py` - Local Chatterbox model tests

## Setup Requirements

### API Keys
Set the following environment variables for the providers you want to test:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_TTS_API_KEY="your-google-api-key"  # Or use service account
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
# Chatterbox requires no API key (local model)
```

### Google Cloud TTS
For Google, you can use either:
1. API Key: Set `GOOGLE_TTS_API_KEY`
2. Service Account: Set `GOOGLE_APPLICATION_CREDENTIALS` to path of JSON file

### Dependencies
Install all provider dependencies:
```bash
./setup.sh install --dev  # Installs all extras
```

## Running Tests

### All Integration Tests
```bash
# Run all integration tests
pytest tests/integration/ -m integration

# Run with slow tests included
pytest tests/integration/ -m integration --slow

# Run specific provider
pytest tests/integration/providers/test_openai_integration.py -v
```

### Individual Test Classes
```bash
# OpenAI tests
pytest tests/integration/providers/test_openai_integration.py::TestOpenAIIntegration -v

# Google tests  
pytest tests/integration/providers/test_google_integration.py::TestGoogleTTSIntegration -v

# ElevenLabs tests
pytest tests/integration/providers/test_elevenlabs_integration.py::TestElevenLabsIntegration -v

# Chatterbox tests
pytest tests/integration/providers/test_chatterbox_integration.py::TestChatterboxIntegration -v
```

### Specific Test Methods
```bash
# Test basic synthesis only
pytest tests/integration/ -k "test_basic_synthesis" -v

# Test voice functionality
pytest tests/integration/ -k "test_voice" -v

# Test error handling
pytest tests/integration/ -k "test_invalid" -v
```

## Test Categories

### Markers
- `@pytest.mark.integration` - All integration tests
- `@pytest.mark.slow` - Tests that take longer (rate limiting, model loading)

### Skip Conditions
Tests are automatically skipped when:
- API keys are not available
- Required libraries are not installed
- System resources are insufficient (for Chatterbox)

## Rate Limiting Considerations

### OpenAI
- Moderate rate limits
- Tests include delays between requests
- Uses both tts-1 and tts-1-hd models

### Google Cloud TTS
- Generous quotas for testing
- Supports free tier usage
- Tests multiple voice types and languages

### ElevenLabs
- Strict rate limits on free tier
- Tests include longer delays (1-2 seconds)
- Limited to essential voice tests

### Chatterbox
- Local model, no rate limits
- Memory intensive (requires ~2GB RAM)
- GPU support automatically detected

## Quota Management

To minimize API usage during development:

```bash
# Run only basic tests
pytest tests/integration/ -k "test_basic_synthesis" -v

# Skip slow/expensive tests
pytest tests/integration/ -m "integration and not slow" -v

# Test single provider
pytest tests/integration/providers/test_openai_integration.py::TestOpenAIIntegration::test_basic_synthesis -v
```

## Audio Validation

Tests validate generated audio files by:
- Checking file existence and minimum size
- Validating audio format headers (MP3, WAV, etc.)
- Ensuring reasonable file sizes for content length
- Basic audio metadata verification

## Error Scenarios Tested

- Invalid API keys (authentication errors)
- Network connectivity issues
- Invalid voice names
- Quota/rate limit exceeded
- Malformed requests
- Service unavailability

## CI/CD Integration

For continuous integration:

```bash
# Quick integration check (basic tests only)
pytest tests/integration/ -k "test_basic_synthesis" --maxfail=3

# Full integration suite (requires all API keys)
pytest tests/integration/ -m integration --maxfail=5
```

## Troubleshooting

### Common Issues

1. **Tests Skipped**: Check that API keys are set correctly
2. **Authentication Errors**: Verify API keys are valid and have correct permissions
3. **Rate Limit Errors**: Run tests with longer delays or fewer concurrent tests
4. **Memory Errors**: For Chatterbox, ensure sufficient RAM (2GB+) available
5. **Network Errors**: Check internet connectivity and service status

### Debug Mode
```bash
# Run with detailed logging
pytest tests/integration/ -v -s --log-cli-level=DEBUG

# Capture all output
pytest tests/integration/ -v -s --capture=no
```

### Test Account Setup

#### OpenAI
- Sign up at platform.openai.com
- Add billing method for API access
- Generate API key in dashboard

#### Google Cloud TTS
- Create Google Cloud project
- Enable Text-to-Speech API
- Create API key or service account
- Free tier includes 1M characters/month

#### ElevenLabs
- Sign up at elevenlabs.io
- Free tier includes 10,000 characters/month
- Generate API key in profile settings

#### Chatterbox
- No account needed (local model)
- Requires PyTorch installation
- GPU support automatic if CUDA available